"""Ground station model for line-of-sight calculations."""

import math

from pydantic import BaseModel

# Earth radius in km
R_EARTH_KM = 6378.137


class GroundStation(BaseModel):
    """A ground station for satellite communication."""

    id: str
    name: str

    # Geodetic coordinates
    latitude_deg: float  # -90 to +90
    longitude_deg: float  # -180 to +180
    altitude_m: float  # Altitude above sea level

    # Antenna constraints
    min_elevation_deg: float = 5.0  # Minimum elevation angle for contact

    # Operational status
    is_active: bool = True

    def get_ecef_position(self) -> tuple[float, float, float]:
        """Convert geodetic coordinates to ECEF (km).

        Uses WGS-84 ellipsoid approximation (simplified as sphere for hackathon).
        """
        lat_rad = math.radians(self.latitude_deg)
        lon_rad = math.radians(self.longitude_deg)

        r = R_EARTH_KM + (self.altitude_m / 1000.0)

        x = r * math.cos(lat_rad) * math.cos(lon_rad)
        y = r * math.cos(lat_rad) * math.sin(lon_rad)
        z = r * math.sin(lat_rad)

        return (x, y, z)

    def get_eci_position(self, sim_time_seconds: float) -> tuple[float, float, float]:
        """Convert to ECI coordinates given simulation time.

        Accounts for Earth rotation (simplified model).

        Args:
            sim_time_seconds: Simulation time since epoch

        Returns:
            Tuple of (x, y, z) in km in ECI frame
        """
        # Earth rotation rate (rad/s)
        OMEGA_EARTH = 7.2921159e-5

        # ECEF position
        x_ecef, y_ecef, z_ecef = self.get_ecef_position()

        # Rotate by Earth's rotation since simulation start
        theta = OMEGA_EARTH * sim_time_seconds

        # Rotation from ECEF to ECI
        x_eci = x_ecef * math.cos(theta) - y_ecef * math.sin(theta)
        y_eci = x_ecef * math.sin(theta) + y_ecef * math.cos(theta)
        z_eci = z_ecef

        return (x_eci, y_eci, z_eci)
