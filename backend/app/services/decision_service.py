"""Decision Intelligence Service for autonomous collision avoidance.

This service provides:
1. Threat prioritization with composite scoring
2. Fuel-aware decision making
3. Constellation-level management
4. Decision explanation and logging
5. Graceful degradation under load
"""

import logging
import uuid
from collections import deque
from typing import Optional

from app.models.conjunction import Conjunction, ConjunctionSeverity
from app.models.decision import (
    ThreatScore,
    ThreatSeverity,
    FuelStatus,
    SatelliteFuelStatus,
    DecisionRecord,
    ConstellationStatus,
    DecisionSummary,
    SystemOperatingMode,
)
from app.services.telemetry_service import telemetry_service

logger = logging.getLogger(__name__)


# Default configuration (can be overridden)
DEFAULT_CONFIG = {
    # Scoring weights for composite threat score
    "weight_miss_distance": 0.50,
    "weight_time_urgency": 0.35,
    "weight_velocity": 0.15,

    # Fuel thresholds
    "fuel_critical_threshold": 0.10,  # Below 10% = critical
    "fuel_low_threshold": 0.30,       # Below 30% = low

    # Constellation management
    "max_concurrent_maneuvers": 5,    # Max simultaneous maneuvers
    "maneuver_spacing_seconds": 60,   # Min time between scheduling for same satellite

    # Degraded mode thresholds
    "degraded_mode_pending_threshold": 10,     # Enter degraded mode if > 10 pending
    "emergency_mode_pending_threshold": 20,    # Enter emergency mode if > 20 pending
    "degraded_mode_critical_threshold": 5,     # Enter degraded mode if > 5 critical threats

    # Priority enforcement
    "critical_only_in_emergency": True,        # Only handle CRITICAL in emergency mode
    "skip_low_when_fuel_critical": True,       # Skip LOW threats when fuel critical
    "skip_medium_when_fuel_low": True,         # Skip MEDIUM threats when fuel low
}


