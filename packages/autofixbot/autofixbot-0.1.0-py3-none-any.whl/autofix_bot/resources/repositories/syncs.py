# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, strip_not_given, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.repositories import sync_list_params, sync_create_params
from ...types.repositories.sync import Sync
from ...types.repositories.sync_list_response import SyncListResponse

__all__ = ["SyncsResource", "AsyncSyncsResource"]


class SyncsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SyncsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return SyncsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SyncsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return SyncsResourceWithStreamingResponse(self)

    def create(
        self,
        id: str,
        *,
        type: Literal["full", "incremental"],
        base_ref: str | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Sync:
        """
        Creates a new sync operation and returns a signed upload URL for uploading code
        bundle

        Args:
          type: Type of sync

          base_ref: The git reference where the uploaded bundle will be applied. Required for
              incremental syncs only. This reference must exist in the already synced
              repository.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return self._post(
            f"/repositories/{id}/syncs",
            body=maybe_transform(
                {
                    "type": type,
                    "base_ref": base_ref,
                },
                sync_create_params.SyncCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Sync,
        )

    def retrieve(
        self,
        sync_id: str,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Sync:
        """
        Retrieves a sync by its ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not sync_id:
            raise ValueError(f"Expected a non-empty value for `sync_id` but received {sync_id!r}")
        return self._get(
            f"/repositories/{id}/syncs/{sync_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Sync,
        )

    def list(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        status: Literal["pending_upload", "processing", "completed", "failed", "expired"] | Omit = omit,
        type: Literal["full", "incremental"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncListResponse:
        """
        Retrieves a paginated list of syncs for a repository

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          status: Filter by sync status

          type: Filter by sync type

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/repositories/{id}/syncs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "limit": limit,
                        "status": status,
                        "type": type,
                    },
                    sync_list_params.SyncListParams,
                ),
            ),
            cast_to=SyncListResponse,
        )


class AsyncSyncsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSyncsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSyncsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSyncsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return AsyncSyncsResourceWithStreamingResponse(self)

    async def create(
        self,
        id: str,
        *,
        type: Literal["full", "incremental"],
        base_ref: str | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Sync:
        """
        Creates a new sync operation and returns a signed upload URL for uploading code
        bundle

        Args:
          type: Type of sync

          base_ref: The git reference where the uploaded bundle will be applied. Required for
              incremental syncs only. This reference must exist in the already synced
              repository.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return await self._post(
            f"/repositories/{id}/syncs",
            body=await async_maybe_transform(
                {
                    "type": type,
                    "base_ref": base_ref,
                },
                sync_create_params.SyncCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Sync,
        )

    async def retrieve(
        self,
        sync_id: str,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Sync:
        """
        Retrieves a sync by its ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not sync_id:
            raise ValueError(f"Expected a non-empty value for `sync_id` but received {sync_id!r}")
        return await self._get(
            f"/repositories/{id}/syncs/{sync_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Sync,
        )

    async def list(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        status: Literal["pending_upload", "processing", "completed", "failed", "expired"] | Omit = omit,
        type: Literal["full", "incremental"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncListResponse:
        """
        Retrieves a paginated list of syncs for a repository

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          status: Filter by sync status

          type: Filter by sync type

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/repositories/{id}/syncs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "limit": limit,
                        "status": status,
                        "type": type,
                    },
                    sync_list_params.SyncListParams,
                ),
            ),
            cast_to=SyncListResponse,
        )


class SyncsResourceWithRawResponse:
    def __init__(self, syncs: SyncsResource) -> None:
        self._syncs = syncs

        self.create = to_raw_response_wrapper(
            syncs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            syncs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            syncs.list,
        )


class AsyncSyncsResourceWithRawResponse:
    def __init__(self, syncs: AsyncSyncsResource) -> None:
        self._syncs = syncs

        self.create = async_to_raw_response_wrapper(
            syncs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            syncs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            syncs.list,
        )


class SyncsResourceWithStreamingResponse:
    def __init__(self, syncs: SyncsResource) -> None:
        self._syncs = syncs

        self.create = to_streamed_response_wrapper(
            syncs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            syncs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            syncs.list,
        )


class AsyncSyncsResourceWithStreamingResponse:
    def __init__(self, syncs: AsyncSyncsResource) -> None:
        self._syncs = syncs

        self.create = async_to_streamed_response_wrapper(
            syncs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            syncs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            syncs.list,
        )
