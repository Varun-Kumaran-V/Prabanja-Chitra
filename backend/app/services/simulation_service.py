"""Simulation service with integrated autonomous avoidance loop.

Drives the constellation simulation clock and executes the closed-loop
avoidance system on each step.
"""

from app.services.orbit_service import orbit_service
from app.services.avoidance_service import avoidance_service
from app.services.event_log_service import event_log_service
from app.models.event_log import EventType


class SimulationService:
    """Drives the constellation simulation clock and per-step processing."""

    def __init__(self) -> None:
        self.current_time: float = 0.0
        self.step_count: int = 0
        self.avoidance_enabled: bool = True

    def step(self, dt_seconds: float) -> float:
        """Advance the simulation by *dt_seconds*.

        Propagates all satellite orbits and returns the new simulation time.
        If avoidance is enabled, also runs the autonomous avoidance cycle.
        """
        # Update simulation clock
        self.current_time += dt_seconds
        self.step_count += 1

        # Propagate all objects
        orbit_service.propagate_all(dt_seconds)

        return self.current_time

    def step_with_avoidance(self, dt_seconds: float) -> dict:
        """Advance the simulation with full avoidance processing.

        This is the main entry point for the autonomous system.

        Args:
            dt_seconds: Time step in seconds

        Returns:
            Dictionary with simulation status and avoidance results
        """
        # Update simulation clock
        self.current_time += dt_seconds
        self.step_count += 1

        # Propagate all objects
        objects_updated = orbit_service.propagate_all(dt_seconds)

        result = {
            "current_time": self.current_time,
            "step_count": self.step_count,
            "objects_propagated": objects_updated,
            "avoidance_enabled": self.avoidance_enabled,
        }

        # Run avoidance cycle if enabled
        if self.avoidance_enabled:
            avoidance_result = avoidance_service.run_avoidance_cycle(self.current_time)
            result["avoidance"] = avoidance_result

        return result

    def enable_avoidance(self) -> None:
        """Enable autonomous collision avoidance."""
        self.avoidance_enabled = True
        event_log_service.log(
            event_type=EventType.SIMULATION_STARTED,
            message="Autonomous avoidance enabled",
            sim_time=self.current_time,
        )

    def disable_avoidance(self) -> None:
        """Disable autonomous collision avoidance."""
        self.avoidance_enabled = False
        event_log_service.log(
            event_type=EventType.SIMULATION_STARTED,
            message="Autonomous avoidance disabled",
            sim_time=self.current_time,
        )

    def reset(self) -> None:
        """Reset simulation to initial state."""
        self.current_time = 0.0
        self.step_count = 0

    def get_status(self) -> dict:
        """Get current simulation status."""
        return {
            "current_time": self.current_time,
            "step_count": self.step_count,
            "avoidance_enabled": self.avoidance_enabled,
            "avoidance_status": avoidance_service.get_avoidance_status(self.current_time)
            if self.avoidance_enabled
            else None,
        }


simulation_service = SimulationService()
