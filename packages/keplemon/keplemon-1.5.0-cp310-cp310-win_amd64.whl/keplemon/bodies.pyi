# flake8: noqa
from keplemon.elements import (
    TLE,
    CartesianState,
    Ephemeris,
    KeplerianState,
    GeodeticPosition,
    OrbitPlotData,
    TopocentricElements,
    RelativeState,
    BoreToBodyAngles,
)
from keplemon.catalogs import TLECatalog
from keplemon.time import Epoch, TimeSpan
from keplemon.events import CloseApproach, CloseApproachReport, HorizonAccessReport, FieldOfViewReport
from keplemon.propagation import ForceProperties
from keplemon.enums import ReferenceFrame

class Earth:
    @staticmethod
    def get_equatorial_radius() -> float:
        """
        Returns:
            Equatorial radius of the Earth in kilometers
        """
        ...

    @staticmethod
    def get_kem() -> float: ...

class Satellite:

    id: str
    """Unique identifier for the satellite."""

    norad_id: int
    """Number corresponding to the satellite's NORAD catalog ID.
    """

    force_properties: ForceProperties
    """Force properties of the satellite used for propagation"""

    name: str | None
    """Human-readable name of the satellite"""

    keplerian_state: KeplerianState | None
    """Keplerian state of the satellite at the epoch of the TLE, if available"""

    geodetic_position: GeodeticPosition | None
    """Geodetic position of the satellite at the epoch of the TLE, if available"""

    def __init__(self) -> None: ...
    @classmethod
    def from_tle(cls, tle: TLE) -> Satellite:
        """
        Instantiate a Satellite from a legacy TLE

        Args:
            tle: Two-line element set for the satellite
        """
        ...

    def get_close_approach(
        self,
        other: Satellite,
        start: Epoch,
        end: Epoch,
        distance_threshold: float,
    ) -> None | CloseApproach: ...
    def get_ephemeris(
        self,
        start: Epoch,
        end: Epoch,
        step: TimeSpan,
    ) -> Ephemeris: ...
    def get_state_at_epoch(self, epoch: Epoch) -> CartesianState: ...
    def to_tle(self) -> TLE | None:
        """
        Returns:
            Satellite as a two-line element set or None if no state is loaded

        """
        ...

    def get_relative_state_at_epoch(self, other: Satellite, epoch: Epoch) -> RelativeState | None:
        """
        Calculate the relative state between this satellite and another satellite at a given epoch.

        Args:
            other: Secondary satellite to calculate the relative state against
            epoch: UTC epoch at which the relative state will be calculated
        """
        ...

    def get_body_angles_at_epoch(self, other: Satellite, epoch: Epoch) -> BoreToBodyAngles | None:
        """
        Calculate the bore-to-body angles between this satellite and another satellite at a given epoch.

        Args:
            other: Secondary satellite to calculate the bore-to-body angles against
            epoch: UTC epoch at which the bore-to-body angles will be calculated
        """
        ...

    def get_plot_data(self, start: Epoch, end: Epoch, step: TimeSpan) -> OrbitPlotData | None: ...
    def get_observatory_access_report(
        self,
        observatories: list[Observatory],
        start: Epoch,
        end: Epoch,
        min_el: float,
        min_duration: TimeSpan,
    ) -> HorizonAccessReport | None:
        """
        Calculate horizon access from multiple observatories to this satellite.

        Args:
            observatories: List of observatories to check for horizon access
            start: UTC epoch of the start of the report
            end: UTC epoch of the end of the report
            min_el: Minimum elevation angle in **_degrees_**
            min_duration: Minimum duration of access

        Returns:
            Horizon access report containing accesses from all observatories to the satellite,
            or None if the satellite ephemeris cannot be generated
        """
        ...

