"""Conjunction event model for predictive collision assessment."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ConjunctionSeverity(str, Enum):
    """Severity classification for conjunction events."""

    CRITICAL = "critical"  # miss_distance < 100m, requires immediate action
    HIGH = "high"  # miss_distance < 500m
    MEDIUM = "medium"  # miss_distance < 1km
    LOW = "low"  # miss_distance < 10km
    WATCH = "watch"  # miss_distance >= 10km but within screening threshold


class ConjunctionStatus(str, Enum):
    """Status of a conjunction event."""

    DETECTED = "detected"  # Newly detected, no action taken
    AVOIDANCE_PLANNED = "avoidance_planned"  # Maneuver has been planned
    AVOIDANCE_SCHEDULED = "avoidance_scheduled"  # Maneuver is in queue
    MITIGATED = "mitigated"  # Maneuver executed successfully
    PASSED = "passed"  # TCA has passed without incident
    CANCELLED = "cancelled"  # Conjunction no longer valid (orbit changed)


class Conjunction(BaseModel):
    """A predicted conjunction event between a satellite and debris/another object."""

    id: str  # Unique identifier for this conjunction event
    satellite_id: str
    secondary_id: str  # Could be debris or another satellite
    secondary_type: str  # "debris" or "satellite"

    # Time information (all in simulation seconds from epoch)
    detection_time: float  # When the conjunction was first detected
    tca: float  # Time of Closest Approach
    time_to_tca: float  # Seconds until TCA from current sim time

    # Miss distance (meters)
    current_distance_m: float  # Current separation
    predicted_miss_distance_m: float  # Predicted miss at TCA

    # Relative velocity at TCA (m/s)
    relative_velocity_ms: float

    # Position at TCA (for visualization)
    tca_position_x: float
    tca_position_y: float
    tca_position_z: float

    # Classification
    severity: ConjunctionSeverity
    status: ConjunctionStatus = ConjunctionStatus.DETECTED

    # Optional probability of collision (if covariance data available)
    probability_of_collision: Optional[float] = None

    # Associated maneuver IDs (if avoidance was planned)
    evasion_maneuver_id: Optional[str] = None
    recovery_maneuver_id: Optional[str] = None

    @classmethod
    def classify_severity(cls, miss_distance_m: float) -> ConjunctionSeverity:
        """Classify conjunction severity based on predicted miss distance."""
        if miss_distance_m < 100:
            return ConjunctionSeverity.CRITICAL
        elif miss_distance_m < 500:
            return ConjunctionSeverity.HIGH
        elif miss_distance_m < 1000:
            return ConjunctionSeverity.MEDIUM
        elif miss_distance_m < 10000:
            return ConjunctionSeverity.LOW
        else:
            return ConjunctionSeverity.WATCH
