# This file has been generated - DO NOT MODIFY
# API Version : 2.20.1


import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar

from avatars.models import (
    CompatibilityResponse,  # noqa: F401
    CreateUser,  # noqa: F401
    CreditsInfo,  # noqa: F401
    FeaturesInfo,  # noqa: F401
    FileAccess,  # noqa: F401
    ForgottenPasswordRequest,  # noqa: F401
    JobCreateRequest,  # noqa: F401
    JobCreateResponse,  # noqa: F401
    JobKind,
    JobResponse,  # noqa: F401
    JobResponseList,  # noqa: F401
    Login,  # noqa: F401
    LoginResponse,  # noqa: F401
    ResetPasswordRequest,  # noqa: F401
    ResourceSetResponse,  # noqa: F401
    User,  # noqa: F401
)

if TYPE_CHECKING:
    from avatars.client import ApiClient


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
DEFAULT_RETRY_TIMEOUT = 60
DEFAULT_TIMEOUT = 60


T = TypeVar("T")


class Auth:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def login(
        self,
        request: Login,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> LoginResponse:
        """Login the user."""

        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/login",  # noqa: F541
            "timeout": timeout,
            "form_data": request,
            "should_verify_auth": False,
        }

        return LoginResponse(**self.client.request(**kwargs))

    def refresh(
        self,
        token: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> LoginResponse:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/refresh",  # noqa: F541
            "timeout": timeout,
            "params": dict(
                token=token,
            ),
        }

        return LoginResponse(**self.client.request(**kwargs))

    def forgotten_password(
        self,
        request: ForgottenPasswordRequest,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/login/forgotten_password",  # noqa: F541
            "timeout": timeout,
            "json_data": request,
            "should_verify_auth": False,
        }

        return self.client.request(**kwargs)

    def reset_password(
        self,
        request: ResetPasswordRequest,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/login/reset_password",  # noqa: F541
            "timeout": timeout,
            "json_data": request,
            "should_verify_auth": False,
        }

        return self.client.request(**kwargs)


