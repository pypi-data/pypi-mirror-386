# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from SearchPilot import SearchPilot, AsyncSearchPilot
from tests.utils import assert_matches_type
from SearchPilot.pagination import SyncCursorURLPage, AsyncCursorURLPage
from SearchPilot.types.shared import Rule

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRules:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: SearchPilot) -> None:
        rule = client.rules.retrieve(
            0,
        )
        assert_matches_type(Rule, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: SearchPilot) -> None:
        response = client.rules.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = response.parse()
        assert_matches_type(Rule, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: SearchPilot) -> None:
        with client.rules.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = response.parse()
            assert_matches_type(Rule, rule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: SearchPilot) -> None:
        rule = client.rules.list()
        assert_matches_type(SyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: SearchPilot) -> None:
        rule = client.rules.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            enabled=True,
            is_in_split_test=True,
            section_slug="section_slug",
        )
        assert_matches_type(SyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: SearchPilot) -> None:
        response = client.rules.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = response.parse()
        assert_matches_type(SyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: SearchPilot) -> None:
        with client.rules.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = response.parse()
            assert_matches_type(SyncCursorURLPage[Rule], rule, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRules:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchPilot) -> None:
        rule = await async_client.rules.retrieve(
            0,
        )
        assert_matches_type(Rule, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.rules.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = await response.parse()
        assert_matches_type(Rule, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.rules.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = await response.parse()
            assert_matches_type(Rule, rule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchPilot) -> None:
        rule = await async_client.rules.list()
        assert_matches_type(AsyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchPilot) -> None:
        rule = await async_client.rules.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            enabled=True,
            is_in_split_test=True,
            section_slug="section_slug",
        )
        assert_matches_type(AsyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.rules.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = await response.parse()
        assert_matches_type(AsyncCursorURLPage[Rule], rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.rules.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = await response.parse()
            assert_matches_type(AsyncCursorURLPage[Rule], rule, path=["response"])

        assert cast(Any, response.is_closed) is True
