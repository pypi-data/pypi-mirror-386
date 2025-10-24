# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "SoiObservationSetCreateBulkParams",
    "Body",
    "BodyCalibration",
    "BodyOpticalSoiObservationList",
    "BodyRadarSoiObservationList",
]


class SoiObservationSetCreateBulkParams(TypedDict, total=False):
    body: Required[Iterable[Body]]


class BodyCalibration(TypedDict, total=False):
    cal_bg_intensity: Annotated[float, PropertyInfo(alias="calBgIntensity")]
    """
    Background intensity, at calibration, specified in kilowatts per steradian per
    micrometer.
    """

    cal_extinction_coeff: Annotated[float, PropertyInfo(alias="calExtinctionCoeff")]
    """
    Coefficient value for how much signal would be lost to atmospheric attenuation
    for a star at zenith, in magnitudes per air mass.
    """

    cal_extinction_coeff_max_unc: Annotated[float, PropertyInfo(alias="calExtinctionCoeffMaxUnc")]
    """Maximum extinction coefficient uncertainty in magnitudes, at calibration (e.g.

    -5.0 to 30.0).
    """

    cal_extinction_coeff_unc: Annotated[float, PropertyInfo(alias="calExtinctionCoeffUnc")]
    """
    Extinction coefficient uncertainty in magnitudes, at calibration, which
    represents the difference between the measured brightness and predicted
    brightness of the star with the extinction removed, making it exo-atmospheric
    (e.g. -5.0 to 30.0).
    """

    cal_num_correlated_stars: Annotated[int, PropertyInfo(alias="calNumCorrelatedStars")]
    """Number of correlated stars in the FOV with the target object, at calibration.

    Can be 0 for narrow FOV sensors.
    """

    cal_num_detected_stars: Annotated[int, PropertyInfo(alias="calNumDetectedStars")]
    """Number of detected stars in the FOV with the target object, at calibration.

    Helps identify frames with clouds.
    """

    cal_sky_bg: Annotated[float, PropertyInfo(alias="calSkyBg")]
    """Average Sky Background signals in magnitudes, at calibration.

    Sky Background refers to the incoming light from an apparently empty part of the
    night sky.
    """

    cal_spectral_filter_solar_mag: Annotated[float, PropertyInfo(alias="calSpectralFilterSolarMag")]
    """In-band solar magnitudes at 1 A.U, at calibration (e.g. -5.0 to 30.0)."""

    cal_time: Annotated[Union[str, datetime], PropertyInfo(alias="calTime", format="iso8601")]
    """Start time of calibration in ISO 8601 UTC time, with millisecond precision."""

    cal_type: Annotated[str, PropertyInfo(alias="calType")]
    """Type of calibration (e.g. PRE, MID, POST)."""

    cal_zero_point: Annotated[float, PropertyInfo(alias="calZeroPoint")]
    """
    Value representing the difference between the catalog magnitude and instrumental
    magnitude for a set of standard stars, at calibration (e.g. -5.0 to 30.0).
    """


