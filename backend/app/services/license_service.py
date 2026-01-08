from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.license import License, LicenseAuditLog
from app.models.tenant import Tenant
from app.schemas.license import LicenseCreate
from app.core.config import settings
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)


class LicenseValidationError(Exception):
    """Custom exception for license validation errors"""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)


def get_licenses(db: Session, skip: int = 0, limit: int = 100) -> List[License]:
    return db.query(License).offset(skip).limit(limit).all()


def get_license_by_id(db: Session, license_id: str) -> Optional[License]:
    return db.query(License).filter(License.id == license_id).first()


def get_licenses_by_tenant(db: Session, tenant_id: str) -> List[License]:
    return db.query(License).filter(License.tenant_id == tenant_id).all()


def generate_license(
    db: Session, license_in: LicenseCreate, performed_by: str = "system"
) -> License:
    tenant = db.query(Tenant).filter(Tenant.id == license_in.tenant_id).first()
    if not tenant:
        raise ValueError("Tenant not found")

    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(days=license_in.expiration_days)

    payload = {
        "iss": "churnvision.tech",
        "sub": f"tenant_{tenant.slug}",
        "iat": issued_at,
        "exp": expires_at,
        "features": license_in.features,
        "limits": {
            "max_employees": license_in.max_employees,
            "max_users": license_in.max_users,
        },
    }

    # Using HS256 for MVP, normally RS256 with private key
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    db_license = License(
        tenant_id=tenant.id,
        key_string=encoded_jwt,
        issued_at=issued_at,
        expires_at=expires_at,
        max_employees=license_in.max_employees,
        max_users=license_in.max_users,
        features=license_in.features,
    )
    db.add(db_license)

    # Audit Log
    audit = LicenseAuditLog(
        license=db_license,
        action="ISSUED",
        performed_by=performed_by,
        details={"expiry_days": license_in.expiration_days},
    )
    db.add(audit)

    db.commit()
    db.refresh(db_license)
    return db_license


def revoke_license(
    db: Session,
    license_id: str,
    reason: str = "Manual revocation",
    performed_by: str = "system",
):
    db_license = db.query(License).filter(License.id == license_id).first()
    if not db_license:
        raise ValueError("License not found")

    db_license.revoked = True
    db_license.revoked_at = datetime.utcnow()
    db_license.revocation_reason = reason

    audit = LicenseAuditLog(
        license=db_license,
        action="REVOKED",
        performed_by=performed_by,
        details={"reason": reason},
    )
    db.add(audit)

    db.commit()
    db.refresh(db_license)
    return db_license


def _map_tier_to_spec(tier_value: str) -> str:
    """Map internal tier names to spec-compliant tier names"""
    tier_mapping = {
        "STARTER": "starter",
        "PROFESSIONAL": "pro",
        "ENTERPRISE": "enterprise",
    }
    return tier_mapping.get(tier_value, tier_value.lower())


