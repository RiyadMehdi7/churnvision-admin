from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class TelemetryPingBase(BaseModel):
    """Base telemetry fields (internal use)"""

    api_status: str
    db_status: str
    ollama_status: str
    active_users_count: int
    predictions_this_period: int
    api_calls_this_period: int
    deployed_version: str
    python_version: str
    recent_errors: List[str] = []


class TelemetryPingCreate(TelemetryPingBase):
    """Internal telemetry creation schema"""

    tenant_id: UUID


class TelemetryPing(TelemetryPingBase):
    """Internal telemetry response"""

    id: UUID
    tenant_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True


# ===== ChurnVision Integration Spec Compliant Schemas =====


class TelemetryPingRequest(BaseModel):
    """
    Telemetry ping request from ChurnVision main app.
    Matches the ChurnVision integration specification.
    """

    installation_id: str = Field(..., description="Unique installation identifier")
    tenant_slug: str = Field(..., description="Tenant slug identifier")
    active_users_24h: int = Field(0, description="Active users in last 24 hours")
    predictions_24h: int = Field(0, description="Predictions made in last 24 hours")
    error_count_24h: int = Field(0, description="Error count in last 24 hours")
    collection_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Client-side collection timestamp"
    )

    # Optional extended fields (for compatibility with existing data)
    api_status: Optional[str] = Field(None, description="API health status")
    db_status: Optional[str] = Field(None, description="Database health status")
    ollama_status: Optional[str] = Field(None, description="Ollama service status")
    deployed_version: Optional[str] = Field(None, description="Deployed app version")
    python_version: Optional[str] = Field(None, description="Python version")
    recent_errors: Optional[List[str]] = Field(
        default_factory=list, description="Recent error messages"
    )


class TelemetryPingResponse(BaseModel):
    """
    Telemetry ping response.
    Matches the ChurnVision integration specification.
    """

    acknowledged: bool = True
