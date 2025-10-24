# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["RepositoryListParams"]


class RepositoryListParams(TypedDict, total=False):
    after: str
    """Cursor for pagination (object ID)"""

    archived: bool

    before: str
    """Cursor for pagination (object ID)"""

    limit: int
    """Number of items to return"""

    status: Literal["empty", "uploading", "error", "ready"]