def validate_license_key(
    db: Session,
    license_key: str,
    installation_id: Optional[str] = None,
    hardware_fingerprint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate a license key and return license details.
    This is the main endpoint for the main app to validate licenses.

    Response format matches the ChurnVision integration specification.
    """
    try:
        # Decode and verify the JWT (validates signature and expiration)
        jwt.decode(license_key, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        logger.warning(f"License validation failed - invalid JWT: {e}")
        raise LicenseValidationError("Invalid license key format", "INVALID_FORMAT")

    # Find the license in database
    db_license = db.query(License).filter(License.key_string == license_key).first()
    if not db_license:
        logger.warning("License validation failed - license not found in database")
        raise LicenseValidationError("License not found", "NOT_FOUND")

    # Get tenant info
    tenant = db.query(Tenant).filter(Tenant.id == db_license.tenant_id).first()

    # Check if revoked - return revoked info instead of raising error
    if db_license.revoked:
        logger.warning(
            f"License validation failed - license {db_license.id} is revoked"
        )
        return {
            "valid": False,
            "revoked": True,
            "revocation_reason": db_license.revocation_reason
            or "License has been revoked",
            "revoked_at": db_license.revoked_at.isoformat()
            if db_license.revoked_at
            else None,
            "license_tier": _map_tier_to_spec(tenant.tier.value)
            if tenant
            else "starter",
            "company_name": tenant.name if tenant else "Unknown",
            "max_employees": db_license.max_employees,
            "expires_at": db_license.expires_at.isoformat(),
            "features": db_license.features or [],
        }

    # Check if expired
    if db_license.expires_at < datetime.utcnow():
        logger.warning(
            f"License validation failed - license {db_license.id} is expired"
        )
        raise LicenseValidationError("License has expired", "EXPIRED")

    # Log successful validation with installation info
    audit = LicenseAuditLog(
        license=db_license,
        action="VALIDATED",
        performed_by="api",
        details={
            "timestamp": datetime.utcnow().isoformat(),
            "installation_id": installation_id,
            "hardware_fingerprint": hardware_fingerprint,
        },
    )
    db.add(audit)
    db.commit()

    # Return response matching ChurnVision integration specification
    return {
        "valid": True,
        "license_tier": _map_tier_to_spec(tenant.tier.value) if tenant else "starter",
        "company_name": tenant.name if tenant else "Unknown",
        "max_employees": db_license.max_employees,
        "expires_at": db_license.expires_at.isoformat(),
        "features": db_license.features or [],
        "revoked": False,
        "revocation_reason": None,
        "revoked_at": None,
        # Additional internal fields
        "license_id": str(db_license.id),
        "tenant_id": str(db_license.tenant_id),
        "tenant_slug": tenant.slug if tenant else None,
        "issued_at": db_license.issued_at.isoformat(),
        "days_until_expiry": (db_license.expires_at - datetime.utcnow()).days,
    }


def validate_license_by_tenant_slug(db: Session, tenant_slug: str) -> Dict[str, Any]:
    """
    Validate the active license for a tenant by slug.
    Returns the most recent valid license for the tenant.
    Response format matches the ChurnVision integration specification.
    """
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if not tenant:
        raise LicenseValidationError("Tenant not found", "TENANT_NOT_FOUND")

    # Get the most recent active license
    db_license = (
        db.query(License)
        .filter(
            License.tenant_id == tenant.id,
            License.revoked == False,
            License.expires_at > datetime.utcnow(),
        )
        .order_by(License.expires_at.desc())
        .first()
    )

    if not db_license:
        raise LicenseValidationError("No valid license found for tenant", "NO_LICENSE")

    # Return response matching ChurnVision integration specification
    return {
        "valid": True,
        "license_tier": _map_tier_to_spec(tenant.tier.value),
        "company_name": tenant.name,
        "max_employees": db_license.max_employees,
        "expires_at": db_license.expires_at.isoformat(),
        "features": db_license.features or [],
        "revoked": False,
        "revocation_reason": None,
        "revoked_at": None,
        # Additional internal fields
        "license_id": str(db_license.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "issued_at": db_license.issued_at.isoformat(),
        "days_until_expiry": (db_license.expires_at - datetime.utcnow()).days,
    }


def get_license_audit_logs(
    db: Session, license_id: str, skip: int = 0, limit: int = 100
) -> List[LicenseAuditLog]:
    """Get audit logs for a specific license"""
    return (
        db.query(LicenseAuditLog)
        .filter(LicenseAuditLog.license_id == license_id)
        .order_by(LicenseAuditLog.performed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def extend_license(
    db: Session, license_id: str, additional_days: int, performed_by: str = "system"
) -> License:
    """Extend an existing license expiration date"""
    db_license = db.query(License).filter(License.id == license_id).first()
    if not db_license:
        raise ValueError("License not found")

    if db_license.revoked:
        raise ValueError("Cannot extend a revoked license")

    old_expiry = db_license.expires_at
    db_license.expires_at = db_license.expires_at + timedelta(days=additional_days)

    audit = LicenseAuditLog(
        license=db_license,
        action="EXTENDED",
        performed_by=performed_by,
        details={
            "old_expiry": old_expiry.isoformat(),
            "new_expiry": db_license.expires_at.isoformat(),
            "additional_days": additional_days,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(db_license)
    return db_license
