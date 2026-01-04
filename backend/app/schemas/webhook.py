from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

class WebhookBase(BaseModel):
    name: str
    url: str
    events: List[str] = []
    tenant_id: Optional[UUID] = None

class WebhookCreate(WebhookBase):
    secret: Optional[str] = None

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None
    tenant_id: Optional[UUID] = None

class Webhook(WebhookBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebhookWithSecret(Webhook):
    secret: Optional[str] = None

class WebhookDeliveryResponse(BaseModel):
    id: UUID
    webhook_id: UUID
    event_type: str
    payload: Dict[str, Any]
    response_status: Optional[str] = None
    success: bool
    delivered_at: datetime

    class Config:
        from_attributes = True

class WebhookTestRequest(BaseModel):
    event_type: str = "test.ping"

class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response: Optional[str] = None
    error: Optional[str] = None

class WebhookEventPayload(BaseModel):
    event_type: str
    timestamp: str
    data: Dict[str, Any]


class WebhookEventTrigger(BaseModel):
    """Schema for manually triggering a webhook event"""
    event_type: str
    data: Dict[str, Any]
    tenant_id: Optional[str] = None


# List of all available event types
AVAILABLE_EVENTS = [
    "tenant.created",
    "tenant.updated",
    "tenant.deleted",
    "tenant.status_changed",
    "license.issued",
    "license.revoked",
    "license.expired",
    "license.expiring_soon",
    "subscription.created",
    "subscription.cancelled",
    "subscription.renewed",
    "invoice.created",
    "invoice.paid",
    "invoice.overdue",
    "release.published",
    "release.deprecated",
    "ticket.created",
    "ticket.updated",
    "telemetry.tenant_unhealthy",
]
