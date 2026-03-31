"""Autonomous collision avoidance service with decision intelligence.

This is the main closed-loop avoidance engine that:
1. Predicts conjunctions up to 24 hours ahead
2. Prioritizes threats using the decision intelligence layer
3. Makes fuel-aware decisions about which threats to handle
4. Plans evasion + recovery maneuver sequences
5. Schedules and executes maneuvers with all constraints
6. Verifies maneuver effectiveness post-execution
7. Handles re-planning after verification failures
8. Logs all events and decisions for history and audit
"""

import logging
import random
import uuid
from typing import Optional

from app.core.conjunction_detector import (
    conjunction_detector,
    MISS_DISTANCE_ALERT_THRESHOLD_M,
)
from app.core.maneuver_planner import maneuver_planner
from app.models.conjunction import Conjunction, ConjunctionStatus, ConjunctionSeverity
from app.models.maneuver import ManeuverSequence
from app.services.event_log_service import event_log_service
from app.models.event_log import EventType
from app.services.execution_service import execution_service
from app.services.telemetry_service import telemetry_service
from app.services.decision_service import decision_service
from app.models.decision import ThreatSeverity, SystemOperatingMode

logger = logging.getLogger(__name__)

# Demo mode settings - generate synthetic conjunctions for demonstration
DEMO_MODE_ENABLED = True
DEMO_CONJUNCTION_MIN_PER_STEP = 1
DEMO_CONJUNCTION_MAX_PER_STEP = 3
DEMO_CONJUNCTION_PROBABILITY = 0.7  # 70% chance per step to generate


