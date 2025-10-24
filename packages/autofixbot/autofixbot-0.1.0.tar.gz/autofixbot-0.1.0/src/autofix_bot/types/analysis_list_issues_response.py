# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .issue import Issue
from .paginated_list import PaginatedList

__all__ = ["AnalysisListIssuesResponse"]


class AnalysisListIssuesResponse(PaginatedList):
    data: Optional[List[Issue]] = None  # type: ignore
