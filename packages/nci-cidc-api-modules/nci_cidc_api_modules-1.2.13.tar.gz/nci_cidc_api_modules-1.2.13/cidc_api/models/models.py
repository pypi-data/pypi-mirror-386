__all__ = [
    "BaseModel",
    "CIDCRole",
    "Column",
    "CommonColumns",
    "DownloadableFiles",
    "FileGroups",
    "FilesToFileGroups",
    "EXTRA_DATA_TYPES",
    "IntegrityError",
    "IAMException",
    "NoResultFound",
    "Permissions",
    "prism",  # for CFns
    "ROLES",
    "Session",
    "String",
    "TrialMetadata",
    "unprism",  # for CFns
    "UploadJobs",
    "UploadJobStatus",
    "Users",
    "ValidationMultiError",
    "with_default_session",
    "PreprocessedFiles",
    "FileValidationErrors",
    "IngestionJobs",
    "JobFileCategories",
    "ValidationConfigs",
    "TRIAL_APPENDIX_A",
    "TRIAL_APPENDIX_A_CELL_THAT_ENDS_THE_HEADER",
    "REQUEST_LETTER",
    "DETAILED_VALIDATION",
    "ADMIN_FILE_CATEGORIES",
    "FINAL_JOB_STATUS",
    "INGESTION_JOB_STATUSES",
    "INGESTION_JOB_COLORS",
]

import hashlib
import os
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from enum import Enum as EnumBaseClass
from functools import wraps
from typing import (
    Any,
    BinaryIO,
    ClassVar,
    Dict,
    Optional,
    List,
    Set,
    Type,
    Union,
    Callable,
    Tuple,
    Iterable,
)

