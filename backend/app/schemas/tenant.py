from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from uuid import UUID
from app.models.tenant import TenantStatus, PricingTier


# Contact Schemas
class TenantContactBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = None
    phone: Optional[str] = None


class TenantContactCreate(TenantContactBase):
    pass


class TenantContact(TenantContactBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True


# Tenant Schemas
class TenantBase(BaseModel):
    name: str
    slug: str
    email_contact: Optional[EmailStr] = None  # Helper, not in DB direct but useful
    industry: Optional[str] = None
    region: Optional[str] = None
    tier: PricingTier = PricingTier.STARTER


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""

    max_employees: Optional[int] = None  # None = unlimited
    max_users: Optional[int] = 5
    expiration_days: int = 365  # License expiration (default 1 year)


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TenantStatus] = None
    tier: Optional[PricingTier] = None
    max_employees: Optional[int] = None
    max_users: Optional[int] = None
    features_enabled: Optional[List[str]] = None


class Tenant(TenantBase):
    id: UUID
    status: TenantStatus
    created_at: datetime
    contacts: List[TenantContact] = []

    max_employees: Optional[int]
    max_users: int
    features_enabled: List[str]

    class Config:
        from_attributes = True


# Config Schemas
class TenantConfigBase(BaseModel):
    key: str
    value: str


class TenantConfigCreate(TenantConfigBase):
    pass


class TenantConfig(TenantConfigBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True


# Deployment Schemas
class TenantDeploymentBase(BaseModel):
    current_version: str
    environment: str = "production"


class TenantDeploymentCreate(TenantDeploymentBase):
    deployed_by: Optional[str] = None


class TenantDeploymentUpdate(BaseModel):
    status: str


class TenantDeployment(TenantDeploymentBase):
    id: UUID
    tenant_id: UUID
    deployed_at: datetime
    deployed_by: Optional[str]
    last_health_check: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ===== Structured Config Response for ChurnVision Integration =====


class TenantConfigFeatureFlags(BaseModel):
    """Feature flags configuration"""

    enable_ai_assistant: bool = False
    enable_playground: bool = False
    enable_knowledge_base: bool = False
    enable_gdpr: bool = False
    max_concurrent_users: int = 10


class TenantConfigBranding(BaseModel):
    """Branding configuration"""

    company_logo_url: Optional[str] = None
    primary_color: str = "#1a73e8"


class TenantConfigLimits(BaseModel):
    """Usage limits configuration"""

    max_employees: Optional[int] = None
    max_predictions_per_day: int = 1000
    max_users: int = 5


class TenantConfigDict(BaseModel):
    """
    Structured tenant configuration response.
    Matches the ChurnVision integration specification.
    """

    feature_flags: Dict[str, Any] = Field(default_factory=dict)
    branding: Dict[str, Any] = Field(default_factory=dict)
    limits: Dict[str, Any] = Field(default_factory=dict)


# ===== Expanded Deployment Health Request =====


class TenantDeploymentHealthUpdate(BaseModel):
    """
    Health update request from ChurnVision main app.

    Privacy-focused: Only requires essential operational data.
    - status: Is the system working?
    - version: What version is running?
    - uptime_seconds: Is the system stable?

    All other fields are optional for backwards compatibility.
    """

    # Required fields (essential for operational monitoring)
    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    version: str = Field("unknown", description="Deployed version")
    uptime_seconds: int = Field(0, description="Application uptime in seconds")

    # Optional fields (for backwards compatibility, no longer required)
    database: Optional[bool] = Field(None, description="Database connectivity status")
    cache: Optional[bool] = Field(None, description="Cache (Redis) connectivity status")
    platform: Optional[str] = Field(
        None, description="Platform info (e.g., Linux-5.15.0-x86_64)"
    )
    python_version: Optional[str] = Field(None, description="Python version")
    installation_id: Optional[str] = Field(
        None, description="Unique installation identifier"
    )
    reported_at: Optional[datetime] = Field(None, description="Client-side timestamp")


class TenantDeploymentHealthResponse(BaseModel):
    """Response for health update acknowledgement"""

    acknowledged: bool = True
