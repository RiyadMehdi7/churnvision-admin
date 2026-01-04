from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.release import ReleaseTrack, ReleaseStatus

class ReleaseBase(BaseModel):
    version: str
    track: ReleaseTrack = ReleaseTrack.STABLE
    status: ReleaseStatus = ReleaseStatus.DRAFT
    docker_images: List[str] = []
    
    requires_downtime: bool = False
    breaking_changes: List[str] = []
    release_notes: Optional[str] = None

class ReleaseCreate(ReleaseBase):
    pass

class ReleaseUpdate(BaseModel):
    status: Optional[ReleaseStatus] = None
    docker_images: Optional[List[str]] = None
    release_notes: Optional[str] = None

class Release(ReleaseBase):
    id: UUID
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
