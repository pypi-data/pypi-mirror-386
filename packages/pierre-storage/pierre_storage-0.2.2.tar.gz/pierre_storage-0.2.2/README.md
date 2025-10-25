# pierre-storage

Pierre Git Storage SDK for Python applications.

## Installation

```bash
# Using uv (recommended)
uv add pierre-storage

# Or using pip
pip install pierre-storage
```

## Usage

### Basic Setup

```python
from pierre_storage import GitStorage

# Initialize the client with your name and key
storage = GitStorage({
    "name": "your-name",  # e.g., 'v0'
    "key": "your-key",  # Your API key in PEM format
})
```

### Creating a Repository

```python
# Create a new repository with auto-generated ID
repo = await storage.create_repo()
print(repo.id)  # e.g., '123e4567-e89b-12d3-a456-426614174000'

# Create a repository with custom ID
custom_repo = await storage.create_repo(id="my-custom-repo")
print(custom_repo.id)  # 'my-custom-repo'

# Create a repository with GitHub sync
github_repo = await storage.create_repo(
    id="my-synced-repo",
    base_repo={
        "owner": "octocat",
        "name": "Hello-World",
        "default_branch": "main",  # optional
    }
)
# This repository will sync with github.com/octocat/Hello-World
```

### Finding a Repository

```python
found_repo = await storage.find_one(id="repo-id")
if found_repo:
    url = await found_repo.get_remote_url()
    print(f"Repository URL: {url}")
```

### Getting Remote URLs

The SDK generates secure URLs with JWT authentication for Git operations:

```python
# Get URL with default permissions (git:write, git:read) and 1-year TTL
url = await repo.get_remote_url()
# Returns: https://t:JWT@your-name.code.storage/repo-id.git

# Configure the Git remote
print(f"Run: git remote add origin {url}")

# Get URL with custom permissions and TTL
read_only_url = await repo.get_remote_url(
    permissions=["git:read"],  # Read-only access
    ttl=3600,  # 1 hour in seconds
)

# Available permissions:
# - 'git:read'   - Read access to Git repository
# - 'git:write'  - Write access to Git repository
# - 'repo:write' - Create a repository
```

### Working with Repository Content

Once you have a repository instance, you can perform various Git operations:

```python
repo = await storage.create_repo()
# or
repo = await storage.find_one(id="existing-repo-id")

# Get file content (streaming)
response = await repo.get_file_stream(
    path="README.md",
    ref="main",  # optional, defaults to default branch
)
text = await response.aread()
print(text.decode())

# List all files in the repository
files = await repo.list_files(
    ref="main",  # optional, defaults to default branch
)
print(files["paths"])  # List of file paths

# List branches
branches = await repo.list_branches(
    limit=10,
    cursor=None,  # for pagination
)
print(branches["branches"])

# List commits
commits = await repo.list_commits(
    branch="main",  # optional
    limit=20,
    cursor=None,  # for pagination
)
print(commits["commits"])

# Get branch diff
branch_diff = await repo.get_branch_diff(
    branch="feature-branch",
    base="main",  # optional, defaults to main
)
print(branch_diff["stats"])
print(branch_diff["files"])

# Get commit diff
commit_diff = await repo.get_commit_diff(
    sha="abc123...",
)
print(commit_diff["stats"])
print(commit_diff["files"])
```

### Creating Commits

The SDK provides a fluent builder API for creating commits with streaming support:

```python
# Create a commit
result = await (
    repo.create_commit(
        target_branch="main",
        commit_message="Update docs",
        author={"name": "Docs Bot", "email": "docs@example.com"},
    )
    .add_file_from_string("docs/changelog.md", "# v2.0.1\n- add streaming SDK\n")
    .add_file("docs/readme.md", b"Binary content here")
    .delete_path("docs/legacy.txt")
    .send()
)

print(result["commit_sha"])
print(result["ref_update"]["new_sha"])
print(result["ref_update"]["old_sha"])  # All zeroes when ref is created
```

