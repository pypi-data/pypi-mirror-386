# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Mapping, cast
from datetime import datetime

import httpx

from ...types import (
    gnss_raw_if_get_params,
    gnss_raw_if_list_params,
    gnss_raw_if_count_params,
    gnss_raw_if_tuple_params,
    gnss_raw_if_file_get_params,
    gnss_raw_if_upload_zip_params,
)
from .history import (
    HistoryResource,
    AsyncHistoryResource,
    HistoryResourceWithRawResponse,
    AsyncHistoryResourceWithRawResponse,
    HistoryResourceWithStreamingResponse,
    AsyncHistoryResourceWithStreamingResponse,
)
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, FileTypes, omit, not_given
from ..._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from ...pagination import SyncOffsetPage, AsyncOffsetPage
from ..._base_client import AsyncPaginator, make_request_options
from ...types.gnss_raw_if_get_response import GnssRawIfGetResponse
from ...types.gnss_raw_if_list_response import GnssRawIfListResponse
from ...types.gnss_raw_if_tuple_response import GnssRawIfTupleResponse
from ...types.gnss_raw_if_queryhelp_response import GnssRawIfQueryhelpResponse

__all__ = ["GnssRawIfResource", "AsyncGnssRawIfResource"]


class GnssRawIfResource(SyncAPIResource):
    @cached_property
    def history(self) -> HistoryResource:
        return HistoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> GnssRawIfResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GnssRawIfResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GnssRawIfResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return GnssRawIfResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncOffsetPage[GnssRawIfListResponse]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/gnssrawif",
            page=SyncOffsetPage[GnssRawIfListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_list_params.GnssRawIfListParams,
                ),
            ),
            model=GnssRawIfListResponse,
        )

    def count(
        self,
        *,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
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
          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return self._get(
            "/udl/gnssrawif/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_count_params.GnssRawIfCountParams,
                ),
            ),
            cast_to=str,
        )

    def file_get(
        self,
        id: str,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """
        Service operation to get a single GNSSRAWIF hdf5 file by its unique ID passed as
        a path parameter. The file is returned as an attachment Content-Disposition.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "application/octet-stream", **(extra_headers or {})}
        return self._get(
            f"/udl/gnssrawif/getFile/{id}",
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
                    gnss_raw_if_file_get_params.GnssRawIfFileGetParams,
                ),
            ),
            cast_to=BinaryAPIResponse,
        )

    def get(
        self,
        id: str,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfGetResponse:
        """
        Service operation to get a single GNSSRawIF by its unique ID passed as a path
        parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/udl/gnssrawif/{id}",
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
                    gnss_raw_if_get_params.GnssRawIfGetParams,
                ),
            ),
            cast_to=GnssRawIfGetResponse,
        )

    def queryhelp(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfQueryhelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return self._get(
            "/udl/gnssrawif/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GnssRawIfQueryhelpResponse,
        )

    def tuple(
        self,
        *,
        columns: str,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfTupleResponse:
        """
        Service operation to dynamically query data and only return specified
        columns/fields. Requested columns are specified by the 'columns' query parameter
        and should be a comma separated list of valid fields for the specified data
        type. classificationMarking is always returned. See the queryhelp operation
        (/udl/<datatype>/queryhelp) for more details on valid/required query parameter
        information. An example URI: /udl/elset/tuple?columns=satNo,period&epoch=>now-5
        hours would return the satNo and period of elsets with an epoch greater than 5
        hours ago.

        Args:
          columns: Comma-separated list of valid field names for this data type to be returned in
              the response. Only the fields specified will be returned as well as the
              classification marking of the data, if applicable. See the ‘queryhelp’ operation
              for a complete list of possible fields.

          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/udl/gnssrawif/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "columns": columns,
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_tuple_params.GnssRawIfTupleParams,
                ),
            ),
            cast_to=GnssRawIfTupleResponse,
        )

    def upload_zip(
        self,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Upload an HDF5 file with its metadata.

        The request body requires a zip file containing exactly two files:\\
        1\\)) A file with the `.json` file extension whose content conforms to the `GNSSRawIF_Ingest`
        schema.\\
        2\\)) A file with the `.hdf5` file extension.

        The JSON and HDF5 files will be associated with each other via the `id` field.
        Query the metadata via `GET /udl/gnssrawif` and use
        `GET /udl/gnssrawif/getFile/{id}` to retrieve the HDF5 file.

        This operation only accepts application/zip media. The application/json request
        body is documented to provide a convenient reference to the ingest schema.

        This operation is intended to be used for automated feeds into UDL. A specific
        role is required to perform this service operation. Please contact the UDL team
        for assistance.

        Args:
          file: Zip file containing files described in the specification

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers["Content-Type"] = "multipart/form-data"
        return self._post(
            "/filedrop/udl-gnssrawif",
            body=maybe_transform(body, gnss_raw_if_upload_zip_params.GnssRawIfUploadZipParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncGnssRawIfResource(AsyncAPIResource):
    @cached_property
    def history(self) -> AsyncHistoryResource:
        return AsyncHistoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncGnssRawIfResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGnssRawIfResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGnssRawIfResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return AsyncGnssRawIfResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[GnssRawIfListResponse, AsyncOffsetPage[GnssRawIfListResponse]]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/gnssrawif",
            page=AsyncOffsetPage[GnssRawIfListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_list_params.GnssRawIfListParams,
                ),
            ),
            model=GnssRawIfListResponse,
        )

    async def count(
        self,
        *,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
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
          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return await self._get(
            "/udl/gnssrawif/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_count_params.GnssRawIfCountParams,
                ),
            ),
            cast_to=str,
        )

    async def file_get(
        self,
        id: str,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """
        Service operation to get a single GNSSRAWIF hdf5 file by its unique ID passed as
        a path parameter. The file is returned as an attachment Content-Disposition.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "application/octet-stream", **(extra_headers or {})}
        return await self._get(
            f"/udl/gnssrawif/getFile/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_file_get_params.GnssRawIfFileGetParams,
                ),
            ),
            cast_to=AsyncBinaryAPIResponse,
        )

    async def get(
        self,
        id: str,
        *,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfGetResponse:
        """
        Service operation to get a single GNSSRawIF by its unique ID passed as a path
        parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/udl/gnssrawif/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_get_params.GnssRawIfGetParams,
                ),
            ),
            cast_to=GnssRawIfGetResponse,
        )

    async def queryhelp(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfQueryhelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return await self._get(
            "/udl/gnssrawif/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GnssRawIfQueryhelpResponse,
        )

    async def tuple(
        self,
        *,
        columns: str,
        start_time: Union[str, datetime],
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GnssRawIfTupleResponse:
        """
        Service operation to dynamically query data and only return specified
        columns/fields. Requested columns are specified by the 'columns' query parameter
        and should be a comma separated list of valid fields for the specified data
        type. classificationMarking is always returned. See the queryhelp operation
        (/udl/<datatype>/queryhelp) for more details on valid/required query parameter
        information. An example URI: /udl/elset/tuple?columns=satNo,period&epoch=>now-5
        hours would return the satNo and period of elsets with an epoch greater than 5
        hours ago.

        Args:
          columns: Comma-separated list of valid field names for this data type to be returned in
              the response. Only the fields specified will be returned as well as the
              classification marking of the data, if applicable. See the ‘queryhelp’ operation
              for a complete list of possible fields.

          start_time: Start time of the data contained in the associated binary file, in ISO 8601 UTC
              format with microsecond precision. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/udl/gnssrawif/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "columns": columns,
                        "start_time": start_time,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    gnss_raw_if_tuple_params.GnssRawIfTupleParams,
                ),
            ),
            cast_to=GnssRawIfTupleResponse,
        )

    async def upload_zip(
        self,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Upload an HDF5 file with its metadata.

        The request body requires a zip file containing exactly two files:\\
        1\\)) A file with the `.json` file extension whose content conforms to the `GNSSRawIF_Ingest`
        schema.\\
        2\\)) A file with the `.hdf5` file extension.

        The JSON and HDF5 files will be associated with each other via the `id` field.
        Query the metadata via `GET /udl/gnssrawif` and use
        `GET /udl/gnssrawif/getFile/{id}` to retrieve the HDF5 file.

        This operation only accepts application/zip media. The application/json request
        body is documented to provide a convenient reference to the ingest schema.

        This operation is intended to be used for automated feeds into UDL. A specific
        role is required to perform this service operation. Please contact the UDL team
        for assistance.

        Args:
          file: Zip file containing files described in the specification

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers["Content-Type"] = "multipart/form-data"
        return await self._post(
            "/filedrop/udl-gnssrawif",
            body=await async_maybe_transform(body, gnss_raw_if_upload_zip_params.GnssRawIfUploadZipParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class GnssRawIfResourceWithRawResponse:
    def __init__(self, gnss_raw_if: GnssRawIfResource) -> None:
        self._gnss_raw_if = gnss_raw_if

        self.list = to_raw_response_wrapper(
            gnss_raw_if.list,
        )
        self.count = to_raw_response_wrapper(
            gnss_raw_if.count,
        )
        self.file_get = to_custom_raw_response_wrapper(
            gnss_raw_if.file_get,
            BinaryAPIResponse,
        )
        self.get = to_raw_response_wrapper(
            gnss_raw_if.get,
        )
        self.queryhelp = to_raw_response_wrapper(
            gnss_raw_if.queryhelp,
        )
        self.tuple = to_raw_response_wrapper(
            gnss_raw_if.tuple,
        )
        self.upload_zip = to_raw_response_wrapper(
            gnss_raw_if.upload_zip,
        )

    @cached_property
    def history(self) -> HistoryResourceWithRawResponse:
        return HistoryResourceWithRawResponse(self._gnss_raw_if.history)


class AsyncGnssRawIfResourceWithRawResponse:
    def __init__(self, gnss_raw_if: AsyncGnssRawIfResource) -> None:
        self._gnss_raw_if = gnss_raw_if

        self.list = async_to_raw_response_wrapper(
            gnss_raw_if.list,
        )
        self.count = async_to_raw_response_wrapper(
            gnss_raw_if.count,
        )
        self.file_get = async_to_custom_raw_response_wrapper(
            gnss_raw_if.file_get,
            AsyncBinaryAPIResponse,
        )
        self.get = async_to_raw_response_wrapper(
            gnss_raw_if.get,
        )
        self.queryhelp = async_to_raw_response_wrapper(
            gnss_raw_if.queryhelp,
        )
        self.tuple = async_to_raw_response_wrapper(
            gnss_raw_if.tuple,
        )
        self.upload_zip = async_to_raw_response_wrapper(
            gnss_raw_if.upload_zip,
        )

    @cached_property
    def history(self) -> AsyncHistoryResourceWithRawResponse:
        return AsyncHistoryResourceWithRawResponse(self._gnss_raw_if.history)


class GnssRawIfResourceWithStreamingResponse:
    def __init__(self, gnss_raw_if: GnssRawIfResource) -> None:
        self._gnss_raw_if = gnss_raw_if

        self.list = to_streamed_response_wrapper(
            gnss_raw_if.list,
        )
        self.count = to_streamed_response_wrapper(
            gnss_raw_if.count,
        )
        self.file_get = to_custom_streamed_response_wrapper(
            gnss_raw_if.file_get,
            StreamedBinaryAPIResponse,
        )
        self.get = to_streamed_response_wrapper(
            gnss_raw_if.get,
        )
        self.queryhelp = to_streamed_response_wrapper(
            gnss_raw_if.queryhelp,
        )
        self.tuple = to_streamed_response_wrapper(
            gnss_raw_if.tuple,
        )
        self.upload_zip = to_streamed_response_wrapper(
            gnss_raw_if.upload_zip,
        )

    @cached_property
    def history(self) -> HistoryResourceWithStreamingResponse:
        return HistoryResourceWithStreamingResponse(self._gnss_raw_if.history)


class AsyncGnssRawIfResourceWithStreamingResponse:
    def __init__(self, gnss_raw_if: AsyncGnssRawIfResource) -> None:
        self._gnss_raw_if = gnss_raw_if

        self.list = async_to_streamed_response_wrapper(
            gnss_raw_if.list,
        )
        self.count = async_to_streamed_response_wrapper(
            gnss_raw_if.count,
        )
        self.file_get = async_to_custom_streamed_response_wrapper(
            gnss_raw_if.file_get,
            AsyncStreamedBinaryAPIResponse,
        )
        self.get = async_to_streamed_response_wrapper(
            gnss_raw_if.get,
        )
        self.queryhelp = async_to_streamed_response_wrapper(
            gnss_raw_if.queryhelp,
        )
        self.tuple = async_to_streamed_response_wrapper(
            gnss_raw_if.tuple,
        )
        self.upload_zip = async_to_streamed_response_wrapper(
            gnss_raw_if.upload_zip,
        )

    @cached_property
    def history(self) -> AsyncHistoryResourceWithStreamingResponse:
        return AsyncHistoryResourceWithStreamingResponse(self._gnss_raw_if.history)
