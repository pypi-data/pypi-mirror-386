"""Commit builder for Pierre Git Storage SDK."""

import base64
import json
import uuid
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import httpx

from pierre_storage.errors import RefUpdateError, infer_ref_update_reason
from pierre_storage.types import (
    CommitFileOptions,
    CommitResult,
    CreateCommitOptions,
    FileSource,
    GitFileMode,
    RefUpdate,
)

MAX_CHUNK_BYTES = 4 * 1024 * 1024  # 4 MiB
DEFAULT_TTL_SECONDS = 3600  # 1 hour


class FileOperation:
    """Represents a file operation in a commit."""

    def __init__(
        self,
        path: str,
        content_id: str,
        operation: str,
        mode: Optional[str] = None,
        source: Optional[FileSource] = None,
    ) -> None:
        """Initialize a file operation.

        Args:
            path: File path
            content_id: Unique content identifier
            operation: Operation type ('upsert' or 'delete')
            mode: Git file mode
            source: File content source
        """
        self.path = path
        self.content_id = content_id
        self.operation = operation
        self.mode = mode
        self.source = source


class CommitBuilderImpl:
    """Implementation of commit builder for creating commits."""

    def __init__(
        self,
        options: CreateCommitOptions,
        get_auth_token: Callable[[], str],
        base_url: str,
        api_version: int,
    ) -> None:
        """Initialize the commit builder.

        Args:
            options: Commit options
            get_auth_token: Function to get auth token
            base_url: API base URL
            api_version: API version

        Raises:
            ValueError: If required options are missing or invalid
        """
        self.options = options
        self.get_auth_token = get_auth_token
        self.url = f"{base_url.rstrip('/')}/api/v{api_version}/repos/commit-pack"
        self.operations: List[FileOperation] = []
        self.sent = False

        # Validate required options
        target_branch = options.get("target_branch", "").strip()
        if not target_branch:
            raise ValueError("createCommit target_branch is required")
        if target_branch.startswith("refs/"):
            raise ValueError("createCommit target_branch must not include refs/ prefix")

        commit_message = options.get("commit_message", "").strip()
        if not commit_message:
            raise ValueError("createCommit commit_message is required")

        author = options.get("author")
        if not author:
            raise ValueError("createCommit author is required")

        author_name = author.get("name", "").strip()
        author_email = author.get("email", "").strip()
        if not author_name or not author_email:
            raise ValueError("createCommit author name and email are required")

        # Update options with trimmed values
        self.options["target_branch"] = target_branch
        self.options["commit_message"] = commit_message
        self.options["author"] = {"name": author_name, "email": author_email}

        # Trim expected_head_sha if present
        expected_head_sha = options.get("expected_head_sha")
        if expected_head_sha:
            self.options["expected_head_sha"] = expected_head_sha.strip()

    def add_file(
        self,
        path: str,
        source: FileSource,
        options: Optional[CommitFileOptions] = None,
    ) -> "CommitBuilderImpl":
        """Add a file to the commit.

        Args:
            path: File path
            source: File content source
            options: File options (mode, etc.)

        Returns:
            Self for chaining

        Raises:
            RuntimeError: If builder has already been sent
        """
        self._ensure_not_sent()
        normalized_path = self._normalize_path(path)
        content_id = str(uuid.uuid4())
        mode = options.get("mode", GitFileMode.REGULAR) if options else GitFileMode.REGULAR

        self.operations.append(
            FileOperation(
                path=normalized_path,
                content_id=content_id,
                operation="upsert",
                mode=mode,
                source=source,
            )
        )
        return self

    def add_file_from_string(
        self,
        path: str,
        contents: str,
        encoding: str = "utf-8",
        options: Optional[CommitFileOptions] = None,
    ) -> "CommitBuilderImpl":
        """Add a file from a string.

        Args:
            path: File path
            contents: File contents as string
            encoding: Text encoding (default: utf-8)
            options: File options (mode, etc.)

        Returns:
            Self for chaining
        """
        data = contents.encode(encoding)
        return self.add_file(path, data, options)

    def delete_path(self, path: str) -> "CommitBuilderImpl":
        """Delete a path from the commit.

        Args:
            path: Path to delete

        Returns:
            Self for chaining

        Raises:
            RuntimeError: If builder has already been sent
        """
        self._ensure_not_sent()
        normalized_path = self._normalize_path(path)
        self.operations.append(
            FileOperation(
                path=normalized_path,
                content_id=str(uuid.uuid4()),
                operation="delete",
            )
        )
        return self

    async def send(self) -> CommitResult:
        """Send the commit to the server.

        Returns:
            Commit result with SHA and ref update info

        Raises:
            RuntimeError: If builder has already been sent
            RefUpdateError: If commit fails
        """
        self._ensure_not_sent()
        self.sent = True

        metadata = self._build_metadata()
        auth_token = self.get_auth_token()

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/x-ndjson",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.url,
                headers=headers,
                content=self._build_request_body(metadata),
                timeout=180.0,
            ) as response:
                if not response.is_success:
                    error_info = await self._parse_error(response)
                    raise RefUpdateError(
                        error_info["message"],
                        status=error_info["status"],
                        reason=error_info["status"],
                        ref_update=error_info.get("ref_update"),
                    )

                result_data = await response.aread()
                result = json.loads(result_data)
                return self._build_commit_result(result)

    def _build_metadata(self) -> Dict[str, Any]:
        """Build metadata payload for commit."""
        files = []
        for op in self.operations:
            file_entry: Dict[str, Any] = {
                "path": op.path,
                "content_id": op.content_id,
                "operation": op.operation,
            }
            if op.mode:
                file_entry["mode"] = op.mode
            files.append(file_entry)

        metadata: Dict[str, Any] = {
            "target_branch": self.options["target_branch"],
            "commit_message": self.options["commit_message"],
            "author": self.options["author"],
            "files": files,
        }

        if "expected_head_sha" in self.options:
            metadata["expected_head_sha"] = self.options["expected_head_sha"]

        if "committer" in self.options:
            metadata["committer"] = self.options["committer"]

        return metadata

    async def _build_request_body(
        self, metadata: Dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Build NDJSON request body with metadata and blob chunks."""
        # First line: metadata
        yield json.dumps({"metadata": metadata}).encode("utf-8") + b"\n"

        # Subsequent lines: blob chunks
        for op in self.operations:
            if op.operation == "upsert" and op.source is not None:
                async for chunk in self._chunkify(op.source):
                    blob_chunk = {
                        "blob_chunk": {
                            "content_id": op.content_id,
                            "data": base64.b64encode(chunk["chunk"]).decode("ascii"),
                            "eof": chunk["eof"],
                        }
                    }
                    yield json.dumps(blob_chunk).encode("utf-8") + b"\n"

    async def _chunkify(
        self, source: FileSource
    ) -> AsyncIterator[Dict[str, Any]]:
        """Chunkify a file source into MAX_CHUNK_BYTES segments."""
        pending: Optional[bytes] = None
        produced = False

        async for data in self._to_async_iterator(source):
            # If we have a full chunk ready, yield it
            if pending and len(pending) == MAX_CHUNK_BYTES:
                yield {"chunk": pending, "eof": False}
                produced = True
                pending = None

            # Merge with pending data
            if pending:
                merged = pending + data
                pending = None
            else:
                merged = data

            # Yield full chunks
            while len(merged) > MAX_CHUNK_BYTES:
                chunk = merged[:MAX_CHUNK_BYTES]
                merged = merged[MAX_CHUNK_BYTES:]
                yield {"chunk": chunk, "eof": False}
                produced = True

            pending = merged

        # Yield final chunk
        if pending:
            yield {"chunk": pending, "eof": True}
            produced = True

        # Ensure at least one chunk is produced
        if not produced:
            yield {"chunk": b"", "eof": True}

    async def _to_async_iterator(self, source: FileSource) -> AsyncIterator[bytes]:
        """Convert various source types to async iterator of bytes."""
        if isinstance(source, str):
            yield source.encode("utf-8")
        elif isinstance(source, (bytes, bytearray, memoryview)):
            yield bytes(source)
        elif hasattr(source, "__aiter__"):
            # Async iterable
            async for chunk in source:  # type: ignore
                if isinstance(chunk, str):
                    yield chunk.encode("utf-8")
                else:
                    yield bytes(chunk)
        elif hasattr(source, "__iter__"):
            # Sync iterable
            for chunk in source:  # type: ignore
                if isinstance(chunk, str):
                    yield chunk.encode("utf-8")
                else:
                    yield bytes(chunk)
        else:
            raise TypeError(f"Unsupported file source type: {type(source)}")

    def _build_commit_result(self, ack: Dict[str, Any]) -> CommitResult:
        """Build commit result from server acknowledgment."""
        result = ack.get("result", {})
        ref_update = self._to_ref_update(result)

        if not result.get("success"):
            raise RefUpdateError(
                result.get("message", f"Commit failed with status {result.get('status')}"),
                status=result.get("status"),
                ref_update=ref_update,
            )

        commit = ack.get("commit", {})
        return {
            "commit_sha": commit["commit_sha"],
            "tree_sha": commit["tree_sha"],
            "target_branch": commit["target_branch"],
            "pack_bytes": commit["pack_bytes"],
            "blob_count": commit["blob_count"],
            "ref_update": ref_update,
        }

    def _to_ref_update(self, result: Dict[str, Any]) -> RefUpdate:
        """Convert result to ref update."""
        return {
            "branch": result.get("branch", ""),
            "old_sha": result.get("old_sha", ""),
            "new_sha": result.get("new_sha", ""),
        }

    async def _parse_error(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse error response from server."""
        default_status = infer_ref_update_reason(str(response.status_code))
        status = default_status
        message = f"createCommit request failed ({response.status_code} {response.reason_phrase})"
        ref_update = None

        try:
            data = await response.aread()
            json_data = json.loads(data)

            # Try to parse as commit pack response
            if "result" in json_data:
                result = json_data["result"]
                if result.get("status"):
                    status = result["status"]
                if result.get("message"):
                    message = result["message"]
                ref_update = {
                    "branch": result.get("branch"),
                    "old_sha": result.get("old_sha"),
                    "new_sha": result.get("new_sha"),
                }
                ref_update = {k: v for k, v in ref_update.items() if v}

            # Try to parse as error envelope
            elif "error" in json_data:
                message = json_data["error"]

        except Exception:
            # Use default message if parsing fails
            pass

        return {
            "status": status,
            "message": message,
            "ref_update": ref_update,
        }

    def _ensure_not_sent(self) -> None:
        """Ensure the builder hasn't been sent yet."""
        if self.sent:
            raise RuntimeError("createCommit builder cannot be reused after send()")

    def _normalize_path(self, path: str) -> str:
        """Normalize a file path."""
        if not path or not isinstance(path, str) or not path.strip():
            raise ValueError("File path must be a non-empty string")
        return path.lstrip("/")


def resolve_commit_ttl_seconds(options: Optional[CreateCommitOptions]) -> int:
    """Resolve TTL for commit operations."""
    if options and "ttl" in options:
        ttl = options["ttl"]
        if ttl and ttl > 0:
            return ttl
    return DEFAULT_TTL_SECONDS