class Compatibility:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def is_client_compatible(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> CompatibilityResponse:
        """Verify if the client is compatible with the API."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/check_client",  # noqa: F541
            "timeout": timeout,
            "should_verify_auth": False,
        }

        return CompatibilityResponse(**self.client.request(**kwargs))


class Health:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def get_root(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Verify server health."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)

    def get_health(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Verify server health."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/health",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)

    def get_health_db(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Verify connection to the db health."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/health/db",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)


class Jobs:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def get_jobs(
        self,
        kind: Optional[JobKind] = None,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> JobResponseList:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/jobs",  # noqa: F541
            "timeout": timeout,
            "params": dict(
                kind=kind,
            ),
        }

        return JobResponseList(**self.client.request(**kwargs))

    def create_job(
        self,
        request: JobCreateRequest,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> JobCreateResponse:
        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/jobs",  # noqa: F541
            "timeout": timeout,
            "json_data": request,
        }

        return JobCreateResponse(**self.client.request(**kwargs))

    def get_job_status(
        self,
        job_name: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> JobResponse:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/jobs/{job_name}",  # noqa: F541
            "timeout": timeout,
        }

        return JobResponse(**self.client.request(**kwargs))


class Openapi:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def get_openapi_schema(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/openapi.json",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)


class Resources:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def get_user_volume(
        self,
        volume_name: str,
        purpose: str,
        set_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Generate a user volume configuration for a resource set.

        Creates a volume configuration YAML that can be used to mount user data
        or results for Avatar processing jobs. The volume references a specific
        resource set by display name.

        Args:
            volume_name: Name for the generated volume configuration
            set_name: UUID of the resource set to create volume for (required)
            purpose: Whether this volume is for "input" data or "results" output
            user: Current authenticated user
            display_name: [DEPRECATED] Use set_name instead. For backward compatibility only.

        Returns:
            Plain text response containing the volume configuration YAML
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/resources/volume",  # noqa: F541
            "timeout": timeout,
            "params": dict(
                volume_name=volume_name,
                purpose=purpose,
                set_name=set_name,
                display_name=display_name,
            ),
        }

        return self.client.request(**kwargs)

    def get_resources(
        self,
        set_name: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Retrieve all resources from a resource set.

        Returns all resources in a resource set as YAML content. The set is
        identified by its UUID.

        Args:
            user: Current authenticated user
            set_name: UUID of the resource set to retrieve

        Returns:
            YamlResponse containing all resources in the set as YAML

        Raises:
            HTTPException: 404 if the resource set does not exist
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/resources/{set_name}",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)

    def create_resource(
        self,
        set_name: str,
        yaml_string: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> ResourceSetResponse:
        """Add new resources to an existing resource set.

        Adds resources defined in YAML format to a resource set identified by UUID.
        The resource set must already exist. This endpoint appends to existing
        resources rather than replacing them.

        Args:
            user: Current authenticated user
            set_name: UUID of the resource set to add to
            yaml: YAML content defining the resources to add

        Returns:
            ResourceSetResponse containing the set UUID and display name

        Raises:
            HTTPException: 404 if the resource set does not exist
        """

        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/resources/{set_name}",  # noqa: F541
            "timeout": timeout,
            "content": yaml_string,
            "headers": {"Content-Type": "application/yaml"},
        }

        return ResourceSetResponse(**self.client.request(**kwargs))

    def put_resources(
        self,
        display_name: str,
        yaml_string: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> ResourceSetResponse:
        """Create a new version of a resource set with complete replacement.

        Creates a brand new resource set with a fresh UUID, replacing all resources
        with the provided YAML content. This implements versioning - the old set
        remains unchanged while a new version is created with the same display name.

        Args:
            user: Current authenticated user
            display_name: Human-readable name for the resource set (preserved across versions)
            yaml: YAML content defining all resources for the new version

        Returns:
            ResourceSetResponse with the new UUID and the same display name
        """

        kwargs: Dict[str, Any] = {
            "method": "put",
            "url": f"/resources/{display_name}",  # noqa: F541
            "timeout": timeout,
            "content": yaml_string,
            "headers": {"Content-Type": "application/yaml"},
        }

        return ResourceSetResponse(**self.client.request(**kwargs))


class Results:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def get_results(
        self,
        job_name: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/results/{job_name}",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)

    def get_permission_to_download(
        self,
        url: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> FileAccess:
        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/access",  # noqa: F541
            "timeout": timeout,
            "params": dict(
                url=url,
            ),
        }

        return FileAccess(**self.client.request(**kwargs))

    def get_permissions_to_download_batch(
        self,
        urls: List[str],
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> List[FileAccess]:
        """Get permissions for multiple files at once.

        Files that fail permission checks are silently skipped rather than
        causing the entire batch to fail.
        """

        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/access/batch",  # noqa: F541
            "timeout": timeout,
            "json_data": urls,
        }

        return [FileAccess(**item) for item in self.client.request(**kwargs)]

    def get_upload_url(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        """Get a URL to upload a dataset."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/upload_url",  # noqa: F541
            "timeout": timeout,
        }

        return self.client.request(**kwargs)

    def get_file(
        self,
        request: FileAccess,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/download",  # noqa: F541
            "timeout": timeout,
            "json_data": request,
        }

        return self.client.request(**kwargs)


class Users:
    def __init__(self, client: "ApiClient") -> None:
        self.client = client

    def find_users(
        self,
        email: Optional[str] = None,
        username: Optional[str] = None,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> List[User]:
        """Get users, optionally filtering them by username or email.

        This endpoint is protected with rate limiting.
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/users",  # noqa: F541
            "timeout": timeout,
            "params": dict(
                email=email,
                username=username,
            ),
        }

        return [User(**item) for item in self.client.request(**kwargs)]

    def create_user(
        self,
        request: CreateUser,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> User:
        """Create a user.

        This endpoint is protected with rate limiting.
        """

        kwargs: Dict[str, Any] = {
            "method": "post",
            "url": f"/users",  # noqa: F541
            "timeout": timeout,
            "json_data": request,
        }

        return User(**self.client.request(**kwargs))

    def get_me(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> User:
        """Get my own user."""

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/users/me",  # noqa: F541
            "timeout": timeout,
        }

        return User(**self.client.request(**kwargs))

    def get_credits_info(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> CreditsInfo:
        """Get the credits info for a user by id.

        This endpoint is protected with rate limiting.
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/users/credits_info",  # noqa: F541
            "timeout": timeout,
        }

        return CreditsInfo(**self.client.request(**kwargs))

    def get_features_info(
        self,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> FeaturesInfo:
        """Get the list of features for a user.

        This endpoint is protected with rate limiting.
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/users/features_info",  # noqa: F541
            "timeout": timeout,
        }

        return FeaturesInfo(**self.client.request(**kwargs))

    def get_user(
        self,
        id: str,
        *,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> User:
        """Get a user by id.

        This endpoint is protected with rate limiting.
        """

        kwargs: Dict[str, Any] = {
            "method": "get",
            "url": f"/users/{id}",  # noqa: F541
            "timeout": timeout,
        }

        return User(**self.client.request(**kwargs))
