"""Execution service for autonomous collision avoidance maneuvers.

Enforces operational constraints:
- Configurable cooldown between burns
- Command uplink latency
- Ground station line-of-sight requirement
- Fuel tracking with Tsiolkovsky depletion
- Post-maneuver verification
- LOS failure escalation
"""

import logging
import time
from typing import Optional

from app.config import settings
from app.core.ground_station import ground_station_visibility
from app.core.maneuver_executor import maneuver_executor, ManeuverResult
from app.models import Maneuver
from app.models.maneuver import ManeuverStatus, ManeuverSequence
from app.services.event_log_service import event_log_service
from app.services.maneuver_service import maneuver_service
from app.services.telemetry_service import telemetry_service

logger = logging.getLogger(__name__)

# Operational constraints from configuration
COOLDOWN_SECONDS = settings.COOLDOWN_SECONDS
COMMAND_LATENCY_SECONDS = settings.COMMAND_LATENCY_SECONDS
LOS_CRITICAL_TCA_THRESHOLD_S = settings.LOS_CRITICAL_TCA_THRESHOLD_S


class ExecutionService:
    """Executes planned maneuvers with full constraint enforcement."""

    def __init__(self) -> None:
        self.cooldowns: dict[str, float] = {}  # satellite_id -> last_burn_sim_time
        self.pending_sequences: dict[str, ManeuverSequence] = {}  # sequence_id -> sequence
        self.maneuver_queue: list[Maneuver] = []  # Ordered by scheduled_time
        self.commanding_maneuvers: dict[str, float] = {}  # maneuver_id -> command_sent_time
        # Track conjunction info for post-maneuver verification
        self.conjunction_miss_distances: dict[str, float] = {}  # conjunction_id -> original_miss_distance_m
        # Track maneuver to conjunction mapping
        self.maneuver_conjunctions: dict[str, str] = {}  # maneuver_id -> conjunction_id
        # Track failed verifications for re-planning
        self.verification_failures: dict[str, dict] = {}  # satellite_id -> failure_info

    def _is_on_cooldown(self, satellite_id: str, sim_time: float) -> bool:
        """Check if satellite is in cooldown period."""
        last_burn = self.cooldowns.get(satellite_id)
        if last_burn is None:
            return False
        return (sim_time - last_burn) < COOLDOWN_SECONDS

    def _get_cooldown_remaining(self, satellite_id: str, sim_time: float) -> float:
        """Get remaining cooldown time in seconds."""
        last_burn = self.cooldowns.get(satellite_id)
        if last_burn is None:
            return 0.0
        remaining = COOLDOWN_SECONDS - (sim_time - last_burn)
        return max(0.0, remaining)

    def _check_ground_contact(self, satellite_id: str, sim_time: float) -> tuple[bool, Optional[str]]:
        """Check if satellite has line-of-sight to any ground station.

        Returns:
            Tuple of (has_contact, station_id)
        """
        telemetry = telemetry_service.get_satellite(satellite_id)
        if telemetry is None:
            return False, None

        visible = ground_station_visibility.find_visible_stations(
            telemetry.state, sim_time
        )

        if visible:
            return True, visible[0].station_id
        return False, None

    def _verify_maneuver_effectiveness(
        self,
        maneuver: Maneuver,
        sim_time: float,
    ) -> dict:
        """Verify that a maneuver improved miss distance after execution.

        Args:
            maneuver: The executed maneuver
            sim_time: Current simulation time

        Returns:
            Verification result dict
        """
        from app.core.conjunction_detector import conjunction_detector

        sat_id = maneuver.satellite_id
        conjunction_id = self.maneuver_conjunctions.get(maneuver.id)

        if conjunction_id is None:
            # No conjunction to verify against
            return {"verified": True, "reason": "no_conjunction_tracked"}

        original_miss_m = self.conjunction_miss_distances.get(conjunction_id)
        if original_miss_m is None:
            return {"verified": True, "reason": "no_original_miss_distance"}

        # Re-predict conjunction with updated satellite state
        satellites = telemetry_service.get_all_satellites()
        debris = telemetry_service.get_all_debris()

        if sat_id not in satellites:
            return {"verified": False, "reason": "satellite_not_found"}

        # Run conjunction prediction for this satellite
        new_conjunctions = conjunction_detector.predict_conjunctions(
            satellites={sat_id: satellites[sat_id]},
            debris=debris,
            current_sim_time=sim_time,
            prediction_horizon_seconds=86400.0,
            alert_threshold_m=10000.0,  # Wide threshold to catch the conjunction
        )

        # Find the same conjunction (by secondary_id)
        # Get original conjunction info from active conjunctions
        active_conjs = conjunction_detector.get_active_conjunctions()
        original_conj = None
        for conj in active_conjs:
            if conj.id == conjunction_id:
                original_conj = conj
                break

        if original_conj is None:
            return {"verified": True, "reason": "conjunction_no_longer_tracked"}

        secondary_id = original_conj.secondary_id

        # Find matching conjunction in new predictions
        new_miss_m = None
        for conj in new_conjunctions:
            if conj.secondary_id == secondary_id:
                new_miss_m = conj.predicted_miss_distance_m
                break

        if new_miss_m is None:
            # Conjunction no longer detected - success!
            event_log_service.log_maneuver_verified(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                old_miss_distance_m=original_miss_m,
                new_miss_distance_m=float('inf'),
                conjunction_id=conjunction_id,
            )
            return {
                "verified": True,
                "old_miss_m": original_miss_m,
                "new_miss_m": None,
                "improvement": "conjunction_cleared",
            }

        # Check if miss distance improved
        if new_miss_m > original_miss_m:
            # Success - miss distance increased
            event_log_service.log_maneuver_verified(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                old_miss_distance_m=original_miss_m,
                new_miss_distance_m=new_miss_m,
                conjunction_id=conjunction_id,
            )
            return {
                "verified": True,
                "old_miss_m": original_miss_m,
                "new_miss_m": new_miss_m,
                "improvement_m": new_miss_m - original_miss_m,
            }
        else:
            # Failure - miss distance did not improve
            event_log_service.log_maneuver_verification_failed(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                old_miss_distance_m=original_miss_m,
                new_miss_distance_m=new_miss_m,
                conjunction_id=conjunction_id,
            )

            # Store failure for re-planning
            self.verification_failures[sat_id] = {
                "conjunction_id": conjunction_id,
                "maneuver_id": maneuver.id,
                "old_miss_m": original_miss_m,
                "new_miss_m": new_miss_m,
                "time": sim_time,
            }

            return {
                "verified": False,
                "old_miss_m": original_miss_m,
                "new_miss_m": new_miss_m,
                "degradation_m": original_miss_m - new_miss_m,
            }

    def _check_los_escalation(self, maneuver: Maneuver, sim_time: float) -> Optional[dict]:
        """Check if LOS failure should trigger escalation for critical TCA.

        Args:
            maneuver: The maneuver waiting for LOS
            sim_time: Current simulation time

        Returns:
            Escalation info dict if critical, None otherwise
        """
        sat_id = maneuver.satellite_id
        conjunction_id = self.maneuver_conjunctions.get(maneuver.id)

        if conjunction_id is None:
            return None

        # Get conjunction info
        from app.core.conjunction_detector import conjunction_detector
        active_conjs = conjunction_detector.get_active_conjunctions()

        target_conj = None
        for conj in active_conjs:
            if conj.id == conjunction_id:
                target_conj = conj
                break

        if target_conj is None:
            return None

        # Calculate time to TCA
        time_to_tca = target_conj.tca - sim_time

        # Check if critical
        if time_to_tca < LOS_CRITICAL_TCA_THRESHOLD_S and target_conj.predicted_miss_distance_m < 100:
            # This is critical - log escalation
            event_log_service.log_los_critical_alert(
                sim_time=sim_time,
                satellite_id=sat_id,
                conjunction_id=conjunction_id,
                time_to_tca=time_to_tca,
                miss_distance_m=target_conj.predicted_miss_distance_m,
            )

            # Mark satellite as unprotected
            telemetry_service.mark_unprotected(
                satellite_id=sat_id,
                conjunction_id=conjunction_id,
                time_to_tca=time_to_tca,
                reason=f"No ground contact for critical conjunction (TCA in {time_to_tca:.0f}s)",
            )

            event_log_service.log_satellite_unprotected(
                sim_time=sim_time,
                satellite_id=sat_id,
                conjunction_id=conjunction_id,
                reason=f"No ground contact, TCA in {time_to_tca:.0f}s, miss distance {target_conj.predicted_miss_distance_m:.1f}m",
            )

            return {
                "satellite_id": sat_id,
                "conjunction_id": conjunction_id,
                "time_to_tca": time_to_tca,
                "miss_distance_m": target_conj.predicted_miss_distance_m,
                "status": "unprotected",
            }

        return None

    def schedule_maneuver_sequence(
        self,
        sequence: ManeuverSequence,
        sim_time: float,
        original_miss_distance_m: Optional[float] = None,
    ) -> dict:
        """Schedule a maneuver sequence for execution.

        Args:
            sequence: The ManeuverSequence to schedule
            sim_time: Current simulation time
            original_miss_distance_m: Miss distance before maneuver (for verification)

        Returns:
            Status dict with scheduling result
        """
        sat_id = sequence.satellite_id

        # Check cooldown
        if self._is_on_cooldown(sat_id, sim_time):
            remaining = self._get_cooldown_remaining(sat_id, sim_time)
            return {
                "status": "delayed",
                "reason": "cooldown",
                "cooldown_remaining_s": remaining,
                "satellite_id": sat_id,
            }

        # Check fuel availability
        sat_metadata = telemetry_service.get_satellite_metadata(sat_id)
        if sat_metadata is None:
            return {
                "status": "failed",
                "reason": "satellite_not_found",
                "satellite_id": sat_id,
            }

        total_fuel_needed = sequence.total_estimated_fuel_kg
        if total_fuel_needed > sat_metadata.available_fuel:
            return {
                "status": "failed",
                "reason": "insufficient_fuel",
                "fuel_needed": total_fuel_needed,
                "fuel_available": sat_metadata.available_fuel,
                "satellite_id": sat_id,
            }

        # Store conjunction info for verification
        if sequence.conjunction_id and original_miss_distance_m is not None:
            self.conjunction_miss_distances[sequence.conjunction_id] = original_miss_distance_m
            self.maneuver_conjunctions[sequence.evasion.id] = sequence.conjunction_id
            self.maneuver_conjunctions[sequence.recovery.id] = sequence.conjunction_id

        # Store sequence and queue maneuvers
        self.pending_sequences[sequence.id] = sequence

        # Update maneuver statuses
        evasion = sequence.evasion.model_copy(update={"status": ManeuverStatus.SCHEDULED})
        recovery = sequence.recovery.model_copy(update={"status": ManeuverStatus.SCHEDULED})

        # Add to queue (maintain order by scheduled_time)
        self.maneuver_queue.append(evasion)
        self.maneuver_queue.append(recovery)
        self.maneuver_queue.sort(key=lambda m: m.scheduled_time)

        # Log the scheduling
        event_log_service.log_maneuver_planned(
            sim_time=sim_time,
            satellite_id=sat_id,
            maneuver_id=evasion.id,
            maneuver_type="evasion",
            delta_v_ms=evasion.delta_v,
            direction=evasion.direction,
            scheduled_time=evasion.scheduled_time,
            conjunction_id=sequence.conjunction_id,
        )

        event_log_service.log_maneuver_planned(
            sim_time=sim_time,
            satellite_id=sat_id,
            maneuver_id=recovery.id,
            maneuver_type="recovery",
            delta_v_ms=recovery.delta_v,
            direction=recovery.direction,
            scheduled_time=recovery.scheduled_time,
            conjunction_id=sequence.conjunction_id,
        )

        return {
            "status": "scheduled",
            "sequence_id": sequence.id,
            "evasion_id": evasion.id,
            "recovery_id": recovery.id,
            "evasion_time": evasion.scheduled_time,
            "recovery_time": recovery.scheduled_time,
            "satellite_id": sat_id,
        }

    def process_maneuver_queue(self, sim_time: float) -> list[dict]:
        """Process the maneuver queue at the current simulation time.

        Executes maneuvers that are due and have ground contact.
        Includes LOS escalation for critical conjunctions.

        Args:
            sim_time: Current simulation time

        Returns:
            List of execution result dicts
        """
        results = []
        executed_ids = []

        for maneuver in self.maneuver_queue:
            sat_id = maneuver.satellite_id

            # Skip if not yet due
            if maneuver.scheduled_time > sim_time:
                continue

            # Skip if satellite on cooldown
            if self._is_on_cooldown(sat_id, sim_time):
                continue

            # Check if already commanding (waiting for latency)
            if maneuver.id in self.commanding_maneuvers:
                command_time = self.commanding_maneuvers[maneuver.id]
                if sim_time - command_time < COMMAND_LATENCY_SECONDS:
                    # Still waiting for command to arrive
                    continue
                else:
                    # Command has arrived, execute maneuver
                    result = self._execute_single_maneuver(maneuver, sim_time)
                    results.append(result)
                    executed_ids.append(maneuver.id)
                    del self.commanding_maneuvers[maneuver.id]

                    # Clear unprotected status if maneuver executed
                    if result.get("status") == "executed":
                        if telemetry_service.is_unprotected(sat_id):
                            telemetry_service.clear_unprotected(sat_id)
                            event_log_service.log_satellite_protected(sim_time, sat_id)
                    continue

            # Check ground contact for command uplink
            has_contact, station_id = self._check_ground_contact(sat_id, sim_time)

            if not has_contact:
                # No ground contact - check for LOS escalation
                escalation = self._check_los_escalation(maneuver, sim_time)

                result = {
                    "maneuver_id": maneuver.id,
                    "satellite_id": sat_id,
                    "status": "waiting_los",
                    "reason": "no_ground_contact",
                }

                if escalation:
                    result["escalation"] = escalation

                results.append(result)
                continue

            # Start commanding (introduce latency)
            self.commanding_maneuvers[maneuver.id] = sim_time

            event_log_service.log_command_sent(
                sim_time=sim_time,
                satellite_id=sat_id,
                station_id=station_id or "UNKNOWN",
                maneuver_id=maneuver.id,
            )

            results.append({
                "maneuver_id": maneuver.id,
                "satellite_id": sat_id,
                "status": "commanding",
                "station_id": station_id,
                "execution_in": COMMAND_LATENCY_SECONDS,
            })

        # Remove executed maneuvers from queue
        self.maneuver_queue = [m for m in self.maneuver_queue if m.id not in executed_ids]

        return results

    def _execute_single_maneuver(self, maneuver: Maneuver, sim_time: float) -> dict:
        """Execute a single maneuver with fuel tracking and post-verification.

        Args:
            maneuver: The maneuver to execute
            sim_time: Current simulation time

        Returns:
            Execution result dict
        """
        sat_id = maneuver.satellite_id

        # Get satellite state and metadata
        telemetry = telemetry_service.get_satellite(sat_id)
        sat_metadata = telemetry_service.get_satellite_metadata(sat_id)

        if telemetry is None or sat_metadata is None:
            event_log_service.log_maneuver_failed(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                reason="satellite_not_found",
            )
            return {
                "maneuver_id": maneuver.id,
                "satellite_id": sat_id,
                "status": "failed",
                "reason": "satellite_not_found",
            }

        # Execute with fuel tracking
        result: ManeuverResult = maneuver_executor.execute_maneuver_with_fuel(
            telemetry, sat_metadata, maneuver
        )

        if not result.success:
            event_log_service.log_maneuver_failed(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                reason=result.error_message or "execution_failed",
            )
            return {
                "maneuver_id": maneuver.id,
                "satellite_id": sat_id,
                "status": "failed",
                "reason": result.error_message,
            }

        # Update satellite state
        telemetry_service.update_satellite_state(
            object_id=sat_id,
            new_state=result.new_state,
            timestamp=sim_time,
        )

        # Update fuel
        telemetry_service.update_satellite_fuel(sat_id, result.new_fuel_mass_kg)

        # Record cooldown
        self.cooldowns[sat_id] = sim_time

        # Structured logging
        logger.info(
            f"MANEUVER_EXECUTED | sat={sat_id} | type={maneuver.maneuver_type.value} | "
            f"dv={result.actual_delta_v_ms:.2f}m/s | fuel_used={result.fuel_consumed_kg:.2f}kg | "
            f"fuel_remaining={result.new_fuel_mass_kg:.2f}kg"
        )

        # Log execution
        event_log_service.log_maneuver_executed(
            sim_time=sim_time,
            satellite_id=sat_id,
            maneuver_id=maneuver.id,
            delta_v_actual_ms=result.actual_delta_v_ms,
            fuel_consumed_kg=result.fuel_consumed_kg,
            fuel_remaining_kg=result.new_fuel_mass_kg,
        )

        event_log_service.log_fuel_consumed(
            sim_time=sim_time,
            satellite_id=sat_id,
            fuel_before_kg=sat_metadata.fuel_mass,
            fuel_after_kg=result.new_fuel_mass_kg,
            maneuver_id=maneuver.id,
        )

        # Log recovery if this was a recovery maneuver
        if maneuver.maneuver_type.value == "recovery":
            logger.info(f"RECOVERY_EXECUTED | sat={sat_id} | dv={result.actual_delta_v_ms:.2f}m/s")
            event_log_service.log_recovery_executed(
                sim_time=sim_time,
                satellite_id=sat_id,
                maneuver_id=maneuver.id,
                delta_v_ms=result.actual_delta_v_ms,
            )

        # POST-MANEUVER VERIFICATION (only for evasion maneuvers)
        verification_result = None
        if maneuver.maneuver_type.value == "evasion":
            logger.info(f"VERIFICATION_STARTED | sat={sat_id} | maneuver={maneuver.id}")
            verification_result = self._verify_maneuver_effectiveness(maneuver, sim_time)

            if verification_result.get("verified"):
                logger.info(
                    f"VERIFICATION_SUCCESS | sat={sat_id} | "
                    f"old_miss={verification_result.get('old_miss_m', 0):.1f}m | "
                    f"new_miss={verification_result.get('new_miss_m', 'cleared')}"
                )
            else:
                logger.warning(
                    f"VERIFICATION_FAILED | sat={sat_id} | "
                    f"old_miss={verification_result.get('old_miss_m', 0):.1f}m | "
                    f"new_miss={verification_result.get('new_miss_m', 0):.1f}m | "
                    f"RE-PLANNING REQUIRED"
                )

        exec_result = {
            "maneuver_id": maneuver.id,
            "satellite_id": sat_id,
            "status": "executed",
            "delta_v_actual": result.actual_delta_v_ms,
            "fuel_consumed_kg": result.fuel_consumed_kg,
            "fuel_remaining_kg": result.new_fuel_mass_kg,
            "maneuver_type": maneuver.maneuver_type.value,
        }

        if verification_result:
            exec_result["verification"] = verification_result

        return exec_result

    def get_verification_failures(self) -> dict[str, dict]:
        """Get satellites with verification failures needing re-planning."""
        return self.verification_failures.copy()

    def clear_verification_failure(self, satellite_id: str) -> None:
        """Clear verification failure for a satellite after re-planning."""
        if satellite_id in self.verification_failures:
            del self.verification_failures[satellite_id]

    def get_pending_maneuvers(self) -> list[Maneuver]:
        """Get all pending maneuvers in the queue."""
        return list(self.maneuver_queue)

    def get_pending_sequences(self) -> list[ManeuverSequence]:
        """Get all pending maneuver sequences."""
        return list(self.pending_sequences.values())

    def cancel_sequence(self, sequence_id: str) -> bool:
        """Cancel a pending maneuver sequence."""
        if sequence_id not in self.pending_sequences:
            return False

        sequence = self.pending_sequences[sequence_id]

        # Remove maneuvers from queue
        maneuver_ids = {sequence.evasion.id, sequence.recovery.id}
        self.maneuver_queue = [m for m in self.maneuver_queue if m.id not in maneuver_ids]

        # Remove from commanding if in progress
        for mid in maneuver_ids:
            if mid in self.commanding_maneuvers:
                del self.commanding_maneuvers[mid]

        del self.pending_sequences[sequence_id]
        return True

    def get_satellite_cooldown_status(self, satellite_id: str, sim_time: float) -> dict:
        """Get cooldown status for a satellite."""
        on_cooldown = self._is_on_cooldown(satellite_id, sim_time)
        remaining = self._get_cooldown_remaining(satellite_id, sim_time)
        last_burn = self.cooldowns.get(satellite_id)

        return {
            "satellite_id": satellite_id,
            "on_cooldown": on_cooldown,
            "remaining_seconds": remaining,
            "last_burn_time": last_burn,
            "cooldown_duration": COOLDOWN_SECONDS,
        }


execution_service = ExecutionService()
