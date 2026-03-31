from pydantic import BaseModel

from .state_vector import StateVector


class Debris(BaseModel):
    id: str
    state: StateVector
