from sqlalchemy import Column, String, Text, DateTime, Boolean, DECIMAL, Integer, JSON, ForeignKey, Index
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database.connection import Base

class Event(Base):
    __tablename__ = "events"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic event information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime)
    
    # Venue information
    venue_name = Column(String(255))
    venue_address = Column(Text)
    
    # Location (simplified for SQLite - in PostgreSQL would use PostGIS)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Event categorization
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    tags = Column(SQLiteJSON)  # Array of tags as JSON
    
    # Pricing
    price = Column(DECIMAL(10, 2))
    currency = Column(String(3), default='ARS')
    is_free = Column(Boolean, default=False)
    
    # External API tracking
    external_id = Column(String(255))
    source_api = Column(String(50), nullable=False)  # 'eventbrite', 'ticketmaster', 'meetup'
    external_url = Column(Text)
    api_data = Column(SQLiteJSON)  # Store original API response
    
    # Media
    image_url = Column(Text)
    images = Column(SQLiteJSON)  # Multiple images array
    
    # Event metadata
    attendee_count = Column(Integer, default=0)
    max_attendees = Column(Integer)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_events = relationship("UserEvent", back_populates="event")
    
    # Indexes (for better query performance)
    __table_args__ = (
        Index('idx_events_datetime', 'start_datetime'),
        Index('idx_events_category', 'category'),
        Index('idx_events_source_api', 'source_api', 'external_id'),
        Index('idx_events_location', 'latitude', 'longitude'),
        Index('idx_events_active', 'is_active', 'start_datetime'),
    )

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), nullable=False)  # Hex color code
    icon = Column(String(100))  # Icon identifier (Feather/FontAwesome)
    description = Column(Text)
    
    # Hierarchy support
    parent_id = Column(String(36), ForeignKey("categories.id"))
    
    # External API mappings
    eventbrite_id = Column(String(50))
    ticketmaster_id = Column(String(50))
    meetup_id = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)