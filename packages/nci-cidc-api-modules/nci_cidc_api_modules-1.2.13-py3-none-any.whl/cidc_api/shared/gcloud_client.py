"""Utilities for interacting with the Google Cloud Platform APIs."""

# pylint: disable=logging-fstring-interpolation

import base64
import datetime
import hashlib
import io
import json
import os
import warnings
from collections import namedtuple
from concurrent.futures import Future
from os import environ
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import googleapiclient.discovery
import pandas as pd
import requests
from cidc_schemas.prism.constants import ASSAY_TO_FILEPATH
from google.api_core.client_options import ClientOptions
from google.api_core.iam import Policy
from google.cloud import storage, pubsub, bigquery
from google.cloud.bigquery.enums import EntityTypes
from google.oauth2.service_account import Credentials
from sqlalchemy.orm.session import Session
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from cidc_api.config.secrets import get_secrets_manager
from ..config.logging import get_logger
from ..config.settings import (
    DEV_USE_GCS,
    GOOGLE_INTAKE_ROLE,
    GOOGLE_INTAKE_BUCKET,
    GOOGLE_UPLOAD_ROLE,
    GOOGLE_UPLOAD_BUCKET,
    GOOGLE_UPLOAD_TOPIC,
    GOOGLE_ACL_DATA_BUCKET,
    GOOGLE_LISTER_ROLE,
    GOOGLE_BIGQUERY_USER_ROLE,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_EMAILS_TOPIC,
    GOOGLE_PATIENT_SAMPLE_TOPIC,
    GOOGLE_ARTIFACT_UPLOAD_TOPIC,
    GOOGLE_GRANT_DOWNLOAD_PERMISSIONS_TOPIC,
    GOOGLE_HL_CLINICAL_VALIDATION_TOPIC,
    GOOGLE_DL_CLINICAL_VALIDATION_TOPIC,
    TESTING,
    ENV,
    IS_EMAIL_ON,
    DEV_CFUNCTIONS_SERVER,
    INACTIVE_USER_DAYS,
)

os.environ["TZ"] = "UTC"
logger = get_logger(__name__)

TIMEOUT_IN_SECONDS = 20

# these should be initialized here or used as cached values
STORAGE_CLIENT = None
BIGQUERY_CLIENT = None
CRM_SERVICE = None

# The Secret Manager object should only be initiated once and reused.
# This is due to the fact that every time this object is initiated, a
# Google Cloud client is also initiated, which is an expensive handshake
# that significantly adds to the latency of the script.
SECRET_MANAGER = get_secrets_manager(TESTING)


def _get_storage_client() -> storage.Client:
    global STORAGE_CLIENT
    if STORAGE_CLIENT is None:
        logger.debug("Getting local client")
        if os.environ.get("DEV_GOOGLE_STORAGE", None):
            client_options = ClientOptions(api_endpoint=os.environ.get("DEV_GOOGLE_STORAGE"))
            credentials = Credentials.from_service_account_info(
                json.loads(SECRET_MANAGER.get("APP_ENGINE_CREDENTIALS"))
            )
            STORAGE_CLIENT = storage.Client(client_options=client_options, credentials=credentials)
            logger.debug(f"Local client set to {STORAGE_CLIENT}")
            return STORAGE_CLIENT

        return _get_storage_client2()

    return STORAGE_CLIENT


def _get_storage_client2() -> storage.Client:
    """
    the project which the client acts on behalf of falls back to the default inferred from the environment
    see: https://googleapis.dev/python/storage/latest/client.html#google.cloud.storage.client.Client

    directly providing service account credentials for signing in get_signed_url() below
    """
    global STORAGE_CLIENT
    if STORAGE_CLIENT is None:
        credentials = Credentials.from_service_account_info(
            json.loads(SECRET_MANAGER.get(environ.get("APP_ENGINE_CREDENTIALS_ID")))
        )
        # client_options = ClientOptions(api_endpoint=os.environ.get("DEV_GOOGLE_STORAGE"))
        # STORAGE_CLIENT = storage.Client(client_options=client_options, credentials=credentials)
        STORAGE_CLIENT = storage.Client(credentials=credentials)
    return STORAGE_CLIENT


def _get_crm_service() -> googleapiclient.discovery.Resource:
    """
    Initializes a Cloud Resource Manager service.
    """
    global CRM_SERVICE
    if CRM_SERVICE is None:
        credentials = Credentials.from_service_account_info(
            json.loads(SECRET_MANAGER.get(environ.get("APP_ENGINE_CREDENTIALS_ID")))
        )
        CRM_SERVICE = googleapiclient.discovery.build("cloudresourcemanager", "v1", credentials=credentials)
    return CRM_SERVICE


