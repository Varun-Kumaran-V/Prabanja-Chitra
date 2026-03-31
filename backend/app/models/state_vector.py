from pydantic import BaseModel


class StateVector(BaseModel):
    """Position (km) and velocity (km/s) in an inertial reference frame."""

    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float

    def to_array(self) -> list[float]:
        return [self.x, self.y, self.z, self.vx, self.vy, self.vz]