class BodyOpticalSoiObservationList(TypedDict, total=False):
    ob_start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="obStartTime", format="iso8601")]]
    """Observation detection start time in ISO 8601 UTC with microsecond precision."""

    current_spectral_filter_num: Annotated[int, PropertyInfo(alias="currentSpectralFilterNum")]
    """
    The reference number, x, where x ranges from 1 to n, where n is the number
    specified in spectralFilters that corresponds to the spectral filter used.
    """

    declination_rates: Annotated[Iterable[float], PropertyInfo(alias="declinationRates")]
    """
    Array of declination rate values, in degrees per second, measuring the rate
    speed at which an object's declination changes over time, for each element in
    the intensities field, at the middle of the frame's exposure time.
    """

    declinations: Iterable[float]
    """
    Array of declination values, in degrees, of the Target object from the frame of
    reference of the sensor. A value is provided for each element in the intensities
    field, at the middle of the frame’s exposure time.
    """

    exp_duration: Annotated[float, PropertyInfo(alias="expDuration")]
    """Image exposure duration in seconds."""

    extinction_coeffs: Annotated[Iterable[float], PropertyInfo(alias="extinctionCoeffs")]
    """
    Array of coefficients for how much signal would be lost to atmospheric
    attenuation for a star at zenith for each element in intensities, in magnitudes
    per air mass.
    """

    extinction_coeffs_unc: Annotated[Iterable[float], PropertyInfo(alias="extinctionCoeffsUnc")]
    """Array of extinction coefficient uncertainties for each element in intensities.

    Each value represents the difference between the measured brightness and
    predicted brightness of the star with the extinction removed, making it
    exo-atmospheric (e.g. -5.0 to 30.0).
    """

    intensities: Iterable[float]
    """
    Array of intensities of the Space Object for observations, in kilowatts per
    steradian per micrometer.
    """

    intensity_times: Annotated[
        SequenceNotStr[Union[str, datetime]], PropertyInfo(alias="intensityTimes", format="iso8601")
    ]
    """Array of start times for each intensity measurement.

    The 1st value in the array will match obStartTime.
    """

    local_sky_bgs: Annotated[Iterable[float], PropertyInfo(alias="localSkyBgs")]
    """
    Array of local average Sky Background signals, in magnitudes, with a value
    corresponding to the time of each intensity measurement. Sky Background refers
    to the incoming light from an apparently empty part of the night sky.
    """

    local_sky_bgs_unc: Annotated[Iterable[float], PropertyInfo(alias="localSkyBgsUnc")]
    """
    Array of uncertainty of the local average Sky Background signal, in magnitudes,
    with a value corresponding to the time of each intensity measurement.
    """

    num_correlated_stars: Annotated[Iterable[int], PropertyInfo(alias="numCorrelatedStars")]
    """
    Array of the number of correlated stars in the FOV with a value for each element
    in the intensities field.
    """

    num_detected_stars: Annotated[Iterable[int], PropertyInfo(alias="numDetectedStars")]
    """
    Array of the number of detected stars in the FOV with a value for each element
    in the intensities field.
    """

    percent_sats: Annotated[Iterable[float], PropertyInfo(alias="percentSats")]
    """
    Array of values giving the percent of pixels that make up the object signal that
    are beyond the saturation point for the sensor, with a value for each element in
    the intensities field.
    """

    ra_rates: Annotated[Iterable[float], PropertyInfo(alias="raRates")]
    """
    Array of right ascension rate values, in degrees per second, measuring the rate
    the telescope is moving to track the Target object from the frame of reference
    of the sensor, for each element in the intensities field, at the middle of the
    frame’s exposure time.
    """

    ras: Iterable[float]
    """
    Array of right ascension values, in degrees, of the Target object from the frame
    of reference of the sensor. A value is provided for each element in the
    intensities field.
    """

    sky_bgs: Annotated[Iterable[float], PropertyInfo(alias="skyBgs")]
    """
    Array of average Sky Background signals, in magnitudes, with a value
    corresponding to the time of each intensity measurement. Sky Background refers
    to the incoming light from an apparently empty part of the night sky.
    """

    zero_points: Annotated[Iterable[float], PropertyInfo(alias="zeroPoints")]
    """
    Array of values for the zero-point in magnitudes, calculated at the time of each
    intensity measurement. It is the difference between the catalog mag and
    instrumental mag for a set of standard stars (e.g. -5.0 to 30.0).
    """


