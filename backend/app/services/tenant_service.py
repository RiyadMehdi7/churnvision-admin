from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.tenant import (
    Tenant,
    TenantContact,
    TenantConfig,
    TenantDeployment,
    TenantStatus,
)
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.license import LicenseCreate
from app.services import license_service


def create_tenant(
    db: Session, tenant_in: TenantCreate, auto_generate_license: bool = True
) -> Tenant:
    """
    Create a new tenant and optionally auto-generate a license.
    """
    # Default features based on tier
    tier_features = {
        "STARTER": ["home", "data-management", "settings"],
        "PROFESSIONAL": [
            "home",
            "data-management",
            "settings",
            "ai-assistant",
            "knowledge-base",
        ],
        "ENTERPRISE": [
            "home",
            "data-management",
            "settings",
            "ai-assistant",
            "knowledge-base",
            "playground",
            "gdpr",
        ],
    }

    features = tier_features.get(tenant_in.tier.value, [])

    db_tenant = Tenant(
        name=tenant_in.name,
        slug=tenant_in.slug,
        tier=tenant_in.tier,
        industry=tenant_in.industry,
        region=tenant_in.region,
        status=TenantStatus.TRIAL,
        features_enabled=features,
        max_employees=tenant_in.max_employees,
        max_users=tenant_in.max_users or 5,
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    # Auto-generate license for the new tenant
    if auto_generate_license:
        license_data = LicenseCreate(
            tenant_id=db_tenant.id,
            expiration_days=365,  # 1 year default
            max_employees=tenant_in.max_employees,
            max_users=tenant_in.max_users or 5,
            features=features,
        )
        license_service.generate_license(
            db=db, license_in=license_data, performed_by="system"
        )

    return db_tenant


def get_tenants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tenant).offset(skip).limit(limit).all()


def get_tenant_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.slug == slug).first()


def get_tenant_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def update_tenant(db: Session, tenant: Tenant, tenant_in: TenantUpdate) -> Tenant:
    update_data = tenant_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return tenant


def delete_tenant(db: Session, tenant: Tenant) -> None:
    db.delete(tenant)
    db.commit()


# ===== Tenant Config Management =====


def get_tenant_configs(db: Session, tenant_id: str) -> List[TenantConfig]:
    """Get all config entries for a tenant"""
    return db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).all()


def get_tenant_config(db: Session, tenant_id: str, key: str) -> Optional[TenantConfig]:
    """Get a specific config value for a tenant"""
    return (
        db.query(TenantConfig)
        .filter(TenantConfig.tenant_id == tenant_id, TenantConfig.key == key)
        .first()
    )


def set_tenant_config(
    db: Session, tenant_id: str, key: str, value: str
) -> TenantConfig:
    """Set or update a config value for a tenant"""
    config = get_tenant_config(db, tenant_id, key)
    if config:
        config.value = value
    else:
        config = TenantConfig(tenant_id=tenant_id, key=key, value=value)
        db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_tenant_config(db: Session, tenant_id: str, key: str) -> bool:
    """Delete a config entry for a tenant"""
    config = get_tenant_config(db, tenant_id, key)
    if config:
        db.delete(config)
        db.commit()
        return True
    return False


def get_tenant_configs_as_dict(db: Session, tenant_id: str) -> Dict[str, str]:
    """Get all tenant configs as a flat dictionary"""
    configs = get_tenant_configs(db, tenant_id)
    return {c.key: c.value for c in configs}


