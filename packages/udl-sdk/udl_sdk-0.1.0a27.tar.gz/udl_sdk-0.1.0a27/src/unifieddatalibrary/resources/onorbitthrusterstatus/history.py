# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime

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
from ...types.onorbitthrusterstatus import history_list_params, history_count_params
from ...types.shared.onorbitthrusterstatus_full import OnorbitthrusterstatusFull

__all__ = ["HistoryResource", "AsyncHistoryResource"]


class HistoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> HistoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return HistoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HistoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return HistoryResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        columns: str | Omit = omit,
        first_result: int | Omit = omit,
        id_onorbit_thruster: str | Omit = omit,
        max_results: int | Omit = omit,
        status_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncOffsetPage[OnorbitthrusterstatusFull]:
        """
        Service operation to dynamically query historical data by a variety of query
        parameters not specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          columns: optional, fields for retrieval. When omitted, ALL fields are assumed. See the
              queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid
              query fields that can be selected.

          id_onorbit_thruster: (One or more of fields 'idOnorbitThruster, statusTime' are required.) ID of the
              associated OnorbitThruster record. This ID can be used to obtain additional
              information on an onorbit thruster object using the 'get by ID' operation (e.g.
              /udl/onorbitthruster/{id}). For example, the OnorbitThruster object with
              idOnorbitThruster = abc would be queried as /udl/onorbitthruster/abc.

          status_time: (One or more of fields 'idOnorbitThruster, statusTime' are required.) Datetime
              of the thruster status observation in ISO 8601 UTC datetime format with
              millisecond precision. (YYYY-MM-DDTHH:MM:SS.sssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/onorbitthrusterstatus/history",
            page=SyncOffsetPage[OnorbitthrusterstatusFull],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "columns": columns,
                        "first_result": first_result,
                        "id_onorbit_thruster": id_onorbit_thruster,
                        "max_results": max_results,
                        "status_time": status_time,
                    },
                    history_list_params.HistoryListParams,
                ),
            ),
            model=OnorbitthrusterstatusFull,
        )

    def count(
        self,
        *,
        first_result: int | Omit = omit,
        id_onorbit_thruster: str | Omit = omit,
        max_results: int | Omit = omit,
        status_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """
        Service operation to return the count of records satisfying the specified query
        parameters. This operation is useful to determine how many records pass a
        particular query criteria without retrieving large amounts of data. See the
        queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on
        valid/required query parameter information.

        Args:
          id_onorbit_thruster: (One or more of fields 'idOnorbitThruster, statusTime' are required.) ID of the
              associated OnorbitThruster record. This ID can be used to obtain additional
              information on an onorbit thruster object using the 'get by ID' operation (e.g.
              /udl/onorbitthruster/{id}). For example, the OnorbitThruster object with
              idOnorbitThruster = abc would be queried as /udl/onorbitthruster/abc.

          status_time: (One or more of fields 'idOnorbitThruster, statusTime' are required.) Datetime
              of the thruster status observation in ISO 8601 UTC datetime format with
              millisecond precision. (YYYY-MM-DDTHH:MM:SS.sssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return self._get(
            "/udl/onorbitthrusterstatus/history/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "first_result": first_result,
                        "id_onorbit_thruster": id_onorbit_thruster,
                        "max_results": max_results,
                        "status_time": status_time,
                    },
                    history_count_params.HistoryCountParams,
                ),
            ),
            cast_to=str,
        )


class AsyncHistoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncHistoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncHistoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHistoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return AsyncHistoryResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        columns: str | Omit = omit,
        first_result: int | Omit = omit,
        id_onorbit_thruster: str | Omit = omit,
        max_results: int | Omit = omit,
        status_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[OnorbitthrusterstatusFull, AsyncOffsetPage[OnorbitthrusterstatusFull]]:
        """
        Service operation to dynamically query historical data by a variety of query
        parameters not specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          columns: optional, fields for retrieval. When omitted, ALL fields are assumed. See the
              queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on valid
              query fields that can be selected.

          id_onorbit_thruster: (One or more of fields 'idOnorbitThruster, statusTime' are required.) ID of the
              associated OnorbitThruster record. This ID can be used to obtain additional
              information on an onorbit thruster object using the 'get by ID' operation (e.g.
              /udl/onorbitthruster/{id}). For example, the OnorbitThruster object with
              idOnorbitThruster = abc would be queried as /udl/onorbitthruster/abc.

          status_time: (One or more of fields 'idOnorbitThruster, statusTime' are required.) Datetime
              of the thruster status observation in ISO 8601 UTC datetime format with
              millisecond precision. (YYYY-MM-DDTHH:MM:SS.sssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/onorbitthrusterstatus/history",
            page=AsyncOffsetPage[OnorbitthrusterstatusFull],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "columns": columns,
                        "first_result": first_result,
                        "id_onorbit_thruster": id_onorbit_thruster,
                        "max_results": max_results,
                        "status_time": status_time,
                    },
                    history_list_params.HistoryListParams,
                ),
            ),
            model=OnorbitthrusterstatusFull,
        )

    async def count(
        self,
        *,
        first_result: int | Omit = omit,
        id_onorbit_thruster: str | Omit = omit,
        max_results: int | Omit = omit,
        status_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """
        Service operation to return the count of records satisfying the specified query
        parameters. This operation is useful to determine how many records pass a
        particular query criteria without retrieving large amounts of data. See the
        queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on
        valid/required query parameter information.

        Args:
          id_onorbit_thruster: (One or more of fields 'idOnorbitThruster, statusTime' are required.) ID of the
              associated OnorbitThruster record. This ID can be used to obtain additional
              information on an onorbit thruster object using the 'get by ID' operation (e.g.
              /udl/onorbitthruster/{id}). For example, the OnorbitThruster object with
              idOnorbitThruster = abc would be queried as /udl/onorbitthruster/abc.

          status_time: (One or more of fields 'idOnorbitThruster, statusTime' are required.) Datetime
              of the thruster status observation in ISO 8601 UTC datetime format with
              millisecond precision. (YYYY-MM-DDTHH:MM:SS.sssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return await self._get(
            "/udl/onorbitthrusterstatus/history/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "first_result": first_result,
                        "id_onorbit_thruster": id_onorbit_thruster,
                        "max_results": max_results,
                        "status_time": status_time,
                    },
                    history_count_params.HistoryCountParams,
                ),
            ),
            cast_to=str,
        )


class HistoryResourceWithRawResponse:
    def __init__(self, history: HistoryResource) -> None:
        self._history = history

        self.list = to_raw_response_wrapper(
            history.list,
        )
        self.count = to_raw_response_wrapper(
            history.count,
        )


class AsyncHistoryResourceWithRawResponse:
    def __init__(self, history: AsyncHistoryResource) -> None:
        self._history = history

        self.list = async_to_raw_response_wrapper(
            history.list,
        )
        self.count = async_to_raw_response_wrapper(
            history.count,
        )


class HistoryResourceWithStreamingResponse:
    def __init__(self, history: HistoryResource) -> None:
        self._history = history

        self.list = to_streamed_response_wrapper(
            history.list,
        )
        self.count = to_streamed_response_wrapper(
            history.count,
        )


class AsyncHistoryResourceWithStreamingResponse:
    def __init__(self, history: AsyncHistoryResource) -> None:
        self._history = history

        self.list = async_to_streamed_response_wrapper(
            history.list,
        )
        self.count = async_to_streamed_response_wrapper(
            history.count,
        )
