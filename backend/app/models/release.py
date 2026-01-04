import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base
from datetime import datetime

class ReleaseTrack(str, enum.Enum):
    STABLE = "STABLE"
    BETA = "BETA"
    LTS = "LTS"

class ReleaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"

class Release(Base):
    __tablename__ = "releases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String, unique=True, nullable=False) # "2.1.0"
    track = Column(Enum(ReleaseTrack), default=ReleaseTrack.STABLE)
    status = Column(Enum(ReleaseStatus), default=ReleaseStatus.DRAFT)
    
    # Artifacts (simplified list of strings for docker images)
    docker_images = Column(ARRAY(String), default=[]) 
    migration_scripts = Column(String, nullable=True)

    # Compatibility
    min_upgrade_from = Column(String, nullable=True)
    requires_downtime = Column(Boolean, default=False)
    breaking_changes = Column(ARRAY(String), default=[])

    # Documentation
    release_notes = Column(String, nullable=True) # Markdown
    upgrade_guide = Column(String, nullable=True)

    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
