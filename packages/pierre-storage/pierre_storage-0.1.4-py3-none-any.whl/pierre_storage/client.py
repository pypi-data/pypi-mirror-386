"""Main client for Pierre Git Storage SDK."""

import uuid
from typing import Optional

import httpx

from pierre_storage.auth import generate_jwt
from pierre_storage.errors import ApiError
from pierre_storage.repo import DEFAULT_TOKEN_TTL_SECONDS, RepoImpl
from pierre_storage.types import (
    CreateRepoOptions,
    FindOneOptions,
    GetRemoteURLOptions,
    GitStorageOptions,
    Repo,
)

DEFAULT_API_BASE_URL = "https://api.code.storage"
DEFAULT_STORAGE_BASE_URL = "code.storage"
DEFAULT_API_VERSION = 1


class GitStorage:
    """Pierre Git Storage client."""

    _overrides: GitStorageOptions = {}

    def __init__(self, options: GitStorageOptions) -> None:
        """Initialize GitStorage client.

        Args:
            options: Client configuration options

        Raises:
            ValueError: If required options are missing or invalid
        """
        # Validate required fields
        if not options or "name" not in options or "key" not in options:
            raise ValueError(
                "GitStorage requires a name and key. Please check your configuration and try again."
            )

        name = options["name"]
        key = options["key"]

        if name is None or key is None:
            raise ValueError(
                "GitStorage requires a name and key. Please check your configuration and try again."
            )

        if not isinstance(name, str) or not name.strip():
            raise ValueError("GitStorage name must be a non-empty string.")

        if not isinstance(key, str) or not key.strip():
            raise ValueError("GitStorage key must be a non-empty string.")

        # Resolve configuration with overrides
        api_base_url = (
            options.get("api_base_url")
            or self._overrides.get("api_base_url")
            or DEFAULT_API_BASE_URL
        )

        storage_base_url = (
            options.get("storage_base_url")
            or self._overrides.get("storage_base_url")
            or DEFAULT_STORAGE_BASE_URL
        )

        api_version = (
            options.get("api_version")
            or self._overrides.get("api_version")
            or DEFAULT_API_VERSION
        )

        default_ttl = options.get("default_ttl") or self._overrides.get("default_ttl")

        self.options: GitStorageOptions = {
            "name": name,
            "key": key,
            "api_base_url": api_base_url,
            "storage_base_url": storage_base_url,
            "api_version": api_version,
        }

        if default_ttl:
            self.options["default_ttl"] = default_ttl

    @classmethod
    def override(cls, options: GitStorageOptions) -> None:
        """Override default configuration.

        Args:
            options: Configuration overrides
        """
        cls._overrides = {**cls._overrides, **options}

    async def create_repo(
        self, options: Optional[CreateRepoOptions] = None
    ) -> Repo:
        """Create a new repository.

        Args:
            options: Repository creation options

        Returns:
            Created repository instance

        Raises:
            ApiError: If repository creation fails
        """
        opts = options or {}
        repo_id = opts.get("id") or str(uuid.uuid4())
        default_branch = opts.get("default_branch", "main")

        ttl = opts.get("ttl", DEFAULT_TOKEN_TTL_SECONDS)
        jwt = self._generate_jwt(
            repo_id,
            {"permissions": ["repo:write"], "ttl": ttl},
        )

        url = f"{self.options['api_base_url']}/api/v{self.options['api_version']}/repos"
        body = {"default_branch": default_branch}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=30.0,
            )

            if response.status_code == 409:
                raise ApiError("Repository already exists", status_code=409)

            if not response.is_success:
                raise ApiError(
                    f"Failed to create repository: {response.status_code} {response.reason_phrase}",
                    status_code=response.status_code,
                    response=response,
                )

        return RepoImpl(
            repo_id,
            self.options["api_base_url"],  # type: ignore
            self.options["storage_base_url"],  # type: ignore
            self.options["name"],  # type: ignore
            self.options["api_version"],  # type: ignore
            self._generate_jwt,
        )

    async def find_one(self, options: FindOneOptions) -> Optional[Repo]:
        """Find a repository by ID.

        Args:
            options: Search options with repository ID

        Returns:
            Repository instance if found, None otherwise
        """
        repo_id = options["id"]
        jwt = self._generate_jwt(
            repo_id,
            {"permissions": ["git:read"], "ttl": DEFAULT_TOKEN_TTL_SECONDS},
        )

        url = f"{self.options['api_base_url']}/api/v{self.options['api_version']}/repo"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=30.0,
            )

            if response.status_code == 404:
                return None

            if not response.is_success:
                raise ApiError(
                    f"Failed to find repository: {response.status_code} {response.reason_phrase}",
                    status_code=response.status_code,
                    response=response,
                )

        return RepoImpl(
            repo_id,
            self.options["api_base_url"],  # type: ignore
            self.options["storage_base_url"],  # type: ignore
            self.options["name"],  # type: ignore
            self.options["api_version"],  # type: ignore
            self._generate_jwt,
        )

    def get_config(self) -> GitStorageOptions:
        """Get current client configuration.

        Returns:
            Copy of current configuration
        """
        return {**self.options}

    def _generate_jwt(
        self,
        repo_id: str,
        options: Optional[GetRemoteURLOptions] = None,
    ) -> str:
        """Generate JWT token for authentication.

        Args:
            repo_id: Repository identifier
            options: JWT generation options

        Returns:
            Signed JWT token
        """
        permissions = ["git:write", "git:read"]
        ttl = 31536000  # 1 year default

        if options:
            if "permissions" in options:
                permissions = options["permissions"]  # type: ignore
            if "ttl" in options:
                ttl = options["ttl"]  # type: ignore
        elif "default_ttl" in self.options:
            ttl = self.options["default_ttl"]  # type: ignore

        return generate_jwt(
            self.options["key"],  # type: ignore
            self.options["name"],  # type: ignore
            repo_id,
            permissions,
            ttl,
        )


def create_client(options: GitStorageOptions) -> GitStorage:
    """Create a GitStorage client.

    Args:
        options: Client configuration options

    Returns:
        GitStorage client instance
    """
    return GitStorage(options)
