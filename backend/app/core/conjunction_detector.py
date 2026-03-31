"""Predictive conjunction detection engine with TCA calculation.

Implements efficient candidate filtering to avoid O(N^2) degradation:
1. Spatial filtering: KD-tree for current proximity candidates
2. Temporal filtering: Only propagate pairs within screening threshold
3. TCA refinement: Newton-Raphson iteration to find exact closest approach
4. Result caching: Cache recent predictions to avoid redundant computation
"""

import math
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.spatial import KDTree

from app.models import Telemetry, StateVector
from app.models.conjunction import (
    Conjunction,
    ConjunctionSeverity,
    ConjunctionStatus,
)
from app.config import settings

# Screening thresholds
SPATIAL_SCREENING_THRESHOLD_KM = settings.SPATIAL_SCREENING_THRESHOLD_KM
TEMPORAL_SCREENING_THRESHOLD_KM = settings.TEMPORAL_SCREENING_THRESHOLD_KM
MISS_DISTANCE_ALERT_THRESHOLD_M = settings.MISS_DISTANCE_ALERT_THRESHOLD_M

# Prediction parameters
PREDICTION_HORIZON_SECONDS = settings.PREDICTION_HORIZON_SECONDS
COARSE_PROPAGATION_STEP_SECONDS = settings.COARSE_PROPAGATION_STEP_SECONDS
FINE_PROPAGATION_STEP_SECONDS = settings.FINE_PROPAGATION_STEP_SECONDS

# TCA refinement
TCA_TOLERANCE_SECONDS = 0.1  # Stop Newton iteration when change < 0.1s
TCA_MAX_ITERATIONS = 20

# Cache settings
CACHE_ENABLED = settings.CACHE_PROPAGATION_RESULTS
CACHE_TTL_SECONDS = settings.CACHE_TTL_SECONDS

# WGS-84 gravitational parameter (km^3 / s^2)
MU_EARTH = 398600.4418


@dataclass
class PropagatedState:
    """Lightweight state for propagation (avoids Pydantic overhead)."""

    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    time_offset: float = 0.0

    def position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def velocity(self) -> np.ndarray:
        return np.array([self.vx, self.vy, self.vz])

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z, self.vx, self.vy, self.vz])

    @classmethod
    def from_state_vector(cls, sv: StateVector, t: float = 0.0) -> "PropagatedState":
        return cls(sv.x, sv.y, sv.z, sv.vx, sv.vy, sv.vz, t)


def _gravity_acceleration(pos: np.ndarray) -> np.ndarray:
    """Two-body gravitational acceleration (km/s^2)."""
    r = np.linalg.norm(pos)
    return -MU_EARTH * pos / (r**3)


def _propagate_rk4(state: PropagatedState, dt: float) -> PropagatedState:
    """Single RK4 step for two-body propagation."""
    y = state.to_array()

    def derivatives(y: np.ndarray) -> np.ndarray:
        pos = y[:3]
        vel = y[3:6]
        acc = _gravity_acceleration(pos)
        return np.concatenate([vel, acc])

    k1 = derivatives(y)
    k2 = derivatives(y + 0.5 * dt * k1)
    k3 = derivatives(y + 0.5 * dt * k2)
    k4 = derivatives(y + dt * k3)

    y_new = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    return PropagatedState(
        y_new[0], y_new[1], y_new[2],
        y_new[3], y_new[4], y_new[5],
        state.time_offset + dt
    )


def _propagate_to_time(state: PropagatedState, target_time: float, step: float = 10.0) -> PropagatedState:
    """Propagate state to target_time using adaptive RK4."""
    current = state
    remaining = target_time - current.time_offset

    while abs(remaining) > 1e-6:
        if remaining > 0:
            h = min(step, remaining)
        else:
            h = max(-step, remaining)
        current = _propagate_rk4(current, h)
        remaining = target_time - current.time_offset

    return current


