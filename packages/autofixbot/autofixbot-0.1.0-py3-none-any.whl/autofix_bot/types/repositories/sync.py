# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["Sync", "Error"]


class Error(BaseModel):
    code: Optional[str] = None

    message: Optional[str] = None


class Sync(BaseModel):
    id: Optional[str] = None
    """Unique identifier of the sync"""

    base_ref: Optional[str] = None
    """The git reference where the uploaded bundle will be applied.

    Only used for incremental syncs. This reference must exist in the already synced
    repository.
    """

    completed_at: Optional[int] = None
    """Unix timestamp when the sync completed"""

    created_at: Optional[int] = None
    """Unix timestamp when the sync was created"""

    error: Optional[Error] = None
    """Error details if status is failed"""

    format: Optional[Literal["bundle"]] = None
    """
    Upload format (git bundle file, can be uploaded directly without additional
    compression)
    """

    object: Optional[Literal["sync"]] = None

    repository: Optional[str] = None
    """Repository this sync belongs to"""

    size_bytes: Optional[int] = None
    """Size of uploaded file in bytes"""

    status: Optional[Literal["pending_upload", "processing", "completed", "failed", "expired"]] = None
    """Current status of the sync"""

    type: Optional[Literal["full", "incremental"]] = None
    """Type of sync"""

    updated_at: Optional[int] = None
    """Unix timestamp when the sync was last updated"""

    upload_expires_at: Optional[int] = None
    """Unix timestamp when the upload URL expires"""

    upload_url: Optional[str] = None
    """Signed URL for uploading the code bundle"""
