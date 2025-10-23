# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from SearchPilot import SearchPilot, AsyncSearchPilot
from tests.utils import assert_matches_type
from SearchPilot.pagination import SyncCursorURLPage, AsyncCursorURLPage
from SearchPilot.types.shared import Customer

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCustomers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: SearchPilot) -> None:
        customer = client.customers.retrieve(
            "customer_slug",
        )
        assert_matches_type(Customer, customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: SearchPilot) -> None:
        response = client.customers.with_raw_response.retrieve(
            "customer_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(Customer, customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: SearchPilot) -> None:
        with client.customers.with_streaming_response.retrieve(
            "customer_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(Customer, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `customer_slug` but received ''"):
            client.customers.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: SearchPilot) -> None:
        customer = client.customers.list()
        assert_matches_type(SyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: SearchPilot) -> None:
        customer = client.customers.list(
            cursor="cursor",
        )
        assert_matches_type(SyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: SearchPilot) -> None:
        response = client.customers.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(SyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: SearchPilot) -> None:
        with client.customers.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(SyncCursorURLPage[Customer], customer, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCustomers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchPilot) -> None:
        customer = await async_client.customers.retrieve(
            "customer_slug",
        )
        assert_matches_type(Customer, customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.customers.with_raw_response.retrieve(
            "customer_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(Customer, customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.customers.with_streaming_response.retrieve(
            "customer_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(Customer, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `customer_slug` but received ''"):
            await async_client.customers.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchPilot) -> None:
        customer = await async_client.customers.list()
        assert_matches_type(AsyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchPilot) -> None:
        customer = await async_client.customers.list(
            cursor="cursor",
        )
        assert_matches_type(AsyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.customers.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(AsyncCursorURLPage[Customer], customer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.customers.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(AsyncCursorURLPage[Customer], customer, path=["response"])

        assert cast(Any, response.is_closed) is True