class Constellation:

    count: int
    """Number of satellites in the constellation"""

    name: str | None
    """Human-readable name of the constellation"""

    def __init__(self) -> None: ...
    def get_plot_data(self, start: Epoch, end: Epoch, step: TimeSpan) -> dict[str, OrbitPlotData]: ...
    @classmethod
    def from_tle_catalog(cls, tle_catalog: TLECatalog) -> Constellation:
        """
        Instantiate a Constellation from a TLE catalog

        Args:
            tle_catalog: TLE catalog for the constellation
        """
        ...

    def get_states_at_epoch(self, epoch: Epoch) -> dict[int, CartesianState]:
        """
        Args:
            epoch: UTC epoch at which the states will be calculated

        Returns:
            (satellite_id, state) dictionary for the constellation at the given epoch
        """
        ...

    def get_ephemeris(
        self,
        start: Epoch,
        end: Epoch,
        step: TimeSpan,
    ) -> dict[str, Ephemeris]:
        """
        Args:
            start: UTC epoch of the start of the ephemeris
            end: UTC epoch of the end of the ephemeris
            step: Time step for the ephemeris

        Returns:
            (satellite_id, ephemeris) dictionary for the constellation
        """
        ...

    def get_ca_report_vs_one(
        self,
        other: Satellite,
        start: Epoch,
        end: Epoch,
        distance_threshold: float,
    ) -> CloseApproachReport:
        """
        Calculate close approaches between the constellation and a given satellite.

        Args:
            other: Satellite to compare against
            start: UTC epoch of the start of the close approach report
            end: UTC epoch of the end of the close approach report
            distance_threshold: Distance threshold for close approach screening in **_kilometers_**

        Returns:
            Close approach report for the constellation vs. the given satellite
        """
        ...

    def get_ca_report_vs_many(
        self,
        start: Epoch,
        end: Epoch,
        distance_threshold: float,
    ) -> CloseApproachReport:
        """
        Calculate close approaches among satellites in the calling constellation.

        !!! warning
            This is a long-running operation when the constellation is large.

        Args:
            start: UTC epoch of the start of the close approach report
            end: UTC epoch of the end of the close approach report
            distance_threshold: Distance threshold for close approach screening in **_kilometers_**

        Returns:
            Close approach report for the constellation vs. all other satellites
        """
        ...

    def __getitem__(self, satellite_id: str) -> Satellite: ...
    def __setitem__(self, satellite_id: str, sat: Satellite) -> None: ...
    def get_horizon_access_report(
        self,
        site: Observatory,
        start: Epoch,
        end: Epoch,
        min_el: float,
        min_duration: TimeSpan,
    ) -> HorizonAccessReport:
        """
        Calculate horizon access to a given observatory.

        Args:
            site: Observatory to check for horizon access
            start: UTC epoch of the start of the report
            end: UTC epoch of the end of the report
            min_el: Minimum elevation angle in **_degrees_**
            min_duration: Minimum duration of access

        Returns:
            Horizon access report for the constellation from the observatory
        """
        ...

class Sensor:
    """
    Args:
        name: Identifier of the sensor
        angular_noise: Angular noise in **_degrees_**
    """

    id: str
    """Unique identifier for the sensor."""
    name: str | None
    angular_noise: float
    range_noise: float | None
    """Range noise in **_kilometers_**"""

    range_rate_noise: float | None
    """Range rate noise in **_kilometers per second_**"""

    angular_rate_noise: float | None
    """Angular rate noise in **_degrees per second_**"""
    def __init__(self, angular_noise: float) -> None: ...

class Observatory:
    """
    Args:
        latitude: Latitude in **_degrees_**
        longitude: Longitude in **_degrees_**
        altitude: Altitude in **_kilometers_**
    """

    name: str
    id: str
    """Unique identifier for the observatory."""
    latitude: float
    longitude: float
    altitude: float
    sensors: list[Sensor]
    """List of sensors at the observatory"""
    def __init__(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
    ) -> None: ...
    def get_state_at_epoch(self, epoch: Epoch) -> CartesianState:
        """
        Args:
            epoch: UTC epoch of the state

        Returns:
            TEME Cartesian state of the observatory in **_kilometers_** and **_kilometers per second_**
        """
        ...

    @classmethod
    def from_cartesian_state(cls, state: CartesianState) -> Observatory:
        """
        Create an observatory from a Cartesian state.

        Args:
            state: Cartesian state of the observatory

        """
        ...

    def get_horizon_access_report(
        self,
        satellite: Satellite,
        start: Epoch,
        end: Epoch,
        min_el: float,
        min_duration: TimeSpan,
    ) -> HorizonAccessReport:
        """
        Calculate horizon access for a satellite from the observatory.

        Args:
            satellite: Satellite to check for horizon access
            start: UTC epoch of the start of the report
            end: UTC epoch of the end of the report
            min_el: Minimum elevation angle in **_degrees_**
            min_duration: Minimum duration of access in **_seconds_**

        Returns:
            Horizon access report for the satellite from the observatory
        """
        ...

    def get_field_of_view_report(
        self,
        epoch: Epoch,
        sensor_direction: TopocentricElements,
        angular_threshold: float,
        sats: Constellation,
        reference_frame: ReferenceFrame,
    ) -> FieldOfViewReport:
        """
        Calculate satellites in the field of view from a given time and direction.

        Args:
            epoch: UTC epoch of the report
            sensor_direction: Topocentric direction the sensor is pointing
            angular_threshold: Angular threshold in **_degrees_**
            sats: Constellation of satellites to check for being in the field of view
            reference_frame: Reference frame of the output direction elements
        """
        ...

    def get_topocentric_to_satellite(
        self,
        epoch: Epoch,
        sat: Satellite,
        reference_frame: ReferenceFrame,
    ) -> TopocentricElements:
        """
        Get the topocentric elements of a satellite as seen from the observatory.
        Args:
            epoch: UTC epoch of the observation
            sat: Satellite to observe
            reference_frame: Reference frame of the output direction elements
        """
        ...
