from typing import Optional
from sqlalchemy.orm import Session
from app.models.telemetry import TelemetryPing
from app.models.tenant import Tenant
from app.schemas.telemetry import TelemetryPingCreate, TelemetryPingRequest


def record_ping(db: Session, ping_in: TelemetryPingCreate) -> TelemetryPing:
    """Record telemetry ping (internal format)"""
    db_ping = TelemetryPing(
        tenant_id=ping_in.tenant_id,
        api_status=ping_in.api_status,
        db_status=ping_in.db_status,
        ollama_status=ping_in.ollama_status,
        active_users_count=ping_in.active_users_count,
        predictions_this_period=ping_in.predictions_this_period,
        api_calls_this_period=ping_in.api_calls_this_period,
        deployed_version=ping_in.deployed_version,
        python_version=ping_in.python_version,
        recent_errors=ping_in.recent_errors,
    )
    db.add(db_ping)
    db.commit()
    db.refresh(db_ping)
    return db_ping


def record_ping_from_spec(
    db: Session, ping_in: TelemetryPingRequest
) -> Optional[TelemetryPing]:
    """
    Record telemetry ping from ChurnVision integration spec format.
    Looks up tenant by slug and maps fields to internal format.
    """
    # Look up tenant by slug
    tenant = db.query(Tenant).filter(Tenant.slug == ping_in.tenant_slug).first()
    if not tenant:
        return None

    # Map spec fields to internal model fields
    db_ping = TelemetryPing(
        tenant_id=tenant.id,
        api_status=ping_in.api_status or "unknown",
        db_status=ping_in.db_status or "unknown",
        ollama_status=ping_in.ollama_status or "unknown",
        active_users_count=ping_in.active_users_24h,
        predictions_this_period=ping_in.predictions_24h,
        api_calls_this_period=0,  # Not in spec, default to 0
        deployed_version=ping_in.deployed_version or "unknown",
        python_version=ping_in.python_version or "unknown",
        recent_errors=ping_in.recent_errors or [],
    )

    # Store additional spec fields in recent_errors as metadata if needed
    # Or add installation_id, error_count_24h to the model in future migration

    db.add(db_ping)
    db.commit()
    db.refresh(db_ping)
    return db_ping
