from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.tenant import Tenant, TenantStatus, TenantDeployment
from app.models.license import License
from app.models.billing import Invoice, InvoiceStatus, Subscription, SubscriptionStatus
from app.models.release import Release, ReleaseStatus

def get_dashboard_stats(db: Session) -> dict:
    # Tenant counts
    total_tenants = db.query(func.count(Tenant.id)).scalar() or 0
    active_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.status == TenantStatus.ACTIVE
    ).scalar() or 0
    trial_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.status == TenantStatus.TRIAL
    ).scalar() or 0

    # MRR calculation from active subscriptions
    mrr_result = db.query(func.sum(Subscription.base_price)).filter(
        Subscription.status == SubscriptionStatus.ACTIVE
    ).scalar()
    mrr = float(mrr_result) if mrr_result else 0.0

    # Get latest published release version
    latest_release = db.query(Release).filter(
        Release.status == ReleaseStatus.PUBLISHED
    ).order_by(Release.published_at.desc()).first()
    latest_version = latest_release.version if latest_release else "N/A"

    # Count tenants on latest version
    tenants_on_latest = 0
    if latest_release:
        tenants_on_latest = db.query(func.count(TenantDeployment.id)).filter(
            TenantDeployment.current_version == latest_version
        ).scalar() or 0

    # Licenses expiring in 30 days
    thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
    expiring_licenses_count = db.query(func.count(License.id)).filter(
        License.expires_at <= thirty_days_from_now,
        License.expires_at > datetime.utcnow(),
        License.revoked == False
    ).scalar() or 0

    # Overdue invoices
    overdue_invoices_count = db.query(func.count(Invoice.id)).filter(
        Invoice.status == InvoiceStatus.OVERDUE
    ).scalar() or 0

    # Tenants on deprecated versions
    deprecated_versions = db.query(Release.version).filter(
        Release.status == ReleaseStatus.DEPRECATED
    ).subquery()
    deprecated_version_tenants = db.query(func.count(TenantDeployment.id)).filter(
        TenantDeployment.current_version.in_(deprecated_versions)
    ).scalar() or 0

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "trial_tenants": trial_tenants,
        "mrr": mrr,
        "latest_version": latest_version,
        "tenants_on_latest": tenants_on_latest,
        "expiring_licenses_count": expiring_licenses_count,
        "overdue_invoices_count": overdue_invoices_count,
        "deprecated_version_tenants": deprecated_version_tenants,
    }

def get_recent_activity(db: Session, limit: int = 10) -> list:
    # Get recent tenant creations and license events
    activities = []

    # Recent tenants
    recent_tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).limit(limit).all()
    for tenant in recent_tenants:
        activities.append({
            "id": str(tenant.id),
            "tenant_name": tenant.name,
            "action": f"started {tenant.status.value.lower()}",
            "timestamp": tenant.created_at,
        })

    # Recent licenses
    recent_licenses = db.query(License).order_by(License.issued_at.desc()).limit(limit).all()
    for lic in recent_licenses:
        tenant = db.query(Tenant).filter(Tenant.id == lic.tenant_id).first()
        if tenant:
            activities.append({
                "id": str(lic.id),
                "tenant_name": tenant.name,
                "action": "license issued" if not lic.revoked else "license revoked",
                "timestamp": lic.issued_at,
            })

    # Sort by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]
