# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ...types import (
    onorbit_get_params,
    onorbit_list_params,
    onorbit_count_params,
    onorbit_tuple_params,
    onorbit_create_params,
    onorbit_update_params,
    onorbit_get_signature_params,
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
from .antenna_details import (
    AntennaDetailsResource,
    AsyncAntennaDetailsResource,
    AntennaDetailsResourceWithRawResponse,
    AsyncAntennaDetailsResourceWithRawResponse,
    AntennaDetailsResourceWithStreamingResponse,
    AsyncAntennaDetailsResourceWithStreamingResponse,
)
from ...types.shared.onorbit_full import OnorbitFull
from ...types.onorbit_list_response import OnorbitListResponse
from ...types.onorbit_tuple_response import OnorbitTupleResponse
from ...types.onorbit_queryhelp_response import OnorbitQueryhelpResponse
from ...types.onorbit_get_signature_response import OnorbitGetSignatureResponse

__all__ = ["OnorbitResource", "AsyncOnorbitResource"]


class OnorbitResource(SyncAPIResource):
    @cached_property
    def antenna_details(self) -> AntennaDetailsResource:
        return AntennaDetailsResource(self._client)

    @cached_property
    def with_raw_response(self) -> OnorbitResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return OnorbitResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OnorbitResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return OnorbitResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        sat_no: int,
        source: str,
        alt_name: str | Omit = omit,
        category: Literal[
            "Unknown",
            "On-Orbit",
            "Decayed",
            "Cataloged Without State",
            "Launch Nominal",
            "Analyst Satellite",
            "Cislunar",
            "Lunar",
            "Hyperbolic",
            "Heliocentric",
            "Interplanetary",
            "Lagrangian",
            "Docked",
        ]
        | Omit = omit,
        common_name: str | Omit = omit,
        constellation: str | Omit = omit,
        country_code: str | Omit = omit,
        decay_date: Union[str, datetime] | Omit = omit,
        id_on_orbit: str | Omit = omit,
        intl_des: str | Omit = omit,
        launch_date: Union[str, date] | Omit = omit,
        launch_site_id: str | Omit = omit,
        lifetime_years: int | Omit = omit,
        mission_number: str | Omit = omit,
        object_type: Literal["ROCKET BODY", "DEBRIS", "PAYLOAD", "PLATFORM", "MANNED", "UNKNOWN"] | Omit = omit,
        origin: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take a single onorbit object as a POST body and ingest into
        the database. A specific role is required to perform this service operation.
        Please contact the UDL team for assistance.

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

          sat_no: Satellite/Catalog number of the target on-orbit object.

          source: Source of the data.

          alt_name: Alternate name of the on-orbit object.

          category: Category of the on-orbit object. (Unknown, On-Orbit, Decayed, Cataloged Without
              State, Launch Nominal, Analyst Satellite, Cislunar, Lunar, Hyperbolic,
              Heliocentric, Interplanetary, Lagrangian, Docked).

          common_name: Common name of the on-orbit object.

          constellation: Constellation to which this satellite belongs.

          country_code: The country code. This value is typically the ISO 3166 Alpha-2 two-character
              country code, however it can also represent various consortiums that do not
              appear in the ISO document. The code must correspond to an existing country in
              the UDL’s country API. Call udl/country/{code} to get any associated FIPS code,
              ISO Alpha-3 code, or alternate code values that exist for the specified country
              code.

          decay_date: Date of decay.

          id_on_orbit: For the public catalog, the idOnOrbit is typically the satellite number as a
              string, but may be a UUID for analyst or other unknown or untracked satellites,
              auto-generated by the system.

          intl_des: International Designator, typically of the format YYYYLLLAAA, where YYYY is the
              launch year, LLL is the sequential launch number of that year, and AAA is an
              optional launch piece designator for the launch.

          launch_date: Date of launch.

          launch_site_id: Id of the associated launchSite entity.

          lifetime_years: Estimated lifetime of the on-orbit payload, if known.

          mission_number: Mission number of the on-orbit object.

          object_type: Type of on-orbit object: ROCKET BODY, DEBRIS, PAYLOAD, PLATFORM, MANNED,
              UNKNOWN.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/udl/onorbit",
            body=maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "sat_no": sat_no,
                    "source": source,
                    "alt_name": alt_name,
                    "category": category,
                    "common_name": common_name,
                    "constellation": constellation,
                    "country_code": country_code,
                    "decay_date": decay_date,
                    "id_on_orbit": id_on_orbit,
                    "intl_des": intl_des,
                    "launch_date": launch_date,
                    "launch_site_id": launch_site_id,
                    "lifetime_years": lifetime_years,
                    "mission_number": mission_number,
                    "object_type": object_type,
                    "origin": origin,
                },
                onorbit_create_params.OnorbitCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update(
        self,
        id: str,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        sat_no: int,
        source: str,
        alt_name: str | Omit = omit,
        category: Literal[
            "Unknown",
            "On-Orbit",
            "Decayed",
            "Cataloged Without State",
            "Launch Nominal",
            "Analyst Satellite",
            "Cislunar",
            "Lunar",
            "Hyperbolic",
            "Heliocentric",
            "Interplanetary",
            "Lagrangian",
            "Docked",
        ]
        | Omit = omit,
        common_name: str | Omit = omit,
        constellation: str | Omit = omit,
        country_code: str | Omit = omit,
        decay_date: Union[str, datetime] | Omit = omit,
        id_on_orbit: str | Omit = omit,
        intl_des: str | Omit = omit,
        launch_date: Union[str, date] | Omit = omit,
        launch_site_id: str | Omit = omit,
        lifetime_years: int | Omit = omit,
        mission_number: str | Omit = omit,
        object_type: Literal["ROCKET BODY", "DEBRIS", "PAYLOAD", "PLATFORM", "MANNED", "UNKNOWN"] | Omit = omit,
        origin: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Service operation to update a single OnOrbit object.

        A specific role is required
        to perform this service operation. Please contact the UDL team for assistance.

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

          sat_no: Satellite/Catalog number of the target on-orbit object.

          source: Source of the data.

          alt_name: Alternate name of the on-orbit object.

          category: Category of the on-orbit object. (Unknown, On-Orbit, Decayed, Cataloged Without
              State, Launch Nominal, Analyst Satellite, Cislunar, Lunar, Hyperbolic,
              Heliocentric, Interplanetary, Lagrangian, Docked).

          common_name: Common name of the on-orbit object.

          constellation: Constellation to which this satellite belongs.

          country_code: The country code. This value is typically the ISO 3166 Alpha-2 two-character
              country code, however it can also represent various consortiums that do not
              appear in the ISO document. The code must correspond to an existing country in
              the UDL’s country API. Call udl/country/{code} to get any associated FIPS code,
              ISO Alpha-3 code, or alternate code values that exist for the specified country
              code.

          decay_date: Date of decay.

          id_on_orbit: For the public catalog, the idOnOrbit is typically the satellite number as a
              string, but may be a UUID for analyst or other unknown or untracked satellites,
              auto-generated by the system.

          intl_des: International Designator, typically of the format YYYYLLLAAA, where YYYY is the
              launch year, LLL is the sequential launch number of that year, and AAA is an
              optional launch piece designator for the launch.

          launch_date: Date of launch.

          launch_site_id: Id of the associated launchSite entity.

          lifetime_years: Estimated lifetime of the on-orbit payload, if known.

          mission_number: Mission number of the on-orbit object.

          object_type: Type of on-orbit object: ROCKET BODY, DEBRIS, PAYLOAD, PLATFORM, MANNED,
              UNKNOWN.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/udl/onorbit/{id}",
            body=maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "sat_no": sat_no,
                    "source": source,
                    "alt_name": alt_name,
                    "category": category,
                    "common_name": common_name,
                    "constellation": constellation,
                    "country_code": country_code,
                    "decay_date": decay_date,
                    "id_on_orbit": id_on_orbit,
                    "intl_des": intl_des,
                    "launch_date": launch_date,
                    "launch_site_id": launch_site_id,
                    "lifetime_years": lifetime_years,
                    "mission_number": mission_number,
                    "object_type": object_type,
                    "origin": origin,
                },
                onorbit_update_params.OnorbitUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

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
    ) -> SyncOffsetPage[OnorbitListResponse]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/onorbit",
            page=SyncOffsetPage[OnorbitListResponse],
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
                    onorbit_list_params.OnorbitListParams,
                ),
            ),
            model=OnorbitListResponse,
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
        Service operation to delete an OnOrbit object specified by the passed ID path
        parameter. A specific role is required to perform this service operation. Please
        contact the UDL team for assistance.

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
            f"/udl/onorbit/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def count(
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
    ) -> str:
        """
        Service operation to return the count of records satisfying the specified query
        parameters. This operation is useful to determine how many records pass a
        particular query criteria without retrieving large amounts of data. See the
        queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on
        valid/required query parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return self._get(
            "/udl/onorbit/count",
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
                    onorbit_count_params.OnorbitCountParams,
                ),
            ),
            cast_to=str,
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
    ) -> OnorbitFull:
        """
        Service operation to get a single OnOrbit object by its unique ID passed as a
        path parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/udl/onorbit/{id}",
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
                    onorbit_get_params.OnorbitGetParams,
                ),
            ),
            cast_to=OnorbitFull,
        )

    def get_signature(
        self,
        *,
        id_on_orbit: str,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnorbitGetSignatureResponse:
        """
        This service queries common information across Radar, EO, and RF observations.

        Args:
          id_on_orbit: ID of the Onorbit object.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/udl/onorbit/getSignature",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "id_on_orbit": id_on_orbit,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    onorbit_get_signature_params.OnorbitGetSignatureParams,
                ),
            ),
            cast_to=OnorbitGetSignatureResponse,
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
    ) -> OnorbitQueryhelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return self._get(
            "/udl/onorbit/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OnorbitQueryhelpResponse,
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
    ) -> OnorbitTupleResponse:
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

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/udl/onorbit/tuple",
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
                    onorbit_tuple_params.OnorbitTupleParams,
                ),
            ),
            cast_to=OnorbitTupleResponse,
        )


class AsyncOnorbitResource(AsyncAPIResource):
    @cached_property
    def antenna_details(self) -> AsyncAntennaDetailsResource:
        return AsyncAntennaDetailsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncOnorbitResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncOnorbitResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOnorbitResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Bluestaq/udl-python-sdk#with_streaming_response
        """
        return AsyncOnorbitResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        sat_no: int,
        source: str,
        alt_name: str | Omit = omit,
        category: Literal[
            "Unknown",
            "On-Orbit",
            "Decayed",
            "Cataloged Without State",
            "Launch Nominal",
            "Analyst Satellite",
            "Cislunar",
            "Lunar",
            "Hyperbolic",
            "Heliocentric",
            "Interplanetary",
            "Lagrangian",
            "Docked",
        ]
        | Omit = omit,
        common_name: str | Omit = omit,
        constellation: str | Omit = omit,
        country_code: str | Omit = omit,
        decay_date: Union[str, datetime] | Omit = omit,
        id_on_orbit: str | Omit = omit,
        intl_des: str | Omit = omit,
        launch_date: Union[str, date] | Omit = omit,
        launch_site_id: str | Omit = omit,
        lifetime_years: int | Omit = omit,
        mission_number: str | Omit = omit,
        object_type: Literal["ROCKET BODY", "DEBRIS", "PAYLOAD", "PLATFORM", "MANNED", "UNKNOWN"] | Omit = omit,
        origin: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Service operation to take a single onorbit object as a POST body and ingest into
        the database. A specific role is required to perform this service operation.
        Please contact the UDL team for assistance.

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

          sat_no: Satellite/Catalog number of the target on-orbit object.

          source: Source of the data.

          alt_name: Alternate name of the on-orbit object.

          category: Category of the on-orbit object. (Unknown, On-Orbit, Decayed, Cataloged Without
              State, Launch Nominal, Analyst Satellite, Cislunar, Lunar, Hyperbolic,
              Heliocentric, Interplanetary, Lagrangian, Docked).

          common_name: Common name of the on-orbit object.

          constellation: Constellation to which this satellite belongs.

          country_code: The country code. This value is typically the ISO 3166 Alpha-2 two-character
              country code, however it can also represent various consortiums that do not
              appear in the ISO document. The code must correspond to an existing country in
              the UDL’s country API. Call udl/country/{code} to get any associated FIPS code,
              ISO Alpha-3 code, or alternate code values that exist for the specified country
              code.

          decay_date: Date of decay.

          id_on_orbit: For the public catalog, the idOnOrbit is typically the satellite number as a
              string, but may be a UUID for analyst or other unknown or untracked satellites,
              auto-generated by the system.

          intl_des: International Designator, typically of the format YYYYLLLAAA, where YYYY is the
              launch year, LLL is the sequential launch number of that year, and AAA is an
              optional launch piece designator for the launch.

          launch_date: Date of launch.

          launch_site_id: Id of the associated launchSite entity.

          lifetime_years: Estimated lifetime of the on-orbit payload, if known.

          mission_number: Mission number of the on-orbit object.

          object_type: Type of on-orbit object: ROCKET BODY, DEBRIS, PAYLOAD, PLATFORM, MANNED,
              UNKNOWN.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/udl/onorbit",
            body=await async_maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "sat_no": sat_no,
                    "source": source,
                    "alt_name": alt_name,
                    "category": category,
                    "common_name": common_name,
                    "constellation": constellation,
                    "country_code": country_code,
                    "decay_date": decay_date,
                    "id_on_orbit": id_on_orbit,
                    "intl_des": intl_des,
                    "launch_date": launch_date,
                    "launch_site_id": launch_site_id,
                    "lifetime_years": lifetime_years,
                    "mission_number": mission_number,
                    "object_type": object_type,
                    "origin": origin,
                },
                onorbit_create_params.OnorbitCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update(
        self,
        id: str,
        *,
        classification_marking: str,
        data_mode: Literal["REAL", "TEST", "SIMULATED", "EXERCISE"],
        sat_no: int,
        source: str,
        alt_name: str | Omit = omit,
        category: Literal[
            "Unknown",
            "On-Orbit",
            "Decayed",
            "Cataloged Without State",
            "Launch Nominal",
            "Analyst Satellite",
            "Cislunar",
            "Lunar",
            "Hyperbolic",
            "Heliocentric",
            "Interplanetary",
            "Lagrangian",
            "Docked",
        ]
        | Omit = omit,
        common_name: str | Omit = omit,
        constellation: str | Omit = omit,
        country_code: str | Omit = omit,
        decay_date: Union[str, datetime] | Omit = omit,
        id_on_orbit: str | Omit = omit,
        intl_des: str | Omit = omit,
        launch_date: Union[str, date] | Omit = omit,
        launch_site_id: str | Omit = omit,
        lifetime_years: int | Omit = omit,
        mission_number: str | Omit = omit,
        object_type: Literal["ROCKET BODY", "DEBRIS", "PAYLOAD", "PLATFORM", "MANNED", "UNKNOWN"] | Omit = omit,
        origin: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Service operation to update a single OnOrbit object.

        A specific role is required
        to perform this service operation. Please contact the UDL team for assistance.

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

          sat_no: Satellite/Catalog number of the target on-orbit object.

          source: Source of the data.

          alt_name: Alternate name of the on-orbit object.

          category: Category of the on-orbit object. (Unknown, On-Orbit, Decayed, Cataloged Without
              State, Launch Nominal, Analyst Satellite, Cislunar, Lunar, Hyperbolic,
              Heliocentric, Interplanetary, Lagrangian, Docked).

          common_name: Common name of the on-orbit object.

          constellation: Constellation to which this satellite belongs.

          country_code: The country code. This value is typically the ISO 3166 Alpha-2 two-character
              country code, however it can also represent various consortiums that do not
              appear in the ISO document. The code must correspond to an existing country in
              the UDL’s country API. Call udl/country/{code} to get any associated FIPS code,
              ISO Alpha-3 code, or alternate code values that exist for the specified country
              code.

          decay_date: Date of decay.

          id_on_orbit: For the public catalog, the idOnOrbit is typically the satellite number as a
              string, but may be a UUID for analyst or other unknown or untracked satellites,
              auto-generated by the system.

          intl_des: International Designator, typically of the format YYYYLLLAAA, where YYYY is the
              launch year, LLL is the sequential launch number of that year, and AAA is an
              optional launch piece designator for the launch.

          launch_date: Date of launch.

          launch_site_id: Id of the associated launchSite entity.

          lifetime_years: Estimated lifetime of the on-orbit payload, if known.

          mission_number: Mission number of the on-orbit object.

          object_type: Type of on-orbit object: ROCKET BODY, DEBRIS, PAYLOAD, PLATFORM, MANNED,
              UNKNOWN.

          origin: Originating system or organization which produced the data, if different from
              the source. The origin may be different than the source if the source was a
              mediating system which forwarded the data on behalf of the origin system. If
              null, the source may be assumed to be the origin.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/udl/onorbit/{id}",
            body=await async_maybe_transform(
                {
                    "classification_marking": classification_marking,
                    "data_mode": data_mode,
                    "sat_no": sat_no,
                    "source": source,
                    "alt_name": alt_name,
                    "category": category,
                    "common_name": common_name,
                    "constellation": constellation,
                    "country_code": country_code,
                    "decay_date": decay_date,
                    "id_on_orbit": id_on_orbit,
                    "intl_des": intl_des,
                    "launch_date": launch_date,
                    "launch_site_id": launch_site_id,
                    "lifetime_years": lifetime_years,
                    "mission_number": mission_number,
                    "object_type": object_type,
                    "origin": origin,
                },
                onorbit_update_params.OnorbitUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

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
    ) -> AsyncPaginator[OnorbitListResponse, AsyncOffsetPage[OnorbitListResponse]]:
        """
        Service operation to dynamically query data by a variety of query parameters not
        specified in this API documentation. See the queryhelp operation
        (/udl/&lt;datatype&gt;/queryhelp) for more details on valid/required query
        parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/udl/onorbit",
            page=AsyncOffsetPage[OnorbitListResponse],
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
                    onorbit_list_params.OnorbitListParams,
                ),
            ),
            model=OnorbitListResponse,
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
        Service operation to delete an OnOrbit object specified by the passed ID path
        parameter. A specific role is required to perform this service operation. Please
        contact the UDL team for assistance.

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
            f"/udl/onorbit/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def count(
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
    ) -> str:
        """
        Service operation to return the count of records satisfying the specified query
        parameters. This operation is useful to determine how many records pass a
        particular query criteria without retrieving large amounts of data. See the
        queryhelp operation (/udl/&lt;datatype&gt;/queryhelp) for more details on
        valid/required query parameter information.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return await self._get(
            "/udl/onorbit/count",
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
                    onorbit_count_params.OnorbitCountParams,
                ),
            ),
            cast_to=str,
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
    ) -> OnorbitFull:
        """
        Service operation to get a single OnOrbit object by its unique ID passed as a
        path parameter.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/udl/onorbit/{id}",
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
                    onorbit_get_params.OnorbitGetParams,
                ),
            ),
            cast_to=OnorbitFull,
        )

    async def get_signature(
        self,
        *,
        id_on_orbit: str,
        first_result: int | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnorbitGetSignatureResponse:
        """
        This service queries common information across Radar, EO, and RF observations.

        Args:
          id_on_orbit: ID of the Onorbit object.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/udl/onorbit/getSignature",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "id_on_orbit": id_on_orbit,
                        "first_result": first_result,
                        "max_results": max_results,
                    },
                    onorbit_get_signature_params.OnorbitGetSignatureParams,
                ),
            ),
            cast_to=OnorbitGetSignatureResponse,
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
    ) -> OnorbitQueryhelpResponse:
        """
        Service operation to provide detailed information on available dynamic query
        parameters for a particular data type.
        """
        return await self._get(
            "/udl/onorbit/queryhelp",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OnorbitQueryhelpResponse,
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
    ) -> OnorbitTupleResponse:
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

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/udl/onorbit/tuple",
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
                    onorbit_tuple_params.OnorbitTupleParams,
                ),
            ),
            cast_to=OnorbitTupleResponse,
        )


