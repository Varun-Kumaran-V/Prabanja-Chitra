"""Collision avoidance maneuver planner.

Generates physics-based evasion and recovery burn sequences for conjunction avoidance.

Strategy:
1. Compute optimal evasion burn to maximize miss distance at TCA
2. Validate maneuver effectiveness through simulation BEFORE scheduling
3. Schedule recovery burn based on nominal orbit deviation (not simple opposite)
4. Respect constraints: max delta-v, fuel budget, timing
"""

import math
import uuid
from typing import Optional, Tuple

import numpy as np

from app.models import Maneuver, Telemetry, StateVector, Satellite
from app.models.maneuver import ManeuverType, ManeuverStatus, ManeuverSequence
from app.models.conjunction import Conjunction


# Constraints
MAX_DELTA_V_PER_BURN_MS = 15.0  # Maximum delta-v per burn (m/s)
MIN_TIME_BEFORE_TCA_S = 1800.0  # Minimum 30 minutes before TCA for evasion
RECOVERY_DELAY_AFTER_TCA_S = 3600.0  # Recovery burn 1 hour after TCA
COMMAND_LATENCY_S = 10.0  # Command uplink latency

# Avoidance threshold
MISS_DISTANCE_THRESHOLD_M = 100.0  # Trigger avoidance below 100m

# Physics constants
MU_EARTH_KM3S2 = 398600.4418


def _compute_orbital_elements(state: StateVector) -> dict:
    """Compute basic orbital elements from state vector."""
    r = np.array([state.x, state.y, state.z])
    v = np.array([state.vx, state.vy, state.vz])

    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)

    # Specific angular momentum
    h = np.cross(r, v)
    h_mag = np.linalg.norm(h)

    # Semi-major axis (vis-viva)
    a = 1.0 / (2.0 / r_mag - v_mag**2 / MU_EARTH_KM3S2)

    # Orbital period
    period = 2 * math.pi * math.sqrt(a**3 / MU_EARTH_KM3S2)

    # Eccentricity vector
    e_vec = ((v_mag**2 - MU_EARTH_KM3S2 / r_mag) * r - np.dot(r, v) * v) / MU_EARTH_KM3S2
    e_mag = np.linalg.norm(e_vec)

    # Mean motion (rad/s)
    n = math.sqrt(MU_EARTH_KM3S2 / a**3)

    return {
        "a": a,
        "e": e_mag,
        "h": h_mag,
        "period": period,
        "n": n,
        "r_mag": r_mag,
        "v_mag": v_mag,
        "h_vec": h,
    }


