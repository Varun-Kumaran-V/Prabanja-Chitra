from app.core.conjunction_detector import conjunction_detector, SPATIAL_SCREENING_THRESHOLD_KM
from app.services.telemetry_service import telemetry_service


class ConjunctionService:
    """Detects potential collisions across the full constellation."""

    def detect_all_collisions(
        self, threshold_km: float = SPATIAL_SCREENING_THRESHOLD_KM
    ) -> list[dict]:
        """Screen every satellite against all known debris.

        Returns a list of conjunction alerts sorted by distance (closest first).
        """
        satellites = telemetry_service.get_all_satellites()
        debris = telemetry_service.get_all_debris()

        alerts = conjunction_detector.find_conjunctions(
            satellites, debris, threshold_km
        )
        alerts.sort(key=lambda a: a["distance"])
        return alerts


conjunction_service = ConjunctionService()
