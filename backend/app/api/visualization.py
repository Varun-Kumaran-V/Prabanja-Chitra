"""Visualization API endpoints."""

from fastapi import APIRouter

from app.config import settings
from app.services.avoidance_service import avoidance_service
from app.services.conjunction_service import conjunction_service
from app.services.execution_service import execution_service
from app.services.maneuver_service import maneuver_service
from app.services.simulation_service import simulation_service
from app.services.telemetry_service import telemetry_service

router = APIRouter()


@router.get("/snapshot")
async def snapshot():
    """Return the current constellation state for visualisation."""
    satellites = [
        {"id": sid, "x": t.state.x, "y": t.state.y, "z": t.state.z}
        for sid, t in telemetry_service.get_all_satellites().items()
    ]

    debris = [
        {"id": did, "x": t.state.x, "y": t.state.y, "z": t.state.z}
        for did, t in telemetry_service.get_all_debris().items()
    ]

    collisions = conjunction_service.detect_all_collisions()
    maneuvers = [m.model_dump() for m in maneuver_service.generate_maneuvers()]

    return {
        "satellites": satellites,
        "debris": debris,
        "collisions": collisions,
        "maneuvers": maneuvers,
    }


@router.get("/snapshot/full")
async def snapshot_full():
    """Return comprehensive constellation state including avoidance data.

    This endpoint provides all data needed for full visualization
    and status display. Optimized for large debris populations by:
    - Limiting debris count to configurable maximum
    - Excluding velocity data for debris (positions only)
    - Including only essential satellite data
    """
    sim_time = simulation_service.current_time

    # Basic telemetry - satellites with full data
    satellites_data = []
    for sid, t in telemetry_service.get_all_satellites().items():
        meta = telemetry_service.get_satellite_metadata(sid)
        sat_data = {
            "id": sid,
            "x": t.state.x,
            "y": t.state.y,
            "z": t.state.z,
            "vx": t.state.vx,
            "vy": t.state.vy,
            "vz": t.state.vz,
        }
        if meta:
            sat_data["fuel_kg"] = meta.fuel_mass
            sat_data["fuel_fraction"] = meta.fuel_fraction_remaining
            sat_data["is_maneuverable"] = meta.is_maneuverable
        satellites_data.append(sat_data)

    # Debris - positions only, limit count for performance
    all_debris = telemetry_service.get_all_debris()
    debris_items = list(all_debris.items())

    # Limit debris count for performance
    max_debris = settings.MAX_DEBRIS_IN_SNAPSHOT
    if len(debris_items) > max_debris:
        # Sample evenly across the debris set
        step = len(debris_items) // max_debris
        debris_items = debris_items[::step][:max_debris]

    debris_data = [
        {
            "id": did,
            "x": t.state.x,
            "y": t.state.y,
            "z": t.state.z,
        }
        for did, t in debris_items
    ]

    # Current-position collisions (for immediate display)
    collisions = conjunction_service.detect_all_collisions()

    # Predicted conjunctions
    predicted_conjunctions = [
        {
            "id": c.id,
            "satellite_id": c.satellite_id,
            "secondary_id": c.secondary_id,
            "miss_distance_m": c.predicted_miss_distance_m,
            "time_to_tca": c.time_to_tca,
            "severity": c.severity.value,
            "status": c.status.value,
            "tca_position": {
                "x": c.tca_position_x,
                "y": c.tca_position_y,
                "z": c.tca_position_z,
            },
        }
        for c in avoidance_service.get_active_conjunctions()
    ]

    # Pending maneuvers
    pending_maneuvers = [
        {
            "id": m.id,
            "satellite_id": m.satellite_id,
            "delta_v": m.delta_v,
            "direction": m.direction,
            "scheduled_time": m.scheduled_time,
            "type": m.maneuver_type.value,
            "status": m.status.value,
        }
        for m in execution_service.get_pending_maneuvers()
    ]

    # System status
    stats = telemetry_service.get_constellation_stats()

    return {
        "sim_time": sim_time,
        "satellites": satellites_data,
        "debris": debris_data,
        "debris_total_count": len(all_debris),
        "debris_sampled": len(debris_data) < len(all_debris),
        "collisions": collisions,
        "predicted_conjunctions": predicted_conjunctions,
        "pending_maneuvers": pending_maneuvers,
        "avoidance_enabled": simulation_service.avoidance_enabled,
        "constellation_stats": stats,
    }


@router.get("/ground-stations")
async def get_ground_stations():
    """Get all ground station positions for visualization."""
    from app.core.ground_station import ground_station_visibility, DEFAULT_GROUND_STATIONS

    stations = []
    sim_time = simulation_service.current_time

    for station in DEFAULT_GROUND_STATIONS:
        x, y, z = station.get_eci_position(sim_time)
        stations.append({
            "id": station.id,
            "name": station.name,
            "latitude": station.latitude_deg,
            "longitude": station.longitude_deg,
            "x": x,
            "y": y,
            "z": z,
        })

    return {"stations": stations}
