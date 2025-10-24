# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal

import httpx

from ...types import (
    sensor_maintenance_get_params,
    sensor_maintenance_list_params,
    sensor_maintenance_count_params,
    sensor_maintenance_tuple_params,
    sensor_maintenance_create_params,
    sensor_maintenance_update_params,
    sensor_maintenance_create_bulk_params,
    sensor_maintenance_list_current_params,
)
from .history import (
    HistoryResource,
    AsyncHistoryResource,
    HistoryResourceWithRawResponse,
    AsyncHistoryResourceWithRawResponse,
    HistoryResourceWithStreamingResponse,
    AsyncHistoryResourceWithStreamingResponse,
)
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ...types.sensor_maintenance_get_response import SensorMaintenanceGetResponse
from ...types.sensor_maintenance_list_response import SensorMaintenanceListResponse
from ...types.sensor_maintenance_tuple_response import SensorMaintenanceTupleResponse
from ...types.sensor_maintenance_query_help_response import SensorMaintenanceQueryHelpResponse
from ...types.sensor_maintenance_list_current_response import SensorMaintenanceListCurrentResponse

__all__ = ["SensorMaintenanceResource", "AsyncSensorMaintenanceResource"]


class SensorMaintenanceResource(SyncAPIResource):
    @cached_property
    def history(self) -> HistoryResource:
        return HistoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> SensorMaintenanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return SensorMaintenanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SensorMaintenanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return SensorMaintenanceResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        end_time: Union[str, datetime],
        site_code: str,
        source: str,
        start_time: Union[str, datetime],
        id: str | Omit = omit,
        activity: str | Omit = omit,
        approver: str | Omit = omit,
        changer: str | Omit = omit,
        duration: str | Omit = omit,
        eow_id: str | Omit = omit,
        equip_status: str | Omit = omit,
        id_sensor: str | Omit = omit,
        impacted_faces: str | Omit = omit,
        line_number: str | Omit = omit,
        md_ops_cap: str | Omit = omit,
        mw_ops_cap: str | Omit = omit,
        origin: str | Omit = omit,
        priority: str | Omit = omit,
        recall: str | Omit = omit,
        rel: str | Omit = omit,
        remark: str | Omit = omit,
        requestor: str | Omit = omit,
        resource: str | Omit = omit,
        rev: str | Omit = omit,
        ss_ops_cap: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take a single SensorMaintenance as a POST body and ingest
        into the database. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          classification_marking: Classification marking of the data in IC/CAPCO Portion-marked format.

          data_mode:
              Indicator of whether the data is EXERCISE, REAL, SIMULATED, or TEST data:

              EXERCISE:&nbsp;Data pertaining to a government or military exercise. The data
              may include both real and simulated data.

              REAL:&nbsp;Data collected or produced that pertains to real-world objects,
              events, and analysis.

              SIMULATED:&nbsp;Synthetic data generated by a model to mimic real-world
              datasets.

              TEST:&nbsp;Specific datasets used to evaluate compliance with specifications and
              requirements, and for validating technical, functional, and performance
              characteristics.

          end_time: The planned outage end time in ISO8601 UTC format.

          site_code: The site to which this item applies. NOTE - this site code is COLT specific and
              may not identically correspond to other UDL site IDs.

          source: Source of the data.

          start_time: The planned outage start time in ISO8601 UTC format.

          id: Unique identifier of the record, auto-generated by the system.

          activity: Description of the activity taking place during this outage.

          approver: The name of the approver.

          changer: The name of the changer, if applicable.

          duration: The duration of the planned outage, expressed as ddd:hh:mm.

          eow_id: COLT EOWID.

          equip_status: The mission capability status of the equipment (e.g. FMC, NMC, PMC, UNK, etc.).

          id_sensor: UUID of the sensor.

          impacted_faces: The sensor face(s) to which this COLT maintenance item applies, if applicable.

          line_number: The internal COLT line number assigned to this item.

          md_ops_cap: The Missile Defense operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          mw_ops_cap: The Missile Warning operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          priority: The priority of this maintenance item.

          recall: The minimum time required to recall this activity, expressed as ddd:hh:mm.

          rel: Release.

          remark: Remarks concerning this outage.

          requestor: The name of the requestor.

          resource: The name of the resource(s) affected by this maintenance item.

          rev: The revision number for this maintenance item.

          ss_ops_cap: The Space Surveillance operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/udl/sensormaintenance",
            body=maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "end_time": end_time,
                    "site_code": site_code,
                    "source": source,
                    "start_time": start_time,
                    "id": id,
                    "activity": activity,
                    "approver": approver,
                    "changer": changer,
                    "duration": duration,
                    "eow_id": eow_id,
                    "equip_status": equip_status,
                    "id_sensor": id_sensor,
                    "impacted_faces": impacted_faces,
                    "line_number": line_number,
                    "md_ops_cap": md_ops_cap,
                    "mw_ops_cap": mw_ops_cap,
                    "origin": origin,
                    "priority": priority,
                    "recall": recall,
                    "rel": rel,
                    "remark": remark,
                    "requestor": requestor,
                    "resource": resource,
                    "rev": rev,
                    "ss_ops_cap": ss_ops_cap,
                },
                sensor_maintenance_create_params.SensorMaintenanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update(
        self,
        path_id: str,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        end_time: Union[str, datetime],
        site_code: str,
        source: str,
        start_time: Union[str, datetime],
        body_id: str | Omit = omit,
        activity: str | Omit = omit,
        approver: str | Omit = omit,
        changer: str | Omit = omit,
        duration: str | Omit = omit,
        eow_id: str | Omit = omit,
        equip_status: str | Omit = omit,
        id_sensor: str | Omit = omit,
        impacted_faces: str | Omit = omit,
        line_number: str | Omit = omit,
        md_ops_cap: str | Omit = omit,
        mw_ops_cap: str | Omit = omit,
        origin: str | Omit = omit,
        priority: str | Omit = omit,
        recall: str | Omit = omit,
        rel: str | Omit = omit,
        remark: str | Omit = omit,
        requestor: str | Omit = omit,
        resource: str | Omit = omit,
        rev: str | Omit = omit,
        ss_ops_cap: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Service operation to update a single SensorMaintenance.

        A specific role is
        required to perform this service operation. Please contact the UDL team for
        assistance.

        Args:
          classification_marking: Classification marking of the data in IC/CAPCO Portion-marked format.

          data_mode:
              Indicator of whether the data is EXERCISE, REAL, SIMULATED, or TEST data:

              EXERCISE:&nbsp;Data pertaining to a government or military exercise. The data
              may include both real and simulated data.

              REAL:&nbsp;Data collected or produced that pertains to real-world objects,
              events, and analysis.

              SIMULATED:&nbsp;Synthetic data generated by a model to mimic real-world
              datasets.

              TEST:&nbsp;Specific datasets used to evaluate compliance with specifications and
              requirements, and for validating technical, functional, and performance
              characteristics.

          end_time: The planned outage end time in ISO8601 UTC format.

          site_code: The site to which this item applies. NOTE - this site code is COLT specific and
              may not identically correspond to other UDL site IDs.

          source: Source of the data.

          start_time: The planned outage start time in ISO8601 UTC format.

          body_id: Unique identifier of the record, auto-generated by the system.

          activity: Description of the activity taking place during this outage.

          approver: The name of the approver.

          changer: The name of the changer, if applicable.

          duration: The duration of the planned outage, expressed as ddd:hh:mm.

          eow_id: COLT EOWID.

          equip_status: The mission capability status of the equipment (e.g. FMC, NMC, PMC, UNK, etc.).

          id_sensor: UUID of the sensor.

          impacted_faces: The sensor face(s) to which this COLT maintenance item applies, if applicable.

          line_number: The internal COLT line number assigned to this item.

          md_ops_cap: The Missile Defense operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          mw_ops_cap: The Missile Warning operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          priority: The priority of this maintenance item.

          recall: The minimum time required to recall this activity, expressed as ddd:hh:mm.

          rel: Release.

          remark: Remarks concerning this outage.

          requestor: The name of the requestor.

          resource: The name of the resource(s) affected by this maintenance item.

          rev: The revision number for this maintenance item.

          ss_ops_cap: The Space Surveillance operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not path_id:
            raise ValueError(f"Expected a non-empty value for `path_id` but received {path_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/udl/sensormaintenance/{path_id}",
            body=maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "end_time": end_time,
                    "site_code": site_code,
                    "source": source,
                    "start_time": start_time,
                    "body_id": body_id,
                    "activity": activity,
                    "approver": approver,
                    "changer": changer,
                    "duration": duration,
                    "eow_id": eow_id,
                    "equip_status": equip_status,
                    "id_sensor": id_sensor,
                    "impacted_faces": impacted_faces,
                    "line_number": line_number,
                    "md_ops_cap": md_ops_cap,
                    "mw_ops_cap": mw_ops_cap,
                    "origin": origin,
                    "priority": priority,
                    "recall": recall,
                    "rel": rel,
                    "remark": remark,
                    "requestor": requestor,
                    "resource": resource,
                    "rev": rev,
                    "ss_ops_cap": ss_ops_cap,
                },
                sensor_maintenance_update_params.SensorMaintenanceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        *,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncOffsetPage[SensorMaintenanceListResponse]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/sensormaintenance",
            page=SyncOffsetPage[SensorMaintenanceListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_list_params.SensorMaintenanceListParams,
                ),
            ),
            model=SensorMaintenanceListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to delete a SensorMaintenance object specified by the passed
        ID path parameter. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/udl/sensormaintenance/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def count(
        self,
        *,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
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
          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return self._get(
            "/udl/sensormaintenance/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_count_params.SensorMaintenanceCountParams,
                ),
            ),
            cast_to=str,
        )

    def create_bulk(
        self,
        *,
        body: Iterable[sensor_maintenance_create_bulk_params.Body],
        origin: str | Omit = omit,
        source: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take multiple SensorMaintenance as a POST body and ingest
        into the database. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          origin: Origin of the SensorMaintenance data.

          source: Source of the SensorMaintenance data.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/udl/sensormaintenance/createBulk",
            body=maybe_transform(body, Iterable[sensor_maintenance_create_bulk_params.Body]),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "origin": origin,
                        "source": source,
                    },
                    sensor_maintenance_create_bulk_params.SensorMaintenanceCreateBulkParams,
                ),
            ),
            cast_to=NoneType,
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
    ) -> SensorMaintenanceGetResponse:
        """
        Service operation to get a single SensorMaintenance record by its unique ID
        passed as a path parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/udl/sensormaintenance/{id}",
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
                    sensor_maintenance_get_params.SensorMaintenanceGetParams,
                ),
            ),
            cast_to=SensorMaintenanceGetResponse,
        )

    def list_current(
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
    ) -> SyncOffsetPage[SensorMaintenanceListCurrentResponse]:
        """
        Service operation to get current Sensor Maintenance records using any number of
        additional parameters.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/sensormaintenance/current",
            page=SyncOffsetPage[SensorMaintenanceListCurrentResponse],
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
                    sensor_maintenance_list_current_params.SensorMaintenanceListCurrentParams,
                ),
            ),
            model=SensorMaintenanceListCurrentResponse,
        )

    def query_help(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SensorMaintenanceQueryHelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return self._get(
            "/udl/sensormaintenance/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SensorMaintenanceQueryHelpResponse,
        )

    def tuple(
        self,
        *,
        columns: str,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SensorMaintenanceTupleResponse:
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

          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/udl/sensormaintenance/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "columns": columns,
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_tuple_params.SensorMaintenanceTupleParams,
                ),
            ),
            cast_to=SensorMaintenanceTupleResponse,
        )


