# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .analysis import Analysis
from .paginated_list import PaginatedList

__all__ = ["AnalysisListResponse"]


class AnalysisListResponse(PaginatedList):
    data: Optional[List[Analysis]] = None  # type: ignore
