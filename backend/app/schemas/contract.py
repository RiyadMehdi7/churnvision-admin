from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from app.models.contract import ContractStatus

class ContractBase(BaseModel):
    contract_type: str = "subscription"
    start_date: date
    end_date: date
    auto_renew: bool = True
    notice_period_days: int = 30
    total_contract_value: Decimal
    payment_terms: str = "net30"
    document_url: Optional[str] = None

class ContractCreate(ContractBase):
    tenant_id: UUID


class ContractUpdate(BaseModel):
    contract_type: Optional[str] = None
    end_date: Optional[date] = None
    auto_renew: Optional[bool] = None
    notice_period_days: Optional[int] = None
    total_contract_value: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    document_url: Optional[str] = None
    status: Optional[ContractStatus] = None


class ContractRenew(BaseModel):
    new_end_date: date
    new_value: Optional[Decimal] = None


class Contract(ContractBase):
    id: UUID
    tenant_id: UUID
    status: ContractStatus
    renewal_reminder_sent: bool

    class Config:
        from_attributes = True

class AssetCreate(BaseModel):
    name: str
    asset_type: str
    url: Optional[str] = None


class Asset(BaseModel):
    id: UUID
    name: str
    asset_type: str
    url: Optional[str]

    class Config:
        from_attributes = True
