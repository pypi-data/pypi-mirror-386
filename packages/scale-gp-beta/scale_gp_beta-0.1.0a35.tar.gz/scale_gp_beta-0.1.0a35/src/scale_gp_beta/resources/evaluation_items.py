# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import evaluation_item_list_params, evaluation_item_retrieve_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursorPage, AsyncCursorPage
from .._base_client import AsyncPaginator, make_request_options
from ..types.evaluation_item import EvaluationItem

__all__ = ["EvaluationItemsResource", "AsyncEvaluationItemsResource"]


class EvaluationItemsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EvaluationItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return EvaluationItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EvaluationItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return EvaluationItemsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        evaluation_item_id: str,
        *,
        include_archived: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EvaluationItem:
        """
        Get Evaluation Item

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_item_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_item_id` but received {evaluation_item_id!r}")
        return self._get(
            f"/v5/evaluation-items/{evaluation_item_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"include_archived": include_archived}, evaluation_item_retrieve_params.EvaluationItemRetrieveParams
                ),
            ),
            cast_to=EvaluationItem,
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        evaluation_id: str | Omit = omit,
        include_archived: bool | Omit = omit,
        limit: int | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[EvaluationItem]:
        """
        List Evaluation Items

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/evaluation-items",
            page=SyncCursorPage[EvaluationItem],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "evaluation_id": evaluation_id,
                        "include_archived": include_archived,
                        "limit": limit,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                    },
                    evaluation_item_list_params.EvaluationItemListParams,
                ),
            ),
            model=EvaluationItem,
        )


class AsyncEvaluationItemsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEvaluationItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return AsyncEvaluationItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEvaluationItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return AsyncEvaluationItemsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        evaluation_item_id: str,
        *,
        include_archived: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EvaluationItem:
        """
        Get Evaluation Item

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_item_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_item_id` but received {evaluation_item_id!r}")
        return await self._get(
            f"/v5/evaluation-items/{evaluation_item_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include_archived": include_archived}, evaluation_item_retrieve_params.EvaluationItemRetrieveParams
                ),
            ),
            cast_to=EvaluationItem,
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        evaluation_id: str | Omit = omit,
        include_archived: bool | Omit = omit,
        limit: int | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[EvaluationItem, AsyncCursorPage[EvaluationItem]]:
        """
        List Evaluation Items

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/evaluation-items",
            page=AsyncCursorPage[EvaluationItem],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "evaluation_id": evaluation_id,
                        "include_archived": include_archived,
                        "limit": limit,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                    },
                    evaluation_item_list_params.EvaluationItemListParams,
                ),
            ),
            model=EvaluationItem,
        )


class EvaluationItemsResourceWithRawResponse:
    def __init__(self, evaluation_items: EvaluationItemsResource) -> None:
        self._evaluation_items = evaluation_items

        self.retrieve = to_raw_response_wrapper(
            evaluation_items.retrieve,
        )
        self.list = to_raw_response_wrapper(
            evaluation_items.list,
        )


class AsyncEvaluationItemsResourceWithRawResponse:
    def __init__(self, evaluation_items: AsyncEvaluationItemsResource) -> None:
        self._evaluation_items = evaluation_items

        self.retrieve = async_to_raw_response_wrapper(
            evaluation_items.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            evaluation_items.list,
        )


class EvaluationItemsResourceWithStreamingResponse:
    def __init__(self, evaluation_items: EvaluationItemsResource) -> None:
        self._evaluation_items = evaluation_items

        self.retrieve = to_streamed_response_wrapper(
            evaluation_items.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            evaluation_items.list,
        )


class AsyncEvaluationItemsResourceWithStreamingResponse:
    def __init__(self, evaluation_items: AsyncEvaluationItemsResource) -> None:
        self._evaluation_items = evaluation_items

        self.retrieve = async_to_streamed_response_wrapper(
            evaluation_items.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            evaluation_items.list,
        )