class AsyncSensorMaintenanceResource(AsyncAPIResource):
    @cached_property
    def history(self) -> AsyncHistoryResource:
        return AsyncHistoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSensorMaintenanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSensorMaintenanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSensorMaintenanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return AsyncSensorMaintenanceResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        end_time: Union[str, datetime],
        site_code: str,
        source: str,
        start_time: Union[str, datetime],
        id: str | Omit = omit,
        activity: str | Omit = omit,
        approver: str | Omit = omit,
        changer: str | Omit = omit,
        duration: str | Omit = omit,
        eow_id: str | Omit = omit,
        equip_status: str | Omit = omit,
        id_sensor: str | Omit = omit,
        impacted_faces: str | Omit = omit,
        line_number: str | Omit = omit,
        md_ops_cap: str | Omit = omit,
        mw_ops_cap: str | Omit = omit,
        origin: str | Omit = omit,
        priority: str | Omit = omit,
        recall: str | Omit = omit,
        rel: str | Omit = omit,
        remark: str | Omit = omit,
        requestor: str | Omit = omit,
        resource: str | Omit = omit,
        rev: str | Omit = omit,
        ss_ops_cap: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take a single SensorMaintenance as a POST body and ingest
        into the database. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          classification_marking: Classification marking of the data in IC/CAPCO Portion-marked format.

          data_mode:
              Indicator of whether the data is EXERCISE, REAL, SIMULATED, or TEST data:

              EXERCISE:&nbsp;Data pertaining to a government or military exercise. The data
              may include both real and simulated data.

              REAL:&nbsp;Data collected or produced that pertains to real-world objects,
              events, and analysis.

              SIMULATED:&nbsp;Synthetic data generated by a model to mimic real-world
              datasets.

              TEST:&nbsp;Specific datasets used to evaluate compliance with specifications and
              requirements, and for validating technical, functional, and performance
              characteristics.

          end_time: The planned outage end time in ISO8601 UTC format.

          site_code: The site to which this item applies. NOTE - this site code is COLT specific and
              may not identically correspond to other UDL site IDs.

          source: Source of the data.

          start_time: The planned outage start time in ISO8601 UTC format.

          id: Unique identifier of the record, auto-generated by the system.

          activity: Description of the activity taking place during this outage.

          approver: The name of the approver.

          changer: The name of the changer, if applicable.

          duration: The duration of the planned outage, expressed as ddd:hh:mm.

          eow_id: COLT EOWID.

          equip_status: The mission capability status of the equipment (e.g. FMC, NMC, PMC, UNK, etc.).

          id_sensor: UUID of the sensor.

          impacted_faces: The sensor face(s) to which this COLT maintenance item applies, if applicable.

          line_number: The internal COLT line number assigned to this item.

          md_ops_cap: The Missile Defense operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          mw_ops_cap: The Missile Warning operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          priority: The priority of this maintenance item.

          recall: The minimum time required to recall this activity, expressed as ddd:hh:mm.

          rel: Release.

          remark: Remarks concerning this outage.

          requestor: The name of the requestor.

          resource: The name of the resource(s) affected by this maintenance item.

          rev: The revision number for this maintenance item.

          ss_ops_cap: The Space Surveillance operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/udl/sensormaintenance",
            body=await async_maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "end_time": end_time,
                    "site_code": site_code,
                    "source": source,
                    "start_time": start_time,
                    "id": id,
                    "activity": activity,
                    "approver": approver,
                    "changer": changer,
                    "duration": duration,
                    "eow_id": eow_id,
                    "equip_status": equip_status,
                    "id_sensor": id_sensor,
                    "impacted_faces": impacted_faces,
                    "line_number": line_number,
                    "md_ops_cap": md_ops_cap,
                    "mw_ops_cap": mw_ops_cap,
                    "origin": origin,
                    "priority": priority,
                    "recall": recall,
                    "rel": rel,
                    "remark": remark,
                    "requestor": requestor,
                    "resource": resource,
                    "rev": rev,
                    "ss_ops_cap": ss_ops_cap,
                },
                sensor_maintenance_create_params.SensorMaintenanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update(
        self,
        path_id: str,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        end_time: Union[str, datetime],
        site_code: str,
        source: str,
        start_time: Union[str, datetime],
        body_id: str | Omit = omit,
        activity: str | Omit = omit,
        approver: str | Omit = omit,
        changer: str | Omit = omit,
        duration: str | Omit = omit,
        eow_id: str | Omit = omit,
        equip_status: str | Omit = omit,
        id_sensor: str | Omit = omit,
        impacted_faces: str | Omit = omit,
        line_number: str | Omit = omit,
        md_ops_cap: str | Omit = omit,
        mw_ops_cap: str | Omit = omit,
        origin: str | Omit = omit,
        priority: str | Omit = omit,
        recall: str | Omit = omit,
        rel: str | Omit = omit,
        remark: str | Omit = omit,
        requestor: str | Omit = omit,
        resource: str | Omit = omit,
        rev: str | Omit = omit,
        ss_ops_cap: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Service operation to update a single SensorMaintenance.

        A specific role is
        required to perform this service operation. Please contact the UDL team for
        assistance.

        Args:
          classification_marking: Classification marking of the data in IC/CAPCO Portion-marked format.

          data_mode:
              Indicator of whether the data is EXERCISE, REAL, SIMULATED, or TEST data:

              EXERCISE:&nbsp;Data pertaining to a government or military exercise. The data
              may include both real and simulated data.

              REAL:&nbsp;Data collected or produced that pertains to real-world objects,
              events, and analysis.

              SIMULATED:&nbsp;Synthetic data generated by a model to mimic real-world
              datasets.

              TEST:&nbsp;Specific datasets used to evaluate compliance with specifications and
              requirements, and for validating technical, functional, and performance
              characteristics.

          end_time: The planned outage end time in ISO8601 UTC format.

          site_code: The site to which this item applies. NOTE - this site code is COLT specific and
              may not identically correspond to other UDL site IDs.

          source: Source of the data.

          start_time: The planned outage start time in ISO8601 UTC format.

          body_id: Unique identifier of the record, auto-generated by the system.

          activity: Description of the activity taking place during this outage.

          approver: The name of the approver.

          changer: The name of the changer, if applicable.

          duration: The duration of the planned outage, expressed as ddd:hh:mm.

          eow_id: COLT EOWID.

          equip_status: The mission capability status of the equipment (e.g. FMC, NMC, PMC, UNK, etc.).

          id_sensor: UUID of the sensor.

          impacted_faces: The sensor face(s) to which this COLT maintenance item applies, if applicable.

          line_number: The internal COLT line number assigned to this item.

          md_ops_cap: The Missile Defense operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          mw_ops_cap: The Missile Warning operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          priority: The priority of this maintenance item.

          recall: The minimum time required to recall this activity, expressed as ddd:hh:mm.

          rel: Release.

          remark: Remarks concerning this outage.

          requestor: The name of the requestor.

          resource: The name of the resource(s) affected by this maintenance item.

          rev: The revision number for this maintenance item.

          ss_ops_cap: The Space Surveillance operational capability of this maintenance item. Typical
              values are G, Y, R, and - for non-applicable sites.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not path_id:
            raise ValueError(f"Expected a non-empty value for `path_id` but received {path_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/udl/sensormaintenance/{path_id}",
            body=await async_maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "end_time": end_time,
                    "site_code": site_code,
                    "source": source,
                    "start_time": start_time,
                    "body_id": body_id,
                    "activity": activity,
                    "approver": approver,
                    "changer": changer,
                    "duration": duration,
                    "eow_id": eow_id,
                    "equip_status": equip_status,
                    "id_sensor": id_sensor,
                    "impacted_faces": impacted_faces,
                    "line_number": line_number,
                    "md_ops_cap": md_ops_cap,
                    "mw_ops_cap": mw_ops_cap,
                    "origin": origin,
                    "priority": priority,
                    "recall": recall,
                    "rel": rel,
                    "remark": remark,
                    "requestor": requestor,
                    "resource": resource,
                    "rev": rev,
                    "ss_ops_cap": ss_ops_cap,
                },
                sensor_maintenance_update_params.SensorMaintenanceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        *,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[SensorMaintenanceListResponse, AsyncOffsetPage[SensorMaintenanceListResponse]]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/sensormaintenance",
            page=AsyncOffsetPage[SensorMaintenanceListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_list_params.SensorMaintenanceListParams,
                ),
            ),
            model=SensorMaintenanceListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to delete a SensorMaintenance object specified by the passed
        ID path parameter. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/udl/sensormaintenance/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def count(
        self,
        *,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
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
          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return await self._get(
            "/udl/sensormaintenance/count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_count_params.SensorMaintenanceCountParams,
                ),
            ),
            cast_to=str,
        )

    async def create_bulk(
        self,
        *,
        body: Iterable[sensor_maintenance_create_bulk_params.Body],
        origin: str | Omit = omit,
        source: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take multiple SensorMaintenance as a POST body and ingest
        into the database. A specific role is required to perform this service
        operation. Please contact the UDL team for assistance.

        Args:
          origin: Origin of the SensorMaintenance data.

          source: Source of the SensorMaintenance data.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/udl/sensormaintenance/createBulk",
            body=await async_maybe_transform(body, Iterable[sensor_maintenance_create_bulk_params.Body]),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "origin": origin,
                        "source": source,
                    },
                    sensor_maintenance_create_bulk_params.SensorMaintenanceCreateBulkParams,
                ),
            ),
            cast_to=NoneType,
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
    ) -> SensorMaintenanceGetResponse:
        """
        Service operation to get a single SensorMaintenance record by its unique ID
        passed as a path parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/udl/sensormaintenance/{id}",
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
                    sensor_maintenance_get_params.SensorMaintenanceGetParams,
                ),
            ),
            cast_to=SensorMaintenanceGetResponse,
        )

    def list_current(
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
    ) -> AsyncPaginator[SensorMaintenanceListCurrentResponse, AsyncOffsetPage[SensorMaintenanceListCurrentResponse]]:
        """
        Service operation to get current Sensor Maintenance records using any number of
        additional parameters.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/sensormaintenance/current",
            page=AsyncOffsetPage[SensorMaintenanceListCurrentResponse],
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
                    sensor_maintenance_list_current_params.SensorMaintenanceListCurrentParams,
                ),
            ),
            model=SensorMaintenanceListCurrentResponse,
        )

    async def query_help(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SensorMaintenanceQueryHelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return await self._get(
            "/udl/sensormaintenance/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SensorMaintenanceQueryHelpResponse,
        )

    async def tuple(
        self,
        *,
        columns: str,
        end_time: Union[str, datetime] | Omit = omit,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        start_time: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SensorMaintenanceTupleResponse:
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

          end_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              end time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          start_time: (One or more of fields 'endTime, startTime' are required.) The planned outage
              start time in ISO8601 UTC format. (YYYY-MM-DDTHH:MM:SS.ssssssZ)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/udl/sensormaintenance/tuple",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "columns": columns,
                        "end_time": end_time,
                        "first_result": first_result,
                        "max_results": max_results,
                        "start_time": start_time,
                    },
                    sensor_maintenance_tuple_params.SensorMaintenanceTupleParams,
                ),
            ),
            cast_to=SensorMaintenanceTupleResponse,
        )


