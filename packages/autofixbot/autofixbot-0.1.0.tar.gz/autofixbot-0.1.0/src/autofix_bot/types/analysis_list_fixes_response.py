# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .fix import Fix
from .paginated_list import PaginatedList

__all__ = ["AnalysisListFixesResponse"]


class AnalysisListFixesResponse(PaginatedList):
    data: Optional[List[Fix]] = None  # type: ignore
