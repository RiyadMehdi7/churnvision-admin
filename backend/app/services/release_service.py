from datetime import datetime
from sqlalchemy.orm import Session
from app.models.release import Release, ReleaseStatus
from app.schemas.release import ReleaseCreate, ReleaseUpdate

def create_release(db: Session, release_in: ReleaseCreate) -> Release:
    db_release = Release(
        version=release_in.version,
        track=release_in.track,
        status=release_in.status,
        docker_images=release_in.docker_images,
        requires_downtime=release_in.requires_downtime,
        breaking_changes=release_in.breaking_changes,
        release_notes=release_in.release_notes
    )
    if release_in.status == ReleaseStatus.PUBLISHED:
        db_release.published_at = datetime.utcnow()
        
    db.add(db_release)
    db.commit()
    db.refresh(db_release)
    return db_release

def get_releases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Release).order_by(Release.created_at.desc()).offset(skip).limit(limit).all()

def get_release_by_version(db: Session, version: str):
    return db.query(Release).filter(Release.version == version).first()

def update_release(db: Session, release: Release, release_in: ReleaseUpdate) -> Release:
    update_data = release_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(release, field, value)
    
    if release_in.status == ReleaseStatus.PUBLISHED and not release.published_at:
        release.published_at = datetime.utcnow()
        
    db.add(release)
    db.commit()
    db.refresh(release)
    return release
