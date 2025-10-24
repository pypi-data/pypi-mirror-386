# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["SyncCreateParams"]


class SyncCreateParams(TypedDict, total=False):
    type: Required[Literal["full", "incremental"]]
    """Type of sync"""

    base_ref: str
    """The git reference where the uploaded bundle will be applied.

    Required for incremental syncs only. This reference must exist in the already
    synced repository.
    """

    idempotency_key: Annotated[str, PropertyInfo(alias="Idempotency-Key")]
