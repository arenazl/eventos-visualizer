from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = None
    price: Optional[Decimal] = None
    currency: str = Field(default="ARS", max_length=3)
    is_free: bool = False
    external_id: Optional[str] = None
    source_api: str = Field(..., max_length=50)
    external_url: Optional[str] = None
    image_url: Optional[str] = None
    attendee_count: int = Field(default=0, ge=0)
    is_featured: bool = False

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    is_free: Optional[bool] = None
    image_url: Optional[str] = None
    attendee_count: Optional[int] = None
    is_featured: Optional[bool] = None

class EventResponse(EventBase):
    id: str
    tags: Optional[List[str]] = None
    images: Optional[List[Dict[str, Any]]] = None
    max_attendees: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    synced_at: datetime

    class Config:
        from_attributes = True