def _get_bucket(bucket_name: str) -> storage.Bucket:
    """
    Get the bucket with name `bucket_name` from GCS.
    This does not make an HTTP request; it simply instantiates a bucket object owned by STORAGE_CLIENT.
    see: https://googleapis.dev/python/storage/latest/client.html#google.cloud.storage.client.Client.bucket
    """
    storage_client = _get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    return bucket


def _get_project_policy() -> Policy:
    """
    Get the project policy.
    """
    crm_service = _get_crm_service()
    policy = (
        crm_service.projects()
        .getIamPolicy(
            resource=GOOGLE_CLOUD_PROJECT,
            body={},
        )
        .execute()
    )
    return policy


def _get_bigquery_dataset(dataset_id: str) -> bigquery.Dataset:
    """
    Get the bigquery dataset with the id 'dataset_id'.
    makes an API request to pull this with the bigquery client
    """
    global BIGQUERY_CLIENT
    if BIGQUERY_CLIENT is None:
        credentials = Credentials.from_service_account_info(
            json.loads(SECRET_MANAGER.get(environ.get("APP_ENGINE_CREDENTIALS_ID")))
        )
        # client_options = ClientOptions(api_endpoint=os.environ.get("DEV_GOOGLE_BIGQUERY"))
        # BIGQUERY_CLIENT = bigquery.Client(client_options=client_options, credentials=credentials)
        BIGQUERY_CLIENT = bigquery.Client(credentials=credentials)

    dataset = BIGQUERY_CLIENT.get_dataset(dataset_id)  # Make an API request.

    return dataset


XLSX_GCS_URI_FORMAT = "{trial_id}/xlsx/{template_category}/{template_type}/{upload_moment}.xlsx"


PseudoBblob = namedtuple("_pseudo_blob", ["name", "size", "md5_hash", "crc32c", "time_created"])


def upload_xlsx_to_gcs(
    trial_id: str,
    template_category: str,
    template_type: str,
    filebytes: BinaryIO,
    upload_moment: str,
) -> storage.Blob:
    """
    Upload an xlsx template file to GOOGLE_ACL_DATA_BUCKET, returning the object URI.

    `template_category` is either "manifests" or "assays".
    `template_type` is an assay or manifest type, like "wes" or "pbmc" respectively.

    Returns:
        arg1: GCS blob object
    """
    blob_name = XLSX_GCS_URI_FORMAT.format(
        trial_id=trial_id,
        template_category=template_category,
        template_type=template_type,
        upload_moment=upload_moment,
    )

    if ENV == "dev" and not DEV_USE_GCS:
        logger.info(f"Would've saved {blob_name} to {GOOGLE_UPLOAD_BUCKET} and {GOOGLE_ACL_DATA_BUCKET}")
        return PseudoBblob(blob_name, 0, "_pseudo_md5_hash", "_pseudo_crc32c", upload_moment)

    upload_bucket: storage.Bucket = _get_bucket(GOOGLE_UPLOAD_BUCKET)
    blob = upload_bucket.blob(blob_name)

    filebytes.seek(0)
    blob.upload_from_file(filebytes)

    data_bucket = _get_bucket(GOOGLE_ACL_DATA_BUCKET)
    final_object = upload_bucket.copy_blob(blob, data_bucket)

    return final_object


def upload_file_to_gcs(file: FileStorage, bucket_name: str, gcs_folder: str, append_timestamp: bool = False) -> str:
    """Upload a file to the specified GCS folder and return the GCS path from the bucket."""
    # Secure the filename and prepare file
    filename = secure_filename(file.filename)
    if append_timestamp:
        filename = _append_iso_timestamp_to_filename(filename)
    gcs_file_path = os.path.join(gcs_folder, filename)
    binary_file = io.BytesIO(file.read())

    if ENV == "dev" and not DEV_USE_GCS:
        logger.info(f"Would've saved {gcs_file_path} to {bucket_name}")
        return gcs_file_path

    # Upload to GCS
    blob = _get_bucket(bucket_name).blob(gcs_file_path)
    blob.upload_from_file(binary_file, content_type=file.content_type)

    return gcs_file_path


def move_gcs_file(bucket_name: str, existing_path: str, to_folder: str, append_timestamp: bool = True) -> str:
    """Move a file within a GCS bucket to a new folder, optionally appending a timestamp to the filename."""
    filename = os.path.basename(existing_path)
    if append_timestamp:
        filename = _append_iso_timestamp_to_filename(filename)
    # Ensure trailing slash on folder
    if not to_folder.endswith("/"):
        to_folder += "/"
    new_gcs_file_path = f"{to_folder}{filename}"

    if ENV == "dev" and not DEV_USE_GCS:
        logger.info(f"Would've moved {existing_path} to {new_gcs_file_path} in {bucket_name}")
        return new_gcs_file_path

    bucket = _get_bucket(bucket_name)
    source_blob = bucket.blob(existing_path)
    if not source_blob.exists():
        raise Exception("Expected file not found in GCS")
    new_blob = bucket.blob(new_gcs_file_path)
    # GCS move = rewrite + delete
    new_blob.rewrite(source_blob)
    source_blob.delete()

    return new_gcs_file_path


