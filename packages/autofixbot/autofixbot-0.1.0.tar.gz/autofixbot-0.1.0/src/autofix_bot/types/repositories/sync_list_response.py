# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .sync import Sync
from ..paginated_list import PaginatedList

__all__ = ["SyncListResponse"]


class SyncListResponse(PaginatedList):
    data: Optional[List[Sync]] = None  # type: ignore
