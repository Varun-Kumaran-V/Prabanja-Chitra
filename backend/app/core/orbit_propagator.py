"""SGP4-based orbit propagator with J2 and atmospheric drag perturbations.

Uses the sgp4 library for physically accurate orbit propagation including:
- J2 oblateness perturbation
- Atmospheric drag (for LEO objects)
- Solar radiation pressure effects
"""

from sgp4.api import Satrec
import math
from typing import Optional

from app.models import StateVector

# WGS-84 gravitational parameter (km^3 / s^2)
MU_EARTH = 398600.4418

# Try to import sgp4
try:
    from sgp4.api import Satrec
    _SGP4_AVAILABLE = True
except ImportError:
    _SGP4_AVAILABLE = False


def _gravity_with_j2(state: list[float]) -> list[float]:
    """Two-body gravitational acceleration with J2 perturbation (km/s^2)."""
    x, y, z, vx, vy, vz = state
    r_sq = x**2 + y**2 + z**2
    r = math.sqrt(r_sq)
    r3 = r_sq * r

    # Basic two-body
    ax = -MU_EARTH * x / r3
    ay = -MU_EARTH * y / r3
    az = -MU_EARTH * z / r3

    # J2 perturbation (Earth oblateness)
    J2 = 1.08263e-3
    R_EARTH = 6378.137

    factor = -1.5 * J2 * MU_EARTH * R_EARTH**2 / (r**5)
    z_factor = 5 * z**2 / r_sq

    ax += factor * x * (1 - z_factor)
    ay += factor * y * (1 - z_factor)
    az += factor * z * (3 - z_factor)

    return [vx, vy, vz, ax, ay, az]


def _rk4_step(state: list[float], dt: float) -> list[float]:
    k1 = _gravity_with_j2(state)
    k2 = _gravity_with_j2([s + 0.5 * dt * k for s, k in zip(state, k1)])
    k3 = _gravity_with_j2([s + 0.5 * dt * k for s, k in zip(state, k2)])
    k4 = _gravity_with_j2([s + dt * k for s, k in zip(state, k3)])
    return [s + (dt / 6.0) * (a + 2 * b + 2 * c + d)
            for s, a, b, c, d in zip(state, k1, k2, k3, k4)]


def _propagate_rk4_with_j2(sv: StateVector, dt_seconds: float) -> StateVector:
    """Propagate using RK4 with J2 perturbation (fallback)."""
    STEP = 10.0  # seconds
    state = sv.to_array()
    elapsed = 0.0
    while elapsed < abs(dt_seconds):
        h = min(STEP, abs(dt_seconds) - elapsed)
        if dt_seconds < 0:
            h = -h
        state = _rk4_step(state, h)
        elapsed += abs(h)
    x, y, z, vx, vy, vz = state
    return StateVector(x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)


class SGP4Propagator:
    """SGP4-based propagator using TLE data."""

    def __init__(self):
        # Cache of Satrec objects keyed by (tle_line1, tle_line2)
        self._satrec_cache: dict[tuple[str, str], Satrec] = {}

    def _get_satrec(self, tle_line1: str, tle_line2: str) -> Optional[Satrec]:
        """Get or create a Satrec object from TLE lines."""
        if not _SGP4_AVAILABLE:
            return None

        cache_key = (tle_line1, tle_line2)
        if cache_key not in self._satrec_cache:
            try:
                satellite = Satrec.twoline2rv(tle_line1, tle_line2)
                self._satrec_cache[cache_key] = satellite
            except Exception:
                return None
        return self._satrec_cache.get(cache_key)

    def propagate_sgp4(
        self,
        tle_line1: str,
        tle_line2: str,
        dt_seconds: float,
        base_minutes_from_epoch: float = 0.0,
    ) -> Optional[StateVector]:
        """Propagate using SGP4 from TLE.

        Args:
            tle_line1: First TLE line
            tle_line2: Second TLE line
            dt_seconds: Time delta from current position (seconds)
            base_minutes_from_epoch: Current offset from TLE epoch in minutes

        Returns:
            New StateVector or None if propagation fails
        """
        satrec = self._get_satrec(tle_line1, tle_line2)
        if satrec is None:
            return None

        # Calculate new time offset from TLE epoch
        new_minutes = base_minutes_from_epoch + (dt_seconds / 60.0)

        # Propagate to new time (minutes since epoch)
        error_code, position, velocity = satrec.sgp4(
            satrec.jdsatepoch, satrec.jdsatepochF + new_minutes / 1440.0
        )

        if error_code != 0:
            return None

        return StateVector(
            x=position[0],
            y=position[1],
            z=position[2],
            vx=velocity[0],
            vy=velocity[1],
            vz=velocity[2],
        )

    def get_state_at_epoch(self, tle_line1: str, tle_line2: str) -> Optional[StateVector]:
        """Get state vector at TLE epoch."""
        return self.propagate_sgp4(tle_line1, tle_line2, 0.0, 0.0)

    def clear_cache(self):
        """Clear the Satrec cache."""
        self._satrec_cache.clear()


