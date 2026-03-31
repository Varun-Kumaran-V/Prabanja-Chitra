"""Ground station visibility calculations for satellite communication.

Implements line-of-sight (LOS) constraints for command uplink scheduling.
"""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.models.ground_station import GroundStation
from app.models import StateVector

# Constants
R_EARTH_KM = 6378.137
OMEGA_EARTH = 7.2921159e-5  # Earth rotation rate (rad/s)


@dataclass
class ContactWindow:
    """A period when a satellite is visible from a ground station."""

    station_id: str
    satellite_id: str
    start_time: float  # Simulation time
    end_time: float  # Simulation time
    max_elevation_deg: float  # Peak elevation during pass
    aos_azimuth_deg: float  # Acquisition of Signal azimuth
    los_azimuth_deg: float  # Loss of Signal azimuth

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time


@dataclass
class VisibilityResult:
    """Result of a visibility check at a specific time."""

    is_visible: bool
    elevation_deg: float
    azimuth_deg: float
    range_km: float
    station_id: str


def _compute_station_eci(station: GroundStation, sim_time: float) -> np.ndarray:
    """Get ground station position in ECI frame at given simulation time."""
    x, y, z = station.get_eci_position(sim_time)
    return np.array([x, y, z])


def _compute_topocentric(
    sat_eci: np.ndarray,
    station_eci: np.ndarray,
    station_lat_rad: float,
    station_lon_rad: float,
    theta_gmst: float,
) -> tuple[float, float, float]:
    """Compute topocentric coordinates (elevation, azimuth, range).

    Args:
        sat_eci: Satellite position in ECI (km)
        station_eci: Station position in ECI (km)
        station_lat_rad: Station latitude (radians)
        station_lon_rad: Station longitude (radians)
        theta_gmst: Greenwich Mean Sidereal Time angle (radians)

    Returns:
        Tuple of (elevation_deg, azimuth_deg, range_km)
    """
    # Range vector from station to satellite (ECI)
    rho_eci = sat_eci - station_eci
    range_km = np.linalg.norm(rho_eci)

    if range_km < 1e-6:
        return 90.0, 0.0, 0.0

    # Local sidereal time at station
    lst = theta_gmst + station_lon_rad

    # Rotation matrix from ECI to topocentric (SEZ: South-East-Zenith)
    sin_lat = math.sin(station_lat_rad)
    cos_lat = math.cos(station_lat_rad)
    sin_lst = math.sin(lst)
    cos_lst = math.cos(lst)

    # SEZ components
    # S (South) = -cos(lat)*cos(lst)*x - cos(lat)*sin(lst)*y + sin(lat)*z
    # E (East)  = -sin(lst)*x + cos(lst)*y
    # Z (Zenith)= cos(lat)*cos(lst)*(-sin(lat)) + ... simplified:

    # Transform to topocentric
    rho_s = (
        sin_lat * cos_lst * rho_eci[0]
        + sin_lat * sin_lst * rho_eci[1]
        - cos_lat * rho_eci[2]
    )
    rho_e = -sin_lst * rho_eci[0] + cos_lst * rho_eci[1]
    rho_z = (
        cos_lat * cos_lst * rho_eci[0]
        + cos_lat * sin_lst * rho_eci[1]
        + sin_lat * rho_eci[2]
    )

    # Elevation
    elevation_rad = math.asin(rho_z / range_km)
    elevation_deg = math.degrees(elevation_rad)

    # Azimuth (measured clockwise from North)
    azimuth_rad = math.atan2(rho_e, -rho_s)
    azimuth_deg = math.degrees(azimuth_rad)
    if azimuth_deg < 0:
        azimuth_deg += 360.0

    return elevation_deg, azimuth_deg, range_km


