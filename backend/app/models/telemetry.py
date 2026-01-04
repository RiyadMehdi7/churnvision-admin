import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.db import Base


class TelemetryPing(Base):
    __tablename__ = "health_pings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Health
    api_status = Column(String)
    db_status = Column(String)
    ollama_status = Column(String)

    # Usage
    active_users_count = Column(Integer)
    predictions_this_period = Column(Integer)
    api_calls_this_period = Column(Integer)

    # Version
    deployed_version = Column(String)
    python_version = Column(String)

    # Errors
    recent_errors = Column(JSON)  # List of strings

    # Extended fields (ChurnVision integration spec)
    installation_id = Column(String, nullable=True)
    error_count_24h = Column(Integer, default=0, nullable=True)
    collection_timestamp = Column(DateTime, nullable=True)


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Integer, nullable=False)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