def delete_items_from_folder(bucket_name: str, folder: str):
    """Deletes all blobs from the specified folder in the specified bucket."""
    if ENV == "dev" and not DEV_USE_GCS:
        logger.info(f"Would've deleted file(s) from {folder} in {bucket_name}")
        return
    bucket = _get_bucket(bucket_name)
    existing_blobs = bucket.list_blobs(prefix=folder)
    for blob in existing_blobs:
        blob.delete()


def _append_iso_timestamp_to_filename(filename: str) -> str:
    """Append an ISO 8601 timestamp to a filename, preserving its extension."""
    base, ext = os.path.splitext(filename)
    timestamp = datetime.datetime.now().isoformat(timespec="milliseconds").replace(":", "-")
    return f"{base}_{timestamp}{ext}"


def grant_lister_access(user_email: str) -> None:
    """
    Grant a user list access to the GOOGLE_ACL_DATA_BUCKET. List access is
    required for the user to download or read objects from this bucket.
    As lister is an IAM permission on an ACL-controlled bucket, can't have conditions.
    """
    logger.info(f"granting list to {user_email}")
    bucket = _get_bucket(GOOGLE_ACL_DATA_BUCKET)
    grant_storage_iam_access(bucket, GOOGLE_LISTER_ROLE, user_email, expiring=False)


def revoke_lister_access(user_email: str) -> None:
    """
    Revoke a user's list access to the GOOGLE_ACL_DATA_BUCKET. List access is
    required for the user to download or read objects from this bucket.
    Unlike grant_lister_access, revoking doesn't care if the binding is expiring or not so we don't need to specify.
    """
    logger.info(f"revoking list to {user_email}")
    bucket = _get_bucket(GOOGLE_ACL_DATA_BUCKET)
    revoke_storage_iam_access(bucket, GOOGLE_LISTER_ROLE, user_email)


def grant_upload_access(user_email: str) -> None:
    """
    Grant a user upload access to the GOOGLE_UPLOAD_BUCKET. Upload access
    means a user can write objects to the bucket but cannot delete,
    overwrite, or read objects from this bucket.
    Non-expiring as GOOGLE_UPLOAD_BUCKET is subject to ACL.
    """
    logger.info(f"granting upload to {user_email}")
    bucket = _get_bucket(GOOGLE_UPLOAD_BUCKET)
    grant_storage_iam_access(bucket, GOOGLE_UPLOAD_ROLE, user_email, expiring=False)


def revoke_upload_access(user_email: str) -> None:
    """
    Revoke a user's upload access from GOOGLE_UPLOAD_BUCKET.
    """
    logger.info(f"revoking upload from {user_email}")
    bucket = _get_bucket(GOOGLE_UPLOAD_BUCKET)
    revoke_storage_iam_access(bucket, GOOGLE_UPLOAD_ROLE, user_email)


def grant_bigquery_access(user_emails: List[str]) -> None:
    """
    Grant a user's access to run bigquery queries on project.
    Grant access to public level bigquery tables.
    """
    logger.info(f"granting bigquery access to {user_emails}")
    policy = _get_project_policy()
    grant_bigquery_iam_access(policy, user_emails)


def revoke_bigquery_access(user_email: str) -> None:
    """
    Revoke a user's access to run bigquery queries on project.
    Revoke access to public level bigquery tables.
    """
    logger.info(f"revoking bigquery access from {user_email}")
    policy = _get_project_policy()
    revoke_bigquery_iam_access(policy, user_email)


def get_intake_bucket_name(user_email: str) -> str:
    """
    Get the name for an intake bucket associated with the given user.
    Bucket names will have a structure like GOOGLE_INTAKE_BUCKET-<hash>
    """
    # 10 characters should be plenty, given that we only expect
    # a handful of unique data uploaders - we get 16^10 possible hashes.
    email_hash = hashlib.sha1(bytes(user_email, "utf-8")).hexdigest()[:10]
    bucket_name = f"{GOOGLE_INTAKE_BUCKET}-{email_hash}"
    return bucket_name


def create_intake_bucket(user_email: str) -> storage.Bucket:
    """
    Create a new data intake bucket for this user, or get the existing one.
    Grant the user GCS object admin permissions on the bucket, or refresh those
    permissions if they've already been granted.
    Created with uniform bucket-level IAM access, so expiring permission.
    """
    storage_client = _get_storage_client()
    bucket_name = get_intake_bucket_name(user_email)
    bucket = storage_client.bucket(bucket_name)

    if not bucket.exists():
        # Create a new bucket with bucket-level permissions enabled.
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket = storage_client.create_bucket(bucket)

    # Grant the user appropriate permissions
    grant_storage_iam_access(bucket, GOOGLE_INTAKE_ROLE, user_email)

    return bucket