import pandas as pd
from cidc_schemas import prism, unprism, json_validation
from flask import current_app as app
from google.cloud.storage import Blob
from jsonschema.exceptions import ValidationError
from sqlalchemy import (
    and_,
    asc,
    case,
    desc,
    func,
    literal,
    literal_column,
    not_,
    or_,
    select,
    text,
    true,
    tuple_,
    update,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine import ResultProxy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import (
    # This is unfortunate but other code in this file relies on sqlalchemy.and_, or_, etc
    # instead of the sqlalchemy.sql versions we are importing here.  The solution is to
    # break up this giant file.
    and_ as sql_and,
    or_ as sql_or,
)
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.functions import coalesce
from werkzeug.exceptions import BadRequest

from .files import (
    build_trial_facets,
    build_data_category_facets,
    get_facet_groups_for_paths,
    facet_groups_to_categories,
    details_dict,
    FilePurpose,
    FACET_NAME_DELIM,
)
from ..config.db import BaseModel
from ..config.logging import get_logger
from ..config.settings import (
    PAGINATION_PAGE_SIZE,
    MAX_PAGINATION_PAGE_SIZE,
    TESTING,
    INACTIVE_USER_DAYS,
    GOOGLE_CLINICAL_DATA_BUCKET,
)
from ..shared import emails
from ..shared.gcloud_client import (
    grant_download_access_to_blob_names,
    grant_lister_access,
    grant_download_access,
    publish_artifact_upload,
    publish_patient_sample_update,
    refresh_intake_access,
    revoke_download_access,
    revoke_intake_access,
    revoke_lister_access,
    revoke_bigquery_access,
    gcs_xlsx_or_csv_file_to_pandas_dataframe,
)

os.environ["TZ"] = "UTC"
logger = get_logger(__name__)

# pylint: disable=protected-access,not-callable,no-value-for-parameter,too-many-positional-arguments
# pylint: disable=unsubscriptable-object,singleton-comparison,broad-exception-raised,redefined-builtin
# pylint: disable=arguments-renamed,logging-fstring-interpolation,disable=comparison-with-callable


class FileGroups:
    pass


def with_default_session(f):
    """
    For some `f` expecting a database session instance as a keyword argument,
    set the default value of the session keyword argument to the current app's
    database driver's session. We need to do this in a decorator rather than
    inline in the function definition because the current app is only available
    once the app is running and an application context has been pushed.
    """

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "session" not in kwargs:
            kwargs["session"] = app.extensions["sqlalchemy"].session
        return f(*args, **kwargs)

    return wrapped


def make_etag(args: Union[dict, list]):
    """Make an etag by hashing the representation of the provided `args` dict"""
    argbytes = bytes(repr(args), "utf-8")
    return hashlib.md5(argbytes).hexdigest()


class CommonColumns(BaseModel):  # type: ignore
    """Metadata attributes shared by all resources"""

    __abstract__ = True  # Indicate that this isn't a Table schema

    _created = Column(DateTime, default=func.now(), nullable=False)
    _updated = Column(DateTime, default=func.now(), nullable=False)
    _etag = Column(String(40), nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict of all non-null columns (by name) and their values"""
        # avoid circular imports
        _all_bases: Callable[[Type], Set[Type]] = lambda cls: set(cls.__bases__).union(
            [s for c in cls.__bases__ for s in _all_bases(c)]
        )

        columns_to_check = list(type(self).__table__.columns)
        for b in _all_bases(type(self)):
            if hasattr(b, "__table__"):
                columns_to_check.extend(b.__table__.columns)

        ret = {c.name: getattr(self, c.name) for c in columns_to_check if hasattr(self, c.name)}
        ret = {k: v for k, v in ret.items() if v is not None}
        return ret

    def compute_etag(self) -> str:
        """Calculate the etag for this instance"""
        columns = self.__table__.columns.keys()
        etag_fields = [getattr(self, c) for c in columns if not c.startswith("_")]
        return make_etag(etag_fields)

    @with_default_session
    def insert(self, session: Session, commit: bool = True):
        """Add the current instance to the session."""
        # Compute an _etag if none was provided
        self._etag = self._etag or self.compute_etag()

        session.add(self)
        if commit:
            session.commit()

    @with_default_session
    def update(self, session: Session, changes: dict = None, commit: bool = True):
        """
        Update the current instance if it exists in the session.
        `changes` should be a dictionary mapping column names to updated values.
        """
        # Ensure the record exists in the database
        if not self.find_by_id(self.id, session=session):
            raise NoResultFound()

        # Update this record's fields if changes were provided
        if changes:
            for column in self.__table__.columns.keys():
                if column in changes:
                    setattr(self, column, changes[column])

        # Set the _updated field to now
        self._updated = datetime.now()

        # Update the instance etag
        self._etag = self.compute_etag()

        session.merge(self)
        if commit:
            session.commit()

    @with_default_session
    def delete(self, session: Session, commit: bool = True):
        """Delete the current instance from the session."""
        session.delete(self)
        if commit:
            session.commit()

    @classmethod
    @with_default_session
    def list(cls, session: Session, **pagination_args):
        """List records in this table, with pagination support."""
        query = session.query(cls)
        query = cls._add_pagination_filters(query, **pagination_args)
        return query.all()

    @classmethod
    def _add_pagination_filters(
        cls,
        query: Query,
        page_num: int = 0,
        page_size: int = PAGINATION_PAGE_SIZE,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        filter_: Callable[[Query], Query] = lambda q: q,
    ) -> Query:
        # Enforce positive page numbers
        page_num = 0 if page_num < 0 else page_num

        # Enforce maximum page size
        page_size = min(page_size, MAX_PAGINATION_PAGE_SIZE)

        # Handle sorting
        if sort_field:
            # Get the attribute from the class, in case this is a hybrid attribute
            sort_attribute = getattr(cls, sort_field)
            field_with_dir = asc(sort_attribute) if sort_direction == "asc" else desc(sort_attribute)
            query = query.order_by(field_with_dir)
            if sort_field != "id":
                # When sorting, need to guarantee unique order for offset/limit pagination to produce
                # consistent results. Adding secondary "id" sort field to ensure unique order.
                secondary_field_with_dir = asc("id") if sort_direction == "asc" else desc("id")
                query = query.order_by(secondary_field_with_dir)

        # Apply filter function
        query = filter_(query)

        # Handle pagination
        query = query.offset(page_num * page_size)
        query = query.limit(page_size)

        return query

    @classmethod
    @with_default_session
    def count(cls, session: Session, filter_: Callable[[Query], Query] = lambda q: q):
        """Return the total number of records in this table."""
        filtered_query = filter_(session.query(cls.id))
        return filtered_query.count()

    @classmethod
    @with_default_session
    def count_by(cls, expr, session: Session, filter_: Callable[[Query], Query] = lambda q: q) -> Dict[str, int]:
        """
        Return a dictionary mapping results of `expr` to the number of times each result
        occurs in the table related to this model. E.g., for the `UploadJobs` model,
        `UploadJobs.count_by_column(UploadJobs.upload_type)` would return a dictionary mapping
        upload types to the number of jobs for each type.
        """
        results = filter_(session.query(expr, func.count(cls.id)).group_by(expr)).all()
        return dict(results)

    @classmethod
    @with_default_session
    def find_by_id(cls, id: int, session: Session):
        """Find the record with this id"""
        return session.get(cls, id)

    @classmethod
    @with_default_session
    def get_distinct(
        cls,
        column_name: str,
        session: Session,
        filter_: Callable[[Query], Query] = lambda q: q,
    ):
        """Get a list of distinct values for the given column."""
        assert column_name in cls.__table__.columns.keys(), f"{cls.__tablename__} has no column {column_name}"

        base_query = session.query(getattr(cls, column_name))
        filtered_query = filter_(base_query)
        distinct_query = filtered_query.distinct()

        return list(v[0] for v in distinct_query)

    def validate(self):
        """Run custom validations on attributes set on this instance."""

    @classmethod
    def get_unique_columns(cls):
        """Get a list of all the unique columns in this table."""
        return [column for column in cls.__table__.c if column.unique or column.primary_key]


class CIDCRole(EnumBaseClass):
    ADMIN = "cidc-admin"
    CIDC_BIOFX_USER = "cidc-biofx-user"
    CIMAC_BIOFX_USER = "cimac-biofx-user"
    CIMAC_USER = "cimac-user"
    DEVELOPER = "developer"
    DEVOPS = "devops"
    NCI_BIOBANK_USER = "nci-biobank-user"
    NETWORK_VIEWER = "network-viewer"
    PACT_USER = "pact-user"
    CLINICAL_TRIAL_USER = "clinical-trial-user"


ROLES = [role.value for role in CIDCRole]
ORGS = ["CIDC", "DFCI", "ICAHN", "STANFORD", "ANDERSON", "N/A"]


class Users(CommonColumns):
    __tablename__ = "users"

    _accessed = Column(DateTime, default=func.now(), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    contact_email = Column(String)
    first_n = Column(String)
    last_n = Column(String)
    organization = Column(Enum(*ORGS, name="orgs"))
    approval_date = Column(DateTime)
    role = Column(Enum(*ROLES, name="role"))
    disabled = Column(Boolean, default=False, server_default="false")

    @validates("approval_date")
    def send_approval_confirmation(self, key, new_approval_date):
        """Send this user an approval email if their account has just been approved"""
        if self.approval_date is None and new_approval_date is not None:
            emails.confirm_account_approval(self, send_email=True)

        return new_approval_date

    def is_admin(self) -> bool:
        """Returns true if this user is a CIDC admin."""
        return self.role == CIDCRole.ADMIN.value

    def is_nci_user(self) -> bool:
        """Returns true if this user is an NCI Biobank user."""
        return self.role == CIDCRole.NCI_BIOBANK_USER.value

    def is_admin_or_nci_user(self) -> bool:
        """Returns true if this user is a CIDC admin or NCI Biobank user. These users
        share full access to much of the system."""
        return self.is_admin() or self.is_nci_user()

    def has_download_permissions(self) -> bool:
        """Returns false if this user is a Network Viewer or PACT User."""
        return self.role not in (
            CIDCRole.NETWORK_VIEWER.value,
            CIDCRole.PACT_USER.value,
        )

    @with_default_session
    def update_accessed(self, session: Session, commit: bool = True):
        """Set this user's last system access to now."""
        today = datetime.now()
        if not self._accessed or (today - self._accessed).days > 1:
            self._accessed = today
            session.merge(self)
            if commit:
                session.commit()

    @staticmethod
    @with_default_session
    def find_by_email(email: str, session: Session) -> Optional["Users"]:
        """
        Search for a record in the Users table with the given email.
        If found, return the record. If not found, return None.
        """
        user = session.query(Users).filter_by(email=email).first()
        return user

    @staticmethod
    @with_default_session
    def create(profile: dict, session: Session):
        """
        Create a new record for a user if one doesn't exist
        for the given email. Return the user record associated
        with that email.
        """
        email = profile.get("email")
        first_n = profile.get("given_name")
        last_n = profile.get("family_name")

        user = Users.find_by_email(email)
        if not user:
            logger.info("Creating new user with email %s", email)
            user = Users(email=email, contact_email=email, first_n=first_n, last_n=last_n)
            user.insert(session=session)
        return user

    @staticmethod
    @with_default_session
    def disable_inactive_users(session: Session, commit: bool = True) -> List[str]:
        """
        Disable any users who haven't accessed the API in more than `settings.INACTIVE_USER_DAYS`.
        Returns list of user emails that have been disabled.
        """
        user_inactivity_cutoff = datetime.today() - timedelta(days=INACTIVE_USER_DAYS)
        update_query = (
            update(Users)
            .where(and_(Users._accessed < user_inactivity_cutoff, Users.disabled == False))
            .values(disabled=True)
            .returning(Users.id)
        )
        disabled_user_ids: List[int] = list(session.execute(update_query))
        if commit:
            session.commit()

        disabled_users = [Users.find_by_id(uid, session=session) for uid in disabled_user_ids]
        for u in disabled_users:
            Permissions.revoke_user_permissions(u, session=session)
            revoke_bigquery_access(u.email)

        return [u.email for u in disabled_users]

    @staticmethod
    @with_default_session
    def get_data_access_report(io: BinaryIO, session: Session) -> pd.DataFrame:
        """
        Generate an XLSX containing an overview of trial/assay data access permissions
        for every active user in the database. The report will have a sheet per protocol
        identifier, with each sheet containing columns corresponding to a user's email,
        organization, role, and upload type access permissions.

        Save an excel file to the given file handler, and return the pandas dataframe
        used to generate that excel file.
        """
        user_columns = (Users.email, Users.organization, Users.role)

        query = (
            session.query(
                *user_columns,
                Permissions.trial_id,
                func.string_agg(coalesce(Permissions.upload_type, "*"), ","),
            )
            .filter(
                Users.id == Permissions.granted_to_user,
                Users.disabled == False,
                Users.role != None,
                # Exclude admins, since perms in the Permissions table don't impact them.
                # Admin users are handled below.
                Users.role != CIDCRole.ADMIN.value,
            )
            .group_by(Users.id, Permissions.trial_id)
            .union_all(
                # Handle admins separately, since they can view all data for all
                # trials even if they have no permissions assigned to them.
                session.query(*user_columns, TrialMetadata.trial_id, literal("*,clinical_data")).filter(
                    Users.role == CIDCRole.ADMIN.value
                )
            )
        )

        df = pd.DataFrame(query, columns=["email", "organization", "role", "trial_id", "permissions"]).fillna("*")

        with pd.ExcelWriter(
            io
        ) as writer:  # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
            for trial_id in df["trial_id"].unique():
                if trial_id == "*":
                    continue

                trial_group = df[(df["trial_id"] == trial_id) | (df["trial_id"] == "*")]
                trial_group.to_excel(writer, sheet_name=trial_id, index=False)

        return df


class IAMException(Exception):
    pass


EXTRA_DATA_TYPES = [
    "participants info",
    "samples info",
    "clinical_upload",
    "file_group",
]
ALL_UPLOAD_TYPES = set(
    [
        *prism.SUPPORTED_MANIFESTS,
        *prism.SUPPORTED_ASSAYS,
        *prism.SUPPORTED_ANALYSES,
        *EXTRA_DATA_TYPES,
    ]
)


class Permissions(CommonColumns):
    __tablename__ = "permissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["granted_by_user"],
            ["users.id"],
            name="ix_permissions_granted_by_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["granted_to_user"],
            ["users.id"],
            name="ix_permissions_granted_to_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["trial_id"],
            ["trial_metadata.trial_id"],
            name="ix_permissions_trial_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["file_group_id"],
            ["file_groups.id"],
            name="ix_permissions_file_group_id",
            ondelete="CASCADE",
        ),
        CheckConstraint("trial_id is not null or upload_type is not null"),
        CheckConstraint("upload_type <> 'file_group' OR file_group_id is NOT NULL"),
    )
    __mapper_args__ = {"confirm_deleted_rows": False}

    # If user who granted this permission is deleted, this permission will be deleted.
    # TODO: is this what we want?
    granted_by_user = Column(Integer)
    granted_to_user = Column(Integer, nullable=False, index=True)
    trial_id = Column(String, index=True)
    upload_type = Column(String)
    file_group_id = Column(Integer, index=True)
    file_group = relationship("FileGroups", back_populates="permissions")

    __table_args__ = __table_args__ + (
        Index(
            "uix_upload_type_perms",
            "granted_to_user",
            "trial_id",
            "upload_type",
            unique=True,
            postgresql_where=file_group_id.is_(None),
        ),
        Index(
            "uix_file_group_perms",
            "granted_to_user",
            "file_group_id",
            unique=True,
            postgresql_where=file_group_id.isnot(None),
        ),
    )

    # Shorthand to make code related to trial- and upload-type-level permissions
    # easier to interpret.
    EVERY = None

    @validates("upload_type")
    def validate_upload_type(self, key, value: Any) -> Any:
        if value not in ALL_UPLOAD_TYPES and value != self.EVERY:
            raise ValueError(f"cannot grant permission on invalid upload type: {value}")
        return value

    @with_default_session
    def insert(
        self,
        session: Session,
        commit: bool = True,
    ) -> None:
        """
        Insert this permission record into the database and add a corresponding IAM policy binding
        on the GCS data bucket.

        If only a trial_id value is provided, then the permission denotes access to all upload_types
        for the given trial.

        If only an upload_type value is provided, then the permission denotes access to data of that
        upload_type for all trials.

        NOTE: values provided to the `commit` argument will be ignored. This method always commits.
        """
        if self.upload_type == self.EVERY and self.trial_id == self.EVERY and not self.file_group_id:
            raise ValueError("A permission must have a trial id, upload type, or file group.")

        if self.file_group_id and self.upload_type != "file_group":
            raise ValueError("If a permission has a file group, its upload_type must be set to file_group")

        grantee = Users.find_by_id(self.granted_to_user, session=session)
        if grantee is None:
            raise IntegrityError(
                params=None,
                statement=None,
                orig=f"`granted_to_user` user must exist, but no user found with id {self.granted_to_user}",
            )

        grantor = None
        if self.granted_by_user is not None:
            grantor = Users.find_by_id(self.granted_by_user, session=session)
        else:
            raise IntegrityError(
                params=None,
                statement=None,
                orig="`granted_by_user` user must be given",
            )
        if grantor is None:
            raise IntegrityError(
                params=None,
                statement=None,
                orig=f"`granted_by_user` user must exist, but no user found with id {self.granted_by_user}",
            )
        file_group: FileGroups = None
        if self.upload_type == "file_group":
            file_group = FileGroups.find_by_id(self.file_group_id, session=session)
            if not file_group:
                raise IntegrityError(
                    params=None,
                    statement=None,
                    orig=f"`file_group` must exist, but none found with id {self.file_group_id}",
                )

        info_message = f"admin-action: {grantor.email} gave {grantee.email} the permission {self.upload_type or 'all assays'}{'(' + file_group.name + ')' if file_group else ''} on {self.trial_id or 'all trials'}"
        logger.info(info_message)

        if self.upload_type == "file_group":
            # Do not delete past-assigned file_group permissions for this user.
            perms_to_delete = []
        else:
            # If this is a permission granting the user access to all trials for
            # a given upload type or all upload types for a given trial, delete
            # any related trial-upload type specific permissions to avoid
            # redundancy in the database and in conditional IAM bindings.
            perms_to_delete = (
                session.query(Permissions)
                .filter(
                    Permissions.granted_to_user == self.granted_to_user,
                    # If inserting a cross-trial perm, then select relevant
                    # trial-specific perms for deletion.
                    (
                        Permissions.trial_id != self.EVERY
                        if self.trial_id == self.EVERY
                        else Permissions.trial_id == self.trial_id
                    ),
                    # If inserting a cross-upload type perm, then select relevant
                    # upload type-specific perms for deletion. This does NOT
                    # include clinical_data, just manifests/assays/analysis.
                    (
                        and_(
                            Permissions.upload_type != self.EVERY,
                            Permissions.upload_type != "clinical_data",
                        )
                        if self.upload_type == self.EVERY
                        else Permissions.upload_type == self.upload_type
                    ),
                )
                .all()
            )

        # Add any related permission deletions to the insertion transaction.
        # If a delete operation fails, all other deletes and the insertion will
        # be rolled back.
        for perm in perms_to_delete:
            session.delete(perm)

        # Always commit, because we don't want to grant IAM download unless this insert succeeds.
        super().insert(session=session, commit=True)

        # Don't make any GCS changes if this user doesn't have download access, is disabled, or isn't approved
        if not grantee.has_download_permissions() or grantee.disabled or grantee.approval_date is None:
            # TODO: pact users do not have download permissions currently
            return

        try:
            # Grant ACL download permissions in GCS

            if self.upload_type == "file_group":
                Permissions.grant_download_access_to_file_group(grantee.email, file_group)
            else:

                # if they have any download permissions, they need the CIDC Lister role
                grant_lister_access(grantee.email)
                grant_download_access(grantee.email, self.trial_id, self.upload_type)
                # Remove permissions staged for deletion, if any
                for perm in perms_to_delete:
                    revoke_download_access(grantee.email, perm.trial_id, perm.upload_type)
        except Exception as e:
            # Add back deleted permissions, if any
            for perm in perms_to_delete:
                perm.insert(session=session)
            # Delete the just-created permissions record
            super().delete(session=session)

            logger.warning(str(e))
            raise IAMException("IAM grant failed.") from e

    @with_default_session
    def delete(self, deleted_by: Union[Users, int], session: Session, commit: bool = True) -> None:
        """
        Delete this permission record from the database and revoke the corresponding IAM policy binding
        on the GCS data bucket.

        NOTE: values provided to the `commit` argument will be ignored. This method always commits.
        """
        grantee = Users.find_by_id(self.granted_to_user, session=session)
        if grantee is None:
            raise NoResultFound(f"no user with id {self.granted_to_user}")

        if not isinstance(deleted_by, Users):
            deleted_by_user = Users.find_by_id(deleted_by, session=session)
        else:
            deleted_by_user = deleted_by
        if deleted_by_user is None:
            raise NoResultFound(f"no user with id {deleted_by}")

        # Only make GCS ACL changes if this user has download access
        if grantee.has_download_permissions():
            try:
                # Revoke ACL permission in GCS
                revoke_download_access(grantee.email, self.trial_id, self.upload_type)

                # If the permission to delete is the last one, also revoke Lister access
                def filter_(q):
                    return q.filter(Permissions.granted_to_user == grantee.id)

                if Permissions.count(session=session, filter_=filter_) <= 1:
                    # this one hasn't been deleted yet, so 1 means this is the last one
                    revoke_lister_access(grantee.email)

            except Exception as e:
                raise IAMException("IAM revoke failed, and permission db record not removed.") from e

        info_message = f"admin-action: {deleted_by_user.email} removed from {grantee.email} the permission {self.upload_type or 'all assays'} on {self.trial_id or 'all trials'}"
        logger.info(info_message)
        super().delete(session=session, commit=True)

    @staticmethod
    @with_default_session
    def find_for_user(user_id: int, session: Session) -> List["Permissions"]:
        """Find all Permissions granted to the given user."""
        return session.query(Permissions).filter_by(granted_to_user=user_id).all()

    @staticmethod
    @with_default_session
    def get_for_trial_type(
        trial_id: Optional[str],
        upload_type: Optional[Union[str, List[str]]],
        session: Session,
    ) -> List["Permissions"]:
        """
        Check if a Permissions record exists for the given user, trial, and type.
        The result may be a trial- or assay-level permission that encompasses the
        given trial id or upload type.
        """
        if trial_id is None:
            trial_id = Permissions.EVERY
        if upload_type is None:
            upload_type = Permissions.EVERY

        return (
            session.query(Permissions)
            .filter(
                (
                    (
                        (Permissions.trial_id == trial_id)
                        | (trial_id == Permissions.EVERY)
                        | (Permissions.trial_id == Permissions.EVERY)
                    )
                    & (
                        # return if it's the target
                        (Permissions.upload_type == upload_type)
                        # if getting EVERY, return all
                        | (upload_type == Permissions.EVERY)
                        # if permission is EVERY, don't return if looking for clinical_data
                        | ((Permissions.upload_type == Permissions.EVERY) & (upload_type != "clinical_data"))
                    )
                ),
            )
            .all()
        )

    @staticmethod
    @with_default_session
    def get_user_emails_for_trial_upload(
        trial_id: Optional[str], upload_type: Optional[Union[str, List[str]]], session
    ) -> Dict[str, Dict[Optional[str], List[str]]]:
        if upload_type is None or isinstance(upload_type, str):
            permissions_list: List[Permissions] = Permissions.get_for_trial_type(
                trial_id=trial_id, upload_type=upload_type, session=session
            )
        else:
            permissions_list: List[Permissions] = []
            for upload in upload_type:
                permissions_list.extend(
                    Permissions.get_for_trial_type(trial_id=trial_id, upload_type=upload, session=session)
                )

        permissions_dict: Dict[str, Dict[str, List[Permissions]]] = defaultdict(lambda: defaultdict(list))
        for perm in permissions_list:
            permissions_dict[perm.trial_id][perm.upload_type].append(perm)

        user_dict: Dict[str, Dict[str, List[Users]]] = {
            trial: {
                upload: [Users.find_by_id(id=perm.granted_to_user, session=session) for perm in perms]
                for upload, perms in upload_dict.items()
            }
            for trial, upload_dict in permissions_dict.items()
        }
        user_email_dict: Dict[Optional[str], Dict[Optional[str], List[str]]] = {
            trial: {
                upload: list({u.email for u in users if not u.disabled})
                for upload, users in upload_dict.items()
                # only add if at least one user is NOT disabled
                if sum(not u.disabled for u in users)
            }
            for trial, upload_dict in user_dict.items()
        }
        # remove any trial that doesn't have any uploads in it
        user_email_dict = {trial: upload_dict for trial, upload_dict in user_email_dict.items() if len(upload_dict)}
        return user_email_dict

    @staticmethod
    @with_default_session
    def find_for_user_trial_file(
        user_id: int,
        trial_id: str,
        upload_type: str,
        file_groups: Iterable,
        session: Session,
    ) -> Optional["Permissions"]:
        """
        Check if a Permissions record exists for the given user, trial, and file.
        The result may be a trial-, assay-, or file-group-level permission.
        """
        results = (
            session.query(Permissions)
            .filter(
                Permissions.granted_to_user == user_id,
                ((Permissions.trial_id == trial_id) & (Permissions.upload_type == upload_type))
                | ((Permissions.trial_id == Permissions.EVERY) & (Permissions.upload_type == upload_type))
                | (
                    (Permissions.trial_id == trial_id)
                    # if permission is EVERY, don't return if looking for clinical_data
                    & (Permissions.upload_type == Permissions.EVERY)
                    & (upload_type != "clinical_data")
                ),
            )
            .first()
        )

        # If nothing found so far, check file-group-level permissions.
        if not results and file_groups:
            results = (
                session.query(Permissions)
                .join(FileGroups, Permissions.file_group_id == FileGroups.id)
                .filter(Permissions.granted_to_user == user_id)
                .filter(Permissions.trial_id == trial_id)
                .filter(Permissions.file_group_id == FileGroups.id)
                .all()
            )
            if results:
                file_group_ids = {file_group.id for file_group in file_groups}
                results = [result for result in results if result.file_group_id in file_group_ids]

        results = results and results or None
        return results

    @staticmethod
    @with_default_session
    def grant_user_permissions(user: Users, session: Session) -> None:
        """
        Grant each of the given `user`'s permissions. Idempotent.
        """
        # Don't make any GCS changes if this user doesn't have download access
        if not user.has_download_permissions():
            return

        perms = Permissions.find_for_user(user.id, session=session)
        # if they have any download permissions, they need the CIDC Lister role
        # If a Permission's FileGroup is None, that implies the Permission is a
        # trial/assay type and thus lister access is required.
        if len(perms) and any(perm.file_group_id is None for perm in perms):
            grant_lister_access(user.email)

        # separate permissions by trial, as they are strictly non-overlapping
        perms_by_trial: Dict[str, List[Permissions]] = defaultdict(list)
        # Or separate permissions by filegroup
        file_group_perms = []
        file_group_perms_ids = []
        for perm in perms:
            if perm.upload_type == "file_group":
                if perm.file_group_id not in file_group_perms_ids:
                    file_group_perms.append(perm)
                    file_group_perms_ids.append(perm.file_group_id)
            else:
                perms_by_trial[perm.trial_id].append(perm)
        perms_by_trial = dict(perms_by_trial)

        for trial_id, trial_perms in perms_by_trial.items():
            # Regrant each permission: idempotent.
            grant_download_access(
                user_email_list=user.email,
                trial_id=trial_id,
                upload_type=[p.upload_type for p in trial_perms],
            )
        for perm in file_group_perms:
            file_group: FileGroups = FileGroups.find_by_id(perm.file_group_id, session=session)
            Permissions.grant_download_access_to_file_group(user.email, file_group)

        # Regrant all of the user's intake bucket upload permissions, if they have any
        refresh_intake_access(user.email)

    @staticmethod
    @with_default_session
    def revoke_user_permissions(user: Users, session: Session) -> None:
        """
        Revoke each of the given `user`'s permissions. Idempotent.
        """
        # Don't make any GCS changes if this user doesn't have download access
        if not user.has_download_permissions():
            return

        perms = Permissions.find_for_user(user.id, session=session)
        # since we're revoking all, should revoke the CIDC Lister role too
        if len(perms):
            revoke_lister_access(user.email)

        # separate permissions by trial, as they are strictly non-overlapping
        perms_by_trial: Dict[str, List[Permissions]] = defaultdict(list)
        for perm in perms:
            perms_by_trial[perm.trial_id].append(perm)
        perms_by_trial = dict(perms_by_trial)

        for trial_id, trial_perms in perms_by_trial.items():
            # Regrant each permission: idempotent.
            revoke_download_access(
                user_email_list=user.email,
                trial_id=trial_id,
                upload_type=[p.upload_type for p in trial_perms],
            )

        # Revoke all of the user's intake bucket upload permissions, if they have any
        revoke_intake_access(user.email)

    @classmethod
    @with_default_session
    def grant_download_permissions_for_upload_job(cls, upload: "UploadJobs", session: Session) -> None:
        """
        For a given UploadJob, issue all relevant Permissions on Google
        Loads all cross-trial permissions for the upload_type
            and the cross-assay permissions for the trial_id
        """
        # Permissions with matching trial_id or cross-trial single-assay
        # upload.trial_id can't be None
        filters = [
            or_(cls.trial_id == upload.trial_id, cls.trial_id == None),
        ]

        # Permissions with matching upload_type or cross-assay single-trial
        if upload.upload_type == "clinical_data":
            # clinical_data is not included in cross-assay
            filters.append(cls.upload_type == upload.upload_type)
        else:
            # upload.upload_type can't be None
            filters.append(or_(cls.upload_type == upload.upload_type, cls.upload_type == None))

        perms = session.query(cls).filter(*filters).all()
        user_email_list: List[str] = []

        for perm in perms:
            user = Users.find_by_id(perm.granted_to_user, session=session)
            if user.is_admin() or user.is_nci_user() or user.disabled or user.email in user_email_list:
                continue

            user_email_list.append(user.email)
            grant_lister_access(user.email)

        if upload.upload_type in prism.SUPPORTED_SHIPPING_MANIFESTS:
            # Passed with empty user email list because they will be queried for in CFn
            grant_download_access([], upload.trial_id, "participants info")
            grant_download_access([], upload.trial_id, "samples info")
        elif upload.upload_type not in prism.SUPPORTED_WEIRD_MANIFESTS:
            grant_download_access(user_email_list, upload.trial_id, upload.upload_type)

    @staticmethod
    def grant_download_access_to_file_group(user_email: str, file_group: FileGroups):
        # grant to individual blobs rather than calling grant_download_access(grantee, trial, upload_type)
        blob_names: list[str] = [df.object_url for df in file_group.downloadable_files]
        logger.info(
            "Granting access to %s for the following downloadables: %s",
            user_email,
            blob_names,
        )
        grant_download_access_to_blob_names([user_email], blob_names)


