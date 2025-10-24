# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AttitudeSetTupleParams"]


class AttitudeSetTupleParams(TypedDict, total=False):
    columns: Required[str]
    """
    Comma-separated list of valid field names for this data type to be returned in
    the response. Only the fields specified will be returned as well as the
    classification marking of the data, if applicable. See the ‘queryhelp’ operation
    for a complete list of possible fields.
    """

    start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startTime", format="iso8601")]]
    """
    The epoch or start time of the attitude parameter or attitude ephemeris, in ISO
    8601 UTC format, with microsecond precision. If this set is constituted by a
    single attitude parameter message then startTime is the epoch.
    (YYYY-MM-DDTHH:MM:SS.ssssssZ)
    """

    first_result: Annotated[int, PropertyInfo(alias="firstResult")]

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