def refresh_intake_access(user_email: str) -> None:
    """
    Re-grant a user's access to their intake bucket if it exists.
    """
    bucket_name = get_intake_bucket_name(user_email)
    bucket = _get_bucket(bucket_name)

    if bucket.exists():
        grant_storage_iam_access(bucket, GOOGLE_INTAKE_ROLE, user_email)


def revoke_intake_access(user_email: str) -> None:
    """
    Re-grant a user's access to their intake bucket if it exists.
    """
    bucket_name = get_intake_bucket_name(user_email)
    bucket = _get_bucket(bucket_name)

    if bucket.exists():
        revoke_storage_iam_access(bucket, GOOGLE_INTAKE_ROLE, user_email)


def upload_xlsx_to_intake_bucket(user_email: str, trial_id: str, upload_type: str, xlsx: FileStorage) -> str:
    """
    Upload a metadata spreadsheet file to the GCS intake bucket,
    returning the URL to the bucket in the GCP console.
    """
    # add a timestamp to the metadata file name to avoid overwriting previous versions
    filename_with_ts = f'{xlsx.filename.rsplit(".xlsx", 1)[0]}_{datetime.datetime.now().isoformat()}.xlsx'
    blob_name = f"{trial_id}/{upload_type}/metadata/{filename_with_ts}"

    # upload the metadata spreadsheet to the intake bucket
    bucket_name = get_intake_bucket_name(user_email)
    bucket = _get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(xlsx)

    return f"https://console.cloud.google.com/storage/browser/_details/{bucket_name}/{blob_name}"


def gcs_xlsx_or_csv_file_to_pandas_dataframe(bucket_name: str, blob_name: str):
    """Reads an XLSX or CSV file from Google Cloud Storage into a Pandas DataFrame."""
    temp_file = get_file_bytes_from_gcs(bucket_name, blob_name)

    # TODO: specify sheet in xlsx file and/or accept tsv and xls files
    if blob_name[-3:] == "csv":
        return pd.read_csv(temp_file)
    elif blob_name[-4:] == "xlsx":
        return pd.read_excel(temp_file)
    else:
        raise Exception("Can only read csv or xlsx files")


def get_file_bytes_from_gcs(bucket_name: str, blob_name: str) -> io.BytesIO:
    """Reads a file from Google Cloud Storage and returns it as BytesIO."""
    sheet_data = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
    return io.BytesIO(sheet_data)


def _execute_multiblob_acl_change(
    user_email_list: List[str],
    blob_list: List[storage.Blob],
    callback_fn: Callable[[storage.acl._ACLEntity], None],
) -> None:
    """
    Spools out each blob and each user with saving the blob.
    callback_fn is called on each blob / user to make the changes in permissions there.
        See see https://googleapis.dev/python/storage/latest/acl.html
    After processing all of the users for each blob, blob.acl.save() is called.

    Parameters
    ----------
    user_email_list : List[str]
    blob_list: List[google.cloud.storage.Blob]
        used to generate blob / user ACL entries
    callback_fun : Callable[google.cloud.storage.acl._ACLEntity]
        each blob / user ACL entry is passed in turn
    """
    for blob in blob_list:
        for user_email in user_email_list:
            blob_user = blob.acl.user(user_email)
            callback_fn(blob_user)

        blob.acl.save()


def get_blob_names(
    trial_id: Optional[str],
    upload_type: Optional[Tuple[str]],
    session: Optional[Session] = None,
) -> Set[str]:
    """session only needed if trial_id is None"""
    prefixes: Set[str] = _build_trial_upload_prefixes(trial_id, upload_type, session=session)

    # https://googleapis.dev/python/storage/latest/client.html#google.cloud.storage.client.Client.list_blobs
    blob_list = []
    storage_client = _get_storage_client()
    for prefix in prefixes:
        blob_list.extend(storage_client.list_blobs(GOOGLE_ACL_DATA_BUCKET, prefix=prefix))
    return {blob.name for blob in blob_list}


def grant_download_access_to_blob_names(
    user_email_list: List[str],
    blob_name_list: List[str],
) -> None:
    """
    Using ACL, grant download access to all blobs given to the user(s) given.
    """
    bucket = _get_bucket(GOOGLE_ACL_DATA_BUCKET)
    blob_list = [bucket.get_blob(name) for name in blob_name_list]

    if isinstance(user_email_list, str):
        user_email_list = [user_email_list]

    _execute_multiblob_acl_change(
        user_email_list=user_email_list,
        blob_list=blob_list,
        callback_fn=lambda obj: obj.grant_read(),
    )


