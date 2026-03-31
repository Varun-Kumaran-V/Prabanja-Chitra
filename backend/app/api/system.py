"""System-level aggregation API for hackathon presentation.

Provides high-level overviews and metrics without heavy recomputation.
"""

from fastapi import APIRouter, Query

from app.services.avoidance_service import avoidance_service
from app.services.decision_service import decision_service
from app.services.simulation_service import simulation_service
from app.services.telemetry_service import telemetry_service
from app.services.event_log_service import event_log_service
from app.models.event_log import EventType

router = APIRouter()


# =============================================================================
# SYSTEM SUMMARY
# =============================================================================


@router.get("/summary")
async def get_system_summary():
    """Get high-level system status summary for dashboards.

    Returns aggregate metrics across the entire constellation.
    """
    sim_time = simulation_service.current_time

    # Constellation stats
    constellation_stats = telemetry_service.get_constellation_stats()

    # Conjunction status
    all_conjunctions = avoidance_service.get_active_conjunctions()
    critical_conjunctions = avoidance_service.get_critical_conjunctions()

    # Avoidance status
    avoidance_status = avoidance_service.get_avoidance_status(sim_time)

    # Decision intelligence status
    operating_mode, mode_reason = decision_service.get_operating_mode()
    constellation_status = decision_service.get_constellation_status()

    # Fuel aggregates
    fuel_statuses = decision_service.get_all_fuel_statuses()
    low_fuel_count = sum(1 for s in fuel_statuses.values() if s.status.value in ("low", "critical"))
    critical_fuel_count = sum(1 for s in fuel_statuses.values() if s.status.value == "critical")

    return {
        "timestamp": sim_time,
        "constellation": {
            "total_satellites": constellation_stats["total_satellites"],
            "total_debris": constellation_stats["total_debris"],
            "healthy_satellites": constellation_stats["healthy_satellites"],
            "maneuverable_satellites": constellation_stats["maneuverable_satellites"],
        },
        "threats": {
            "active_conjunctions": len(all_conjunctions),
            "critical_threats": len(critical_conjunctions),
            "unprotected_satellites": len(avoidance_status["unprotected_satellites"]),
        },
        "operations": {
            "maneuvers_in_progress": constellation_status.active_maneuvers,
            "maneuvers_pending": constellation_status.pending_maneuvers,
            "planned_sequences": avoidance_status["planned_sequences"],
            "verification_failures": avoidance_status["verification_failures_pending"],
        },
        "fuel": {
            "total_fuel_kg": constellation_stats["total_fuel_kg"],
            "total_initial_fuel_kg": constellation_stats["total_initial_fuel_kg"],
            "constellation_fuel_fraction": constellation_stats["constellation_fuel_fraction"],
            "low_fuel_satellites": low_fuel_count,
            "critical_fuel_satellites": critical_fuel_count,
        },
        "system_mode": {
            "mode": operating_mode.value,
            "reason": mode_reason,
            "capacity_utilization": constellation_status.capacity_utilization,
        },
        "avoidance_enabled": simulation_service.avoidance_enabled,
    }


# =============================================================================
# RISK OVERVIEW
# =============================================================================


@router.get("/risk")
async def get_risk_overview(top_n: int = Query(default=10, ge=1, le=50)):
    """Get risk overview with highest-priority threats.

    Returns prioritized threats and risk distribution metrics.
    """
    sim_time = simulation_service.current_time

    # Get all conjunctions with threat scores
    conjunctions = avoidance_service.get_active_conjunctions()
    prioritized = decision_service.prioritize_threats(conjunctions)

    # Top N highest-risk threats
    top_threats = []
    for conj, score in prioritized[:top_n]:
        sat_fuel = decision_service.get_satellite_fuel_status(conj.satellite_id)
        top_threats.append({
            "conjunction_id": conj.id,
            "satellite_id": conj.satellite_id,
            "secondary_id": conj.secondary_id,
            "miss_distance_m": conj.predicted_miss_distance_m,
            "time_to_tca_s": conj.time_to_tca,
            "relative_velocity_ms": conj.relative_velocity_ms,
            "threat_score": score.composite_score,
            "severity": score.severity.value,
            "fuel_status": sat_fuel.status.value if sat_fuel else "unknown",
        })

    # Severity distribution
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for _, score in prioritized:
        severity_counts[score.severity.value] += 1

    # Satellites at risk (unique satellites with conjunctions)
    satellites_at_risk = {}
    for conj, score in prioritized:
        sat_id = conj.satellite_id
        if sat_id not in satellites_at_risk or score.composite_score > satellites_at_risk[sat_id]["max_threat_score"]:
            satellites_at_risk[sat_id] = {
                "satellite_id": sat_id,
                "max_threat_score": score.composite_score,
                "max_severity": score.severity.value,
                "conjunction_count": sum(1 for c, _ in prioritized if c.satellite_id == sat_id),
                "min_miss_distance_m": min(
                    c.predicted_miss_distance_m for c, _ in prioritized if c.satellite_id == sat_id
                ),
            }

    # Sort satellites by risk
    satellites_by_risk = sorted(
        satellites_at_risk.values(),
        key=lambda x: x["max_threat_score"],
        reverse=True
    )

    return {
        "timestamp": sim_time,
        "overview": {
            "total_conjunctions": len(conjunctions),
            "total_satellites_at_risk": len(satellites_at_risk),
            "severity_distribution": severity_counts,
        },
        "top_threats": top_threats,
        "satellites_at_highest_risk": satellites_by_risk[:top_n],
    }


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================