class BodyRadarSoiObservationList(TypedDict, total=False):
    ob_start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="obStartTime", format="iso8601")]]
    """
    Observation detection start time in ISO 8601 UTC format with microsecond
    precision.
    """

    aspect_angles: Annotated[Iterable[float], PropertyInfo(alias="aspectAngles")]
    """Array of the aspect angle at the center of the image in degrees.

    The 'tovs' and 'aspectAngles' arrays must match in size, if 'aspectAngles' is
    provided.
    """

    azimuth_biases: Annotated[Iterable[float], PropertyInfo(alias="azimuthBiases")]
    """Array of sensor azimuth angle biases in degrees.

    The 'tovs' and 'azimuthBiases' arrays must match in size, if 'azimuthBiases' is
    provided.
    """

    azimuth_rates: Annotated[Iterable[float], PropertyInfo(alias="azimuthRates")]
    """Array of the azimuth rate of target at image center in degrees per second.

    The 'tovs' and 'azimuthRates' arrays must match in size, if 'azimuthRates' is
    provided. If there is an associated image the azimuth rate is assumed to be at
    image center.
    """

    azimuths: Iterable[float]
    """Array of the azimuth angle to target at image center in degrees.

    The 'tovs' and 'azimuths' arrays must match in size, if 'azimuths' is provided.
    If there is an associated image the azimuth angle is assumed to be at image
    center.
    """

    beta: float
    """Beta angle (between target and radar-image frame z axis) in degrees."""

    center_frequency: Annotated[float, PropertyInfo(alias="centerFrequency")]
    """Radar center frequency of the radar in hertz."""

    cross_range_res: Annotated[Iterable[float], PropertyInfo(alias="crossRangeRes")]
    """
    Array of cross-range resolutions (accounting for weighting function) in
    kilometers. The 'tovs' and 'crossRangeRes' arrays must match in size, if
    'crossRangeRes' is provided.
    """

    delta_times: Annotated[Iterable[float], PropertyInfo(alias="deltaTimes")]
    """Array of average Interpulse spacing in seconds.

    The 'tovs' and 'deltaTimes' arrays must match in size, if 'deltaTimes' is
    provided.
    """

    doppler2_x_rs: Annotated[Iterable[float], PropertyInfo(alias="doppler2XRs")]
    """Array of conversion factors between Doppler in hertz and cross-range in meters.

    The 'tovs' and 'doppler2XRs' arrays must match in size, if 'doppler2XRs' is
    provided.
    """

    elevation_biases: Annotated[Iterable[float], PropertyInfo(alias="elevationBiases")]
    """Array of sensor elevation biases in degrees.

    The 'tovs' and 'elevationBiases' arrays must match in size, if 'elevationBiases'
    is provided.
    """

    elevation_rates: Annotated[Iterable[float], PropertyInfo(alias="elevationRates")]
    """Array of the elevation rate of target at image center in degrees per second.

    The 'tovs' and 'elevationRates' arrays must match in size, if 'elevationRates'
    is provided. If there is an associated image the elevation rate is assumed to be
    at image center.
    """

    elevations: Iterable[float]
    """Array of the elevation angle to target at image center in degrees.

    The 'tovs' and 'elevations' arrays must match in size, if 'elevations' is
    provided. If there is an associated image the elevation angle is assumed to be
    at image center.
    """

    id_attitude_set: Annotated[str, PropertyInfo(alias="idAttitudeSet")]
    """Optional id of assumed AttitudeSet of object being observed."""

    id_state_vector: Annotated[str, PropertyInfo(alias="idStateVector")]
    """Optional id of assumed StateVector of object being observed."""

    integration_angles: Annotated[Iterable[float], PropertyInfo(alias="integrationAngles")]
    """Array of Integration angles in degrees.

    The 'tovs' and 'integrationAngles' arrays must match in size, if
    'integrationAngles' is provided.
    """

    kappa: float
    """Kappa angle (between radar-line-of-sight and target-frame x axis) in degrees."""

    peak_amplitudes: Annotated[Iterable[float], PropertyInfo(alias="peakAmplitudes")]
    """Array of the peak pixel amplitude for each image in decibels.

    The 'tovs' and 'peakAmplitudes' arrays must match in size, if 'peakAmplitudes'
    is provided.
    """

    polarizations: SequenceNotStr[str]
    """Array of sensor polarizations when collecting the data.

    Polarization is a property of electromagnetic waves that describes the
    orientation of their oscillations. Possible values are H - (Horizontally
    Polarized) Perpendicular to Earth's surface, V - (Vertically Polarized) Parallel
    to Earth's surface, L - (Left Hand Circularly Polarized) Rotating left relative
    to the Earth's surface, R - (Right Hand Circularly Polarized) Rotating right
    relative to the Earth's surface.
    """

    proj_ang_vels: Annotated[Iterable[float], PropertyInfo(alias="projAngVels")]
    """
    Array of the component of target angular velocity observable by radar in radians
    per second. The 'tovs' and 'projAngVels' arrays must match in size, if
    'projAngVels' is provided.
    """

    pulse_bandwidth: Annotated[float, PropertyInfo(alias="pulseBandwidth")]
    """Bandwidth of radar pulse in hertz."""

    range_accels: Annotated[Iterable[float], PropertyInfo(alias="rangeAccels")]
    """Array of the range accelerations of target in kilometers per second squared.

    The 'tovs' and 'rangeAccels' arrays must match in size, if 'rangeAccels' is
    provided. If there is an associated image the range acceleration is assumed to
    be at image center.
    """

    range_biases: Annotated[Iterable[float], PropertyInfo(alias="rangeBiases")]
    """Array of sensor range biases in kilometers.

    The 'tovs' and 'rangeBiases' arrays must match in size, if 'rangeBiases' is
    provided.
    """

    range_rates: Annotated[Iterable[float], PropertyInfo(alias="rangeRates")]
    """Array of the range rate of target at image center in kilometers per second.

    The 'tovs' and 'rangeRates' arrays must match in size, if 'rangeRates' is
    provided. If there is an associated image the range rate is assumed to be at
    image center.
    """

    ranges: Iterable[float]
    """Array of the range to target at image center in kilometers.

    The 'tovs' and 'ranges' arrays must match in size, if 'ranges' is provided. If
    there is an associated image the range is assumed to be at image center.
    """

    rcs_error_ests: Annotated[Iterable[float], PropertyInfo(alias="rcsErrorEsts")]
    """Array of error estimates of RCS values, in square meters."""

    rcs_values: Annotated[Iterable[float], PropertyInfo(alias="rcsValues")]
    """Array of observed radar cross section (RCS) values, in square meters."""

    rspaces: Iterable[float]
    """Array of range sample spacing in meters.

    The 'tovs' and 'rspaces' arrays must match in size, if 'rspaces' is provided.
    """

    spectral_widths: Annotated[Iterable[float], PropertyInfo(alias="spectralWidths")]
    """Array of spectral widths, in hertz.

    The spectral width of a satellite can help determine if an object is stable or
    tumbling which is often useful to distinguish a rocket body from an active
    stabilized payload or to deduce a rotational period of slowly tumbling objects
    at GEO.
    """

    tovs: Annotated[SequenceNotStr[Union[str, datetime]], PropertyInfo(format="iso8601")]
    """
    Array of the times of validity in ISO 8601 UTC format with microsecond
    precision.
    """

    waveform_number: Annotated[int, PropertyInfo(alias="waveformNumber")]
    """
    A unique numeric or hash identifier assigned to each distinct waveform, enabling
    traceability between the waveform used and the images or data products generated
    from it.
    """

    xaccel: Iterable[float]
    """
    Array of the cartesian X accelerations, in kilometers per second squared, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'xaccel' arrays must match in size, if 'xaccel' is provided.
    """

    xpos: Iterable[float]
    """
    Array of the cartesian X positions of the target, in kilometers, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'xpos' arrays must match in size, if 'xpos' is provided.
    """

    xspaces: Iterable[float]
    """Array of cross-range sample spacing in meters.

    The 'tovs' and 'xspaces' arrays must match in size, if 'xspaces' is provided.
    """

    xvel: Iterable[float]
    """
    Array of the cartesian X velocities of target, in kilometers per second, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'xvel' arrays must match in size, if 'xvel' is provided.
    """

    yaccel: Iterable[float]
    """
    Array of the cartesian Y accelerations, in kilometers per second squared, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'yaccel' arrays must match in size, if 'yaccel' is provided.
    """

    ypos: Iterable[float]
    """
    Array of the cartesian Y positions of the target, in kilometers, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'ypos' arrays must match in size, if 'ypos' is provided.
    """

    yvel: Iterable[float]
    """
    Array of the cartesian Y velocities of target, in kilometers per second, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'yvel' arrays must match in size, if 'yvel' is provided.
    """

    zaccel: Iterable[float]
    """
    Array of the cartesian Z accelerations, in kilometers per second squared, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'zaccel' arrays must match in size, if 'zaccel' is provided.
    """

    zpos: Iterable[float]
    """
    Array of the cartesian Z positions of the target, in kilometers, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'zpos' arrays must match in size, if 'zpos' is provided.
    """

    zvel: Iterable[float]
    """
    Array of the cartesian Z velocities of target, in kilometers per second, in the
    specified referenceFrame. If referenceFrame is null then J2K should be assumed.
    The 'tovs' and 'zvel' arrays must match in size, if 'zvel' is provided.
    """


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

    num_obs: Required[Annotated[int, PropertyInfo(alias="numObs")]]
    """The number of observation records in the set."""

    source: Required[str]
    """Source of the data."""

    start_time: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startTime", format="iso8601")]]
    """
    Observation set detection start time in ISO 8601 UTC with microsecond precision.
    """

    type: Required[Literal["OPTICAL", "RADAR"]]
    """Observation type (OPTICAL, RADAR)."""

    id: str
    """Unique identifier of the record, auto-generated by the system."""

    binning_horiz: Annotated[int, PropertyInfo(alias="binningHoriz")]
    """The number of pixels binned horizontally."""

    binning_vert: Annotated[int, PropertyInfo(alias="binningVert")]
    """The number of pixels binned vertically."""

    brightness_variance_change_detected: Annotated[bool, PropertyInfo(alias="brightnessVarianceChangeDetected")]
    """
    Boolean indicating if a brightness variance change event was detected, based on
    historical collection data for the object.
    """

    calibrations: Iterable[BodyCalibration]
    """Array of SOI Calibrations associated with this SOIObservationSet."""

    calibration_type: Annotated[str, PropertyInfo(alias="calibrationType")]
    """Type of calibration used by the Sensor (e.g.

    ALL SKY, DIFFERENTIAL, DEFAULT, NONE).
    """

    change_conf: Annotated[str, PropertyInfo(alias="changeConf")]
    """Overall qualitative confidence assessment of change detection results (e.g.

    HIGH, MEDIUM, LOW).
    """

    change_detected: Annotated[bool, PropertyInfo(alias="changeDetected")]
    """
    Boolean indicating if any change event was detected, based on historical
    collection data for the object.
    """

    collection_density_conf: Annotated[str, PropertyInfo(alias="collectionDensityConf")]
    """
    Qualitative Collection Density assessment, with respect to confidence of
    detecting a change event (e.g. HIGH, MEDIUM, LOW).
    """

    collection_id: Annotated[str, PropertyInfo(alias="collectionId")]
    """Universally Unique collection ID.

    Mechanism to correlate Single Point Photometry (SPP) JSON files to images.
    """

    collection_mode: Annotated[str, PropertyInfo(alias="collectionMode")]
    """
    Mode indicating telescope movement during collection (AUTOTRACK, MANUAL
    AUTOTRACK, MANUAL RATE TRACK, MANUAL SIDEREAL, SIDEREAL, RATE TRACK).
    """

    corr_quality: Annotated[float, PropertyInfo(alias="corrQuality")]
    """Object Correlation Quality value.

    Measures how close the observed object's orbit is to matching an object in the
    catalog. The scale of this field may vary depending on provider. Users should
    consult the data provider to verify the meaning of the value (e.g. A value of
    0.0 indicates a high/strong correlation, while a value closer to 1.0 indicates
    low/weak correlation).
    """

    end_time: Annotated[Union[str, datetime], PropertyInfo(alias="endTime", format="iso8601")]
    """Observation set detection end time in ISO 8601 UTC with microsecond precision."""

    gain: float
    """
    The gain used during the collection, in units of photoelectrons per
    analog-to-digital unit (e-/ADU). If no gain is used, the value = 1.
    """

    id_elset: Annotated[str, PropertyInfo(alias="idElset")]
    """ID of the UDL Elset of the Space Object under observation."""

    id_sensor: Annotated[str, PropertyInfo(alias="idSensor")]
    """ID of the observing sensor."""

    los_declination_end: Annotated[float, PropertyInfo(alias="losDeclinationEnd")]
    """Line of sight declination at observation set detection end time.

    Specified in degrees, in the specified referenceFrame. If referenceFrame is null
    then J2K should be assumed (e.g -30 to 130.0).
    """

    los_declination_start: Annotated[float, PropertyInfo(alias="losDeclinationStart")]
    """Line of sight declination at observation set detection start time.

    Specified in degrees, in the specified referenceFrame. If referenceFrame is null
    then J2K should be assumed (e.g -30 to 130.0).
    """

    msg_create_date: Annotated[Union[str, datetime], PropertyInfo(alias="msgCreateDate", format="iso8601")]
    """SOI msgCreateDate time in ISO 8601 UTC time, with millisecond precision."""

    num_spectral_filters: Annotated[int, PropertyInfo(alias="numSpectralFilters")]
    """The value is the number of spectral filters used."""

    optical_soi_observation_list: Annotated[
        Iterable[BodyOpticalSoiObservationList], PropertyInfo(alias="opticalSOIObservationList")
    ]
    """OpticalSOIObservations associated with this SOIObservationSet."""

    origin: str
    """
    Originating system or organization which produced the data, if different from
    the source. The origin may be different than the source if the source was a
    mediating system which forwarded the data on behalf of the origin system. If
    null, the source may be assumed to be the origin.
    """

    orig_object_id: Annotated[str, PropertyInfo(alias="origObjectId")]
    """
    Optional identifier provided by observation source to indicate the target
    onorbit object of this observation. This may be an internal identifier and not
    necessarily a valid satellite number.
    """

    orig_sensor_id: Annotated[str, PropertyInfo(alias="origSensorId")]
    """
    Optional identifier provided by the record source to indicate the sensor
    identifier to which this attitude set applies if this set is reporting a single
    sensor orientation. This may be an internal identifier and not necessarily a
    valid sensor ID.
    """

    percent_sat_threshold: Annotated[float, PropertyInfo(alias="percentSatThreshold")]
    """
    A threshold for percent of pixels that make up object signal that are beyond the
    saturation point for the sensor that are removed in the EOSSA file, in range of
    0 to 1.
    """

    periodicity_change_detected: Annotated[bool, PropertyInfo(alias="periodicityChangeDetected")]
    """
    Boolean indicating if a periodicity change event was detected, based on
    historical collection data for the object.
    """

    periodicity_detection_conf: Annotated[str, PropertyInfo(alias="periodicityDetectionConf")]
    """
    Qualitative assessment of the periodicity detection results from the Attitude
    and Shape Retrieval (ASR) Periodicity Assessment (PA) Tool (e.g. HIGH, MEDIUM,
    LOW).
    """

    periodicity_sampling_conf: Annotated[str, PropertyInfo(alias="periodicitySamplingConf")]
    """
    Qualitative Periodicity Sampling assessment, with respect to confidence of
    detecting a change event (e.g. HIGH, MEDIUM, LOW).
    """

    pixel_array_height: Annotated[int, PropertyInfo(alias="pixelArrayHeight")]
    """Pixel array size (height) in pixels."""

    pixel_array_width: Annotated[int, PropertyInfo(alias="pixelArrayWidth")]
    """Pixel array size (width) in pixels."""

    pixel_max: Annotated[int, PropertyInfo(alias="pixelMax")]
    """The maximum valid pixel value."""

    pixel_min: Annotated[int, PropertyInfo(alias="pixelMin")]
    """The minimum valid pixel value."""

    pointing_angle_az_end: Annotated[float, PropertyInfo(alias="pointingAngleAzEnd")]
    """Pointing angle of the Azimuth gimbal/mount at observation set detection end
    time.

    Specified in degrees.
    """

    pointing_angle_az_start: Annotated[float, PropertyInfo(alias="pointingAngleAzStart")]
    """
    Pointing angle of the Azimuth gimbal/mount at observation set detection start
    time. Specified in degrees.
    """

    pointing_angle_el_end: Annotated[float, PropertyInfo(alias="pointingAngleElEnd")]
    """
    Pointing angle of the Elevation gimbal/mount at observation set detection end
    time. Specified in degrees.
    """

    pointing_angle_el_start: Annotated[float, PropertyInfo(alias="pointingAngleElStart")]
    """
    Pointing angle of the Elevation gimbal/mount at observation set detection start
    time. Specified in degrees.
    """

    polar_angle_end: Annotated[float, PropertyInfo(alias="polarAngleEnd")]
    """
    Polar angle of the gimbal/mount at observation set detection end time in
    degrees.
    """

    polar_angle_start: Annotated[float, PropertyInfo(alias="polarAngleStart")]
    """
    Polar angle of the gimbal/mount at observation set detection start time in
    degrees.
    """

    radar_soi_observation_list: Annotated[
        Iterable[BodyRadarSoiObservationList], PropertyInfo(alias="radarSOIObservationList")
    ]
    """RadarSOIObservations associated with this RadarSOIObservationSet."""

    reference_frame: Annotated[
        Literal["J2000", "EFG/TDR", "ECR/ECEF", "TEME", "ITRF", "GCRF"], PropertyInfo(alias="referenceFrame")
    ]
    """The reference frame of the observation measurements.

    If the referenceFrame is null it is assumed to be J2000.
    """

    satellite_name: Annotated[str, PropertyInfo(alias="satelliteName")]
    """Name of the target satellite."""

    sat_no: Annotated[int, PropertyInfo(alias="satNo")]
    """Satellite/catalog number of the target on-orbit object."""

    senalt: float
    """Sensor altitude at startTime (if mobile/onorbit) in kilometers."""

    senlat: float
    """Sensor WGS84 latitude at startTime (if mobile/onorbit) in degrees.

    If null, can be obtained from sensor info. -90 to 90 degrees (negative values
    south of equator).
    """

    senlon: float
    """Sensor WGS84 longitude at startTime (if mobile/onorbit) in degrees.

    If null, can be obtained from sensor info. -180 to 180 degrees (negative values
    south of equator).
    """

    sen_reference_frame: Annotated[
        Literal["J2000", "EFG/TDR", "ECR/ECEF", "TEME", "ITRF", "GCRF"], PropertyInfo(alias="senReferenceFrame")
    ]
    """The reference frame of the observing sensor state.

    If the senReferenceFrame is null it is assumed to be J2000.
    """

    sensor_as_id: Annotated[str, PropertyInfo(alias="sensorAsId")]
    """ID of the AttitudeSet record for the observing sensor."""

    senvelx: float
    """
    Cartesian X velocity of the observing mobile/onorbit sensor at startTime, in
    kilometers per second, in the specified senReferenceFrame. If senReferenceFrame
    is null then J2K should be assumed.
    """

    senvely: float
    """
    Cartesian Y velocity of the observing mobile/onorbit sensor at startTime, in
    kilometers per second, in the specified senReferenceFrame. If senReferenceFrame
    is null then J2K should be assumed.
    """

    senvelz: float
    """
    Cartesian Z velocity of the observing mobile/onorbit sensor at startTime, in
    kilometers per second, in the specified senReferenceFrame. If senReferenceFrame
    is null then J2K should be assumed.
    """

    senx: float
    """
    Cartesian X position of the observing mobile/onorbit sensor at startTime, in
    kilometers, in the specified senReferenceFrame. If senReferenceFrame is null
    then J2K should be assumed.
    """

    seny: float
    """
    Cartesian Y position of the observing mobile/onorbit sensor at startTime, in
    kilometers, in the specified senReferenceFrame. If senReferenceFrame is null
    then J2K should be assumed.
    """

    senz: float
    """
    Cartesian Z position of the observing mobile/onorbit sensor at startTime, in
    kilometers, in the specified senReferenceFrame. If senReferenceFrame is null
    then J2K should be assumed.
    """

    software_version: Annotated[str, PropertyInfo(alias="softwareVersion")]
    """Software Version used to Capture, Process, and Deliver the data."""

    solar_mag: Annotated[float, PropertyInfo(alias="solarMag")]
    """The in-band solar magnitude at 1 A.U."""

    solar_phase_angle_brightness_change_detected: Annotated[
        bool, PropertyInfo(alias="solarPhaseAngleBrightnessChangeDetected")
    ]
    """
    Boolean indicating if a solar phase angle brightness change event was detected,
    based on historical collection data for the object.
    """

    spectral_filters: Annotated[SequenceNotStr[str], PropertyInfo(alias="spectralFilters")]
    """
    Array of the SpectralFilters keywords, must be present for all values n=1 to
    numSpectralFilters, in incrementing order of n, and for no other values of n.
    """

    star_cat_name: Annotated[str, PropertyInfo(alias="starCatName")]
    """Name of the Star Catalog used for photometry and astrometry."""

    tags: SequenceNotStr[str]
    """
    Optional array of provider/source specific tags for this data, where each
    element is no longer than 32 characters, used for implementing data owner
    conditional access controls to restrict access to the data. Should be left null
    by data providers unless conditional access controls are coordinated with the
    UDL team.
    """

    transaction_id: Annotated[str, PropertyInfo(alias="transactionId")]
    """
    Optional identifier to track a commercial or marketplace transaction executed to
    produce this data.
    """

    uct: bool
    """
    Boolean indicating whether the target object was unable to be correlated to a
    known object. This flag should only be set to true by data providers after an
    attempt to correlate to an OnOrbit object was made and failed. If unable to
    correlate, the 'origObjectId' field may be populated with an internal data
    provider specific identifier.
    """

    valid_calibrations: Annotated[str, PropertyInfo(alias="validCalibrations")]
    """
    Key to indicate which, if any of, the pre/post photometer calibrations are valid
    for use when generating data for the EOSSA file. If the field is not populated,
    then the provided calibration data will be used when generating the EOSSA file
    (e.g. PRE, POST, BOTH, NONE).
    """
