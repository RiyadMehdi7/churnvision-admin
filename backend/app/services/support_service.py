from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.support import Ticket, Announcement
from app.schemas.support import TicketCreate, TicketUpdate, AnnouncementCreate, AnnouncementUpdate


def get_tickets(db: Session, tenant_id: str = None, status: str = None, skip: int = 0, limit: int = 100) -> List[Ticket]:
    query = db.query(Ticket)
    if tenant_id:
        query = query.filter(Ticket.tenant_id == tenant_id)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


def get_ticket_by_id(db: Session, ticket_id: str) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def create_ticket(db: Session, ticket_in: TicketCreate) -> Ticket:
    db_ticket = Ticket(
        tenant_id=ticket_in.tenant_id,
        subject=ticket_in.subject,
        description=ticket_in.description,
        priority=ticket_in.priority
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket: Ticket, ticket_in: TicketUpdate) -> Ticket:
    update_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def close_ticket(db: Session, ticket: Ticket) -> Ticket:
    ticket.status = "CLOSED"
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def get_announcements(db: Session, include_expired: bool = False, skip: int = 0, limit: int = 100) -> List[Announcement]:
    query = db.query(Announcement)
    if not include_expired:
        query = query.filter(
            (Announcement.expires_at == None) | (Announcement.expires_at > datetime.utcnow())
        )
    return query.order_by(Announcement.published_at.desc()).offset(skip).limit(limit).all()


def get_announcement_by_id(db: Session, announcement_id: str) -> Optional[Announcement]:
    return db.query(Announcement).filter(Announcement.id == announcement_id).first()


def create_announcement(db: Session, announce_in: AnnouncementCreate) -> Announcement:
    db_ann = Announcement(
        title=announce_in.title,
        content=announce_in.content,
        expires_at=announce_in.expires_at
    )
    db.add(db_ann)
    db.commit()
    db.refresh(db_ann)
    return db_ann


def update_announcement(db: Session, announcement: Announcement, announce_in: AnnouncementUpdate) -> Announcement:
    update_data = announce_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(announcement, field, value)
    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement: Announcement) -> None:
    db.delete(announcement)
    db.commit()