@router.get("/metrics")
async def get_performance_metrics():
    """Get system performance metrics and historical statistics.

    Returns aggregated performance data from event logs.
    """
    sim_time = simulation_service.current_time

    # Event log statistics
    event_stats = event_log_service.get_statistics()

    # Conjunction events
    conjunction_events = event_log_service.get_events(
        limit=10000,
        event_types=[
            EventType.CONJUNCTION_DETECTED,
            EventType.CONJUNCTION_CLEARED,
            EventType.CONJUNCTION_PASSED,
        ]
    )

    conjunctions_detected = sum(
        1 for e in conjunction_events if e.event_type == EventType.CONJUNCTION_DETECTED
    )
    conjunctions_cleared = sum(
        1 for e in conjunction_events if e.event_type == EventType.CONJUNCTION_CLEARED
    )
    conjunctions_passed = sum(
        1 for e in conjunction_events if e.event_type == EventType.CONJUNCTION_PASSED
    )

    # Maneuver events
    maneuver_events = event_log_service.get_events(
        limit=10000,
        event_types=[
            EventType.MANEUVER_EXECUTED,
            EventType.MANEUVER_FAILED,
            EventType.MANEUVER_VERIFIED,
            EventType.MANEUVER_VERIFICATION_FAILED,
        ]
    )

    maneuvers_executed = sum(
        1 for e in maneuver_events if e.event_type == EventType.MANEUVER_EXECUTED
    )
    maneuvers_failed = sum(
        1 for e in maneuver_events if e.event_type == EventType.MANEUVER_FAILED
    )
    maneuvers_verified = sum(
        1 for e in maneuver_events if e.event_type == EventType.MANEUVER_VERIFIED
    )
    verification_failures = sum(
        1 for e in maneuver_events if e.event_type == EventType.MANEUVER_VERIFICATION_FAILED
    )

    # Calculate average miss distance improvement from verified maneuvers
    verified_events = [
        e for e in maneuver_events if e.event_type == EventType.MANEUVER_VERIFIED
    ]
    if verified_events:
        improvements = [
            e.details.get("improvement_m", 0) for e in verified_events if e.details
        ]
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0
    else:
        avg_improvement = 0

    # Fuel consumption
    total_fuel_consumed = event_stats.get("total_fuel_consumed_kg", 0)

    # Decision statistics
    decision_stats = decision_service.get_statistics()

    # Success rate
    total_maneuvers = maneuvers_executed + maneuvers_failed
    success_rate = (maneuvers_executed / total_maneuvers * 100) if total_maneuvers > 0 else 0

    verification_rate = (
        (maneuvers_verified / (maneuvers_verified + verification_failures) * 100)
        if (maneuvers_verified + verification_failures) > 0
        else 0
    )

    return {
        "timestamp": sim_time,
        "simulation": {
            "current_time_s": sim_time,
            "step_count": simulation_service.step_count,
        },
        "conjunctions": {
            "total_detected": conjunctions_detected,
            "total_cleared": conjunctions_cleared,
            "total_passed_safely": conjunctions_passed,
            "avoidance_triggered": conjunctions_detected - conjunctions_passed,
        },
        "maneuvers": {
            "total_executed": maneuvers_executed,
            "total_failed": maneuvers_failed,
            "success_rate_pct": round(success_rate, 2),
            "total_verified": maneuvers_verified,
            "verification_failures": verification_failures,
            "verification_success_rate_pct": round(verification_rate, 2),
        },
        "performance": {
            "avg_miss_distance_improvement_m": round(avg_improvement, 2),
            "total_fuel_consumed_kg": round(total_fuel_consumed, 3),
        },
        "decisions": {
            "total_decisions": decision_stats["total_decisions"],
            "by_action": decision_stats["decisions_by_action"],
            "by_severity": decision_stats["decisions_by_severity"],
            "degraded_mode_activations": decision_stats["degraded_mode_activations"],
        },
        "events": {
            "total_logged": event_stats["total_events"],
            "by_type": event_stats["events_by_type"],
            "by_severity": event_stats["events_by_severity"],
        },
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================


@router.get("/health")
async def get_system_health():
    """Get quick system health status for monitoring.

    Returns simplified health indicators.
    """
    sim_time = simulation_service.current_time

    constellation_stats = telemetry_service.get_constellation_stats()
    operating_mode, _ = decision_service.get_operating_mode()
    critical_threats = len(avoidance_service.get_critical_conjunctions())
    unprotected = telemetry_service.get_unprotected_satellites()

    # Determine overall health
    health_status = "healthy"
    health_issues = []

    if operating_mode.value == "emergency":
        health_status = "critical"
        health_issues.append("System in EMERGENCY mode")
    elif operating_mode.value == "degraded":
        health_status = "degraded"
        health_issues.append("System in DEGRADED mode")

    if critical_threats > 5:
        health_status = "warning" if health_status == "healthy" else health_status
        health_issues.append(f"{critical_threats} critical threats detected")

    if len(unprotected) > 0:
        health_status = "critical"
        health_issues.append(f"{len(unprotected)} unprotected satellites")

    if constellation_stats["constellation_fuel_fraction"] < 0.2:
        health_status = "warning" if health_status == "healthy" else health_status
        health_issues.append("Constellation fuel below 20%")

    return {
        "status": health_status,
        "timestamp": sim_time,
        "issues": health_issues,
        "metrics": {
            "satellites": constellation_stats["total_satellites"],
            "critical_threats": critical_threats,
            "unprotected": len(unprotected),
            "fuel_fraction": round(constellation_stats["constellation_fuel_fraction"], 3),
            "operating_mode": operating_mode.value,
        },
    }
