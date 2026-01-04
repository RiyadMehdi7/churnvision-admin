from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID


class LicenseBase(BaseModel):
    expiration_days: int = 365
    max_employees: Optional[int] = None
    max_users: Optional[int] = None
    features: List[str] = []


class LicenseCreate(LicenseBase):
    tenant_id: UUID


class LicenseExtend(BaseModel):
    additional_days: int


class License(BaseModel):
    id: UUID
    tenant_id: UUID
    key_string: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool

    class Config:
        from_attributes = True


class LicenseDecoded(BaseModel):
    iss: str
    sub: str
    iat: int
    exp: int
    features: List[str]
    limits: Dict[str, Any]


class LicenseLimits(BaseModel):
    max_employees: Optional[int] = None
    max_users: Optional[int] = None


class LicenseValidationRequest(BaseModel):
    """Request schema for license validation from ChurnVision main app"""

    license_key: str
    installation_id: Optional[str] = None  # Unique identifier for the installation
    hardware_fingerprint: Optional[str] = None  # Hardware-based license binding


class LicenseValidationResponse(BaseModel):
    """
    Response schema for license validation.
    Field names match the ChurnVision integration specification.
    """

    valid: bool
    license_tier: str = Field(..., description="License tier: starter, pro, enterprise")
    company_name: str = Field(..., description="Tenant/company name")
    max_employees: Optional[int] = Field(None, description="Maximum employees allowed")
    expires_at: str = Field(..., description="License expiration datetime ISO format")
    features: List[str] = Field(
        default_factory=list, description="List of enabled features"
    )
    revoked: bool = Field(False, description="Whether the license has been revoked")

    # Additional fields for revoked licenses
    revocation_reason: Optional[str] = Field(
        None, description="Reason for revocation if revoked"
    )
    revoked_at: Optional[str] = Field(
        None, description="Revocation datetime if revoked"
    )

    # Internal fields (still useful for admin panel)
    license_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tenant_slug: Optional[str] = None
    issued_at: Optional[str] = None
    days_until_expiry: Optional[int] = None


class LicenseValidationErrorResponse(BaseModel):
    """Response when license validation fails"""

    valid: bool = False
    error: str
    revoked: Optional[bool] = None
    revocation_reason: Optional[str] = None
    revoked_at: Optional[str] = None


class LicenseValidationError(BaseModel):
    valid: bool = False
    error: str
    code: str


class LicenseAuditLogResponse(BaseModel):
    id: UUID
    license_id: UUID
    action: str
    performed_by: Optional[str] = None
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