class SensorMaintenanceResourceWithRawResponse:
    def __init__(self, sensor_maintenance: SensorMaintenanceResource) -> None:
        self._sensor_maintenance = sensor_maintenance

        self.create = to_raw_response_wrapper(
            sensor_maintenance.create,
        )
        self.update = to_raw_response_wrapper(
            sensor_maintenance.update,
        )
        self.list = to_raw_response_wrapper(
            sensor_maintenance.list,
        )
        self.delete = to_raw_response_wrapper(
            sensor_maintenance.delete,
        )
        self.count = to_raw_response_wrapper(
            sensor_maintenance.count,
        )
        self.create_bulk = to_raw_response_wrapper(
            sensor_maintenance.create_bulk,
        )
        self.get = to_raw_response_wrapper(
            sensor_maintenance.get,
        )
        self.list_current = to_raw_response_wrapper(
            sensor_maintenance.list_current,
        )
        self.query_help = to_raw_response_wrapper(
            sensor_maintenance.query_help,
        )
        self.tuple = to_raw_response_wrapper(
            sensor_maintenance.tuple,
        )

    @cached_property
    def history(self) -> HistoryResourceWithRawResponse:
        return HistoryResourceWithRawResponse(self._sensor_maintenance.history)


class AsyncSensorMaintenanceResourceWithRawResponse:
    def __init__(self, sensor_maintenance: AsyncSensorMaintenanceResource) -> None:
        self._sensor_maintenance = sensor_maintenance

        self.create = async_to_raw_response_wrapper(
            sensor_maintenance.create,
        )
        self.update = async_to_raw_response_wrapper(
            sensor_maintenance.update,
        )
        self.list = async_to_raw_response_wrapper(
            sensor_maintenance.list,
        )
        self.delete = async_to_raw_response_wrapper(
            sensor_maintenance.delete,
        )
        self.count = async_to_raw_response_wrapper(
            sensor_maintenance.count,
        )
        self.create_bulk = async_to_raw_response_wrapper(
            sensor_maintenance.create_bulk,
        )
        self.get = async_to_raw_response_wrapper(
            sensor_maintenance.get,
        )
        self.list_current = async_to_raw_response_wrapper(
            sensor_maintenance.list_current,
        )
        self.query_help = async_to_raw_response_wrapper(
            sensor_maintenance.query_help,
        )
        self.tuple = async_to_raw_response_wrapper(
            sensor_maintenance.tuple,
        )

    @cached_property
    def history(self) -> AsyncHistoryResourceWithRawResponse:
        return AsyncHistoryResourceWithRawResponse(self._sensor_maintenance.history)