def grant_download_access(
    user_email_list: Union[List[str], str],
    trial_id: Optional[str],
    upload_type: Optional[Union[str, List[str]]],
) -> None:
    """
    Gives users download access to all objects in a trial of a particular upload type.

    If trial_id is None, then grant access to all trials.
    If upload_type is None, then grant access to all upload_types.
    if user_email_list is []. then CFn loads users from db table.

    If the user already has download access for this trial and upload type, idempotent.
    Download access is controlled by IAM on production and ACL elsewhere.
    """
    user_email_list = [user_email_list] if isinstance(user_email_list, str) else user_email_list

    logger.info(f"Granting download access on trial {trial_id} upload {upload_type} to {user_email_list}")

    # ---- Handle through main grant permissions topic ----
    # would time out in CFn
    kwargs = {
        "trial_id": trial_id,
        "upload_type": upload_type,
        "user_email_list": user_email_list,
        "revoke": False,
    }
    report = _encode_and_publish(str(kwargs), GOOGLE_GRANT_DOWNLOAD_PERMISSIONS_TOPIC)
    # Wait for response from pub/sub
    if report:
        report.result()


def revoke_download_access_from_blob_names(
    user_email_list: List[str],
    blob_name_list: List[str],
) -> None:
    """
    Using ACL, grant download access to all blobs given to the users given.
    """
    bucket = _get_bucket(GOOGLE_ACL_DATA_BUCKET)
    blob_list = [bucket.get_blob(name) for name in blob_name_list]

    def revoke(blob_user: storage.acl._ACLEntity):
        blob_user.revoke_owner()
        blob_user.revoke_write()
        blob_user.revoke_read()

    _execute_multiblob_acl_change(
        blob_list=blob_list,
        callback_fn=revoke,
        user_email_list=user_email_list,
    )


def revoke_download_access(
    user_email_list: Union[str, List[str]],
    trial_id: Optional[str],
    upload_type: Optional[Union[str, List[str]]],
) -> None:
    """
    Revoke users' download access to all objects in a trial of a particular upload type.

    If trial_id is None, then revoke access to all trials.
    If upload_type is None, then revoke access to all upload_types.
    if user_email_list is []. then CFn loads users from db table.

    Return the GCS URIs from which access has been revoked.
    Download access is controlled by ACL.
    """

    user_email_list = [user_email_list] if isinstance(user_email_list, str) else user_email_list
    logger.info(f"Revoking download access on trial {trial_id} upload {upload_type} from {user_email_list}")

    # ---- Handle through main grant permissions topic ----
    # would timeout in cloud function
    kwargs = {
        "trial_id": trial_id,
        "upload_type": upload_type,
        "user_email_list": user_email_list,
        "revoke": True,
    }
    report = _encode_and_publish(str(kwargs), GOOGLE_GRANT_DOWNLOAD_PERMISSIONS_TOPIC)
    # Wait for response from pub/sub
    if report:
        report.result()


def _build_trial_upload_prefixes(
    trial_id: Optional[str],
    upload_type: Optional[Tuple[Optional[str]]],
    session: Optional[Session] = None,
) -> Set[str]:
    """
    Build the set of prefixes associated with the trial_id and upload_type
    If no trial_id is given, all trials are used.
    If no upload_type is given, the prefixes are everything but clinical_data.
        If upload_type has no files, returns empty set.
        if None in upload_type, it's treated the same as bare None
    If neither are given, an empty set is returned.

    session is only used with trial_id is None and upload_type is not None
    """
    if trial_id is None and (upload_type is None or None in upload_type):
        return set()

    trial_set: Set[str] = set()
    upload_set: Set[str] = set()
    if not trial_id:
        from ..models.models import TrialMetadata

        trial_set = {str(t.trial_id) for t in session.query(TrialMetadata).add_columns(TrialMetadata.trial_id)}

    else:
        trial_set = set([trial_id])

    if not upload_type or None in upload_type:
        upload_set = {upload_name for upload_name in ASSAY_TO_FILEPATH.keys() if upload_name != "clinical_data"}
    else:
        upload_set = set(upload_type)

    ret: Set[str] = set()
    for trial in trial_set:
        for upload in upload_set:
            if upload_type:
                if upload in ASSAY_TO_FILEPATH:
                    ret.add(f"{trial}/{ASSAY_TO_FILEPATH[upload]}")
            else:  # null means cross-assay
                # don't affect clinical_data
                ret = ret.union(
                    {
                        f"{trial}/{upload_prefix}"
                        for trial in trial_set
                        for upload_name, upload_prefix in ASSAY_TO_FILEPATH.items()
                        if upload_name != "clinical_data"
                    }
                )

    return ret


