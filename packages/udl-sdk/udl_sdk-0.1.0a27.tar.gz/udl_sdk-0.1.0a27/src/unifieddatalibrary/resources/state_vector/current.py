# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncOffsetPage, AsyncOffsetPage
from ..._base_client import AsyncPaginator, make_request_options
from ...types.state_vector import current_list_params, current_tuple_params
from ...types.state_vector_abridged import StateVectorAbridged
from ...types.state_vector.current_tuple_response import CurrentTupleResponse

__all__ = ["CurrentResource", "AsyncCurrentResource"]


class CurrentResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CurrentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return CurrentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CurrentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return CurrentResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncOffsetPage[StateVectorAbridged]:
        """
        Service operation to dynamically query/filter current StateVector data within
        the system by a variety of query parameters not specified in this API
        documentation. A current StateVector is the currently active, latest StateVector
        for an on-orbit object. Current state vectors are tracked by source and a source
        should be provided as a query parameter to this service operation to view the
        'current' catalog for a particular provider. Default current state vector
        sources may vary by UDL environment. Please contact the UDL help desk for more
        information, or explicitly specify the desired source. See the queryhelp
        operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required
        query parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/statevector/current",
            page=SyncOffsetPage[StateVectorAbridged],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    current_list_params.CurrentListParams,
                ),
            ),
            model=StateVectorAbridged,
        )

    def tuple(
        self,
        *,
        columns: str,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrentTupleResponse:
        """
        Service operation to dynamically query/filter current StateVector data within
        the system by a variety of query parameters not specified in this API
        documentation. A current StateVector is the currently active, latest StateVector
        for an on-orbit object. Current state vectors are tracked by source and a source
        should be provided as a query parameter to this service operation to view the
        'current' catalog for a particular provider. Default current state vector
        sources may vary by UDL environment. Please contact the UDL help desk for more
        information, or explicitly specify the desired source. See the queryhelp
        operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required
        query parameter information.

        Args:
          columns: Comma-separated list of valid field names for this data type to be returned in
              the response. Only the fields specified will be returned as well as the
              classification marking of the data, if applicable. See the ‘queryhelp’ operation
              for a complete list of possible fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/udl/statevector/current/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "columns": columns,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    current_tuple_params.CurrentTupleParams,
                ),
            ),
            cast_to=CurrentTupleResponse,
        )


class AsyncCurrentResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCurrentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCurrentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCurrentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return AsyncCurrentResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[StateVectorAbridged, AsyncOffsetPage[StateVectorAbridged]]:
        """
        Service operation to dynamically query/filter current StateVector data within
        the system by a variety of query parameters not specified in this API
        documentation. A current StateVector is the currently active, latest StateVector
        for an on-orbit object. Current state vectors are tracked by source and a source
        should be provided as a query parameter to this service operation to view the
        'current' catalog for a particular provider. Default current state vector
        sources may vary by UDL environment. Please contact the UDL help desk for more
        information, or explicitly specify the desired source. See the queryhelp
        operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required
        query parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/statevector/current",
            page=AsyncOffsetPage[StateVectorAbridged],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    current_list_params.CurrentListParams,
                ),
            ),
            model=StateVectorAbridged,
        )

    async def tuple(
        self,
        *,
        columns: str,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrentTupleResponse:
        """
        Service operation to dynamically query/filter current StateVector data within
        the system by a variety of query parameters not specified in this API
        documentation. A current StateVector is the currently active, latest StateVector
        for an on-orbit object. Current state vectors are tracked by source and a source
        should be provided as a query parameter to this service operation to view the
        'current' catalog for a particular provider. Default current state vector
        sources may vary by UDL environment. Please contact the UDL help desk for more
        information, or explicitly specify the desired source. See the queryhelp
        operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required
        query parameter information.

        Args:
          columns: Comma-separated list of valid field names for this data type to be returned in
              the response. Only the fields specified will be returned as well as the
              classification marking of the data, if applicable. See the ‘queryhelp’ operation
              for a complete list of possible fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/udl/statevector/current/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "columns": columns,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    current_tuple_params.CurrentTupleParams,
                ),
            ),
            cast_to=CurrentTupleResponse,
        )


class CurrentResourceWithRawResponse:
    def __init__(self, current: CurrentResource) -> None:
        self._current = current

        self.list = to_raw_response_wrapper(
            current.list,
        )
        self.tuple = to_raw_response_wrapper(
            current.tuple,
        )


class AsyncCurrentResourceWithRawResponse:
    def __init__(self, current: AsyncCurrentResource) -> None:
        self._current = current

        self.list = async_to_raw_response_wrapper(
            current.list,
        )
        self.tuple = async_to_raw_response_wrapper(
            current.tuple,
        )


class CurrentResourceWithStreamingResponse:
    def __init__(self, current: CurrentResource) -> None:
        self._current = current

        self.list = to_streamed_response_wrapper(
            current.list,
        )
        self.tuple = to_streamed_response_wrapper(
            current.tuple,
        )


class AsyncCurrentResourceWithStreamingResponse:
    def __init__(self, current: AsyncCurrentResource) -> None:
        self._current = current

        self.list = async_to_streamed_response_wrapper(
            current.list,
        )
        self.tuple = async_to_streamed_response_wrapper(
            current.tuple,
        )
