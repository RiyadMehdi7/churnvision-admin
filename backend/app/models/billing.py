import uuid
import enum
from sqlalchemy import Column, String, Integer, DateTime, Date, Numeric, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base

class PricingPlan(str, enum.Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"
    MULTI_YEAR = "MULTI_YEAR"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    VOID = "VOID"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    plan = Column(Enum(PricingPlan), default=PricingPlan.MONTHLY)
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    
    # Dates
    billing_cycle_start = Column(Date, nullable=False)
    next_invoice_date = Column(Date, nullable=False)
    
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    payment_method = Column(String, default="invoice")

    tenant = relationship("Tenant")
    invoices = relationship("Invoice", back_populates="subscription")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    invoice_number = Column(String, unique=True, nullable=False)
    
    subtotal = Column(Numeric(10, 2))
    tax = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))
    currency = Column(String, default="USD")
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    pdf_url = Column(String, nullable=True)

    subscription = relationship("Subscription", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1)

    invoice = relationship("Invoice", back_populates="line_items")