def grant_storage_iam_access(
    bucket: storage.Bucket,
    role: str,
    user_email: str,
    expiring: bool = True,
) -> None:
    """
    Grant `user_email` the provided IAM `role` on a storage `bucket`.
    Default assumes `bucket` is IAM controlled and should expire after `INACTIVE_USER_DAYS` days have elapsed.
    Set `expiring` to False for IAM permissions on ACL-controlled buckets.
    """
    # see https://cloud.google.com/storage/docs/access-control/using-iam-permissions#code-samples_3
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.version = 3

    # remove the existing binding if one exists so that we can recreate it with an updated TTL.
    _find_and_pop_storage_iam_binding(policy, role, user_email)

    if not expiring:
        # special value -1 for non-expiring
        binding = _build_storage_iam_binding(bucket.name, role, user_email, ttl_days=-1)
    else:
        binding = _build_storage_iam_binding(bucket.name, role, user_email)  # use default
    # insert the binding into the policy
    policy.bindings.append(binding)

    try:
        bucket.set_iam_policy(policy)
    except Exception as e:
        logger.error(str(e))
        raise e


def grant_bigquery_iam_access(policy: Policy, user_emails: List[str]) -> None:
    """
    Grant all 'user_emails' the "roles/bigquery.jobUser" role on project.
    If we are in the production environment, all 'user_emails' also get access to
    the public bigquery dataset in prod.
    """
    roles = [b["role"] for b in policy["bindings"]]

    if GOOGLE_BIGQUERY_USER_ROLE in roles:  # if the role is already in the policy, add the users
        binding = next(b for b in policy["bindings"] if b["role"] == GOOGLE_BIGQUERY_USER_ROLE)
        for user_email in user_emails:
            binding["members"].append(user_member(user_email))
    else:  # otherwise create the role and add to policy
        binding = {
            "role": GOOGLE_BIGQUERY_USER_ROLE,
            "members": [user_member(user_email) for user_email in user_emails],  # convert format
        }
        policy["bindings"].append(binding)

    # try to set the new policy with edits
    try:
        CRM_SERVICE.projects().setIamPolicy(
            resource=GOOGLE_CLOUD_PROJECT,
            body={
                "policy": policy,
            },
        ).execute()
    except Exception as e:
        logger.error(str(e))
        raise e

    # grant dataset level access to public dataset
    dataset_id = GOOGLE_CLOUD_PROJECT + ".public"
    dataset = _get_bigquery_dataset(dataset_id)
    entries = list(dataset.access_entries)
    for user_email in user_emails:
        entries.append(
            bigquery.AccessEntry(
                role="READER",
                entity_type=EntityTypes.USER_BY_EMAIL,
                entity_id=user_email,
            )
        )
    dataset.access_entries = entries
    BIGQUERY_CLIENT.update_dataset(dataset, ["access_entries"])  # Make an API request.


# Arbitrary upper bound on the number of GCS IAM bindings we expect a user to have for uploads
MAX_REVOKE_ALL_ITERATIONS = 250


def revoke_storage_iam_access(bucket: storage.Bucket, role: str, user_email: str) -> None:
    """Revoke a bucket IAM policy made by calling `grant_storage_iam_access`."""
    # see https://cloud.google.com/storage/docs/access-control/using-iam-permissions#code-samples_3
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.version = 3

    # find and remove any matching policy binding for this user
    for i in range(MAX_REVOKE_ALL_ITERATIONS):
        removed_binding = _find_and_pop_storage_iam_binding(policy, role, user_email)
        if removed_binding is None:
            if i == 0:
                warnings.warn(f"Tried to revoke a non-existent download IAM permission for {user_email}")
            break

    try:
        bucket.set_iam_policy(policy)
    except Exception as e:
        logger.error(str(e))
        raise e


def revoke_bigquery_iam_access(policy: Policy, user_email: str) -> None:
    """
    Revoke 'user_email' the "roles/bigquery.jobUser" role on project.
    If we are in the production environment, 'user_email' also get access
    revoked from the public bigquery dataset in prod.
    """
    # find and remove user on binding
    binding = next((b for b in policy["bindings"] if b["role"] == GOOGLE_BIGQUERY_USER_ROLE), None)
    if not binding:
        logger.warning("Expected at least 1 user to have a bigquery jobUser role, but 0 found.")
        return

    if "members" in binding and user_member(user_email) in binding["members"]:
        binding["members"].remove(user_member(user_email))

    # try update of the policy
    try:
        policy = (
            CRM_SERVICE.projects()
            .setIamPolicy(
                resource=GOOGLE_CLOUD_PROJECT,
                body={
                    "policy": policy,
                },
            )
            .execute()
        )
    except Exception as e:
        logger.error(str(e))
        raise e

    # remove dataset level access
    dataset_id = GOOGLE_CLOUD_PROJECT + ".public"
    dataset = _get_bigquery_dataset(dataset_id)
    entries = list(dataset.access_entries)

    dataset.access_entries = [entry for entry in entries if entry.entity_id != user_email]

    dataset = BIGQUERY_CLIENT.update_dataset(
        dataset,
        # Update just the `access_entries` property of the dataset.
        ["access_entries"],
    )  # Make an API request.


