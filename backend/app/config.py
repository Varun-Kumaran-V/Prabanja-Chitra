import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application info
    APP_NAME: str = "AETHER – Autonomous Constellation Manager"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Data paths (relative to backend directory or absolute)
    # TLE files are in the backend/data/ folder
    DATA_DIR: str = os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "data"))
    SATELLITE_TLE_FILE: str = os.getenv("SATELLITE_TLE_FILE", "active.txt")
    DEBRIS_TLE_FILES: str = os.getenv(
        "DEBRIS_TLE_FILES",
        "debris_iridium.txt,debris_cosmos.txt,debris_fengyun.txt"
    )

    # Conjunction detection parameters
    PREDICTION_HORIZON_SECONDS: float = 86400.0  # 24 hours
    MISS_DISTANCE_ALERT_THRESHOLD_M: float = 100.0  # 100m
    SPATIAL_SCREENING_THRESHOLD_KM: float = 50.0
    TEMPORAL_SCREENING_THRESHOLD_KM: float = 25.0
    COARSE_PROPAGATION_STEP_SECONDS: float = 300.0  # 5 minutes
    FINE_PROPAGATION_STEP_SECONDS: float = 10.0

    # Maneuver constraints
    MAX_DELTA_V_MS: float = 15.0  # 15 m/s max per burn
    COOLDOWN_SECONDS: float = 600.0  # 10 minutes between burns
    COMMAND_LATENCY_SECONDS: float = 10.0  # Uplink delay
    LOS_CRITICAL_TCA_THRESHOLD_S: float = 1800.0  # 30 minutes

    # Fuel parameters
    DEFAULT_FUEL_MASS_KG: float = 50.0
    DEFAULT_DRY_MASS_KG: float = 500.0
    DEFAULT_ISP_SECONDS: float = 300.0

    # Decision Intelligence parameters
    # Fuel thresholds for decision making
    FUEL_CRITICAL_THRESHOLD: float = 0.10  # Below 10% = critical
    FUEL_LOW_THRESHOLD: float = 0.30       # Below 30% = low

    # Threat scoring weights (must sum to 1.0)
    THREAT_WEIGHT_MISS_DISTANCE: float = 0.50
    THREAT_WEIGHT_TIME_URGENCY: float = 0.35
    THREAT_WEIGHT_VELOCITY: float = 0.15

    # Constellation management
    MAX_CONCURRENT_MANEUVERS: int = 5      # Max simultaneous maneuvers

    # Graceful degradation thresholds
    DEGRADED_MODE_PENDING_THRESHOLD: int = 10   # Enter degraded mode if > 10 pending
    EMERGENCY_MODE_PENDING_THRESHOLD: int = 20  # Enter emergency mode if > 20 pending

    # Performance tuning
    CACHE_PROPAGATION_RESULTS: bool = True
    CACHE_TTL_SECONDS: float = 60.0  # Cache propagation results for 60s
    MAX_DEBRIS_IN_SNAPSHOT: int = 10000  # Limit for visualization

    # ==========================================================================
    # DEMO MODE CONFIGURATION
    # ==========================================================================
    # Demo mode injects controlled scenarios to ensure visible system activity
    # during demonstrations. It influences INPUTS only - all core logic runs normally.

    # Master toggle - enables/disables synthetic conjunction generation
    DEMO_MODE_ENABLED: bool = True

    # Conjunction generation probability per simulation step (0.0-1.0)
    # Higher = more frequent conjunctions
    DEMO_CONJUNCTION_PROBABILITY: float = 0.8

    # Min/max synthetic conjunctions per step when triggered
    DEMO_CONJUNCTION_MIN_PER_STEP: int = 1
    DEMO_CONJUNCTION_MAX_PER_STEP: int = 3

    # Miss distance range for synthetic conjunctions (meters)
    # Values below MISS_DISTANCE_ALERT_THRESHOLD_M (100m) trigger avoidance
    DEMO_MISS_DISTANCE_MIN_M: float = 15.0   # Very close - CRITICAL
    DEMO_MISS_DISTANCE_MAX_M: float = 85.0   # Still critical but less urgent

    # Time to TCA range for synthetic conjunctions (seconds)
    # Shorter = more urgent, triggers faster response
    DEMO_TIME_TO_TCA_MIN_S: float = 1200.0   # 20 minutes (urgent)
    DEMO_TIME_TO_TCA_MAX_S: float = 14400.0  # 4 hours (allows planning)

    # Relative velocity range (m/s) - typical LEO encounters
    DEMO_RELATIVE_VELOCITY_MIN_MS: float = 5000.0   # 5 km/s
    DEMO_RELATIVE_VELOCITY_MAX_MS: float = 14000.0  # 14 km/s

    # Scenario variety - probability of each severity level when generating
    # These sum to 1.0 and control the mix of threat severities
    DEMO_CRITICAL_PROBABILITY: float = 0.5   # 50% CRITICAL (<50m)
    DEMO_HIGH_PROBABILITY: float = 0.35      # 35% HIGH (50-75m)
    DEMO_MEDIUM_PROBABILITY: float = 0.15    # 15% MEDIUM (75-100m)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings instance
