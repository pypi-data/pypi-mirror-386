# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from typing_extensions import Literal

from .fix import Fix
from .issue import Issue
from .._models import BaseModel
from .language import Language

__all__ = ["Analysis", "Cost", "DetectionResult", "FixResult"]


class Cost(BaseModel):
    input_loc: Optional[int] = None
    """Lines of code analyzed"""

    input_loc_rate: Optional[float] = None
    """Rate per input line of code in cents"""

    object: Optional[Literal["result.cost"]] = None

    output_fix_loc: Optional[int] = None
    """Lines of code generated in fixes"""

    output_fix_rate: Optional[float] = None
    """Rate per output fix line of code in cents"""

    total: Optional[float] = None
    """
    Total cost in cents (input_loc _ input_loc_rate + output_fix_loc _
    output_fix_rate)
    """


class DetectionResult(BaseModel):
    has_more: Optional[bool] = None
    """True if there are more than 50 issues"""

    issues: Optional[List[Issue]] = None
    """First 50 detected issues"""

    issues_detected_by_category: Optional[Dict[str, int]] = None
    """Issues by category (e.g., {"security": 65, "secrets": 22})"""

    issues_detected_by_language: Optional[Dict[str, int]] = None
    """Issues by language (e.g., {"python": 11, "typescript": 12})"""

    issues_detected_count: Optional[int] = None
    """Total number of issues detected"""

    object: Optional[Literal["result.detection"]] = None

    url: Optional[str] = None
    """URL to access the paginated list of all issues"""


class FixResult(BaseModel):
    fixes: Optional[List[Fix]] = None
    """First 50 individual fixes"""

    has_more: Optional[bool] = None
    """True if there are more than 50 fixes"""

    issues_fixed_by_category: Optional[Dict[str, int]] = None
    """Issues fixed by category (e.g., {"security": 8, "secrets": 2})"""

    issues_fixed_count: Optional[int] = None
    """Total number of issues fixed"""

    object: Optional[Literal["result.fix"]] = None

    patch: Optional[str] = None
    """Unified git patch ready to apply to the repository"""

    url: Optional[str] = None
    """URL to access the paginated list of all fixes"""


class Analysis(BaseModel):
    id: Optional[str] = None
    """Unique identifier of the analysis"""

    code: Optional[str] = None
    """Code for standalone analysis"""

    completed_at: Optional[int] = None
    """Unix timestamp when the analysis completed"""

    cost: Optional[Cost] = None

    created_at: Optional[int] = None
    """Unix timestamp when the analysis was created"""

    detection: Optional[List[Literal["security", "secrets", "dependencies"]]] = None

    detection_result: Optional[DetectionResult] = None

    filename: Optional[str] = None
    """Filename of the code snippet (only present if type is file)"""

    fix: Optional[List[Literal["security", "secrets", "dependencies"]]] = None

    fix_result: Optional[FixResult] = None

    from_ref: Optional[str] = None
    """Beginning git reference"""

    language: Optional[Language] = None
    """Language of the code snippet (only present if type is file)"""

    object: Optional[Literal["analysis"]] = None

    patch: Optional[str] = None
    """Git patch to apply before analysis"""

    repository: Optional[str] = None
    """Repository this analysis belongs to"""

    status: Optional[Literal["queued", "in_progress", "completed", "canceled"]] = None
    """Current status of the analysis"""

    to_ref: Optional[str] = None
    """End git reference"""

    type: Optional[Literal["repository", "file"]] = None
    """Type of analysis performed"""

    updated_at: Optional[int] = None
    """Unix timestamp when the analysis was last updated"""

    workspace: Optional[str] = None
    """Workspace this analysis belongs to"""