def user_member(email):
    return f"user:{email}"


def _build_storage_iam_binding(
    bucket: str,
    role: str,
    user_email: str,
    ttl_days: int = INACTIVE_USER_DAYS,
) -> Dict[str, Any]:
    """
    Grant the user associated with `user_email` the provided IAM `role` when acting
    on objects in `bucket`. This permission remains active for `ttl_days` days.

    See GCP common expression language syntax overview: https://cloud.google.com/iam/docs/conditions-overview

    Parameters
    ----------
    bucket: str
        the name of the bucket to build the binding for
    role: str
        the role name to build the binding for
    user_email: str
        the email of the user to build the binding for
    ttl_days: int = INACTIVE_USER_DAYS
        the number of days until this permission should expire
        pass -1 for non-expiring


    Returns
    -------
    List[dict]
        the bindings to be put onto policy.bindings
    """
    timestamp = datetime.datetime.now()
    expiry_date = (timestamp + datetime.timedelta(ttl_days)).date()

    # going to add the expiration condition after, so don't return directly
    ret = {
        "role": role,
        "members": {user_member(user_email)},  # convert format
    }

    if ttl_days >= 0:
        # special value -1 doesn't expire
        ret["condition"] = {
            "title": f"{role} access on {bucket}",
            "description": f"Auto-updated by the CIDC API on {timestamp}",
            "expression": f'request.time < timestamp("{expiry_date.isoformat()}T00:00:00Z")',
        }

    return ret


def _find_and_pop_storage_iam_binding(
    policy: storage.bucket.Policy,
    role: str,
    user_email: str,
) -> Optional[dict]:
    """
    Find an IAM policy binding for the given `user_email`, `policy`, and `role`, and pop
    it from the policy's bindings list if it exists.
    """
    # try to find the policy binding on the `policy`
    user_binding_index = None
    for i, binding in enumerate(policy.bindings):
        role_matches = binding.get("role") == role
        member_matches = binding.get("members") == {user_member(user_email)}
        if role_matches and member_matches:
            # a user should be a member of no more than one conditional download binding
            # if they do, warn - but use the last one because this isn't breaking
            if user_binding_index is not None:
                warnings.warn(
                    f"Found multiple conditional bindings for {user_email} role {role}. This is an invariant violation - "
                    "check out permissions on the CIDC GCS buckets to debug."
                )
            user_binding_index = i

    binding = policy.bindings.pop(user_binding_index) if user_binding_index is not None else None

    return binding


# object_url          | essex_test/xlsx/assays/wes_bam/2023-04-18T16:33:03.735217.xlsx
# http://localhost:4443/storage/v1/b/essex-data-staging-acl/o/essex_test%2Fxlsx%2Fassays%2Fwes_bam%2F2023-04-18T16%3A33%3A03.735217.xlsx?Expires=1683748504&GoogleAccessId=commanding-hawk-348012%40appspot.gserviceaccount.com&Signature=nBKeq%2BlOCYrCKqxXgiKP2hnLqOerrl5lTdGYfaFQPgkyJeRzHOk42R25L31X%2FKgR8t%2FHzqfpzQJzsW65kXDK59ZEhDs1TAS23gCUXHQMZImScU7yXWr%2FXTM4iVXNfDi%2Fq592v%2BTpnDowjnG21ixWRLt3oBep39trkAXL%2FOK%2Fe21fJHQvxNo%2F%2BMPGYUcU5oWJqdh1pS55IAZbLfhvcvUJQBSn0B0tWOSahncC9iLtaipBAMGA%2F3vjNUzUTuL2i0ED%2F7rkWrWPPaFaF6c0bTvpfF23hjNXzaH3CEq2a5ozvXAR2ltaDf7zgxxpwtC5XLKnjnc%2F%2BIIVsFnRdFzZGFTToA%3D%3D&response-content-disposition=attachment%3B+filename%3D%22_storage_v1_b_essex_test_xlsx_assays_wes_bam_2023-04-18T16%3A33%3A03.735217.xlsx%22
def get_signed_url(
    object_name: str,
    bucket_name: str = GOOGLE_ACL_DATA_BUCKET,
    method: str = "GET",
    expiry_mins: int = 30,
) -> str:
    """
    Generate a signed URL for `object_name` to give a client temporary access.

    Using v2 signed urls because v4 is in Beta and response_disposition doesn't work.
    https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers
    """
    storage_client = _get_storage_client()
    logger.info(storage_client)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)

    # Generate the signed URL, allowing a client to use `method` for `expiry_mins` minutes
    expiration = datetime.timedelta(minutes=expiry_mins)
    full_filename = object_name.replace("/", "_").replace('"', "_").replace(" ", "_")
    other_kwargs = {}
    if os.environ.get("DEV_GOOGLE_STORAGE", None):
        other_kwargs["api_access_endpoint"] = (os.environ.get("DEV_GOOGLE_STORAGE") or "") + (
            os.environ.get("DEV_GOOGLE_STORAGE_PATH") or ""
        )
    url = blob.generate_signed_url(
        version="v2",
        expiration=expiration,
        method=method,
        response_disposition=f'attachment; filename="{full_filename}"',
        **other_kwargs,
    )
    logger.info(f"generated signed URL for {object_name}: {url}")

    return url


