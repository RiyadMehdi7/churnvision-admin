from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user, verify_api_key
from app.models.user import User
from app.schemas import license as schemas
from app.services import license_service
from app.services.license_service import LicenseValidationError
from uuid import UUID

router = APIRouter()

# ===== Validation Endpoints (for main app integration - API Key auth) =====


@router.post(
    "/validate",
    response_model=Union[
        schemas.LicenseValidationResponse, schemas.LicenseValidationErrorResponse
    ],
)
def validate_license(
    request: schemas.LicenseValidationRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Validate a license key. This endpoint is used by the main ChurnVision app
    to verify that a tenant's license is valid before granting access to features.

    Request body:
    - license_key: The JWT license key to validate
    - installation_id: (optional) Unique identifier for the installation
    - hardware_fingerprint: (optional) Hardware-based license binding

    Response (200):
    - valid: true/false
    - license_tier: starter/pro/enterprise
    - company_name: Tenant name
    - max_employees: Employee limit
    - expires_at: ISO datetime
    - features: List of enabled features
    - revoked: Whether license is revoked
    - revocation_reason: Reason if revoked
    - revoked_at: Datetime if revoked

    Requires API key authentication via X-API-Key header.
    """
    try:
        result = license_service.validate_license_key(
            db=db,
            license_key=request.license_key,
            installation_id=request.installation_id,
            hardware_fingerprint=request.hardware_fingerprint,
        )
        # Check if this is a revoked license response
        if not result.get("valid", True):
            return schemas.LicenseValidationErrorResponse(
                valid=False,
                error=result.get("revocation_reason", "License is invalid"),
                revoked=result.get("revoked"),
                revocation_reason=result.get("revocation_reason"),
                revoked_at=result.get("revoked_at"),
            )
        return schemas.LicenseValidationResponse(**result)
    except LicenseValidationError as e:
        # Return 200 with error details per spec (not 400)
        return schemas.LicenseValidationErrorResponse(valid=False, error=e.message)


@router.get(
    "/validate/tenant/{tenant_slug}", response_model=schemas.LicenseValidationResponse
)
def validate_license_by_tenant(
    tenant_slug: str, db: Session = Depends(get_db), _: bool = Depends(verify_api_key)
):
    """
    Validate the active license for a tenant by slug.
    Returns the most recent valid license for the tenant.
    Used by the main app to check tenant license status.
    Requires API key authentication.
    """
    try:
        result = license_service.validate_license_by_tenant_slug(
            db=db, tenant_slug=tenant_slug
        )
        return schemas.LicenseValidationResponse(**result)
    except LicenseValidationError as e:
        raise HTTPException(
            status_code=400, detail={"valid": False, "error": e.message, "code": e.code}
        )


# ===== CRUD Endpoints (User auth) =====


@router.get("/", response_model=List[schemas.License])
def list_licenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all licenses with pagination"""
    return license_service.get_licenses(db=db, skip=skip, limit=limit)


@router.get("/tenant/{tenant_id}", response_model=List[schemas.License])
def get_licenses_by_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all licenses for a specific tenant"""
    return license_service.get_licenses_by_tenant(db=db, tenant_id=str(tenant_id))


@router.get("/{license_id}", response_model=schemas.License)
def get_license(
    license_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific license by ID"""
    license = license_service.get_license_by_id(db=db, license_id=str(license_id))
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    return license


@router.get(
    "/{license_id}/audit-logs", response_model=List[schemas.LicenseAuditLogResponse]
)
def get_license_audit_logs(
    license_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs for a specific license"""
    license = license_service.get_license_by_id(db=db, license_id=str(license_id))
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    return license_service.get_license_audit_logs(
        db=db, license_id=str(license_id), skip=skip, limit=limit
    )


@router.post("/", response_model=schemas.License)
def generate_license(
    license_in: schemas.LicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new license for a tenant"""
    try:
        return license_service.generate_license(db=db, license_in=license_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{license_id}/extend", response_model=schemas.License)
def extend_license(
    license_id: UUID,
    extend_data: schemas.LicenseExtend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extend an existing license by additional days"""
    try:
        return license_service.extend_license(
            db=db,
            license_id=str(license_id),
            additional_days=extend_data.additional_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{license_id}", response_model=schemas.License)
def revoke_license(
    license_id: UUID,
    reason: str = "Revoked via API",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a license"""
    try:
        return license_service.revoke_license(
            db=db, license_id=str(license_id), reason=reason
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
