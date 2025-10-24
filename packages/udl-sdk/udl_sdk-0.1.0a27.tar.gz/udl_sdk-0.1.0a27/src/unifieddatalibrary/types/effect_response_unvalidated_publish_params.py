# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "EffectResponseUnvalidatedPublishParams",
    "Body",
    "BodyActionsList",
    "BodyActionsListActionMetric",
    "BodyCoaMetric",
]


class EffectResponseUnvalidatedPublishParams(TypedDict, total=False):
    body: Required[Iterable[Body]]


class BodyActionsListActionMetric(TypedDict, total=False):
    domain_value: Annotated[float, PropertyInfo(alias="domainValue")]
    """The metric score specific to its domain."""

    metric_type: Annotated[str, PropertyInfo(alias="metricType")]
    """The type of the metric (e.g.

    CollateralDamage, GoalAchievement, OpportunityCost, Timeliness, Unavailable,
    etc.).
    """

    provenance: str
    """The metric that was used to score this task."""

    relative_value: Annotated[float, PropertyInfo(alias="relativeValue")]
    """The metric score adjusted to be relative and comparable to other domains."""


class BodyActionsList(TypedDict, total=False):
    action_actor_src_id: Annotated[str, PropertyInfo(alias="actionActorSrcId")]
    """
    The record ID, depending on the type identified in actorSrcType, of the
    requested asset/actor.
    """

    action_actor_src_type: Annotated[str, PropertyInfo(alias="actionActorSrcType")]
    """
    The source type of the asset/actor identifier (AIRCRAFT, LANDCRAFT, SEACRAFT,
    TRACK).
    """

    action_end_time: Annotated[Union[str, datetime], PropertyInfo(alias="actionEndTime", format="iso8601")]
    """The desired end time of this task, in ISO8601 UTC format."""

    action_id: Annotated[str, PropertyInfo(alias="actionId")]
    """Identifier of this action."""

    action_metrics: Annotated[Iterable[BodyActionsListActionMetric], PropertyInfo(alias="actionMetrics")]
    """List of metrics associated with this action."""

    action_start_time: Annotated[Union[str, datetime], PropertyInfo(alias="actionStartTime", format="iso8601")]
    """The desired start time of this task, in ISO8601 UTC format."""

    actor_intercept_alt: Annotated[float, PropertyInfo(alias="actorInterceptAlt")]
    """The WGS-84 altitude of the asset/actor location at weapon launch, in meters."""

    actor_intercept_lat: Annotated[float, PropertyInfo(alias="actorInterceptLat")]
    """The WGS-84 latitude of the asset/actor location at weapon launch, in degrees.

    -90 to 90 degrees (negative values south of equator).
    """

    actor_intercept_lon: Annotated[float, PropertyInfo(alias="actorInterceptLon")]
    """The WGS-84 longitude of the asset/actor location at weapon launch, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian).
    """

    effector: str
    """The type of munition or sensor used by this asset/actor."""

    summary: str
    """A summary string describing different aspects of the action."""

    target_src_id: Annotated[str, PropertyInfo(alias="targetSrcId")]
    """
    The POI or TRACK ID, depending on the type identified in targetSrcType, of the
    requested target. This identifier corresponds to either poi.poiid or track.trkId
    from their respective schemas.
    """

    target_src_type: Annotated[str, PropertyInfo(alias="targetSrcType")]
    """The source type of the targetId identifier (POI, TRACK)."""

    tot_end_time: Annotated[Union[str, datetime], PropertyInfo(alias="totEndTime", format="iso8601")]
    """The end time of the asset TOT (time over target), in ISO8601 UTC format."""

    tot_start_time: Annotated[Union[str, datetime], PropertyInfo(alias="totStartTime", format="iso8601")]
    """The start time of the asset TOT (time over target), in ISO8601 UTC format."""

    weapon_intercept_alt: Annotated[float, PropertyInfo(alias="weaponInterceptAlt")]
    """The WGS-84 altitude of the weapon destination location, in meters."""

    weapon_intercept_lat: Annotated[float, PropertyInfo(alias="weaponInterceptLat")]
    """The WGS-84 latitude of the weapon destination location, in degrees.

    -90 to 90 degrees (negative values south of equator).
    """

    weapon_intercept_lon: Annotated[float, PropertyInfo(alias="weaponInterceptLon")]
    """The WGS-84 longitude of the weapon destination location, in degrees.

    -180 to 180 degrees (negative values west of Prime Meridian).
    """


