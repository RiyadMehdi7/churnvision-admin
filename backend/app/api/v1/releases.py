from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas import release as schemas
from app.services import release_service

router = APIRouter()

@router.post("/", response_model=schemas.Release)
def create_release(
    release_in: schemas.ReleaseCreate,
    db: Session = Depends(get_db)
):
    if release_service.get_release_by_version(db, release_in.version):
        raise HTTPException(status_code=400, detail="Version already exists")
    return release_service.create_release(db=db, release_in=release_in)

@router.get("/", response_model=List[schemas.Release])
def read_releases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return release_service.get_releases(db, skip=skip, limit=limit)

@router.put("/{version}", response_model=schemas.Release)
def update_release(
    version: str,
    release_in: schemas.ReleaseUpdate,
    db: Session = Depends(get_db)
):
    db_release = release_service.get_release_by_version(db, version)
    if not db_release:
        raise HTTPException(status_code=404, detail="Release not found")
    return release_service.update_release(db=db, release=db_release, release_in=release_in)
