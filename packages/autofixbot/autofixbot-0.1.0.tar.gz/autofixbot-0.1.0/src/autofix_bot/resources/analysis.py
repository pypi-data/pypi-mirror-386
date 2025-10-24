# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal

import httpx

from ..types import (
    Language,
    analysis_list_params,
    analysis_create_params,
    analysis_list_fixes_params,
    analysis_list_issues_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, strip_not_given, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.analysis import Analysis
from ..types.language import Language
from ..types.analysis_list_response import AnalysisListResponse
from ..types.analysis_list_fixes_response import AnalysisListFixesResponse
from ..types.analysis_list_issues_response import AnalysisListIssuesResponse

__all__ = ["AnalysisResource", "AsyncAnalysisResource"]


class AnalysisResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AnalysisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return AnalysisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AnalysisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return AnalysisResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        type: Literal["repository", "file"],
        code: str | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        filename: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        from_ref: str | Omit = omit,
        language: Language | Omit = omit,
        patch: str | Omit = omit,
        repository_id: str | Omit = omit,
        to_ref: str | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Analysis:
        """
        Creates a new code analysis session

        Args:
          type: Type of analysis to perform

          code: Standalone code to analyze (required if type is file)

          detection: Controls what kind of analysis to perform (defaults to repository's detection
              setting)

          filename: Filename for the code snippet (optional if type is file)

          fix: Controls which issues are fixed (defaults to repository's fix setting)

          from_ref: Beginning git reference for repository analysis (required if type is repository)

          language: Explicit language override (optional if type is file)

          patch: Git patch to apply before analysis (optional if type is repository)

          repository_id: Repository ID or external:{external_id} (required if type is repository)

          to_ref: End git reference for repository analysis (optional if type is repository)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return self._post(
            "/analysis",
            body=maybe_transform(
                {
                    "type": type,
                    "code": code,
                    "detection": detection,
                    "filename": filename,
                    "fix": fix,
                    "from_ref": from_ref,
                    "language": language,
                    "patch": patch,
                    "repository_id": repository_id,
                    "to_ref": to_ref,
                },
                analysis_create_params.AnalysisCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
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
    ) -> Analysis:
        """
        Returns the analysis object

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/analysis/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        repository_id: str | Omit = omit,
        status: Literal["queued", "in_progress", "completed"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListResponse:
        """
        Retrieves a paginated list of analysis runs in your workspace

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          repository_id: Filter by repository (supports external: format)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/analysis",
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
                        "repository_id": repository_id,
                        "status": status,
                    },
                    analysis_list_params.AnalysisListParams,
                ),
            ),
            cast_to=AnalysisListResponse,
        )

    def cancel(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Analysis:
        """
        Cancels a running analysis

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/analysis/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
        )

    def list_fixes(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        category: Literal["security", "secrets", "dependencies"] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListFixesResponse:
        """
        Retrieves a paginated list of all individual fixes generated in an analysis

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          category: Filter by fix category

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/analysis/{id}/fixes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "category": category,
                        "limit": limit,
                    },
                    analysis_list_fixes_params.AnalysisListFixesParams,
                ),
            ),
            cast_to=AnalysisListFixesResponse,
        )

    def list_issues(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        category: Literal["security", "secrets", "dependencies"] | Omit = omit,
        file: str | Omit = omit,
        language: Language | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListIssuesResponse:
        """
        Retrieves a paginated list of all issues detected in an analysis

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          category: Filter by issue category

          file: Filter by file path

          language: Filter by programming language

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/analysis/{id}/issues",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "category": category,
                        "file": file,
                        "language": language,
                        "limit": limit,
                    },
                    analysis_list_issues_params.AnalysisListIssuesParams,
                ),
            ),
            cast_to=AnalysisListIssuesResponse,
        )


class AsyncAnalysisResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAnalysisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAnalysisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAnalysisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DeepSourceCorp/autofixbot-python#with_streaming_response
        """
        return AsyncAnalysisResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        type: Literal["repository", "file"],
        code: str | Omit = omit,
        detection: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        filename: str | Omit = omit,
        fix: List[Literal["security", "secrets", "dependencies"]] | Omit = omit,
        from_ref: str | Omit = omit,
        language: Language | Omit = omit,
        patch: str | Omit = omit,
        repository_id: str | Omit = omit,
        to_ref: str | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Analysis:
        """
        Creates a new code analysis session

        Args:
          type: Type of analysis to perform

          code: Standalone code to analyze (required if type is file)

          detection: Controls what kind of analysis to perform (defaults to repository's detection
              setting)

          filename: Filename for the code snippet (optional if type is file)

          fix: Controls which issues are fixed (defaults to repository's fix setting)

          from_ref: Beginning git reference for repository analysis (required if type is repository)

          language: Explicit language override (optional if type is file)

          patch: Git patch to apply before analysis (optional if type is repository)

          repository_id: Repository ID or external:{external_id} (required if type is repository)

          to_ref: End git reference for repository analysis (optional if type is repository)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return await self._post(
            "/analysis",
            body=await async_maybe_transform(
                {
                    "type": type,
                    "code": code,
                    "detection": detection,
                    "filename": filename,
                    "fix": fix,
                    "from_ref": from_ref,
                    "language": language,
                    "patch": patch,
                    "repository_id": repository_id,
                    "to_ref": to_ref,
                },
                analysis_create_params.AnalysisCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
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
    ) -> Analysis:
        """
        Returns the analysis object

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/analysis/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
        )

    async def list(
        self,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        repository_id: str | Omit = omit,
        status: Literal["queued", "in_progress", "completed"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListResponse:
        """
        Retrieves a paginated list of analysis runs in your workspace

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          limit: Number of items to return

          repository_id: Filter by repository (supports external: format)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/analysis",
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
                        "repository_id": repository_id,
                        "status": status,
                    },
                    analysis_list_params.AnalysisListParams,
                ),
            ),
            cast_to=AnalysisListResponse,
        )

    async def cancel(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Analysis:
        """
        Cancels a running analysis

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/analysis/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Analysis,
        )

    async def list_fixes(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        category: Literal["security", "secrets", "dependencies"] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListFixesResponse:
        """
        Retrieves a paginated list of all individual fixes generated in an analysis

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          category: Filter by fix category

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/analysis/{id}/fixes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "category": category,
                        "limit": limit,
                    },
                    analysis_list_fixes_params.AnalysisListFixesParams,
                ),
            ),
            cast_to=AnalysisListFixesResponse,
        )

    async def list_issues(
        self,
        id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        category: Literal["security", "secrets", "dependencies"] | Omit = omit,
        file: str | Omit = omit,
        language: Language | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalysisListIssuesResponse:
        """
        Retrieves a paginated list of all issues detected in an analysis

        Args:
          after: Cursor for pagination (object ID)

          before: Cursor for pagination (object ID)

          category: Filter by issue category

          file: Filter by file path

          language: Filter by programming language

          limit: Number of items to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/analysis/{id}/issues",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "category": category,
                        "file": file,
                        "language": language,
                        "limit": limit,
                    },
                    analysis_list_issues_params.AnalysisListIssuesParams,
                ),
            ),
            cast_to=AnalysisListIssuesResponse,
        )


class AnalysisResourceWithRawResponse:
    def __init__(self, analysis: AnalysisResource) -> None:
        self._analysis = analysis

        self.create = to_raw_response_wrapper(
            analysis.create,
        )
        self.retrieve = to_raw_response_wrapper(
            analysis.retrieve,
        )
        self.list = to_raw_response_wrapper(
            analysis.list,
        )
        self.cancel = to_raw_response_wrapper(
            analysis.cancel,
        )
        self.list_fixes = to_raw_response_wrapper(
            analysis.list_fixes,
        )
        self.list_issues = to_raw_response_wrapper(
            analysis.list_issues,
        )


class AsyncAnalysisResourceWithRawResponse:
    def __init__(self, analysis: AsyncAnalysisResource) -> None:
        self._analysis = analysis

        self.create = async_to_raw_response_wrapper(
            analysis.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            analysis.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            analysis.list,
        )
        self.cancel = async_to_raw_response_wrapper(
            analysis.cancel,
        )
        self.list_fixes = async_to_raw_response_wrapper(
            analysis.list_fixes,
        )
        self.list_issues = async_to_raw_response_wrapper(
            analysis.list_issues,
        )


class AnalysisResourceWithStreamingResponse:
    def __init__(self, analysis: AnalysisResource) -> None:
        self._analysis = analysis

        self.create = to_streamed_response_wrapper(
            analysis.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            analysis.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            analysis.list,
        )
        self.cancel = to_streamed_response_wrapper(
            analysis.cancel,
        )
        self.list_fixes = to_streamed_response_wrapper(
            analysis.list_fixes,
        )
        self.list_issues = to_streamed_response_wrapper(
            analysis.list_issues,
        )


class AsyncAnalysisResourceWithStreamingResponse:
    def __init__(self, analysis: AsyncAnalysisResource) -> None:
        self._analysis = analysis

        self.create = async_to_streamed_response_wrapper(
            analysis.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            analysis.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            analysis.list,
        )
        self.cancel = async_to_streamed_response_wrapper(
            analysis.cancel,
        )
        self.list_fixes = async_to_streamed_response_wrapper(
            analysis.list_fixes,
        )
        self.list_issues = async_to_streamed_response_wrapper(
            analysis.list_issues,
        )
