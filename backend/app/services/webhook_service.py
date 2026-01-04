import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx

from app.models.webhook import Webhook, WebhookDelivery
from app.schemas.webhook import WebhookCreate, WebhookUpdate

logger = logging.getLogger(__name__)

# Timeout for webhook delivery
WEBHOOK_TIMEOUT = 10.0  # seconds


def get_webhooks(db: Session, skip: int = 0, limit: int = 100) -> List[Webhook]:
    return db.query(Webhook).offset(skip).limit(limit).all()


def get_webhook_by_id(db: Session, webhook_id: str) -> Optional[Webhook]:
    return db.query(Webhook).filter(Webhook.id == webhook_id).first()


def get_active_webhooks_for_event(db: Session, event_type: str, tenant_id: Optional[str] = None) -> List[Webhook]:
    """Get all active webhooks that are subscribed to the given event type"""
    query = db.query(Webhook).filter(
        Webhook.is_active == True,
        Webhook.events.contains([event_type])
    )

    # Return webhooks that either have no tenant filter or match the tenant
    if tenant_id:
        query = query.filter(
            (Webhook.tenant_id == None) | (Webhook.tenant_id == tenant_id)
        )
    else:
        query = query.filter(Webhook.tenant_id == None)

    return query.all()


def create_webhook(db: Session, webhook_in: WebhookCreate) -> Webhook:
    db_webhook = Webhook(
        name=webhook_in.name,
        url=webhook_in.url,
        secret=webhook_in.secret,
        events=webhook_in.events,
        tenant_id=webhook_in.tenant_id,
    )
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


def update_webhook(db: Session, webhook: Webhook, webhook_in: WebhookUpdate) -> Webhook:
    update_data = webhook_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(webhook, field, value)
    db.commit()
    db.refresh(webhook)
    return webhook


def delete_webhook(db: Session, webhook: Webhook) -> None:
    db.delete(webhook)
    db.commit()


def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


async def deliver_webhook(
    db: Session,
    webhook: Webhook,
    event_type: str,
    data: Dict[str, Any]
) -> WebhookDelivery:
    """Deliver a webhook event to the registered URL"""
    payload = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    payload_json = json.dumps(payload)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_type,
    }

    # Add signature if secret is configured
    if webhook.secret:
        signature = generate_signature(payload_json, webhook.secret)
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=payload,
        success=False,
    )

    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            response = await client.post(
                webhook.url,
                content=payload_json,
                headers=headers,
            )
            delivery.response_status = str(response.status_code)
            delivery.response_body = response.text[:1000] if response.text else None
            delivery.success = 200 <= response.status_code < 300

    except httpx.TimeoutException:
        delivery.response_status = "TIMEOUT"
        delivery.response_body = "Request timed out"
        logger.error(f"Webhook delivery timeout: {webhook.url}")

    except httpx.RequestError as e:
        delivery.response_status = "ERROR"
        delivery.response_body = str(e)[:1000]
        logger.error(f"Webhook delivery error: {webhook.url} - {e}")

    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


async def trigger_event(
    db: Session,
    event_type: str,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None
) -> List[WebhookDelivery]:
    """Trigger an event and deliver to all subscribed webhooks"""
    webhooks = get_active_webhooks_for_event(db, event_type, tenant_id)
    deliveries = []

    for webhook in webhooks:
        try:
            delivery = await deliver_webhook(db, webhook, event_type, data)
            deliveries.append(delivery)
        except Exception as e:
            logger.error(f"Failed to deliver webhook {webhook.id}: {e}")

    return deliveries


def get_webhook_deliveries(
    db: Session,
    webhook_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[WebhookDelivery]:
    """Get delivery history for a webhook"""
    return (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


async def test_webhook(db: Session, webhook: Webhook) -> Dict[str, Any]:
    """Send a test event to a webhook"""
    test_payload = {
        "message": "This is a test webhook delivery",
        "webhook_id": str(webhook.id),
        "webhook_name": webhook.name,
    }

    delivery = await deliver_webhook(db, webhook, "test.ping", test_payload)

    return {
        "success": delivery.success,
        "status_code": int(delivery.response_status) if delivery.response_status and delivery.response_status.isdigit() else None,
        "response": delivery.response_body,
        "error": None if delivery.success else delivery.response_body,
    }
