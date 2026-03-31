from fastapi import APIRouter

from app.models import Telemetry
from app.services.telemetry_service import telemetry_service

router = APIRouter()


@router.post("/")
async def ingest_telemetry(telemetry: Telemetry):
    """Receive and store a single telemetry frame."""
    telemetry_service.add_telemetry(telemetry)
    return {"status": "ok", "object_id": telemetry.object_id}
