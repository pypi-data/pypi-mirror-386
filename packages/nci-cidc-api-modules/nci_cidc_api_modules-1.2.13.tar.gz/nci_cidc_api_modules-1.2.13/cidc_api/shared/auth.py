from functools import wraps
from typing import List

from packaging import version

from flask import g, request, current_app as app, Flask
from werkzeug.exceptions import Unauthorized, BadRequest, PreconditionFailed

from ..models import Users, UserSchema

from ..config.logging import get_logger

from ..shared.jose import decode_id_token

logger = get_logger(__name__)


### Main auth utility functions ###
def validate_api_auth(app: Flask):
    """
    Assert that all URLs in `app`'s API are explicitly marked with either
    `requires_auth` or `public`.
    """
    unmarked_endpoints = []
    for label, endpoint in app.view_functions.items():
        if not hasattr(endpoint, "is_protected"):
            unmarked_endpoints.append(label)

    assert len(unmarked_endpoints) == 0, (
        "All endpoints must use either the `requires_auth` or `public` decorator "
        "to explicitly specify their auth configuration. Missing from the following "
        "endpoints: " + ", ".join(unmarked_endpoints)
    )


def requires_auth(resource: str, allowed_roles: list = None):
    """
    A decorator that adds authentication and basic access to an endpoint.

    NOTE: leaving the `allowed_roles` argument empty allows any authenticated user to access
    the decorated endpoint.

    Raises:
        Unauthorized if unauthorized
    """

    if allowed_roles is None:
        allowed_roles = []

    def decorator(endpoint):
        # Store metadata on this function stating that it is protected by authentication
        endpoint.is_protected = True

        @wraps(endpoint)
        def wrapped(*args, **kwargs):
            is_authorized = check_auth(allowed_roles, resource, request.method)
            if not is_authorized:
                raise Unauthorized("Please provide proper credentials")
            return endpoint(*args, **kwargs)

        return wrapped

    return decorator


def authenticate_and_get_user():
    """
    Try to authenticate the user associated with this request. Return the user
    if authentication succeeds, or `None` if it fails.
    NOTE: this function bypasses RBAC. It's up to the caller to determine whether
    an authenticated user is authorized to take subsequent action.
    """
    try:
        check_auth(None, None, None)
        return get_current_user()
    except (AssertionError, BadRequest, PreconditionFailed, Unauthorized):
        return None


def public(endpoint):
    """Declare an endpoint to be public, i.e., not requiring auth."""
    # Store metadata on this function stating that it is unprotected
    endpoint.is_protected = False

    return endpoint


def check_auth(allowed_roles: List[str], resource: str, method: str) -> bool:
    """
    Perform authentication and authorization for the current request.

    Args:
        allowed_roles: a list of CIDC user roles allowed to access this endpoint
        resource: the resource targeted by this request
        method: the HTTP method of this request
    Raises:
        Unauthorized if not authorized
        BadRequest if cannot parse User-Agent string
        PreconditionFailed if too low CLI version
    Returns:
        bool, `True` if authentication and authorization passed.
    """
    user = authenticate()

    try:
        is_authorized = authorize(user, allowed_roles, resource, method)
    except Unauthorized:
        _log_user_and_request_details(False)
        raise

    _log_user_and_request_details(is_authorized)

    _enforce_cli_version()

    return is_authorized


### Current user management ###
CURRENT_USER_KEY = "current_user"


def _set_current_user(user: Users):
    """Store a user in the current request's context.
    Raises AssertionError if not given a `Users`"""
    assert isinstance(user, Users), "`user` must be an instance of the `Users` model"
    setattr(g, CURRENT_USER_KEY, user)


def get_current_user() -> Users:
    """Returns the authenticated user who made the current request.
    Raises AssertionError if no current user"""
    current_user = g.get(CURRENT_USER_KEY)

    assert current_user, (
        "There is no user associated with the current request.\n"
        "Note: `auth.get_current_user` can't be called by a request handler without authentication. "
        "Decorate your handler with `auth.requires_auth` to authenticate the requesting user before calling the handler."
    )

    return current_user


