import uuid
import enum
from sqlalchemy import Column, String, Integer, DateTime, Date, Numeric, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base

class ContractStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING_RENEWAL = "PENDING_RENEWAL"
    EXPIRED = "EXPIRED"

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    document_url = Column(String, nullable=True) # Signed PDF
    contract_type = Column(String, default="subscription")
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    auto_renew = Column(Boolean, default=True)
    notice_period_days = Column(Integer, default=30)
    
    total_contract_value = Column(Numeric(10, 2), default=0)
    payment_terms = Column(String, default="net30")
    
    status = Column(Enum(ContractStatus), default=ContractStatus.ACTIVE)
    renewal_reminder_sent = Column(Boolean, default=False)

    tenant = relationship("Tenant", back_populates="contracts")

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=True)
    name = Column(String, nullable=False)
    asset_type = Column(String) # License, Doc, Hardware
    url = Column(String)
    
    contract = relationship("Contract")

# Update Tenant to include contracts relation
# This requires updating tenant.py or just leaving it one-way if not needed. 
# Spec implied relations. I'll add it to Tenant in separate step if strictly required but back_populates="contracts" means I must.
