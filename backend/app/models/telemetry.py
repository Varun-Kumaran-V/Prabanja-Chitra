from typing import Optional

from pydantic import BaseModel

from .state_vector import StateVector


class Telemetry(BaseModel):
    object_id: str
    timestamp: float
    state: StateVector

    # TLE data for SGP4 propagation (optional for backwards compatibility)
    tle_line1: Optional[str] = None
    tle_line2: Optional[str] = None
    tle_epoch: Optional[float] = None  # Minutes from TLE epoch
