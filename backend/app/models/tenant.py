import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Date,
    Enum,
    JSON,
    Boolean,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base
import enum


class TenantStatus(str, enum.Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CHURNED = "CHURNED"


class PricingTier(str, enum.Enum):
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    tier = Column(Enum(PricingTier), default=PricingTier.STARTER, nullable=False)

    # Limits
    max_employees = Column(Integer, nullable=True)  # None = unlimited
    max_users = Column(Integer, default=5)
    features_enabled = Column(JSON, default=[])  # List of strings

    # Dates
    trial_started_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(DateTime, nullable=True)
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    industry = Column(String, nullable=True)
    employee_count_range = Column(String, nullable=True)
    region = Column(String, nullable=True)

    # Relationships
    contacts = relationship(
        "TenantContact", back_populates="tenant", cascade="all, delete-orphan"
    )
    configs = relationship(
        "TenantConfig", back_populates="tenant", cascade="all, delete-orphan"
    )
    deployments = relationship(
        "TenantDeployment", back_populates="tenant", cascade="all, delete-orphan"
    )
    licenses = relationship(
        "License", back_populates="tenant", cascade="all, delete-orphan"
    )
    contracts = relationship(
        "Contract", back_populates="tenant", cascade="all, delete-orphan"
    )


class TenantContact(Base):
    __tablename__ = "tenant_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=True)  # e.g. "Primary", "Billing"
    phone = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="contacts")


class TenantConfig(Base):
    __tablename__ = "tenant_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    tenant = relationship("Tenant", back_populates="configs")


# Deployment model for release tracking
class TenantDeployment(Base):
    __tablename__ = "tenant_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    current_version = Column(String, nullable=False)
    deployed_at = Column(DateTime, default=datetime.utcnow)
    deployed_by = Column(String, nullable=True)
    environment = Column(String, default="production")
    last_health_check = Column(DateTime, nullable=True)
    status = Column(String, default="UNKNOWN")  # HEALTHY, DEGRADED, UNHEALTHY

    # Extended health fields (ChurnVision integration spec)
    database_healthy = Column(Boolean, default=True, nullable=True)
    cache_healthy = Column(Boolean, default=True, nullable=True)
    uptime_seconds = Column(Integer, default=0, nullable=True)
    platform = Column(String, nullable=True)
    python_version = Column(String, nullable=True)
    installation_id = Column(String, nullable=True)
    last_reported_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="deployments")
