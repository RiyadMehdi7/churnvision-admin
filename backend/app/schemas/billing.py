from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from app.models.billing import PricingPlan, SubscriptionStatus, InvoiceStatus

class SubscriptionBase(BaseModel):
    plan: PricingPlan = PricingPlan.MONTHLY
    base_price: Decimal
    currency: str = "USD"
    payment_method: str = "invoice"

class SubscriptionCreate(SubscriptionBase):
    tenant_id: UUID
    start_date: Optional[date] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[PricingPlan] = None
    base_price: Optional[Decimal] = None
    status: Optional[SubscriptionStatus] = None
    payment_method: Optional[str] = None


class Subscription(SubscriptionBase):
    id: UUID
    tenant_id: UUID
    status: SubscriptionStatus
    billing_cycle_start: date
    next_invoice_date: date

    class Config:
        from_attributes = True

class InvoiceLineItemBase(BaseModel):
    description: str
    amount: Decimal
    quantity: int = 1

class InvoiceBase(BaseModel):
    invoice_number: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    currency: str
    due_date: date
    status: InvoiceStatus

class InvoiceCreate(InvoiceBase):
    tenant_id: UUID
    subscription_id: Optional[UUID] = None
    line_items: List[InvoiceLineItemBase] = []

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    pdf_url: Optional[str] = None


class Invoice(InvoiceBase):
    id: UUID
    tenant_id: UUID
    subscription_id: Optional[UUID]
    paid_at: Optional[datetime]
    pdf_url: Optional[str]

    class Config:
        from_attributes = True
