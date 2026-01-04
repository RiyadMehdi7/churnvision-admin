from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.billing import Subscription, Invoice, InvoiceLineItem, InvoiceStatus, SubscriptionStatus

from app.schemas.billing import SubscriptionCreate, SubscriptionUpdate, InvoiceCreate, InvoiceUpdate


def get_subscriptions(db: Session, skip: int = 0, limit: int = 100) -> List[Subscription]:
    return db.query(Subscription).offset(skip).limit(limit).all()


def get_subscription_by_id(db: Session, subscription_id: str) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()


def get_tenant_subscriptions(db: Session, tenant_id: str) -> List[Subscription]:
    return db.query(Subscription).filter(Subscription.tenant_id == tenant_id).all()


def create_subscription(db: Session, sub_in: SubscriptionCreate) -> Subscription:
    start_date = sub_in.start_date or date.today()
    next_invoice = start_date + timedelta(days=30)

    db_sub = Subscription(
        tenant_id=sub_in.tenant_id,
        plan=sub_in.plan,
        base_price=sub_in.base_price,
        currency=sub_in.currency,
        billing_cycle_start=start_date,
        next_invoice_date=next_invoice,
        payment_method=sub_in.payment_method
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub


def update_subscription(db: Session, subscription: Subscription, sub_in: SubscriptionUpdate) -> Subscription:
    update_data = sub_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    db.commit()
    db.refresh(subscription)
    return subscription


def cancel_subscription(db: Session, subscription: Subscription) -> Subscription:
    subscription.status = SubscriptionStatus.CANCELLED
    db.commit()
    db.refresh(subscription)
    return subscription


def get_all_invoices(db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Invoice]:
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()


def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def create_invoice(db: Session, inv_in: InvoiceCreate) -> Invoice:
    db_inv = Invoice(
        tenant_id=inv_in.tenant_id,
        subscription_id=inv_in.subscription_id,
        invoice_number=inv_in.invoice_number,
        subtotal=inv_in.subtotal,
        tax=inv_in.tax,
        total=inv_in.total,
        currency=inv_in.currency,
        due_date=inv_in.due_date,
        status=inv_in.status
    )
    db.add(db_inv)
    db.flush()

    for item in inv_in.line_items:
        db_item = InvoiceLineItem(
            invoice_id=db_inv.id,
            description=item.description,
            amount=item.amount,
            quantity=item.quantity
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_inv)
    return db_inv


def update_invoice(db: Session, invoice: Invoice, inv_in: InvoiceUpdate) -> Invoice:
    update_data = inv_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    db.commit()
    db.refresh(invoice)
    return invoice


def mark_invoice_paid(db: Session, invoice: Invoice) -> Invoice:
    from datetime import datetime
    invoice.status = InvoiceStatus.PAID
    invoice.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(invoice)
    return invoice


def void_invoice(db: Session, invoice: Invoice) -> Invoice:
    invoice.status = InvoiceStatus.VOID
    db.commit()
    db.refresh(invoice)
    return invoice


def get_tenant_invoices(db: Session, tenant_id: str) -> List[Invoice]:
    return db.query(Invoice).filter(Invoice.tenant_id == tenant_id).order_by(Invoice.created_at.desc()).all()


def get_overdue_invoices(db: Session) -> List[Invoice]:
    """Get all overdue invoices"""
    today = date.today()
    return db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.SENT,
        Invoice.due_date < today
    ).all()
