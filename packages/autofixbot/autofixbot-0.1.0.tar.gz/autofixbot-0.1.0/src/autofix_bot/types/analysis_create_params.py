# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .language import Language

__all__ = ["AnalysisCreateParams"]


class AnalysisCreateParams(TypedDict, total=False):
    type: Required[Literal["repository", "file"]]
    """Type of analysis to perform"""

    code: str
    """Standalone code to analyze (required if type is file)"""

    detection: List[Literal["security", "secrets", "dependencies"]]
    """
    Controls what kind of analysis to perform (defaults to repository's detection
    setting)
    """

    filename: str
    """Filename for the code snippet (optional if type is file)"""

    fix: List[Literal["security", "secrets", "dependencies"]]
    """Controls which issues are fixed (defaults to repository's fix setting)"""

    from_ref: str
    """
    Beginning git reference for repository analysis (required if type is repository)
    """

    language: Language
    """Explicit language override (optional if type is file)"""

    patch: str
    """Git patch to apply before analysis (optional if type is repository)"""

    repository_id: str
    """Repository ID or external:{external_id} (required if type is repository)"""

    to_ref: str
    """End git reference for repository analysis (optional if type is repository)"""

    idempotency_key: Annotated[str, PropertyInfo(alias="Idempotency-Key")]
