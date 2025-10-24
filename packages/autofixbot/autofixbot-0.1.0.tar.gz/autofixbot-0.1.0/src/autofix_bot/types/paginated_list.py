# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["PaginatedList"]


class PaginatedList(BaseModel):
    data: Optional[List[object]] = None
    """Array of response elements"""

    has_more: Optional[bool] = None
    """True if there are more elements"""

    object: Optional[Literal["list"]] = None

    url: Optional[str] = None
    """URL for accessing this list"""
