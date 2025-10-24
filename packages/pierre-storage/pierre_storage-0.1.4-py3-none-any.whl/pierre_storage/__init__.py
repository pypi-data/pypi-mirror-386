"""Pierre Git Storage SDK for Python.

A Python SDK for interacting with Pierre's git storage system.
"""

from pierre_storage.client import GitStorage, create_client
from pierre_storage.errors import ApiError, RefUpdateError
from pierre_storage.types import (
    BranchInfo,
    CommitInfo,
    CommitResult,
    CommitSignature,
    CreateRepoOptions,
    DiffFileState,
    DiffStats,
    FileDiff,
    FilteredFile,
    GetBranchDiffOptions,
    GetBranchDiffResult,
    GetCommitDiffOptions,
    GetCommitDiffResult,
    GetFileOptions,
    GetRemoteURLOptions,
    GitStorageOptions,
    ListBranchesOptions,
    ListBranchesResult,
    ListCommitsOptions,
    ListCommitsResult,
    ListFilesOptions,
    ListFilesResult,
    RefUpdate,
    Repo,
    RestoreCommitOptions,
    RestoreCommitResult,
)
from pierre_storage.webhook import (
    WebhookPushEvent,
    parse_signature_header,
    validate_webhook,
    validate_webhook_signature,
)

__version__ = "0.1.4"

__all__ = [
    # Main client
    "GitStorage",
    "create_client",
    # Errors
    "ApiError",
    "RefUpdateError",
    # Types
    "BranchInfo",
    "CommitInfo",
    "CommitResult",
    "CommitSignature",
    "CreateRepoOptions",
    "DiffFileState",
    "DiffStats",
    "FileDiff",
    "FilteredFile",
    "GetBranchDiffOptions",
    "GetBranchDiffResult",
    "GetCommitDiffOptions",
    "GetCommitDiffResult",
    "GetFileOptions",
    "GetRemoteURLOptions",
    "GitStorageOptions",
    "ListBranchesOptions",
    "ListBranchesResult",
    "ListCommitsOptions",
    "ListCommitsResult",
    "ListFilesOptions",
    "ListFilesResult",
    "RefUpdate",
    "Repo",
    "RestoreCommitOptions",
    "RestoreCommitResult",
    # Webhook
    "WebhookPushEvent",
    "parse_signature_header",
    "validate_webhook",
    "validate_webhook_signature",
]
