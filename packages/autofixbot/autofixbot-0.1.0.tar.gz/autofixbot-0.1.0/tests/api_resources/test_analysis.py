# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from autofix_bot import AutofixBot, AsyncAutofixBot
from tests.utils import assert_matches_type
from autofix_bot.types import (
    Analysis,
    AnalysisListResponse,
    AnalysisListFixesResponse,
    AnalysisListIssuesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAnalysis:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: AutofixBot) -> None:
        analysis = client.analysis.create(
            type="repository",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: AutofixBot) -> None:
        analysis = client.analysis.create(
            type="repository",
            code="code",
            detection=["security", "secrets"],
            filename="filename",
            fix=["security"],
            from_ref="a1b2c3d",
            language="python",
            patch="patch",
            repository_id="repo_018e8c5a23457891bcdef01234567890",
            to_ref="d4e5f6a",
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.create(
            type="repository",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.create(
            type="repository",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: AutofixBot) -> None:
        analysis = client.analysis.retrieve(
            "id",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.analysis.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: AutofixBot) -> None:
        analysis = client.analysis.list()
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: AutofixBot) -> None:
        analysis = client.analysis.list(
            after="after",
            before="before",
            limit=1,
            repository_id="repository_id",
            status="queued",
        )
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(AnalysisListResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: AutofixBot) -> None:
        analysis = client.analysis.cancel(
            "id",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.cancel(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.cancel(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.analysis.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_fixes(self, client: AutofixBot) -> None:
        analysis = client.analysis.list_fixes(
            id="id",
        )
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_fixes_with_all_params(self, client: AutofixBot) -> None:
        analysis = client.analysis.list_fixes(
            id="id",
            after="after",
            before="before",
            category="security",
            limit=1,
        )
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_fixes(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.list_fixes(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_fixes(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.list_fixes(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_fixes(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.analysis.with_raw_response.list_fixes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_issues(self, client: AutofixBot) -> None:
        analysis = client.analysis.list_issues(
            id="id",
        )
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_issues_with_all_params(self, client: AutofixBot) -> None:
        analysis = client.analysis.list_issues(
            id="id",
            after="after",
            before="before",
            category="security",
            file="file",
            language="python",
            limit=1,
        )
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_issues(self, client: AutofixBot) -> None:
        response = client.analysis.with_raw_response.list_issues(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_issues(self, client: AutofixBot) -> None:
        with client.analysis.with_streaming_response.list_issues(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_issues(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.analysis.with_raw_response.list_issues(
                id="",
            )


class TestAsyncAnalysis:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.create(
            type="repository",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.create(
            type="repository",
            code="code",
            detection=["security", "secrets"],
            filename="filename",
            fix=["security"],
            from_ref="a1b2c3d",
            language="python",
            patch="patch",
            repository_id="repo_018e8c5a23457891bcdef01234567890",
            to_ref="d4e5f6a",
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.create(
            type="repository",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.create(
            type="repository",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.retrieve(
            "id",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.analysis.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list()
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list(
            after="after",
            before="before",
            limit=1,
            repository_id="repository_id",
            status="queued",
        )
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(AnalysisListResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(AnalysisListResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.cancel(
            "id",
        )
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.cancel(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(Analysis, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.cancel(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(Analysis, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.analysis.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_fixes(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list_fixes(
            id="id",
        )
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_fixes_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list_fixes(
            id="id",
            after="after",
            before="before",
            category="security",
            limit=1,
        )
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_fixes(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.list_fixes(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_fixes(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.list_fixes(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(AnalysisListFixesResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_fixes(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.analysis.with_raw_response.list_fixes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_issues(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list_issues(
            id="id",
        )
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_issues_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        analysis = await async_client.analysis.list_issues(
            id="id",
            after="after",
            before="before",
            category="security",
            file="file",
            language="python",
            limit=1,
        )
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_issues(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.analysis.with_raw_response.list_issues(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_issues(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.analysis.with_streaming_response.list_issues(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(AnalysisListIssuesResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_issues(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.analysis.with_raw_response.list_issues(
                id="",
            )