class OnorbitResourceWithRawResponse:
    def __init__(self, onorbit: OnorbitResource) -> None:
        self._onorbit = onorbit

        self.create = to_raw_response_wrapper(
            onorbit.create,
        )
        self.update = to_raw_response_wrapper(
            onorbit.update,
        )
        self.list = to_raw_response_wrapper(
            onorbit.list,
        )
        self.delete = to_raw_response_wrapper(
            onorbit.delete,
        )
        self.count = to_raw_response_wrapper(
            onorbit.count,
        )
        self.get = to_raw_response_wrapper(
            onorbit.get,
        )
        self.get_signature = to_raw_response_wrapper(
            onorbit.get_signature,
        )
        self.queryhelp = to_raw_response_wrapper(
            onorbit.queryhelp,
        )
        self.tuple = to_raw_response_wrapper(
            onorbit.tuple,
        )

    @cached_property
    def antenna_details(self) -> AntennaDetailsResourceWithRawResponse:
        return AntennaDetailsResourceWithRawResponse(self._onorbit.antenna_details)


class AsyncOnorbitResourceWithRawResponse:
    def __init__(self, onorbit: AsyncOnorbitResource) -> None:
        self._onorbit = onorbit

        self.create = async_to_raw_response_wrapper(
            onorbit.create,
        )
        self.update = async_to_raw_response_wrapper(
            onorbit.update,
        )
        self.list = async_to_raw_response_wrapper(
            onorbit.list,
        )
        self.delete = async_to_raw_response_wrapper(
            onorbit.delete,
        )
        self.count = async_to_raw_response_wrapper(
            onorbit.count,
        )
        self.get = async_to_raw_response_wrapper(
            onorbit.get,
        )
        self.get_signature = async_to_raw_response_wrapper(
            onorbit.get_signature,
        )
        self.queryhelp = async_to_raw_response_wrapper(
            onorbit.queryhelp,
        )
        self.tuple = async_to_raw_response_wrapper(
            onorbit.tuple,
        )

    @cached_property
    def antenna_details(self) -> AsyncAntennaDetailsResourceWithRawResponse:
        return AsyncAntennaDetailsResourceWithRawResponse(self._onorbit.antenna_details)


