"""History API endpoints for event logs and audit trail.

Provides endpoints for:
- Querying event history
- Maneuver records
- Fuel consumption history
- Statistics
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.services.event_log_service import event_log_service
from app.models.event_log import EventType

router = APIRouter()


@router.get("/events")
async def get_events(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[str] = None,
    satellite_id: Optional[str] = None,
    severity: Optional[str] = None,
    since_sim_time: Optional[float] = None,
):
    """Query event history with optional filtering.

    Args:
        limit: Maximum number of events to return
        offset: Number of events to skip
        event_type: Filter by event type (e.g., "maneuver_executed")
        satellite_id: Filter by satellite ID
        severity: Filter by severity ("debug", "info", "warning", "error", "critical")
        since_sim_time: Only events after this simulation time
    """
    # Parse event type if provided
    event_types = None
    if event_type:
        try:
            event_types = [EventType(event_type)]
        except ValueError:
            pass

    events = event_log_service.get_events(
        limit=limit,
        offset=offset,
        event_types=event_types,
        satellite_id=satellite_id,
        severity=severity,
        since_sim_time=since_sim_time,
    )

    return {
        "count": len(events),
        "events": [e.model_dump() for e in events],
    }


@router.get("/events/types")
async def get_event_types():
    """Get all available event types."""
    return {
        "types": [e.value for e in EventType],
    }


@router.get("/maneuvers")
async def get_maneuver_history(
    limit: int = Query(default=50, le=500),
    satellite_id: Optional[str] = None,
):
    """Get history of executed maneuvers.

    Args:
        limit: Maximum number of records to return
        satellite_id: Filter by satellite ID
    """
    records = event_log_service.get_recent_maneuvers(
        limit=limit, satellite_id=satellite_id
    )

    return {
        "count": len(records),
        "maneuvers": [r.model_dump() for r in records],
    }


@router.get("/maneuvers/{maneuver_id}")
async def get_maneuver_record(maneuver_id: str):
    """Get detailed record of a specific maneuver."""
    record = event_log_service.get_maneuver_record(maneuver_id)

    if record is None:
        return {"error": "Maneuver not found", "maneuver_id": maneuver_id}

    return record.model_dump()


@router.get("/fuel/{satellite_id}")
async def get_fuel_history(satellite_id: str):
    """Get fuel consumption history for a satellite."""
    history = event_log_service.get_fuel_history(satellite_id)

    if history is None:
        return {
            "satellite_id": satellite_id,
            "error": "No fuel history found",
        }

    return history.model_dump()


@router.get("/statistics")
async def get_statistics():
    """Get summary statistics of all logged events."""
    return event_log_service.get_statistics()


@router.get("/conjunctions/history")
async def get_conjunction_history(
    limit: int = Query(default=50, le=200),
    satellite_id: Optional[str] = None,
):
    """Get history of detected conjunctions."""
    events = event_log_service.get_events(
        limit=limit,
        event_types=[EventType.CONJUNCTION_DETECTED],
        satellite_id=satellite_id,
    )

    return {
        "count": len(events),
        "conjunctions": [
            {
                "event_id": e.id,
                "timestamp": e.timestamp,
                "satellite_id": e.satellite_id,
                "conjunction_id": e.conjunction_id,
                "message": e.message,
                "details": e.details,
            }
            for e in events
        ],
    }


@router.delete("/clear")
async def clear_history():
    """Clear all event history. Use with caution!"""
    event_log_service.clear()
    return {"status": "cleared"}