### Authentication logic ###
_user_schema = UserSchema()


def authenticate() -> Users:
    id_token = _extract_token()
    token_payload = decode_id_token(id_token)
    profile = {"email": token_payload["email"]}
    return _user_schema.load(profile)


def _extract_token() -> str:
    """Extract an identity token from the current request's authorization header or from the request body.
    Raises Unauthorized if cannot find the token"""
    auth_header = request.headers.get("Authorization")

    try:
        if auth_header:
            bearer, id_token = auth_header.split(" ")
            assert bearer.lower() == "bearer"
        else:
            id_token = request.json["id_token"]
    except (AssertionError, AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Unauthorized(
            "Either the 'Authorization' header must be set with structure 'Authorization: Bearer <id token>' "
            'or "id_token" must be present in the JSON body of the request.'
        ) from exc

    return id_token


### Authorization logic ###
def authorize(user: Users, allowed_roles: List[str], resource: str, method: str) -> bool:
    """Check if the current user is authorized to act on the current request's resource.
    Raises Unauthorized
        - if user is not registered
        - if user is disabled
        - if user's registration is pending approval
        - if user.role is not in allowed_roles
    """
    db_user = Users.find_by_email(user.email)

    # User hasn't registered yet.
    if not db_user:
        # Although the user doesn't exist in the database, we still
        # make the user's identity data available in the request context.
        _set_current_user(user)

        # User is only authorized to create themself.
        if resource == "self" and method == "POST":
            return True

        raise Unauthorized(f"{user.email} is not registered.")

    _set_current_user(db_user)

    db_user.update_accessed()

    # User is registered but disabled.
    if db_user.disabled:
        # Disabled users are not authorized to do anything but access their
        # account info.
        if resource == "self" and method == "GET":
            return True

        raise Unauthorized(f"{db_user.email}'s account is disabled.")

    # User is registered but not yet approved.
    if not db_user.approval_date:
        # Unapproved users are not authorized to do anything but access their
        # account info.
        if resource == "self" and method == "GET":
            return True

        raise Unauthorized(f"{db_user.email}'s registration is pending approval")

    # User is approved and registered, so just check their role.
    if allowed_roles and db_user.role not in allowed_roles:
        raise Unauthorized(f"{db_user.email} is not authorized to access this endpoint.")

    return True


### Miscellaneous helpers ###
def _log_user_and_request_details(is_authorized: bool):
    """Log user and request info before every request"""
    log_msg = f"{'' if is_authorized else 'UN'}AUTHORIZED"

    # log request details
    log_msg += f" {request.environ['REQUEST_METHOD']} {request.environ['RAW_URI']}"

    # log user details
    user = get_current_user()
    log_msg += f" (user:{user.id}:{user.email})"

    if is_authorized:
        logger.info(log_msg)
    else:
        logger.error(log_msg)


def _enforce_cli_version():
    """
    If the current request appears to come from the CLI and not the Portal, enforce the configured
    minimum CLI version.

    Raises:
        BadRequest if could not parse the User-Agent string
        PreconditionFailed if too low CLI version
    """
    user_agent = request.headers.get("User-Agent")

    # e.g., during testing no User-Agent header is supplied
    if not user_agent:
        return

    try:
        client, client_version = user_agent.split("/", 1)
    except ValueError as exc:
        logger.error("Unrecognized user-agent string format: %s", user_agent)
        raise BadRequest("could not parse User-Agent string") from exc

    # The CLI sets the User-Agent header to `cidc-cli/{version}`,
    # so we can assess whether the requester needs to update their CLI.
    is_old_cli = client == "cidc-cli" and version.parse(client_version) < version.parse(app.config["MIN_CLI_VERSION"])

    if is_old_cli:
        logger.info("cancelling request: detected outdated CLI")
        message = (
            "You appear to be using an out-of-date version of the CIDC CLI. "
            "Please upgrade to the most recent version:\n"
            "    pip3 install --upgrade cidc-cli"
        )
        raise PreconditionFailed(message)
