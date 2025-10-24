# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, TypedDict

from .._types import SequenceNotStr
from .language import Language

__all__ = ["RepositoryUpdateParams"]


class RepositoryUpdateParams(TypedDict, total=False):
    archived: bool
    """Whether the repository is archived"""

    detection: List[Literal["security", "secrets", "dependencies"]]
    """Controls what kind of analysis should be performed"""

    exclude_patterns: SequenceNotStr[str]
    """Glob patterns of files and folders to ignore"""

    external_id: str
    """Repository's identifier in your system"""

    fix: List[Literal["security", "secrets", "dependencies"]]
    """Controls which issues are fixed"""

    languages: List[Language]
    """Programming languages to analyze"""

    name: str
    """Repository name"""

    test_patterns: SequenceNotStr[str]
    """Glob patterns of test files and folders"""