class ValidationMultiError(Exception):
    """Holds multiple jsonschema.ValidationErrors"""


trial_metadata_validator: json_validation._Validator = json_validation.load_and_validate_schema(
    "clinical_trial.json", return_validator=True
)

FileBundle = Dict[str, Dict[FilePurpose, List[int]]]


class TrialMetadata(CommonColumns):
    __tablename__ = "trial_metadata"
    # The CIMAC-determined trial id
    trial_id = Column(String, unique=True, nullable=False, index=True)
    metadata_json = Column(JSONB, nullable=False)

    # Create a GIN index on the metadata JSON blobs
    _metadata_idx = Index("metadata_idx", metadata_json, postgresql_using="gin")

    @staticmethod
    def validate_metadata_json(metadata_json: dict, strip_metadata=True) -> dict:
        # Prior to running trial_metadata_validator.iter_error_messages on the metadata_json, if
        # strip_metadata=True, will strip out unnecessary manifest data for the validation so that
        # existing manifest data that no longer conform to the post-CSMS-integration schema can be kept.
        # See more details in the strip_metadata_for_validation function docs.
        metadata_to_validate = (
            json_validation.strip_metadata_for_validation(metadata_json) if strip_metadata else metadata_json
        )
        errs = trial_metadata_validator.iter_error_messages(metadata_to_validate)
        messages = list(f"'metadata_json': {err}" for err in errs)
        if messages:
            raise ValidationMultiError(messages)
        return metadata_json

    def validate(self):
        """Run custom validations on attributes set on this instance."""
        if self.metadata_json is not None:
            self.validate_metadata_json(self.metadata_json)

    def safely_set_metadata_json(self, metadata_json: dict):
        """
        Validate `metadata_json` according to the trial metadata schema before setting
        the `TrialMetadata.metadata_json` attribute.
        """
        self.validate_metadata_json(metadata_json)
        self.metadata_json = metadata_json

    @staticmethod
    @with_default_session
    def find_by_trial_id(trial_id: str, session: Session):
        """
        Find a trial by its CIMAC id.
        """
        return session.query(TrialMetadata).filter_by(trial_id=trial_id).first()

    @staticmethod
    @with_default_session
    def select_for_update_by_trial_id(trial_id: str, session: Session):
        """
        Find a trial by its CIMAC id.
        """
        try:
            trial = session.query(TrialMetadata).filter_by(trial_id=trial_id).with_for_update().one()
        except NoResultFound as e:
            raise NoResultFound(f"No trial found with id {trial_id}") from e
        return trial

    @staticmethod
    @with_default_session
    def patch_assays(trial_id: str, assay_patch: dict, session: Session, commit: bool = False):
        """
        Applies assay updates to the metadata object from the trial with id `trial_id`.

        TODO: apply this update directly to the not-yet-existent TrialMetadata.manifest field
        """
        return TrialMetadata._patch_trial_metadata(trial_id, assay_patch, session=session, commit=commit)

    @staticmethod
    @with_default_session
    def patch_manifest(trial_id: str, manifest_patch: dict, session: Session, commit: bool = False):
        """
        Applies manifest updates to the metadata object from the trial with id `trial_id`.

        TODO: apply this update directly to the not-yet-existent TrialMetadata.assays field
        """
        return TrialMetadata._patch_trial_metadata(trial_id, manifest_patch, session=session, commit=commit)

    @staticmethod
    @with_default_session
    def _patch_trial_metadata(trial_id: str, json_patch: dict, session: Session, commit: bool = False):
        """
        Applies updates to the metadata object from the trial with id `trial_id`
        and commits current session.

        TODO: remove this function and dependency on it, in favor of separate assay
        and manifest patch strategies.
        """

        trial = TrialMetadata.select_for_update_by_trial_id(trial_id, session=session)

        # Merge assay metadata into the existing clinical trial metadata
        updated_metadata, errs = prism.merge_clinical_trial_metadata(json_patch, trial.metadata_json)
        if errs:
            raise ValidationMultiError(errs)
        # Save updates to trial record
        trial.safely_set_metadata_json(updated_metadata)
        trial._etag = make_etag([trial.trial_id, updated_metadata])

        session.add(trial)
        if commit:
            session.commit()

        return trial

    @staticmethod
    @with_default_session
    def create(trial_id: str, metadata_json: dict, session: Session, commit: bool = True):
        """
        Create a new clinical trial metadata record.
        """

        logger.info("Creating new trial metadata with id %s", trial_id)
        trial = TrialMetadata(trial_id=trial_id, metadata_json=metadata_json)
        trial.insert(session=session, commit=commit)

        return trial

    @staticmethod
    def merge_gcs_artifact(metadata: dict, upload_type: str, uuid: str, gcs_object: Blob):
        return prism.merge_artifact(
            ct=metadata,
            assay_type=upload_type,  # assay_type is the old name for upload_type
            artifact_uuid=uuid,
            object_url=gcs_object.name,
            file_size_bytes=gcs_object.size,
            uploaded_timestamp=gcs_object.time_created.isoformat(),
            md5_hash=gcs_object.md5_hash,
            crc32c_hash=gcs_object.crc32c,
        )

    @staticmethod
    def merge_gcs_artifacts(metadata: dict, upload_type: str, uuids_and_gcs_objects: List[Tuple[str, Blob]]):
        return prism.merge_artifacts(
            metadata,
            [
                prism.ArtifactInfo(
                    upload_type=upload_type,
                    artifact_uuid=uuid,
                    object_url=gcs_object.name,
                    file_size_bytes=gcs_object.size,
                    uploaded_timestamp=gcs_object.time_created.isoformat(),
                    md5_hash=gcs_object.md5_hash,
                    crc32c_hash=gcs_object.crc32c,
                )
                for uuid, gcs_object in uuids_and_gcs_objects
            ],
        )

    @classmethod
    @with_default_session
    def generate_patient_csv(cls, trial_id: str, session: Session) -> str:
        """Get the current patient CSV for this trial."""
        trial = cls.find_by_trial_id(trial_id, session=session)
        if not trial:
            raise NoResultFound(f"No trial found with id {trial_id}")
        return unprism.unprism_participants(trial.metadata_json)

    @classmethod
    @with_default_session
    def generate_sample_csv(cls, trial_id: str, session: Session) -> str:
        """Get the current sample CSV for this trial."""
        trial = cls.find_by_trial_id(trial_id, session=session)
        if not trial:
            raise NoResultFound(f"No trial found with id {trial_id}")
        return unprism.unprism_samples(trial.metadata_json)

    file_bundle: ClassVar[Optional[FileBundle]]
    num_participants: ClassVar[Optional[int]]
    num_samples: ClassVar[Optional[int]]
    ready_for_submission: ClassVar[Optional[Boolean]]

    # List of metadata JSON fields that should not be sent to clients
    # in queries that list trial metadata, because they may contain a lot
    # of data.
    PRUNED_FIELDS = ["participants", "assays", "analysis", "shipments"]

    # List of metadata JSON fields that should only be settable via
    # manifest and metadata templates.
    PROTECTED_FIELDS = [*PRUNED_FIELDS, "protocol_identifier"]

    @classmethod
    def _pruned_metadata_json(cls):
        """
        Builds a modified metadata_json column selector with the "assays", "analysis",
        "shipments", and "participants" properties removed.
        """
        query = cls.metadata_json
        for field in cls.PRUNED_FIELDS:
            query = query.op("-")(field)

        return query.label("metadata_json")

    @classmethod
    @with_default_session
    def list(
        cls,
        session: Session,
        user: Users,
        include_file_bundles: bool = False,
        include_counts: bool = False,
        **pagination_args,
    ):
        """
        List `TrialMetadata` records from the database with pruned metadata JSON blobs.
        If `file_bundle=True`, include the file bundle associated with each trial.
        If `include_counts=True`, include participant and sample counts for this trial
            using `TrialMetadata.get_summaries()`.

        NOTE: use find_by_id or find_by_trial_id to get the full metadata JSON blob
        for a particular trial. We don't want lists of trials to include full metadata,
        because doing so can require loading lots of data at once.
        """
        # Instead of selecting the raw "metadata_json" for each trial,
        # select a pruned version with data-heavy attributes removed.]
        columns = [c for c in cls.__table__.c if c.name != "metadata_json"]
        columns.append(cls._pruned_metadata_json())

        # Add other subqueries/columns to include in the query
        subqueries = []

        if include_file_bundles:
            file_bundle_query = DownloadableFiles.build_file_bundle_query()

            columns.append(file_bundle_query.c.file_bundle)
            subqueries.append(file_bundle_query)

        if include_counts:
            trial_summaries: List[dict] = cls.get_summaries()

            participant_counts: Dict[str, int] = {t["trial_id"]: t["total_participants"] for t in trial_summaries}
            sample_counts: Dict[str, int] = {t["trial_id"]: t["total_samples"] for t in trial_summaries}

        # Combine all query components
        query = session.query(*columns)
        for subquery in subqueries:
            # Each subquery will have a trial_id column and one record per trial id
            query = query.outerjoin(subquery, cls.trial_id == subquery.c.trial_id)

        query = query.order_by(cls.trial_id)
        query = cls._add_pagination_filters(query, **pagination_args)

        trials = []
        for result in query:
            # result._asdict gives us a dictionary mapping column names
            # to values for this result
            result_dict = result._asdict()

            # Create a TrialMetadata model instance from the result
            trial = cls()
            for column, value in result_dict.items():
                if value is not None:
                    setattr(trial, column, value)

            if include_counts:
                setattr(trial, "num_participants", participant_counts.get(trial.trial_id, 0))
                setattr(trial, "num_samples", sample_counts.get(trial.trial_id, 0))

            if include_file_bundles and hasattr(trial, "file_bundle"):
                # File bundle has all existing object ids. Remove ones that aren't allowed by permissions.

                # Gather all object ids in the file bundle
                all_object_ids = set()

                for assay, purposes in trial.file_bundle.items():
                    for purpose, object_ids in purposes.items():
                        all_object_ids = all_object_ids.union(object_ids)
                # Remove any impermissible object ids
                filtered_object_ids = DownloadableFiles.filter_object_ids_by_permissions(user, all_object_ids)
                logger.debug(f"Filtered object ids: {len(all_object_ids)} -> {len(filtered_object_ids)}")

                for assay, purposes in trial.file_bundle.items():
                    size_results = {}
                    for purpose, object_ids in purposes.items():
                        # Only allow object ids that are permitted
                        permitted_object_ids = list(set(object_ids).intersection(filtered_object_ids))
                        trial.file_bundle[assay][purpose] = permitted_object_ids
                        if permitted_object_ids:
                            # For any files left in the purpose, get their total size
                            filter_ = lambda q: q.filter(DownloadableFiles.id.in_(permitted_object_ids))
                            size_results[f"{purpose}_size"] = DownloadableFiles.get_total_bytes(filter_=filter_)
                    trial.file_bundle[assay].update(size_results)

                # Trim the file bundle
                for assay, purposes in deepcopy(trial.file_bundle).items():
                    for purpose, object_ids in purposes.items():
                        if not object_ids:
                            # No file ids left in the purpose after filtering. Remove this purpose from the bundle.
                            del trial.file_bundle[assay][purpose]
                    if not trial.file_bundle[assay]:
                        del trial.file_bundle[assay]
            # Check if trial is ready for submission
            setattr(trial, "ready_for_submission", trial.determine_ready_for_submission())

            trials.append(trial)

        return trials

    @with_default_session
    def determine_ready_for_submission(self, session: Session) -> Boolean:
        open_job = IngestionJobs.get_open_job_by_trial(self.trial_id)
        if not open_job:
            return False
        appendix_a_files = PreprocessedFiles.get_files_by_category_and_status(
            "trial_appendix_a", "current", job_id=open_job.id
        )
        trial_letters = PreprocessedFiles.get_files_by_category_and_status(
            "request_letter", "current", job_id=open_job.id
        )
        return appendix_a_files and trial_letters and open_job.status == "DRAFT"

    @with_default_session
    def insert(
        self,
        session: Session,
        commit: bool = True,
        validate_metadata: bool = True,
    ):
        """Add the current instance to the session. Skip JSON metadata validation validate_metadata=False."""
        if self.metadata_json is not None and validate_metadata:
            self.validate_metadata_json(self.metadata_json)

        return super().insert(session=session, commit=commit)

    @with_default_session
    def update(
        self,
        session: Session,
        changes: dict = None,
        commit: bool = True,
        validate_metadata: bool = True,
    ):
        """
        Update the current TrialMetadata instance if it exists. `changes` should be
        a dictionary mapping column names to updated values. Skip JSON metadata validation
        if validate_metadata=False.
        """
        # This update will get rolled back if commit = False
        super().update(session=session, changes=changes)

        # metadata_json was possibly updated in above method call,
        # so check that it's still valid if validate_metadata=True
        if validate_metadata:
            self.validate_metadata_json(self.metadata_json)

        if commit:
            session.commit()
        else:
            session.rollback()

    @classmethod
    def build_trial_filter(cls, user: Users, trial_ids: List[str] = None):
        if trial_ids is None:
            trial_ids = []

        filters = []
        if trial_ids:
            filters.append(cls.trial_id.in_(trial_ids))
        if not user.is_admin() and not user.is_nci_user():
            has_cross_trial_perms = False
            granular_trial_perms = []
            for perm in Permissions.find_for_user(user.id):
                # If perm.trial_id is None, then the user has a cross-trial permission
                if perm.trial_id is None:
                    has_cross_trial_perms = True
                else:
                    granular_trial_perms.append(perm.trial_id)
            # If the user has a cross-trial permission, then they should be able
            # to list all trials, so don't include granular permission filters
            # in that case.
            if not has_cross_trial_perms:
                filters.append(cls.trial_id.in_(granular_trial_perms))

        # possible TODO: filter by assays in a trial
        return lambda q: q.filter(*filters)

    @classmethod
    @with_default_session
    def get_metadata_counts(cls, session: Session) -> dict:
        """
        Return a dictionary using `TrialMetadata.get_summaries()` with the following structure:
        ```
            {
                "num_trials": <count of all trials>,
                "num_participants": <count of all participants across all trials>,
                "num_samples": <count of all samples across all participants across all trials>
            }
        ```
        """

        trial_summaries: List[dict] = cls.get_summaries(session=session)

        return {
            "num_trials": len(trial_summaries),
            "num_participants": sum(t["total_participants"] for t in trial_summaries),
            "num_samples": sum(t["total_samples"] for t in trial_summaries),
        }

    @staticmethod
    def get_summaries_query() -> str:
        # Compute the total amount of data in bytes stored for each trial
        files_subquery = """
                    select
                        trial_id,
                        sum(file_size_bytes) as value
                    from
                        downloadable_files
                    group by
                        trial_id
                """

        # Count how many participants have associated clinical data. The same
        # participant may appear in multiple clinical data files, so deduplicate
        # participants before counting them.
        clinical_subquery = """
                    select
                        trial_id,
                        count(distinct participants) as value
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{clinical_data,records}') as records,
                        jsonb_array_elements(records#>'{clinical_file,participants}') as participants
                    group by
                        trial_id
                """

        # Find all samples associated with each assay type for
        # assays whose metadata follows the typical structure: an array of batches,
        # with each batch containing an array of records, where each record
        # corresponds to a unique sample with a cimac_id.
        generic_assay_subquery = """
                    select
                        trial_id,
                        case
                            when key = 'hande' then 'h&e'
                            else key
                        end as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_each(metadata_json->'assays') assays,
                        jsonb_array_elements(value) batches,
                        jsonb_array_elements(batches->'records') record
                    where key not in ('olink', 'nanostring', 'elisa', 'wes', 'misc_data')
                """

        # Find all samples associated with nanostring uploads.
        # Nanostring metadata has a slightly different structure than typical
        # assays, where each batch has an array of runs, and each run has
        # an array of sample-level entries each with a cimac_id.
        nanostring_subquery = """
                    select
                        trial_id,
                        'nanostring' as key,
                        sample->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,nanostring}') batches,
                        jsonb_array_elements(batches->'runs') runs,
                        jsonb_array_elements(runs->'samples') sample
                """

        # Find all samples associated with olink uploads.
        # Unlike other assays, olink metadata is an object at the top level
        # rather than an array of batches. This object has a "batches"
        # property that points to an array of batches, and each batch contains
        # an array of records. These records are *not* sample-level; rather,
        # the samples corresponding to a given record are stored
        # like: record["files"]["assay_npx"]["samples"].
        olink_subquery = """
                    select
                        trial_id,
                        'olink' as key,
                        sample as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,olink,batches}') batches,
                        jsonb_array_elements(batches->'records') records,
                        jsonb_array_elements_text(records#>'{files,assay_npx,samples}') sample
                """

        # Find all samples associated with elisa uploads.
        # Unlike other assays, elisa metadata is an array of entries, each containing a single data file.
        # The samples corresponding to a given entry are stored like:
        # entry["assay_xlsx"]["samples"].
        elisa_subquery = """
                    select
                        trial_id,
                        'elisa' as key,
                        sample as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,elisa}') entry,
                        jsonb_array_elements_text(entry#>'{assay_xlsx,samples}') sample
                """

        # Find the tumor samples that have associated paired-analysis data.
        wes_analysis_subquery = """
                    select
                        trial_id,
                        'wes_analysis' as key,
                        pair#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_analysis,pair_runs}') pair
                    where
                        pair#>>'{report,report}' is not null
                    union all
                    select
                        trial_id,
                        'wes_analysis' as key,
                        pair#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_analysis_old,pair_runs}') pair
                    where
                        pair#>>'{report,report}' is not null
                """

        # Find the tumor samples that have associated tumor-only analysis data.
        wes_tumor_only_analysis_subquery = """
                    select
                        trial_id,
                        'wes_tumor_only_analysis' as key,
                        run#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_tumor_only_analysis,runs}') run
                    where
                        run#>>'{report,report}' is not null
                    union all
                    select
                        trial_id,
                        'wes_tumor_only_analysis' as key,
                        run#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_tumor_only_analysis_old,runs}') run
                    where
                        run#>>'{report,report}' is not null
                """

        # Find the tumor samples that will have associated paired-analysis data.
        # We are asserting that a tumor sample will not be used for multiple analyses.
        # This is similar to the wes_analysis_subquery but without the requirement for a report,
        # which is the defining feature of analysis.
        wes_subquery = """
                    select
                        trial_id,
                        'wes' as key,
                        pair#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_analysis,pair_runs}') pair
                    union all
                    select
                        trial_id,
                        'wes' as key,
                        pair#>>'{tumor,cimac_id}' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,wes_analysis_old,pair_runs}') pair
                """

        # Find the tumor samples that WON'T have associated paired-analysis data.
        # Get all tumor samples with WES data not in the equivalent of wes_subquery.
        wes_tumor_assay_subquery = """
                    select
                        trial_metadata.trial_id,
                        'wes_tumor_only' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,wes}') batch,
                        jsonb_array_elements(batch->'records') record
                    join (
                        select
                            trial_id,
                            sample->>'cimac_id' as cimac_id
                        from
                            trial_metadata,
                            jsonb_array_elements(metadata_json->'participants') participant,
                            jsonb_array_elements(participant->'samples') sample

                        where
                                sample->>'processed_sample_derivative' = 'Tumor DNA'
                            or
                                sample->>'processed_sample_derivative' = 'Tumor RNA'
                    ) sample_data
                    on
                        sample_data.cimac_id = record->>'cimac_id'
                    where
                        sample_data.trial_id = trial_metadata.trial_id
                        and
                        record->>'cimac_id' not in (
                            select
                                pair#>>'{tumor,cimac_id}'
                            from
                                trial_metadata,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_analysis,pair_runs}') pair
                            union all
                            select
                                pair#>>'{tumor,cimac_id}'
                            from
                                trial_metadata,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_analysis_old,pair_runs}') pair
                        )
                """

        # Find ALL normal samples that have WES data.
        # This is included in counting for total_participants and total_samples,
        # but do not affect the assay-level counts which are tumor sample-specific for WES.
        wes_normal_assay_subquery = """
                    select
                        trial_id,
                        'wes_normal' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,wes}') batch,
                        jsonb_array_elements(batch->'records') record
                    join (
                            select
                                sample->>'cimac_id' as cimac_id
                            from
                                trial_metadata,
                                jsonb_array_elements(metadata_json->'participants') participant,
                                jsonb_array_elements(participant->'samples') sample
                            where
                                    sample->>'processed_sample_derivative' <> 'Tumor DNA'
                                and
                                    sample->>'processed_sample_derivative' <> 'Tumor RNA'
                        ) sample_data
                    on
                        sample_data.cimac_id = record->>'cimac_id'
                """

        # Find all samples associated with RNA analysis uploads.
        # There is ONLY level_1
        rna_level1_analysis_subquery = """
                    select
                        trial_id,
                        'rna_level1_analysis' as key,
                        run->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,rna_analysis,level_1}') run
                """

        # Find all samples associated with TCR analysis uploads.
        tcr_analysis_subquery = """
                    select
                        trial_id,
                        'tcr_analysis' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,tcr_analysis,batches}') batch,
                        jsonb_array_elements(batch->'records') record
                """

        # Find all samples associated with CyTOF analysis uploads.
        cytof_analysis_subquery = """
                    select
                        trial_id,
                        'cytof_analysis' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{assays,cytof}') batch,
                        jsonb_array_elements(batch->'records') record
                    where
                        record->'output_files' is not null
                """

        # Find all samples associated with ATACseq analysis uploads.
        atacseq_analysis_subquery = """
                    select
                        trial_id,
                        'atacseq_analysis' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,atacseq_analysis}') batch,
                        jsonb_array_elements(batch->'records') record
                """

        # Find all samples associated with scrnaseq analysis uploads.
        scrnaseq_analysis_subquery = """
                    select
                        trial_id,
                        'scrnaseq_analysis' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,scrnaseq_analysis}') batch,
                        jsonb_array_elements(batch->'records') record
                """

        # Find all samples associated with visium analysis uploads.
        visium_analysis_subquery = """
                    select
                        trial_id,
                        'visium_analysis' as key,
                        record->>'cimac_id' as cimac_id
                    from
                        trial_metadata,
                        jsonb_array_elements(metadata_json#>'{analysis,visium_analysis}') batch,
                        jsonb_array_elements(batch->'records') record
                """

        # Build up a JSON object mapping analysis types to arrays of excluded samples.
        # The resulting object will have structure like:
        # {
        #   "cytof_analysis": [missing samples],
        #   "wes_analysis": [missing samples],
        #   ...
        # }
        excluded_samples_subquery = """
                    select
                        trial_id,
                        jsonb_object_agg(key, value) as value
                    from (
                        select
                            trial_id,
                            key,
                            jsonb_agg(sample) as value
                        from (
                            select
                                trial_id,
                                'cytof_analysis' as key,
                                jsonb_array_elements(batch->'excluded_samples') as sample
                            from
                                trial_metadata,
                                jsonb_array_elements(metadata_json#>'{assays,cytof}') batch
                            union all
                            select
                                trial_id,
                                'wes_analysis' as key,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_analysis,excluded_samples}') as sample
                            from
                                trial_metadata
                            union all
                            select
                                trial_id,
                                'wes_analysis' as key,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_analysis_old,excluded_samples}') as sample
                            from
                                trial_metadata
                            union all
                            select
                                trial_id,
                                'wes_tumor_only_analysis' as key,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_tumor_only_analysis,excluded_samples}') as sample
                            from
                                trial_metadata
                            union all
                            select
                                trial_id,
                                'wes_tumor_only_analysis' as key,
                                jsonb_array_elements(metadata_json#>'{analysis,wes_tumor_only_analysis_old,excluded_samples}') as sample
                            from
                                trial_metadata
                            union all
                            select
                                trial_id,
                                'rna_level1_analysis' as key,
                                jsonb_array_elements(metadata_json#>'{analysis,rna_analysis,excluded_samples}') as sample
                            from
                                trial_metadata
                            union all
                            select
                                trial_id,
                                'tcr_analysis' as key,
                                jsonb_array_elements(batches->'excluded_samples') as sample
                            from
                                trial_metadata,
                                jsonb_array_elements(metadata_json#>'{analysis,tcr_analysis,batches}') batches
                        ) excluded_q1
                        group by trial_id, key
                    ) excluded_q2
                    group by trial_id
                """

        # Extract an array of expected assays or an empty array if expected assays is null.
        expected_assays_subquery = """
                    select
                        trial_id,
                        coalesce(metadata_json->'expected_assays', '[]'::jsonb) as expected_assays
                    from
                        trial_metadata
                """

        # All the subqueries produce the same set of columns, so UNION ALL
        # them together into a single query, aggregating results into
        # trial-level JSON dictionaries with the shape described in the docstring.
        # NOTE: we use UNION ALL for assay-level counts instead of just UNION to
        # prevent any unwanted de-duplication within subquery results.
        combined_query = f"""
                    select
                        jsonb_object_agg('trial_id', expected_assays.trial_id)
                        || jsonb_object_agg('excluded_samples', coalesce(excluded_sample_lists.value, '{{}}'::jsonb))
                        || jsonb_object_agg('expected_assays', coalesce(expected_assays, '[]'::jsonb))
                        || jsonb_object_agg('file_size_bytes', coalesce(file_sizes.value, 0))
                        || jsonb_object_agg('clinical_participants', coalesce(clinical_participants.value, 0))
                        || jsonb_build_object('total_participants', coalesce(total_participants, 0))
                        || jsonb_build_object('total_samples', coalesce(total_samples, 0))
                        || coalesce(sample_counts.sample_counts, '{{}}'::jsonb) as result
                    from ({expected_assays_subquery}) expected_assays
                    full join (
                        select
                            trial_id,
                            count(distinct cimac_id) as total_samples,
                            count(distinct left(cimac_id, 7)) as total_participants
                        from (
                            {generic_assay_subquery}
                            union
                            {nanostring_subquery}
                            union
                            {olink_subquery}
                            union
                            {elisa_subquery}
                            union
                            {wes_subquery}
                            union
                            {wes_tumor_assay_subquery}
                            union
                            {wes_normal_assay_subquery}
                        ) assays
                        group by
                            trial_id
                    ) total_counts
                    on expected_assays.trial_id = total_counts.trial_id
                    full join (
                        select
                            trial_id,
                            jsonb_object_agg(key, num_sample) as sample_counts
                        from (
                            select
                                trial_id,
                                key,
                                count(distinct cimac_id) as num_sample
                            from (
                                {generic_assay_subquery}
                                union all
                                {nanostring_subquery}
                                union all
                                {olink_subquery}
                                union all
                                {elisa_subquery}
                                union all
                                {wes_subquery}
                                union all
                                {wes_tumor_assay_subquery}
                                union all
                                {wes_analysis_subquery}
                                union all
                                {wes_tumor_only_analysis_subquery}
                                union all
                                {rna_level1_analysis_subquery}
                                union all
                                {tcr_analysis_subquery}
                                union all
                                {cytof_analysis_subquery}
                                union all
                                {atacseq_analysis_subquery}
                                union all
                                {scrnaseq_analysis_subquery}
                                union all
                                {visium_analysis_subquery}
                            ) assays_and_analysis
                            group by
                                trial_id, key
                        ) q
                        group by
                            trial_id
                    ) sample_counts
                    on expected_assays.trial_id = sample_counts.trial_id
                    full join ({excluded_samples_subquery}) excluded_sample_lists
                    on expected_assays.trial_id = excluded_sample_lists.trial_id
                    full join ({files_subquery}) file_sizes
                    on expected_assays.trial_id = file_sizes.trial_id
                    full join ({clinical_subquery}) clinical_participants
                    on expected_assays.trial_id = clinical_participants.trial_id
                    group by
                        expected_assays.trial_id,
                        total_participants,
                        total_samples,
                        sample_counts.sample_counts
                    ;
                """

        return combined_query

    @staticmethod
    @with_default_session
    def get_summaries(session: Session) -> List[dict]:
        """
        Return a list of trial summaries, where each summary has structure like:
        ```python
            {
                "trial_id": ...,
                "expected_assays": ..., # list of assays the trial should have data for
                "file_size_bytes": ..., # total file size for the trial
                "clinical_participants": ..., # number of participants with clinical data
                "total_participants": ..., # number of unique participants with assay data
                "total_samples": ..., # number of samples with assay data
                "cytof": ..., # cytof sample count
                ... # other assays and analysis
            }
        ```
        NOTE: if the metadata model for any existing assays substantially changes,
        or if new assays are introduced that don't follow the typical structure
        (batches containing sample-level records), then this method will need to
        be updated to accommodate those changes.

        Only the assays are used for calculating `"total_participants"` and `"total_samples"`,
        as all analyses are derived from assay data.
        Each assay/analysis subquery is expected to return a set with `trial_id`, `key`,
        and `cimac_id` which are used for both assay-level and overall counting.

        There is a bit of complexity with the way that WES samples are counted:
            - `"wes"` only counts tumor samples slated for paired wes_analysis
            - `"wes_tumor_only"` counts all tumor samples NOT slated for paired wes_analysis
            - `"wes_analysis"` counts tumor samples with paired wes_analysis
            - `"wes_tumor_only_analysis"` counts (tumor) samples with tumor-only analysis
        For `"total_[participants/samples]"`, ALL (ie tumor AND normal) WES assay samples are included.
        """
        summaries_query = text("SELECT result FROM trial_summaries_mv")
        # Retrieve trial-level summary results from data cached in trial_summaries_mv materialized view.
        # The source of the SQL query used in trial_summaries_mv is get_summaries_query()
        summaries = [summary for (summary,) in session.execute(summaries_query) if summary]

        # Shortcut to impute 0 values for assays where trials don't yet have data
        summaries = pd.DataFrame(summaries).fillna(0).to_dict("records")

        return summaries


