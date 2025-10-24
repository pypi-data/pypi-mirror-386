# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from autofix_bot import AutofixBot, AsyncAutofixBot
from tests.utils import assert_matches_type
from autofix_bot.types.repositories import Sync, SyncListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSyncs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: AutofixBot) -> None:
        sync = client.repositories.syncs.create(
            id="id",
            type="incremental",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: AutofixBot) -> None:
        sync = client.repositories.syncs.create(
            id="id",
            type="incremental",
            base_ref="a1b2c3d",
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: AutofixBot) -> None:
        response = client.repositories.syncs.with_raw_response.create(
            id="id",
            type="incremental",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = response.parse()
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: AutofixBot) -> None:
        with client.repositories.syncs.with_streaming_response.create(
            id="id",
            type="incremental",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = response.parse()
            assert_matches_type(Sync, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.syncs.with_raw_response.create(
                id="",
                type="incremental",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: AutofixBot) -> None:
        sync = client.repositories.syncs.retrieve(
            sync_id="sync_id",
            id="id",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: AutofixBot) -> None:
        response = client.repositories.syncs.with_raw_response.retrieve(
            sync_id="sync_id",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = response.parse()
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: AutofixBot) -> None:
        with client.repositories.syncs.with_streaming_response.retrieve(
            sync_id="sync_id",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = response.parse()
            assert_matches_type(Sync, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.syncs.with_raw_response.retrieve(
                sync_id="sync_id",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sync_id` but received ''"):
            client.repositories.syncs.with_raw_response.retrieve(
                sync_id="",
                id="id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: AutofixBot) -> None:
        sync = client.repositories.syncs.list(
            id="id",
        )
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: AutofixBot) -> None:
        sync = client.repositories.syncs.list(
            id="id",
            after="after",
            before="before",
            limit=1,
            status="pending_upload",
            type="full",
        )
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: AutofixBot) -> None:
        response = client.repositories.syncs.with_raw_response.list(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = response.parse()
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: AutofixBot) -> None:
        with client.repositories.syncs.with_streaming_response.list(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = response.parse()
            assert_matches_type(SyncListResponse, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: AutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.repositories.syncs.with_raw_response.list(
                id="",
            )


class TestAsyncSyncs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAutofixBot) -> None:
        sync = await async_client.repositories.syncs.create(
            id="id",
            type="incremental",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        sync = await async_client.repositories.syncs.create(
            id="id",
            type="incremental",
            base_ref="a1b2c3d",
            idempotency_key="Idempotency-Key",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.syncs.with_raw_response.create(
            id="id",
            type="incremental",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = await response.parse()
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.syncs.with_streaming_response.create(
            id="id",
            type="incremental",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = await response.parse()
            assert_matches_type(Sync, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.syncs.with_raw_response.create(
                id="",
                type="incremental",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncAutofixBot) -> None:
        sync = await async_client.repositories.syncs.retrieve(
            sync_id="sync_id",
            id="id",
        )
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.syncs.with_raw_response.retrieve(
            sync_id="sync_id",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = await response.parse()
        assert_matches_type(Sync, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.syncs.with_streaming_response.retrieve(
            sync_id="sync_id",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = await response.parse()
            assert_matches_type(Sync, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.syncs.with_raw_response.retrieve(
                sync_id="sync_id",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sync_id` but received ''"):
            await async_client.repositories.syncs.with_raw_response.retrieve(
                sync_id="",
                id="id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAutofixBot) -> None:
        sync = await async_client.repositories.syncs.list(
            id="id",
        )
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncAutofixBot) -> None:
        sync = await async_client.repositories.syncs.list(
            id="id",
            after="after",
            before="before",
            limit=1,
            status="pending_upload",
            type="full",
        )
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAutofixBot) -> None:
        response = await async_client.repositories.syncs.with_raw_response.list(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sync = await response.parse()
        assert_matches_type(SyncListResponse, sync, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAutofixBot) -> None:
        async with async_client.repositories.syncs.with_streaming_response.list(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sync = await response.parse()
            assert_matches_type(SyncListResponse, sync, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncAutofixBot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.repositories.syncs.with_raw_response.list(
                id="",
            )
