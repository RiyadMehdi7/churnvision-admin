from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class TicketBase(BaseModel):
    subject: str
    description: str
    priority: str = "NORMAL"

class TicketCreate(TicketBase):
    tenant_id: UUID

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class Ticket(TicketBase):
    id: UUID
    tenant_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnnouncementBase(BaseModel):
    title: str
    content: str
    expires_at: Optional[datetime] = None

class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    expires_at: Optional[datetime] = None


class Announcement(AnnouncementBase):
    id: UUID
    published_at: datetime
    
    class Config:
        from_attributes = True