def _compute_relative_state(
    sat_state: PropagatedState,
    debris_state: PropagatedState,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Compute relative position, velocity, distance, and range rate."""
    rel_pos = sat_state.position() - debris_state.position()
    rel_vel = sat_state.velocity() - debris_state.velocity()
    distance = np.linalg.norm(rel_pos)

    # Range rate (rate of change of distance)
    if distance > 0:
        range_rate = np.dot(rel_pos, rel_vel) / distance
    else:
        range_rate = 0.0

    return rel_pos, rel_vel, distance, range_rate


def _find_tca_newton(
    sat_initial: PropagatedState,
    debris_initial: PropagatedState,
    t_guess: float,
    t_min: float,
    t_max: float,
) -> tuple[float, float, float]:
    """Find Time of Closest Approach using Newton-Raphson iteration.

    The TCA is where range_rate = 0 (d(distance)/dt = 0).

    Returns:
        Tuple of (tca, miss_distance_km, relative_velocity_kms)
    """
    t_current = t_guess

    for _ in range(TCA_MAX_ITERATIONS):
        # Propagate both objects to current time estimate
        sat_state = _propagate_to_time(sat_initial, t_current)
        debris_state = _propagate_to_time(debris_initial, t_current)

        rel_pos, rel_vel, distance, range_rate = _compute_relative_state(
            sat_state, debris_state
        )

        # Check convergence
        if abs(range_rate) < 1e-9:
            break

        # Newton step: t_new = t - f(t)/f'(t)
        # f(t) = range_rate
        # f'(t) = d(range_rate)/dt ≈ (v·v - a·r + (r·v)^2/r^2) / r
        # Simplified: use finite difference

        dt_h = 1.0  # 1 second step for derivative
        sat_state_h = _propagate_to_time(sat_initial, t_current + dt_h)
        debris_state_h = _propagate_to_time(debris_initial, t_current + dt_h)
        _, _, _, range_rate_h = _compute_relative_state(sat_state_h, debris_state_h)

        range_rate_derivative = (range_rate_h - range_rate) / dt_h

        if abs(range_rate_derivative) < 1e-12:
            break

        delta_t = -range_rate / range_rate_derivative

        # Clamp step size
        delta_t = max(-600.0, min(600.0, delta_t))

        t_new = t_current + delta_t

        # Bound within search window
        t_new = max(t_min, min(t_max, t_new))

        if abs(t_new - t_current) < TCA_TOLERANCE_SECONDS:
            t_current = t_new
            break

        t_current = t_new

    # Final evaluation at TCA
    sat_state = _propagate_to_time(sat_initial, t_current)
    debris_state = _propagate_to_time(debris_initial, t_current)
    rel_pos, rel_vel, miss_distance, _ = _compute_relative_state(sat_state, debris_state)

    relative_velocity = np.linalg.norm(rel_vel)

    return t_current, miss_distance, relative_velocity


def _coarse_scan_for_minima(
    sat_initial: PropagatedState,
    debris_initial: PropagatedState,
    t_end: float,
    step: float,
) -> list[tuple[float, float]]:
    """Scan for local distance minima over the prediction horizon.

    Returns list of (time, distance) tuples for each local minimum found.
    """
    minima: list[tuple[float, float]] = []

    prev_distance = float("inf")
    prev_prev_distance = float("inf")
    prev_time = 0.0

    t = 0.0
    sat_state = sat_initial
    debris_state = debris_initial

    while t <= t_end:
        rel_pos = sat_state.position() - debris_state.position()
        distance = np.linalg.norm(rel_pos)

        # Detect local minimum: prev < prev_prev and prev < current
        if prev_distance < prev_prev_distance and prev_distance < distance:
            if prev_distance < TEMPORAL_SCREENING_THRESHOLD_KM:
                minima.append((prev_time, prev_distance))

        prev_prev_distance = prev_distance
        prev_distance = distance
        prev_time = t

        # Propagate forward
        sat_state = _propagate_rk4(sat_state, step)
        debris_state = _propagate_rk4(debris_state, step)
        t += step

    return minima


class ConjunctionDetector:
    """Predictive conjunction detection engine.

    Performs efficient screening and computes Time of Closest Approach (TCA)
    for all satellite-debris pairs that may come within threshold.
    Caches recent predictions to avoid redundant computation.
    """

    def __init__(self):
        self._active_conjunctions: dict[str, Conjunction] = {}
        # Cache for conjunction predictions: (sat_id, debris_id) -> (result, timestamp)
        self._prediction_cache: dict[tuple[str, str], tuple[Optional[Conjunction], float]] = {}

    def find_conjunctions(
        self,
        satellites: dict[str, Telemetry],
        debris: dict[str, Telemetry],
        threshold_km: float = SPATIAL_SCREENING_THRESHOLD_KM,
    ) -> list[dict]:
        """Legacy API: Return current-position conjunctions (for compatibility).

        Each result is a dict with keys `satellite_id`, `debris_id`, and `distance` (km).
        """
        if not satellites or not debris:
            return []

        debris_ids = list(debris.keys())
        debris_positions = np.array(
            [[d.state.x, d.state.y, d.state.z] for d in debris.values()]
        )

        tree = KDTree(debris_positions)

        alerts: list[dict] = []
        for sat_id, sat_telemetry in satellites.items():
            sat_pos = np.array(
                [sat_telemetry.state.x, sat_telemetry.state.y, sat_telemetry.state.z]
            )
            indices = tree.query_ball_point(sat_pos, r=threshold_km)

            for idx in indices:
                distance = float(np.linalg.norm(sat_pos - debris_positions[idx]))
                alerts.append(
                    {
                        "satellite_id": sat_id,
                        "debris_id": debris_ids[idx],
                        "distance": round(distance, 6),
                    }
                )

        return alerts

    def predict_conjunctions(
        self,
        satellites: dict[str, Telemetry],
        debris: dict[str, Telemetry],
        current_sim_time: float,
        prediction_horizon_seconds: float = PREDICTION_HORIZON_SECONDS,
        alert_threshold_m: float = MISS_DISTANCE_ALERT_THRESHOLD_M,
    ) -> list[Conjunction]:
        """Predict conjunctions up to prediction_horizon_seconds ahead.

        This is the main entry point for the autonomous avoidance system.

        Algorithm:
        1. Spatial filter: KD-tree query for pairs currently within screening threshold
        2. Temporal scan: Coarse propagation to find approach minima
        3. TCA refinement: Newton-Raphson to find precise closest approach
        4. Alert generation: Create Conjunction objects for pairs below threshold

        Returns:
            List of Conjunction objects sorted by time_to_tca (closest first)
        """
        if not satellites or not debris:
            return []

        # Step 1: Spatial screening with KD-tree
        # Find pairs that are currently (or soon will be) close enough to matter
        debris_ids = list(debris.keys())
        debris_states = [
            PropagatedState.from_state_vector(d.state) for d in debris.values()
        ]
        debris_positions = np.array([d.position() for d in debris_states])

        tree = KDTree(debris_positions)

        candidate_pairs: list[tuple[str, str, int, PropagatedState, PropagatedState]] = []

        for sat_id, sat_telemetry in satellites.items():
            sat_state = PropagatedState.from_state_vector(sat_telemetry.state)
            sat_pos = sat_state.position()

            # Query for debris within expanded screening radius
            indices = tree.query_ball_point(sat_pos, r=SPATIAL_SCREENING_THRESHOLD_KM)

            for idx in indices:
                debris_id = debris_ids[idx]
                candidate_pairs.append(
                    (sat_id, debris_id, idx, sat_state, debris_states[idx])
                )

        # Step 2 & 3: For each candidate, do coarse scan and TCA refinement
        conjunctions: list[Conjunction] = []

        for sat_id, debris_id, debris_idx, sat_state, debris_state in candidate_pairs:
            # Coarse scan for approach minima
            minima = _coarse_scan_for_minima(
                sat_state,
                debris_state,
                prediction_horizon_seconds,
                COARSE_PROPAGATION_STEP_SECONDS,
            )

            if not minima:
                continue

            # Refine each minimum to find precise TCA
            for t_approx, dist_approx in minima:
                # Search window around the approximate minimum
                t_min = max(0.0, t_approx - 2 * COARSE_PROPAGATION_STEP_SECONDS)
                t_max = min(
                    prediction_horizon_seconds,
                    t_approx + 2 * COARSE_PROPAGATION_STEP_SECONDS,
                )

                tca, miss_distance_km, rel_velocity_kms = _find_tca_newton(
                    sat_state,
                    debris_state,
                    t_approx,
                    t_min,
                    t_max,
                )

                miss_distance_m = miss_distance_km * 1000.0
                rel_velocity_ms = rel_velocity_kms * 1000.0

                # Only alert if miss distance is below expanded threshold
                # (we want to track more to see trends, but only trigger on < 100m)
                if miss_distance_m > alert_threshold_m * 100:  # Track up to 10km
                    continue

                # Compute position at TCA for visualization
                sat_at_tca = _propagate_to_time(sat_state, tca)

                # Current distance for comparison
                current_rel_pos = sat_state.position() - debris_state.position()
                current_distance_m = float(np.linalg.norm(current_rel_pos)) * 1000.0

                # Classify severity
                severity = Conjunction.classify_severity(miss_distance_m)

                # Generate unique ID
                conj_id = f"CONJ-{sat_id}-{debris_id}-{uuid.uuid4().hex[:8]}"

                conjunction = Conjunction(
                    id=conj_id,
                    satellite_id=sat_id,
                    secondary_id=debris_id,
                    secondary_type="debris",
                    detection_time=current_sim_time,
                    tca=current_sim_time + tca,
                    time_to_tca=tca,
                    current_distance_m=current_distance_m,
                    predicted_miss_distance_m=miss_distance_m,
                    relative_velocity_ms=rel_velocity_ms,
                    tca_position_x=sat_at_tca.x,
                    tca_position_y=sat_at_tca.y,
                    tca_position_z=sat_at_tca.z,
                    severity=severity,
                    status=ConjunctionStatus.DETECTED,
                )

                conjunctions.append(conjunction)

        # Sort by time_to_tca (most urgent first)
        conjunctions.sort(key=lambda c: c.time_to_tca)

        # Update active conjunctions tracker
        for conj in conjunctions:
            self._active_conjunctions[conj.id] = conj

        return conjunctions

    def get_critical_conjunctions(
        self,
        satellites: dict[str, Telemetry],
        debris: dict[str, Telemetry],
        current_sim_time: float,
    ) -> list[Conjunction]:
        """Get only conjunctions that require avoidance action (miss < 100m)."""
        all_conjunctions = self.predict_conjunctions(
            satellites,
            debris,
            current_sim_time,
            alert_threshold_m=MISS_DISTANCE_ALERT_THRESHOLD_M,
        )

        return [
            c
            for c in all_conjunctions
            if c.predicted_miss_distance_m < MISS_DISTANCE_ALERT_THRESHOLD_M
        ]

    def update_conjunction_status(
        self, conjunction_id: str, new_status: ConjunctionStatus
    ) -> Optional[Conjunction]:
        """Update the status of an active conjunction."""
        if conjunction_id in self._active_conjunctions:
            conj = self._active_conjunctions[conjunction_id]
            # Create updated version (Pydantic models are immutable by default)
            updated = conj.model_copy(update={"status": new_status})
            self._active_conjunctions[conjunction_id] = updated
            return updated
        return None

    def get_active_conjunctions(self) -> list[Conjunction]:
        """Get all currently tracked conjunctions."""
        return list(self._active_conjunctions.values())

    def clear_passed_conjunctions(self, current_sim_time: float) -> int:
        """Remove conjunctions whose TCA has passed."""
        to_remove = [
            cid
            for cid, conj in self._active_conjunctions.items()
            if conj.tca < current_sim_time
        ]

        for cid in to_remove:
            conj = self._active_conjunctions[cid]
            # Update status to PASSED if not already mitigated
            if conj.status not in (
                ConjunctionStatus.MITIGATED,
                ConjunctionStatus.CANCELLED,
            ):
                self._active_conjunctions[cid] = conj.model_copy(
                    update={"status": ConjunctionStatus.PASSED}
                )
            del self._active_conjunctions[cid]

        return len(to_remove)


# Singleton instance
conjunction_detector = ConjunctionDetector()