class AvoidanceService:
    """Autonomous collision avoidance orchestration service with decision intelligence.

    This service runs the closed-loop avoidance cycle:
    1. Predict conjunctions (24-hour lookahead)
    2. Prioritize threats using composite scoring
    3. Make fuel-aware decisions (skip low-priority if fuel constrained)
    4. Plan avoidance sequences for selected conjunctions
    5. Schedule and execute maneuvers with constellation-level management
    6. Verify maneuver effectiveness and re-plan if needed
    7. Log all activities and decisions
    """

    def __init__(self):
        self.active_conjunctions: dict[str, Conjunction] = {}
        self.planned_sequences: dict[str, ManeuverSequence] = {}  # conjunction_id -> sequence
        self.mitigated_conjunctions: set[str] = set()
        self._synthetic_conj_counter = 0

    def _generate_synthetic_conjunctions(self, sim_time: float) -> list[Conjunction]:
        """Generate synthetic conjunctions for demo purposes.

        This ensures the system always has activity to demonstrate even when
        real orbital mechanics don't produce close approaches.

        Returns:
            List of synthetic Conjunction objects
        """
        if not DEMO_MODE_ENABLED:
            return []

        # Random chance to generate conjunctions
        if random.random() > DEMO_CONJUNCTION_PROBABILITY:
            return []

        satellites = telemetry_service.get_all_satellites()
        debris = telemetry_service.get_all_debris()

        if not satellites or not debris:
            return []

        # Pick random count of conjunctions
        num_conjunctions = random.randint(
            DEMO_CONJUNCTION_MIN_PER_STEP,
            min(DEMO_CONJUNCTION_MAX_PER_STEP, len(satellites))
        )

        synthetic_conjunctions = []
        sat_ids = list(satellites.keys())
        debris_ids = list(debris.keys())

        # Avoid satellites that already have active sequences
        available_sats = [
            sid for sid in sat_ids
            if not any(
                seq.satellite_id == sid
                for seq in self.planned_sequences.values()
            )
        ]

        if not available_sats:
            available_sats = sat_ids

        for _ in range(num_conjunctions):
            if not available_sats or not debris_ids:
                break

            # Pick random satellite and debris
            sat_id = random.choice(available_sats)
            debris_id = random.choice(debris_ids)

            # Remove this satellite from available list to avoid duplicate conjunctions
            if sat_id in available_sats:
                available_sats.remove(sat_id)

            # Get actual telemetry for realistic position data
            sat_telemetry = satellites.get(sat_id)
            debris_telemetry = debris.get(debris_id)

            if not sat_telemetry or not debris_telemetry:
                continue

            # Generate realistic threat parameters
            # Miss distance: 20-90m (always below 100m threshold for CRITICAL)
            miss_distance_m = random.uniform(20.0, 90.0)

            # Time to TCA: 30 minutes to 6 hours in future
            time_to_tca = random.uniform(1800.0, 21600.0)

            # Relative velocity: typical LEO encounter 5-15 km/s
            relative_velocity_ms = random.uniform(5000.0, 15000.0)

            # Current distance: miss distance + closing distance
            current_distance_m = miss_distance_m + (relative_velocity_ms * random.uniform(0.01, 0.05))

            # Use satellite's current position for TCA position (approximate)
            sat_state = sat_telemetry.state

            # Generate unique ID
            self._synthetic_conj_counter += 1
            conj_id = f"SYNTH-CONJ-{sat_id}-{debris_id}-{self._synthetic_conj_counter:04d}"

            conjunction = Conjunction(
                id=conj_id,
                satellite_id=sat_id,
                secondary_id=debris_id,
                secondary_type="debris",
                detection_time=sim_time,
                tca=sim_time + time_to_tca,
                time_to_tca=time_to_tca,
                current_distance_m=current_distance_m,
                predicted_miss_distance_m=miss_distance_m,
                relative_velocity_ms=relative_velocity_ms,
                tca_position_x=sat_state.x,
                tca_position_y=sat_state.y,
                tca_position_z=sat_state.z,
                severity=ConjunctionSeverity.CRITICAL,  # Always critical for demo
                status=ConjunctionStatus.DETECTED,
            )

            synthetic_conjunctions.append(conjunction)
            logger.info(
                f"SYNTHETIC_CONJUNCTION_GENERATED | sat={sat_id} | debris={debris_id} | "
                f"miss={miss_distance_m:.1f}m | tca_in={time_to_tca:.0f}s"
            )

        return synthetic_conjunctions

    def run_avoidance_cycle(self, sim_time: float) -> dict:
        """Run one complete avoidance cycle with decision intelligence.

        This should be called every simulation step.

        Args:
            sim_time: Current simulation time

        Returns:
            Summary of avoidance cycle results including decision metrics
        """
        satellites = telemetry_service.get_all_satellites()
        debris = telemetry_service.get_all_debris()

        # Step 1: Check for verification failures that need re-planning
        replanning_results = self._handle_verification_failures(sim_time)

        # Step 2: Predict conjunctions
        predicted_conjunctions = conjunction_detector.predict_conjunctions(
            satellites=satellites,
            debris=debris,
            current_sim_time=sim_time,
            prediction_horizon_seconds=86400.0,  # 24 hours
            alert_threshold_m=MISS_DISTANCE_ALERT_THRESHOLD_M,
        )

        # Step 2.5: DEMO MODE - Inject synthetic conjunctions if none detected
        # This ensures visible system activity for demonstration purposes
        synthetic_count = 0
        critical_real = [
            c for c in predicted_conjunctions
            if c.predicted_miss_distance_m < MISS_DISTANCE_ALERT_THRESHOLD_M
        ]
        if DEMO_MODE_ENABLED and len(critical_real) == 0:
            synthetic_conjunctions = self._generate_synthetic_conjunctions(sim_time)
            predicted_conjunctions.extend(synthetic_conjunctions)
            synthetic_count = len(synthetic_conjunctions)
            if synthetic_count > 0:
                logger.info(
                    f"DEMO_MODE | Injected {synthetic_count} synthetic conjunctions for demonstration"
                )

        # Step 3: Update decision service with pending count for mode calculation
        pending_count = len(execution_service.get_pending_maneuvers())
        decision_service.update_pending_count(pending_count)

        # Step 4: Prioritize threats using decision intelligence
        prioritized_threats = decision_service.prioritize_threats(predicted_conjunctions)

        # Step 5: Process threats by priority, making fuel-aware decisions
        new_critical = []
        decisions_made = []
        skipped_count = 0
        deferred_count = 0

        for conj, threat_score in prioritized_threats:
            # Skip if not critical enough (above threshold)
            if conj.predicted_miss_distance_m >= MISS_DISTANCE_ALERT_THRESHOLD_M:
                continue

            # Skip if already handled
            if conj.satellite_id in self.mitigated_conjunctions:
                continue

            # Check if we already have a sequence for this satellite+debris pair
            existing_key = f"{conj.satellite_id}-{conj.secondary_id}"
            if existing_key in self.planned_sequences:
                continue

            # Get fuel status for the satellite
            fuel_status = decision_service.get_satellite_fuel_status(conj.satellite_id)
            if fuel_status is None:
                continue

            # Check if this threat should be skipped based on fuel/mode
            should_skip, skip_reason = decision_service.should_skip_threat(
                threat_score, fuel_status
            )

            if should_skip:
                # Record decision to skip
                decision = decision_service.make_decision(
                    conjunction=conj,
                    sim_time=sim_time,
                    maneuver_planned=False,
                )
                decisions_made.append(decision)
                skipped_count += 1
                logger.info(
                    f"THREAT_SKIPPED | sat={conj.satellite_id} | "
                    f"severity={threat_score.severity.value} | reason={skip_reason}"
                )
                continue

            # Check constellation capacity
            can_schedule, capacity_reason = decision_service.can_schedule_maneuver(
                conj.satellite_id
            )

            if not can_schedule:
                # Record decision to defer
                decision = decision_service.make_decision(
                    conjunction=conj,
                    sim_time=sim_time,
                    maneuver_planned=False,
                )
                decisions_made.append(decision)
                deferred_count += 1
                logger.info(
                    f"THREAT_DEFERRED | sat={conj.satellite_id} | "
                    f"severity={threat_score.severity.value} | reason={capacity_reason}"
                )
                continue

            # Add to processing list
            new_critical.append((conj, threat_score))

            # Log detection
            logger.warning(
                f"CONJUNCTION_DETECTED | sat={conj.satellite_id} | "
                f"debris={conj.secondary_id} | miss={conj.predicted_miss_distance_m:.1f}m | "
                f"tca_in={conj.time_to_tca:.0f}s | severity={threat_score.severity.value} | "
                f"score={threat_score.composite_score:.1f}"
            )

            event_log_service.log_conjunction_detected(
                sim_time=sim_time,
                satellite_id=conj.satellite_id,
                conjunction_id=conj.id,
                miss_distance_m=conj.predicted_miss_distance_m,
                time_to_tca=conj.time_to_tca,
                secondary_id=conj.secondary_id,
            )

        # Step 6: Plan avoidance sequences for selected conjunctions
        planned_count = 0
        for conj, threat_score in new_critical:
            logger.info(
                f"PLANNING_AVOIDANCE | sat={conj.satellite_id} | conj={conj.id} | "
                f"severity={threat_score.severity.value}"
            )

            sequence = self._plan_avoidance(conj, sim_time)

            if sequence:
                planned_count += 1
                # Register active maneuver with decision service
                decision_service.register_active_maneuver(conj.satellite_id)

                # Record successful decision
                fuel_status = decision_service.get_satellite_fuel_status(conj.satellite_id)
                decision = decision_service.make_decision(
                    conjunction=conj,
                    sim_time=sim_time,
                    maneuver_planned=True,
                    maneuver_id=sequence.evasion.id,
                    delta_v_ms=sequence.evasion.delta_v,
                    fuel_cost_kg=sequence.total_estimated_fuel_kg,
                    expected_improvement_m=conj.predicted_miss_distance_m,  # Expect to clear
                )
                decisions_made.append(decision)

                logger.info(
                    f"AVOIDANCE_PLANNED | sat={conj.satellite_id} | "
                    f"evasion_at={sequence.evasion.scheduled_time:.0f}s | "
                    f"recovery_at={sequence.recovery.scheduled_time:.0f}s | "
                    f"fuel_cost={sequence.total_estimated_fuel_kg:.3f}kg"
                )
            else:
                # Record failed planning
                decision = decision_service.make_decision(
                    conjunction=conj,
                    sim_time=sim_time,
                    maneuver_planned=False,
                )
                decisions_made.append(decision)
                logger.error(
                    f"AVOIDANCE_PLANNING_FAILED | sat={conj.satellite_id} | conj={conj.id}"
                )

        # Step 7: Execute pending maneuvers
        execution_results = execution_service.process_maneuver_queue(sim_time)

        # Clear active maneuver status for completed maneuvers
        for result in execution_results:
            if result.get("status") == "executed":
                decision_service.clear_active_maneuver(result["satellite_id"])

        # Step 8: Clear passed conjunctions
        cleared = conjunction_detector.clear_passed_conjunctions(sim_time)

        # Update tracking
        for conj in predicted_conjunctions:
            self.active_conjunctions[conj.id] = conj

        # Get unprotected satellites for reporting
        unprotected = telemetry_service.get_unprotected_satellites()

        # Get operating mode
        operating_mode, mode_reason = decision_service.get_operating_mode()

        return {
            "sim_time": sim_time,
            "conjunctions_predicted": len(predicted_conjunctions),
            "critical_conjunctions": len([
                c for c in predicted_conjunctions
                if c.predicted_miss_distance_m < MISS_DISTANCE_ALERT_THRESHOLD_M
            ]),
            "threats_evaluated": len(new_critical) + skipped_count + deferred_count,
            "threats_skipped": skipped_count,
            "threats_deferred": deferred_count,
            "sequences_planned": planned_count,
            "execution_results": execution_results,
            "conjunctions_cleared": cleared,
            "pending_maneuvers": len(execution_service.get_pending_maneuvers()),
            "replanning_triggered": replanning_results,
            "unprotected_satellites": list(unprotected.keys()),
            "operating_mode": operating_mode.value,
            "mode_reason": mode_reason,
            "decisions_made": len(decisions_made),
            "synthetic_conjunctions": synthetic_count,
            "demo_mode_active": DEMO_MODE_ENABLED,
        }

    def _handle_verification_failures(self, sim_time: float) -> list[dict]:
        """Handle verification failures by triggering re-planning.

        Args:
            sim_time: Current simulation time

        Returns:
            List of re-planning results
        """
        results = []
        failures = execution_service.get_verification_failures()

        for sat_id, failure_info in failures.items():
            conjunction_id = failure_info["conjunction_id"]

            # Log re-planning
            event_log_service.log_maneuver_replanning(
                sim_time=sim_time,
                satellite_id=sat_id,
                conjunction_id=conjunction_id,
                reason=f"Previous maneuver did not improve miss distance "
                       f"({failure_info['old_miss_m']:.1f}m -> {failure_info['new_miss_m']:.1f}m)",
            )

            # Get conjunction
            conjunction = self.active_conjunctions.get(conjunction_id)
            if conjunction is None:
                # Find in active conjunctions list
                for conj in conjunction_detector.get_active_conjunctions():
                    if conj.id == conjunction_id:
                        conjunction = conj
                        break

            if conjunction is None:
                results.append({
                    "satellite_id": sat_id,
                    "conjunction_id": conjunction_id,
                    "status": "conjunction_not_found",
                })
                execution_service.clear_verification_failure(sat_id)
                continue

            # Remove old sequence tracking
            pair_key = f"{sat_id}-{conjunction.secondary_id}"
            if pair_key in self.planned_sequences:
                del self.planned_sequences[pair_key]

            # Clear active maneuver to allow re-planning
            decision_service.clear_active_maneuver(sat_id)

            # Plan new avoidance sequence
            new_sequence = self._plan_avoidance(conjunction, sim_time)

            if new_sequence:
                decision_service.register_active_maneuver(sat_id)
                results.append({
                    "satellite_id": sat_id,
                    "conjunction_id": conjunction_id,
                    "status": "replanned",
                    "new_sequence_id": new_sequence.id,
                })
            else:
                results.append({
                    "satellite_id": sat_id,
                    "conjunction_id": conjunction_id,
                    "status": "replanning_failed",
                })

            # Clear the failure
            execution_service.clear_verification_failure(sat_id)

        return results

    def _plan_avoidance(self, conjunction: Conjunction, sim_time: float) -> Optional[ManeuverSequence]:
        """Plan and schedule an avoidance sequence for a conjunction.

        Args:
            conjunction: The conjunction to avoid
            sim_time: Current simulation time

        Returns:
            ManeuverSequence if successfully planned and scheduled, None otherwise
        """
        sat_id = conjunction.satellite_id

        # Get satellite telemetry and metadata
        satellite = telemetry_service.get_satellite(sat_id)
        sat_metadata = telemetry_service.get_satellite_metadata(sat_id)

        if satellite is None or sat_metadata is None:
            return None

        # Get debris telemetry for geometry calculations
        debris = telemetry_service.get_debris(conjunction.secondary_id)

        # Get nominal orbit for recovery planning
        nominal_state = telemetry_service.get_nominal_orbit(sat_id)

        # Plan the sequence with nominal orbit reference
        sequence = maneuver_planner.plan_avoidance_sequence(
            conjunction=conjunction,
            satellite=satellite,
            debris=debris,
            sat_metadata=sat_metadata,
            current_sim_time=sim_time,
            nominal_state=nominal_state,
        )

        if sequence is None:
            return None

        # Schedule the sequence with original miss distance for verification
        result = execution_service.schedule_maneuver_sequence(
            sequence,
            sim_time,
            original_miss_distance_m=conjunction.predicted_miss_distance_m,
        )

        if result["status"] == "scheduled":
            # Track the planned sequence
            pair_key = f"{sat_id}-{conjunction.secondary_id}"
            self.planned_sequences[pair_key] = sequence

            # Update conjunction status
            conjunction_detector.update_conjunction_status(
                conjunction.id, ConjunctionStatus.AVOIDANCE_PLANNED
            )

            return sequence

        return None

    def get_active_conjunctions(self) -> list[Conjunction]:
        """Get all currently tracked conjunctions."""
        return list(self.active_conjunctions.values())

    def get_critical_conjunctions(self) -> list[Conjunction]:
        """Get conjunctions that require avoidance action."""
        return [
            c for c in self.active_conjunctions.values()
            if c.predicted_miss_distance_m < MISS_DISTANCE_ALERT_THRESHOLD_M
        ]

    def get_prioritized_conjunctions(self) -> list[tuple[Conjunction, dict]]:
        """Get all conjunctions with their threat scores, prioritized.

        Returns:
            List of (conjunction, threat_score_dict) tuples, sorted by priority
        """
        conjunctions = self.get_active_conjunctions()
        prioritized = decision_service.prioritize_threats(conjunctions)
        return [(conj, score.model_dump()) for conj, score in prioritized]

    def get_planned_sequences(self) -> list[ManeuverSequence]:
        """Get all planned avoidance sequences."""
        return list(self.planned_sequences.values())

    def cancel_avoidance(self, conjunction_id: str) -> bool:
        """Cancel avoidance for a conjunction.

        Args:
            conjunction_id: ID of the conjunction

        Returns:
            True if cancelled successfully
        """
        # Find and cancel the associated sequence
        for key, sequence in list(self.planned_sequences.items()):
            if sequence.conjunction_id == conjunction_id:
                execution_service.cancel_sequence(sequence.id)
                del self.planned_sequences[key]

                # Clear active maneuver status
                decision_service.clear_active_maneuver(sequence.satellite_id)

                # Update conjunction status
                conjunction_detector.update_conjunction_status(
                    conjunction_id, ConjunctionStatus.CANCELLED
                )
                return True

        return False

    def get_avoidance_status(self, sim_time: float) -> dict:
        """Get comprehensive avoidance system status with decision intelligence.

        Args:
            sim_time: Current simulation time

        Returns:
            Status dictionary with all relevant information including decision metrics
        """
        conjunctions = list(self.active_conjunctions.values())
        critical = [
            c for c in conjunctions
            if c.predicted_miss_distance_m < MISS_DISTANCE_ALERT_THRESHOLD_M
        ]

        pending_maneuvers = execution_service.get_pending_maneuvers()
        unprotected = telemetry_service.get_unprotected_satellites()
        verification_failures = execution_service.get_verification_failures()

        # Get decision intelligence metrics
        operating_mode, mode_reason = decision_service.get_operating_mode()
        constellation_status = decision_service.get_constellation_status()
        decision_stats = decision_service.get_statistics()

        return {
            "sim_time": sim_time,
            "total_conjunctions": len(conjunctions),
            "critical_conjunctions": len(critical),
            "mitigated_count": len(self.mitigated_conjunctions),
            "planned_sequences": len(self.planned_sequences),
            "pending_maneuvers": len(pending_maneuvers),
            "next_maneuver_time": min(
                (m.scheduled_time for m in pending_maneuvers), default=None
            ),
            "unprotected_satellites": list(unprotected.keys()),
            "verification_failures_pending": len(verification_failures),
            "constellation_stats": telemetry_service.get_constellation_stats(),
            # Decision intelligence metrics
            "operating_mode": operating_mode.value,
            "mode_reason": mode_reason,
            "constellation_status": constellation_status.model_dump(),
            "decision_statistics": decision_stats,
        }

    def mark_mitigated(self, satellite_id: str):
        """Mark a satellite as having its conjunction mitigated."""
        self.mitigated_conjunctions.add(satellite_id)
        decision_service.clear_active_maneuver(satellite_id)

    def clear_mitigation(self, satellite_id: str):
        """Clear mitigation status for a satellite."""
        self.mitigated_conjunctions.discard(satellite_id)


# Singleton instance
avoidance_service = AvoidanceService()
