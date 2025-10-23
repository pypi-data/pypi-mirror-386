# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ..types import account_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursorURLPage, AsyncCursorURLPage
from .._base_client import AsyncPaginator, make_request_options
from ..types.shared.account import Account

__all__ = ["AccountsResource", "AsyncAccountsResource"]


class AccountsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AccountsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        deployment_status: Literal["deployed", "migrating", "pre-deployment", "retired", "sales", "test"] | Omit = omit,
        environment: Optional[Literal["Demo", "dev", "lower_envs", "production", "qa", "staging", "uat"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorURLPage[Account]:
        """
        Args:
          cursor: The pagination cursor value.

          customer_slug: Customer slug

          deployment_status: - `deployed` - Deployed
              - `pre-deployment` - Pre Deployment
              - `migrating` - Migrating
              - `sales` - Sales
              - `test` - Test
              - `retired` - Retired

          environment: - `production` - Production
              - `staging` - Staging
              - `qa` - QA
              - `dev` - Dev
              - `uat` - UAT
              - `lower_envs` - Lower Environments
              - `Demo` - Demo

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/external/v1/accounts/",
            page=SyncCursorURLPage[Account],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "deployment_status": deployment_status,
                        "environment": environment,
                    },
                    account_list_params.AccountListParams,
                ),
            ),
            model=Account,
        )

    def retrieve1(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test1",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve10(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test10",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve11(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test11",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve12(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test12",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve2(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test2",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve3(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test3",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve4(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test4",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve5(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test5",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve6(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test6",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve7(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test7",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve8(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test8",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def retrieve9(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return self._get(
            f"/api/external/v1/accounts/{account_slug}/test9",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )


class AsyncAccountsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncAccountsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        deployment_status: Literal["deployed", "migrating", "pre-deployment", "retired", "sales", "test"] | Omit = omit,
        environment: Optional[Literal["Demo", "dev", "lower_envs", "production", "qa", "staging", "uat"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[Account, AsyncCursorURLPage[Account]]:
        """
        Args:
          cursor: The pagination cursor value.

          customer_slug: Customer slug

          deployment_status: - `deployed` - Deployed
              - `pre-deployment` - Pre Deployment
              - `migrating` - Migrating
              - `sales` - Sales
              - `test` - Test
              - `retired` - Retired

          environment: - `production` - Production
              - `staging` - Staging
              - `qa` - QA
              - `dev` - Dev
              - `uat` - UAT
              - `lower_envs` - Lower Environments
              - `Demo` - Demo

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/external/v1/accounts/",
            page=AsyncCursorURLPage[Account],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "deployment_status": deployment_status,
                        "environment": environment,
                    },
                    account_list_params.AccountListParams,
                ),
            ),
            model=Account,
        )

    async def retrieve1(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test1",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve10(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test10",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve11(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test11",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve12(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test12",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve2(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test2",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve3(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test3",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve4(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test4",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve5(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test5",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve6(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test6",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve7(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test7",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve8(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test8",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def retrieve9(
        self,
        account_slug: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        return await self._get(
            f"/api/external/v1/accounts/{account_slug}/test9",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )


class AccountsResourceWithRawResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.list = to_raw_response_wrapper(
            accounts.list,
        )
        self.retrieve1 = to_raw_response_wrapper(
            accounts.retrieve1,
        )
        self.retrieve10 = to_raw_response_wrapper(
            accounts.retrieve10,
        )
        self.retrieve11 = to_raw_response_wrapper(
            accounts.retrieve11,
        )
        self.retrieve12 = to_raw_response_wrapper(
            accounts.retrieve12,
        )
        self.retrieve2 = to_raw_response_wrapper(
            accounts.retrieve2,
        )
        self.retrieve3 = to_raw_response_wrapper(
            accounts.retrieve3,
        )
        self.retrieve4 = to_raw_response_wrapper(
            accounts.retrieve4,
        )
        self.retrieve5 = to_raw_response_wrapper(
            accounts.retrieve5,
        )
        self.retrieve6 = to_raw_response_wrapper(
            accounts.retrieve6,
        )
        self.retrieve7 = to_raw_response_wrapper(
            accounts.retrieve7,
        )
        self.retrieve8 = to_raw_response_wrapper(
            accounts.retrieve8,
        )
        self.retrieve9 = to_raw_response_wrapper(
            accounts.retrieve9,
        )


class AsyncAccountsResourceWithRawResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = async_to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            accounts.list,
        )
        self.retrieve1 = async_to_raw_response_wrapper(
            accounts.retrieve1,
        )
        self.retrieve10 = async_to_raw_response_wrapper(
            accounts.retrieve10,
        )
        self.retrieve11 = async_to_raw_response_wrapper(
            accounts.retrieve11,
        )
        self.retrieve12 = async_to_raw_response_wrapper(
            accounts.retrieve12,
        )
        self.retrieve2 = async_to_raw_response_wrapper(
            accounts.retrieve2,
        )
        self.retrieve3 = async_to_raw_response_wrapper(
            accounts.retrieve3,
        )
        self.retrieve4 = async_to_raw_response_wrapper(
            accounts.retrieve4,
        )
        self.retrieve5 = async_to_raw_response_wrapper(
            accounts.retrieve5,
        )
        self.retrieve6 = async_to_raw_response_wrapper(
            accounts.retrieve6,
        )
        self.retrieve7 = async_to_raw_response_wrapper(
            accounts.retrieve7,
        )
        self.retrieve8 = async_to_raw_response_wrapper(
            accounts.retrieve8,
        )
        self.retrieve9 = async_to_raw_response_wrapper(
            accounts.retrieve9,
        )


class AccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            accounts.list,
        )
        self.retrieve1 = to_streamed_response_wrapper(
            accounts.retrieve1,
        )
        self.retrieve10 = to_streamed_response_wrapper(
            accounts.retrieve10,
        )
        self.retrieve11 = to_streamed_response_wrapper(
            accounts.retrieve11,
        )
        self.retrieve12 = to_streamed_response_wrapper(
            accounts.retrieve12,
        )
        self.retrieve2 = to_streamed_response_wrapper(
            accounts.retrieve2,
        )
        self.retrieve3 = to_streamed_response_wrapper(
            accounts.retrieve3,
        )
        self.retrieve4 = to_streamed_response_wrapper(
            accounts.retrieve4,
        )
        self.retrieve5 = to_streamed_response_wrapper(
            accounts.retrieve5,
        )
        self.retrieve6 = to_streamed_response_wrapper(
            accounts.retrieve6,
        )
        self.retrieve7 = to_streamed_response_wrapper(
            accounts.retrieve7,
        )
        self.retrieve8 = to_streamed_response_wrapper(
            accounts.retrieve8,
        )
        self.retrieve9 = to_streamed_response_wrapper(
            accounts.retrieve9,
        )


class AsyncAccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = async_to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            accounts.list,
        )
        self.retrieve1 = async_to_streamed_response_wrapper(
            accounts.retrieve1,
        )
        self.retrieve10 = async_to_streamed_response_wrapper(
            accounts.retrieve10,
        )
        self.retrieve11 = async_to_streamed_response_wrapper(
            accounts.retrieve11,
        )
        self.retrieve12 = async_to_streamed_response_wrapper(
            accounts.retrieve12,
        )
        self.retrieve2 = async_to_streamed_response_wrapper(
            accounts.retrieve2,
        )
        self.retrieve3 = async_to_streamed_response_wrapper(
            accounts.retrieve3,
        )
        self.retrieve4 = async_to_streamed_response_wrapper(
            accounts.retrieve4,
        )
        self.retrieve5 = async_to_streamed_response_wrapper(
            accounts.retrieve5,
        )
        self.retrieve6 = async_to_streamed_response_wrapper(
            accounts.retrieve6,
        )
        self.retrieve7 = async_to_streamed_response_wrapper(
            accounts.retrieve7,
        )
        self.retrieve8 = async_to_streamed_response_wrapper(
            accounts.retrieve8,
        )
        self.retrieve9 = async_to_streamed_response_wrapper(
            accounts.retrieve9,
        )
