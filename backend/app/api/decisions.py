"""Decision Intelligence API endpoints.

Provides endpoints for:
- Querying decision records
- Getting threat scorings
- Viewing fuel statuses
- System operating mode status
- Decision summaries
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.decision_service import decision_service
from app.services.simulation_service import simulation_service
from app.services.avoidance_service import avoidance_service
from app.models.decision import ThreatSeverity, SystemOperatingMode

router = APIRouter()


class ForceDegradedModeRequest(BaseModel):
    reason: str


class ThreatScoreRequest(BaseModel):
    conjunction_id: str


# =============================================================================
# DECISIONS ENDPOINTS
# =============================================================================


@router.get("")
async def get_decisions(
    limit: int = Query(default=50, ge=1, le=500),
    severity: Optional[str] = Query(default=None, description="Filter by severity: critical, high, medium, low"),
    action: Optional[str] = Query(default=None, description="Filter by action: maneuver_scheduled, deferred, skipped"),
):
    """Get recent decisions with optional filtering.

    Returns list of decision records with full explanation.
    """
    severity_enum = None
    if severity:
        try:
            severity_enum = ThreatSeverity(severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}. Must be one of: critical, high, medium, low"
            )

    decisions = decision_service.get_recent_decisions(
        limit=limit,
        severity=severity_enum,
        action=action,
    )

    return {
        "count": len(decisions),
        "decisions": [d.model_dump() for d in decisions],
    }


@router.get("/summary")
async def get_decision_summary(
    hours: float = Query(default=1.0, ge=0.1, le=24, description="Time period in hours"),
):
    """Get summary of decision-making activity.

    Returns aggregated statistics for the specified time period.
    """
    sim_time = simulation_service.current_time
    start_time = max(0, sim_time - (hours * 3600))

    summary = decision_service.get_decision_summary(start_time, sim_time)

    return summary.model_dump()


@router.get("/statistics")
async def get_decision_statistics():
    """Get overall decision service statistics.

    Returns comprehensive statistics about all decisions made.
    """
    return decision_service.get_statistics()


@router.get("/{satellite_id}")
async def get_satellite_decisions(
    satellite_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get decisions for a specific satellite.

    Returns decision history for the satellite, including threat assessments
    and explanations.
    """
    decisions = decision_service.get_decisions_for_satellite(satellite_id, limit)

    if not decisions:
        # Check if satellite exists
        from app.services.telemetry_service import telemetry_service
        if telemetry_service.get_satellite(satellite_id) is None:
            raise HTTPException(status_code=404, detail=f"Satellite {satellite_id} not found")

    return {
        "satellite_id": satellite_id,
        "count": len(decisions),
        "decisions": [d.model_dump() for d in decisions],
    }


@router.get("/conjunction/{conjunction_id}")
async def get_conjunction_decision(conjunction_id: str):
    """Get the decision made for a specific conjunction.

    Returns full decision record with threat score and explanation.
    """
    decision = decision_service.get_decision_for_conjunction(conjunction_id)

    if decision is None:
        raise HTTPException(
            status_code=404,
            detail=f"No decision found for conjunction {conjunction_id}"
        )

    return decision.model_dump()


# =============================================================================
# THREAT SCORING ENDPOINTS
# =============================================================================


@router.get("/threats/scores")
async def get_threat_scores():
    """Get threat scores for all active conjunctions.

    Returns prioritized list of conjunctions with composite scores.
    """
    conjunctions = avoidance_service.get_active_conjunctions()

    prioritized = decision_service.prioritize_threats(conjunctions)

    return {
        "count": len(prioritized),
        "threats": [
            {
                "conjunction_id": conj.id,
                "satellite_id": conj.satellite_id,
                "secondary_id": conj.secondary_id,
                "threat_score": score.model_dump(),
            }
            for conj, score in prioritized
        ],
    }


@router.get("/threats/critical")
async def get_critical_threats():
    """Get only CRITICAL severity threats.

    Returns conjunctions that require immediate attention.
    """
    conjunctions = avoidance_service.get_active_conjunctions()
    prioritized = decision_service.prioritize_threats(conjunctions)

    critical = [
        (conj, score) for conj, score in prioritized
        if score.severity == ThreatSeverity.CRITICAL
    ]

    return {
        "count": len(critical),
        "threats": [
            {
                "conjunction_id": conj.id,
                "satellite_id": conj.satellite_id,
                "secondary_id": conj.secondary_id,
                "miss_distance_m": conj.predicted_miss_distance_m,
                "time_to_tca_s": conj.time_to_tca,
                "score": score.composite_score,
                "threat_score": score.model_dump(),
            }
            for conj, score in critical
        ],
    }


