from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import billing as schemas
from app.services import billing_service

router = APIRouter()


# ===== Subscriptions =====

@router.get("/subscriptions", response_model=List[schemas.Subscription])
def list_subscriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all subscriptions with pagination"""
    return billing_service.get_subscriptions(db=db, skip=skip, limit=limit)


@router.get("/subscriptions/tenant/{tenant_id}", response_model=List[schemas.Subscription])
def get_tenant_subscriptions(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subscriptions for a specific tenant"""
    return billing_service.get_tenant_subscriptions(db=db, tenant_id=str(tenant_id))


@router.get("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
def get_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific subscription by ID"""
    subscription = billing_service.get_subscription_by_id(db=db, subscription_id=str(subscription_id))
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.post("/subscriptions", response_model=schemas.Subscription)
def create_subscription(
    sub_in: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription"""
    return billing_service.create_subscription(db=db, sub_in=sub_in)


@router.put("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
def update_subscription(
    subscription_id: UUID,
    sub_in: schemas.SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing subscription"""
    subscription = billing_service.get_subscription_by_id(db=db, subscription_id=str(subscription_id))
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return billing_service.update_subscription(db=db, subscription=subscription, sub_in=sub_in)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=schemas.Subscription)
def cancel_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a subscription"""
    subscription = billing_service.get_subscription_by_id(db=db, subscription_id=str(subscription_id))
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return billing_service.cancel_subscription(db=db, subscription=subscription)


# ===== Invoices =====

@router.get("/invoices", response_model=List[schemas.Invoice])
def list_invoices(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all invoices with optional status filter"""
    return billing_service.get_all_invoices(db=db, status=status, skip=skip, limit=limit)


@router.get("/invoices/tenant/{tenant_id}", response_model=List[schemas.Invoice])
def get_invoices_by_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invoices for a specific tenant"""
    return billing_service.get_tenant_invoices(db=db, tenant_id=str(tenant_id))


@router.get("/invoices/overdue", response_model=List[schemas.Invoice])
def get_overdue_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all overdue invoices"""
    return billing_service.get_overdue_invoices(db=db)


@router.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific invoice by ID"""
    invoice = billing_service.get_invoice_by_id(db=db, invoice_id=str(invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices", response_model=schemas.Invoice)
def create_invoice(
    inv_in: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice"""
    return billing_service.create_invoice(db=db, inv_in=inv_in)


@router.put("/invoices/{invoice_id}", response_model=schemas.Invoice)
def update_invoice(
    invoice_id: UUID,
    inv_in: schemas.InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing invoice"""
    invoice = billing_service.get_invoice_by_id(db=db, invoice_id=str(invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return billing_service.update_invoice(db=db, invoice=invoice, inv_in=inv_in)


@router.post("/invoices/{invoice_id}/pay", response_model=schemas.Invoice)
def mark_invoice_paid(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an invoice as paid"""
    invoice = billing_service.get_invoice_by_id(db=db, invoice_id=str(invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return billing_service.mark_invoice_paid(db=db, invoice=invoice)


@router.post("/invoices/{invoice_id}/void", response_model=schemas.Invoice)
def void_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Void an invoice"""
    invoice = billing_service.get_invoice_by_id(db=db, invoice_id=str(invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return billing_service.void_invoice(db=db, invoice=invoice)
