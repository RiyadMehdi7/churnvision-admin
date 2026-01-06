from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.deps import get_current_user, verify_api_key
from app.models.user import User
from app.schemas import tenant as schemas
from app.services import tenant_service
from app.services import installation_service

router = APIRouter()


# ===== Tenant CRUD =====


@router.post("/", response_model=schemas.Tenant)
def create_tenant(
    tenant_in: schemas.TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new tenant"""
    db_tenant = tenant_service.get_tenant_by_slug(db, slug=tenant_in.slug)
    if db_tenant:
        raise HTTPException(
            status_code=400, detail="Tenant with this slug already exists"
        )
    return tenant_service.create_tenant(db=db, tenant_in=tenant_in)


@router.get("/", response_model=List[schemas.Tenant])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tenants with pagination"""
    return tenant_service.get_tenants(db, skip=skip, limit=limit)


@router.get("/deployments/all", response_model=List[schemas.TenantDeployment])
def list_all_deployments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tenant deployments"""
    return tenant_service.get_all_deployments(db=db, skip=skip, limit=limit)


@router.get(
    "/deployments/version/{version}", response_model=List[schemas.TenantDeployment]
)
def get_deployments_by_version(
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all deployments running a specific version"""
    return tenant_service.get_deployments_by_version(db=db, version=version)


@router.get("/deployments/unhealthy", response_model=List[schemas.TenantDeployment])
def get_unhealthy_deployments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all deployments with non-healthy status"""
    return tenant_service.get_unhealthy_deployments(db=db)


@router.get("/{slug}", response_model=schemas.Tenant)
def get_tenant(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific tenant by slug"""
    db_tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant


@router.put("/{slug}", response_model=schemas.Tenant)
def update_tenant(
    slug: str,
    tenant_in: schemas.TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing tenant"""
    db_tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_service.update_tenant(db=db, tenant=db_tenant, tenant_in=tenant_in)


@router.delete("/{slug}")
def delete_tenant(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a tenant"""
    db_tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_service.delete_tenant(db=db, tenant=db_tenant)
    return {"message": "Tenant deleted successfully"}


# ===== Tenant Config Management =====


@router.get("/{slug}/configs", response_model=List[schemas.TenantConfig])
def get_tenant_configs(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all config entries for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_service.get_tenant_configs(db=db, tenant_id=str(tenant.id))


@router.get("/{slug}/configs/dict", response_model=schemas.TenantConfigDict)
def get_tenant_configs_as_dict(
    slug: str, db: Session = Depends(get_db), _: bool = Depends(verify_api_key)
):
    """
    Get tenant configs as a structured dictionary.

    Returns configuration organized into sections:
    - feature_flags: Feature toggles (enable_ai_assistant, enable_playground, etc.)
    - branding: UI customization (company_logo_url, primary_color)
    - limits: Usage limits (max_employees, max_predictions_per_day, max_users)

    Requires API key authentication via X-API-Key header.
    Used by the main ChurnVision app to fetch tenant configuration.
    """
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_service.get_tenant_configs_structured(db=db, tenant_id=str(tenant.id))


@router.get("/{slug}/configs/{key}")
def get_tenant_config(
    slug: str,
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific config value for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    config = tenant_service.get_tenant_config(db=db, tenant_id=str(tenant.id), key=key)
    if not config:
        raise HTTPException(status_code=404, detail="Config key not found")
    return {"key": config.key, "value": config.value}


@router.put("/{slug}/configs/{key}", response_model=schemas.TenantConfig)
def set_tenant_config(
    slug: str,
    key: str,
    config_in: schemas.TenantConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set or update a config value for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_service.set_tenant_config(
        db=db, tenant_id=str(tenant.id), key=key, value=config_in.value
    )


@router.delete("/{slug}/configs/{key}")
def delete_tenant_config(
    slug: str,
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a config entry for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    deleted = tenant_service.delete_tenant_config(
        db=db, tenant_id=str(tenant.id), key=key
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Config key not found")
    return {"message": "Config deleted successfully"}


# ===== Tenant Deployment Management =====


@router.get("/{slug}/deployment", response_model=schemas.TenantDeployment)
def get_tenant_deployment(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current deployment info for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    deployment = tenant_service.get_tenant_deployment(db=db, tenant_id=str(tenant.id))
    if not deployment:
        raise HTTPException(
            status_code=404, detail="No deployment found for this tenant"
        )
    return deployment


@router.post("/{slug}/deployment", response_model=schemas.TenantDeployment)
def update_tenant_deployment(
    slug: str,
    deployment_in: schemas.TenantDeploymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update or create deployment info for a tenant"""
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_service.update_tenant_deployment(
        db=db,
        tenant_id=str(tenant.id),
        version=deployment_in.current_version,
        deployed_by=deployment_in.deployed_by
        or (current_user.email if current_user else None),
        environment=deployment_in.environment,
    )


@router.put(
    "/{slug}/deployment/health", response_model=schemas.TenantDeploymentHealthResponse
)
def update_deployment_health(
    slug: str,
    health_in: schemas.TenantDeploymentHealthUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Update health status for a tenant deployment.

    Required fields:
    - status: Health status (healthy, degraded, unhealthy)
    - version: Deployed version
    - uptime_seconds: Application uptime in seconds

    Optional fields (for backwards compatibility):
    - database: Database connectivity (bool)
    - cache: Cache/Redis connectivity (bool)
    - platform: Platform info
    - python_version: Python version
    - installation_id: Unique installation identifier
    - reported_at: Client-side timestamp

    Requires API key authentication via X-API-Key header.
    Used by the main ChurnVision app to report deployment health.
    """
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    deployment = tenant_service.update_deployment_health_extended(
        db=db,
        tenant_id=str(tenant.id),
        status=health_in.status,
        database_healthy=health_in.database,
        cache_healthy=health_in.cache,
        uptime_seconds=health_in.uptime_seconds,
        version=health_in.version,
        platform=health_in.platform,
        python_version=health_in.python_version,
        installation_id=health_in.installation_id,
        reported_at=health_in.reported_at,
    )
    if not deployment:
        raise HTTPException(
            status_code=404, detail="No deployment found for this tenant"
        )

    return schemas.TenantDeploymentHealthResponse(acknowledged=True)


# ===== Installation Package =====


@router.get("/{slug}/install-package")
def download_installation_package(
    slug: str,
    docker_image: str = Query(
        default="ghcr.io/riyadmehdi7/churnvision_web_1_0:latest",
        description="Docker image to use in docker-compose.yml",
    ),
    admin_api_url: Optional[str] = Query(
        default=None, description="Admin API URL (defaults to production URL)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download installation package for a tenant.

    Returns a ZIP file containing:
    - docker-compose.yml
    - .env (with license key and configuration)
    - README.md (installation instructions)

    The package can be sent to the customer for installation.
    """
    tenant = tenant_service.get_tenant_by_slug(db, slug=slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    try:
        zip_bytes = installation_service.generate_installation_package(
            db=db,
            tenant=tenant,
            docker_image=docker_image,
            admin_api_url=admin_api_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"churnvision-{slug}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