class SensorMaintenanceResourceWithStreamingResponse:
    def __init__(self, sensor_maintenance: SensorMaintenanceResource) -> None:
        self._sensor_maintenance = sensor_maintenance

        self.create = to_streamed_response_wrapper(
            sensor_maintenance.create,
        )
        self.update = to_streamed_response_wrapper(
            sensor_maintenance.update,
        )
        self.list = to_streamed_response_wrapper(
            sensor_maintenance.list,
        )
        self.delete = to_streamed_response_wrapper(
            sensor_maintenance.delete,
        )
        self.count = to_streamed_response_wrapper(
            sensor_maintenance.count,
        )
        self.create_bulk = to_streamed_response_wrapper(
            sensor_maintenance.create_bulk,
        )
        self.get = to_streamed_response_wrapper(
            sensor_maintenance.get,
        )
        self.list_current = to_streamed_response_wrapper(
            sensor_maintenance.list_current,
        )
        self.query_help = to_streamed_response_wrapper(
            sensor_maintenance.query_help,
        )
        self.tuple = to_streamed_response_wrapper(
            sensor_maintenance.tuple,
        )

    @cached_property
    def history(self) -> HistoryResourceWithStreamingResponse:
        return HistoryResourceWithStreamingResponse(self._sensor_maintenance.history)


