from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import verify_api_key
from app.schemas import telemetry as schemas
from app.services import telemetry_service

router = APIRouter()


@router.post("/ping", response_model=schemas.TelemetryPingResponse)
def record_telemetry_ping(
    ping_in: schemas.TelemetryPingRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Record telemetry ping from ChurnVision main app.

    Request body:
    - installation_id: Unique installation identifier
    - tenant_slug: Tenant slug identifier
    - active_users_24h: Active users in last 24 hours
    - predictions_24h: Predictions made in last 24 hours
    - error_count_24h: Error count in last 24 hours
    - collection_timestamp: Client-side collection timestamp

    Optional extended fields:
    - api_status, db_status, ollama_status: Service health statuses
    - deployed_version, python_version: Version info
    - recent_errors: List of recent error messages

    Requires API key authentication via X-API-Key header.
    """
    result = telemetry_service.record_ping_from_spec(db=db, ping_in=ping_in)
    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return schemas.TelemetryPingResponse(acknowledged=True)


# Keep internal endpoint for backward compatibility
@router.post("/ping/internal", response_model=schemas.TelemetryPing)
def record_telemetry_ping_internal(
    ping_in: schemas.TelemetryPingCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Internal telemetry endpoint (backward compatible).
    Requires API key authentication.
    """
    return telemetry_service.record_ping(db=db, ping_in=ping_in)
