from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import webhook as schemas
from app.services import webhook_service

router = APIRouter()


@router.get("/", response_model=List[schemas.Webhook])
def list_webhooks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all webhooks"""
    return webhook_service.get_webhooks(db=db, skip=skip, limit=limit)


@router.get("/{webhook_id}", response_model=schemas.Webhook)
def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific webhook by ID"""
    webhook = webhook_service.get_webhook_by_id(db=db, webhook_id=str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.post("/", response_model=schemas.Webhook)
def create_webhook(
    webhook_in: schemas.WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook"""
    return webhook_service.create_webhook(db=db, webhook_in=webhook_in)


@router.put("/{webhook_id}", response_model=schemas.Webhook)
def update_webhook(
    webhook_id: UUID,
    webhook_in: schemas.WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing webhook"""
    webhook = webhook_service.get_webhook_by_id(db=db, webhook_id=str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook_service.update_webhook(db=db, webhook=webhook, webhook_in=webhook_in)


@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook"""
    webhook = webhook_service.get_webhook_by_id(db=db, webhook_id=str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    webhook_service.delete_webhook(db=db, webhook=webhook)
    return {"message": "Webhook deleted successfully"}


@router.post("/{webhook_id}/test", response_model=schemas.WebhookTestResponse)
async def test_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test event to a webhook"""
    webhook = webhook_service.get_webhook_by_id(db=db, webhook_id=str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await webhook_service.test_webhook(db=db, webhook=webhook)
    return schemas.WebhookTestResponse(**result)


@router.get("/{webhook_id}/deliveries", response_model=List[schemas.WebhookDeliveryResponse])
def get_webhook_deliveries(
    webhook_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get delivery history for a webhook"""
    webhook = webhook_service.get_webhook_by_id(db=db, webhook_id=str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook_service.get_webhook_deliveries(
        db=db, webhook_id=str(webhook_id), skip=skip, limit=limit
    )


@router.post("/trigger", response_model=List[schemas.WebhookDeliveryResponse])
async def trigger_webhook_event(
    event: schemas.WebhookEventTrigger,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a webhook event.
    This endpoint is for testing or manual event dispatch.
    """
    deliveries = await webhook_service.trigger_event(
        db=db,
        event_type=event.event_type,
        data=event.data,
        tenant_id=event.tenant_id
    )
    return deliveries
