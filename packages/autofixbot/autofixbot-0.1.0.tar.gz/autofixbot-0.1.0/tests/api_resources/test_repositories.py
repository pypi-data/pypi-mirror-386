# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from autofix_bot import AutofixBot, AsyncAutofixBot
from tests.utils import assert_matches_type
from autofix_bot.types import (
    Repository,
    RepositoryListResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRepositories:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: AutofixBot) -> None:
        repository = client.repositories.create(
            name="backend-api",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: AutofixBot) -> None:
        repository = client.repositories.create(
            name="backend-api",
            archived=False,
            detection=["security", "secrets"],
            exclude_patterns=["**/node_modules/**", "**/*.min.js"],
            external_id="github:123456789",
            fix=["security", "secrets"],
            languages=["python", "javascript"],
            test_patterns=["**/tests/**", "**/*_test.py"],
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: AutofixBot) -> None:
        response = client.repositories.with_raw_response.create(
            name="backend-api",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: AutofixBot) -> None:
        with client.repositories.with_streaming_response.create(
            name="backend-api",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: AutofixBot) -> None:
        repository = client.repositories.retrieve(
            "id",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: AutofixBot) -> None:
        response = client.repositories.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: AutofixBot) -> None:
        with client.repositories.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: AutofixBot) -> None:
        repository = client.repositories.update(
            id="id",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: AutofixBot) -> None:
        repository = client.repositories.update(
            id="id",
            archived=True,
            detection=["security"],
            exclude_patterns=["string"],
            external_id="external_id",
            fix=["security"],
            languages=["python"],
            name="backend-api-v2",
            test_patterns=["string"],
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: AutofixBot) -> None:
        response = client.repositories.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: AutofixBot) -> None:
        with client.repositories.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: AutofixBot) -> None:
        repository = client.repositories.list()
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: AutofixBot) -> None:
        repository = client.repositories.list(
            after="after",
            archived=True,
            before="before",
            limit=1,
            status="empty",
        )
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: AutofixBot) -> None:
        response = client.repositories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = response.parse()
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: AutofixBot) -> None:
        with client.repositories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = response.parse()
            assert_matches_type(RepositoryListResponse, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: AutofixBot) -> None:
        repository = client.repositories.delete(
            "id",
        )
        assert repository is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: AutofixBot) -> None:
        response = client.repositories.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = response.parse()
        assert repository is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: AutofixBot) -> None:
        with client.repositories.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = response.parse()
            assert repository is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.with_raw_response.delete(
                "",
            )


class TestAsyncRepositories:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.create(
            name="backend-api",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.create(
            name="backend-api",
            archived=False,
            detection=["security", "secrets"],
            exclude_patterns=["**/node_modules/**", "**/*.min.js"],
            external_id="github:123456789",
            fix=["security", "secrets"],
            languages=["python", "javascript"],
            test_patterns=["**/tests/**", "**/*_test.py"],
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.with_raw_response.create(
            name="backend-api",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = await response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.with_streaming_response.create(
            name="backend-api",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = await response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.retrieve(
            "id",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = await response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = await response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.update(
            id="id",
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.update(
            id="id",
            archived=True,
            detection=["security"],
            exclude_patterns=["string"],
            external_id="external_id",
            fix=["security"],
            languages=["python"],
            name="backend-api-v2",
            test_patterns=["string"],
        )
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = await response.parse()
        assert_matches_type(Repository, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = await response.parse()
            assert_matches_type(Repository, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.list()
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.list(
            after="after",
            archived=True,
            before="before",
            limit=1,
            status="empty",
        )
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = await response.parse()
        assert_matches_type(RepositoryListResponse, repository, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = await response.parse()
            assert_matches_type(RepositoryListResponse, repository, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncAutofixBot) -> None:
        repository = await async_client.repositories.delete(
            "id",
        )
        assert repository is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repository = await response.parse()
        assert repository is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repository = await response.parse()
            assert repository is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.with_raw_response.delete(
                "",
            )