class UploadJobStatus(EnumBaseClass):
    STARTED = "started"
    # Set by CLI based on GCS upload results
    UPLOAD_COMPLETED = "upload-completed"
    UPLOAD_FAILED = "upload-failed"
    # Set by ingest_UploadJobs cloud function based on merge / transfer results
    MERGE_COMPLETED = "merge-completed"
    MERGE_FAILED = "merge-failed"

    @classmethod
    def is_valid_transition(cls, current: str, target: str, is_manifest: bool = False) -> bool:
        """
        Enforce logic about which state transitions are valid. E.g.,
        an upload whose status is "merge-completed" should never be updated
        to "started".
        """
        c = cls(current)
        t = cls(target)
        upload_statuses = [cls.UPLOAD_COMPLETED, cls.UPLOAD_FAILED]
        merge_statuses = [cls.MERGE_COMPLETED, cls.MERGE_FAILED]
        if c != t:
            if t == cls.STARTED:
                return False
            if c in upload_statuses:
                if t not in merge_statuses:
                    return False
            if c in merge_statuses:
                return False
            if c == cls.STARTED and t in merge_statuses and not is_manifest:
                return False
        return True


UPLOAD_STATUSES = [s.value for s in UploadJobStatus]


class UploadJobs(CommonColumns):
    __tablename__ = "upload_jobs"
    # An upload job must contain a gcs_file_map is it isn't a manifest upload
    __table_args__ = (
        CheckConstraint("multifile = true OR gcs_file_map != null"),
        ForeignKeyConstraint(
            ["uploader_email"],
            ["users.email"],
            name="upload_jobs_uploader_email_fkey",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["trial_id"],
            ["trial_metadata.trial_id"],
            name="assay_uploads_trial_id_fkey",
        ),
    )

    # The current status of the upload job
    _status = Column("status", Enum(*UPLOAD_STATUSES, name="upload_job_status"), nullable=False)
    # A long, random identifier for this upload job
    token = Column(UUID, server_default=text("gen_random_uuid()"), nullable=False)
    # Text containing feedback on why the upload status is what it is
    status_details = Column(String, nullable=True)
    # Whether the upload contains multiple files
    multifile = Column(Boolean, nullable=False)
    # For multifile UploadJobs, object names for the files to be uploaded mapped to upload_placeholder uuids.
    # For single file UploadJobs, this field is null.
    gcs_file_map = Column(JSONB, nullable=True)
    # track the GCS URI of the .xlsx file used for this upload
    gcs_xlsx_uri = Column(String, nullable=True)
    # The parsed JSON metadata blob associated with this upload
    metadata_patch = Column(JSONB, nullable=False)
    # The type of upload (pbmc, wes, olink, wes_analysis, ...)
    upload_type = Column(String, nullable=False)
    # Link to the user who created this upload.
    uploader_email = Column(String, nullable=False)
    # The trial that this is an upload for.
    trial_id = Column(String, nullable=False, index=True)

    # Create a GIN index on the GCS object names
    _gcs_objects_idx = Index("upload_jobs_gcs_gcs_file_map_idx", gcs_file_map, postgresql_using="gin")

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, status: str):
        """Set the status if given value is valid."""
        # If old status isn't set on this instance, then this instance hasn't
        # yet been saved to the db, so default to the old status to STARTED.
        old_status = self.status or UploadJobStatus.STARTED.value
        is_manifest = self.upload_type in prism.SUPPORTED_MANIFESTS
        if not UploadJobStatus.is_valid_transition(old_status, status, is_manifest):
            raise ValueError(f"Upload job with status {self.status} can't transition to status {status}")
        self._status = status

    def _set_status_no_validation(self, status: str):
        """Set the status without performing validations."""
        assert TESTING, "status_no_validation should only be used in tests"
        self._status = status

    def alert_upload_success(self, trial: TrialMetadata):
        """Send an email notification that an upload has succeeded."""
        # Send admin notification email
        emails.new_upload_alert(self, trial.metadata_json, send_email=True)

    def upload_uris_with_data_uris_with_uuids(self):
        for upload_uri, uuid in (self.gcs_file_map or {}).items():
            # URIs in the upload bucket have a structure like (see ingestion.upload_assay)
            # [trial id]/{prismify_generated_path}/[timestamp].
            # We strip off the /[timestamp] suffix from the upload url,
            # since we don't care when this was uploaded.
            target_url = "/".join(upload_uri.split("/")[:-1])

            yield upload_uri, target_url, uuid

    @staticmethod
    @with_default_session
    def create(
        upload_type: str,
        uploader_email: str,
        gcs_file_map: dict,
        metadata: dict,
        gcs_xlsx_uri: str,
        session: Session,
        commit: bool = True,
        send_email: bool = False,
        status: UploadJobStatus = UploadJobStatus.STARTED.value,
    ):
        """Create a new upload job for the given trial metadata patch."""
        assert prism.PROTOCOL_ID_FIELD_NAME in metadata, "metadata must have a trial ID"

        is_manifest_upload = upload_type in prism.SUPPORTED_MANIFESTS
        assert gcs_file_map is not None or is_manifest_upload, "assay/analysis uploads must have a gcs_file_map"

        trial_id = metadata[prism.PROTOCOL_ID_FIELD_NAME]

        job = UploadJobs(
            multifile=not is_manifest_upload,  # manifests are single file, assay/analysis are multifile
            trial_id=trial_id,
            upload_type=upload_type,
            gcs_file_map=gcs_file_map,
            metadata_patch=metadata,
            uploader_email=uploader_email,
            gcs_xlsx_uri=gcs_xlsx_uri,
            status=status,
        )
        job.insert(session=session, commit=commit)

        if send_email:
            trial = TrialMetadata.find_by_trial_id(trial_id, session=session)
            job.alert_upload_success(trial)

        return job

    @staticmethod
    @with_default_session
    def merge_extra_metadata(job_id: int, files: dict, session: Session):
        """
        Args:
            job_id: the ID of the UploadJob to merge
            files: mapping from uuid of the artifact-to-update to metadata file-to-update-from
            session: the current session; uses default if not passed
        Returns:
            None
        Raises:
            ValueError
                if `job_id` doesn't exist or is already merged
                from prism.merge_artifact_extra_metadata
        """

        job = UploadJobs.find_by_id(job_id, session=session)

        if job is None or job.status == UploadJobStatus.MERGE_COMPLETED.value:
            raise ValueError(f"Upload job {job_id} doesn't exist or is already merged")

        logger.info("About to merge extra md to %s/%s", job.id, job.status)

        for uuid, file in files.items():
            logger.info("About to parse/merge extra md on %s", uuid)
            (
                job.metadata_patch,
                updated_artifact,
                _,
            ) = prism.merge_artifact_extra_metadata(job.metadata_patch, uuid, job.upload_type, file)
            logger.info("Updated md for %s: %s", uuid, updated_artifact.keys())

        # A workaround fix for JSON field modifications not being tracked
        # by SQLalchemy for some reason. Using MutableDict.as_mutable(JSON)
        # in the model doesn't seem to help.
        flag_modified(job, "metadata_patch")

        logger.info("Updated %s/%s patch: %s", job.id, job.status, job.metadata_patch)
        session.commit()

    @classmethod
    @with_default_session
    def find_by_id_and_email(cls, id, email, session):
        upload = super().find_by_id(id, session=session)
        if upload and upload.uploader_email != email:
            return None
        return upload

    @classmethod
    @with_default_session
    def find_first_manifest_job(cls, trial_id: str, session):
        return session.query(UploadJobs).filter_by(trial_id=trial_id, gcs_xlsx_uri="").order_by(text("id ASC")).first()

    @with_default_session
    def ingestion_success(self, trial, session: Session, commit: bool = False, send_email: bool = False):
        """Set own status to reflect successful merge and trigger email notifying CIDC admins."""
        # Do status update if the transition is valid
        if not UploadJobStatus.is_valid_transition(self.status, UploadJobStatus.MERGE_COMPLETED.value):
            raise Exception(f"Cannot declare ingestion success given current status: {self.status}")
        self.status = UploadJobStatus.MERGE_COMPLETED.value

        if commit:
            session.commit()

        if send_email:
            self.alert_upload_success(trial)


