from fastapi import APIRouter
from app.api.v1 import (
    auth,
    tenants,
    licenses,
    releases,
    billing,
    telemetry,
    contracts,
    support,
    dashboard,
    webhooks,
)

api_router = APIRouter()


# Health check at /api/v1/health for deployment healthchecks
@api_router.get("/health", tags=["health"])
def api_health():
    """Health check endpoint for deployment monitoring"""
    return {"status": "ok", "api_version": "v1"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["licenses"])
api_router.include_router(releases.router, prefix="/releases", tags=["releases"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