class OnorbitResourceWithStreamingResponse:
    def __init__(self, onorbit: OnorbitResource) -> None:
        self._onorbit = onorbit

        self.create = to_streamed_response_wrapper(
            onorbit.create,
        )
        self.update = to_streamed_response_wrapper(
            onorbit.update,
        )
        self.list = to_streamed_response_wrapper(
            onorbit.list,
        )
        self.delete = to_streamed_response_wrapper(
            onorbit.delete,
        )
        self.count = to_streamed_response_wrapper(
            onorbit.count,
        )
        self.get = to_streamed_response_wrapper(
            onorbit.get,
        )
        self.get_signature = to_streamed_response_wrapper(
            onorbit.get_signature,
        )
        self.queryhelp = to_streamed_response_wrapper(
            onorbit.queryhelp,
        )
        self.tuple = to_streamed_response_wrapper(
            onorbit.tuple,
        )

    @cached_property
    def antenna_details(self) -> AntennaDetailsResourceWithStreamingResponse:
        return AntennaDetailsResourceWithStreamingResponse(self._onorbit.antenna_details)


class AsyncOnorbitResourceWithStreamingResponse:
    def __init__(self, onorbit: AsyncOnorbitResource) -> None:
        self._onorbit = onorbit

        self.create = async_to_streamed_response_wrapper(
            onorbit.create,
        )
        self.update = async_to_streamed_response_wrapper(
            onorbit.update,
        )
        self.list = async_to_streamed_response_wrapper(
            onorbit.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            onorbit.delete,
        )
        self.count = async_to_streamed_response_wrapper(
            onorbit.count,
        )
        self.get = async_to_streamed_response_wrapper(
            onorbit.get,
        )
        self.get_signature = async_to_streamed_response_wrapper(
            onorbit.get_signature,
        )
        self.queryhelp = async_to_streamed_response_wrapper(
            onorbit.queryhelp,
        )
        self.tuple = async_to_streamed_response_wrapper(
            onorbit.tuple,
        )

    @cached_property
    def antenna_details(self) -> AsyncAntennaDetailsResourceWithStreamingResponse:
        return AsyncAntennaDetailsResourceWithStreamingResponse(self._onorbit.antenna_details)
