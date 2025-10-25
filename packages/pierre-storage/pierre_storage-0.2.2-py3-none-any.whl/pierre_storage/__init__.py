"""Pierre Git Storage SDK for Python.

A Python SDK for interacting with Pierre's git storage system.
"""

from pierre_storage.client import GitStorage, create_client
from pierre_storage.errors import ApiError, RefUpdateError
from pierre_storage.types import (
    BaseRepo,
    BranchInfo,
    CommitInfo,
    CommitResult,
    CommitSignature,
    DiffFileState,
    DiffStats,
    FileDiff,
    FilteredFile,
    GetBranchDiffResult,
    GetCommitDiffResult,
    GitStorageOptions,
    ListBranchesResult,
    ListCommitsResult,
    ListFilesResult,
    RefUpdate,
    Repo,
    RestoreCommitResult,
)
from pierre_storage.webhook import (
    WebhookPushEvent,
    parse_signature_header,
    validate_webhook,
    validate_webhook_signature,
)

__version__ = "0.2.2"

__all__ = [
    # Main client
    "GitStorage",
    "create_client",
    # Errors
    "ApiError",
    "RefUpdateError",
    # Types
    "BaseRepo",
    "BranchInfo",
    "CommitInfo",
    "CommitResult",
    "CommitSignature",
    "DiffFileState",
    "DiffStats",
    "FileDiff",
    "FilteredFile",
    "GetBranchDiffResult",
    "GetCommitDiffResult",
    "GitStorageOptions",
    "ListBranchesResult",
    "ListCommitsResult",
    "ListFilesResult",
    "RefUpdate",
    "Repo",
    "RestoreCommitResult",
    # Webhook
    "WebhookPushEvent",
    "parse_signature_header",
    "validate_webhook",
    "validate_webhook_signature",
]
