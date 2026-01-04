from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.contract import Contract, ContractStatus, Asset
from app.schemas.contract import ContractCreate, ContractUpdate


def get_contracts(db: Session, tenant_id: str = None, status: str = None, skip: int = 0, limit: int = 100) -> List[Contract]:
    query = db.query(Contract)
    if tenant_id:
        query = query.filter(Contract.tenant_id == tenant_id)
    if status:
        query = query.filter(Contract.status == status)
    return query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()


def get_contract_by_id(db: Session, contract_id: str) -> Optional[Contract]:
    return db.query(Contract).filter(Contract.id == contract_id).first()


def create_contract(db: Session, contract_in: ContractCreate) -> Contract:
    db_contract = Contract(
        tenant_id=contract_in.tenant_id,
        contract_type=contract_in.contract_type,
        start_date=contract_in.start_date,
        end_date=contract_in.end_date,
        auto_renew=contract_in.auto_renew,
        notice_period_days=contract_in.notice_period_days,
        total_contract_value=contract_in.total_contract_value,
        payment_terms=contract_in.payment_terms,
        document_url=contract_in.document_url
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


def update_contract(db: Session, contract: Contract, contract_in: ContractUpdate) -> Contract:
    update_data = contract_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    db.commit()
    db.refresh(contract)
    return contract


def renew_contract(db: Session, contract: Contract, new_end_date: date, new_value: float = None) -> Contract:
    """Renew a contract with a new end date"""
    contract.start_date = contract.end_date
    contract.end_date = new_end_date
    contract.status = ContractStatus.ACTIVE
    contract.renewal_reminder_sent = False
    if new_value:
        contract.total_contract_value = new_value
    db.commit()
    db.refresh(contract)
    return contract


def expire_contract(db: Session, contract: Contract) -> Contract:
    contract.status = ContractStatus.EXPIRED
    db.commit()
    db.refresh(contract)
    return contract


def get_expiring_contracts(db: Session, days_ahead: int = 30) -> List[Contract]:
    """Get contracts expiring within the specified number of days"""
    from datetime import timedelta
    cutoff_date = date.today() + timedelta(days=days_ahead)
    return db.query(Contract).filter(
        Contract.status == ContractStatus.ACTIVE,
        Contract.end_date <= cutoff_date,
        Contract.end_date >= date.today()
    ).all()


def get_contract_assets(db: Session, contract_id: str) -> List[Asset]:
    return db.query(Asset).filter(Asset.contract_id == contract_id).all()


def add_contract_asset(db: Session, contract_id: str, name: str, asset_type: str, url: str = None) -> Asset:
    db_asset = Asset(
        contract_id=contract_id,
        name=name,
        asset_type=asset_type,
        url=url
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


def delete_contract_asset(db: Session, asset: Asset) -> None:
    db.delete(asset)
    db.commit()
