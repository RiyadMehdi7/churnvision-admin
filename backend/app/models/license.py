import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base


class License(Base):
    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    key_string = Column(String, nullable=False)  # The JWT blob

    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String, nullable=True)

    # Key parameters stored for audit
    max_employees = Column(Integer)
    max_users = Column(Integer)
    features = Column(JSON)  # Snapshot of features enabled at issuance

    tenant = relationship("Tenant", back_populates="licenses")
    audit_logs = relationship(
        "LicenseAuditLog", back_populates="license", cascade="all, delete-orphan"
    )


class LicenseAuditLog(Base):
    __tablename__ = "license_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    action = Column(String, nullable=False)  # "ISSUED", "VALIDATED", "REVOKED"
    performed_at = Column(
        DateTime, default=datetime.utcnow
    )  # Changed from timestamp to match migration
    performed_by = Column(String, nullable=True)  # Admin user
    details = Column(JSON, nullable=True)

    license = relationship("License", back_populates="audit_logs")
