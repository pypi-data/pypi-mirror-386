# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal

import httpx

from .syncs import (
    SyncsResource,
    AsyncSyncsResource,
    SyncsResourceWithRawResponse,
    AsyncSyncsResourceWithRawResponse,
    SyncsResourceWithStreamingResponse,
    AsyncSyncsResourceWithStreamingResponse,
)
from ...types import repository_list_params, repository_create_params, repository_update_params
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
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
from ...types.language import Language
from ...types.repository import Repository
from ...types.repository_list_response import RepositoryListResponse

__all__ = ["RepositoriesResource", "AsyncRepositoriesResource"]


class RepositoriesResource(SyncAPIResource):
    @cached_property
    def syncs(self) -> SyncsResource:
        return SyncsResource(self._client)

    @cached_property
    def with_raw_response(self) -> RepositoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return RepositoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RepositoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return RepositoriesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        archived: bool | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        exclude_patterns: SequenceNotStr[str] | Omit = omit,
        external_id: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        languages: List[Language] | Omit = omit,
        test_patterns: SequenceNotStr[str] | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Creates a new repository for code analysis

        Args:
          name: Repository's display name

          archived: Whether the repository is archived. We'll return a validation error if an
              analysis is requested on an archived repository.

          detection: Controls what kind of analysis should be performed. Can be overriden per
              analysis request.

          exclude_patterns: Glob patterns of files and folders to ignore

          external_id: Repository's identifier in your system

          fix: Controls which issues are fixed (defaults to same as detection). Can be
              overriden per analysis request.

          languages: Programming languages to analyze (auto-detected if not provided)

          test_patterns: Glob patterns of test files and folders (auto-detected if not provided)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return self._post(
            "/repositories",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "detection": detection,
                    "exclude_patterns": exclude_patterns,
                    "external_id": external_id,
                    "fix": fix,
                    "languages": languages,
                    "test_patterns": test_patterns,
                },
                repository_create_params.RepositoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Retrieves a repository by its ID or external ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/repositories/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    def update(
        self,
        id: str,
        *,
        archived: bool | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        exclude_patterns: SequenceNotStr[str] | Omit = omit,
        external_id: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        languages: List[Language] | Omit = omit,
        name: str | Omit = omit,
        test_patterns: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Updates a repository by its ID or external ID

        Args:
          archived: Whether the repository is archived

          detection: Controls what kind of analysis should be performed

          exclude_patterns: Glob patterns of files and folders to ignore

          external_id: Repository's identifier in your system

          fix: Controls which issues are fixed

          languages: Programming languages to analyze

          name: Repository name

          test_patterns: Glob patterns of test files and folders

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._patch(
            f"/repositories/{id}",
            body=maybe_transform(
                {
                    "archived": archived,
                    "detection": detection,
                    "exclude_patterns": exclude_patterns,
                    "external_id": external_id,
                    "fix": fix,
                    "languages": languages,
                    "name": name,
                    "test_patterns": test_patterns,
                },
                repository_update_params.RepositoryUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        archived: bool | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        status: Literal["empty", "uploading", "error", "ready"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepositoryListResponse:
        """
        Retrieves a paginated list of repositories in your workspace

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/repositories",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "archived": archived,
                        "before": before,
                        "limit": limit,
                        "status": status,
                    },
                    repository_list_params.RepositoryListParams,
                ),
            ),
            cast_to=RepositoryListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Permanently deletes a repository and all associated data

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/repositories/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncRepositoriesResource(AsyncAPIResource):
    @cached_property
    def syncs(self) -> AsyncSyncsResource:
        return AsyncSyncsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRepositoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRepositoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRepositoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return AsyncRepositoriesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        archived: bool | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        exclude_patterns: SequenceNotStr[str] | Omit = omit,
        external_id: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        languages: List[Language] | Omit = omit,
        test_patterns: SequenceNotStr[str] | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Creates a new repository for code analysis

        Args:
          name: Repository's display name

          archived: Whether the repository is archived. We'll return a validation error if an
              analysis is requested on an archived repository.

          detection: Controls what kind of analysis should be performed. Can be overriden per
              analysis request.

          exclude_patterns: Glob patterns of files and folders to ignore

          external_id: Repository's identifier in your system

          fix: Controls which issues are fixed (defaults to same as detection). Can be
              overriden per analysis request.

          languages: Programming languages to analyze (auto-detected if not provided)

          test_patterns: Glob patterns of test files and folders (auto-detected if not provided)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return await self._post(
            "/repositories",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "detection": detection,
                    "exclude_patterns": exclude_patterns,
                    "external_id": external_id,
                    "fix": fix,
                    "languages": languages,
                    "test_patterns": test_patterns,
                },
                repository_create_params.RepositoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Retrieves a repository by its ID or external ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/repositories/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    async def update(
        self,
        id: str,
        *,
        archived: bool | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        exclude_patterns: SequenceNotStr[str] | Omit = omit,
        external_id: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        languages: List[Language] | Omit = omit,
        name: str | Omit = omit,
        test_patterns: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Repository:
        """
        Updates a repository by its ID or external ID

        Args:
          archived: Whether the repository is archived

          detection: Controls what kind of analysis should be performed

          exclude_patterns: Glob patterns of files and folders to ignore

          external_id: Repository's identifier in your system

          fix: Controls which issues are fixed

          languages: Programming languages to analyze

          name: Repository name

          test_patterns: Glob patterns of test files and folders

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._patch(
            f"/repositories/{id}",
            body=await async_maybe_transform(
                {
                    "archived": archived,
                    "detection": detection,
                    "exclude_patterns": exclude_patterns,
                    "external_id": external_id,
                    "fix": fix,
                    "languages": languages,
                    "name": name,
                    "test_patterns": test_patterns,
                },
                repository_update_params.RepositoryUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Repository,
        )

    async def list(
        self,
        *,
        after: str | Omit = omit,
        archived: bool | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        status: Literal["empty", "uploading", "error", "ready"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepositoryListResponse:
        """
        Retrieves a paginated list of repositories in your workspace

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/repositories",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "archived": archived,
                        "before": before,
                        "limit": limit,
                        "status": status,
                    },
                    repository_list_params.RepositoryListParams,
                ),
            ),
            cast_to=RepositoryListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Permanently deletes a repository and all associated data

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/repositories/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class RepositoriesResourceWithRawResponse:
    def __init__(self, repositories: RepositoriesResource) -> None:
        self._repositories = repositories

        self.create = to_raw_response_wrapper(
            repositories.create,
        )
        self.retrieve = to_raw_response_wrapper(
            repositories.retrieve,
        )
        self.update = to_raw_response_wrapper(
            repositories.update,
        )
        self.list = to_raw_response_wrapper(
            repositories.list,
        )
        self.delete = to_raw_response_wrapper(
            repositories.delete,
        )

    @cached_property
    def syncs(self) -> SyncsResourceWithRawResponse:
        return SyncsResourceWithRawResponse(self._repositories.syncs)


class AsyncRepositoriesResourceWithRawResponse:
    def __init__(self, repositories: AsyncRepositoriesResource) -> None:
        self._repositories = repositories

        self.create = async_to_raw_response_wrapper(
            repositories.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            repositories.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            repositories.update,
        )
        self.list = async_to_raw_response_wrapper(
            repositories.list,
        )
        self.delete = async_to_raw_response_wrapper(
            repositories.delete,
        )

    @cached_property
    def syncs(self) -> AsyncSyncsResourceWithRawResponse:
        return AsyncSyncsResourceWithRawResponse(self._repositories.syncs)


class RepositoriesResourceWithStreamingResponse:
    def __init__(self, repositories: RepositoriesResource) -> None:
        self._repositories = repositories

        self.create = to_streamed_response_wrapper(
            repositories.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            repositories.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            repositories.update,
        )
        self.list = to_streamed_response_wrapper(
            repositories.list,
        )
        self.delete = to_streamed_response_wrapper(
            repositories.delete,
        )

    @cached_property
    def syncs(self) -> SyncsResourceWithStreamingResponse:
        return SyncsResourceWithStreamingResponse(self._repositories.syncs)


class AsyncRepositoriesResourceWithStreamingResponse:
    def __init__(self, repositories: AsyncRepositoriesResource) -> None:
        self._repositories = repositories

        self.create = async_to_streamed_response_wrapper(
            repositories.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            repositories.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            repositories.update,
        )
        self.list = async_to_streamed_response_wrapper(
            repositories.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            repositories.delete,
        )

    @cached_property
    def syncs(self) -> AsyncSyncsResourceWithStreamingResponse:
        return AsyncSyncsResourceWithStreamingResponse(self._repositories.syncs)
