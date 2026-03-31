"""Event logging service for tracking system activities and maintaining history."""

import time
import uuid
from collections import deque
from typing import Any, Optional

from app.models.event_log import (
    EventLog,
    EventType,
    ManeuverRecord,
    FuelHistory,
)


class EventLogService:
    """Service for logging and retrieving system events."""

    def __init__(self, max_events: int = 10000):
        """Initialize the event log service.

        Args:
            max_events: Maximum number of events to retain in memory
        """
        self._events: deque[EventLog] = deque(maxlen=max_events)
        self._maneuver_records: dict[str, ManeuverRecord] = {}
        self._fuel_history: dict[str, FuelHistory] = {}
        self._event_id_counter = 0

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        self._event_id_counter += 1
        return f"EVT-{self._event_id_counter:08d}"

    def log(
        self,
        event_type: EventType,
        message: str,
        sim_time: float,
        satellite_id: Optional[str] = None,
        conjunction_id: Optional[str] = None,
        maneuver_id: Optional[str] = None,
        ground_station_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        severity: str = "info",
    ) -> EventLog:
        """Log an event to the system.

        Args:
            event_type: Type of event
            message: Human-readable message
            sim_time: Simulation time when event occurred
            satellite_id: Associated satellite (if any)
            conjunction_id: Associated conjunction (if any)
            maneuver_id: Associated maneuver (if any)
            ground_station_id: Associated ground station (if any)
            details: Additional structured data
            severity: "debug", "info", "warning", "error", "critical"

        Returns:
            The created EventLog entry
        """
        event = EventLog(
            id=self._generate_event_id(),
            timestamp=sim_time,
            real_time=time.time(),
            event_type=event_type,
            satellite_id=satellite_id,
            conjunction_id=conjunction_id,
            maneuver_id=maneuver_id,
            ground_station_id=ground_station_id,
            message=message,
            details=details,
            severity=severity,
        )

        self._events.append(event)
        return event

    # Convenience methods for common event types

    def log_conjunction_detected(
        self,
        sim_time: float,
        satellite_id: str,
        conjunction_id: str,
        miss_distance_m: float,
        time_to_tca: float,
        secondary_id: str,
    ) -> EventLog:
        """Log detection of a new conjunction."""
        return self.log(
            event_type=EventType.CONJUNCTION_DETECTED,
            message=f"Conjunction detected: {satellite_id} <-> {secondary_id}, "
            f"miss distance {miss_distance_m:.1f}m in {time_to_tca:.0f}s",
            sim_time=sim_time,
            satellite_id=satellite_id,
            conjunction_id=conjunction_id,
            details={
                "secondary_id": secondary_id,
                "miss_distance_m": miss_distance_m,
                "time_to_tca_s": time_to_tca,
            },
            severity="warning" if miss_distance_m < 100 else "info",
        )

    def log_maneuver_planned(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        maneuver_type: str,
        delta_v_ms: float,
        direction: str,
        scheduled_time: float,
        conjunction_id: Optional[str] = None,
    ) -> EventLog:
        """Log planning of a new maneuver."""
        return self.log(
            event_type=EventType.MANEUVER_PLANNED,
            message=f"Maneuver planned for {satellite_id}: {maneuver_type} "
            f"{delta_v_ms:.2f} m/s {direction} at T+{scheduled_time - sim_time:.0f}s",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            conjunction_id=conjunction_id,
            details={
                "maneuver_type": maneuver_type,
                "delta_v_ms": delta_v_ms,
                "direction": direction,
                "scheduled_time": scheduled_time,
            },
        )

    def log_maneuver_executed(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        delta_v_actual_ms: float,
        fuel_consumed_kg: float,
        fuel_remaining_kg: float,
    ) -> EventLog:
        """Log successful execution of a maneuver."""
        return self.log(
            event_type=EventType.MANEUVER_EXECUTED,
            message=f"Maneuver executed for {satellite_id}: {delta_v_actual_ms:.2f} m/s, "
            f"fuel consumed {fuel_consumed_kg:.3f} kg, remaining {fuel_remaining_kg:.3f} kg",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            details={
                "delta_v_actual_ms": delta_v_actual_ms,
                "fuel_consumed_kg": fuel_consumed_kg,
                "fuel_remaining_kg": fuel_remaining_kg,
            },
        )

    def log_maneuver_failed(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        reason: str,
    ) -> EventLog:
        """Log failed maneuver execution."""
        return self.log(
            event_type=EventType.MANEUVER_FAILED,
            message=f"Maneuver failed for {satellite_id}: {reason}",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            details={"reason": reason},
            severity="error",
        )

    def log_recovery_executed(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        delta_v_ms: float,
    ) -> EventLog:
        """Log successful recovery burn."""
        return self.log(
            event_type=EventType.RECOVERY_EXECUTED,
            message=f"Recovery burn executed for {satellite_id}: {delta_v_ms:.2f} m/s",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            details={"delta_v_ms": delta_v_ms},
        )

    def log_fuel_consumed(
        self,
        sim_time: float,
        satellite_id: str,
        fuel_before_kg: float,
        fuel_after_kg: float,
        maneuver_id: Optional[str] = None,
    ) -> EventLog:
        """Log fuel consumption."""
        consumed = fuel_before_kg - fuel_after_kg
        return self.log(
            event_type=EventType.FUEL_CONSUMED,
            message=f"Fuel consumed for {satellite_id}: {consumed:.3f} kg "
            f"({fuel_after_kg:.3f} kg remaining)",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            details={
                "fuel_before_kg": fuel_before_kg,
                "fuel_after_kg": fuel_after_kg,
                "consumed_kg": consumed,
            },
        )

    def log_ground_contact(
        self,
        sim_time: float,
        satellite_id: str,
        station_id: str,
        is_start: bool,
        elevation_deg: float,
    ) -> EventLog:
        """Log ground station contact start/end."""
        event_type = (
            EventType.GROUND_CONTACT_START if is_start else EventType.GROUND_CONTACT_END
        )
        action = "acquired" if is_start else "lost"

        return self.log(
            event_type=event_type,
            message=f"Ground contact {action}: {satellite_id} <-> {station_id} "
            f"at {elevation_deg:.1f}deg elevation",
            sim_time=sim_time,
            satellite_id=satellite_id,
            ground_station_id=station_id,
            details={"elevation_deg": elevation_deg, "is_start": is_start},
        )

    def log_command_sent(
        self,
        sim_time: float,
        satellite_id: str,
        station_id: str,
        maneuver_id: str,
    ) -> EventLog:
        """Log command uplink to satellite."""
        return self.log(
            event_type=EventType.COMMAND_SENT,
            message=f"Command sent to {satellite_id} via {station_id} for maneuver {maneuver_id}",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            ground_station_id=station_id,
        )

    # Post-maneuver verification events

    def log_maneuver_verified(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        old_miss_distance_m: float,
        new_miss_distance_m: float,
        conjunction_id: Optional[str] = None,
    ) -> EventLog:
        """Log successful maneuver verification (miss distance improved)."""
        improvement = old_miss_distance_m - new_miss_distance_m
        return self.log(
            event_type=EventType.MANEUVER_VERIFIED,
            message=f"Maneuver verified for {satellite_id}: miss distance improved "
            f"from {old_miss_distance_m:.1f}m to {new_miss_distance_m:.1f}m (+{improvement:.1f}m)",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            conjunction_id=conjunction_id,
            details={
                "old_miss_distance_m": old_miss_distance_m,
                "new_miss_distance_m": new_miss_distance_m,
                "improvement_m": improvement,
            },
        )

    def log_maneuver_verification_failed(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        old_miss_distance_m: float,
        new_miss_distance_m: float,
        conjunction_id: Optional[str] = None,
    ) -> EventLog:
        """Log failed maneuver verification (miss distance not improved or worsened)."""
        return self.log(
            event_type=EventType.MANEUVER_VERIFICATION_FAILED,
            message=f"Maneuver verification FAILED for {satellite_id}: miss distance "
            f"changed from {old_miss_distance_m:.1f}m to {new_miss_distance_m:.1f}m (no improvement)",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            conjunction_id=conjunction_id,
            details={
                "old_miss_distance_m": old_miss_distance_m,
                "new_miss_distance_m": new_miss_distance_m,
            },
            severity="error",
        )

    def log_maneuver_replanning(
        self,
        sim_time: float,
        satellite_id: str,
        conjunction_id: str,
        reason: str,
    ) -> EventLog:
        """Log re-planning triggered after verification failure."""
        return self.log(
            event_type=EventType.MANEUVER_REPLANNING,
            message=f"Re-planning maneuver for {satellite_id}: {reason}",
            sim_time=sim_time,
            satellite_id=satellite_id,
            conjunction_id=conjunction_id,
            details={"reason": reason},
            severity="warning",
        )

    # Pre-maneuver validation events

    def log_maneuver_validated(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        miss_without_maneuver_m: float,
        miss_with_maneuver_m: float,
        conjunction_id: Optional[str] = None,
    ) -> EventLog:
        """Log successful pre-validation (maneuver improves miss distance)."""
        improvement = miss_without_maneuver_m - miss_with_maneuver_m
        return self.log(
            event_type=EventType.MANEUVER_VALIDATED,
            message=f"Maneuver pre-validated for {satellite_id}: expected improvement "
            f"from {miss_without_maneuver_m:.1f}m to {miss_with_maneuver_m:.1f}m (+{improvement:.1f}m)",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            conjunction_id=conjunction_id,
            details={
                "miss_without_maneuver_m": miss_without_maneuver_m,
                "miss_with_maneuver_m": miss_with_maneuver_m,
                "expected_improvement_m": improvement,
            },
        )

    def log_maneuver_rejected(
        self,
        sim_time: float,
        satellite_id: str,
        maneuver_id: str,
        miss_without_maneuver_m: float,
        miss_with_maneuver_m: float,
        conjunction_id: Optional[str] = None,
    ) -> EventLog:
        """Log rejected maneuver (pre-validation failed, maneuver doesn't improve)."""
        return self.log(
            event_type=EventType.MANEUVER_REJECTED,
            message=f"Maneuver REJECTED for {satellite_id}: would not improve miss distance "
            f"({miss_without_maneuver_m:.1f}m -> {miss_with_maneuver_m:.1f}m)",
            sim_time=sim_time,
            satellite_id=satellite_id,
            maneuver_id=maneuver_id,
            conjunction_id=conjunction_id,
            details={
                "miss_without_maneuver_m": miss_without_maneuver_m,
                "miss_with_maneuver_m": miss_with_maneuver_m,
            },
            severity="warning",
        )

    # LOS failure escalation events

    def log_los_critical_alert(
        self,
        sim_time: float,
        satellite_id: str,
        conjunction_id: str,
        time_to_tca: float,
        miss_distance_m: float,
    ) -> EventLog:
        """Log critical LOS failure alert (critical conjunction with no ground contact)."""
        return self.log(
            event_type=EventType.LOS_CRITICAL_ALERT,
            message=f"CRITICAL: {satellite_id} has critical conjunction (miss {miss_distance_m:.1f}m "
            f"in {time_to_tca:.0f}s) but NO GROUND CONTACT for command uplink",
            sim_time=sim_time,
            satellite_id=satellite_id,
            conjunction_id=conjunction_id,
            details={
                "time_to_tca_s": time_to_tca,
                "miss_distance_m": miss_distance_m,
            },
            severity="critical",
        )

    def log_satellite_unprotected(
        self,
        sim_time: float,
        satellite_id: str,
        conjunction_id: str,
        reason: str,
    ) -> EventLog:
        """Log satellite marked as unprotected."""
        return self.log(
            event_type=EventType.SATELLITE_UNPROTECTED,
            message=f"Satellite {satellite_id} marked UNPROTECTED: {reason}",
            sim_time=sim_time,
            satellite_id=satellite_id,
            conjunction_id=conjunction_id,
            details={"reason": reason},
            severity="critical",
        )

    def log_satellite_protected(
        self,
        sim_time: float,
        satellite_id: str,
    ) -> EventLog:
        """Log satellite protection restored."""
        return self.log(
            event_type=EventType.SATELLITE_PROTECTED,
            message=f"Satellite {satellite_id} protection RESTORED",
            sim_time=sim_time,
            satellite_id=satellite_id,
        )

    # Maneuver record tracking

    def create_maneuver_record(
        self,
        maneuver_id: str,
        satellite_id: str,
        maneuver_type: str,
        planned_time: float,
        scheduled_time: float,
        delta_v_planned_ms: float,
        direction: str,
        fuel_before_kg: float,
        conjunction_id: Optional[str] = None,
    ) -> ManeuverRecord:
        """Create and store a detailed maneuver record."""
        record = ManeuverRecord(
            maneuver_id=maneuver_id,
            satellite_id=satellite_id,
            maneuver_type=maneuver_type,
            planned_time=planned_time,
            scheduled_time=scheduled_time,
            delta_v_planned_ms=delta_v_planned_ms,
            direction=direction,
            fuel_before_kg=fuel_before_kg,
            conjunction_id=conjunction_id,
        )
        self._maneuver_records[maneuver_id] = record
        return record

    def update_maneuver_record(
        self,
        maneuver_id: str,
        **updates: Any,
    ) -> Optional[ManeuverRecord]:
        """Update a maneuver record with execution results."""
        if maneuver_id not in self._maneuver_records:
            return None

        record = self._maneuver_records[maneuver_id]

        # Create updated record
        updated_data = record.model_dump()
        updated_data.update(updates)
        updated_record = ManeuverRecord(**updated_data)

        self._maneuver_records[maneuver_id] = updated_record
        return updated_record

    def get_maneuver_record(self, maneuver_id: str) -> Optional[ManeuverRecord]:
        """Get a maneuver record by ID."""
        return self._maneuver_records.get(maneuver_id)

    # Fuel history tracking

    def init_fuel_history(
        self, satellite_id: str, initial_fuel_kg: float
    ) -> FuelHistory:
        """Initialize fuel history for a satellite."""
        history = FuelHistory(
            satellite_id=satellite_id,
            initial_fuel_kg=initial_fuel_kg,
            current_fuel_kg=initial_fuel_kg,
            total_consumed_kg=0.0,
            burn_count=0,
        )
        self._fuel_history[satellite_id] = history
        return history

    def record_fuel_consumption(
        self,
        satellite_id: str,
        fuel_consumed_kg: float,
        new_fuel_kg: float,
        sim_time: float,
        maneuver_id: Optional[str] = None,
    ) -> Optional[FuelHistory]:
        """Record a fuel consumption event."""
        if satellite_id not in self._fuel_history:
            return None

        history = self._fuel_history[satellite_id]

        # Update history
        updated = FuelHistory(
            satellite_id=satellite_id,
            initial_fuel_kg=history.initial_fuel_kg,
            current_fuel_kg=new_fuel_kg,
            total_consumed_kg=history.total_consumed_kg + fuel_consumed_kg,
            burn_count=history.burn_count + 1,
            last_burn_time=sim_time,
            consumption_records=history.consumption_records
            + [
                {
                    "time": sim_time,
                    "consumed_kg": fuel_consumed_kg,
                    "remaining_kg": new_fuel_kg,
                    "maneuver_id": maneuver_id,
                }
            ],
        )

        self._fuel_history[satellite_id] = updated
        return updated

    def get_fuel_history(self, satellite_id: str) -> Optional[FuelHistory]:
        """Get fuel history for a satellite."""
        return self._fuel_history.get(satellite_id)

    # Query methods

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_types: Optional[list[EventType]] = None,
        satellite_id: Optional[str] = None,
        severity: Optional[str] = None,
        since_sim_time: Optional[float] = None,
    ) -> list[EventLog]:
        """Query events with optional filtering.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            event_types: Filter by event types
            satellite_id: Filter by satellite
            severity: Filter by severity level
            since_sim_time: Only events after this simulation time

        Returns:
            List of matching events, newest first
        """
        events = list(self._events)

        # Apply filters
        if event_types:
            events = [e for e in events if e.event_type in event_types]

        if satellite_id:
            events = [e for e in events if e.satellite_id == satellite_id]

        if severity:
            events = [e for e in events if e.severity == severity]

        if since_sim_time is not None:
            events = [e for e in events if e.timestamp >= since_sim_time]

        # Sort by timestamp descending (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return events[offset : offset + limit]

    def get_recent_maneuvers(
        self, limit: int = 10, satellite_id: Optional[str] = None
    ) -> list[ManeuverRecord]:
        """Get recent maneuver records."""
        records = list(self._maneuver_records.values())

        if satellite_id:
            records = [r for r in records if r.satellite_id == satellite_id]

        # Sort by planned time descending
        records.sort(key=lambda r: r.planned_time, reverse=True)

        return records[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get summary statistics of logged events."""
        events = list(self._events)

        # Count by type
        type_counts: dict[str, int] = {}
        for event in events:
            type_name = event.event_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Count by severity
        severity_counts: dict[str, int] = {}
        for event in events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1

        # Maneuver statistics
        total_maneuvers = len(self._maneuver_records)
        completed_maneuvers = sum(
            1 for r in self._maneuver_records.values() if r.status == "completed"
        )
        failed_maneuvers = sum(
            1 for r in self._maneuver_records.values() if r.status == "failed"
        )

        # Fuel statistics
        total_fuel_consumed = sum(
            h.total_consumed_kg for h in self._fuel_history.values()
        )

        return {
            "total_events": len(events),
            "events_by_type": type_counts,
            "events_by_severity": severity_counts,
            "total_maneuvers": total_maneuvers,
            "completed_maneuvers": completed_maneuvers,
            "failed_maneuvers": failed_maneuvers,
            "total_fuel_consumed_kg": total_fuel_consumed,
            "satellites_with_fuel_history": len(self._fuel_history),
        }

    def clear(self) -> None:
        """Clear all logged events and records."""
        self._events.clear()
        self._maneuver_records.clear()
        self._fuel_history.clear()
        self._event_id_counter = 0


# Singleton instance
event_log_service = EventLogService()