class AsyncSensorMaintenanceResourceWithStreamingResponse:
    def __init__(self, sensor_maintenance: AsyncSensorMaintenanceResource) -> None:
        self._sensor_maintenance = sensor_maintenance

        self.create = async_to_streamed_response_wrapper(
            sensor_maintenance.create,
        )
        self.update = async_to_streamed_response_wrapper(
            sensor_maintenance.update,
        )
        self.list = async_to_streamed_response_wrapper(
            sensor_maintenance.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            sensor_maintenance.delete,
        )
        self.count = async_to_streamed_response_wrapper(
            sensor_maintenance.count,
        )
        self.create_bulk = async_to_streamed_response_wrapper(
            sensor_maintenance.create_bulk,
        )
        self.get = async_to_streamed_response_wrapper(
            sensor_maintenance.get,
        )
        self.list_current = async_to_streamed_response_wrapper(
            sensor_maintenance.list_current,
        )
        self.query_help = async_to_streamed_response_wrapper(
            sensor_maintenance.query_help,
        )
        self.tuple = async_to_streamed_response_wrapper(
            sensor_maintenance.tuple,
        )

    @cached_property
    def history(self) -> AsyncHistoryResourceWithStreamingResponse:
        return AsyncHistoryResourceWithStreamingResponse(self._sensor_maintenance.history)
