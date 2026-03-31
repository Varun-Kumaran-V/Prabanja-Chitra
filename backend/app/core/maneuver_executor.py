"""Maneuver executor with Tsiolkovsky rocket equation for fuel depletion.

Applies impulsive maneuvers to satellite states and tracks fuel consumption
using the classical rocket equation.
"""

import math
from dataclasses import dataclass
from typing import Optional

from app.models import Maneuver, Satellite, StateVector, Telemetry

# Hard safety cap (m/s)
MAX_DELTA_V_MS = 15.0

# Default exhaust velocity (hydrazine monoprop, Isp ~220s)
DEFAULT_EXHAUST_VELOCITY_MS = 2157.0


@dataclass
class ManeuverResult:
    """Result of maneuver execution."""

    success: bool
    new_state: Optional[StateVector]
    fuel_consumed_kg: float
    new_fuel_mass_kg: float
    actual_delta_v_ms: float
    error_message: Optional[str] = None


class ManeuverExecutor:
    """Applies impulsive maneuvers to satellite states with fuel tracking."""

    def apply_maneuver(
        self, satellite: Telemetry, maneuver: Maneuver
    ) -> StateVector:
        """Return a new StateVector with the burn applied.

        Legacy interface for compatibility. Does not track fuel.

        The *delta_v* on the Maneuver is in **m/s**; internally it is
        converted to km/s before being added to the velocity components.

        Raises
        ------
        ValueError
            If ``maneuver.delta_v`` exceeds the safety cap.
        """
        if maneuver.delta_v > MAX_DELTA_V_MS:
            raise ValueError(
                f"delta_v {maneuver.delta_v} m/s exceeds safety cap "
                f"of {MAX_DELTA_V_MS} m/s"
            )

        return self._apply_delta_v(satellite.state, maneuver.delta_v, maneuver.direction)

    def execute_maneuver_with_fuel(
        self,
        satellite: Telemetry,
        sat_metadata: Satellite,
        maneuver: Maneuver,
    ) -> ManeuverResult:
        """Execute a maneuver with proper fuel tracking using Tsiolkovsky equation.

        The Tsiolkovsky rocket equation:
            delta_v = V_e * ln(m_0 / m_1)

        Where:
            V_e = exhaust velocity
            m_0 = initial mass (before burn)
            m_1 = final mass (after burn)

        Solving for fuel consumed:
            m_fuel = m_0 * (1 - exp(-delta_v / V_e))

        Args:
            satellite: Current satellite telemetry
            sat_metadata: Satellite metadata with mass and fuel info
            maneuver: The maneuver to execute

        Returns:
            ManeuverResult with new state and fuel consumption
        """
        # Validate delta-v
        if maneuver.delta_v > MAX_DELTA_V_MS:
            return ManeuverResult(
                success=False,
                new_state=None,
                fuel_consumed_kg=0.0,
                new_fuel_mass_kg=sat_metadata.fuel_mass,
                actual_delta_v_ms=0.0,
                error_message=f"Delta-v {maneuver.delta_v:.2f} m/s exceeds max {MAX_DELTA_V_MS} m/s",
            )

        # Calculate fuel required using Tsiolkovsky equation
        v_exhaust = sat_metadata.exhaust_velocity_ms
        m_initial = sat_metadata.total_mass  # dry_mass + fuel_mass

        # mass_ratio = m_0 / m_1 = exp(delta_v / v_e)
        # fuel = m_0 - m_1 = m_0 * (1 - 1/mass_ratio)
        mass_ratio = math.exp(maneuver.delta_v / v_exhaust)
        fuel_required = m_initial * (1 - 1 / mass_ratio)

        # Check fuel availability (accounting for reserve)
        available_fuel = sat_metadata.available_fuel

        if fuel_required > available_fuel:
            # Compute max achievable delta-v with available fuel
            if available_fuel <= 0:
                return ManeuverResult(
                    success=False,
                    new_state=None,
                    fuel_consumed_kg=0.0,
                    new_fuel_mass_kg=sat_metadata.fuel_mass,
                    actual_delta_v_ms=0.0,
                    error_message="Insufficient fuel for maneuver (reserves depleted)",
                )

            # Partial burn with available fuel
            m_final = m_initial - available_fuel
            actual_delta_v = v_exhaust * math.log(m_initial / m_final)
            fuel_consumed = available_fuel

            # Apply partial maneuver
            new_state = self._apply_delta_v(
                satellite.state, actual_delta_v, maneuver.direction
            )

            return ManeuverResult(
                success=True,  # Partial success
                new_state=new_state,
                fuel_consumed_kg=fuel_consumed,
                new_fuel_mass_kg=sat_metadata.fuel_mass - fuel_consumed,
                actual_delta_v_ms=actual_delta_v,
                error_message=f"Partial burn: requested {maneuver.delta_v:.2f} m/s, achieved {actual_delta_v:.2f} m/s",
            )

        # Full burn possible
        new_state = self._apply_delta_v(
            satellite.state, maneuver.delta_v, maneuver.direction
        )

        return ManeuverResult(
            success=True,
            new_state=new_state,
            fuel_consumed_kg=fuel_required,
            new_fuel_mass_kg=sat_metadata.fuel_mass - fuel_required,
            actual_delta_v_ms=maneuver.delta_v,
        )

    def estimate_fuel_consumption(
        self,
        sat_metadata: Satellite,
        delta_v_ms: float,
    ) -> float:
        """Estimate fuel required for a given delta-v.

        Uses Tsiolkovsky equation to compute fuel mass.
        """
        if delta_v_ms <= 0:
            return 0.0

        v_exhaust = sat_metadata.exhaust_velocity_ms
        m_initial = sat_metadata.total_mass

        mass_ratio = math.exp(delta_v_ms / v_exhaust)
        fuel_required = m_initial * (1 - 1 / mass_ratio)

        return fuel_required

    def compute_max_delta_v(self, sat_metadata: Satellite) -> float:
        """Compute maximum achievable delta-v with available fuel.

        Uses inverse Tsiolkovsky equation.
        """
        available_fuel = sat_metadata.available_fuel

        if available_fuel <= 0:
            return 0.0

        v_exhaust = sat_metadata.exhaust_velocity_ms
        m_initial = sat_metadata.total_mass
        m_final = m_initial - available_fuel

        if m_final <= 0:
            return float("inf")

        return v_exhaust * math.log(m_initial / m_final)

    def _apply_delta_v(
        self,
        sv: StateVector,
        delta_v_ms: float,
        direction: str,
    ) -> StateVector:
        """Apply a delta-v in the specified direction.

        Args:
            sv: Current state vector
            delta_v_ms: Delta-v magnitude in m/s
            direction: One of "prograde", "retrograde", "radial", "normal"

        Returns:
            New StateVector with velocity changed
        """
        dv_kms = delta_v_ms / 1000.0  # Convert to km/s

        # Current velocity magnitude
        v_mag = math.sqrt(sv.vx**2 + sv.vy**2 + sv.vz**2)

        if v_mag == 0:
            return sv

        # Velocity unit vector (prograde direction)
        ux, uy, uz = sv.vx / v_mag, sv.vy / v_mag, sv.vz / v_mag

        # Position unit vector (radial direction, outward)
        r_mag = math.sqrt(sv.x**2 + sv.y**2 + sv.z**2)
        rx, ry, rz = sv.x / r_mag, sv.y / r_mag, sv.z / r_mag

        # Normal = r x v (orbit-normal direction)
        nx = ry * uz - rz * uy
        ny = rz * ux - rx * uz
        nz = rx * uy - ry * ux
        n_mag = math.sqrt(nx**2 + ny**2 + nz**2)
        if n_mag > 0:
            nx, ny, nz = nx / n_mag, ny / n_mag, nz / n_mag
        else:
            nx, ny, nz = 0, 0, 1

        # Select direction components
        if direction == "prograde":
            dvx, dvy, dvz = ux * dv_kms, uy * dv_kms, uz * dv_kms
        elif direction == "retrograde":
            dvx, dvy, dvz = -ux * dv_kms, -uy * dv_kms, -uz * dv_kms
        elif direction == "radial":
            dvx, dvy, dvz = rx * dv_kms, ry * dv_kms, rz * dv_kms
        elif direction == "normal":
            dvx, dvy, dvz = nx * dv_kms, ny * dv_kms, nz * dv_kms
        else:
            raise ValueError(f"Unknown direction: {direction}")

        return StateVector(
            x=sv.x,
            y=sv.y,
            z=sv.z,
            vx=sv.vx + dvx,
            vy=sv.vy + dvy,
            vz=sv.vz + dvz,
        )

    def validate_maneuver(
        self,
        sat_metadata: Satellite,
        maneuver: Maneuver,
    ) -> tuple[bool, str]:
        """Validate that a maneuver can be executed.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check delta-v limit
        if maneuver.delta_v > MAX_DELTA_V_MS:
            return False, f"Delta-v {maneuver.delta_v:.2f} m/s exceeds max {MAX_DELTA_V_MS} m/s"

        # Check satellite maneuverable
        if not sat_metadata.is_maneuverable:
            return False, "Satellite is not maneuverable"

        # Check satellite health
        if not sat_metadata.is_healthy:
            return False, "Satellite is unhealthy"

        # Check fuel
        fuel_required = self.estimate_fuel_consumption(sat_metadata, maneuver.delta_v)
        if fuel_required > sat_metadata.available_fuel:
            return False, f"Insufficient fuel: need {fuel_required:.3f} kg, have {sat_metadata.available_fuel:.3f} kg"

        return True, "OK"


# Singleton instance
maneuver_executor = ManeuverExecutor()
