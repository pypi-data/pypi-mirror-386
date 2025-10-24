"""Repository implementation for Pierre Git Storage SDK."""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field

from pierre_storage.commit import CommitBuilderImpl, resolve_commit_ttl_seconds
from pierre_storage.errors import RefUpdateError, infer_ref_update_reason
from pierre_storage.types import (
    BranchInfo,
    CommitBuilder,
    CommitInfo,
    CommitSignature,
    CreateCommitOptions,
    DiffFileState,
    FileDiff,
    FilteredFile,
    GetBranchDiffResult,
    GetCommitDiffResult,
    ListBranchesResult,
    ListCommitsResult,
    ListFilesResult,
    RefUpdate,
    RestoreCommitResult,
)

DEFAULT_TOKEN_TTL_SECONDS = 3600  # 1 hour


def resolve_invocation_ttl_seconds(
    options: Optional[Dict[str, Any]] = None,
    default_value: int = DEFAULT_TOKEN_TTL_SECONDS,
) -> int:
    """Resolve TTL for API invocations."""
    if options and "ttl" in options:
        ttl = options["ttl"]
        if isinstance(ttl, int) and ttl > 0:
            return int(ttl)
    return default_value


def normalize_diff_state(raw_state: str) -> DiffFileState:
    """Normalize diff state from raw format."""
    if not raw_state:
        return DiffFileState.UNKNOWN

    leading = raw_state.strip()[0].upper() if raw_state.strip() else ""
    state_map = {
        "A": DiffFileState.ADDED,
        "M": DiffFileState.MODIFIED,
        "D": DiffFileState.DELETED,
        "R": DiffFileState.RENAMED,
        "C": DiffFileState.COPIED,
        "T": DiffFileState.TYPE_CHANGED,
        "U": DiffFileState.UNMERGED,
    }
    return state_map.get(leading, DiffFileState.UNKNOWN)


