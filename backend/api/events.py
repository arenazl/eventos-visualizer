from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.events import Event, Category
from models.users import User, UserEvent
from schemas.events import EventResponse, EventCreate, EventUpdate

router = APIRouter()

@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: Optional[int] = Query(25, ge=1, le=100),
    is_free: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get events with filtering options"""
    
    query = db.query(Event).filter(Event.is_active == True)
    
    # Apply filters
    if category:
        query = query.filter(Event.category == category)
    
    if is_free is not None:
        query = query.filter(Event.is_free == is_free)
    
    if date_from:
        query = query.filter(Event.start_datetime >= date_from)
    
    if date_to:
        query = query.filter(Event.start_datetime <= date_to)
    
    # Location filtering (simplified - in real implementation would use PostGIS)
    if latitude and longitude:
        # Simple bounding box calculation (not precise, but works for demo)
        lat_delta = radius_km * 0.009  # Rough conversion
        lng_delta = radius_km * 0.009
        
        query = query.filter(
            and_(
                Event.latitude.between(latitude - lat_delta, latitude + lat_delta),
                Event.longitude.between(longitude - lng_delta, longitude + lng_delta)
            )
        )
    
    # Order by start date
    query = query.order_by(Event.start_datetime.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    events = query.all()
    
    return events

@router.get("/search")
def search_events(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search events by title and description"""
    
    search_term = f"%{q}%"
    
    events = db.query(Event).filter(
        and_(
            Event.is_active == True,
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.venue_name.ilike(search_term)
            )
        )
    ).order_by(Event.start_datetime.asc()).offset(skip).limit(limit).all()
    
    return events

@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific event by ID"""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.get("/categories/", response_model=List[dict])
def get_categories(db: Session = Depends(get_db)):
    """Get all event categories"""
    
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "color": cat.color,
            "icon": cat.icon,
            "description": cat.description
        } for cat in categories
    ]