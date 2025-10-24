# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["WorkspaceRetrieveResponse"]


class WorkspaceRetrieveResponse(BaseModel):
    id: Optional[str] = None
    """Unique identifier of the workspace"""

    created_at: Optional[int] = None
    """Unix timestamp when the workspace was created"""

    name: Optional[str] = None
    """Workspace name"""

    object: Optional[Literal["workspace"]] = None

    status: Optional[Literal["active", "inactive"]] = None
    """Current status of the workspace"""
