# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from SearchPilot import SearchPilot, AsyncSearchPilot
from tests.utils import assert_matches_type
from SearchPilot.pagination import SyncCursorURLPage, AsyncCursorURLPage
from SearchPilot.types.shared import Account

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAccounts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: SearchPilot) -> None:
        account = client.accounts.list()
        assert_matches_type(SyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: SearchPilot) -> None:
        account = client.accounts.list(
            cursor="cursor",
            customer_slug="customer_slug",
            deployment_status="deployed",
            environment="Demo",
        )
        assert_matches_type(SyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(SyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(SyncCursorURLPage[Account], account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve1(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve1(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve1(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve1(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve1(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve1(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve1(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve1(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve10(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve10(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve10(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve10(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve10(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve10(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve10(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve10(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve11(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve11(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve11(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve11(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve11(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve11(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve11(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve11(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve12(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve12(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve12(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve12(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve12(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve12(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve12(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve12(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve2(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve2(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve2(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve2(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve2(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve2(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve2(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve2(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve3(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve3(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve3(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve3(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve3(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve3(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve3(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve3(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve4(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve4(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve4(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve4(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve4(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve4(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve4(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve4(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve5(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve5(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve5(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve5(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve5(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve5(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve5(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve5(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve6(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve6(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve6(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve6(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve6(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve6(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve6(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve6(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve7(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve7(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve7(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve7(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve7(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve7(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve7(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve7(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve8(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve8(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve8(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve8(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve8(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve8(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve8(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve8(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve9(self, client: SearchPilot) -> None:
        account = client.accounts.retrieve9(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve9(self, client: SearchPilot) -> None:
        response = client.accounts.with_raw_response.retrieve9(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve9(self, client: SearchPilot) -> None:
        with client.accounts.with_streaming_response.retrieve9(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve9(self, client: SearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.accounts.with_raw_response.retrieve9(
                "",
            )


class TestAsyncAccounts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.list()
        assert_matches_type(AsyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.list(
            cursor="cursor",
            customer_slug="customer_slug",
            deployment_status="deployed",
            environment="Demo",
        )
        assert_matches_type(AsyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AsyncCursorURLPage[Account], account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AsyncCursorURLPage[Account], account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve1(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve1(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve1(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve1(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve1(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve1(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve1(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve1(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve10(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve10(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve10(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve10(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve10(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve10(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve10(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve10(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve11(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve11(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve11(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve11(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve11(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve11(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve11(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve11(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve12(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve12(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve12(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve12(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve12(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve12(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve12(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve12(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve2(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve2(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve2(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve2(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve2(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve2(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve2(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve2(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve3(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve3(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve3(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve3(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve3(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve3(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve3(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve3(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve4(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve4(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve4(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve4(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve4(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve4(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve4(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve4(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve5(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve5(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve5(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve5(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve5(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve5(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve5(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve5(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve6(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve6(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve6(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve6(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve6(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve6(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve6(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve6(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve7(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve7(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve7(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve7(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve7(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve7(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve7(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve7(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve8(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve8(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve8(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve8(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve8(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve8(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve8(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve8(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve9(self, async_client: AsyncSearchPilot) -> None:
        account = await async_client.accounts.retrieve9(
            "account_slug",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve9(self, async_client: AsyncSearchPilot) -> None:
        response = await async_client.accounts.with_raw_response.retrieve9(
            "account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve9(self, async_client: AsyncSearchPilot) -> None:
        async with async_client.accounts.with_streaming_response.retrieve9(
            "account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve9(self, async_client: AsyncSearchPilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.accounts.with_raw_response.retrieve9(
                "",
            )
