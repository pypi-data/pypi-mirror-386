"""Type definitions for Pierre Git Storage SDK."""

from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, Iterable, List, Literal, Optional, Protocol, Union

from typing_extensions import TypedDict


class DiffFileState(str, Enum):
    """File state in a diff."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    TYPE_CHANGED = "type_changed"
    UNMERGED = "unmerged"
    UNKNOWN = "unknown"


class GitFileMode(str, Enum):
    """Git file modes."""

    REGULAR = "100644"
    EXECUTABLE = "100755"
    SYMLINK = "120000"
    SUBMODULE = "160000"


# Configuration types
class GitStorageOptions(TypedDict, total=False):
    """Options for GitStorage client."""

    name: str  # required
    key: str  # required
    api_base_url: Optional[str]
    storage_base_url: Optional[str]
    api_version: Optional[int]
    default_ttl: Optional[int]


class GetRemoteURLOptions(TypedDict, total=False):
    """Options for generating remote URLs."""

    permissions: List[Literal["git:write", "git:read", "repo:write"]]
    ttl: int


class CreateRepoOptions(TypedDict, total=False):
    """Options for creating a repository."""

    id: str
    default_branch: str
    ttl: int


class FindOneOptions(TypedDict):
    """Options for finding a repository."""

    id: str


# File and branch types
class GetFileOptions(TypedDict, total=False):
    """Options for getting a file."""

    path: str  # required
    ref: Optional[str]
    ttl: int


class ListFilesOptions(TypedDict, total=False):
    """Options for listing files."""

    ref: Optional[str]
    ttl: int


class ListFilesResult(TypedDict):
    """Result from listing files."""

    paths: List[str]
    ref: str


class ListBranchesOptions(TypedDict, total=False):
    """Options for listing branches."""

    cursor: Optional[str]
    limit: int
    ttl: int


class BranchInfo(TypedDict):
    """Information about a branch."""

    cursor: str
    name: str
    head_sha: str
    created_at: str


class ListBranchesResult(TypedDict):
    """Result from listing branches."""

    branches: List[BranchInfo]
    next_cursor: Optional[str]
    has_more: bool


class ListCommitsOptions(TypedDict, total=False):
    """Options for listing commits."""

    branch: Optional[str]
    cursor: Optional[str]
    limit: int
    ttl: int


class CommitInfo(TypedDict):
    """Information about a commit."""

    sha: str
    message: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    date: datetime
    raw_date: str


class ListCommitsResult(TypedDict):
    """Result from listing commits."""

    commits: List[CommitInfo]
    next_cursor: Optional[str]
    has_more: bool


# Diff types
class DiffStats(TypedDict):
    """Statistics about a diff."""

    files: int
    additions: int
    deletions: int
    changes: int


class FileDiff(TypedDict):
    """A file diff entry."""

    path: str
    state: DiffFileState
    raw_state: str
    old_path: Optional[str]
    raw: str
    bytes: int
    is_eof: bool


class FilteredFile(TypedDict):
    """A filtered file entry."""

    path: str
    state: DiffFileState
    raw_state: str
    old_path: Optional[str]
    bytes: int
    is_eof: bool


class GetBranchDiffOptions(TypedDict, total=False):
    """Options for getting branch diff."""

    branch: str  # required
    base: Optional[str]
    ttl: int


class GetBranchDiffResult(TypedDict):
    """Result from getting branch diff."""

    branch: str
    base: str
    stats: DiffStats
    files: List[FileDiff]
    filtered_files: List[FilteredFile]


class GetCommitDiffOptions(TypedDict, total=False):
    """Options for getting commit diff."""

    sha: str  # required
    ttl: int


class GetCommitDiffResult(TypedDict):
    """Result from getting commit diff."""

    sha: str
    stats: DiffStats
    files: List[FileDiff]
    filtered_files: List[FilteredFile]


# Commit types
class CommitSignature(TypedDict):
    """Git commit signature."""

    name: str
    email: str


class CreateCommitOptions(TypedDict, total=False):
    """Options for creating a commit."""

    target_branch: str  # required
    commit_message: str  # required
    author: CommitSignature  # required
    expected_head_sha: Optional[str]
    committer: Optional[CommitSignature]
    ttl: int


class CommitFileOptions(TypedDict, total=False):
    """Options for adding a file to a commit."""

    mode: GitFileMode


class RefUpdate(TypedDict):
    """Information about a ref update."""

    branch: str
    old_sha: str
    new_sha: str


class CommitResult(TypedDict):
    """Result from creating a commit."""

    commit_sha: str
    tree_sha: str
    target_branch: str
    pack_bytes: int
    blob_count: int
    ref_update: RefUpdate


class RestoreCommitOptions(TypedDict, total=False):
    """Options for restoring a commit."""

    target_branch: str  # required
    target_commit_sha: str  # required
    author: CommitSignature  # required
    commit_message: Optional[str]
    expected_head_sha: Optional[str]
    committer: Optional[CommitSignature]
    ttl: int


class RestoreCommitResult(TypedDict):
    """Result from restoring a commit."""

    commit_sha: str
    tree_sha: str
    target_branch: str
    pack_bytes: int
    ref_update: RefUpdate


class PullUpstreamOptions(TypedDict, total=False):
    """Options for pulling from upstream."""

    ref: Optional[str]
    ttl: int


# File source types for commits
FileSource = Union[
    str,
    bytes,
    bytearray,
    memoryview,
    Iterable[bytes],
    AsyncIterator[bytes],
]


# Protocol for commit builder
class CommitBuilder(Protocol):
    """Protocol for commit builder."""

    def add_file(
        self,
        path: str,
        source: FileSource,
        options: Optional[CommitFileOptions] = None,
    ) -> "CommitBuilder":
        """Add a file to the commit."""
        ...

    def add_file_from_string(
        self,
        path: str,
        contents: str,
        encoding: str = "utf-8",
        options: Optional[CommitFileOptions] = None,
    ) -> "CommitBuilder":
        """Add a file from a string."""
        ...

    def delete_path(self, path: str) -> "CommitBuilder":
        """Delete a path from the commit."""
        ...

    async def send(self) -> CommitResult:
        """Send the commit to the server."""
        ...


# Protocol for repository
class Repo(Protocol):
    """Protocol for repository."""

    @property
    def id(self) -> str:
        """Get the repository ID."""
        ...

    async def get_remote_url(
        self, options: Optional[GetRemoteURLOptions] = None
    ) -> str:
        """Get the remote URL for the repository."""
        ...

    async def get_file_stream(
        self, options: GetFileOptions
    ) -> Any:  # httpx.Response
        """Get a file as a stream."""
        ...

    async def list_files(
        self, options: Optional[ListFilesOptions] = None
    ) -> ListFilesResult:
        """List files in the repository."""
        ...

    async def list_branches(
        self, options: Optional[ListBranchesOptions] = None
    ) -> ListBranchesResult:
        """List branches in the repository."""
        ...

    async def list_commits(
        self, options: Optional[ListCommitsOptions] = None
    ) -> ListCommitsResult:
        """List commits in the repository."""
        ...

    async def get_branch_diff(
        self, options: GetBranchDiffOptions
    ) -> GetBranchDiffResult:
        """Get diff between branches."""
        ...

    async def get_commit_diff(
        self, options: GetCommitDiffOptions
    ) -> GetCommitDiffResult:
        """Get diff for a commit."""
        ...

    async def pull_upstream(
        self, options: Optional[PullUpstreamOptions] = None
    ) -> None:
        """Pull from upstream repository."""
        ...

    async def restore_commit(
        self, options: RestoreCommitOptions
    ) -> RestoreCommitResult:
        """Restore a previous commit."""
        ...

    def create_commit(self, options: CreateCommitOptions) -> CommitBuilder:
        """Create a new commit builder."""
        ...


# Webhook types
class WebhookValidationOptions(TypedDict, total=False):
    """Options for webhook validation."""

    max_age_seconds: int


class WebhookValidationResult(TypedDict):
    """Result from webhook validation."""

    valid: bool
    error: Optional[str]
    event_type: Optional[str]
    timestamp: Optional[int]


class WebhookPushEvent(TypedDict):
    """Webhook push event."""

    type: Literal["push"]
    repository: Dict[str, str]
    ref: str
    before: str
    after: str
    customer_id: str
    pushed_at: datetime
    raw_pushed_at: str


class ParsedWebhookSignature(TypedDict):
    """Parsed webhook signature."""

    timestamp: str
    signature: str