class BodyCoaMetric(TypedDict, total=False):
    domain_value: Annotated[float, PropertyInfo(alias="domainValue")]
    """The metric score specific to its domain."""

    metric_type: Annotated[str, PropertyInfo(alias="metricType")]
    """The type of the metric (e.g.

    CollateralDamage, GoalAchievement, OpportunityCost, Timeliness, Unavailable,
    etc.).
    """

    provenance: str
    """The metric that was used to score this task."""

    relative_value: Annotated[float, PropertyInfo(alias="relativeValue")]
    """The metric score adjusted to be relative and comparable to other domains."""


class Body(TypedDict, total=False):
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

    source: Required[str]
    """Source of the data."""

    type: Required[str]
    """The type of response in this record (e.g. COA, SCORECARD, etc.)."""

    id: str
    """Unique identifier of the record, auto-generated by the system."""

    actions_list: Annotated[Iterable[BodyActionsList], PropertyInfo(alias="actionsList")]
    """List of actions associated with this effect response."""

    actor_src_id: Annotated[str, PropertyInfo(alias="actorSrcId")]
    """
    The record ID, depending on the type identified in actorSrcType, of the
    requested asset.
    """

    actor_src_type: Annotated[str, PropertyInfo(alias="actorSrcType")]
    """
    The source type of the asset/actor identifier (AIRCRAFT, LANDCRAFT, SEACRAFT,
    TRACK).
    """

    coa_metrics: Annotated[Iterable[BodyCoaMetric], PropertyInfo(alias="coaMetrics")]
    """List of COA metrics associated with this effect response."""

    collateral_damage_est: Annotated[float, PropertyInfo(alias="collateralDamageEst")]
    """The collateral damage estimate (CDE) of the munition being fired."""

    decision_deadline: Annotated[Union[str, datetime], PropertyInfo(alias="decisionDeadline", format="iso8601")]
    """
    The deadline time to accept this COA before it's no longer valid, in ISO8601 UTC
    format.
    """

    external_actions: Annotated[SequenceNotStr[str], PropertyInfo(alias="externalActions")]
    """List of external actions to be executed as part of this task."""

    external_request_id: Annotated[str, PropertyInfo(alias="externalRequestId")]
    """The external system identifier of the associated effect request.

    A human readable unique id.
    """

    id_effect_request: Annotated[str, PropertyInfo(alias="idEffectRequest")]
    """Unique identifier of the EffectRequest associated with this response."""

    munition_id: Annotated[str, PropertyInfo(alias="munitionId")]
    """Unique identifier of the munition."""

    munition_type: Annotated[str, PropertyInfo(alias="munitionType")]
    """The type of munition being fired."""

    origin: str
    """
    Originating system or organization which produced the data, if different from
    the source. The origin may be different than the source if the source was a
    mediating system which forwarded the data on behalf of the origin system. If
    null, the source may be assumed to be the origin.
    """

    probability_of_kill: Annotated[float, PropertyInfo(alias="probabilityOfKill")]
    """The probability of kill (0-1) of the target being destroyed."""

    red_target_src_id: Annotated[str, PropertyInfo(alias="redTargetSrcId")]
    """
    The record ID, depending on the type identified in redTargetSrcType, of the red
    force target. If the redTargetSrcType is POI or TRACK, then this identifier
    corresponds to either poi.poiid or track.trkId from their respective schemas.
    """

    red_target_src_type: Annotated[str, PropertyInfo(alias="redTargetSrcType")]
    """The source type of the targetId identifier (POI, SITE, TRACK)."""

    red_time_to_overhead: Annotated[Union[str, datetime], PropertyInfo(alias="redTimeToOverhead", format="iso8601")]
    """
    The time to overhead for the red force to be over their target, in ISO8601 UTC
    format.
    """

    shots_required: Annotated[int, PropertyInfo(alias="shotsRequired")]
    """The number of shots required to destroy target."""