The builder exposes:

- `add_file(path, source, *, mode=None)` - Attach bytes from various sources
- `add_file_from_string(path, contents, encoding="utf-8", *, mode=None)` - Add text files (defaults to UTF-8)
- `delete_path(path)` - Remove files or folders
- `send()` - Finalize the commit and receive metadata

`send()` returns a result with:

```python
{
    "commit_sha": str,
    "tree_sha": str,
    "target_branch": str,
    "pack_bytes": int,
    "blob_count": int,
    "ref_update": {
        "branch": str,
        "old_sha": str,  # All zeroes when the ref is created
        "new_sha": str,
    }
}
```

If the backend reports a failure, the builder raises a `RefUpdateError` containing the status, reason, and ref details.

**Options:**

- `target_branch` (required): Branch name (without `refs/heads/` prefix)
- `expected_head_sha` (optional): Branch or commit that must match the remote tip
- `commit_message` (required): The commit message
- `author` (required): Dictionary with `name` and `email`
- `committer` (optional): Dictionary with `name` and `email` (defaults to author)

> Files are chunked into 4 MiB segments, allowing streaming of large assets without buffering in memory.

> The `target_branch` must already exist on the remote repository. To seed an empty repository, omit `expected_head_sha`; the service will create the first commit only when no refs are present.

### Streaming Large Files

The commit builder accepts async iterables, allowing streaming of large files:

```python
async def file_chunks():
    """Generate file chunks asynchronously."""
    with open("/tmp/large-file.zip", "rb") as f:
        while chunk := f.read(1024 * 1024):  # Read 1MB at a time
            yield chunk

result = await (
    repo.create_commit(
        target_branch="assets",
        expected_head_sha="abc123...",
        commit_message="Upload latest design bundle",
        author={"name": "Assets Uploader", "email": "assets@example.com"},
    )
    .add_file("assets/design-kit.zip", file_chunks())
    .send()
)
```

### GitHub Repository Sync

You can create a Pierre repository that syncs with a GitHub repository:

```python
# Create a repository synced with GitHub
repo = await storage.create_repo(
    id="my-synced-repo",
    base_repo={
        "owner": "your-org",
        "name": "your-repo",
        "default_branch": "main",  # optional, defaults to "main"
    }
)

# Pull latest changes from GitHub upstream
await repo.pull_upstream()

# Now you can work with the synced content
files = await repo.list_files()
commits = await repo.list_commits()
```

**How it works:**

1. When you create a repo with `base_repo`, Pierre links it to the specified GitHub repository
2. The `pull_upstream()` method fetches the latest changes from GitHub
3. You can then use all Pierre SDK features (diffs, commits, file access) on the synced content
4. The provider is automatically set to `"github"` when using `base_repo`

### Restoring Commits

You can restore a repository to a previous commit:

```python
result = await repo.restore_commit(
    target_branch="main",
    target_commit_sha="abc123...",  # Commit to restore to
    expected_head_sha="def456...",  # Optional: current HEAD for safety
    commit_message="Restore to stable version",
    author={"name": "DevOps", "email": "devops@example.com"},
)

print(result["commit_sha"])
print(result["ref_update"])
```

## API Reference

### GitStorage

```python
class GitStorage:
    def __init__(self, options: GitStorageOptions) -> None: ...
    async def create_repo(
        self,
        *,
        id: Optional[str] = None,
        default_branch: str = "main",
        base_repo: Optional[BaseRepo] = None,
        ttl: Optional[int] = None,
    ) -> Repo: ...
    async def find_one(self, *, id: str) -> Optional[Repo]: ...
    def get_config(self) -> GitStorageOptions: ...
```

### Repo

