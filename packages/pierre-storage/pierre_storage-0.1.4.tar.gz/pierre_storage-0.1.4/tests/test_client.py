"""Tests for GitStorage client."""

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from pierre_storage import GitStorage, create_client
from pierre_storage.errors import ApiError


class TestGitStorage:
    """Tests for GitStorage class."""

    def test_create_instance(self, git_storage_options: dict) -> None:
        """Test creating GitStorage instance."""
        storage = GitStorage(git_storage_options)
        assert storage is not None
        assert isinstance(storage, GitStorage)

    def test_store_key(self, git_storage_options: dict, test_key: str) -> None:
        """Test that key is stored."""
        storage = GitStorage(git_storage_options)
        config = storage.get_config()
        assert config["key"] == test_key

    def test_missing_options(self) -> None:
        """Test error when options are missing."""
        with pytest.raises(ValueError, match="GitStorage requires a name and key"):
            GitStorage({})  # type: ignore

    def test_null_key(self, test_key: str) -> None:
        """Test error when key is null."""
        with pytest.raises(ValueError, match="GitStorage requires a name and key"):
            GitStorage({"name": "test", "key": None})  # type: ignore

    def test_empty_key(self) -> None:
        """Test error when key is empty."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": ""})

    def test_empty_name(self, test_key: str) -> None:
        """Test error when name is empty."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": "", "key": test_key})

    def test_whitespace_key(self) -> None:
        """Test error when key is whitespace."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": "   "})

    def test_whitespace_name(self, test_key: str) -> None:
        """Test error when name is whitespace."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": "   ", "key": test_key})

    def test_non_string_key(self) -> None:
        """Test error when key is not a string."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": 123})  # type: ignore

    def test_non_string_name(self, test_key: str) -> None:
        """Test error when name is not a string."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": 123, "key": test_key})  # type: ignore

    @pytest.mark.asyncio
    async def test_create_repo(self, git_storage_options: dict) -> None:
        """Test creating a repository."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"repo_id": "test-repo", "url": "https://test.git"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo({"id": "test-repo"})
            assert repo is not None
            assert repo.id == "test-repo"

    @pytest.mark.asyncio
    async def test_create_repo_conflict(self, git_storage_options: dict) -> None:
        """Test creating a repository that already exists."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.is_success = False

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(ApiError, match="Repository already exists"):
                await storage.create_repo({"id": "existing-repo"})

    @pytest.mark.asyncio
    async def test_find_one(self, git_storage_options: dict) -> None:
        """Test finding a repository."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"id": "test-repo"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.find_one({"id": "test-repo"})
            assert repo is not None
            assert repo.id == "test-repo"

    @pytest.mark.asyncio
    async def test_find_one_not_found(self, git_storage_options: dict) -> None:
        """Test finding a repository that doesn't exist."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.find_one({"id": "nonexistent"})
            assert repo is None

    def test_create_client_factory(self, git_storage_options: dict) -> None:
        """Test create_client factory function."""
        client = create_client(git_storage_options)
        assert isinstance(client, GitStorage)


class TestJWTGeneration:
    """Tests for JWT generation."""

    @pytest.mark.asyncio
    async def test_jwt_structure(self, git_storage_options: dict, test_key: str) -> None:
        """Test JWT has correct structure."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo({"id": "test-repo"})
            url = await repo.get_remote_url()

            # Extract JWT from URL
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            assert match is not None
            token = match.group(1)

            # Decode JWT (without verification for testing)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["iss"] == "test-customer"
            assert payload["sub"] == "@pierre/storage"
            assert payload["repo"] == "test-repo"
            assert "scopes" in payload
            assert "iat" in payload
            assert "exp" in payload
            assert payload["exp"] > payload["iat"]

    @pytest.mark.asyncio
    async def test_jwt_default_permissions(self, git_storage_options: dict) -> None:
        """Test JWT has default permissions."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo({"id": "test-repo"})
            url = await repo.get_remote_url()

            # Extract and decode JWT
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["scopes"] == ["git:write", "git:read"]

    @pytest.mark.asyncio
    async def test_jwt_custom_permissions(self, git_storage_options: dict) -> None:
        """Test JWT with custom permissions."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo({"id": "test-repo"})
            url = await repo.get_remote_url({"permissions": ["git:read"], "ttl": 3600})

            # Extract and decode JWT
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["scopes"] == ["git:read"]
            assert payload["exp"] - payload["iat"] == 3600
