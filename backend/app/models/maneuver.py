from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel


class ManeuverType(str, Enum):
    """Type of maneuver in the avoidance sequence."""

    EVASION = "evasion"  # Initial burn to avoid conjunction
    RECOVERY = "recovery"  # Follow-up burn to restore original orbit
    STATION_KEEPING = "station_keeping"  # Routine orbit maintenance
    EMERGENCY = "emergency"  # Emergency avoidance burn


class ManeuverStatus(str, Enum):
    """Execution status of a maneuver."""

    PLANNED = "planned"  # Computed but not yet scheduled
    SCHEDULED = "scheduled"  # In execution queue
    PENDING_LOS = "pending_los"  # Waiting for ground station contact
    COMMANDING = "commanding"  # Command being uploaded
    EXECUTING = "executing"  # Burn in progress
    COMPLETED = "completed"  # Successfully executed
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # Cancelled before execution


class Maneuver(BaseModel):
    """A satellite maneuver command."""

    id: str  # Unique maneuver identifier
    satellite_id: str

    # Burn parameters
    delta_v: float  # m/s
    direction: Literal["prograde", "retrograde", "radial", "normal"]

    # Custom delta-v vector (alternative to direction, in velocity frame)
    delta_v_vector: Optional[tuple[float, float, float]] = None  # (tangential, normal, radial)

    # Timing (all in simulation seconds)
    planned_time: float  # When the maneuver was computed
    scheduled_time: float  # When the burn should execute
    execution_time: Optional[float] = None  # When the burn actually started
    completion_time: Optional[float] = None  # When the burn completed

    # Type and status
    maneuver_type: ManeuverType = ManeuverType.EVASION
    status: ManeuverStatus = ManeuverStatus.PLANNED

    # Fuel tracking
    estimated_fuel_kg: Optional[float] = None  # Pre-computed fuel requirement
    actual_fuel_kg: Optional[float] = None  # Actual fuel consumed

    # Associated conjunction (for traceability)
    conjunction_id: Optional[str] = None

    # Recovery burn linkage
    paired_maneuver_id: Optional[str] = None  # Links evasion to recovery

    # Ground station for command uplink
    command_station_id: Optional[str] = None
    command_sent_time: Optional[float] = None

    # Error tracking
    failure_reason: Optional[str] = None

    @property
    def is_evasion(self) -> bool:
        return self.maneuver_type == ManeuverType.EVASION

    @property
    def is_recovery(self) -> bool:
        return self.maneuver_type == ManeuverType.RECOVERY

    @property
    def is_pending(self) -> bool:
        return self.status in (
            ManeuverStatus.PLANNED,
            ManeuverStatus.SCHEDULED,
            ManeuverStatus.PENDING_LOS,
        )

    @property
    def is_complete(self) -> bool:
        return self.status == ManeuverStatus.COMPLETED


class ManeuverSequence(BaseModel):
    """A complete avoidance maneuver sequence (evasion + recovery)."""

    id: str
    satellite_id: str
    conjunction_id: str

    evasion: Maneuver
    recovery: Maneuver

    # Sequence timing
    created_time: float
    estimated_completion_time: float

    # Total fuel budget
    total_estimated_fuel_kg: float

    # Status helpers
    @property
    def is_complete(self) -> bool:
        return self.evasion.is_complete and self.recovery.is_complete

    @property
    def status(self) -> str:
        if self.evasion.status == ManeuverStatus.CANCELLED:
            return "cancelled"
        if not self.evasion.is_complete:
            return f"evasion_{self.evasion.status.value}"
        if not self.recovery.is_complete:
            return f"recovery_{self.recovery.status.value}"
        return "complete"