@router.post("/threats/score")
async def calculate_threat_score(request: ThreatScoreRequest):
    """Calculate threat score for a specific conjunction.

    Returns detailed scoring breakdown.
    """
    # Find the conjunction
    conjunctions = avoidance_service.get_active_conjunctions()
    target_conj = None
    for conj in conjunctions:
        if conj.id == request.conjunction_id:
            target_conj = conj
            break

    if target_conj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conjunction {request.conjunction_id} not found"
        )

    score = decision_service.calculate_threat_score(target_conj)

    return {
        "conjunction_id": target_conj.id,
        "threat_score": score.model_dump(),
    }


# =============================================================================
# FUEL STATUS ENDPOINTS
# =============================================================================


@router.get("/fuel/status")
async def get_all_fuel_statuses():
    """Get fuel status for all satellites.

    Returns classification (NORMAL/LOW/CRITICAL) and metrics for each satellite.
    """
    statuses = decision_service.get_all_fuel_statuses()

    # Aggregate counts
    by_status = {"normal": 0, "low": 0, "critical": 0}
    for status in statuses.values():
        by_status[status.status.value] += 1

    return {
        "count": len(statuses),
        "by_status": by_status,
        "satellites": {
            sat_id: status.model_dump()
            for sat_id, status in statuses.items()
        },
    }


@router.get("/fuel/status/{satellite_id}")
async def get_satellite_fuel_status(satellite_id: str):
    """Get fuel status for a specific satellite.

    Returns detailed fuel metrics and classification.
    """
    status = decision_service.get_satellite_fuel_status(satellite_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"Satellite {satellite_id} not found")

    return status.model_dump()


@router.get("/fuel/critical")
async def get_critical_fuel_satellites():
    """Get satellites with CRITICAL fuel status.

    These satellites will skip non-critical threats to preserve fuel.
    """
    statuses = decision_service.get_all_fuel_statuses()

    critical = {
        sat_id: status.model_dump()
        for sat_id, status in statuses.items()
        if status.status.value == "critical"
    }

    return {
        "count": len(critical),
        "satellites": critical,
    }


@router.get("/fuel/low")
async def get_low_fuel_satellites():
    """Get satellites with LOW or CRITICAL fuel status.

    These satellites have restricted maneuver capability.
    """
    statuses = decision_service.get_all_fuel_statuses()

    low_or_critical = {
        sat_id: status.model_dump()
        for sat_id, status in statuses.items()
        if status.status.value in ("low", "critical")
    }

    return {
        "count": len(low_or_critical),
        "satellites": low_or_critical,
    }


# =============================================================================
# CONSTELLATION STATUS ENDPOINTS
# =============================================================================


@router.get("/constellation/status")
async def get_constellation_status():
    """Get constellation-level status for decision making.

    Includes maneuver capacity, operating mode, and aggregate metrics.
    """
    status = decision_service.get_constellation_status()
    return status.model_dump()


@router.get("/mode")
async def get_operating_mode():
    """Get current system operating mode.

    Returns NOMINAL, DEGRADED, or EMERGENCY with explanation.
    """
    mode, reason = decision_service.get_operating_mode()

    return {
        "mode": mode.value,
        "reason": reason,
        "description": {
            "nominal": "Full system capability, all threats processed",
            "degraded": "Limited capacity, LOW priority threats deferred",
            "emergency": "Overloaded, only CRITICAL threats processed",
        }.get(mode.value, "Unknown"),
    }


@router.post("/mode/degraded")
async def force_degraded_mode(request: ForceDegradedModeRequest):
    """Force system into degraded mode.

    Use this to manually limit system capacity.
    """
    decision_service.force_degraded_mode(request.reason)
    mode, reason = decision_service.get_operating_mode()

    return {
        "status": "ok",
        "mode": mode.value,
        "reason": reason,
    }


@router.post("/mode/clear")
async def clear_degraded_mode():
    """Clear forced degraded mode if conditions allow.

    System will return to nominal if load is acceptable.
    """
    decision_service.clear_degraded_mode()
    mode, reason = decision_service.get_operating_mode()

    return {
        "status": "ok",
        "mode": mode.value,
        "reason": reason,
    }


# =============================================================================
# DECISION EXPLANATION ENDPOINTS
# =============================================================================


@router.get("/explain/{decision_id}")
async def explain_decision(decision_id: str):
    """Get detailed explanation for a decision.

    Returns human-readable explanation of why the decision was made.
    """
    decision = decision_service.get_decision(decision_id)

    if decision is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

    return {
        "decision_id": decision_id,
        "satellite_id": decision.satellite_id,
        "conjunction_id": decision.conjunction_id,
        "action": decision.action_taken,
        "explanation": decision.explanation,
        "threat_score": decision.threat_score.model_dump(),
        "fuel_status": decision.fuel_status.model_dump(),
        "decision_factors": decision.decision_factors,
        "constraints_checked": decision.constraints_checked,
        "constraints_violated": decision.constraints_violated,
    }
