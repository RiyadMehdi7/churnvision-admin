from pydantic import BaseModel
from typing import List
from datetime import datetime

class DashboardStats(BaseModel):
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    mrr: float
    latest_version: str
    tenants_on_latest: int
    expiring_licenses_count: int
    overdue_invoices_count: int
    deprecated_version_tenants: int

class ActivityItem(BaseModel):
    id: str
    tenant_name: str
    action: str
    timestamp: datetime