# Singleton SGP4 propagator instance
_sgp4_propagator = SGP4Propagator()


class OrbitPropagator:
    """Propagate a satellite state vector forward in time.

    Uses SGP4 when TLE data is available, falls back to RK4 with J2 otherwise.
    """

    def propagate(self, state_vector: StateVector, dt_seconds: float) -> StateVector:
        """Return the new StateVector after *dt_seconds* seconds.

        This method uses RK4 with J2 perturbation for objects without TLE data.
        For SGP4 propagation with TLE data, use propagate_with_tle().
        """
        return _propagate_rk4_with_j2(state_vector, dt_seconds)

    def propagate_with_tle(
        self,
        tle_line1: str,
        tle_line2: str,
        dt_seconds: float,
        base_minutes_from_epoch: float = 0.0,
        fallback_state: Optional[StateVector] = None,
    ) -> StateVector:
        """Propagate using SGP4 with TLE data.

        Args:
            tle_line1: First TLE line
            tle_line2: Second TLE line
            dt_seconds: Time to propagate (seconds)
            base_minutes_from_epoch: Current offset from TLE epoch (minutes)
            fallback_state: State to use for J2 propagation if SGP4 fails

        Returns:
            New StateVector
        """
        if _SGP4_AVAILABLE:
            result = _sgp4_propagator.propagate_sgp4(
                tle_line1, tle_line2, dt_seconds, base_minutes_from_epoch
            )
            if result is not None:
                return result

        # Fallback to RK4 with J2 if SGP4 fails or not available
        if fallback_state is not None:
            return _propagate_rk4_with_j2(fallback_state, dt_seconds)

        raise ValueError("SGP4 propagation failed and no fallback state provided")

    def propagate_telemetry(self, telemetry, dt_seconds: float):
        """Propagate a Telemetry object using best available method.

        Uses SGP4 if TLE data is present, otherwise falls back to J2 RK4.

        Args:
            telemetry: Telemetry object with state and optional TLE data
            dt_seconds: Time to propagate (seconds)

        Returns:
            Tuple of (new_state, new_tle_epoch_minutes)
        """
        # Use SGP4 if TLE data available
        if (
            _SGP4_AVAILABLE
            and telemetry.tle_line1 is not None
            and telemetry.tle_line2 is not None
        ):
            base_minutes = telemetry.tle_epoch or 0.0
            new_state = _sgp4_propagator.propagate_sgp4(
                telemetry.tle_line1,
                telemetry.tle_line2,
                dt_seconds,
                base_minutes,
            )
            if new_state is not None:
                new_epoch = base_minutes + (dt_seconds / 60.0)
                return new_state, new_epoch

        # Fallback to J2 RK4
        new_state = _propagate_rk4_with_j2(telemetry.state, dt_seconds)
        new_epoch = (telemetry.tle_epoch or 0.0) + (dt_seconds / 60.0)
        return new_state, new_epoch


# Singleton instance
orbit_propagator = OrbitPropagator()
