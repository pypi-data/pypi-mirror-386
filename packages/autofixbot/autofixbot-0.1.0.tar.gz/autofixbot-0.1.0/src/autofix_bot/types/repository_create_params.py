# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .language import Language

__all__ = ["RepositoryCreateParams"]


class RepositoryCreateParams(TypedDict, total=False):
    name: Required[str]
    """Repository's display name"""

    archived: bool
    """Whether the repository is archived.

    We'll return a validation error if an analysis is requested on an archived
    repository.
    """

    detection: List[Literal["security", "secrets", "dependencies"]]
    """Controls what kind of analysis should be performed.

    Can be overriden per analysis request.
    """

    exclude_patterns: SequenceNotStr[str]
    """Glob patterns of files and folders to ignore"""

    external_id: str
    """Repository's identifier in your system"""

    fix: List[Literal["security", "secrets", "dependencies"]]
    """Controls which issues are fixed (defaults to same as detection).

    Can be overriden per analysis request.
    """

    languages: List[Language]
    """Programming languages to analyze (auto-detected if not provided)"""

    test_patterns: SequenceNotStr[str]
    """Glob patterns of test files and folders (auto-detected if not provided)"""

    idempotency_key: Annotated[str, PropertyInfo(alias="Idempotency-Key")]
