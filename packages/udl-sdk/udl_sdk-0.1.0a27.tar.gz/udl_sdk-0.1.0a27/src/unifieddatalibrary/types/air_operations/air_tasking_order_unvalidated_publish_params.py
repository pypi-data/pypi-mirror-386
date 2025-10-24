# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = [
    "AirTaskingOrderUnvalidatedPublishParams",
    "Body",
    "BodyAcMsnTasking",
    "BodyAcMsnTaskingAcMsnLocSeg",
    "BodyAcMsnTaskingIndAcTasking",
    "BodyGenText",
    "BodyNavalFltOp",
]


class AirTaskingOrderUnvalidatedPublishParams(TypedDict, total=False):
    body: Required[Iterable[Body]]


class BodyAcMsnTaskingAcMsnLocSeg(TypedDict, total=False):
    start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startTime", format="iso8601")]]
    """
    The start time of this mission in ISO 8601 UTC format with millisecond
    precision.
    """

    air_msn_pri: Annotated[str, PropertyInfo(alias="airMsnPri")]
    """The code for the priority assigned to this mission."""

    alt: int
    """The altitude for this mission represented as hundreds of feet above MSL."""

    area_geo_rad: Annotated[int, PropertyInfo(alias="areaGeoRad")]
    """The radius of the circle around the location being reported in feet."""

    end_time: Annotated[Union[str, datetime], PropertyInfo(alias="endTime", format="iso8601")]
    """The end time of this mission in ISO 8601 UTC format with millisecond precision."""

    msn_loc_name: Annotated[str, PropertyInfo(alias="msnLocName")]
    """The name that identifies the location at which this mission is to be performed.

    This can be the name of a general target area, orbit, cap point, station, etc.
    """

    msn_loc_pt_bar_t: Annotated[str, PropertyInfo(alias="msnLocPtBarT")]
    """
    The alpha-numeric specified location for this mission specified as a bearing
    angle in degrees relative to true north and a range in nautical miles (NM).
    """

    msn_loc_pt_lat: Annotated[float, PropertyInfo(alias="msnLocPtLat")]
    """WGS-84 latitude of the mission location, in degrees.

    -90 to 90 degrees (negative values south of equator) for this tasked air
    mission.
    """

    msn_loc_pt_lon: Annotated[float, PropertyInfo(alias="msnLocPtLon")]
    """WGS-84 longitude of the mission location, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian) for this tasked air
    mission.
    """

    msn_loc_pt_name: Annotated[str, PropertyInfo(alias="msnLocPtName")]
    """The location name for this mission."""


class BodyAcMsnTaskingIndAcTasking(TypedDict, total=False):
    acft_type: Required[Annotated[str, PropertyInfo(alias="acftType")]]
    """The type and model number for the aircraft.

    The field may specify a value of an aircraft not yet assigned an aircraft code
    contained in the aircraft codes list.
    """

    call_sign: Annotated[str, PropertyInfo(alias="callSign")]
    """The call sign assigned to this mission aircraft."""

    iff_sif_mode1_code: Annotated[str, PropertyInfo(alias="iffSifMode1Code")]
    """
    The mode 1 and code of the Identification Friend or FOE (IFF) or Selective
    Identification Feature (SIF).
    """

    iff_sif_mode2_code: Annotated[str, PropertyInfo(alias="iffSifMode2Code")]
    """
    The mode 2 and code of the Identification Friend or FOE (IFF) or Selective
    Identification Feature (SIF).
    """

    iff_sif_mode3_code: Annotated[str, PropertyInfo(alias="iffSifMode3Code")]
    """
    The mode 3 and code of the Identification Friend or FOE (IFF) or Selective
    Identification Feature (SIF).
    """

    ju_address: Annotated[Iterable[int], PropertyInfo(alias="juAddress")]
    """
    An optional array of link 16 octal track numbers assigned as the primary JTIDS
    Unit (JU) address for the mission aircraft.
    """

    link16_call_sign: Annotated[str, PropertyInfo(alias="link16CallSign")]
    """The Link 16 abbreviated call sign assigned to the ACA.

    This is normally the first and last letter and the last two numbers of the call
    sign.
    """

    num_acft: Annotated[int, PropertyInfo(alias="numAcft")]
    """The number of aircraft participating in this mission."""

    pri_config_code: Annotated[str, PropertyInfo(alias="priConfigCode")]
    """The code that indicates the ordinance mix carried on this mission aircraft."""

    sec_config_code: Annotated[str, PropertyInfo(alias="secConfigCode")]
    """The code for the secondary ordinance mix carried on this mission aircraft."""

    tacan_chan: Annotated[int, PropertyInfo(alias="tacanChan")]
    """The TACAN channel assigned to this mission aircraft."""


