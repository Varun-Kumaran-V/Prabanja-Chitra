"""Event logging model for tracking system activities."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class EventType(str, Enum):
    """Types of events that can be logged."""

    # Conjunction events
    CONJUNCTION_DETECTED = "conjunction_detected"
    CONJUNCTION_CLEARED = "conjunction_cleared"
    CONJUNCTION_PASSED = "conjunction_passed"

    # Maneuver events
    MANEUVER_PLANNED = "maneuver_planned"
    MANEUVER_SCHEDULED = "maneuver_scheduled"
    MANEUVER_EXECUTING = "maneuver_executing"
    MANEUVER_EXECUTED = "maneuver_executed"
    MANEUVER_FAILED = "maneuver_failed"
    MANEUVER_CANCELLED = "maneuver_cancelled"

    # Post-maneuver verification events
    MANEUVER_VERIFIED = "maneuver_verified"  # Maneuver improved miss distance
    MANEUVER_VERIFICATION_FAILED = "maneuver_verification_failed"  # Maneuver did not improve
    MANEUVER_REPLANNING = "maneuver_replanning"  # Re-planning after failed verification

    # Pre-maneuver validation events
    MANEUVER_VALIDATED = "maneuver_validated"  # Pre-validation passed
    MANEUVER_REJECTED = "maneuver_rejected"  # Pre-validation failed

    # Recovery events
    RECOVERY_PLANNED = "recovery_planned"
    RECOVERY_EXECUTED = "recovery_executed"

    # Fuel events
    FUEL_CONSUMED = "fuel_consumed"
    FUEL_LOW_WARNING = "fuel_low_warning"
    FUEL_DEPLETED = "fuel_depleted"

    # Communication events
    GROUND_CONTACT_START = "ground_contact_start"
    GROUND_CONTACT_END = "ground_contact_end"
    COMMAND_SENT = "command_sent"
    COMMAND_RECEIVED = "command_received"

    # LOS failure escalation events
    LOS_CRITICAL_ALERT = "los_critical_alert"  # Critical conjunction, no LOS
    SATELLITE_UNPROTECTED = "satellite_unprotected"  # Satellite marked unprotected
    SATELLITE_PROTECTED = "satellite_protected"  # Satellite protection restored

    # System events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_STEP = "simulation_step"
    AVOIDANCE_CYCLE_COMPLETE = "avoidance_cycle_complete"


class EventLog(BaseModel):
    """A single logged event in the system."""

    id: str  # Unique event ID
    timestamp: float  # Simulation time when event occurred
    real_time: float  # Wall-clock time when event was logged
    event_type: EventType

    # Entity references
    satellite_id: Optional[str] = None
    conjunction_id: Optional[str] = None
    maneuver_id: Optional[str] = None
    ground_station_id: Optional[str] = None

    # Event details
    message: str
    details: Optional[dict[str, Any]] = None

    # Severity for filtering/alerting
    severity: str = "info"  # "debug", "info", "warning", "error", "critical"


class ManeuverRecord(BaseModel):
    """Detailed record of a maneuver execution."""

    maneuver_id: str
    satellite_id: str
    maneuver_type: str  # "evasion" or "recovery"

    # Timing
    planned_time: float
    scheduled_time: float
    execution_time: Optional[float] = None
    completion_time: Optional[float] = None

    # Burn parameters
    delta_v_planned_ms: float
    delta_v_actual_ms: Optional[float] = None
    direction: str

    # Fuel
    fuel_before_kg: float
    fuel_after_kg: Optional[float] = None
    fuel_consumed_kg: Optional[float] = None

    # Status
    status: str = "planned"  # "planned", "scheduled", "executing", "completed", "failed"
    failure_reason: Optional[str] = None

    # Associated conjunction
    conjunction_id: Optional[str] = None

    # Ground station used for command uplink
    command_station_id: Optional[str] = None


class FuelHistory(BaseModel):
    """Fuel consumption history for a satellite."""

    satellite_id: str
    initial_fuel_kg: float
    current_fuel_kg: float
    total_consumed_kg: float
    burn_count: int
    last_burn_time: Optional[float] = None
    consumption_records: list[dict[str, Any]] = []