def _encode_and_publish(content: str, topic: str) -> Future:
    """Convert `content` to bytes and publish it to `topic`."""
    pubsub_publisher = pubsub.PublisherClient()
    topic = pubsub_publisher.topic_path(GOOGLE_CLOUD_PROJECT, topic)
    data = bytes(content, "utf-8")

    # Don't actually publish to Pub/Sub if running locally
    if ENV == "dev":
        if DEV_CFUNCTIONS_SERVER:
            logger.info(f"Publishing message {content!r} to topic {DEV_CFUNCTIONS_SERVER}/{topic}")

            bdata = base64.b64encode(content.encode("utf-8"))
            try:
                res = requests.post(
                    f"{DEV_CFUNCTIONS_SERVER}/{topic}",
                    data={"data": bdata},
                    timeout=TIMEOUT_IN_SECONDS,
                )
            except Exception as e:
                raise Exception(f"Couldn't publish message {content!r} to topic {DEV_CFUNCTIONS_SERVER}/{topic}") from e

            logger.info(f"Got {res}")
            if res.status_code != 200:
                raise Exception(f"Couldn't publish message {content!r} to {DEV_CFUNCTIONS_SERVER}/{topic}: {res!r}")

        else:
            logger.info(f"Would've published message {content} to topic {topic}")
        return None

    # The Pub/Sub publisher client returns a concurrent.futures.Future
    # containing info about whether the publishing was successful.
    report = pubsub_publisher.publish(topic, data=data)

    return report


def publish_upload_success(job_id: int) -> None:
    """Publish to the uploads topic that the upload job with the provided `job_id` succeeded."""
    report = _encode_and_publish(str(job_id), GOOGLE_UPLOAD_TOPIC)

    # For now, we wait await this Future. Going forward, maybe
    # we should look for a way to leverage asynchrony here.
    if report:
        report.result()


def publish_patient_sample_update(manifest_upload_id: int) -> None:
    """Publish to the patient_sample_update topic that a new manifest has been uploaded."""
    report = _encode_and_publish(str(manifest_upload_id), GOOGLE_PATIENT_SAMPLE_TOPIC)

    # Wait for response from pub/sub
    if report:
        report.result()


def publish_artifact_upload(file_id: int) -> None:
    """Publish a downloadable file ID to the artifact_upload topic"""
    report = _encode_and_publish(str(file_id), GOOGLE_ARTIFACT_UPLOAD_TOPIC)

    # Wait for response from pub/sub
    if report:
        report.result()


def publish_hl_clinical_validation(job_id: int) -> None:
    """Publish to the high_level_clinical_validation topic that a job's files are ready to be validated."""
    # Start validation asynchronously
    _report = _encode_and_publish(str(job_id), GOOGLE_HL_CLINICAL_VALIDATION_TOPIC)


def publish_detailed_validation(job_id: int) -> None:
    """Start detailed validation and create the detailed validation preprocessed file"""
    # Start validation asynchronously
    _report = _encode_and_publish(str(job_id), GOOGLE_DL_CLINICAL_VALIDATION_TOPIC)


def send_email(to_emails: List[str], subject: str, html_content: str, **kw) -> None:
    """
    Publish an email-to-send to the emails topic.
    `kw` are expected to be sendgrid json api style additional email parameters.
    """
    # Don't actually send an email if this is a test
    if TESTING or ENV == "dev" or IS_EMAIL_ON.lower() == "false":
        logger.info(f"Would send email with subject '{subject}' to {to_emails}")
        return

    logger.info(f"({ENV}) Sending email to {to_emails} with subject {subject}")
    email_json = json.dumps({"to_emails": to_emails, "subject": subject, "html_content": html_content, **kw})

    report = _encode_and_publish(email_json, GOOGLE_EMAILS_TOPIC)

    # Await confirmation that the published message was received.
    if report:
        report.result()