class BodyAcMsnTasking(TypedDict, total=False):
    country_code: Required[Annotated[str, PropertyInfo(alias="countryCode")]]
    """
    The country code responsible for conducting this aircraft mission tasking for
    the exercise or operation.
    """

    tasked_service: Required[Annotated[str, PropertyInfo(alias="taskedService")]]
    """
    The service tasked with conducting this aircraft mission tasking for the
    exercise or operation.
    """

    unit_designator: Required[Annotated[str, PropertyInfo(alias="unitDesignator")]]
    """
    The designator of the unit that is tasked to perform this aircraft mission
    tasking.
    """

    ac_msn_loc_seg: Annotated[Iterable[BodyAcMsnTaskingAcMsnLocSeg], PropertyInfo(alias="acMsnLocSeg")]
    """
    A collection of aircraft mission location information for this aircraft mission
    tasking.
    """

    alert_status: Annotated[int, PropertyInfo(alias="alertStatus")]
    """
    The readiness status expressed in time (minutes) for an aircraft to be airborne
    after the launch order is received or the time required for a missile unit to
    assume battle stations.
    """

    amc_msn_num: Annotated[str, PropertyInfo(alias="amcMsnNum")]
    """The AMC number assigned to identify one aircraft from another."""

    dep_loc_lat: Annotated[float, PropertyInfo(alias="depLocLat")]
    """WGS-84 latitude of the departure location, in degrees.

    -90 to 90 degrees (negative values south of equator) for this tasked air
    mission.
    """

    dep_loc_lon: Annotated[float, PropertyInfo(alias="depLocLon")]
    """WGS-84 longitude of the departure location, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian) for this tasked air
    mission.
    """

    dep_loc_name: Annotated[str, PropertyInfo(alias="depLocName")]
    """The location or name specified for the departure of the tasked air mission."""

    dep_loc_utm: Annotated[str, PropertyInfo(alias="depLocUTM")]
    """
    The departure location specified in UTM (100 meter) coordinates for the tasked
    air mission.
    """

    dep_time: Annotated[Union[str, datetime], PropertyInfo(alias="depTime", format="iso8601")]
    """
    The time of departure for the tasked air mission in ISO8601 UTC format with
    millisecond precision.
    """

    ind_ac_tasking: Annotated[Iterable[BodyAcMsnTaskingIndAcTasking], PropertyInfo(alias="indACTasking")]
    """
    A collection of the individual aircraft assigned to this aircraft mission
    tasking.
    """

    msn_commander: Annotated[str, PropertyInfo(alias="msnCommander")]
    """
    The commander responsible for the planning and execution of the forces necessary
    to achieve desired objectives.
    """

    msn_num: Annotated[str, PropertyInfo(alias="msnNum")]
    """The mission number assigned to this mission."""

    pkg_id: Annotated[str, PropertyInfo(alias="pkgId")]
    """The identifier for the composite set of missions for this operation/exercise."""

    pri_msn_type: Annotated[str, PropertyInfo(alias="priMsnType")]
    """The code for the preferred type or designator for a tasked air mission."""

    rcvy_loc_lat: Annotated[Iterable[float], PropertyInfo(alias="rcvyLocLat")]
    """An array of WGS-84 latitude of the recovery locations, in degrees.

    -90 to 90 degrees (negative values south of equator) for this tasked air
    mission.
    """

    rcvy_loc_lon: Annotated[Iterable[float], PropertyInfo(alias="rcvyLocLon")]
    """An array of WGS-84 longitude of the recovery locations, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian) for this tasked air
    mission.
    """

    rcvy_loc_name: Annotated[SequenceNotStr[str], PropertyInfo(alias="rcvyLocName")]
    """
    An array of locations specified for the recovery of the tasked air mission
    represented by varying formats.
    """

    rcvy_loc_utm: Annotated[SequenceNotStr[str], PropertyInfo(alias="rcvyLocUTM")]
    """
    An array of recovery locations specified in UTM (100 meter) coordinates for the
    tasked air mission.
    """

    rcvy_time: Annotated[SequenceNotStr[Union[str, datetime]], PropertyInfo(alias="rcvyTime", format="iso8601")]
    """
    An array of recovery times for the tasked air mission in ISO8601 UTC format with
    millisecond precision.
    """

    res_msn_ind: Annotated[str, PropertyInfo(alias="resMsnInd")]
    """An indicator of whether a mission is or will be a residual mission."""

    sec_msn_type: Annotated[str, PropertyInfo(alias="secMsnType")]
    """The code for the alternative type of a tasked air mission."""

    unit_loc_name: Annotated[str, PropertyInfo(alias="unitLocName")]
    """The tasked units location expressed as an ICAO or a place name."""