class DecisionService:
    """Decision intelligence engine for collision avoidance."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize the decision service.

        Args:
            config: Optional configuration overrides
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # Decision tracking
        self._decisions: deque[DecisionRecord] = deque(maxlen=10000)
        self._decisions_by_satellite: dict[str, list[str]] = {}  # sat_id -> [decision_ids]
        self._decisions_by_conjunction: dict[str, str] = {}  # conj_id -> decision_id

        # Operating mode
        self._operating_mode = SystemOperatingMode.NOMINAL
        self._mode_reason: Optional[str] = None
        self._degraded_mode_count = 0

        # Constellation tracking
        self._active_maneuvers: set[str] = set()  # satellite_ids with active maneuvers
        self._pending_maneuvers_count = 0

        # Decision ID counter
        self._decision_counter = 0

    def _generate_decision_id(self) -> str:
        """Generate unique decision ID."""
        self._decision_counter += 1
        return f"DEC-{self._decision_counter:08d}"

    # =========================================================================
    # THREAT PRIORITIZATION
    # =========================================================================

    def calculate_threat_score(self, conjunction: Conjunction) -> ThreatScore:
        """Calculate composite threat score for a conjunction.

        Args:
            conjunction: The conjunction to score

        Returns:
            ThreatScore with all scoring components
        """
        # Calculate individual scores
        miss_score = ThreatScore.calculate_miss_distance_score(
            conjunction.predicted_miss_distance_m
        )
        time_score = ThreatScore.calculate_time_urgency_score(
            conjunction.time_to_tca
        )
        velocity_score = ThreatScore.calculate_velocity_score(
            conjunction.relative_velocity_ms
        )

        # Calculate weighted composite
        composite = (
            self.config["weight_miss_distance"] * miss_score +
            self.config["weight_time_urgency"] * time_score +
            self.config["weight_velocity"] * velocity_score
        )

        # Classify severity
        severity = ThreatScore.classify_severity(composite)

        return ThreatScore(
            conjunction_id=conjunction.id,
            satellite_id=conjunction.satellite_id,
            secondary_id=conjunction.secondary_id,
            miss_distance_score=miss_score,
            time_urgency_score=time_score,
            velocity_score=velocity_score,
            composite_score=composite,
            severity=severity,
            miss_distance_m=conjunction.predicted_miss_distance_m,
            time_to_tca_s=conjunction.time_to_tca,
            relative_velocity_ms=conjunction.relative_velocity_ms,
        )

    def prioritize_threats(
        self,
        conjunctions: list[Conjunction],
    ) -> list[tuple[Conjunction, ThreatScore]]:
        """Prioritize conjunctions by threat score.

        Args:
            conjunctions: List of conjunctions to prioritize

        Returns:
            List of (conjunction, threat_score) tuples, sorted by priority (highest first)
        """
        scored = []
        for conj in conjunctions:
            score = self.calculate_threat_score(conj)
            scored.append((conj, score))

        # Sort by composite score descending (highest priority first)
        scored.sort(key=lambda x: x[1].composite_score, reverse=True)

        return scored

    # =========================================================================
    # FUEL-AWARE DECISION MAKING
    # =========================================================================

    def get_satellite_fuel_status(self, satellite_id: str) -> Optional[SatelliteFuelStatus]:
        """Get fuel status for a satellite.

        Args:
            satellite_id: The satellite ID

        Returns:
            SatelliteFuelStatus or None if satellite not found
        """
        metadata = telemetry_service.get_satellite_metadata(satellite_id)
        if metadata is None:
            return None

        # Calculate estimated maneuvers remaining
        # Assume average delta-v of 5 m/s per maneuver pair
        avg_delta_v = 5.0
        fuel_per_maneuver = metadata.calculate_fuel_for_delta_v(avg_delta_v)
        if fuel_per_maneuver > 0:
            est_maneuvers = int(metadata.available_fuel / fuel_per_maneuver)
        else:
            est_maneuvers = 0

        status = SatelliteFuelStatus.classify_status(metadata.fuel_fraction_remaining)

        return SatelliteFuelStatus(
            satellite_id=satellite_id,
            current_fuel_kg=metadata.fuel_mass,
            initial_fuel_kg=metadata.initial_fuel_mass or metadata.fuel_mass,
            available_fuel_kg=metadata.available_fuel,
            fuel_fraction=metadata.fuel_fraction_remaining,
            status=status,
            max_delta_v_available_ms=metadata.calculate_max_delta_v(),
            estimated_maneuvers_remaining=est_maneuvers,
        )

    def get_all_fuel_statuses(self) -> dict[str, SatelliteFuelStatus]:
        """Get fuel status for all satellites.

        Returns:
            Dict mapping satellite_id to SatelliteFuelStatus
        """
        statuses = {}
        for sat_id in telemetry_service.satellite_metadata.keys():
            status = self.get_satellite_fuel_status(sat_id)
            if status:
                statuses[sat_id] = status
        return statuses

    def should_skip_threat(
        self,
        threat_score: ThreatScore,
        fuel_status: SatelliteFuelStatus,
    ) -> tuple[bool, Optional[str]]:
        """Determine if a threat should be skipped based on fuel status.

        Args:
            threat_score: The threat score
            fuel_status: Current fuel status for the satellite

        Returns:
            Tuple of (should_skip, reason)
        """
        # In emergency mode, only handle CRITICAL threats
        if self._operating_mode == SystemOperatingMode.EMERGENCY:
            if threat_score.severity != ThreatSeverity.CRITICAL:
                return True, f"Emergency mode: only handling CRITICAL threats"

        # Never skip CRITICAL threats
        if threat_score.severity == ThreatSeverity.CRITICAL:
            return False, None

        # Fuel-based skipping
        if fuel_status.status == FuelStatus.CRITICAL:
            if self.config["skip_low_when_fuel_critical"]:
                if threat_score.severity == ThreatSeverity.LOW:
                    return True, "Fuel CRITICAL: skipping LOW priority threat"
                if threat_score.severity == ThreatSeverity.MEDIUM:
                    return True, "Fuel CRITICAL: skipping MEDIUM priority threat"

        if fuel_status.status == FuelStatus.LOW:
            if self.config["skip_medium_when_fuel_low"]:
                if threat_score.severity == ThreatSeverity.LOW:
                    return True, "Fuel LOW: skipping LOW priority threat"

        # Degraded mode checks
        if self._operating_mode == SystemOperatingMode.DEGRADED:
            if threat_score.severity == ThreatSeverity.LOW:
                return True, "Degraded mode: deferring LOW priority threat"

        return False, None

    # =========================================================================
    # CONSTELLATION-LEVEL MANAGEMENT
    # =========================================================================

    def get_constellation_status(self) -> ConstellationStatus:
        """Get current constellation-level status.

        Returns:
            ConstellationStatus with current metrics
        """
        stats = telemetry_service.get_constellation_stats()

        # Count by fuel status
        fuel_statuses = self.get_all_fuel_statuses()
        by_fuel = {"normal": 0, "low": 0, "critical": 0}
        for status in fuel_statuses.values():
            by_fuel[status.status.value] += 1

        # Get active threats (would need to be passed in or queried)
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        max_concurrent = self.config["max_concurrent_maneuvers"]
        capacity_available = max(0, max_concurrent - len(self._active_maneuvers))
        utilization = len(self._active_maneuvers) / max_concurrent if max_concurrent > 0 else 0

        return ConstellationStatus(
            total_satellites=stats["total_satellites"],
            active_maneuvers=len(self._active_maneuvers),
            pending_maneuvers=self._pending_maneuvers_count,
            max_concurrent_maneuvers=max_concurrent,
            satellites_by_fuel_status=by_fuel,
            active_threats_by_severity=by_severity,
            operating_mode=self._operating_mode,
            mode_reason=self._mode_reason,
            maneuver_capacity_available=capacity_available,
            capacity_utilization=utilization,
        )

    def update_pending_count(self, count: int) -> None:
        """Update pending maneuver count for mode calculation.

        Args:
            count: Current number of pending maneuvers
        """
        self._pending_maneuvers_count = count
        self._update_operating_mode()

    def register_active_maneuver(self, satellite_id: str) -> None:
        """Register that a satellite has an active maneuver.

        Args:
            satellite_id: The satellite ID
        """
        self._active_maneuvers.add(satellite_id)

    def clear_active_maneuver(self, satellite_id: str) -> None:
        """Clear active maneuver for a satellite.

        Args:
            satellite_id: The satellite ID
        """
        self._active_maneuvers.discard(satellite_id)

    def can_schedule_maneuver(self, satellite_id: str) -> tuple[bool, Optional[str]]:
        """Check if a maneuver can be scheduled for constellation capacity.

        Args:
            satellite_id: The satellite ID

        Returns:
            Tuple of (can_schedule, reason_if_not)
        """
        # Check if satellite already has active maneuver
        if satellite_id in self._active_maneuvers:
            return False, "Satellite already has active maneuver"

        # Check concurrent maneuver limit
        max_concurrent = self.config["max_concurrent_maneuvers"]
        if len(self._active_maneuvers) >= max_concurrent:
            return False, f"Max concurrent maneuvers ({max_concurrent}) reached"

        return True, None

    # =========================================================================
    # GRACEFUL DEGRADATION
    # =========================================================================

    def _update_operating_mode(self) -> None:
        """Update operating mode based on current load."""
        old_mode = self._operating_mode

        # Check for emergency mode
        if self._pending_maneuvers_count >= self.config["emergency_mode_pending_threshold"]:
            self._operating_mode = SystemOperatingMode.EMERGENCY
            self._mode_reason = f"Pending maneuvers ({self._pending_maneuvers_count}) exceeds emergency threshold"
        # Check for degraded mode
        elif self._pending_maneuvers_count >= self.config["degraded_mode_pending_threshold"]:
            self._operating_mode = SystemOperatingMode.DEGRADED
            self._mode_reason = f"Pending maneuvers ({self._pending_maneuvers_count}) exceeds degraded threshold"
        else:
            self._operating_mode = SystemOperatingMode.NOMINAL
            self._mode_reason = None

        # Log mode changes
        if old_mode != self._operating_mode:
            if self._operating_mode != SystemOperatingMode.NOMINAL:
                self._degraded_mode_count += 1
                logger.warning(
                    f"OPERATING_MODE_CHANGE | {old_mode.value} -> {self._operating_mode.value} | "
                    f"reason={self._mode_reason}"
                )
            else:
                logger.info(
                    f"OPERATING_MODE_CHANGE | {old_mode.value} -> {self._operating_mode.value} | "
                    f"system recovered to nominal"
                )

    def get_operating_mode(self) -> tuple[SystemOperatingMode, Optional[str]]:
        """Get current operating mode.

        Returns:
            Tuple of (mode, reason)
        """
        return self._operating_mode, self._mode_reason

    def force_degraded_mode(self, reason: str) -> None:
        """Force system into degraded mode.

        Args:
            reason: Reason for forced degradation
        """
        if self._operating_mode == SystemOperatingMode.NOMINAL:
            self._operating_mode = SystemOperatingMode.DEGRADED
            self._mode_reason = reason
            self._degraded_mode_count += 1
            logger.warning(f"FORCED_DEGRADED_MODE | reason={reason}")

    def clear_degraded_mode(self) -> None:
        """Clear forced degraded mode if conditions allow."""
        if self._pending_maneuvers_count < self.config["degraded_mode_pending_threshold"]:
            self._operating_mode = SystemOperatingMode.NOMINAL
            self._mode_reason = None
            logger.info("CLEARED_DEGRADED_MODE | system returned to nominal")

    # =========================================================================
    # DECISION MAKING & RECORDING
    # =========================================================================

    def make_decision(
        self,
        conjunction: Conjunction,
        sim_time: float,
        maneuver_planned: bool = False,
        maneuver_id: Optional[str] = None,
        delta_v_ms: Optional[float] = None,
        fuel_cost_kg: Optional[float] = None,
        expected_improvement_m: Optional[float] = None,
    ) -> DecisionRecord:
        """Record a decision about a conjunction.

        Args:
            conjunction: The conjunction being evaluated
            sim_time: Current simulation time
            maneuver_planned: Whether a maneuver was scheduled
            maneuver_id: ID of scheduled maneuver (if any)
            delta_v_ms: Planned delta-v (if any)
            fuel_cost_kg: Expected fuel cost (if any)
            expected_improvement_m: Expected miss distance improvement (if any)

        Returns:
            DecisionRecord documenting the decision
        """
        # Calculate threat score
        threat_score = self.calculate_threat_score(conjunction)

        # Get fuel status
        fuel_status = self.get_satellite_fuel_status(conjunction.satellite_id)
        if fuel_status is None:
            # Create placeholder for missing satellite
            fuel_status = SatelliteFuelStatus(
                satellite_id=conjunction.satellite_id,
                current_fuel_kg=0,
                initial_fuel_kg=0,
                available_fuel_kg=0,
                fuel_fraction=0,
                status=FuelStatus.CRITICAL,
                max_delta_v_available_ms=0,
                estimated_maneuvers_remaining=0,
            )

        # Determine action and factors
        if maneuver_planned:
            action = "maneuver_scheduled"
            factors = {
                "operating_mode": self._operating_mode.value,
                "fuel_sufficient": True,
                "capacity_available": True,
            }
        else:
            # Check why it was skipped
            should_skip, skip_reason = self.should_skip_threat(threat_score, fuel_status)
            can_schedule, capacity_reason = self.can_schedule_maneuver(conjunction.satellite_id)

            if should_skip:
                action = "skipped"
                factors = {
                    "skip_reason": skip_reason,
                    "operating_mode": self._operating_mode.value,
                }
            elif not can_schedule:
                action = "deferred"
                factors = {
                    "defer_reason": capacity_reason,
                    "operating_mode": self._operating_mode.value,
                }
            else:
                action = "deferred"
                factors = {
                    "defer_reason": "Planning failed or insufficient resources",
                    "operating_mode": self._operating_mode.value,
                }

        # Check constraints
        constraints_checked = [
            "fuel_availability",
            "concurrent_maneuver_limit",
            "satellite_cooldown",
            "ground_station_contact",
        ]
        constraints_violated = []
        if fuel_status.status == FuelStatus.CRITICAL:
            constraints_violated.append("fuel_critical")
        if conjunction.satellite_id in self._active_maneuvers:
            constraints_violated.append("maneuver_already_active")

        # Create decision record
        decision = DecisionRecord(
            id=self._generate_decision_id(),
            timestamp=sim_time,
            satellite_id=conjunction.satellite_id,
            conjunction_id=conjunction.id,
            action_taken=action,
            threat_score=threat_score,
            fuel_status=fuel_status,
            decision_factors=factors,
            expected_improvement_m=expected_improvement_m,
            expected_new_miss_distance_m=(
                conjunction.predicted_miss_distance_m + (expected_improvement_m or 0)
                if expected_improvement_m
                else None
            ),
            maneuver_id=maneuver_id,
            delta_v_planned_ms=delta_v_ms,
            fuel_cost_kg=fuel_cost_kg,
            constraints_checked=constraints_checked,
            constraints_violated=constraints_violated,
        )

        # Generate explanation
        decision.explanation = decision.generate_explanation()

        # Store decision
        self._decisions.append(decision)

        # Index by satellite
        if decision.satellite_id not in self._decisions_by_satellite:
            self._decisions_by_satellite[decision.satellite_id] = []
        self._decisions_by_satellite[decision.satellite_id].append(decision.id)

        # Index by conjunction
        self._decisions_by_conjunction[decision.conjunction_id] = decision.id

        # Log decision
        logger.info(
            f"DECISION | sat={decision.satellite_id} | conj={decision.conjunction_id} | "
            f"action={action} | severity={threat_score.severity.value} | "
            f"score={threat_score.composite_score:.1f} | fuel={fuel_status.status.value}"
        )

        return decision

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Get a decision by ID.

        Args:
            decision_id: The decision ID

        Returns:
            DecisionRecord or None
        """
        for decision in self._decisions:
            if decision.id == decision_id:
                return decision
        return None

    def get_decisions_for_satellite(
        self,
        satellite_id: str,
        limit: int = 50,
    ) -> list[DecisionRecord]:
        """Get decisions for a specific satellite.

        Args:
            satellite_id: The satellite ID
            limit: Maximum number of decisions to return

        Returns:
            List of DecisionRecord, newest first
        """
        decision_ids = self._decisions_by_satellite.get(satellite_id, [])
        decisions = []

        for dec_id in reversed(decision_ids[-limit:]):
            dec = self.get_decision(dec_id)
            if dec:
                decisions.append(dec)

        return decisions

    def get_decision_for_conjunction(self, conjunction_id: str) -> Optional[DecisionRecord]:
        """Get the decision for a conjunction.

        Args:
            conjunction_id: The conjunction ID

        Returns:
            DecisionRecord or None
        """
        dec_id = self._decisions_by_conjunction.get(conjunction_id)
        if dec_id:
            return self.get_decision(dec_id)
        return None

    def get_recent_decisions(
        self,
        limit: int = 100,
        severity: Optional[ThreatSeverity] = None,
        action: Optional[str] = None,
    ) -> list[DecisionRecord]:
        """Get recent decisions with optional filtering.

        Args:
            limit: Maximum number of decisions
            severity: Filter by threat severity
            action: Filter by action taken

        Returns:
            List of DecisionRecord, newest first
        """
        decisions = list(self._decisions)

        if severity:
            decisions = [d for d in decisions if d.threat_score.severity == severity]

        if action:
            decisions = [d for d in decisions if d.action_taken == action]

        # Sort by timestamp descending
        decisions.sort(key=lambda d: d.timestamp, reverse=True)

        return decisions[:limit]

    def get_decision_summary(
        self,
        start_time: float,
        end_time: float,
    ) -> DecisionSummary:
        """Get summary of decisions in a time period.

        Args:
            start_time: Start of period (simulation time)
            end_time: End of period (simulation time)

        Returns:
            DecisionSummary for the period
        """
        decisions = [
            d for d in self._decisions
            if start_time <= d.timestamp <= end_time
        ]

        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        scheduled = 0
        deferred = 0
        skipped = 0
        total_fuel = 0.0
        total_dv = 0.0

        for dec in decisions:
            by_severity[dec.threat_score.severity.value] += 1

            if dec.action_taken == "maneuver_scheduled":
                scheduled += 1
                total_fuel += dec.fuel_cost_kg or 0
                total_dv += dec.delta_v_planned_ms or 0
            elif dec.action_taken == "deferred":
                deferred += 1
            elif dec.action_taken == "skipped":
                skipped += 1

        return DecisionSummary(
            start_time=start_time,
            end_time=end_time,
            total_threats_evaluated=len(decisions),
            threats_by_severity=by_severity,
            maneuvers_scheduled=scheduled,
            maneuvers_deferred=deferred,
            maneuvers_skipped=skipped,
            total_fuel_committed_kg=total_fuel,
            total_delta_v_committed_ms=total_dv,
            operating_mode=self._operating_mode,
            degraded_mode_activations=self._degraded_mode_count,
        )

    def get_statistics(self) -> dict:
        """Get overall decision service statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self._decisions)
        by_action = {"maneuver_scheduled": 0, "deferred": 0, "skipped": 0}
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for dec in self._decisions:
            by_action[dec.action_taken] = by_action.get(dec.action_taken, 0) + 1
            by_severity[dec.threat_score.severity.value] += 1

        return {
            "total_decisions": total,
            "decisions_by_action": by_action,
            "decisions_by_severity": by_severity,
            "operating_mode": self._operating_mode.value,
            "degraded_mode_activations": self._degraded_mode_count,
            "active_maneuvers": len(self._active_maneuvers),
            "config": self.config,
        }


# Singleton instance
decision_service = DecisionService()