class RepoImpl:
    """Implementation of repository operations."""

    def __init__(
        self,
        repo_id: str,
        api_base_url: str,
        storage_base_url: str,
        name: str,
        api_version: int,
        generate_jwt: Callable[[str, Optional[Dict[str, Any]]], str],
    ) -> None:
        """Initialize repository.

        Args:
            repo_id: Repository identifier
            api_base_url: API base URL
            storage_base_url: Storage base URL
            name: Customer name
            api_version: API version
            generate_jwt: Function to generate JWT tokens
        """
        self._id = repo_id
        self.api_base_url = api_base_url.rstrip("/")
        self.storage_base_url = storage_base_url
        self.name = name
        self.api_version = api_version
        self.generate_jwt = generate_jwt

    @property
    def id(self) -> str:
        """Get repository ID."""
        return self._id

    async def get_remote_url(
        self,
        *,
        permissions: Optional[list[str]] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """Get remote URL for Git operations.

        Args:
            permissions: List of permissions (e.g., ["git:write", "git:read"])
            ttl: Token TTL in seconds

        Returns:
            Git remote URL with embedded JWT
        """
        options: Dict[str, Any] = {}
        if permissions is not None:
            options["permissions"] = permissions
        if ttl is not None:
            options["ttl"] = ttl

        jwt_token = self.generate_jwt(self._id, options if options else None)
        url = f"https://t:{jwt_token}@{self.name}.{self.storage_base_url}/{self._id}.git"
        return url

    async def get_file_stream(
        self,
        *,
        path: str,
        ref: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> httpx.Response:
        """Get file content as streaming response.

        Args:
            path: File path to retrieve
            ref: Git ref (branch, tag, or commit SHA)
            ttl: Token TTL in seconds

        Returns:
            HTTP response with file content stream
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {"path": path}
        if ref:
            params["ref"] = ref

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/file"
        if params:
            url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response

    async def list_files(
        self,
        *,
        ref: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> ListFilesResult:
        """List files in repository.

        Args:
            ref: Git ref (branch, tag, or commit SHA)
            ttl: Token TTL in seconds

        Returns:
            List of file paths and ref
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {}
        if ref:
            params["ref"] = ref

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/files"
        if params:
            url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return {"paths": data["paths"], "ref": data["ref"]}

    async def list_branches(
        self,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> ListBranchesResult:
        """List branches in repository.

        Args:
            cursor: Pagination cursor
            limit: Maximum number of branches to return
            ttl: Token TTL in seconds

        Returns:
            List of branches with pagination info
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/branches"
        if params:
            url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            branches: List[BranchInfo] = [
                {
                    "cursor": b["cursor"],
                    "name": b["name"],
                    "head_sha": b["head_sha"],
                    "created_at": b["created_at"],
                }
                for b in data["branches"]
            ]

            return {
                "branches": branches,
                "next_cursor": data.get("next_cursor"),
                "has_more": data["has_more"],
            }

    async def list_commits(
        self,
        *,
        branch: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> ListCommitsResult:
        """List commits in repository.

        Args:
            branch: Branch name to list commits from
            cursor: Pagination cursor
            limit: Maximum number of commits to return
            ttl: Token TTL in seconds

        Returns:
            List of commits with pagination info
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {}
        if branch:
            params["branch"] = branch
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/commits"
        if params:
            url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            commits: List[CommitInfo] = []
            for c in data["commits"]:
                date = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
                commits.append(
                    {
                        "sha": c["sha"],
                        "message": c["message"],
                        "author_name": c["author_name"],
                        "author_email": c["author_email"],
                        "committer_name": c["committer_name"],
                        "committer_email": c["committer_email"],
                        "date": date,
                        "raw_date": c["date"],
                    }
                )

            return {
                "commits": commits,
                "next_cursor": data.get("next_cursor"),
                "has_more": data["has_more"],
            }

    async def get_branch_diff(
        self,
        *,
        branch: str,
        base: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> GetBranchDiffResult:
        """Get diff between branches.

        Args:
            branch: Target branch name
            base: Base branch name (for comparison)
            ttl: Token TTL in seconds

        Returns:
            Branch diff with stats and file changes
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {"branch": branch}
        if base:
            params["base"] = base

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/branches/diff"
        url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            files: List[FileDiff] = []
            for f in data["files"]:
                files.append(
                    {
                        "path": f["path"],
                        "state": normalize_diff_state(f["state"]),
                        "raw_state": f["state"],
                        "old_path": f.get("old_path"),
                        "raw": f["raw"],
                        "bytes": f["bytes"],
                        "is_eof": f["is_eof"],
                    }
                )

            filtered_files: List[FilteredFile] = []
            for f in data.get("filtered_files", []):
                filtered_files.append(
                    {
                        "path": f["path"],
                        "state": normalize_diff_state(f["state"]),
                        "raw_state": f["state"],
                        "old_path": f.get("old_path"),
                        "bytes": f["bytes"],
                        "is_eof": f["is_eof"],
                    }
                )

            return {
                "branch": data["branch"],
                "base": data["base"],
                "stats": data["stats"],
                "files": files,
                "filtered_files": filtered_files,
            }

    async def get_commit_diff(
        self,
        *,
        sha: str,
        ttl: Optional[int] = None,
    ) -> GetCommitDiffResult:
        """Get diff for a specific commit.

        Args:
            sha: Commit SHA
            ttl: Token TTL in seconds

        Returns:
            Commit diff with stats and file changes
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:read"], "ttl": ttl})

        params = {"sha": sha}
        url = f"{self.api_base_url}/api/v{self.api_version}/repos/diff"
        url += f"?{urlencode(params)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            files: List[FileDiff] = []
            for f in data["files"]:
                files.append(
                    {
                        "path": f["path"],
                        "state": normalize_diff_state(f["state"]),
                        "raw_state": f["state"],
                        "old_path": f.get("old_path"),
                        "raw": f["raw"],
                        "bytes": f["bytes"],
                        "is_eof": f["is_eof"],
                    }
                )

            filtered_files: List[FilteredFile] = []
            for f in data.get("filtered_files", []):
                filtered_files.append(
                    {
                        "path": f["path"],
                        "state": normalize_diff_state(f["state"]),
                        "raw_state": f["state"],
                        "old_path": f.get("old_path"),
                        "bytes": f["bytes"],
                        "is_eof": f["is_eof"],
                    }
                )

            return {
                "sha": data["sha"],
                "stats": data["stats"],
                "files": files,
                "filtered_files": filtered_files,
            }

    async def pull_upstream(
        self,
        *,
        ref: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Pull from upstream repository.

        Args:
            ref: Git ref to pull
            ttl: Token TTL in seconds

        Raises:
            ApiError: If pull fails
        """
        ttl = ttl or DEFAULT_TOKEN_TTL_SECONDS
        jwt = self.generate_jwt(self._id, {"permissions": ["git:write"], "ttl": ttl})

        body = {}
        if ref:
            body["ref"] = ref

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/pull-upstream"

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

            if response.status_code != 202:
                text = await response.aread()
                raise Exception(f"Pull Upstream failed: {response.status_code} {text.decode()}")

    async def restore_commit(
        self,
        *,
        target_branch: str,
        target_commit_sha: str,
        author: CommitSignature,
        commit_message: Optional[str] = None,
        expected_head_sha: Optional[str] = None,
        committer: Optional[CommitSignature] = None,
        ttl: Optional[int] = None,
    ) -> RestoreCommitResult:
        """Restore a previous commit.

        Args:
            target_branch: Target branch name
            target_commit_sha: Commit SHA to restore
            author: Author signature (name and email)
            commit_message: Optional commit message
            expected_head_sha: Expected HEAD SHA for optimistic locking
            committer: Optional committer signature (name and email)
            ttl: Token TTL in seconds

        Returns:
            Restore result with commit info

        Raises:
            ValueError: If required options are missing
            RefUpdateError: If restore fails
        """
        target_branch = target_branch.strip()
        if not target_branch:
            raise ValueError("restoreCommit target_branch is required")
        if target_branch.startswith("refs/"):
            raise ValueError("restoreCommit target_branch must not include refs/ prefix")

        target_commit_sha = target_commit_sha.strip()
        if not target_commit_sha:
            raise ValueError("restoreCommit target_commit_sha is required")

        author_name = author.get("name", "").strip()
        author_email = author.get("email", "").strip()
        if not author_name or not author_email:
            raise ValueError("restoreCommit author name and email are required")

        ttl = ttl or resolve_commit_ttl_seconds(None)
        jwt = self.generate_jwt(self._id, {"permissions": ["git:write"], "ttl": ttl})

        metadata: Dict[str, Any] = {
            "target_branch": target_branch,
            "target_commit_sha": target_commit_sha,
            "author": {"name": author_name, "email": author_email},
        }

        if commit_message:
            metadata["commit_message"] = commit_message.strip()

        if expected_head_sha:
            metadata["expected_head_sha"] = expected_head_sha.strip()

        if committer:
            committer_name = committer.get("name", "").strip()
            committer_email = committer.get("email", "").strip()
            if not committer_name or not committer_email:
                raise ValueError(
                    "restoreCommit committer name and email are required when provided"
                )
            metadata["committer"] = {"name": committer_name, "email": committer_email}

        url = f"{self.api_base_url}/api/v{self.api_version}/repos/restore-commit"

        allowed_status = [400, 401, 403, 404, 408, 409, 412, 422, 429, 499, 500, 502, 503, 504]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "Content-Type": "application/json",
                },
                json={"metadata": metadata},
                timeout=180.0,
            )

            # Try to parse JSON response, fallback to text for 5xx errors
            try:
                payload = response.json()
            except Exception:
                # If JSON parsing fails (e.g., CDN HTML response on 5xx), use text
                status = infer_ref_update_reason(str(response.status_code))
                text = await response.aread()
                message = f"Restore commit failed with HTTP {response.status_code}"
                if response.reason_phrase:
                    message += f" {response.reason_phrase}"
                # Include response body for debugging
                if text:
                    message += f": {text.decode('utf-8', errors='replace')[:200]}"
                raise RefUpdateError(message, status=status)

            # Check if we got a successful acknowledgment
            if "commit" in payload and "result" in payload:
                result = payload["result"]
                ref_update = self._to_ref_update(result)

                if not result.get("success"):
                    raise RefUpdateError(
                        result.get(
                            "message", f"Restore commit failed with status {result.get('status')}"
                        ),
                        status=result.get("status"),
                        ref_update=ref_update,
                    )

                commit = payload["commit"]
                return {
                    "commit_sha": commit["commit_sha"],
                    "tree_sha": commit["tree_sha"],
                    "target_branch": commit["target_branch"],
                    "pack_bytes": commit["pack_bytes"],
                    "ref_update": ref_update,
                }

            # Handle error response
            status = infer_ref_update_reason(str(response.status_code))
            message = f"Restore commit failed with HTTP {response.status_code}"
            if response.reason_phrase:
                message += f" {response.reason_phrase}"

            raise RefUpdateError(message, status=status)

    def create_commit(
        self,
        *,
        target_branch: str,
        commit_message: str,
        author: CommitSignature,
        expected_head_sha: Optional[str] = None,
        committer: Optional[CommitSignature] = None,
        ttl: Optional[int] = None,
    ) -> CommitBuilder:
        """Create a new commit builder.

        Args:
            target_branch: Target branch name
            commit_message: Commit message
            author: Author signature (name and email)
            expected_head_sha: Expected HEAD SHA for optimistic locking
            committer: Optional committer signature (name and email)
            ttl: Token TTL in seconds

        Returns:
            Commit builder for fluent API
        """
        options: CreateCommitOptions = {
            "target_branch": target_branch,
            "commit_message": commit_message,
            "author": author,
        }
        if expected_head_sha:
            options["expected_head_sha"] = expected_head_sha
        if committer:
            options["committer"] = committer

        ttl = ttl or resolve_commit_ttl_seconds(None)
        options["ttl"] = ttl

        def get_auth_token() -> str:
            return self.generate_jwt(
                self._id,
                {"permissions": ["git:write"], "ttl": ttl},
            )

        return CommitBuilderImpl(
            options,
            get_auth_token,
            self.api_base_url,
            self.api_version,
        )

    def _to_ref_update(self, result: Dict[str, Any]) -> RefUpdate:
        """Convert result to ref update."""
        return {
            "branch": result.get("branch", ""),
            "old_sha": result.get("old_sha", ""),
            "new_sha": result.get("new_sha", ""),
        }
