# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["Issue", "Position", "PositionBegin", "PositionEnd"]


class PositionBegin(BaseModel):
    column: Optional[int] = None

    line: Optional[int] = None


class PositionEnd(BaseModel):
    column: Optional[int] = None

    line: Optional[int] = None


class Position(BaseModel):
    begin: Optional[PositionBegin] = None

    end: Optional[PositionEnd] = None


class Issue(BaseModel):
    category: Optional[Literal["security", "secrets", "dependencies"]] = None
    """Sub-agent that raised this issue"""

    explanation: Optional[str] = None
    """Detailed explanation of the issue"""

    file: Optional[str] = None
    """File path relative to repository root"""

    object: Optional[Literal["result.detection.issue"]] = None

    position: Optional[Position] = None
