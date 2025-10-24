# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["SyncListParams"]


class SyncListParams(TypedDict, total=False):
    after: str
    """Cursor for pagination (object ID)"""

    before: str
    """Cursor for pagination (object ID)"""

    limit: int
    """Number of items to return"""

    status: Literal["pending_upload", "processing", "completed", "failed", "expired"]
    """Filter by sync status"""

    type: Literal["full", "incremental"]
    """Filter by sync type"""
