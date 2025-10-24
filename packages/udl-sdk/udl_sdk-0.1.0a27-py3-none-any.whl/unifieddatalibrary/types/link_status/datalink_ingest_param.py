# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = [
    "DatalinkIngestParam",
    "MultiDuty",
    "MultiDutyMultiDutyVoiceCoord",
    "Op",
    "Reference",
    "RefPoint",
    "Remark",
    "SpecTrack",
    "VoiceCoord",
]


class MultiDutyMultiDutyVoiceCoord(TypedDict, total=False):
    multi_comm_pri: Annotated[str, PropertyInfo(alias="multiCommPri")]
    """
    Priority of a communication circuit, channel or frequency for multilink
    coordination (e.g. P - Primary, M - Monitor).
    """

    multi_freq_des: Annotated[str, PropertyInfo(alias="multiFreqDes")]
    """
    Designator used in nonsecure communications to refer to a radio frequency for
    multilink coordination.
    """

    multi_tele_freq_nums: Annotated[SequenceNotStr[str], PropertyInfo(alias="multiTeleFreqNums")]
    """
    Array of telephone numbers or contact frequencies used for interface control for
    multilink coordination.
    """

    multi_voice_net_des: Annotated[str, PropertyInfo(alias="multiVoiceNetDes")]
    """
    Designator assigned to a voice interface control and coordination net for
    multilink coordination (e.g. ADCCN, DCN, VPN, etc.).
    """


class MultiDuty(TypedDict, total=False):
    duty: str
    """Specific duties assigned for multilink coordination (e.g. ICO, RICO, SICO)."""

    duty_tele_freq_nums: Annotated[SequenceNotStr[str], PropertyInfo(alias="dutyTeleFreqNums")]
    """
    Array of telephone numbers or the frequency values for radio transmission of the
    person to be contacted for multilink coordination.
    """

    multi_duty_voice_coord: Annotated[Iterable[MultiDutyMultiDutyVoiceCoord], PropertyInfo(alias="multiDutyVoiceCoord")]
    """
    Collection of information regarding the function, frequency, and priority of
    interface control and coordination nets for multilink coordination. There can be
    0 to many DataLinkMultiVoiceCoord collections within a DataLinkMultiDuty
    collection.
    """

    name: str
    """The name of the person to be contacted for multilink coordination."""

    rank: str
    """The rank or position of the person to be contacted for multilink coordination."""

    unit_des: Annotated[str, PropertyInfo(alias="unitDes")]
    """
    Designated force of unit specified by ship name, unit call sign, or unit
    designator.
    """


class Op(TypedDict, total=False):
    link_details: Annotated[str, PropertyInfo(alias="linkDetails")]
    """Detailed characteristics of the data link."""

    link_name: Annotated[str, PropertyInfo(alias="linkName")]
    """Name of the data link."""

    link_start_time: Annotated[Union[str, datetime], PropertyInfo(alias="linkStartTime", format="iso8601")]
    """
    The start of the effective time period of the data link, in ISO 8601 UTC format
    with millisecond precision.
    """

    link_stop_time: Annotated[Union[str, datetime], PropertyInfo(alias="linkStopTime", format="iso8601")]
    """
    The end of the effective time period of the data link, in ISO 8601 UTC format
    with millisecond precision.
    """

    link_stop_time_mod: Annotated[str, PropertyInfo(alias="linkStopTimeMod")]
    """
    A qualifier for the end of the effective time period of this data link, such as
    AFTER, ASOF, NLT, etc. Used with field linkStopTimeMod to indicate a relative
    time.
    """