class FilesToFileGroups(BaseModel):
    """
    Mapping table between files (DownloadableFiles) and FileGroups.
    """

    __tablename__ = "files_to_file_groups"
    __table_args__ = (PrimaryKeyConstraint("file_group_id", "file_id", name="pk_files_to_file_groups"),)
    file_group_id = Column(ForeignKey("file_groups.id"), primary_key=True)
    file_id = Column(ForeignKey("downloadable_files.id"), primary_key=True)
    _created = Column(DateTime, default=func.now(), nullable=False)

    # Not currently used, but may be useful in the future.
    sort_order: int = Column(Integer)

    @with_default_session
    def insert(self, session: Session, commit: bool = True):
        """For compatibility with CommonColumns"""
        session.add(self)
        if commit:
            session.commit()


class FileGroups(CommonColumns):
    """
    Entity representing an arbitrary grouping of files.  With the current permissions
    scheme, file groups always represent groups of files within a single trial, although
    this may not be true in the future.

    File groups are currently used to restrict PACT users' access to subsets of files
    within a trial that do not correspond to assay types or facets.  In the future, we
    may use them to represent collections of data published in a given study.
    """

    __tablename__ = "file_groups"

    name: Column = Column(String, nullable=False, unique=True)
    display_name: Column = Column(String, nullable=True)
    downloadable_files = relationship(
        "DownloadableFiles",
        secondary="files_to_file_groups",
        back_populates="file_groups",
    )

    permissions = relationship("Permissions", back_populates="file_group")

    @classmethod
    @with_default_session
    def find_by_name(cls, name: str, session: Session):
        """Find the record with this name"""
        return session.query(cls).filter_by(name=name).first()


