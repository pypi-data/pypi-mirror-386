# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .repository import Repository
from .paginated_list import PaginatedList

__all__ = ["RepositoryListResponse"]


class RepositoryListResponse(PaginatedList):
    data: Optional[List[Repository]] = None  # type: ignore
