# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["AnalysisListParams"]


class AnalysisListParams(TypedDict, total=False):
    after: str
    """Cursor for pagination (object ID)"""

    before: str
    """Cursor for pagination (object ID)"""

    limit: int
    """Number of items to return"""

    repository_id: str
    """Filter by repository (supports external: format)"""

    status: Literal["queued", "in_progress", "completed"]