```python
class Repo:
    @property
    def id(self) -> str: ...

    async def get_remote_url(
        self,
        *,
        permissions: Optional[List[str]] = None,
        ttl: Optional[int] = None,
    ) -> str: ...

    async def get_file_stream(
        self,
        *,
        path: str,
        ref: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> Response: ...

    async def list_files(
        self,
        *,
        ref: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> ListFilesResult: ...

    async def list_branches(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> ListBranchesResult: ...

    async def list_commits(
        self,
        *,
        branch: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> ListCommitsResult: ...

    async def get_branch_diff(
        self,
        *,
        branch: str,
        base: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> GetBranchDiffResult: ...

    async def get_commit_diff(
        self,
        *,
        sha: str,
        ttl: Optional[int] = None,
    ) -> GetCommitDiffResult: ...

    async def pull_upstream(
        self,
        *,
        ttl: Optional[int] = None,
    ) -> None: ...

    async def restore_commit(
        self,
        *,
        target_branch: str,
        target_commit_sha: str,
        expected_head_sha: Optional[str] = None,
        commit_message: str,
        author: CommitSignature,
        committer: Optional[CommitSignature] = None,
        ttl: Optional[int] = None,
    ) -> RestoreCommitResult: ...

    def create_commit(
        self,
        *,
        target_branch: str,
        expected_head_sha: Optional[str] = None,
        commit_message: str,
        author: CommitSignature,
        committer: Optional[CommitSignature] = None,
        ttl: Optional[int] = None,
    ) -> CommitBuilder: ...
```

### Type Definitions

Key types are provided via TypedDict for better IDE support:

```python
from pierre_storage.types import (
    GitStorageOptions,
    BaseRepo,
    CommitSignature,
    CreateCommitOptions,
    ListFilesResult,
    ListBranchesResult,
    ListCommitsResult,
    GetBranchDiffResult,
    GetCommitDiffResult,
    RestoreCommitResult,
    RefUpdate,
    # ... and more
)

# BaseRepo type for GitHub sync
class BaseRepo(TypedDict, total=False):
    provider: Literal["github"]  # Always "github"
    owner: str                    # GitHub organization or user
    name: str                     # Repository name
    default_branch: Optional[str] # Default branch (optional)
```

## Webhook Validation

The SDK includes utilities for validating webhook signatures:

```python
from pierre_storage import validate_webhook

# Validate webhook signature
result = validate_webhook(
    payload=request.body,  # Raw payload bytes or string
    headers={
        "X-Pierre-Signature": request.headers["X-Pierre-Signature"],
        "X-Pierre-Event": request.headers["X-Pierre-Event"],
    },
    secret="your-webhook-secret",
    options={"max_age_seconds": 300},  # 5 minutes
)

if result["valid"] and result.get("event_type") == "push":
    event = result.get("payload")
    if event:
        print(f"Push to {event['ref']}")
        print(f"Commit: {event['before']} -> {event['after']}")
else:
    print(f"Invalid webhook: {result.get('error')}")
```

## Authentication

The SDK uses JWT (JSON Web Tokens) for authentication. When you call `get_remote_url()`, it:

1. Creates a JWT with your name, repository ID, and requested permissions
2. Signs it with your private key (ES256, RS256, or EdDSA)
3. Embeds it in the Git remote URL as the password

The generated URLs are compatible with standard Git clients and include all necessary authentication.

## Error Handling

The SDK provides specific error classes:

```python
from pierre_storage import ApiError, RefUpdateError

try:
    repo = await storage.create_repo(id="existing")
except ApiError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")

try:
    result = await builder.send()
except RefUpdateError as e:
    print(f"Ref update failed: {e.message}")
    print(f"Status: {e.status}")
    print(f"Reason: {e.reason}")
    print(f"Ref update: {e.ref_update}")
```

## Development

### Setup

```bash
# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Or use Moon
moon run git-storage-sdk-python:setup

# Run tests
pytest

# Run tests with coverage
pytest --cov=pierre_storage --cov-report=html

# Type checking
mypy pierre_storage

# Linting
ruff check pierre_storage
```

### Building

```bash
python -m build
```

## License

MIT
