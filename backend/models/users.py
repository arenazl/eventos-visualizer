from sqlalchemy import Column, String, Text, DateTime, Boolean, DECIMAL, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database.connection import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(Text)
    
    # OAuth integrations
    google_id = Column(String(255), unique=True)
    google_access_token = Column(Text)
    google_refresh_token = Column(Text)
    
    # Location preferences
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100), default='Argentina')
    
    # User preferences
    radius_km = Column(Integer, default=25)
    timezone = Column(String(100), default='America/Argentina/Buenos_Aires')
    locale = Column(String(10), default='es-AR')
    
    # Notification settings
    push_enabled = Column(Boolean, default=False)
    push_subscription = Column(SQLiteJSON)  # Web Push subscription data
    notification_preferences = Column(SQLiteJSON, default={
        "event_reminders": True,
        "new_events_in_categories": True,
        "event_updates": True,
        "quiet_hours": {"start": "22:00", "end": "08:00"}
    })
    
    # Preferences
    favorite_categories = Column(SQLiteJSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    user_events = relationship("UserEvent", back_populates="user")

class UserEvent(Base):
    __tablename__ = "user_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False)
    
    # User's relationship with event
    status = Column(String(50), default='interested')  # 'interested', 'going', 'not_going', 'maybe'
    
    # Notification tracking
    notification_24h_sent = Column(Boolean, default=False)
    notification_1h_sent = Column(Boolean, default=False)
    notification_start_sent = Column(Boolean, default=False)
    
    # Calendar integration
    calendar_synced = Column(Boolean, default=False)
    google_calendar_event_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_events")
    event = relationship("Event", back_populates="user_events")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='_user_event_uc'),
    )

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"))
    
    # Notification details
    type = Column(String(50), nullable=False)  # 'event_reminder', 'new_event', 'event_update'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(SQLiteJSON)  # Additional notification data
    
    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    
    # Platform tracking
    platform = Column(String(20), default='web')  # 'web', 'mobile', 'email'
    
    created_at = Column(DateTime, default=datetime.utcnow)