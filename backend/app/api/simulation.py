"""Simulation API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.simulation_service import simulation_service

router = APIRouter()


class StepRequest(BaseModel):
    dt_seconds: float


@router.post("/step")
async def simulate_step(request: StepRequest):
    """Advance the simulation by the given time step (legacy, no avoidance)."""
    current_time = simulation_service.step(request.dt_seconds)
    return {"status": "ok", "current_time": current_time}


@router.post("/step/auto")
async def simulate_step_with_avoidance(request: StepRequest):
    """Advance the simulation with autonomous avoidance processing.

    This is the main endpoint for the closed-loop avoidance system.
    Each call will:
    1. Propagate all object positions
    2. Predict conjunctions up to 24 hours ahead
    3. Plan avoidance maneuvers for critical conjunctions
    4. Execute scheduled maneuvers (with LOS and cooldown constraints)
    5. Log all events

    Returns comprehensive status including avoidance results.
    """
    result = simulation_service.step_with_avoidance(request.dt_seconds)
    return result


@router.get("/status")
async def get_simulation_status():
    """Get current simulation status."""
    return simulation_service.get_status()


@router.post("/reset")
async def reset_simulation():
    """Reset simulation to initial state."""
    simulation_service.reset()
    return {"status": "ok", "current_time": 0.0}


@router.post("/avoidance/enable")
async def enable_avoidance():
    """Enable autonomous collision avoidance."""
    simulation_service.enable_avoidance()
    return {"avoidance_enabled": True}


@router.post("/avoidance/disable")
async def disable_avoidance():
    """Disable autonomous collision avoidance."""
    simulation_service.disable_avoidance()
    return {"avoidance_enabled": False}
