# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["Fix"]


class Fix(BaseModel):
    category: Optional[Literal["security", "secrets", "dependencies"]] = None
    """The agent that generated this fix"""

    explanation: Optional[str] = None
    """Explanation of what this fix does"""

    object: Optional[Literal["result.fix.item"]] = None

    patch: Optional[str] = None
    """Individual git patch for this fix"""