settings = Settings()


class DemoModeConfig:
    """Runtime-configurable demo mode settings.

    These can be modified at runtime via API without restarting the server.
    """

    def __init__(self):
        self._enabled = settings.DEMO_MODE_ENABLED
        self._probability = settings.DEMO_CONJUNCTION_PROBABILITY
        self._min_conjunctions = settings.DEMO_CONJUNCTION_MIN_PER_STEP
        self._max_conjunctions = settings.DEMO_CONJUNCTION_MAX_PER_STEP
        self._miss_distance_min = settings.DEMO_MISS_DISTANCE_MIN_M
        self._miss_distance_max = settings.DEMO_MISS_DISTANCE_MAX_M
        self._time_to_tca_min = settings.DEMO_TIME_TO_TCA_MIN_S
        self._time_to_tca_max = settings.DEMO_TIME_TO_TCA_MAX_S
        self._velocity_min = settings.DEMO_RELATIVE_VELOCITY_MIN_MS
        self._velocity_max = settings.DEMO_RELATIVE_VELOCITY_MAX_MS
        self._critical_prob = settings.DEMO_CRITICAL_PROBABILITY
        self._high_prob = settings.DEMO_HIGH_PROBABILITY
        self._medium_prob = settings.DEMO_MEDIUM_PROBABILITY

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def probability(self) -> float:
        return self._probability

    @probability.setter
    def probability(self, value: float):
        self._probability = max(0.0, min(1.0, value))

    @property
    def min_conjunctions(self) -> int:
        return self._min_conjunctions

    @property
    def max_conjunctions(self) -> int:
        return self._max_conjunctions

    @property
    def miss_distance_range(self) -> tuple[float, float]:
        return (self._miss_distance_min, self._miss_distance_max)

    @property
    def time_to_tca_range(self) -> tuple[float, float]:
        return (self._time_to_tca_min, self._time_to_tca_max)

    @property
    def velocity_range(self) -> tuple[float, float]:
        return (self._velocity_min, self._velocity_max)

    @property
    def severity_probabilities(self) -> dict[str, float]:
        return {
            "critical": self._critical_prob,
            "high": self._high_prob,
            "medium": self._medium_prob,
        }

    def set_intensity(self, level: str):
        """Set demo intensity preset.

        Args:
            level: 'low', 'medium', 'high', or 'max'
        """
        presets = {
            "low": {
                "probability": 0.4,
                "min_conj": 1,
                "max_conj": 1,
                "critical_prob": 0.3,
            },
            "medium": {
                "probability": 0.6,
                "min_conj": 1,
                "max_conj": 2,
                "critical_prob": 0.5,
            },
            "high": {
                "probability": 0.8,
                "min_conj": 1,
                "max_conj": 3,
                "critical_prob": 0.6,
            },
            "max": {
                "probability": 1.0,
                "min_conj": 2,
                "max_conj": 3,
                "critical_prob": 0.7,
            },
        }

        if level in presets:
            p = presets[level]
            self._probability = p["probability"]
            self._min_conjunctions = p["min_conj"]
            self._max_conjunctions = p["max_conj"]
            self._critical_prob = p["critical_prob"]
            self._high_prob = (1.0 - p["critical_prob"]) * 0.7
            self._medium_prob = (1.0 - p["critical_prob"]) * 0.3

    def get_status(self) -> dict:
        """Get current demo mode status."""
        return {
            "enabled": self._enabled,
            "probability": self._probability,
            "conjunctions_per_step": {
                "min": self._min_conjunctions,
                "max": self._max_conjunctions,
            },
            "miss_distance_range_m": {
                "min": self._miss_distance_min,
                "max": self._miss_distance_max,
            },
            "time_to_tca_range_s": {
                "min": self._time_to_tca_min,
                "max": self._time_to_tca_max,
            },
            "velocity_range_ms": {
                "min": self._velocity_min,
                "max": self._velocity_max,
            },
            "severity_probabilities": self.severity_probabilities,
        }


# Singleton demo mode configuration
demo_mode_config = DemoModeConfig()
