"""Avoidance system API endpoints.

Provides endpoints for:
- Querying conjunction predictions
- Managing avoidance sequences
- System status and configuration
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.avoidance_service import avoidance_service
from app.services.execution_service import execution_service
from app.services.simulation_service import simulation_service
from app.services.telemetry_service import telemetry_service

router = APIRouter()


class AvoidanceToggleRequest(BaseModel):
    enabled: bool


class CancelAvoidanceRequest(BaseModel):
    conjunction_id: str


@router.get("/status")
async def get_avoidance_status():
    """Get comprehensive avoidance system status."""
    sim_time = simulation_service.current_time
    return avoidance_service.get_avoidance_status(sim_time)


@router.get("/conjunctions")
async def get_conjunctions(critical_only: bool = False):
    """Get all predicted conjunctions.

    Args:
        critical_only: If true, only return conjunctions requiring avoidance
    """
    if critical_only:
        conjunctions = avoidance_service.get_critical_conjunctions()
    else:
        conjunctions = avoidance_service.get_active_conjunctions()

    return {
        "count": len(conjunctions),
        "conjunctions": [c.model_dump() for c in conjunctions],
    }


@router.get("/conjunctions/{conjunction_id}")
async def get_conjunction(conjunction_id: str):
    """Get details of a specific conjunction."""
    conjunctions = avoidance_service.get_active_conjunctions()

    for conj in conjunctions:
        if conj.id == conjunction_id:
            return conj.model_dump()

    raise HTTPException(status_code=404, detail="Conjunction not found")


@router.get("/maneuvers/pending")
async def get_pending_maneuvers():
    """Get all pending maneuvers in the queue."""
    pending = execution_service.get_pending_maneuvers()
    return {
        "count": len(pending),
        "maneuvers": [m.model_dump() for m in pending],
    }


@router.get("/sequences")
async def get_avoidance_sequences():
    """Get all planned avoidance sequences."""
    sequences = avoidance_service.get_planned_sequences()
    return {
        "count": len(sequences),
        "sequences": [s.model_dump() for s in sequences],
    }


@router.post("/cancel")
async def cancel_avoidance(request: CancelAvoidanceRequest):
    """Cancel avoidance for a conjunction."""
    success = avoidance_service.cancel_avoidance(request.conjunction_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No avoidance sequence found for conjunction {request.conjunction_id}",
        )

    return {"status": "cancelled", "conjunction_id": request.conjunction_id}


@router.post("/toggle")
async def toggle_avoidance(request: AvoidanceToggleRequest):
    """Enable or disable autonomous avoidance."""
    if request.enabled:
        simulation_service.enable_avoidance()
    else:
        simulation_service.disable_avoidance()

    return {
        "avoidance_enabled": simulation_service.avoidance_enabled,
    }


@router.get("/satellite/{satellite_id}/status")
async def get_satellite_avoidance_status(satellite_id: str):
    """Get avoidance status for a specific satellite."""
    sim_time = simulation_service.current_time

    # Get cooldown status
    cooldown = execution_service.get_satellite_cooldown_status(satellite_id, sim_time)

    # Get satellite metadata
    metadata = telemetry_service.get_satellite_metadata(satellite_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Satellite not found")

    # Get associated conjunctions
    all_conjunctions = avoidance_service.get_active_conjunctions()
    sat_conjunctions = [c for c in all_conjunctions if c.satellite_id == satellite_id]

    # Get pending maneuvers for this satellite
    pending = execution_service.get_pending_maneuvers()
    sat_maneuvers = [m for m in pending if m.satellite_id == satellite_id]

    # Check if satellite is unprotected
    is_unprotected = telemetry_service.is_unprotected(satellite_id)
    unprotected_info = None
    if is_unprotected:
        unprotected_sats = telemetry_service.get_unprotected_satellites()
        unprotected_info = unprotected_sats.get(satellite_id)

    return {
        "satellite_id": satellite_id,
        "cooldown": cooldown,
        "fuel_status": {
            "current_kg": metadata.fuel_mass,
            "available_kg": metadata.available_fuel,
            "fraction_remaining": metadata.fuel_fraction_remaining,
            "max_delta_v_ms": metadata.calculate_max_delta_v(),
        },
        "active_conjunctions": len(sat_conjunctions),
        "critical_conjunctions": len(
            [c for c in sat_conjunctions if c.predicted_miss_distance_m < 100]
        ),
        "pending_maneuvers": len(sat_maneuvers),
        "is_maneuverable": metadata.is_maneuverable,
        "is_healthy": metadata.is_healthy,
        "is_unprotected": is_unprotected,
        "unprotected_info": unprotected_info,
    }


@router.get("/unprotected")
async def get_unprotected_satellites():
    """Get all satellites currently marked as unprotected.

    A satellite is marked unprotected when:
    - It has a critical conjunction (miss < 100m, TCA < 30 min)
    - AND no ground station contact is available for command uplink

    This is a CRITICAL alert condition.
    """
    unprotected = telemetry_service.get_unprotected_satellites()
    return {
        "count": len(unprotected),
        "satellites": [
            {
                "satellite_id": sat_id,
                **info,
            }
            for sat_id, info in unprotected.items()
        ],
        "severity": "critical" if unprotected else "nominal",
    }


@router.get("/verification-failures")
async def get_verification_failures():
    """Get satellites with verification failures needing re-planning.

    A verification failure occurs when a maneuver was executed but
    did not improve the predicted miss distance as expected.
    """
    failures = execution_service.get_verification_failures()
    return {
        "count": len(failures),
        "failures": [
            {
                "satellite_id": sat_id,
                **info,
            }
            for sat_id, info in failures.items()
        ],
    }


@router.get("/ground-stations")
async def get_ground_stations():
    """Get all configured ground stations."""
    from app.core.ground_station import ground_station_visibility

    stations = list(ground_station_visibility.stations.values())
    return {
        "count": len(stations),
        "stations": [s.model_dump() for s in stations],
    }


@router.get("/satellite/{satellite_id}/visibility")
async def get_satellite_visibility(satellite_id: str):
    """Check current ground station visibility for a satellite."""
    from app.core.ground_station import ground_station_visibility

    sim_time = simulation_service.current_time

    telemetry = telemetry_service.get_satellite(satellite_id)
    if telemetry is None:
        raise HTTPException(status_code=404, detail="Satellite not found")

    visible = ground_station_visibility.find_visible_stations(
        telemetry.state, sim_time
    )

    return {
        "satellite_id": satellite_id,
        "has_contact": len(visible) > 0,
        "visible_stations": [
            {
                "station_id": v.station_id,
                "elevation_deg": v.elevation_deg,
                "azimuth_deg": v.azimuth_deg,
                "range_km": v.range_km,
            }
            for v in visible
        ],
    }