def get_tenant_configs_structured(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Get tenant configs as a structured dictionary.
    Organizes configs into feature_flags, branding, and limits sections.
    Matches the ChurnVision integration specification.
    """
    configs = get_tenant_configs(db, tenant_id)
    config_dict = {c.key: c.value for c in configs}

    # Get tenant for limits
    tenant = get_tenant_by_id(db, tenant_id)

    # Parse boolean/int values from string configs
    def parse_bool(val: str) -> bool:
        return val.lower() in ("true", "1", "yes", "on")

    def parse_int(val: str, default: int = 0) -> int:
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    # Build structured response
    result = {
        "feature_flags": {
            "enable_ai_assistant": parse_bool(
                config_dict.get("enable_ai_assistant", "false")
            ),
            "enable_playground": parse_bool(
                config_dict.get("enable_playground", "false")
            ),
            "enable_knowledge_base": parse_bool(
                config_dict.get("enable_knowledge_base", "false")
            ),
            "enable_gdpr": parse_bool(config_dict.get("enable_gdpr", "false")),
            "max_concurrent_users": parse_int(
                config_dict.get("max_concurrent_users", "10"), 10
            ),
        },
        "branding": {
            "company_logo_url": config_dict.get("company_logo_url"),
            "primary_color": config_dict.get("primary_color", "#1a73e8"),
        },
        "limits": {
            "max_employees": tenant.max_employees if tenant else None,
            "max_predictions_per_day": parse_int(
                config_dict.get("max_predictions_per_day", "10000"), 10000
            ),
            "max_users": tenant.max_users if tenant else 5,
        },
    }

    # Add any additional custom configs under a separate key
    known_keys = {
        "enable_ai_assistant",
        "enable_playground",
        "enable_knowledge_base",
        "enable_gdpr",
        "max_concurrent_users",
        "company_logo_url",
        "primary_color",
        "max_predictions_per_day",
    }
    custom_configs = {k: v for k, v in config_dict.items() if k not in known_keys}
    if custom_configs:
        result["custom"] = custom_configs

    return result


# ===== Tenant Deployment Management =====


def get_tenant_deployment(db: Session, tenant_id: str) -> Optional[TenantDeployment]:
    """Get current deployment info for a tenant"""
    return (
        db.query(TenantDeployment)
        .filter(TenantDeployment.tenant_id == tenant_id)
        .first()
    )


def update_tenant_deployment(
    db: Session,
    tenant_id: str,
    version: str,
    deployed_by: str = None,
    environment: str = "production",
) -> TenantDeployment:
    """Update or create deployment info for a tenant"""
    deployment = get_tenant_deployment(db, tenant_id)
    if deployment:
        deployment.current_version = version
        deployment.deployed_at = datetime.utcnow()
        deployment.deployed_by = deployed_by
        deployment.environment = environment
        deployment.status = "DEPLOYED"
    else:
        deployment = TenantDeployment(
            tenant_id=tenant_id,
            current_version=version,
            deployed_by=deployed_by,
            environment=environment,
            status="DEPLOYED",
        )
        db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


def update_deployment_health(
    db: Session, tenant_id: str, status: str = "HEALTHY"
) -> Optional[TenantDeployment]:
    """Update health status for a tenant deployment (basic version)"""
    deployment = get_tenant_deployment(db, tenant_id)
    if deployment:
        deployment.last_health_check = datetime.utcnow()
        deployment.status = status
        db.commit()
        db.refresh(deployment)
    return deployment


def update_deployment_health_extended(
    db: Session,
    tenant_id: str,
    status: str = "HEALTHY",
    database_healthy: Optional[bool] = None,
    cache_healthy: Optional[bool] = None,
    uptime_seconds: int = 0,
    version: str = None,
    platform: str = None,
    python_version: str = None,
    installation_id: str = None,
    reported_at: datetime = None,
) -> Optional[TenantDeployment]:
    """
    Update health status for a tenant deployment with extended fields.

    Privacy-focused: Only status, version, and uptime_seconds are required.
    Other fields (database_healthy, cache_healthy, platform, python_version)
    are optional for backwards compatibility.
    """
    deployment = get_tenant_deployment(db, tenant_id)
    now = datetime.utcnow()

    if deployment:
        deployment.last_health_check = now
        deployment.status = status.upper()

        # Update version if provided
        if version:
            deployment.current_version = version

        # Update uptime (always provided)
        deployment.uptime_seconds = uptime_seconds

        # Update optional extended health fields only if provided
        if database_healthy is not None:
            deployment.database_healthy = database_healthy
        if cache_healthy is not None:
            deployment.cache_healthy = cache_healthy
        if platform:
            deployment.platform = platform
        if python_version:
            deployment.python_version = python_version
        if installation_id:
            deployment.installation_id = installation_id
        deployment.last_reported_at = reported_at or now

        db.commit()
        db.refresh(deployment)
    else:
        # Auto-create deployment if it doesn't exist
        deployment = TenantDeployment(
            tenant_id=tenant_id,
            current_version=version or "unknown",
            status=status.upper(),
            last_health_check=now,
            database_healthy=database_healthy,  # May be None
            cache_healthy=cache_healthy,  # May be None
            uptime_seconds=uptime_seconds,
            platform=platform,
            python_version=python_version,
            installation_id=installation_id,
            last_reported_at=reported_at or now,
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)

    return deployment


def get_all_deployments(
    db: Session, skip: int = 0, limit: int = 100
) -> List[TenantDeployment]:
    """Get all tenant deployments"""
    return db.query(TenantDeployment).offset(skip).limit(limit).all()


def get_deployments_by_version(db: Session, version: str) -> List[TenantDeployment]:
    """Get all deployments running a specific version"""
    return (
        db.query(TenantDeployment)
        .filter(TenantDeployment.current_version == version)
        .all()
    )


def get_unhealthy_deployments(db: Session) -> List[TenantDeployment]:
    """Get all deployments with non-healthy status"""
    return (
        db.query(TenantDeployment)
        .filter(TenantDeployment.status.notin_(["HEALTHY", "DEPLOYED"]))
        .all()
    )