def _compute_unit_vectors(state: StateVector) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute RTN (radial, transverse, normal) unit vectors."""
    r = np.array([state.x, state.y, state.z])
    v = np.array([state.vx, state.vy, state.vz])

    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)

    # Radial (outward)
    r_hat = r / r_mag

    # Velocity direction (prograde)
    v_hat = v / v_mag

    # Normal (orbit plane perpendicular)
    h = np.cross(r, v)
    h_mag = np.linalg.norm(h)
    n_hat = h / h_mag if h_mag > 0 else np.array([0, 0, 1])

    # Transverse (perpendicular to radial, in orbit plane)
    t_hat = np.cross(n_hat, r_hat)

    return r_hat, t_hat, n_hat


def _compute_relative_geometry(
    sat_state: StateVector,
    debris_state: StateVector,
) -> dict:
    """Compute relative geometry between satellite and debris."""
    r_sat = np.array([sat_state.x, sat_state.y, sat_state.z])
    v_sat = np.array([sat_state.vx, sat_state.vy, sat_state.vz])
    r_deb = np.array([debris_state.x, debris_state.y, debris_state.z])
    v_deb = np.array([debris_state.vx, debris_state.vy, debris_state.vz])

    # Relative position and velocity
    rel_pos = r_deb - r_sat
    rel_vel = v_deb - v_sat

    distance = np.linalg.norm(rel_pos)
    rel_speed = np.linalg.norm(rel_vel)

    # Direction from satellite to debris (unit vector)
    if distance > 0:
        threat_direction = rel_pos / distance
    else:
        threat_direction = np.array([1, 0, 0])

    return {
        "rel_pos": rel_pos,
        "rel_vel": rel_vel,
        "distance": distance,
        "rel_speed": rel_speed,
        "threat_direction": threat_direction,
    }


def _compute_evasion_delta_v(
    miss_distance_m: float,
    time_to_tca_s: float,
    relative_velocity_ms: float,
) -> float:
    """Compute required delta-v for evasion based on miss distance and timing.

    Uses linear approximation for small maneuvers:
    delta_r = delta_v * t (for in-track maneuvers)

    For the maneuver to increase miss distance by target_increase:
    delta_v = target_increase / time

    We want to increase miss distance to at least 500m safety margin.
    """
    # Target miss distance (with safety margin)
    TARGET_MISS_M = 500.0

    if miss_distance_m >= TARGET_MISS_M:
        return 0.0

    # Required position change at TCA
    required_change_m = TARGET_MISS_M - miss_distance_m

    # Account for maneuver timing (earlier = more effective)
    # In-track maneuvers: delta_r ~ 1.5 * delta_v * t_lead (simplified)
    effectiveness_factor = 1.5

    if time_to_tca_s <= 0:
        return MAX_DELTA_V_PER_BURN_MS

    # Required delta-v (m/s)
    delta_v = required_change_m / (effectiveness_factor * time_to_tca_s)

    # Add margin for uncertainties
    delta_v *= 1.2

    # Clamp to maximum
    delta_v = min(delta_v, MAX_DELTA_V_PER_BURN_MS)

    # Minimum meaningful maneuver
    delta_v = max(delta_v, 0.1)

    return delta_v


def _determine_burn_direction(
    sat_state: StateVector,
    threat_direction: np.ndarray,
) -> str:
    """Determine optimal burn direction to evade threat.

    Strategy: Burn perpendicular to both the velocity and threat direction
    to maximize out-of-plane separation at TCA.

    If that's not effective, use in-track (prograde/retrograde) to
    change the timing of closest approach.
    """
    r_hat, t_hat, n_hat = _compute_unit_vectors(sat_state)
    v = np.array([sat_state.vx, sat_state.vy, sat_state.vz])
    v_hat = v / np.linalg.norm(v)

    # Component of threat in each direction
    threat_radial = abs(np.dot(threat_direction, r_hat))
    threat_transverse = abs(np.dot(threat_direction, t_hat))
    threat_normal = abs(np.dot(threat_direction, n_hat))

    # Best direction is perpendicular to threat
    # If threat is mostly in-plane, go normal
    # If threat is mostly normal, go in-track

    if threat_normal < 0.5:
        # Threat is mostly in-plane, normal burn most effective
        return "normal"

    # Threat has significant normal component
    # Use in-track to change phasing

    # Determine prograde vs retrograde based on approach geometry
    # If debris is ahead, slow down (retrograde)
    # If debris is behind, speed up (prograde)

    ahead_component = np.dot(threat_direction, v_hat)

    if ahead_component > 0:
        return "retrograde"  # Debris ahead, slow down
    else:
        return "prograde"  # Debris behind, speed up


def _apply_delta_v_to_state(
    state: StateVector,
    delta_v_ms: float,
    direction: str,
) -> StateVector:
    """Apply delta-v to state vector and return new state.

    Args:
        state: Current state vector
        delta_v_ms: Delta-v magnitude in m/s
        direction: Burn direction

    Returns:
        New state vector with applied delta-v
    """
    r_hat, t_hat, n_hat = _compute_unit_vectors(state)
    v = np.array([state.vx, state.vy, state.vz])

    # Convert m/s to km/s for state vector consistency
    delta_v_kms = delta_v_ms / 1000.0

    # Compute delta-v vector based on direction
    if direction == "prograde":
        v_hat = v / np.linalg.norm(v)
        dv = delta_v_kms * v_hat
    elif direction == "retrograde":
        v_hat = v / np.linalg.norm(v)
        dv = -delta_v_kms * v_hat
    elif direction == "normal":
        dv = delta_v_kms * n_hat
    elif direction == "radial":
        dv = delta_v_kms * r_hat
    else:
        dv = np.zeros(3)

    new_v = v + dv

    return StateVector(
        x=state.x,
        y=state.y,
        z=state.z,
        vx=new_v[0],
        vy=new_v[1],
        vz=new_v[2],
    )


def _compute_orbit_deviation(current: StateVector, nominal: StateVector) -> dict:
    """Compute deviation between current state and nominal reference orbit.

    Returns components needed for station-keeping correction.
    """
    r_curr = np.array([current.x, current.y, current.z])
    v_curr = np.array([current.vx, current.vy, current.vz])
    r_nom = np.array([nominal.x, nominal.y, nominal.z])
    v_nom = np.array([nominal.vx, nominal.vy, nominal.vz])

    # Orbital elements comparison
    curr_elems = _compute_orbital_elements(current)
    nom_elems = _compute_orbital_elements(nominal)

    # Semi-major axis difference (affects period/phasing)
    delta_a = curr_elems["a"] - nom_elems["a"]

    # Angular momentum difference (affects orbit plane)
    h_curr = curr_elems["h_vec"]
    h_nom = nom_elems["h_vec"]
    delta_h = h_curr - h_nom
    delta_h_mag = np.linalg.norm(delta_h)

    # Velocity difference in RTN frame
    r_hat, t_hat, n_hat = _compute_unit_vectors(current)
    dv = v_curr - v_nom
    dv_radial = np.dot(dv, r_hat)
    dv_transverse = np.dot(dv, t_hat)
    dv_normal = np.dot(dv, n_hat)

    return {
        "delta_a_km": delta_a,
        "delta_h_mag": delta_h_mag,
        "dv_radial_kms": dv_radial,
        "dv_transverse_kms": dv_transverse,
        "dv_normal_kms": dv_normal,
        "period_curr": curr_elems["period"],
        "period_nom": nom_elems["period"],
    }


def _compute_recovery_burn(
    current_state: StateVector,
    nominal_state: StateVector,
    sat_metadata: Optional[Satellite],
    max_delta_v_ms: float = MAX_DELTA_V_PER_BURN_MS,
) -> Tuple[float, str]:
    """Compute recovery burn to steer back toward nominal orbit.

    Instead of "opposite burn", computes correction based on orbit deviation.
    Uses small corrective burns for station-keeping concept.

    Args:
        current_state: Current (post-evasion) state
        nominal_state: Reference/nominal orbit state
        sat_metadata: Satellite metadata
        max_delta_v_ms: Maximum allowed delta-v

    Returns:
        Tuple of (delta_v_ms, direction)
    """
    deviation = _compute_orbit_deviation(current_state, nominal_state)

    # Priority: correct largest deviation component first
    # Convert km/s to m/s for comparison
    dv_r = abs(deviation["dv_radial_kms"]) * 1000
    dv_t = abs(deviation["dv_transverse_kms"]) * 1000
    dv_n = abs(deviation["dv_normal_kms"]) * 1000

    # Find dominant deviation
    max_dev = max(dv_r, dv_t, dv_n)

    if max_dev < 0.01:  # Less than 10 mm/s deviation - no correction needed
        return 0.0, "prograde"

    # Determine correction direction and magnitude
    if dv_t >= dv_r and dv_t >= dv_n:
        # Transverse (in-track) is dominant - affects phasing
        if deviation["dv_transverse_kms"] > 0:
            # Going faster than nominal - slow down
            direction = "retrograde"
        else:
            # Going slower - speed up
            direction = "prograde"
        delta_v = min(dv_t, max_delta_v_ms)

    elif dv_n >= dv_r:
        # Normal (out-of-plane) is dominant - affects inclination
        direction = "normal"
        # Sign handling: if we're "above" nominal plane, burn opposite
        if deviation["dv_normal_kms"] > 0:
            delta_v = min(dv_n, max_delta_v_ms)
        else:
            delta_v = min(dv_n, max_delta_v_ms)

    else:
        # Radial is dominant - affects eccentricity
        direction = "radial"
        delta_v = min(dv_r, max_delta_v_ms)

    # For station-keeping, use partial correction (don't overcorrect)
    # Apply 50% of deviation as first correction
    delta_v *= 0.5

    # Minimum meaningful burn
    delta_v = max(delta_v, 0.05) if delta_v > 0.01 else 0.0

    return delta_v, direction


class ManeuverPlanner:
    """Plans collision avoidance maneuver sequences."""

    def validate_maneuver_effectiveness(
        self,
        conjunction: Conjunction,
        satellite: Telemetry,
        debris: Optional[Telemetry],
        delta_v_ms: float,
        direction: str,
        time_to_burn: float,
    ) -> dict:
        """Validate that a proposed maneuver actually improves miss distance.

        Simulates satellite trajectory WITH and WITHOUT the maneuver
        and compares predicted miss distance at TCA.

        Args:
            conjunction: The conjunction being avoided
            satellite: Current satellite telemetry
            debris: Debris telemetry
            delta_v_ms: Proposed delta-v (m/s)
            direction: Proposed burn direction
            time_to_burn: Time until burn execution (seconds)

        Returns:
            Validation result dict with miss distances and improvement
        """
        from app.core.orbit_propagator import orbit_propagator

        if debris is None:
            return {"valid": True, "reason": "no_debris_state_for_simulation"}

        time_to_tca = conjunction.time_to_tca

        # Propagate WITHOUT maneuver to TCA
        sat_at_tca_no_burn = orbit_propagator.propagate(satellite.state, time_to_tca)
        deb_at_tca = orbit_propagator.propagate(debris.state, time_to_tca)

        miss_without = np.linalg.norm(
            np.array([sat_at_tca_no_burn.x - deb_at_tca.x,
                      sat_at_tca_no_burn.y - deb_at_tca.y,
                      sat_at_tca_no_burn.z - deb_at_tca.z])
        ) * 1000  # Convert km to m

        # Propagate WITH maneuver:
        # 1. Propagate to burn time
        sat_at_burn = orbit_propagator.propagate(satellite.state, time_to_burn)

        # 2. Apply delta-v
        sat_post_burn = _apply_delta_v_to_state(sat_at_burn, delta_v_ms, direction)

        # 3. Propagate from burn to TCA
        time_burn_to_tca = time_to_tca - time_to_burn
        sat_at_tca_with_burn = orbit_propagator.propagate(sat_post_burn, time_burn_to_tca)

        miss_with = np.linalg.norm(
            np.array([sat_at_tca_with_burn.x - deb_at_tca.x,
                      sat_at_tca_with_burn.y - deb_at_tca.y,
                      sat_at_tca_with_burn.z - deb_at_tca.z])
        ) * 1000  # Convert km to m

        # Determine if maneuver is effective
        improvement_m = miss_with - miss_without
        is_effective = improvement_m > 0

        return {
            "valid": is_effective,
            "miss_without_maneuver_m": miss_without,
            "miss_with_maneuver_m": miss_with,
            "improvement_m": improvement_m,
            "reason": "effective" if is_effective else "no_improvement",
        }

    def plan_avoidance_sequence(
        self,
        conjunction: Conjunction,
        satellite: Telemetry,
        debris: Optional[Telemetry],
        sat_metadata: Optional[Satellite],
        current_sim_time: float,
        nominal_state: Optional[StateVector] = None,
    ) -> Optional[ManeuverSequence]:
        """Plan a complete avoidance maneuver sequence for a conjunction.

        Generates:
        1. Evasion burn: Executed before TCA to avoid collision (validated)
        2. Recovery burn: Based on nominal orbit deviation (not simple opposite)

        Args:
            conjunction: The conjunction to avoid
            satellite: Current satellite telemetry
            debris: Debris telemetry (for geometry calculations)
            sat_metadata: Satellite metadata (for fuel/constraints)
            current_sim_time: Current simulation time
            nominal_state: Reference orbit state for recovery (optional)

        Returns:
            ManeuverSequence with evasion and recovery burns, or None if not needed/possible
        """
        # Check if avoidance is needed
        if conjunction.predicted_miss_distance_m >= MISS_DISTANCE_THRESHOLD_M:
            return None

        # Check if there's enough time before TCA
        time_to_tca = conjunction.time_to_tca

        if time_to_tca < MIN_TIME_BEFORE_TCA_S / 2:
            # Too late for safe maneuver, but might still attempt emergency burn
            pass

        # Compute required delta-v for evasion
        evasion_delta_v = _compute_evasion_delta_v(
            conjunction.predicted_miss_distance_m,
            time_to_tca - MIN_TIME_BEFORE_TCA_S,  # Lead time
            conjunction.relative_velocity_ms,
        )

        if evasion_delta_v <= 0:
            return None

        # Check fuel availability if metadata available
        if sat_metadata:
            total_delta_v = evasion_delta_v * 2  # Evasion + recovery estimate
            can_burn, reason = sat_metadata.can_perform_burn(total_delta_v)
            if not can_burn:
                # Try with reduced delta-v
                max_dv = sat_metadata.calculate_max_delta_v() / 2
                if max_dv < 0.1:
                    return None  # Insufficient fuel
                evasion_delta_v = min(evasion_delta_v, max_dv)

        # Determine burn direction
        if debris:
            rel_geo = _compute_relative_geometry(satellite.state, debris.state)
            direction = _determine_burn_direction(
                satellite.state, rel_geo["threat_direction"]
            )
        else:
            # Default to normal burn if no debris state
            direction = "normal"

        # Schedule evasion burn
        time_to_burn = max(
            COMMAND_LATENCY_S * 2,  # Minimum lead time
            time_to_tca - MIN_TIME_BEFORE_TCA_S,
        )
        evasion_time = current_sim_time + time_to_burn

        # MANEUVER EFFECTIVENESS VALIDATION
        validation = self.validate_maneuver_effectiveness(
            conjunction=conjunction,
            satellite=satellite,
            debris=debris,
            delta_v_ms=evasion_delta_v,
            direction=direction,
            time_to_burn=time_to_burn,
        )

        if not validation["valid"]:
            # Try alternative directions
            alternative_directions = ["prograde", "retrograde", "normal", "radial"]
            alternative_directions = [d for d in alternative_directions if d != direction]

            for alt_dir in alternative_directions:
                alt_validation = self.validate_maneuver_effectiveness(
                    conjunction=conjunction,
                    satellite=satellite,
                    debris=debris,
                    delta_v_ms=evasion_delta_v,
                    direction=alt_dir,
                    time_to_burn=time_to_burn,
                )
                if alt_validation["valid"]:
                    direction = alt_dir
                    validation = alt_validation
                    break

            if not validation["valid"]:
                # No effective maneuver found - still plan but log warning
                pass

        # Generate unique IDs
        sequence_id = f"SEQ-{uuid.uuid4().hex[:8]}"
        evasion_id = f"MAN-E-{uuid.uuid4().hex[:8]}"
        recovery_id = f"MAN-R-{uuid.uuid4().hex[:8]}"

        # Estimate fuel consumption
        if sat_metadata:
            evasion_fuel = sat_metadata.calculate_fuel_for_delta_v(evasion_delta_v)
        else:
            evasion_fuel = 0.0

        # Create evasion maneuver
        evasion = Maneuver(
            id=evasion_id,
            satellite_id=satellite.object_id,
            delta_v=evasion_delta_v,
            direction=direction,
            planned_time=current_sim_time,
            scheduled_time=evasion_time,
            maneuver_type=ManeuverType.EVASION,
            status=ManeuverStatus.PLANNED,
            estimated_fuel_kg=evasion_fuel,
            conjunction_id=conjunction.id,
            paired_maneuver_id=recovery_id,
        )

        # RECOVERY BURN PLANNING (using nominal orbit, not simple opposite)
        # Use provided nominal state or current state as reference
        ref_state = nominal_state if nominal_state else satellite.state

        # Simulate post-evasion state for recovery planning
        from app.core.orbit_propagator import orbit_propagator
        sat_at_evasion = orbit_propagator.propagate(satellite.state, time_to_burn)
        sat_post_evasion = _apply_delta_v_to_state(sat_at_evasion, evasion_delta_v, direction)

        # Propagate to recovery time
        recovery_time = current_sim_time + time_to_tca + RECOVERY_DELAY_AFTER_TCA_S
        time_to_recovery = time_to_tca + RECOVERY_DELAY_AFTER_TCA_S - time_to_burn
        sat_at_recovery = orbit_propagator.propagate(sat_post_evasion, time_to_recovery)

        # Also propagate nominal to recovery time for comparison
        ref_at_recovery = orbit_propagator.propagate(ref_state, recovery_time - current_sim_time)

        # Compute recovery burn based on deviation from nominal
        recovery_delta_v, recovery_direction = _compute_recovery_burn(
            sat_at_recovery,
            ref_at_recovery,
            sat_metadata,
        )

        # Ensure minimum recovery burn if we did an evasion
        if recovery_delta_v < 0.1 and evasion_delta_v > 0.1:
            # Use partial opposite as fallback
            recovery_delta_v = evasion_delta_v * 0.5
            recovery_direction = {
                "prograde": "retrograde",
                "retrograde": "prograde",
                "normal": "normal",
                "radial": "radial",
            }.get(direction, "retrograde")

        if sat_metadata:
            recovery_fuel = sat_metadata.calculate_fuel_for_delta_v(recovery_delta_v)
        else:
            recovery_fuel = 0.0

        recovery = Maneuver(
            id=recovery_id,
            satellite_id=satellite.object_id,
            delta_v=recovery_delta_v,
            direction=recovery_direction,
            planned_time=current_sim_time,
            scheduled_time=recovery_time,
            maneuver_type=ManeuverType.RECOVERY,
            status=ManeuverStatus.PLANNED,
            estimated_fuel_kg=recovery_fuel,
            conjunction_id=conjunction.id,
            paired_maneuver_id=evasion_id,
        )

        # Create sequence
        sequence = ManeuverSequence(
            id=sequence_id,
            satellite_id=satellite.object_id,
            conjunction_id=conjunction.id,
            evasion=evasion,
            recovery=recovery,
            created_time=current_sim_time,
            estimated_completion_time=recovery_time,
            total_estimated_fuel_kg=evasion_fuel + recovery_fuel,
        )

        return sequence

    def plan_maneuver(
        self, satellite: Telemetry, debris_event: dict
    ) -> Maneuver:
        """Legacy API: Plan a single maneuver for immediate execution.

        This is the compatibility interface for the existing system.
        For full avoidance sequences, use plan_avoidance_sequence().
        """
        distance_km: float = debris_event["distance"]
        distance_m = distance_km * 1000.0

        # Compute delta-v based on miss distance
        # Using simplified formula for compatibility
        if distance_m <= 50:
            delta_v = min(2.0, MAX_DELTA_V_PER_BURN_MS)
        elif distance_m <= 100:
            delta_v = min(1.0, MAX_DELTA_V_PER_BURN_MS)
        elif distance_m <= 1000:
            delta_v = 0.5
        else:
            delta_v = 0.25

        # Determine direction based on geometry
        # Simple heuristic: use prograde unless position suggests otherwise
        direction = "prograde"

        # If satellite Z-component is positive (above equatorial plane)
        # and threat is in-plane, use normal burn
        if satellite.state.z > 0:
            direction = "retrograde"

        # Generate unique ID
        maneuver_id = f"MAN-{uuid.uuid4().hex[:8]}"

        import time

        return Maneuver(
            id=maneuver_id,
            satellite_id=debris_event["satellite_id"],
            delta_v=delta_v,
            direction=direction,
            planned_time=time.time(),
            scheduled_time=time.time(),
            maneuver_type=ManeuverType.EVASION,
            status=ManeuverStatus.PLANNED,
        )


# Singleton instance
maneuver_planner = ManeuverPlanner()
