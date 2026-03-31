from app.core.maneuver_planner import maneuver_planner
from app.models import Maneuver
from app.services.conjunction_service import conjunction_service
from app.services.telemetry_service import telemetry_service


class ManeuverService:
    """Generates collision-avoidance maneuvers for all active conjunctions."""

    def generate_maneuvers(self) -> list[Maneuver]:
        """Screen the constellation and return one maneuver per threatened satellite.

        If a satellite appears in multiple conjunction events only the closest
        encounter is used (worst-case planning).
        """
        events = conjunction_service.detect_all_collisions()
        if not events:
            return []

        satellites = telemetry_service.get_all_satellites()

        # Keep only the closest event per satellite (events are pre-sorted)
        closest_per_sat: dict[str, dict] = {}
        for event in events:
            sat_id = event["satellite_id"]
            if sat_id not in closest_per_sat:
                closest_per_sat[sat_id] = event

        maneuvers: list[Maneuver] = []
        for sat_id, event in closest_per_sat.items():
            sat_telemetry = satellites.get(sat_id)
            if sat_telemetry is None:
                continue
            maneuver = maneuver_planner.plan_maneuver(sat_telemetry, event)
            maneuvers.append(maneuver)

        return maneuvers


maneuver_service = ManeuverService()