class GroundStationVisibility:
    """Calculates satellite visibility from ground stations."""

    def __init__(self, stations: list[GroundStation]):
        self.stations: dict[str, GroundStation] = {s.id: s for s in stations}

    def add_station(self, station: GroundStation) -> None:
        """Add a ground station."""
        self.stations[station.id] = station

    def remove_station(self, station_id: str) -> bool:
        """Remove a ground station."""
        if station_id in self.stations:
            del self.stations[station_id]
            return True
        return False

    def check_visibility(
        self,
        satellite_state: StateVector,
        station_id: str,
        sim_time: float,
    ) -> Optional[VisibilityResult]:
        """Check if a satellite is visible from a specific ground station.

        Args:
            satellite_state: Current satellite state vector (ECI)
            station_id: ID of the ground station
            sim_time: Current simulation time

        Returns:
            VisibilityResult if station exists, None otherwise
        """
        station = self.stations.get(station_id)
        if station is None or not station.is_active:
            return None

        sat_eci = np.array([satellite_state.x, satellite_state.y, satellite_state.z])
        station_eci = _compute_station_eci(station, sim_time)

        # GMST (simplified: assume sim_time starts at 0 GMST)
        theta_gmst = OMEGA_EARTH * sim_time

        lat_rad = math.radians(station.latitude_deg)
        lon_rad = math.radians(station.longitude_deg)

        elevation_deg, azimuth_deg, range_km = _compute_topocentric(
            sat_eci, station_eci, lat_rad, lon_rad, theta_gmst
        )

        is_visible = elevation_deg >= station.min_elevation_deg

        return VisibilityResult(
            is_visible=is_visible,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            range_km=range_km,
            station_id=station_id,
        )

    def find_visible_stations(
        self,
        satellite_state: StateVector,
        sim_time: float,
    ) -> list[VisibilityResult]:
        """Find all ground stations that can see the satellite.

        Returns:
            List of VisibilityResult for visible stations, sorted by elevation (highest first)
        """
        visible = []

        for station_id in self.stations:
            result = self.check_visibility(satellite_state, station_id, sim_time)
            if result and result.is_visible:
                visible.append(result)

        # Sort by elevation (prefer higher elevation for better link)
        visible.sort(key=lambda v: v.elevation_deg, reverse=True)

        return visible

    def has_line_of_sight(
        self,
        satellite_state: StateVector,
        sim_time: float,
    ) -> bool:
        """Check if satellite has LOS to any ground station."""
        return len(self.find_visible_stations(satellite_state, sim_time)) > 0

    def get_best_station(
        self,
        satellite_state: StateVector,
        sim_time: float,
    ) -> Optional[VisibilityResult]:
        """Get the best (highest elevation) visible ground station."""
        visible = self.find_visible_stations(satellite_state, sim_time)
        return visible[0] if visible else None

    def predict_next_contact(
        self,
        satellite_state: StateVector,
        sim_time: float,
        max_lookahead_seconds: float = 7200.0,  # 2 hours
        step_seconds: float = 60.0,
    ) -> Optional[ContactWindow]:
        """Predict the next available contact window for a satellite.

        Uses simple propagation to find when satellite will be visible.

        Args:
            satellite_state: Current state vector
            sim_time: Current simulation time
            max_lookahead_seconds: How far ahead to search
            step_seconds: Time step for search

        Returns:
            Next ContactWindow or None if no contact within lookahead
        """
        from app.core.orbit_propagator import orbit_propagator

        # First check if we're already in contact
        visible = self.find_visible_stations(satellite_state, sim_time)
        if visible:
            # Find when this contact ends
            best = visible[0]
            start_time = sim_time
            max_elev = best.elevation_deg
            aos_az = best.azimuth_deg

            current_state = satellite_state
            t = 0.0
            while t < max_lookahead_seconds:
                dt = step_seconds
                t += dt
                current_state = orbit_propagator.propagate(current_state, dt)
                result = self.check_visibility(current_state, best.station_id, sim_time + t)

                if result:
                    if result.elevation_deg > max_elev:
                        max_elev = result.elevation_deg
                    if not result.is_visible:
                        return ContactWindow(
                            station_id=best.station_id,
                            satellite_id="",  # Caller should fill this
                            start_time=start_time,
                            end_time=sim_time + t,
                            max_elevation_deg=max_elev,
                            aos_azimuth_deg=aos_az,
                            los_azimuth_deg=result.azimuth_deg,
                        )

            # Still visible at end of lookahead
            return ContactWindow(
                station_id=best.station_id,
                satellite_id="",
                start_time=start_time,
                end_time=sim_time + max_lookahead_seconds,
                max_elevation_deg=max_elev,
                aos_azimuth_deg=aos_az,
                los_azimuth_deg=best.azimuth_deg,
            )

        # Not in contact - find next AOS
        current_state = satellite_state
        t = 0.0
        while t < max_lookahead_seconds:
            dt = step_seconds
            t += dt
            current_state = orbit_propagator.propagate(current_state, dt)

            visible = self.find_visible_stations(current_state, sim_time + t)
            if visible:
                # Found AOS, now find LOS
                best = visible[0]
                start_time = sim_time + t
                max_elev = best.elevation_deg
                aos_az = best.azimuth_deg

                while t < max_lookahead_seconds:
                    dt = step_seconds
                    t += dt
                    current_state = orbit_propagator.propagate(current_state, dt)
                    result = self.check_visibility(
                        current_state, best.station_id, sim_time + t
                    )

                    if result:
                        if result.elevation_deg > max_elev:
                            max_elev = result.elevation_deg
                        if not result.is_visible:
                            return ContactWindow(
                                station_id=best.station_id,
                                satellite_id="",
                                start_time=start_time,
                                end_time=sim_time + t,
                                max_elevation_deg=max_elev,
                                aos_azimuth_deg=aos_az,
                                los_azimuth_deg=result.azimuth_deg,
                            )

                # Still visible at end of lookahead
                return ContactWindow(
                    station_id=best.station_id,
                    satellite_id="",
                    start_time=start_time,
                    end_time=sim_time + max_lookahead_seconds,
                    max_elevation_deg=max_elev,
                    aos_azimuth_deg=aos_az,
                    los_azimuth_deg=best.azimuth_deg,
                )

        return None


# Default ground stations (major space agency facilities)
DEFAULT_GROUND_STATIONS = [
    GroundStation(
        id="GS-CANBERRA",
        name="Canberra DSN",
        latitude_deg=-35.4016,
        longitude_deg=148.9819,
        altitude_m=680,
        min_elevation_deg=5.0,
    ),
    GroundStation(
        id="GS-GOLDSTONE",
        name="Goldstone DSN",
        latitude_deg=35.4267,
        longitude_deg=-116.89,
        altitude_m=900,
        min_elevation_deg=5.0,
    ),
    GroundStation(
        id="GS-MADRID",
        name="Madrid DSN",
        latitude_deg=40.4294,
        longitude_deg=-3.9544,
        altitude_m=750,
        min_elevation_deg=5.0,
    ),
    GroundStation(
        id="GS-SVALBARD",
        name="Svalbard SvalSat",
        latitude_deg=78.2292,
        longitude_deg=15.3978,
        altitude_m=466,
        min_elevation_deg=3.0,
    ),
    GroundStation(
        id="GS-MCMURDO",
        name="McMurdo MGS",
        latitude_deg=-77.8419,
        longitude_deg=166.6686,
        altitude_m=10,
        min_elevation_deg=5.0,
    ),
]

# Singleton instance with default stations
ground_station_visibility = GroundStationVisibility(DEFAULT_GROUND_STATIONS)
