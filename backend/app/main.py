"""Aether Constellation Manager - FastAPI Application.

Autonomous satellite constellation management with closed-loop collision avoidance.
"""

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.simulation import router as simulation_router
from app.api.telemetry import router as telemetry_router
from app.api.visualization import router as visualization_router
from app.api.avoidance import router as avoidance_router
from app.api.history import router as history_router
from app.api.decisions import router as decisions_router
from app.api.system import router as system_router
from app.config import settings
from app.services.orbit_service import orbit_service
from app.services.event_log_service import event_log_service
from app.models.event_log import EventType

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend service for autonomous satellite constellation management, "
    "orbit propagation, collision avoidance, and mission planning.",
    version=settings.VERSION,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(telemetry_router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(simulation_router, prefix="/api/simulate", tags=["simulation"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])
app.include_router(avoidance_router, prefix="/api/avoidance", tags=["avoidance"])
app.include_router(history_router, prefix="/api/history", tags=["history"])
app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])
app.include_router(system_router, prefix="/api/system", tags=["system"])


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("AETHER CONSTELLATION MANAGER")
    logger.info("Autonomous Collision Avoidance System")
    logger.info("=" * 60)

    # Resolve data directory
    data_dir = Path(settings.DATA_DIR)
    if not data_dir.is_absolute():
        # Make relative to current working directory
        data_dir = Path.cwd() / data_dir

    logger.info(f"Data directory: {data_dir}")

    # Load satellite TLE data
    sat_file = data_dir / settings.SATELLITE_TLE_FILE
    logger.info(f"Loading satellite TLE dataset from: {sat_file}")

    if not sat_file.exists():
        logger.warning(f"Satellite TLE file not found: {sat_file}")
        sat_count = 0
    else:
        sat_count = orbit_service.initialize_from_tle_file(str(sat_file))
        logger.info(f"✓ Loaded {sat_count} satellites")

    # Load debris TLE datasets
    debris_files_str = settings.DEBRIS_TLE_FILES
    debris_file_names = [f.strip() for f in debris_files_str.split(",") if f.strip()]
    debris_files = [data_dir / fname for fname in debris_file_names]

    logger.info(f"Loading debris TLE datasets from {len(debris_files)} file(s)...")

    existing_debris_files = [str(f) for f in debris_files if f.exists()]
    if not existing_debris_files:
        logger.warning("No debris TLE files found")
        debris_count = 0
    else:
        debris_count = orbit_service.initialize_debris_from_tle_file(existing_debris_files)
        logger.info(f"✓ Total: {debris_count} debris objects loaded")

    logger.info(f"Total objects in constellation: {sat_count + debris_count}")

    # Log startup event
    event_log_service.log(
        event_type=EventType.SIMULATION_STARTED,
        message=f"System initialized with {sat_count} satellites and {debris_count} debris objects",
        sim_time=0.0,
        details={
            "satellites": sat_count,
            "debris": debris_count,
        }
    )

    # Print ground stations
    from app.core.ground_station import DEFAULT_GROUND_STATIONS
    logger.info(f"Ground stations configured: {len(DEFAULT_GROUND_STATIONS)}")
    for gs in DEFAULT_GROUND_STATIONS:
        logger.info(f"  - {gs.name} ({gs.latitude_deg:.2f}N, {gs.longitude_deg:.2f}E)")

    # Print system capabilities
    logger.info("-" * 60)
    logger.info("SYSTEM CAPABILITIES:")
    logger.info(f"  - {settings.PREDICTION_HORIZON_SECONDS/3600:.0f}-hour conjunction prediction")
    logger.info(f"  - {settings.MISS_DISTANCE_ALERT_THRESHOLD_M}m avoidance threshold")
    logger.info("  - Evasion + Recovery burn sequences")
    logger.info(f"  - {settings.MAX_DELTA_V_MS} m/s max delta-v per burn")
    logger.info(f"  - {settings.COOLDOWN_SECONDS:.0f}s cooldown between burns")
    logger.info(f"  - {settings.COMMAND_LATENCY_SECONDS:.0f}s command uplink latency")
    logger.info("  - Ground station LOS constraint")
    logger.info("  - Tsiolkovsky fuel depletion")
    logger.info("-" * 60)
    logger.info("DECISION INTELLIGENCE:")
    logger.info(f"  - Threat scoring: distance({settings.THREAT_WEIGHT_MISS_DISTANCE:.0%}) + "
                f"urgency({settings.THREAT_WEIGHT_TIME_URGENCY:.0%}) + "
                f"velocity({settings.THREAT_WEIGHT_VELOCITY:.0%})")
    logger.info(f"  - Fuel thresholds: LOW < {settings.FUEL_LOW_THRESHOLD:.0%}, "
                f"CRITICAL < {settings.FUEL_CRITICAL_THRESHOLD:.0%}")
    logger.info(f"  - Max concurrent maneuvers: {settings.MAX_CONCURRENT_MANEUVERS}")
    logger.info(f"  - Degraded mode at: {settings.DEGRADED_MODE_PENDING_THRESHOLD}+ pending")
    logger.info(f"  - Emergency mode at: {settings.EMERGENCY_MODE_PENDING_THRESHOLD}+ pending")
    logger.info("-" * 60)

    # Print registered routes
    logger.info("API Endpoints:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            logger.info(f"  {methods:12} {route.path}")

    logger.info("=" * 60)
    logger.info(f"Server ready on {settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)


@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """Service health check."""
    from app.services.simulation_service import simulation_service
    from app.services.telemetry_service import telemetry_service

    stats = telemetry_service.get_constellation_stats()

    return {
        "status": "ok",
        "service": "aether-constellation-manager",
        "version": settings.VERSION,
        "simulation_time": simulation_service.current_time,
        "avoidance_enabled": simulation_service.avoidance_enabled,
        "satellites": stats["total_satellites"],
        "debris": stats["total_debris"],
    }


@app.get("/test")
def test():
    """Basic health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