class BodyGenText(TypedDict, total=False):
    text: str
    """The free text that describes the information specific to the text indicator."""

    text_ind: Annotated[str, PropertyInfo(alias="textInd")]
    """The indicator for the general text block.

    Examples include "OPENING REMARKS" and "GENERAL SPINS INFORMATION".
    """


class BodyNavalFltOp(TypedDict, total=False):
    ship_name: Required[Annotated[str, PropertyInfo(alias="shipName")]]
    """The name of a ship or maritime vessel. Specify UNKNOWN if name is not known."""

    flt_op_start: Annotated[Union[str, datetime], PropertyInfo(alias="fltOpStart", format="iso8601")]
    """
    The time when flight operations begin in ISO8601 UTC format with millisecond
    precision.
    """

    flt_op_stop: Annotated[Union[str, datetime], PropertyInfo(alias="fltOpStop", format="iso8601")]
    """
    The time when flight operations end in ISO8601 UTC format with millisecond
    precision.
    """

    schd_launch_rcvy_time: Annotated[
        SequenceNotStr[Union[str, datetime]], PropertyInfo(alias="schdLaunchRcvyTime", format="iso8601")
    ]
    """
    An array of times at which an aircraft will be launched and/or recovered in
    ISO8601 UTC format with millisecond precision.
    """


class Body(TypedDict, total=False):
    begin_ts: Required[Annotated[Union[str, datetime], PropertyInfo(alias="beginTs", format="iso8601")]]
    """
    The effective begin time for this ATO in ISO 8601 UTC format with millisecond
    precision.
    """

    classification_marking: Required[Annotated[str, PropertyInfo(alias="classificationMarking")]]
    """Classification marking of the data in IC/CAPCO Portion-marked format."""

    data_mode: Required[Annotated[Literal["REAL", "TEST", "SIMULATED", "EXERCISE"], PropertyInfo(alias="dataMode")]]
    """Indicator of whether the data is EXERCISE, REAL, SIMULATED, or TEST data:

    EXERCISE:&nbsp;Data pertaining to a government or military exercise. The data
    may include both real and simulated data.

    REAL:&nbsp;Data collected or produced that pertains to real-world objects,
    events, and analysis.

    SIMULATED:&nbsp;Synthetic data generated by a model to mimic real-world
    datasets.

    TEST:&nbsp;Specific datasets used to evaluate compliance with specifications and
    requirements, and for validating technical, functional, and performance
    characteristics.
    """

    op_exer_name: Required[Annotated[str, PropertyInfo(alias="opExerName")]]
    """
    Specifies the unique operation or exercise name, nickname, or codeword assigned
    to a joint exercise or operation plan.
    """

    source: Required[str]
    """Source of the data."""

    id: str
    """Unique identifier of the record, auto-generated by the system."""

    ack_req_ind: Annotated[str, PropertyInfo(alias="ackReqInd")]
    """
    The indicator specifying an affirmative or a negatice condition for this
    message.
    """

    ack_unit_instructions: Annotated[str, PropertyInfo(alias="ackUnitInstructions")]
    """
    Specifies textual data amplifying the data contained in the acknowledgement
    requirement indicator (ackRedInd) field or the unit required to acknowledge.
    """

    ac_msn_tasking: Annotated[Iterable[BodyAcMsnTasking], PropertyInfo(alias="acMsnTasking")]
    """
    A collection that specifies the tasked country, tasked service, unit and mission
    level tasking for this ATO.
    """

    end_ts: Annotated[Union[str, datetime], PropertyInfo(alias="endTs", format="iso8601")]
    """
    The effective end time for this ATO in ISO 8601 UTC format with millisecond
    precision.
    """

    gen_text: Annotated[Iterable[BodyGenText], PropertyInfo(alias="genText")]
    """
    A collection that details special instructions, important information, guidance,
    and amplifying information regarding this ATO.
    """

    msg_month: Annotated[str, PropertyInfo(alias="msgMonth")]
    """The month in which the message originated."""

    msg_originator: Annotated[str, PropertyInfo(alias="msgOriginator")]
    """The identifier of the originator of the message."""

    msg_qualifier: Annotated[str, PropertyInfo(alias="msgQualifier")]
    """The qualifier which caveats the message status."""

    msg_sn: Annotated[str, PropertyInfo(alias="msgSN")]
    """The unique message identifier sequentially assigned by the originator."""

    naval_flt_ops: Annotated[Iterable[BodyNavalFltOp], PropertyInfo(alias="navalFltOps")]
    """A collection that specifies the naval flight operations for this ATO."""

    origin: str
    """
    Originating system or organization which produced the data, if different from
    the source. The origin may be different than the source if the source was a
    mediating system which forwarded the data on behalf of the origin system. If
    null, the source may be assumed to be the origin.
    """