class Reference(TypedDict, total=False):
    ref_originator: Annotated[str, PropertyInfo(alias="refOriginator")]
    """The originator of this reference."""

    ref_serial_id: Annotated[str, PropertyInfo(alias="refSerialId")]
    """
    Specifies an alphabetic serial identifier a reference pertaining to the data
    link message.
    """

    ref_serial_num: Annotated[str, PropertyInfo(alias="refSerialNum")]
    """Serial number assigned to this reference."""

    ref_si_cs: Annotated[SequenceNotStr[str], PropertyInfo(alias="refSICs")]
    """
    Array of NATO Subject Indicator Codes (SIC) or filing numbers of the document
    being referenced.
    """

    ref_special_notation: Annotated[str, PropertyInfo(alias="refSpecialNotation")]
    """
    Indicates any special actions, restrictions, guidance, or information relating
    to this reference.
    """

    ref_ts: Annotated[Union[str, datetime], PropertyInfo(alias="refTs", format="iso8601")]
    """
    Timestamp of the referenced message, in ISO 8601 UTC format with millisecond
    precision.
    """

    ref_type: Annotated[str, PropertyInfo(alias="refType")]
    """Specifies the type of document referenced."""


class RefPoint(TypedDict, total=False):
    eff_event_time: Annotated[Union[str, datetime], PropertyInfo(alias="effEventTime", format="iso8601")]
    """
    Indicates when a particular event or nickname becomes effective or the old event
    or nickname is deleted, in ISO 8601 UTC format with millisecond precision.
    """

    ref_des: Annotated[str, PropertyInfo(alias="refDes")]
    """Identifier to designate a reference point."""

    ref_lat: Annotated[float, PropertyInfo(alias="refLat")]
    """WGS84 latitude of the reference point for this data link message, in degrees.

    -90 to 90 degrees (negative values south of equator).
    """

    ref_loc_name: Annotated[str, PropertyInfo(alias="refLocName")]
    """The location name of the point of reference for this data link message."""

    ref_lon: Annotated[float, PropertyInfo(alias="refLon")]
    """WGS84 longitude of the reference point for this data link message, in degrees.

    -90 to 90 degrees (negative values south of equator).
    """

    ref_point_type: Annotated[str, PropertyInfo(alias="refPointType")]
    """Type of data link reference point or grid origin."""


class Remark(TypedDict, total=False):
    text: str
    """Text of the remark."""

    type: str
    """Indicates the subject matter of the remark."""


class SpecTrack(TypedDict, total=False):
    spec_track_num: Annotated[str, PropertyInfo(alias="specTrackNum")]
    """
    The special track number used on the data link entered as an octal reference
    number. Used to identify a particular type of platform (e.g. MPA, KRESTA) or
    platform name (e.g. TROMP, MOUNT WHITNEY) which is not included in assigned
    track blocks.
    """

    spec_track_num_desc: Annotated[str, PropertyInfo(alias="specTrackNumDesc")]
    """Description of the special track number."""


class VoiceCoord(TypedDict, total=False):
    comm_pri: Annotated[str, PropertyInfo(alias="commPri")]
    """
    Priority of a communication circuit, channel or frequency for this data link
    message such as P (Primary), M (Monitor), etc.
    """

    freq_des: Annotated[str, PropertyInfo(alias="freqDes")]
    """
    Designator used in nonsecure communications to refer to a radio frequency for
    this data link message.
    """

    tele_freq_nums: Annotated[SequenceNotStr[str], PropertyInfo(alias="teleFreqNums")]
    """
    Array of telephone numbers or contact frequencies used for interface control for
    this data link message.
    """

    voice_net_des: Annotated[str, PropertyInfo(alias="voiceNetDes")]
    """
    Designator assigned to a voice interface control and coordination net for this
    data link message (e.g. ADCCN, DCN, VPN, etc.).
    """