class DownloadableFiles(CommonColumns):
    """
    Store required fields from:
    https://github.com/NCI-CIDC/cidc-schemas/blob/master/cidc_schemas/schemas/artifacts/artifact_core.json
    """

    __tablename__ = "downloadable_files"
    __table_args__ = (
        ForeignKeyConstraint(
            ["trial_id"],
            ["trial_metadata.trial_id"],
            name="downloadable_files_trial_id_fkey",
        ),
    )

    file_size_bytes = Column(BigInteger, nullable=False)
    uploaded_timestamp = Column(DateTime, nullable=False)
    facet_group = Column(String, nullable=False)
    # NOTE: this column actually has type CITEXT.
    additional_metadata = Column(JSONB, nullable=False)
    # TODO rename upload_type, because we store manifests in there too.
    # NOTE: this column actually has type CITEXT.
    upload_type = Column(String, nullable=False)
    md5_hash = Column(String, nullable=True)
    crc32c_hash = Column(String, nullable=True)
    trial_id = Column(String, nullable=False)
    object_url = Column(String, nullable=False, index=True, unique=True)
    visible = Column(Boolean, default=True)

    # Would a bioinformatician likely use this file in an analysis?
    analysis_friendly = Column(Boolean, default=False)

    # Visualization data columns (should always be nullable)
    clustergrammer = Column(JSONB, nullable=True)
    ihc_combined_plot = Column(JSONB, nullable=True)

    # This fields are optional and should eventually be removed:
    # - object_url should be used instead of file_name
    # - some combo of object_url/data_category/upload_type should be
    #   used instead of data_format.
    # The columns are left as optional for short term backwards compatibility.
    file_name = Column(String, nullable=True)
    data_format = Column(String, nullable=True)

    file_groups = relationship(
        "FileGroups",
        secondary="files_to_file_groups",
        back_populates="downloadable_files",
        cascade="save-update",
    )

    FILE_EXT_REGEX = r"\.([^./]*(\.gz)?)$"

    @hybrid_property
    def file_ext(self):
        match = re.search(self.FILE_EXT_REGEX, self.object_url)
        return match.group(1) if match else None

    @file_ext.expression
    def file_ext(self):
        return func.substring(self.object_url, self.FILE_EXT_REGEX)

    @hybrid_property
    def data_category(self):
        return facet_groups_to_categories.get(self.facet_group)

    @data_category.expression
    def data_category(self):
        return DATA_CATEGORY_CASE_CLAUSE

    @hybrid_property
    def data_category_prefix(self):
        """
        The overarching data category for a file. E.g., files with `upload_type` of
        "cytof"` and `"cytof_analyis"` should both have a `data_category_prefix` of `"CyTOF"`.
        """
        if self.data_category is None:
            return None
        return self.data_category.split(FACET_NAME_DELIM, 1)[0]

    @data_category_prefix.expression
    def data_category_prefix(self):
        return func.split_part(DATA_CATEGORY_CASE_CLAUSE, FACET_NAME_DELIM, 1)

    @hybrid_property
    def file_purpose(self):
        return details_dict.get(self.facet_group).file_purpose

    @file_purpose.expression
    def file_purpose(self):
        return FILE_PURPOSE_CASE_CLAUSE

    @property
    def short_description(self):
        return details_dict.get(self.facet_group).short_description

    @property
    def long_description(self):
        return details_dict.get(self.facet_group).long_description

    @property
    def cimac_id(self):
        """
        Extract the `cimac_id` associated with this file, if any, by searching the file's
        additional metadata for a field with a key like `<some>.<path>.cimac_id`.

        NOTE: this is not a sqlalchemy hybrid_property, and it can't be used directly in queries.
        """
        for key, value in self.additional_metadata.items():
            if key.endswith("cimac_id"):
                return value
        return None

    @validates("additional_metadata")
    def check_additional_metadata_default(self, key, value):
        return {} if value in ["null", None, {}] else value

    @classmethod
    def _generate_query_objects(cls):

        # This is really unfortunate and a huge duplication of code from the column
        # definitions in this class, but it seemed to be the only way to get the
        # SQLAlchemy Expression Language API to work.
        metadata = MetaData()
        downloadable_files_for_query = Table(
            "downloadable_files",
            metadata,
            Column("_created", BigInteger, nullable=False),
            Column("_updated", DateTime, default=func.now(), nullable=False),
            Column("_etag", String(40), nullable=False),
            Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
            Column("file_size_bytes", BigInteger, nullable=False),
            Column("uploaded_timestamp", DateTime, nullable=False),
            Column("facet_group", String, nullable=False),
            Column("additional_metadata", JSONB, nullable=False),
            Column("upload_type", String, nullable=False),
            Column("md5_hash", String, nullable=True),
            Column("crc32c_hash", String, nullable=True),
            Column("trial_id", String, nullable=False),
            Column("object_url", String, nullable=False, index=True, unique=True),
            Column("visible", Boolean, default=True),
            Column("analysis_friendly", Boolean, default=False),
            Column("clustergrammer", JSONB, nullable=True),
            Column("ihc_combined_plot", JSONB, nullable=True),
            Column("file_name", String, nullable=True),
            Column("data_format", String, nullable=True),
        )

        # TODO(jcallaway): consider this reflection-based approach instead.  It doesn't
        # currently work because of the relationship()s and foreign keys, among other
        # problems.
        # columns = []
        # attributes = inspect.getmembers(CommonColumns, lambda x: not (inspect.isroutine(x)))
        # for k, v in attributes:
        #     if not(k.startswith('__') and k.endswith('__')) and isinstance(v, Column):
        #         v.name = k
        #         columns.append(v)
        # attributes = inspect.getmembers(DownloadableFiles, lambda x: not (inspect.isroutine(x)))
        # for k, v in attributes:
        #     if not (k.startswith('__') and k.endswith('__')) and isinstance(v, Column):
        #         v.name = k
        #         columns.append(v)
        # downloadable_files_for_query = Table("downloadable_files", metadata, *columns)

        files_to_file_groups_for_query = Table(
            "files_to_file_groups",
            metadata,
            Column("_created", BigInteger, nullable=False),
            Column("_updated", DateTime, default=func.now(), nullable=False),
            Column("_etag", String(40), nullable=False),
            Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
            Column("file_group_id", Integer, nullable=False),
            Column("file_id", ForeignKey("downloadable_files.id")),
        )

        return downloadable_files_for_query, files_to_file_groups_for_query

    @classmethod
    def _convert_list_results(cls, downloadable_files_for_query: Table, query_files: List):
        """Converts the results of a SQLalchemy expression language query into actual DownloadableFiles
        objects.  This is necessary since the UI depends on some of the derived properties in
        DownloadableFiles.
        """
        results = []
        for query_file in query_files:
            args = {}
            for column in downloadable_files_for_query.c:
                args[column.name] = getattr(query_file, column.name)
            results.append(DownloadableFiles(**args))

        return results

    @classmethod
    def _generate_where_clauses(
        cls,
        downloadable_files_for_query: Table,
        files_to_file_groups_for_query: Table,
        trial_ids: List[str],
        facets: List[List[str]],
        user: Users,
    ):
        """
        Returns a list of where clauses for use by list_with_permissions() and count_with_permissions().
        If the list is empty, this means to execute the query without a where clause (likely because
        the user is an admin).  If None is returned instead of a list, this means that the user has no
        permissions to view any files specified.
        """

        # From the perspective of viewing files, NCI Biobank users are admins.
        is_admin = user and (user.is_admin() or user.is_nci_user())

        where_clauses = []
        if trial_ids:
            where_clauses.append(downloadable_files_for_query.c.trial_id.in_(trial_ids))
        if facets:
            facet_groups = get_facet_groups_for_paths(facets)
            where_clauses.append(downloadable_files_for_query.c.facet_group.in_(facet_groups))

        if user and not is_admin:
            permissions = Permissions.find_for_user(user.id)
            full_trial_perms, full_type_perms = [], []
            for permission in permissions:

                # If upload_type or trial_id is null, that means to grant permissions to
                # *all* files for that upload type or trial.
                if permission.upload_type is None:
                    full_trial_perms.append(permission.trial_id)
                elif permission.trial_id is None:
                    full_type_perms.append(permission.upload_type)
                elif permission.file_group_id is None:
                    where_clauses.append(
                        sql_and(
                            (downloadable_files_for_query.c.trial_id == permission.trial_id),
                            (downloadable_files_for_query.c.upload_type == permission.upload_type),
                        )
                    )
                else:
                    where_clauses.append(
                        sql_and(
                            (downloadable_files_for_query.c.trial_id == permission.trial_id),
                            (files_to_file_groups_for_query.c.file_group_id == permission.file_group_id),
                        )
                    )

            if full_trial_perms:

                # don't include clinical_data in cross-trial permission
                where_clauses.append(
                    sql_and(
                        downloadable_files_for_query.c.trial_id.in_(full_trial_perms),
                        (downloadable_files_for_query.c.upload_type != "clinical_data"),
                    )
                )
            if full_type_perms:
                where_clauses.append(downloadable_files_for_query.c.upload_type.in_(full_type_perms))

        # Need to be careful about return logic.  Empty results could be because the user
        # is an admin, whereas None means the user has no permissions to view any files.
        if is_admin or where_clauses:
            return where_clauses

        return None

    @classmethod
    def _generate_where_clause_with_permissions(cls, user: Users) -> BooleanClauseList:
        """
        Returns a where clause for DownloadableFiles filtered down to only the files the user
        has access to based on their permissions and role.

        The generated clause will have this form
            WHERE
                downloadable_files.trial_id IN ('x', 'y', ...) AND upload_type != 'clinical_data' <- trial-level permissions
            OR
                upload_type IN ('u', 'v', ...)) <- upload-type-level permissions
            OR
                trial_id = '5' AND upload_type = 'mif' <- regular permissions
            OR
                trial_id = '6' and upload_type = 'hande'
                ...
        """
        # From the perspective of viewing files, NCI Biobank users are admins.
        if user.is_admin_or_nci_user():
            return true()  # Admin has full permissions to all

        permissions = Permissions.find_for_user(user.id)

        full_access_trial_ids = [p.trial_id for p in permissions if not p.upload_type]
        full_access_upload_types = [p.upload_type for p in permissions if not p.trial_id]
        regular_permissions = [p for p in permissions if p.trial_id and p.upload_type]

        full_access_trial_clause = sql_and(
            DownloadableFiles.trial_id.in_(full_access_trial_ids),
            DownloadableFiles.upload_type != "clinical_data",
        )

        full_access_upload_type_clause = sql_or(DownloadableFiles.upload_type.in_(full_access_upload_types))

        regular_permission_clauses = [
            sql_and(
                DownloadableFiles.trial_id == p.trial_id,
                DownloadableFiles.upload_type == p.upload_type,
            )
            for p in regular_permissions
        ]
        clause = sql_or(
            full_access_trial_clause,
            full_access_upload_type_clause,
            *regular_permission_clauses,
        )

        return clause

    @classmethod
    @with_default_session
    def list_ids(cls, session: Session, filter_: Callable[[Query], Query]):
        """List record ids in the downloadable_files table based on filter_."""
        query = session.query(cls.id)
        query = filter_(query)
        return [r[0] for r in query.all()]

    @classmethod
    @with_default_session
    def list_with_permissions(
        cls,
        session: Session,
        trial_ids: List[str] = None,
        facets: List[List[str]] = None,
        page_num: int = 0,
        page_size: int = PAGINATION_PAGE_SIZE,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        user: Users = None,
    ):
        """List records in this table, with pagination support."""
        if trial_ids is None:
            trial_ids = []

        if facets is None:
            facets = []

        (
            downloadable_files_for_query,
            files_to_file_groups_for_query,
        ) = DownloadableFiles._generate_query_objects()
        where_clauses = DownloadableFiles._generate_where_clauses(
            downloadable_files_for_query,
            files_to_file_groups_for_query,
            trial_ids,
            facets,
            user,
        )
        if where_clauses is None:

            # User doesn't have permissions to view any files; no need to issue a query.
            return {}

        if where_clauses:

            # No where clause (the user is likely an admin).
            statement = select([downloadable_files_for_query]).select_from(downloadable_files_for_query)

        else:
            statement = (
                select([downloadable_files_for_query])
                .where(sql_and(*where_clauses))
                .select_from(downloadable_files_for_query.outerjoin(files_to_file_groups_for_query))
            )

        if sort_field:
            sort_attribute = getattr(cls, sort_field)
            field_with_dir = asc(sort_attribute) if sort_direction == "asc" else desc(sort_attribute)
            statement = statement.order_by(field_with_dir)

        # Enforce positive page numbers
        page_num = 0 if page_num < 0 else page_num

        # Enforce maximum page size
        page_size = min(page_size, MAX_PAGINATION_PAGE_SIZE)
        statement = statement.limit(page_size).offset(page_num * page_size)

        return DownloadableFiles._convert_list_results(
            downloadable_files_for_query, session.execute(statement).fetchall()
        )

    @classmethod
    @with_default_session
    def count_with_permissions(
        cls,
        session: Session,
        trial_ids: List[str] = None,
        facets: List[List[str]] = None,
        # page_num: int = 0,
        # page_size: int = PAGINATION_PAGE_SIZE,
        # sort_field: Optional[str] = None,
        # sort_direction: Optional[str] = None,
        user: Users = None,
    ):
        """
        Return the total number of records that would be returned by equivalent calls to
        list_with_permissions() (disregarding results paging).
        """

        if trial_ids is None:
            trial_ids = []

        if facets is None:
            facets = []

        (
            downloadable_files_for_query,
            files_to_file_groups_for_query,
        ) = DownloadableFiles._generate_query_objects()
        where_clauses = DownloadableFiles._generate_where_clauses(
            downloadable_files_for_query,
            files_to_file_groups_for_query,
            trial_ids,
            facets,
            user,
        )
        if where_clauses is None:

            # User doesn't have permissions to view any files; no need to issue a query.
            return 0

        if where_clauses:

            # No where clause (the user is likely an admin).
            statement = select([func.count(downloadable_files_for_query.c.id)]).select_from(
                downloadable_files_for_query
            )

        else:
            statement = (
                select([func.count(downloadable_files_for_query.c.id)])
                .where(sql_and(*where_clauses))
                .select_from(downloadable_files_for_query.outerjoin(files_to_file_groups_for_query))
            )

        return session.execute(statement).fetchone()[0]

    @classmethod
    @with_default_session
    def count_by_facet_with_permissions(cls, session: Session, trial_ids: List[str] = None, user: Users = None):
        """
        Returns a map of facet_group to a count of the number of files that the given user
        has permissions to view.
        """

        if trial_ids is None:
            trial_ids = []

        (
            downloadable_files_for_query,
            files_to_file_groups_for_query,
        ) = DownloadableFiles._generate_query_objects()
        where_clauses = DownloadableFiles._generate_where_clauses(
            downloadable_files_for_query,
            files_to_file_groups_for_query,
            trial_ids,
            None,
            user,
        )
        if where_clauses is None:

            # User doesn't have permissions to view any files; no need to issue a query.
            return {}

        if not where_clauses:

            # No where clause (the user is likely an admin).
            statement = select(
                [
                    downloadable_files_for_query.c.facet_group,
                    func.count(downloadable_files_for_query.c.id),
                ]
            ).select_from(downloadable_files_for_query)

        else:
            statement = (
                select(
                    [
                        downloadable_files_for_query.c.facet_group,
                        func.count(downloadable_files_for_query.c.id),
                    ]
                )
                .where(sql_and(*where_clauses))
                .select_from(downloadable_files_for_query.outerjoin(files_to_file_groups_for_query))
            )

        statement = statement.group_by(downloadable_files_for_query.c.facet_group)
        results = session.execute(statement).fetchall()
        return dict(results)

    @classmethod
    @with_default_session
    def list_object_urls_with_permissions(
        cls, session: Session, user: Users = None, ids: Iterable[int] = None
    ) -> Iterable[str]:
        """
        Checks that the given user has access to all the files identified by ids, and returns
        the object_urls for those the user has permission for.
        """
        (
            downloadable_files_for_query,
            files_to_file_groups_for_query,
        ) = DownloadableFiles._generate_query_objects()
        where_clauses = DownloadableFiles._generate_where_clauses(
            downloadable_files_for_query,
            files_to_file_groups_for_query,
            None,
            None,
            user,
        )
        if where_clauses is None:

            # User doesn't have permissions to view any files; no need to issue a query.
            return {}

        if not where_clauses:

            # No where clause (the user is likely an admin).
            statement = (
                select([downloadable_files_for_query.c.object_url])
                .where(downloadable_files_for_query.c.id.in_(ids))
                .select_from(downloadable_files_for_query)
            )

        else:
            statement = (
                select([downloadable_files_for_query.c.object_url])
                .where(sql_and(*where_clauses, downloadable_files_for_query.c.id.in_(ids)))
                .select_from(downloadable_files_for_query.outerjoin(files_to_file_groups_for_query))
            )

        return [row[0] for row in session.execute(statement).fetchall()]

    @classmethod
    @with_default_session
    def filter_object_ids_by_permissions(cls, user: Users, ids: Iterable[int], session: Session) -> Iterable[int]:
        """
        Takes a list of object ids and filters it to return only those object ids the user has permission for.
        """

        where_clause = DownloadableFiles._generate_where_clause_with_permissions(user)
        statement = select(DownloadableFiles.id).where(sql_and(DownloadableFiles.id.in_(ids), where_clause))

        return [row[0] for row in session.execute(statement).fetchall()]

    @classmethod
    def _generate_trial_file_counts(cls, downloadable_files: Iterable) -> Dict[str, int]:
        results = defaultdict(lambda: 0)
        for downloadable_file in downloadable_files:
            if downloadable_file.data_category:
                results[downloadable_file.trial_id] = results[downloadable_file.trial_id] + 1
        return results

    @classmethod
    @with_default_session
    def remove_participants_and_samples_info_files(cls, trial_id: str, session: Session):
        """
        Remove participants info and samples info downloadable files
        """
        files_to_delete = (
            session.query(cls)
            .filter(cls.trial_id == trial_id)
            .filter(
                or_(
                    cls.upload_type == "participants info",
                    cls.upload_type == "samples info",
                )
            )
            .all()
        )

        for file in files_to_delete:
            file.delete(commit=True)
        session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY trial_summaries_mv"))

    @classmethod
    @with_default_session
    def get_trial_facets_with_permissions(
        cls, session: Session, facets: Iterable[Iterable], user: Users = None
    ) -> Dict[str, int]:
        """
        Returns a map of trial ID to count of files that the user has permissions to view.
        Files with a non-true data_category property are not included in these counts.
        """
        (
            downloadable_files_for_query,
            files_to_file_groups_for_query,
        ) = DownloadableFiles._generate_query_objects()
        where_clauses = DownloadableFiles._generate_where_clauses(
            downloadable_files_for_query,
            files_to_file_groups_for_query,
            None,
            facets,
            user,
        )
        if where_clauses is None:

            # User doesn't have permissions to view any files; no need to issue a query.
            return {}

        if not where_clauses:

            # No where clause (the user is likely an admin).
            statement = select([downloadable_files_for_query]).select_from(downloadable_files_for_query)

        else:
            statement = (
                select([downloadable_files_for_query])
                .where(sql_and(*where_clauses))
                .select_from(downloadable_files_for_query.outerjoin(files_to_file_groups_for_query))
            )

        downloadable_files = DownloadableFiles._convert_list_results(
            downloadable_files_for_query, session.execute(statement).fetchall()
        )
        trial_file_counts = DownloadableFiles._generate_trial_file_counts(downloadable_files)
        return build_trial_facets(trial_file_counts)

    @with_default_session
    def get_related_files(self, session: Session) -> list:
        """
        Return a list of file records related to this file. We could define "related"
        in any number of ways, but currently, a related file:
            * is sample-specific, and relates to the same sample as this file if this file
              has an associated `cimac_id`.
            * isn't sample-specific, and relates to the same `data_category_prefix`.
        """
        # If this file has an associated sample, get other files associated with that sample.
        # Otherwise, get other non-sample-specific files for this trial and data category.
        if self.cimac_id is not None:
            query = text(
                "SELECT DISTINCT downloadable_files.* "
                "FROM downloadable_files, LATERAL jsonb_each_text(additional_metadata) addm_kv "
                "WHERE addm_kv.value LIKE :cimac_id AND trial_id = :trial_id AND id != :id"
            )
            params = {
                "cimac_id": f"%{self.cimac_id}",
                "trial_id": self.trial_id,
                "id": self.id,
            }
            related_files = result_proxy_to_models(session.execute(query, params), DownloadableFiles)
        else:
            not_sample_specific = not_(literal_column("additional_metadata::text").like('%.cimac_id":%'))
            related_files = (
                session.query(DownloadableFiles)
                .filter(
                    DownloadableFiles.trial_id == self.trial_id,
                    DownloadableFiles.data_category_prefix == self.data_category_prefix,
                    DownloadableFiles.id != self.id,
                    not_sample_specific,
                )
                .all()
            )

        return related_files

    # this is the old file filter code which we are temporarily putting back in to make facet search work again
    # TODO use old serach code again
    @staticmethod
    def build_file_filter(
        trial_ids: List[str] = None, facets: List[List[str]] = None, user: Users = None
    ) -> Callable[[Query], Query]:
        """
        Build a file filter function based on the provided parameters. The resultant
        filter can then be passed as the `filter_` argument of `DownloadableFiles.list`
        or `DownloadableFiles.count`.
        Args:
            trial_ids: if provided, the filter will include only files with these trial IDs.
            upload_types: if provided, the filter will include only files with these upload types.
            analysis_friendly: if True, the filter will include only files that are "analysis-friendly".
            non_admin_user_id: if provided, the filter will include only files that satisfy
                this user's data access permissions.
        Returns:
            A function that adds filters to a query against the DownloadableFiles table.
        """
        if trial_ids is None:
            trial_ids = []

        if facets is None:
            facets = []

        file_filters = []
        if trial_ids:
            file_filters.append(DownloadableFiles.trial_id.in_(trial_ids))
        if facets:
            facet_groups = get_facet_groups_for_paths(facets)
            file_filters.append(DownloadableFiles.facet_group.in_(facet_groups))
        # Admins and NCI biobank users can view all files
        if user and not user.is_admin() and not user.is_nci_user():
            permissions = Permissions.find_for_user(user.id)
            full_trial_perms, full_type_perms, trial_type_perms = [], [], []
            for perm in permissions:
                if perm.upload_type is None:
                    full_trial_perms.append(perm.trial_id)
                elif perm.trial_id is None:
                    full_type_perms.append(perm.upload_type)
                else:
                    trial_type_perms.append((perm.trial_id, perm.upload_type))
            df_tuples = tuple_(DownloadableFiles.trial_id, DownloadableFiles.upload_type)
            file_filters.append(
                or_(
                    # don't include clinical_data in cross-trial permission
                    and_(
                        DownloadableFiles.trial_id.in_(full_trial_perms),
                        DownloadableFiles.upload_type != "clinical_data",
                    ),
                    DownloadableFiles.upload_type.in_(full_type_perms),
                    df_tuples.in_(trial_type_perms),
                )
            )

        def filter_files(query: Query) -> Query:
            return query.filter(*file_filters)

        return filter_files

    @staticmethod
    @with_default_session
    def create_from_metadata(
        trial_id: str,
        upload_type: str,
        file_metadata: dict,
        session: Session,
        additional_metadata: Optional[dict] = None,
        commit: bool = True,
        alert_artifact_upload: bool = False,
    ):
        """
        Create a new DownloadableFiles record from artifact metadata.
        """

        # Filter out keys that aren't columns
        supported_columns = DownloadableFiles.__table__.columns.keys()
        filtered_metadata = {
            "trial_id": trial_id,
            "upload_type": upload_type,
            "additional_metadata": additional_metadata,
        }

        # TODO maybe put non supported stuff from file_metadata to some misc jsonb column?
        for key, value in file_metadata.items():
            if key in supported_columns:
                filtered_metadata[key] = value

        etag = make_etag(filtered_metadata.values())

        object_url = filtered_metadata["object_url"]
        df = session.query(DownloadableFiles).filter_by(object_url=object_url).with_for_update().first()
        if df:
            df = session.merge(DownloadableFiles(id=df.id, _etag=etag, **filtered_metadata))
        else:
            df = DownloadableFiles(_etag=etag, **filtered_metadata)

        df.insert(session=session, commit=commit)

        if alert_artifact_upload:
            publish_artifact_upload(object_url)

        return df

    @staticmethod
    @with_default_session
    def create_from_blob(
        trial_id: str,
        upload_type: str,
        data_format: str,
        facet_group: str,
        blob: Blob,
        session: Session,
        commit: bool = True,
        alert_artifact_upload: bool = False,
    ):
        """
        Create a new DownloadableFiles record from from a GCS blob,
        or update an existing one, with the same object_url.
        """

        # trying to find existing one
        df = session.query(DownloadableFiles).filter_by(object_url=blob.name).with_for_update().first()
        if not df:
            df = DownloadableFiles()

        df.trial_id = trial_id
        df.upload_type = upload_type
        df.data_format = data_format
        df.facet_group = facet_group
        df.object_url = blob.name
        df.file_name = blob.name
        df.file_size_bytes = blob.size
        df.md5_hash = blob.md5_hash
        df.crc32c_hash = blob.crc32c
        df.uploaded_timestamp = blob.time_created

        df.insert(session=session, commit=commit)

        if alert_artifact_upload:
            publish_artifact_upload(blob.name)

        return df

    @staticmethod
    @with_default_session
    def get_by_object_url(object_url: str, session: Session):
        """
        Look up the downloadable file record associated with
        the given GCS object url.
        """
        return session.query(DownloadableFiles).filter_by(object_url=object_url).one()

    @classmethod
    @with_default_session
    def list_object_urls(cls, ids: List[int], session: Session, filter_: Callable[[Query], Query]) -> List[str]:
        """Get all object_urls for a batch of downloadable file record IDs"""
        query = session.query(cls.object_url).filter(cls.id.in_(ids))
        query = filter_(query)
        return [r[0] for r in query.all()]

    @classmethod
    def build_file_bundle_query(cls) -> Query:
        """
        Build a query that selects nested file bundles from the downloadable files table.
        The `file_bundles` query below should produce one bundle per unique `trial_id` that
        appears in the downloadable files table. Each bundle will have shape like:
        ```
          {
              <type 1>: {
                <purpose 1>: [<file id 1>, <file id 2>, ...],
                <purpose 2>: [...]
              },
              <type 2>: {...}
          }
        ```
        where "type" is something like `"Olink"` or `"Participants Info"` and "purpose" is a `FilePurpose` string.
        """
        tid_col, type_col, purp_col, ids_col, purps_col = (
            literal_column("trial_id"),
            literal_column("type"),
            literal_column("purpose"),
            literal_column("ids"),
            literal_column("purposes"),
        )

        id_bundles = (
            select(
                cls.trial_id,
                cls.data_category_prefix.label(type_col.key),
                cls.file_purpose.label(purp_col.key),
                func.json_agg(cls.id).label(ids_col.key),
            )
            .group_by(cls.trial_id, type_col, purp_col)
            .alias("id_bundles")
        )
        purpose_bundles = (
            select(
                tid_col,
                type_col,
                func.json_object_agg(func.coalesce(purp_col, "miscellaneous"), ids_col).label(purps_col.key),
            )
            .select_from(id_bundles)
            .group_by(tid_col, type_col)
            .alias("purpose_bundles")
        )
        file_bundles = (
            select(
                tid_col.label(tid_col.key),
                func.json_object_agg(func.coalesce(type_col, "other"), purps_col).label("file_bundle"),
            )
            .select_from(purpose_bundles)
            .group_by(tid_col)
            .alias("file_bundles")
        )
        return file_bundles

    @classmethod
    @with_default_session
    def get_total_bytes(cls, session: Session, filter_: Callable[[Query], Query] = lambda q: q) -> int:
        """Get the total number of bytes of data stored across all files."""
        filtered_query = filter_(session.query(func.sum(cls.file_size_bytes)))
        total_bytes = filtered_query.one()[0]
        # return int(total_bytes)
        return int(total_bytes or 0)

    @classmethod
    @with_default_session
    def get_trial_facets(cls, session: Session, filter_: Callable[[Query], Query] = lambda q: q):
        trial_file_counts = cls.count_by(
            cls.trial_id,
            session=session,
            # Apply the provided filter
            filter_=lambda q: filter_(q),
        )
        trial_facets = build_trial_facets(trial_file_counts)
        return trial_facets

    # old code to make filter search work
    # TODO fix this
    @classmethod
    @with_default_session
    def get_data_category_facets(cls, session: Session, filter_: Callable[[Query], Query] = lambda q: q):
        facet_group_file_counts = cls.count_by(cls.facet_group, session=session, filter_=filter_)
        data_category_facets = build_data_category_facets(facet_group_file_counts)
        return data_category_facets

    # new code that has been commented out to make filter search work
    # def get_data_category_facets(cls, trial_ids, user):
    #    facet_group_file_counts = DownloadableFiles.count_by_facet_with_permissions(
    #        trial_ids=trial_ids, user=user
    #    )
    #    data_category_facets = build_data_category_facets(facet_group_file_counts)
    #    return data_category_facets


