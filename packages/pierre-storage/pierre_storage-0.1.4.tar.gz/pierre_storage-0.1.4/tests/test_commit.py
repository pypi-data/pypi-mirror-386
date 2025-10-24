"""Tests for CommitBuilder."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre_storage import GitStorage
from pierre_storage.errors import RefUpdateError


class TestCommitBuilder:
    """Tests for CommitBuilder operations."""

    @pytest.mark.asyncio
    async def test_create_commit_with_string_file(self, git_storage_options: dict) -> None:
        """Test creating commit with string file."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"abc123","tree_sha":"def456","target_branch":"main","pack_bytes":1024,"blob_count":1},"result":{"success":true,"status":"ok","branch":"main","old_sha":"000000","new_sha":"abc123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Add README",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .add_file_from_string("README.md", "# Hello World")
                .send()
            )

            assert result is not None
            assert result["commit_sha"] == "abc123"
            assert result["tree_sha"] == "def456"
            assert result["target_branch"] == "main"
            assert result["ref_update"]["branch"] == "main"
            assert result["ref_update"]["new_sha"] == "abc123"

    @pytest.mark.asyncio
    async def test_create_commit_with_bytes(self, git_storage_options: dict) -> None:
        """Test creating commit with byte content."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"xyz789","tree_sha":"uvw456","target_branch":"main","pack_bytes":2048,"blob_count":1},"result":{"success":true,"status":"ok","branch":"main","old_sha":"abc123","new_sha":"xyz789"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Add binary file",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .add_file("data.bin", b"\x00\x01\x02\x03")
                .send()
            )

            assert result is not None
            assert result["commit_sha"] == "xyz789"

    @pytest.mark.asyncio
    async def test_create_commit_with_multiple_files(self, git_storage_options: dict) -> None:
        """Test creating commit with multiple files."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"multi123","tree_sha":"multi456","target_branch":"main","pack_bytes":4096,"blob_count":3},"result":{"success":true,"status":"ok","branch":"main","old_sha":"old123","new_sha":"multi123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Multiple files",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .add_file_from_string("README.md", "# Project")
                .add_file_from_string("package.json", '{"name":"test"}')
                .add_file("data.bin", b"\x00\x01")
                .send()
            )

            assert result is not None
            assert result["blob_count"] == 3

    @pytest.mark.asyncio
    async def test_create_commit_with_delete(self, git_storage_options: dict) -> None:
        """Test creating commit with file deletion."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"del123","tree_sha":"del456","target_branch":"main","pack_bytes":512,"blob_count":0},"result":{"success":true,"status":"ok","branch":"main","old_sha":"old123","new_sha":"del123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Delete old file",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .delete_path("old-file.txt")
                .send()
            )

            assert result is not None
            assert result["commit_sha"] == "del123"

    @pytest.mark.asyncio
    async def test_create_commit_with_expected_head(self, git_storage_options: dict) -> None:
        """Test creating commit with expected head SHA."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"new123","tree_sha":"new456","target_branch":"main","pack_bytes":1024,"blob_count":1},"result":{"success":true,"status":"ok","branch":"main","old_sha":"expected123","new_sha":"new123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "expected_head_sha": "expected123",
                        "commit_message": "Safe update",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .add_file_from_string("file.txt", "content")
                .send()
            )

            assert result is not None
            assert result["ref_update"]["old_sha"] == "expected123"

    @pytest.mark.asyncio
    async def test_create_commit_ref_update_failed(self, git_storage_options: dict) -> None:
        """Test handling ref update failure."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"fail123","tree_sha":"fail456","target_branch":"main","pack_bytes":1024,"blob_count":1},"result":{"success":false,"status":"rejected","reason":"conflict","branch":"main","old_sha":"old123","new_sha":"fail123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})

            with pytest.raises(RefUpdateError) as exc_info:
                await (
                    repo.create_commit(
                        {
                            "target_branch": "main",
                            "commit_message": "Should fail",
                            "author": {"name": "Test", "email": "test@example.com"},
                        }
                    )
                    .add_file_from_string("file.txt", "content")
                    .send()
                )

            assert exc_info.value.status == "rejected"
            assert exc_info.value.reason == "rejected"  # reason defaults to status when not provided

    @pytest.mark.asyncio
    async def test_create_commit_with_custom_encoding(self, git_storage_options: dict) -> None:
        """Test creating commit with custom text encoding."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"enc123","tree_sha":"enc456","target_branch":"main","pack_bytes":1024,"blob_count":1},"result":{"success":true,"status":"ok","branch":"main","old_sha":"000000","new_sha":"enc123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Latin-1 file",
                        "author": {"name": "Test", "email": "test@example.com"},
                    }
                )
                .add_file_from_string("file.txt", "café", encoding="latin-1")
                .send()
            )

            assert result is not None
            assert result["commit_sha"] == "enc123"

    @pytest.mark.asyncio
    async def test_create_commit_with_committer(self, git_storage_options: dict) -> None:
        """Test creating commit with separate committer."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock the streaming response
        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(return_value=b'{"commit":{"commit_sha":"com123","tree_sha":"com456","target_branch":"main","pack_bytes":1024,"blob_count":1},"result":{"success":true,"status":"ok","branch":"main","old_sha":"000000","new_sha":"com123"}}')

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            # Mock stream() to return an async context manager
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo({"id": "test-repo"})
            result = await (
                repo.create_commit(
                    {
                        "target_branch": "main",
                        "commit_message": "Authored by one, committed by another",
                        "author": {"name": "Author", "email": "author@example.com"},
                        "committer": {"name": "Committer", "email": "committer@example.com"},
                    }
                )
                .add_file_from_string("file.txt", "content")
                .send()
            )

            assert result is not None
            assert result["commit_sha"] == "com123"
