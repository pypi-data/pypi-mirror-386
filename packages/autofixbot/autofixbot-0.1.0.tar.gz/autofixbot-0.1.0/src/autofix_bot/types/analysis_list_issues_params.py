# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

from .language import Language

__all__ = ["AnalysisListIssuesParams"]


class AnalysisListIssuesParams(TypedDict, total=False):
    after: str
    """Cursor for pagination (object ID)"""

    before: str
    """Cursor for pagination (object ID)"""

    category: Literal["security", "secrets", "dependencies"]
    """Filter by issue category"""

    file: str
    """Filter by file path"""

    language: Language
    """Filter by programming language"""

    limit: int
    """Number of items to return"""
