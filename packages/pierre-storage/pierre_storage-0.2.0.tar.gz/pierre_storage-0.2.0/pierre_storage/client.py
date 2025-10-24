"""Main client for Pierre Git Storage SDK."""

import uuid
from typing import Any, Dict, Optional

import httpx

from pierre_storage.auth import generate_jwt
from pierre_storage.errors import ApiError
from pierre_storage.repo import DEFAULT_TOKEN_TTL_SECONDS, RepoImpl
from pierre_storage.types import (
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
            options.get("api_version") or self._overrides.get("api_version") or DEFAULT_API_VERSION
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
        self,
        *,
        id: Optional[str] = None,
        default_branch: str = "main",
        ttl: Optional[int] = None,
    ) -> Repo:
        """Create a new repository.

        Args:
            id: Repository ID (auto-generated if not provided)
            default_branch: Default branch name (default: "main")
            ttl: Token TTL in seconds

        Returns:
            Created repository instance

        Raises:
            ApiError: If repository creation fails
        """
        repo_id = id or str(uuid.uuid4())
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
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

        # These are guaranteed to be set in __init__
        api_base_url: str = self.options["api_base_url"]  # type: ignore[assignment]
        storage_base_url: str = self.options["storage_base_url"]  # type: ignore[assignment]
        name: str = self.options["name"]
        api_version: int = self.options["api_version"]  # type: ignore[assignment]

        return RepoImpl(
            repo_id,
            api_base_url,
            storage_base_url,
            name,
            api_version,
            self._generate_jwt,
        )

    async def find_one(self, *, id: str) -> Optional[Repo]:
        """Find a repository by ID.

        Args:
            id: Repository ID to find

        Returns:
            Repository instance if found, None otherwise
        """
        repo_id = id
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

        # These are guaranteed to be set in __init__
        api_base_url: str = self.options["api_base_url"]  # type: ignore[assignment]
        storage_base_url: str = self.options["storage_base_url"]  # type: ignore[assignment]
        name: str = self.options["name"]
        api_version: int = self.options["api_version"]  # type: ignore[assignment]

        return RepoImpl(
            repo_id,
            api_base_url,
            storage_base_url,
            name,
            api_version,
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
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate JWT token for authentication.

        Args:
            repo_id: Repository identifier
            options: JWT generation options (internal use)

        Returns:
            Signed JWT token
        """
        permissions = ["git:write", "git:read"]
        ttl: int = 31536000  # 1 year default

        if options:
            if "permissions" in options:
                permissions = options["permissions"]
            if "ttl" in options:
                option_ttl = options["ttl"]
                if isinstance(option_ttl, int):
                    ttl = option_ttl
        elif "default_ttl" in self.options:
            default_ttl = self.options["default_ttl"]
            if isinstance(default_ttl, int):
                ttl = default_ttl

        return generate_jwt(
            self.options["key"],
            self.options["name"],
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
