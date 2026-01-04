from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import support as schemas
from app.services import support_service

router = APIRouter()


# ===== Tickets =====

@router.get("/tickets", response_model=List[schemas.Ticket])
def list_tickets(
    tenant_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tickets with optional filters"""
    return support_service.get_tickets(
        db=db,
        tenant_id=str(tenant_id) if tenant_id else None,
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/tickets/{ticket_id}", response_model=schemas.Ticket)
def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific ticket by ID"""
    ticket = support_service.get_ticket_by_id(db=db, ticket_id=str(ticket_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/tickets", response_model=schemas.Ticket)
def create_ticket(
    ticket_in: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new support ticket"""
    return support_service.create_ticket(db=db, ticket_in=ticket_in)


@router.put("/tickets/{ticket_id}", response_model=schemas.Ticket)
def update_ticket(
    ticket_id: UUID,
    ticket_in: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing ticket"""
    ticket = support_service.get_ticket_by_id(db=db, ticket_id=str(ticket_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return support_service.update_ticket(db=db, ticket=ticket, ticket_in=ticket_in)


@router.post("/tickets/{ticket_id}/close", response_model=schemas.Ticket)
def close_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close a ticket"""
    ticket = support_service.get_ticket_by_id(db=db, ticket_id=str(ticket_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return support_service.close_ticket(db=db, ticket=ticket)


# ===== Announcements =====

@router.get("/announcements", response_model=List[schemas.Announcement])
def list_announcements(
    include_expired: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all announcements"""
    return support_service.get_announcements(
        db=db,
        include_expired=include_expired,
        skip=skip,
        limit=limit
    )


@router.get("/announcements/{announcement_id}", response_model=schemas.Announcement)
def get_announcement(
    announcement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific announcement by ID"""
    announcement = support_service.get_announcement_by_id(db=db, announcement_id=str(announcement_id))
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.post("/announcements", response_model=schemas.Announcement)
def create_announcement(
    announce_in: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new announcement"""
    return support_service.create_announcement(db=db, announce_in=announce_in)


@router.put("/announcements/{announcement_id}", response_model=schemas.Announcement)
def update_announcement(
    announcement_id: UUID,
    announce_in: schemas.AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing announcement"""
    announcement = support_service.get_announcement_by_id(db=db, announcement_id=str(announcement_id))
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return support_service.update_announcement(db=db, announcement=announcement, announce_in=announce_in)


@router.delete("/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an announcement"""
    announcement = support_service.get_announcement_by_id(db=db, announcement_id=str(announcement_id))
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    support_service.delete_announcement(db=db, announcement=announcement)
    return {"message": "Announcement deleted successfully"}