# Query clause for computing a downloadable file's data category.
# Used above in the DownloadableFiles.data_category computed property.
DATA_CATEGORY_CASE_CLAUSE = case(
    *[(DownloadableFiles.facet_group == k, v) for k, v in facet_groups_to_categories.items()]
)

# Query clause for computing a downloadable file's file purpose.
# Used above in the DownloadableFiles.file_purpose computed property.
FILE_PURPOSE_CASE_CLAUSE = case(
    *[
        (DownloadableFiles.facet_group == facet_group, file_details.file_purpose)
        for facet_group, file_details in details_dict.items()
    ]
)


def result_proxy_to_models(result_proxy: ResultProxy, model: BaseModel) -> List[BaseModel]:
    """Materialize a sqlalchemy `result_proxy` iterable as a list of `model` instances"""
    return [model(**dict(row_proxy._mapping)) for row_proxy in result_proxy.all()]


@with_default_session
def upload_manifest_json(
    uploader_email: str,
    trial_id: str,
    template_type: str,
    md_patch: dict,
    session: Session,
):
    """
    Ingest manifest data from JSON.

    * Tries to load existing trial metadata blob (if fails, merge request fails; nothing saved).
    * Merges the request JSON into the trial metadata (if fails, merge request fails; nothing saved).
    * The merge request JSON is saved to `UploadJobs`.
    * The updated trial metadata object is updated in the `TrialMetadata` table.
    """
    try:
        TrialMetadata.patch_manifest(trial_id, md_patch, session=session, commit=True)
    except ValidationError as e:
        raise BadRequest(json_validation.format_validation_error(e)) from e
    except ValidationMultiError as e:
        raise BadRequest({"errors": e.args[0]}) from e

    manifest_upload = UploadJobs.create(
        upload_type=template_type,
        uploader_email=uploader_email,
        metadata=md_patch,
        gcs_xlsx_uri="",  # not saving xlsx so we won't have phi-ish stuff in it
        gcs_file_map=None,
        session=session,
        send_email=True,
        status=UploadJobStatus.MERGE_COMPLETED.value,
    )
    # Publish that a manifest upload has been received
    publish_patient_sample_update(manifest_upload.id)
    return manifest_upload.id


