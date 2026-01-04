from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas import dashboard as schemas
from app.services import dashboard_service

router = APIRouter()

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    return dashboard_service.get_dashboard_stats(db=db)

@router.get("/activity", response_model=List[schemas.ActivityItem])
def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return dashboard_service.get_recent_activity(db=db, limit=limit)
