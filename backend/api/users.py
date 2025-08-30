from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from models.users import User, UserEvent
from models.events import Event

router = APIRouter()

@router.get("/{user_id}/events")
def get_user_events(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get events saved by a specific user"""
    
    user_events = db.query(UserEvent).join(Event).filter(
        UserEvent.user_id == user_id,
        Event.is_active == True
    ).order_by(Event.start_datetime.asc()).all()
    
    return [
        {
            "user_event_id": ue.id,
            "event_id": ue.event_id,
            "status": ue.status,
            "calendar_synced": ue.calendar_synced,
            "created_at": ue.created_at
        } for ue in user_events
    ]

@router.post("/{user_id}/events/{event_id}")
def save_user_event(
    user_id: str,
    event_id: str,
    status: str = "interested",
    db: Session = Depends(get_db)
):
    """Save an event for a user"""
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already saved
    existing = db.query(UserEvent).filter(
        UserEvent.user_id == user_id,
        UserEvent.event_id == event_id
    ).first()
    
    if existing:
        # Update existing
        existing.status = status
        db.commit()
        return {"message": "Event status updated"}
    else:
        # Create new
        user_event = UserEvent(
            user_id=user_id,
            event_id=event_id,
            status=status
        )
        db.add(user_event)
        db.commit()
        return {"message": "Event saved successfully"}