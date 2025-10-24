"""Tests for Repo operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre_storage import GitStorage
from pierre_storage.errors import RefUpdateError


class TestRepoFileOperations:
    """Tests for file operations."""

    @pytest.mark.asyncio
    async def test_get_file_stream(self, git_storage_options: dict) -> None:
        """Test getting file stream."""
        storage = GitStorage(git_storage_options)

        # Mock repo creation
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock file stream response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=file_response
            )

            repo = await storage.create_repo(id="test-repo")
            response = await repo.get_file_stream(path="README.md", ref="main")

            assert response is not None
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_files(self, git_storage_options: dict) -> None:
        """Test listing files in repository."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        list_response = MagicMock()
        list_response.status_code = 200
        list_response.is_success = True
        list_response.json.return_value = {
            "paths": ["README.md", "src/main.py", "package.json"],
            "ref": "main",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=list_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_files(ref="main")

            assert result is not None
            assert "paths" in result
            assert len(result["paths"]) == 3
            assert "README.md" in result["paths"]


class TestRepoBranchOperations:
    """Tests for branch operations."""

    @pytest.mark.asyncio
    async def test_list_branches(self, git_storage_options: dict) -> None:
        """Test listing branches."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        branches_response = MagicMock()
        branches_response.status_code = 200
        branches_response.is_success = True
        branches_response.json.return_value = {
            "branches": [
                {"cursor": "c1", "name": "main", "head_sha": "abc123", "created_at": "2025-01-01T00:00:00Z"},
                {"cursor": "c2", "name": "develop", "head_sha": "def456", "created_at": "2025-01-02T00:00:00Z"},
            ],
            "next_cursor": None,
            "has_more": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=branches_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_branches(limit=10)

            assert result is not None
            assert "branches" in result
            assert len(result["branches"]) == 2
            assert result["branches"][0]["name"] == "main"

    @pytest.mark.asyncio
    async def test_list_branches_with_pagination(self, git_storage_options: dict) -> None:
        """Test listing branches with pagination cursor."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        branches_response = MagicMock()
        branches_response.status_code = 200
        branches_response.is_success = True
        branches_response.json.return_value = {
            "branches": [{"cursor": "c3", "name": "feature-1", "head_sha": "ghi789", "created_at": "2025-01-03T00:00:00Z"}],
            "next_cursor": "next-page-token",
            "has_more": True,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=branches_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_branches(limit=1, cursor="some-cursor")

            assert result is not None
            assert result["next_cursor"] == "next-page-token"
            assert result["has_more"] is True


class TestRepoCommitOperations:
    """Tests for commit operations."""

    @pytest.mark.asyncio
    async def test_list_commits(self, git_storage_options: dict) -> None:
        """Test listing commits."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        commits_response = MagicMock()
        commits_response.status_code = 200
        commits_response.is_success = True
        commits_response.json.return_value = {
            "commits": [
                {
                    "sha": "abc123",
                    "message": "Initial commit",
                    "author_name": "Test User",
                    "author_email": "test@example.com",
                    "committer_name": "Test User",
                    "committer_email": "test@example.com",
                    "date": "2025-01-01T00:00:00Z",
                },
                {
                    "sha": "def456",
                    "message": "Second commit",
                    "author_name": "Test User",
                    "author_email": "test@example.com",
                    "committer_name": "Test User",
                    "committer_email": "test@example.com",
                    "date": "2025-01-02T00:00:00Z",
                },
            ],
            "next_cursor": None,
            "has_more": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=commits_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_commits(branch="main", limit=10)

            assert result is not None
            assert "commits" in result
            assert len(result["commits"]) == 2
            assert result["commits"][0]["sha"] == "abc123"
            assert result["commits"][0]["message"] == "Initial commit"

    @pytest.mark.asyncio
    async def test_restore_commit(self, git_storage_options: dict) -> None:
        """Test restoring to a previous commit."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        restore_response = MagicMock()
        restore_response.status_code = 200
        restore_response.is_success = True
        restore_response.json.return_value = {
            "commit": {
                "commit_sha": "new-commit-sha",
                "tree_sha": "new-tree-sha",
                "target_branch": "main",
                "pack_bytes": 1024,
                "blob_count": 0,
            },
            "result": {
                "success": True,
                "branch": "main",
                "old_sha": "old-sha",
                "new_sha": "new-commit-sha",
                "status": "ok",
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Mock both create and restore
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[create_response, restore_response]
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.restore_commit(
                target_branch="main",
                target_commit_sha="abc123",
                commit_message="Restore commit",
                author={"name": "Test", "email": "test@example.com"},
            )

            assert result is not None
            assert result["commit_sha"] == "new-commit-sha"
            assert result["ref_update"]["branch"] == "main"
            assert result["ref_update"]["new_sha"] == "new-commit-sha"
            assert result["ref_update"]["old_sha"] == "old-sha"


class TestRepoDiffOperations:
    """Tests for diff operations."""

    @pytest.mark.asyncio
    async def test_get_branch_diff(self, git_storage_options: dict) -> None:
        """Test getting branch diff."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        diff_response = MagicMock()
        diff_response.status_code = 200
        diff_response.is_success = True
        diff_response.json.return_value = {
            "branch": "feature",
            "base": "main",
            "stats": {"additions": 10, "deletions": 5, "files_changed": 2},
            "files": [
                {
                    "path": "README.md",
                    "state": "modified",
                    "raw": "diff --git ...",
                    "bytes": 100,
                    "is_eof": True,
                },
                {
                    "path": "new-file.py",
                    "state": "added",
                    "raw": "diff --git ...",
                    "bytes": 200,
                    "is_eof": True,
                },
            ],
            "filtered_files": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=diff_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.get_branch_diff(branch="feature", base="main")

            assert result is not None
            assert "stats" in result
            assert result["stats"]["additions"] == 10
            assert len(result["files"]) == 2

    @pytest.mark.asyncio
    async def test_get_commit_diff(self, git_storage_options: dict) -> None:
        """Test getting commit diff."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        diff_response = MagicMock()
        diff_response.status_code = 200
        diff_response.is_success = True
        diff_response.json.return_value = {
            "sha": "abc123",
            "stats": {"additions": 3, "deletions": 1, "files_changed": 1},
            "files": [
                {
                    "path": "config.json",
                    "state": "modified",
                    "raw": "diff --git a/config.json b/config.json...",
                    "bytes": 150,
                    "is_eof": True,
                }
            ],
            "filtered_files": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=diff_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.get_commit_diff(sha="abc123")

            assert result is not None
            assert "stats" in result
            assert result["stats"]["files_changed"] == 1
            assert result["files"][0]["path"] == "config.json"


class TestRepoUpstreamOperations:
    """Tests for upstream operations."""

    @pytest.mark.asyncio
    async def test_pull_upstream(self, git_storage_options: dict) -> None:
        """Test pulling from upstream."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        pull_response = MagicMock()
        pull_response.status_code = 202
        pull_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(side_effect=[create_response, pull_response])

            repo = await storage.create_repo(id="test-repo")
            # Should not raise an exception
            await repo.pull_upstream(ref="main")

    @pytest.mark.asyncio
    async def test_restore_commit_json_decode_error(self, git_storage_options: dict) -> None:
        """Test restoring commit with non-JSON response (e.g., CDN HTML on 5xx)."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock a 502 response with HTML instead of JSON
        restore_response = MagicMock()
        restore_response.status_code = 502
        restore_response.is_success = False
        restore_response.reason_phrase = "Bad Gateway"
        # Simulate JSON decode error
        restore_response.json.side_effect = Exception("JSON decode error")
        restore_response.aread = AsyncMock(return_value=b"<html><body>502 Bad Gateway</body></html>")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[create_response, restore_response]
            )

            repo = await storage.create_repo(id="test-repo")

            with pytest.raises(RefUpdateError) as exc_info:
                await repo.restore_commit(
                    target_branch="main",
                    target_commit_sha="abc123",
                    commit_message="Restore commit",
                    author={"name": "Test", "email": "test@example.com"},
                )

            # Verify we got a RefUpdateError with meaningful message
            assert "502" in str(exc_info.value)
            assert "Bad Gateway" in str(exc_info.value)
            assert exc_info.value.status == "unavailable"  # 502 maps to "unavailable"

    @pytest.mark.asyncio
    async def test_pull_upstream_no_branch(self, git_storage_options: dict) -> None:
        """Test pulling from upstream without specifying branch."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        pull_response = MagicMock()
        pull_response.status_code = 202
        pull_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(side_effect=[create_response, pull_response])

            repo = await storage.create_repo(id="test-repo")
            # Should work without branch option
            await repo.pull_upstream()
