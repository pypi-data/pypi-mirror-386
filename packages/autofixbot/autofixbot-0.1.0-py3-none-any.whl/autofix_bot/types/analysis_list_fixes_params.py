# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["AnalysisListFixesParams"]


class AnalysisListFixesParams(TypedDict, total=False):
    after: str
    """Cursor for pagination (object ID)"""

    before: str
    """Cursor for pagination (object ID)"""

    category: Literal["security", "secrets", "dependencies"]
    """Filter by fix category"""

    limit: int
    """Number of items to return"""