class DatalinkIngestParam(TypedDict, total=False):
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

    op_ex_name: Required[Annotated[str, PropertyInfo(alias="opExName")]]
    """
    Specifies the unique operation or exercise name, nickname, or codeword assigned
    to a joint exercise or operation plan.
    """

    originator: Required[str]
    """The identifier of the originator of this message."""

    source: Required[str]
    """Source of the data."""

    start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startTime", format="iso8601")]]
    """
    The start of the effective time period of this data link message, in ISO 8601
    UTC format with millisecond precision.
    """

    id: str
    """
    Unique identifier of the record, auto-generated by the system if not provided on
    create operations.
    """

    ack_inst_units: Annotated[SequenceNotStr[str], PropertyInfo(alias="ackInstUnits")]
    """
    Array of instructions for acknowledging and the force or units required to
    acknowledge the data link message being sent.
    """

    ack_req: Annotated[bool, PropertyInfo(alias="ackReq")]
    """
    Flag Indicating if formal acknowledgement is required for the particular data
    link message being sent.
    """

    alt_diff: Annotated[int, PropertyInfo(alias="altDiff")]
    """Maximum altitude difference between two air tracks, in thousands of feet.

    Required if sysDefaultCode field is "MAN". Allowable entires are 5 to 50 in
    increments of 5000 feet.
    """

    canx_id: Annotated[str, PropertyInfo(alias="canxId")]
    """The identifier for this data link message cancellation."""

    canx_originator: Annotated[str, PropertyInfo(alias="canxOriginator")]
    """The originator of this data link message cancellation."""

    canx_serial_num: Annotated[str, PropertyInfo(alias="canxSerialNum")]
    """Serial number assigned to this data link message cancellation."""

    canx_si_cs: Annotated[SequenceNotStr[str], PropertyInfo(alias="canxSICs")]
    """
    Array of NATO Subject Indicator Codes (SIC) or filing numbers of this data link
    message or document being cancelled.
    """

    canx_special_notation: Annotated[str, PropertyInfo(alias="canxSpecialNotation")]
    """
    Indicates any special actions, restrictions, guidance, or information relating
    to this data link message cancellation.
    """

    canx_ts: Annotated[Union[str, datetime], PropertyInfo(alias="canxTs", format="iso8601")]
    """
    Timestamp of the data link message cancellation, in ISO 8601 UTC format with
    millisecond precision.
    """

    class_reasons: Annotated[SequenceNotStr[str], PropertyInfo(alias="classReasons")]
    """Array of codes that indicate the reasons material is classified."""

    class_source: Annotated[str, PropertyInfo(alias="classSource")]
    """
    Markings that define the source material or the original classification
    authority for this data link message.
    """

    consec_decorr: Annotated[int, PropertyInfo(alias="consecDecorr")]
    """
    Number of consecutive remote track reports that must meet the decorrelation
    criteria before the decorrelation is executed. Required if sysDefaultCode field
    is "MAN". Allowable entries are integers from 1 to 5.
    """

    course_diff: Annotated[int, PropertyInfo(alias="courseDiff")]
    """
    Maximum difference between the reported course of the remote track and the
    calculated course of the local track. Required if sysDefaultCode field is "MAN".
    Allowable entries are 15 to 90 in increments of 15 degrees.
    """

    dec_exempt_codes: Annotated[SequenceNotStr[str], PropertyInfo(alias="decExemptCodes")]
    """
    Array of codes that provide justification for exemption from automatic
    downgrading or declassification.
    """

    dec_inst_dates: Annotated[SequenceNotStr[str], PropertyInfo(alias="decInstDates")]
    """
    Array of markings that provide the literal guidance or dates for the downgrading
    or declassification of this data link message.
    """

    decorr_win_mult: Annotated[float, PropertyInfo(alias="decorrWinMult")]
    """
    Distance between the common and remote track is to exceed the applicable
    correlation window for the two tracks in order to be decorrelated. Required if
    sysDefaultCode field is "MAN". Allowable entries are 1.0 to 2.0 in increments of
    0.1.
    """

    geo_datum: Annotated[str, PropertyInfo(alias="geoDatum")]
    """
    The code for the point of reference from which the coordinates and networks are
    computed.
    """

    jre_call_sign: Annotated[str, PropertyInfo(alias="jreCallSign")]
    """
    Call sign which identifies one or more communications facilities, commands,
    authorities, or activities for Joint Range Extension (JRE) units.
    """

    jre_details: Annotated[str, PropertyInfo(alias="jreDetails")]
    """Joint Range Extension (JRE) unit details."""

    jre_pri_add: Annotated[int, PropertyInfo(alias="jrePriAdd")]
    """Link-16 octal track number assigned as the primary JTIDS unit address."""

    jre_sec_add: Annotated[int, PropertyInfo(alias="jreSecAdd")]
    """Link-16 octal track number assigned as the secondary JTIDS unit address."""

    jre_unit_des: Annotated[str, PropertyInfo(alias="jreUnitDes")]
    """Designator of the unit for Joint Range Extension (JRE)."""

    max_geo_pos_qual: Annotated[int, PropertyInfo(alias="maxGeoPosQual")]
    """Number used for maximum geodetic position quality.

    Required if sysDefaultCode field is "MAN". Allowable entires are integers from 1
    to 15.
    """

    max_track_qual: Annotated[int, PropertyInfo(alias="maxTrackQual")]
    """Track quality to prevent correlation windows from being unrealistically small.

    Required if sysDefaultCode field is "MAN". Allowable entries are integers from 8
    to 15.
    """

    mgmt_code: Annotated[str, PropertyInfo(alias="mgmtCode")]
    """Data link management code word."""

    mgmt_code_meaning: Annotated[str, PropertyInfo(alias="mgmtCodeMeaning")]
    """Data link management code word meaning."""

    min_geo_pos_qual: Annotated[int, PropertyInfo(alias="minGeoPosQual")]
    """Number used for minimum geodetic position quality.

    Required if sysDefaultCode field is "MAN". Allowable entries are integers from 1
    to 5.
    """

    min_track_qual: Annotated[int, PropertyInfo(alias="minTrackQual")]
    """Track quality to prevent correlation windows from being unrealistically large.

    Required if sysDefaultCode field is "MAN". Allowable entries are integers from 3
    to 7.
    """

    month: str
    """The month in which this message originated."""

    multi_duty: Annotated[Iterable[MultiDuty], PropertyInfo(alias="multiDuty")]
    """
    Collection of contact and identification information for designated multilink
    coordinator duty assignments. There can be 0 to many DataLinkMultiDuty
    collections within the datalink service.
    """

    non_link_unit_des: Annotated[SequenceNotStr[str], PropertyInfo(alias="nonLinkUnitDes")]
    """Array of non-link specific data unit designators."""

    op_ex_info: Annotated[str, PropertyInfo(alias="opExInfo")]
    """
    Provides an additional caveat further identifying the exercise or modifies the
    exercise nickname.
    """

    op_ex_info_alt: Annotated[str, PropertyInfo(alias="opExInfoAlt")]
    """
    The secondary nickname of the option or the alternative of the operational plan
    or order.
    """

    ops: Iterable[Op]
    """
    Collection of information describing the establishment and detailed operation of
    tactical data links. There can be 0 to many DataLinkOps collections within the
    datalink service.
    """

    origin: str
    """
    Originating system or organization which produced the data, if different from
    the source. The origin may be different than the source if the source was a
    mediating system which forwarded the data on behalf of the origin system. If
    null, the source may be assumed to be the origin.
    """

    plan_orig_num: Annotated[str, PropertyInfo(alias="planOrigNum")]
    """
    The official identifier of the military establishment responsible for the
    operation plan and the identification number assigned to this plan.
    """

    poc_call_sign: Annotated[str, PropertyInfo(alias="pocCallSign")]
    """
    The unit identifier or call sign of the point of contact for this data link
    message.
    """

    poc_lat: Annotated[float, PropertyInfo(alias="pocLat")]
    """WGS84 latitude of the point of contact for this data link message, in degrees.

    -90 to 90 degrees (negative values south of equator).
    """

    poc_loc_name: Annotated[str, PropertyInfo(alias="pocLocName")]
    """The location name of the point of contact for this data link message."""

    poc_lon: Annotated[float, PropertyInfo(alias="pocLon")]
    """WGS84 longitude of the point of contact for this data link message, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian).
    """

    poc_name: Annotated[str, PropertyInfo(alias="pocName")]
    """The name of the point of contact for this data link message."""

    poc_nums: Annotated[SequenceNotStr[str], PropertyInfo(alias="pocNums")]
    """
    Array of telephone numbers, radio frequency values, or email addresses of the
    point of contact for this data link message.
    """

    poc_rank: Annotated[str, PropertyInfo(alias="pocRank")]
    """
    The rank or position of the point of contact for this data link message in a
    military or civilian organization.
    """

    qualifier: str
    """
    The qualifier which caveats the message status such as AMP (Amplification), CHG
    (Change), etc.
    """

    qual_sn: Annotated[int, PropertyInfo(alias="qualSN")]
    """The serial number associated with the message qualifier."""

    references: Iterable[Reference]
    """Collection of reference information.

    There can be 0 to many DataLinkReferences collections within the datalink
    service.
    """

    ref_points: Annotated[Iterable[RefPoint], PropertyInfo(alias="refPoints")]
    """
    Collection that identifies points of reference used in the establishment of the
    data links. There can be 1 to many DataLinkRefPoints collections within the
    datalink service.
    """

    remarks: Iterable[Remark]
    """Collection of remarks associated with this data link message."""

    res_track_qual: Annotated[int, PropertyInfo(alias="resTrackQual")]
    """
    Track quality to enter if too many duals involving low track quality tracks are
    occurring. Required if sysDefaultCode field is "MAN". Allowable entries are
    integers from 2 to 6.
    """

    serial_num: Annotated[str, PropertyInfo(alias="serialNum")]
    """The unique message identifier assigned by the originator."""

    spec_tracks: Annotated[Iterable[SpecTrack], PropertyInfo(alias="specTracks")]
    """Collection of special track numbers used on the data links.

    There can be 0 to many DataLinkSpecTracks collections within the datalink
    service.
    """

    speed_diff: Annotated[int, PropertyInfo(alias="speedDiff")]
    """Maximum percentage the faster track speed may differ from the slower track
    speed.

    Required if sysDefaultCode field is "MAN". Allowable entries are 10 to 100 in
    increments of 10.
    """

    stop_time: Annotated[Union[str, datetime], PropertyInfo(alias="stopTime", format="iso8601")]
    """
    The end of the effective time period of this data link message, in ISO 8601 UTC
    format with millisecond precision. This may be a relative stop time if used with
    stopTimeMod.
    """

    stop_time_mod: Annotated[str, PropertyInfo(alias="stopTimeMod")]
    """
    A qualifier for the end of the effective time period of this data link message,
    such as AFTER, ASOF, NLT, etc. Used with field stopTime to indicate a relative
    time.
    """

    sys_default_code: Annotated[str, PropertyInfo(alias="sysDefaultCode")]
    """
    Indicates the data terminal settings the system defaults to, either automatic
    correlation/decorrelation (AUTO) or manual (MAN).
    """

    track_num_block_l_ls: Annotated[Iterable[int], PropertyInfo(alias="trackNumBlockLLs")]
    """Array of Link-16 octal track numbers used as the lower limit of a track block."""

    track_num_blocks: Annotated[SequenceNotStr[str], PropertyInfo(alias="trackNumBlocks")]
    """
    Array of defined ranges of Link-11/11B track numbers assigned to a participating
    unit or reporting unit.
    """

    voice_coord: Annotated[Iterable[VoiceCoord], PropertyInfo(alias="voiceCoord")]
    """
    Collection of information regarding the function, frequency, and priority of
    interface control and coordination nets for this data link message. There can be
    1 to many DataLinkVoiceCoord collections within the datalink service.
    """

    win_size_min: Annotated[float, PropertyInfo(alias="winSizeMin")]
    """
    Number added to the basic window calculated from track qualities to ensure that
    windows still allow valid correlations. Required if sysDefaultCode field is
    "MAN". Allowable entries are 0.0 to 2.0 in increments of 0.25.
    """

    win_size_mult: Annotated[float, PropertyInfo(alias="winSizeMult")]
    """The correlation window size multiplier to stretch or reduce the window size.

    Required if sysDefaultCode field is "MAN". Allowable entries are 0.5 to 3.0 in
    increments of 0.1.
    """
