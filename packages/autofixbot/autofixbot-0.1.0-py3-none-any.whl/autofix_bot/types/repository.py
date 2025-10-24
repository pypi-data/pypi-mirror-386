# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel
from .language import Language

__all__ = ["Repository"]


class Repository(BaseModel):
    id: Optional[str] = None
    """Unique identifier of the repository"""

    archived: Optional[bool] = None
    """Whether the repository is archived"""

    created_at: Optional[int] = None
    """Unix timestamp when the repository was created"""

    detection: Optional[List[Literal["security", "secrets", "dependencies"]]] = None
    """Types of analysis to perform"""

    exclude_patterns: Optional[List[str]] = None
    """Glob patterns of files and folders to ignore"""

    external_id: Optional[str] = None
    """Repository's identifier in your system"""

    file_count: Optional[int] = None
    """Total number of files"""

    fix: Optional[List[Literal["security", "secrets", "dependencies"]]] = None
    """Types of issues to fix"""

    git_ref: Optional[str] = None
    """Git commit hash, branch, or tag representing the current state of the
    repository.

    This is automatically updated to the last seen ref from successful sync
    operations.
    """

    languages: Optional[List[Language]] = None
    """Programming languages to analyze"""

    last_synced_at: Optional[int] = None
    """
    Unix timestamp of the last successful sync operation (null if no syncs have
    completed)
    """

    name: Optional[str] = None
    """Repository name"""

    object: Optional[Literal["repository"]] = None

    size_bytes: Optional[int] = None
    """Total uploaded size in bytes"""

    test_patterns: Optional[List[str]] = None
    """Glob patterns of test files and folders"""

    updated_at: Optional[int] = None
    """Unix timestamp when the repository was last modified"""

    workspace: Optional[str] = None
    """Workspace this repository belongs to"""
