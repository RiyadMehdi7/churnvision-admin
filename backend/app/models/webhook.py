import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
from app.core.db import Base

class WebhookEventType(str, enum.Enum):
    # Tenant events
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"
    TENANT_STATUS_CHANGED = "tenant.status_changed"

    # License events
    LICENSE_ISSUED = "license.issued"
    LICENSE_REVOKED = "license.revoked"
    LICENSE_EXPIRED = "license.expired"
    LICENSE_EXPIRING_SOON = "license.expiring_soon"

    # Subscription events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_RENEWED = "subscription.renewed"

    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"

    # Release events
    RELEASE_PUBLISHED = "release.published"
    RELEASE_DEPRECATED = "release.deprecated"

    # Support events
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"

    # Telemetry events
    TENANT_UNHEALTHY = "telemetry.tenant_unhealthy"


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    secret = Column(String, nullable=True)  # For HMAC signature verification
    events = Column(ARRAY(String), default=[])  # List of event types to subscribe to
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional filters
    tenant_id = Column(UUID(as_uuid=True), nullable=True)  # Filter events for specific tenant


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    response_status = Column(String, nullable=True)
    response_body = Column(String, nullable=True)
    delivered_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    retry_count = Column(String, default="0")
