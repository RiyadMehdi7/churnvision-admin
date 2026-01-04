from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import contract as schemas
from app.services import contract_service

router = APIRouter()


@router.get("/", response_model=List[schemas.Contract])
def list_contracts(
    tenant_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all contracts with optional filters"""
    return contract_service.get_contracts(
        db=db,
        tenant_id=str(tenant_id) if tenant_id else None,
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/expiring", response_model=List[schemas.Contract])
def get_expiring_contracts(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contracts expiring within the specified number of days"""
    return contract_service.get_expiring_contracts(db=db, days_ahead=days_ahead)


@router.get("/{contract_id}", response_model=schemas.Contract)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific contract by ID"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.post("/", response_model=schemas.Contract)
def create_contract(
    contract_in: schemas.ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new contract"""
    return contract_service.create_contract(db=db, contract_in=contract_in)


@router.put("/{contract_id}", response_model=schemas.Contract)
def update_contract(
    contract_id: UUID,
    contract_in: schemas.ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing contract"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_service.update_contract(db=db, contract=contract, contract_in=contract_in)


@router.post("/{contract_id}/renew", response_model=schemas.Contract)
def renew_contract(
    contract_id: UUID,
    renew_data: schemas.ContractRenew,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renew a contract with a new end date"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_service.renew_contract(
        db=db,
        contract=contract,
        new_end_date=renew_data.new_end_date,
        new_value=renew_data.new_value
    )


@router.post("/{contract_id}/expire", response_model=schemas.Contract)
def expire_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a contract as expired"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_service.expire_contract(db=db, contract=contract)


# ===== Contract Assets =====

@router.get("/{contract_id}/assets", response_model=List[schemas.Asset])
def get_contract_assets(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all assets for a contract"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_service.get_contract_assets(db=db, contract_id=str(contract_id))


@router.post("/{contract_id}/assets", response_model=schemas.Asset)
def add_contract_asset(
    contract_id: UUID,
    asset_in: schemas.AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an asset to a contract"""
    contract = contract_service.get_contract_by_id(db=db, contract_id=str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_service.add_contract_asset(
        db=db,
        contract_id=str(contract_id),
        name=asset_in.name,
        asset_type=asset_in.asset_type,
        url=asset_in.url
    )
