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

    # Data paths (relative to working directory or absolute)
    # TLE files are in the project root, one level up from backend/
    DATA_DIR: str = os.getenv("DATA_DIR", str(Path(__file__).parent.parent.parent / ""))
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