TRIAL_APPENDIX_A = "trial_appendix_a"
REQUEST_LETTER = "request_letter"
DETAILED_VALIDATION = "detailed_validation"
ADMIN_FILE_CATEGORIES = [TRIAL_APPENDIX_A, REQUEST_LETTER, DETAILED_VALIDATION]


class PreprocessedFiles(CommonColumns):
    __tablename__ = "preprocessed_files"
    __table_args__ = (
        ForeignKeyConstraint(
            ["job_id"],
            ["ingestion_jobs.id"],
            name="preprocessed_files_job_id_fkey",
        ),
    )

    file_name = Column(String)
    object_url = Column(String)
    job_id = Column(Integer)
    file_category = Column(String)
    uploader_email = Column(String)
    status = Column(String)
    version = Column(Integer)
    released_version = Column(String)
    error_status = Column(String)

    @staticmethod
    @with_default_session
    def create(
        file_name: str,
        object_url: str,
        file_category: str,
        uploader_email: str,
        status: str = "pending",
        job_id: int = None,
        version: int = None,
        released_version: str = None,
        session: Session = None,
    ):
        """Create and insert a new PreprocessedFiles record."""
        new_file = PreprocessedFiles(
            file_name=file_name,
            object_url=object_url,
            file_category=file_category,
            uploader_email=uploader_email,
            status=status,
            job_id=job_id,
            version=version,
            released_version=released_version,
        )
        new_file.insert(session=session)
        return new_file

    @classmethod
    @with_default_session
    def archive_current_files(cls, file_category: str, job_id: int = None, session: Session = None):
        """Update any 'current' files in the given category to 'archived'. Returns latest existing version number."""
        current_version = 0
        current_files = cls.get_files_by_category_and_status(file_category, "current", job_id=job_id, session=session)
        for file in current_files:
            file.status = "archived"
            file._updated = datetime.now()
            current_version = file.version if file.version > current_version else current_version
        session.commit()
        return current_version

    @classmethod
    @with_default_session
    def delete_pending_files_by_category(cls, file_category: str, job_id: int = None, session: Session = None):
        """Delete all pending files matching given file_category and optional job_id."""
        records = cls.get_files_by_category_and_status(file_category, "pending", job_id=job_id, session=session)
        for record in records:
            session.delete(record)
        session.commit()

    @classmethod
    @with_default_session
    def delete_files_by_category(cls, file_category: str, job_id: int = None, session: Session = None):
        """Delete all files matching a given file_category and job_id (or system files if job_id is None)."""
        query = session.query(cls).filter_by(file_category=file_category)
        query = cls.add_job_filter(query, job_id)
        records = query.all()
        if not records:
            return False
        for record in records:
            session.delete(record)
        session.commit()
        return True

    @classmethod
    @with_default_session
    def get_files_by_category_and_status(
        cls, file_category: str, status: str, job_id: int = None, session: Session = None
    ) -> list["PreprocessedFiles"]:
        """Return all files matching file_category and status, with job_id filter (job_id is NULL if not provided)."""
        query = session.query(cls).filter_by(file_category=file_category, status=status)
        query = cls.add_job_filter(query, job_id)
        return query.all()

    @classmethod
    @with_default_session
    def get_file_by_category_and_version(
        cls, file_category: str, version: int, session: Session = None
    ) -> Optional["PreprocessedFiles"]:
        """Return the file matching the given category and version number."""
        return session.query(cls).filter_by(file_category=file_category, version=version).one_or_none()

    @classmethod
    @with_default_session
    def get_system_reference_files(cls, status: str = "current", session: Session = None) -> list["PreprocessedFiles"]:
        """Return static reference files that are not linked to any job and not Master Appendix A."""
        return (
            session.query(cls)
            .filter(cls.job_id.is_(None))
            .filter(cls.file_category != "master_appendix_a")
            .filter_by(status=status)
            .all()
        )

    @classmethod
    @with_default_session
    def get_latest_non_admin_files(cls, job_id: int, session: Session) -> list["PreprocessedFiles"]:
        """Return the most recently uploaded file for each non-admin file category for the given job_id."""
        # Subquery to get latest _created per file_category
        latest_subquery = (
            session.query(cls.file_category, func.max(cls._created).label("latest_created"))
            .filter(cls.job_id == job_id, cls.file_category.notin_(ADMIN_FILE_CATEGORIES))
            .group_by(cls.file_category)
            .subquery()
        )
        # Join main table on file_category and latest _created to get full records of latest files
        latest_files = (
            session.query(cls)
            .join(
                latest_subquery,
                (cls.file_category == latest_subquery.c.file_category)
                & (cls._created == latest_subquery.c.latest_created),
            )
            .all()
        )
        return latest_files

    @classmethod
    def add_job_filter(cls, query, job_id):
        """
        Add a job_id filter to the SQLAlchemy query:
        - If job_id is provided, filters for exact match.
        - If not, filters for system-wide files (where job_id IS NULL).
        """
        if job_id is not None:
            return query.filter_by(job_id=job_id)

        return query.filter(cls.job_id.is_(None))


INGESTION_JOB_STATUSES = [
    "DRAFT",
    "INITIAL SUBMISSION",
    "VALIDATION REVIEW",
    "REVISION SUBMISSION",
    "INGESTION",
    "PUBLISHED",
]

# Business decision to pass hex codes from the backend though that should be done by the front end...
INGESTION_JOB_COLORS = {
    "DRAFT": "",
    "INITIAL SUBMISSION": "#ACCAD7",
    "VALIDATION REVIEW": "#DABE90",
    "REVISION SUBMISSION": "#C8BAE5",
    "INGESTION": "#8FCEC7",
    "PUBLISHED": "#90D9E6",
}
# TODO If have "CANCELLED" concept or other final status, add here
FINAL_JOB_STATUS = ["PUBLISHED"]
TRIAL_APPENDIX_A_CELL_THAT_ENDS_THE_HEADER = "Data Category"


class IngestionJobs(CommonColumns):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["trial_id"],
            ["trial_metadata.trial_id"],
            name="ingestion_jobs_trial_id_fkey",
        ),
    )

    status = Column("status", Enum(*INGESTION_JOB_STATUSES, name="status"), nullable=False)
    trial_id = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    pending = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime, nullable=True)
    error_status = Column(String, nullable=True)

    @staticmethod
    @with_default_session
    def create(trial_id: str, status: str, version: int, pending: Boolean = False, session: Session = None):
        new_job = IngestionJobs(trial_id=trial_id, status=status, version=version, pending=pending)
        new_job.insert(session=session)
        return new_job

    @with_default_session
    def transition_status(self, status: str, session: Session):
        # create required categories after opening job for submission
        if self.status == "DRAFT" and status == "INITIAL SUBMISSION":
            for category in self.derive_required_categories_from_appendix_a():
                JobFileCategories.create(category=category, job_id=self.id, type="required")
        self.status = status
        self.update(session=session)

    def derive_required_categories_from_appendix_a(self) -> List:
        appendix_a = PreprocessedFiles.get_files_by_category_and_status(TRIAL_APPENDIX_A, "current", job_id=self.id)[0]
        df = gcs_xlsx_or_csv_file_to_pandas_dataframe(GOOGLE_CLINICAL_DATA_BUCKET, appendix_a.object_url)
        categories = []
        headers_ended = False
        for _index, row in df.iterrows():
            cell = str(row.iloc[0])
            if headers_ended:
                if cell != "nan" and cell not in categories:
                    categories.append(cell)
            elif cell.lower() == TRIAL_APPENDIX_A_CELL_THAT_ENDS_THE_HEADER.lower():
                headers_ended = True
        if "data_dictionary" not in categories:
            # Ensure Data_Dictionary is always a required file category
            categories.append("data_dictionary")
        return categories

    @classmethod
    @with_default_session
    def atomic_set_job_as_pending(cls, job_id: int, session: Session) -> Boolean:
        # Preventing rare race condition where multiple people try and submit a job for validation
        result = bool(
            session.execute(
                update(IngestionJobs)
                .where(and_(IngestionJobs.id == job_id, IngestionJobs.pending == False))
                .values(pending=True)
            ).rowcount
        )
        session.commit()
        return result

    @classmethod
    @with_default_session
    def get_jobs_by_trial(cls, trial_id: str, session: Session = None) -> list["IngestionJobs"]:
        return session.query(cls).filter(cls.trial_id == trial_id).order_by(cls.version.desc()).all()

    @classmethod
    @with_default_session
    def get_open_job_by_trial(cls, trial_id: str, session: Session = None) -> Optional["IngestionJobs"]:
        """Return the open job for a given trial if it exists."""
        return (
            session.query(cls)
            .filter(
                cls.trial_id == trial_id,
                cls.status.notin_(FINAL_JOB_STATUS),
            )
            .order_by(cls._created.desc())
            .first()
        )

    @classmethod
    @with_default_session
    def get_open_jobs_for_user(cls, user: Users, session: Session = None) -> list["IngestionJobs"]:
        if user.role not in [CIDCRole.ADMIN.value, CIDCRole.CLINICAL_TRIAL_USER.value]:
            return []
        job_query = session.query(cls).filter(cls.status.notin_(["DRAFT"]))
        if (
            user.role != CIDCRole.ADMIN.value
            and not session.query(Permissions)
            .filter(
                Permissions.granted_to_user == user.id,
                Permissions.upload_type == "clinical_upload",
                Permissions.trial_id == Permissions.EVERY,
            )
            .all()
        ):
            authorized_trials = (
                session.query(Permissions)
                .filter(
                    Permissions.granted_to_user == user.id,
                    Permissions.upload_type == "clinical_upload",
                    Permissions.trial_id != Permissions.EVERY,
                )
                .all()
            )
            job_query = job_query.filter(cls.trial_id.in_(map(lambda x: x.trial_id, authorized_trials)))
        return job_query.order_by(cls._created.desc()).all()


class JobFileCategories(CommonColumns):
    __tablename__ = "job_file_categories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["job_id"],
            ["ingestion_jobs.id"],
        ),
        Index(
            "idx_categories_job_id" "job_id",
            "category",
            unique=True,
        ),
    )

    category = Column(String)
    job_id = Column(Integer)
    type = Column(Enum("required", "optional", name="type"))

    @staticmethod
    @with_default_session
    def create(
        category: str,
        job_id: int,
        type: str,
        session: Session = None,
    ):
        new_category = JobFileCategories(
            category=category,
            job_id=job_id,
            type=type,
        )
        new_category.insert(session=session)
        return new_category

    @classmethod
    @with_default_session
    def categories_for_job(cls, job_id: int, type: str, session: Session = None):
        categories = session.query(cls).filter(cls.job_id == job_id, cls.type == type).all()
        return [c.category for c in categories]


class FileValidationErrors(CommonColumns):
    __tablename__ = "file_validation_errors"
    __table_args__ = (
        ForeignKeyConstraint(
            ["job_id"],
            ["ingestion_jobs.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["file_id"],
            ["preprocessed_files.id"],
            ondelete="CASCADE",
        ),
    )

    error_message = Column(String, nullable=False)
    location = Column(String, nullable=True)
    job_id = Column(Integer, nullable=False)
    file_id = Column(Integer, nullable=False)

    @staticmethod
    @with_default_session
    def create(file_id: int, job_id: int, error_message: str, location: str = None, session: Session = None):
        new_error = FileValidationErrors(file_id=file_id, job_id=job_id, error_message=error_message, location=location)
        new_error.insert(session=session)
        return new_error

    @classmethod
    @with_default_session
    def delete_by_file_ids(cls, file_ids: list[int], session: Session = None):
        """Delete all validation errors for the given list of file_ids."""
        if file_ids:
            session.query(cls).filter(cls.file_id.in_(file_ids)).delete(synchronize_session=False)
            session.commit()

    @classmethod
    @with_default_session
    def get_errors_for_job_sorted_by_file_id(cls, job_id: int, session: Session = None) -> list["FileValidationErrors"]:
        errors = (
            session.query(cls)
            .join(PreprocessedFiles)
            .filter(PreprocessedFiles.status == "current")
            .filter(cls.job_id == job_id)
            .order_by(cls.file_id.asc())
            .all()
        )

        return errors


class ValidationConfigs(CommonColumns):
    __tablename__ = "validation_configs"

    data_element = Column(String, nullable=True)
    validation = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True, server_default="true")

    @classmethod
    @with_default_session
    def get_active_configs_by_scope(cls, scope: str, session=None) -> list["ValidationConfigs"]:
        """Return all active ValidationConfigs rows for the given scope."""
        return session.query(cls).filter(cls.scope == scope, cls.active.is_(True)).all()
