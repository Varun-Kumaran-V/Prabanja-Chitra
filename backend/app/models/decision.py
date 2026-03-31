"""Decision intelligence models for threat prioritization and decision tracking."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ThreatSeverity(str, Enum):
    """Threat severity classification based on composite scoring."""
    CRITICAL = "critical"  # Immediate risk, must handle first
    HIGH = "high"          # High priority, handle after critical
    MEDIUM = "medium"      # Moderate priority
    LOW = "low"            # Low priority, can defer if needed


class FuelStatus(str, Enum):
    """Fuel status classification for decision making."""
    NORMAL = "normal"      # > 30% fuel remaining
    LOW = "low"            # 10-30% fuel remaining
    CRITICAL = "critical"  # < 10% fuel remaining


class SystemOperatingMode(str, Enum):
    """System operating mode for graceful degradation."""
    NOMINAL = "nominal"              # Full capability
    DEGRADED = "degraded"            # Limited capacity, prioritize critical
    EMERGENCY = "emergency"          # Overloaded, critical only


class ThreatScore(BaseModel):
    """Composite threat score for prioritization."""

    conjunction_id: str
    satellite_id: str
    secondary_id: str

    # Individual scoring components (0-100 scale)
    miss_distance_score: float = Field(ge=0, le=100, description="Score based on predicted miss distance")
    time_urgency_score: float = Field(ge=0, le=100, description="Score based on time to TCA")
    velocity_score: float = Field(ge=0, le=100, description="Score based on relative velocity")

    # Composite score (weighted combination)
    composite_score: float = Field(ge=0, le=100, description="Weighted composite threat score")

    # Classification
    severity: ThreatSeverity

    # Raw values for reference
    miss_distance_m: float
    time_to_tca_s: float
    relative_velocity_ms: float

    @classmethod
    def calculate_miss_distance_score(cls, miss_distance_m: float) -> float:
        """Calculate score based on miss distance (closer = higher score)."""
        if miss_distance_m <= 0:
            return 100.0
        elif miss_distance_m < 100:
            return 100.0 - (miss_distance_m / 100) * 10  # 90-100
        elif miss_distance_m < 500:
            return 80.0 - ((miss_distance_m - 100) / 400) * 20  # 60-80
        elif miss_distance_m < 1000:
            return 60.0 - ((miss_distance_m - 500) / 500) * 20  # 40-60
        elif miss_distance_m < 5000:
            return 40.0 - ((miss_distance_m - 1000) / 4000) * 20  # 20-40
        elif miss_distance_m < 10000:
            return 20.0 - ((miss_distance_m - 5000) / 5000) * 10  # 10-20
        else:
            return max(0.0, 10.0 - (miss_distance_m - 10000) / 10000 * 10)  # 0-10

    @classmethod
    def calculate_time_urgency_score(cls, time_to_tca_s: float) -> float:
        """Calculate score based on time to TCA (less time = higher score)."""
        if time_to_tca_s <= 0:
            return 100.0
        elif time_to_tca_s < 1800:  # < 30 minutes
            return 100.0 - (time_to_tca_s / 1800) * 10  # 90-100
        elif time_to_tca_s < 7200:  # < 2 hours
            return 80.0 - ((time_to_tca_s - 1800) / 5400) * 20  # 60-80
        elif time_to_tca_s < 21600:  # < 6 hours
            return 60.0 - ((time_to_tca_s - 7200) / 14400) * 20  # 40-60
        elif time_to_tca_s < 43200:  # < 12 hours
            return 40.0 - ((time_to_tca_s - 21600) / 21600) * 20  # 20-40
        elif time_to_tca_s < 86400:  # < 24 hours
            return 20.0 - ((time_to_tca_s - 43200) / 43200) * 10  # 10-20
        else:
            return max(0.0, 10.0 - (time_to_tca_s - 86400) / 86400 * 10)  # 0-10

    @classmethod
    def calculate_velocity_score(cls, relative_velocity_ms: float) -> float:
        """Calculate score based on relative velocity (higher = more dangerous)."""
        # Typical LEO relative velocities range from ~1 km/s to ~15 km/s
        if relative_velocity_ms <= 0:
            return 0.0
        elif relative_velocity_ms < 1000:  # < 1 km/s (slow approach)
            return (relative_velocity_ms / 1000) * 30  # 0-30
        elif relative_velocity_ms < 5000:  # 1-5 km/s
            return 30.0 + ((relative_velocity_ms - 1000) / 4000) * 30  # 30-60
        elif relative_velocity_ms < 10000:  # 5-10 km/s
            return 60.0 + ((relative_velocity_ms - 5000) / 5000) * 25  # 60-85
        elif relative_velocity_ms < 15000:  # 10-15 km/s (hypervelocity)
            return 85.0 + ((relative_velocity_ms - 10000) / 5000) * 15  # 85-100
        else:
            return 100.0

    @classmethod
    def classify_severity(cls, composite_score: float) -> ThreatSeverity:
        """Classify threat severity based on composite score."""
        if composite_score >= 80:
            return ThreatSeverity.CRITICAL
        elif composite_score >= 60:
            return ThreatSeverity.HIGH
        elif composite_score >= 40:
            return ThreatSeverity.MEDIUM
        else:
            return ThreatSeverity.LOW


class SatelliteFuelStatus(BaseModel):
    """Fuel status for a satellite."""

    satellite_id: str
    current_fuel_kg: float
    initial_fuel_kg: float
    available_fuel_kg: float  # Above reserve
    fuel_fraction: float  # 0-1
    status: FuelStatus
    max_delta_v_available_ms: float
    estimated_maneuvers_remaining: int

    @classmethod
    def classify_status(cls, fuel_fraction: float) -> FuelStatus:
        """Classify fuel status based on remaining fraction."""
        if fuel_fraction < 0.10:
            return FuelStatus.CRITICAL
        elif fuel_fraction < 0.30:
            return FuelStatus.LOW
        else:
            return FuelStatus.NORMAL


class DecisionRecord(BaseModel):
    """Record of a maneuver decision with full explanation."""

    id: str
    timestamp: float  # Simulation time
    satellite_id: str
    conjunction_id: str

    # Decision outcome
    action_taken: str  # "maneuver_scheduled", "deferred", "skipped"

    # Threat assessment
    threat_score: ThreatScore

    # Fuel state at decision time
    fuel_status: SatelliteFuelStatus

    # Decision factors
    decision_factors: dict[str, Any] = Field(default_factory=dict)

    # Expected outcome
    expected_improvement_m: Optional[float] = None
    expected_new_miss_distance_m: Optional[float] = None

    # Maneuver details (if scheduled)
    maneuver_id: Optional[str] = None
    delta_v_planned_ms: Optional[float] = None
    fuel_cost_kg: Optional[float] = None

    # Constraints applied
    constraints_checked: list[str] = Field(default_factory=list)
    constraints_violated: list[str] = Field(default_factory=list)

    # Explanation
    explanation: str = ""

    def generate_explanation(self) -> str:
        """Generate human-readable explanation of the decision."""
        parts = []

        # Threat assessment
        parts.append(
            f"Threat Assessment: {self.threat_score.severity.value.upper()} "
            f"(score: {self.threat_score.composite_score:.1f}/100)"
        )
        parts.append(
            f"  - Miss distance: {self.threat_score.miss_distance_m:.1f}m "
            f"(score: {self.threat_score.miss_distance_score:.1f})"
        )
        parts.append(
            f"  - Time to TCA: {self.threat_score.time_to_tca_s:.0f}s "
            f"(score: {self.threat_score.time_urgency_score:.1f})"
        )
        parts.append(
            f"  - Relative velocity: {self.threat_score.relative_velocity_ms:.1f}m/s "
            f"(score: {self.threat_score.velocity_score:.1f})"
        )

        # Fuel status
        parts.append(
            f"Fuel Status: {self.fuel_status.status.value.upper()} "
            f"({self.fuel_status.fuel_fraction*100:.1f}% remaining)"
        )

        # Decision
        parts.append(f"Action: {self.action_taken.upper()}")

        if self.action_taken == "maneuver_scheduled":
            parts.append(f"  - Delta-V: {self.delta_v_planned_ms:.2f} m/s")
            parts.append(f"  - Fuel cost: {self.fuel_cost_kg:.3f} kg")
            if self.expected_improvement_m:
                parts.append(f"  - Expected improvement: +{self.expected_improvement_m:.1f}m")
        elif self.action_taken == "deferred":
            parts.append(f"  - Reason: {self.decision_factors.get('defer_reason', 'Unknown')}")
        elif self.action_taken == "skipped":
            parts.append(f"  - Reason: {self.decision_factors.get('skip_reason', 'Unknown')}")

        # Constraints
        if self.constraints_violated:
            parts.append(f"Constraints violated: {', '.join(self.constraints_violated)}")

        return "\n".join(parts)


class ConstellationStatus(BaseModel):
    """Constellation-level status for decision making."""

    total_satellites: int
    active_maneuvers: int
    pending_maneuvers: int
    max_concurrent_maneuvers: int

    satellites_by_fuel_status: dict[str, int] = Field(default_factory=dict)
    active_threats_by_severity: dict[str, int] = Field(default_factory=dict)

    operating_mode: SystemOperatingMode
    mode_reason: Optional[str] = None

    # Capacity metrics
    maneuver_capacity_available: int
    capacity_utilization: float  # 0-1


class DecisionSummary(BaseModel):
    """Summary of decision-making activity in a time period."""

    start_time: float
    end_time: float

    total_threats_evaluated: int
    threats_by_severity: dict[str, int] = Field(default_factory=dict)

    maneuvers_scheduled: int
    maneuvers_deferred: int
    maneuvers_skipped: int

    total_fuel_committed_kg: float
    total_delta_v_committed_ms: float

    operating_mode: SystemOperatingMode
    degraded_mode_activations: int = 0
