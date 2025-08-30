# 🎉 EVENTOS VISUALIZER - PRP Completo y Detallado

**Date**: January 2025 | **Confidence**: 9/10 | **Framework**: FastAPI + PostgreSQL + React + Vite + PWA

---

## 🎯 CONTEXTO DEL PROYECTO

### **Descripción del Sistema**
Sistema completo de descubrimiento y gestión de eventos mobile-first con capacidades PWA. Integra múltiples APIs externas (Eventbrite, Ticketmaster, Meetup) para proporcionar cobertura completa de eventos locales con sincronización bidireccional con Google Calendar y notificaciones push en tiempo real.

### **Stack Tecnológico Definitivo**
```yaml
Backend:
  - FastAPI (Python 3.11+) - Puerto 8001 INMUTABLE
  - PostgreSQL 14+ con PostGIS para geolocalización
  - Redis para cache y session storage
  - Celery para background tasks
  - WebSockets para notificaciones en tiempo real

Frontend:
  - React 18+ con TypeScript
  - Vite como build tool - Puerto 5174 INMUTABLE  
  - TailwindCSS + Bootstrap 5 (basado en template)
  - PWA con Service Workers
  - Zustand para state management

APIs Externas:
  - Eventbrite API (Priority 1)
  - Ticketmaster Discovery API (Priority 1)  
  - Meetup API (Priority 2)
  - Google Calendar API (bidirectional sync)
  - Google Maps API (geolocalización)

Infrastructure:
  - IP WSL: 172.29.228.80 (NUNCA localhost)
  - Docker para development consistency
  - Railway/Vercel para production deployment
```

### **Success Criteria Específicos**
- ✅ **Performance**: <3s loading inicial en mobile, <1s navegación entre pantallas
- ✅ **APIs Integration**: 3+ APIs externas funcionando con real data
- ✅ **PWA**: Installable, offline support, push notifications
- ✅ **Geolocation**: Precisión <100m, múltiples radius options (5km, 10km, 25km, 50km)
- ✅ **Design**: Visualmente idéntico al template HTML proporcionado
- ✅ **Calendar Sync**: Bidirectional con Google Calendar
- ✅ **Notifications**: 24h/1h antes del evento, nuevos eventos en categorías favoritas

---

## 🎨 TEMPLATE HTML TO REACT MAPPING (CRÍTICO)

### **Template Base Analysis**
**Template**: `docs/templates/SAMPLE-APW.htm` (E-commerce Bootstrap template)  
**Adaptación**: Product-focused → Event-focused  
**Framework**: Bootstrap 5 con custom CSS variables  

### **Core Design System del Template**
```css
/* Variables CSS del template original */
--theme-color: #0da487 (Primary teal)
--theme-color1: #0e947a (Darker teal)  
--theme-color-rgb: 13,164,135

/* Fluid typography system */
font-size: calc(14px + 4*(100vw - 320px)/1600);
padding: calc(8px + 6*(100vw - 320px)/1600);
```

### **Template Structure → React Components Mapping**

#### **1. Product Card → Event Card Conversion**
```jsx
// Template Original Structure
<div class="product-box product-box-bg wow fadeInUp">
  <div class="product-image">
    <img src="..." class="img-fluid blur-up lazyload" alt="">
  </div>
  <div class="product-detail">
    <div class="product-rating mt-2">
      <!-- Star ratings → Attendee count -->
    </div>
    <!-- Product info → Event info -->
  </div>
</div>

// React Component Adaptación EXACTA
function EventCard({ event }) {
  return (
    <div className="product-box product-box-bg wow fadeInUp event-card">
      {/* Event Image Section */}
      <div className="product-image event-image">
        <Link to={`/events/${event.id}`}>
          <img 
            src={event.image || '/placeholder-event.jpg'} 
            className="img-fluid blur-up lazyload" 
            alt={event.title}
            loading="lazy"
          />
        </Link>
        
        {/* Category Badge (reemplaza product badge) */}
        <div className="absolute top-2 right-2">
          <span className={`badge bg-${getCategoryColor(event.category)} text-white`}>
            {event.category}
          </span>
        </div>
        
        {/* Price Badge */}
        <div className="absolute bottom-2 left-2">
          <span className="badge bg-success text-white font-weight-bold">
            {event.is_free ? 'GRATIS' : `$${event.price}`}
          </span>
        </div>
      </div>
      
      {/* Event Detail Section */}
      <div className="product-detail event-detail">
        {/* Event Title */}
        <h6 className="text-title fw-500 mt-2">
          <Link to={`/events/${event.id}`} className="text-decoration-none">
            {event.title}
          </Link>
        </h6>
        
        {/* Event Description */}
        <p className="text-content text-muted small mb-2 line-clamp-2">
          {event.description}
        </p>
        
        {/* Date & Time */}
        <div className="d-flex align-items-center text-content small mb-2">
          <i className="feather icon-calendar text-theme me-1"></i>
          <span>{formatEventDate(event.start_datetime)}</span>
        </div>
        
        {/* Location */}
        <div className="d-flex align-items-center text-content small mb-2">
          <i className="feather icon-map-pin text-theme me-1"></i>
          <span className="text-truncate">{event.venue_name}</span>
        </div>
        
        {/* Attendee Count (reemplaza product rating) */}
        <div className="product-rating event-attendees mb-2">
          <div className="d-flex align-items-center">
            <i className="feather icon-users text-warning me-1"></i>
            <span className="small text-muted">
              {event.attendee_count || 0} interesados
            </span>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="btn-group w-100" role="group">
          <button 
            className="btn btn-sm theme-bg-color text-white flex-fill"
            onClick={() => handleViewDetails(event.id)}
          >
            Ver Detalles
          </button>
          <button 
            className="btn btn-sm btn-outline-secondary"
            onClick={() => handleSaveEvent(event.id)}
          >
            <i className="feather icon-heart"></i>
          </button>
        </div>
      </div>
    </div>
  );
}
```

#### **2. Header Navigation → Event App Navigation**
```jsx
// Mantener estructura exacta del template
function Header() {
  return (
    <header className="pb-md-4 pb-0">
      {/* Top notification bar */}
      <div className="header-top bg-dark d-sm-block d-none">
        <div className="container">
          <div className="row">
            <div className="col-12">
              <div className="header-top-contain text-center">
                <p className="text-white mb-0 small">
                  Descubre eventos increíbles en tu ciudad 🎉
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main navigation */}
      <div className="top-nav top-header sticky-header">
        <div className="container">
          <div className="row">
            <div className="col-12">
              <EventNavigation />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
```

#### **3. Grid Layout → Event Grid**
```jsx
// Mantener sistema de grid Bootstrap del template
function EventGrid({ events, loading }) {
  return (
    <section className="home-section home-section-ratio pt-2">
      <div className="container">
        <div className="row g-sm-4 g-3">
          {events.map((event) => (
            <div 
              key={event.id} 
              className="col-xxl-3 col-xl-4 col-lg-4 col-md-6 col-sm-6 col-6"
            >
              <EventCard event={event} />
            </div>
          ))}
        </div>
        
        {loading && (
          <div className="row">
            <div className="col-12 text-center py-4">
              <div className="spinner-border text-theme" role="status">
                <span className="visually-hidden">Cargando eventos...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
```

### **CSS Classes Críticas a Preservar**
```css
/* Layout Classes (Bootstrap) */
.container, .row, .col-*, .g-3, .g-4, .g-sm-4

/* Component Classes del Template */  
.product-box → .event-card (mantener ambas clases)
.product-box-bg → aplicar también a .event-card
.product-image → .event-image
.product-detail → .event-detail
.product-rating → .event-attendees

/* Button System */
.btn, .btn-sm, .btn-md, .theme-bg-color, .btn-outline-secondary

/* Utility Classes */
.img-fluid, .blur-up, .lazyload
.text-title, .text-content, .fw-500
.text-truncate, .line-clamp-2
```

---

## 🏗️ BACKEND ARCHITECTURE DETALLADA

### **FastAPI Structure**
```
backend/
├── main.py                 # FastAPI app principal (Puerto 8001)
├── api/
│   ├── __init__.py
│   ├── dependencies.py     # Auth, database deps
│   ├── events.py          # Event CRUD endpoints
│   ├── users.py           # User management
│   ├── external_apis.py   # API integrations
│   ├── notifications.py   # Push notifications
│   └── websockets.py      # Real-time connections
├── models/
│   ├── __init__.py
│   ├── events.py          # Event SQLAlchemy models
│   ├── users.py           # User models
│   └── notifications.py   # Notification models
├── services/
│   ├── __init__.py
│   ├── eventbrite.py      # Eventbrite API integration
│   ├── ticketmaster.py    # Ticketmaster API integration
│   ├── meetup.py          # Meetup API integration
│   ├── google_calendar.py # Calendar sync service
│   ├── geolocation.py     # Location services
│   └── notifications.py   # Push notification service
├── schemas/
│   ├── __init__.py
│   ├── events.py          # Pydantic schemas
│   ├── users.py           # User schemas
│   └── external_apis.py   # External API schemas
├── database/
│   ├── __init__.py
│   ├── connection.py      # PostgreSQL connection
│   ├── migrations/        # Alembic migrations
│   └── init.sql          # Initial schema
├── utils/
│   ├── __init__.py
│   ├── auth.py           # JWT handling
│   ├── cache.py          # Redis operations
│   └── helpers.py        # Utility functions
└── config.py             # Settings and environment
```

### **Core FastAPI Application (main.py)**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from contextlib import asynccontextmanager

from api import events, users, external_apis, notifications
from database.connection import init_db, close_db
from services.external_apis import EventAggregationService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Eventos Visualizer Backend...")
    await init_db()
    
    # Start background task for API sync
    background_tasks = asyncio.create_task(
        EventAggregationService.periodic_sync()
    )
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Eventos Visualizer Backend...")
    background_tasks.cancel()
    await close_db()

app = FastAPI(
    title="Eventos Visualizer API",
    description="Sistema completo de eventos mobile-first con PWA",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for WSL IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://172.29.228.80:5174",  # Frontend Vite dev server
        "http://localhost:5174",       # Fallback
        "https://eventos-visualizer.vercel.app"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(external_apis.router, prefix="/api/external", tags=["external"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

# WebSocket manager for real-time notifications
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            logger.info(f"WebSocket message from {user_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "eventos-visualizer-backend",
        "version": "1.0.0",
        "port": 8001
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
```

### **PostgreSQL Schema Optimizado**
```sql
-- Enable PostGIS extension for geolocation
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Events table with geolocation support
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    venue_name VARCHAR(255),
    venue_address TEXT,
    
    -- PostGIS geolocation (SRID 4326 = WGS 84)
    location GEOMETRY(POINT, 4326),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Event categorization
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    tags TEXT[], -- Array of tags
    
    -- Pricing
    price DECIMAL(10,2),
    currency CHAR(3) DEFAULT 'ARS',
    is_free BOOLEAN DEFAULT false,
    
    -- External API tracking
    external_id VARCHAR(255),
    source_api VARCHAR(50) NOT NULL, -- 'eventbrite', 'ticketmaster', 'meetup'
    external_url TEXT,
    api_data JSONB, -- Store original API response
    
    -- Media
    image_url TEXT,
    images JSONB, -- Multiple images array
    
    -- Event metadata
    attendee_count INTEGER DEFAULT 0,
    max_attendees INTEGER,
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimized indexes for geolocation and search
CREATE INDEX idx_events_location ON events USING GIST(location);
CREATE INDEX idx_events_datetime ON events (start_datetime DESC);
CREATE INDEX idx_events_category ON events (category);
CREATE INDEX idx_events_source_api ON events (source_api, external_id);
CREATE INDEX idx_events_tags ON events USING GIN(tags);
CREATE INDEX idx_events_active ON events (is_active, start_datetime) WHERE is_active = true;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    
    -- OAuth integrations
    google_id VARCHAR(255) UNIQUE,
    google_access_token TEXT,
    google_refresh_token TEXT,
    
    -- Location preferences
    home_location GEOMETRY(POINT, 4326),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Argentina',
    
    -- User preferences
    radius_km INTEGER DEFAULT 25,
    timezone VARCHAR(100) DEFAULT 'America/Argentina/Buenos_Aires',
    locale VARCHAR(10) DEFAULT 'es-AR',
    
    -- Notification settings
    push_enabled BOOLEAN DEFAULT false,
    push_subscription JSONB, -- Web Push subscription data
    notification_preferences JSONB DEFAULT '{
        "event_reminders": true,
        "new_events_in_categories": true,
        "event_updates": true,
        "quiet_hours": {"start": "22:00", "end": "08:00"}
    }'::JSONB,
    
    -- Preferences
    favorite_categories TEXT[] DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- User events (saved/interested events)
CREATE TABLE user_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    
    -- User's relationship with event
    status VARCHAR(50) DEFAULT 'interested', -- 'interested', 'going', 'not_going', 'maybe'
    
    -- Notification tracking
    notification_24h_sent BOOLEAN DEFAULT false,
    notification_1h_sent BOOLEAN DEFAULT false,
    notification_start_sent BOOLEAN DEFAULT false,
    
    -- Calendar integration
    calendar_synced BOOLEAN DEFAULT false,
    google_calendar_event_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, event_id)
);

-- Categories reference table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL, -- Hex color code
    icon VARCHAR(100), -- Icon identifier (Feather/FontAwesome)
    description TEXT,
    
    -- Hierarchy support
    parent_id UUID REFERENCES categories(id),
    
    -- External API mappings
    eventbrite_id VARCHAR(50),
    ticketmaster_id VARCHAR(50),
    meetup_id VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default categories
INSERT INTO categories (name, slug, color, icon, sort_order) VALUES
('Música', 'musica', '#ff6b6b', 'music', 1),
('Deportes', 'deportes', '#4ecdc4', 'activity', 2),
('Cultural', 'cultural', '#45b7d1', 'book-open', 3),
('Tech', 'tech', '#96ceb4', 'cpu', 4),
('Fiestas', 'fiestas', '#feca57', 'star', 5),
('Hobbies', 'hobbies', '#ff9ff3', 'heart', 6),
('Internacional', 'internacional', '#54a0ff', 'globe', 7);

-- Notifications table for tracking sent notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    
    -- Notification details
    type VARCHAR(50) NOT NULL, -- 'event_reminder', 'new_event', 'event_update'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB, -- Additional notification data
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered BOOLEAN DEFAULT false,
    clicked BOOLEAN DEFAULT false,
    
    -- Platform tracking
    platform VARCHAR(20) DEFAULT 'web', -- 'web', 'mobile', 'email'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply auto-update triggers
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_events_updated_at BEFORE UPDATE ON user_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 🔌 EXTERNAL APIS INTEGRATION

### **1. Eventbrite API Service**
```python
# services/eventbrite.py
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from config import settings
from schemas.external_apis import EventbriteEventSchema
from utils.cache import cache_result

logger = logging.getLogger(__name__)

class EventbriteService:
    """Eventbrite API integration service"""
    
    BASE_URL = "https://www.eventbriteapi.com/v3"
    
    def __init__(self):
        self.api_key = settings.EVENTBRITE_API_KEY
        self.session = None
    
    async def get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    @cache_result(ttl=1800)  # Cache for 30 minutes
    async def search_events(
        self, 
        location: str = None,
        latitude: float = None,
        longitude: float = None,
        radius: str = "25km",
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 1
    ) -> List[Dict]:
        """Search for events using Eventbrite API"""
        
        session = await self.get_session()
        
        # Build query parameters
        params = {
            "expand": "venue,organizer,ticket_classes,category",
            "page": page,
            "sort_by": "date",
            "time_filter": "current_future"
        }
        
        # Location filtering
        if latitude and longitude:
            params["location.latitude"] = latitude
            params["location.longitude"] = longitude
            params["location.within"] = radius
        elif location:
            params["location.address"] = location
        
        # Date filtering
        if start_date:
            params["start_date.range_start"] = start_date.isoformat()
        if end_date:
            params["start_date.range_end"] = end_date.isoformat()
            
        # Category filtering
        if categories:
            # Map our categories to Eventbrite category IDs
            category_mapping = {
                "musica": "103",  # Music
                "deportes": "108",  # Sports & Fitness  
                "tech": "102",  # Science & Technology
                "cultural": "105",  # Performing & Visual Arts
                "fiestas": "110"  # Food & Drink
            }
            eventbrite_cats = [category_mapping.get(cat) for cat in categories if cat in category_mapping]
            if eventbrite_cats:
                params["categories"] = ",".join(eventbrite_cats)
        
        try:
            async with session.get(f"{self.BASE_URL}/events/search/", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("events", [])
                    
                    logger.info(f"Retrieved {len(events)} events from Eventbrite")
                    
                    # Transform to our schema
                    transformed_events = []
                    for event in events:
                        transformed_event = await self._transform_event(event)
                        if transformed_event:
                            transformed_events.append(transformed_event)
                    
                    return transformed_events
                    
                else:
                    logger.error(f"Eventbrite API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Eventbrite events: {str(e)}")
            return []
    
    async def _transform_event(self, event: Dict) -> Optional[Dict]:
        """Transform Eventbrite event to our schema"""
        try:
            venue = event.get("venue", {}) or {}
            organizer = event.get("organizer", {}) or {}
            category = event.get("category", {}) or {}
            ticket_classes = event.get("ticket_classes", [])
            
            # Extract pricing information
            is_free = True
            price = 0.0
            currency = "ARS"
            
            if ticket_classes:
                for ticket in ticket_classes:
                    if ticket.get("cost"):
                        cost = ticket["cost"]
                        if cost.get("major_value", 0) > 0:
                            is_free = False
                            price = float(cost.get("major_value", 0))
                            currency = cost.get("currency", "USD")
                            break
            
            # Parse datetime
            start_datetime = None
            if event.get("start", {}).get("utc"):
                start_datetime = datetime.fromisoformat(
                    event["start"]["utc"].replace("Z", "+00:00")
                )
            
            end_datetime = None  
            if event.get("end", {}).get("utc"):
                end_datetime = datetime.fromisoformat(
                    event["end"]["utc"].replace("Z", "+00:00")
                )
            
            # Extract location
            latitude = None
            longitude = None
            if venue.get("address"):
                latitude = venue["address"].get("latitude")
                longitude = venue["address"].get("longitude")
            
            transformed = {
                "external_id": event["id"],
                "source_api": "eventbrite",
                "title": event["name"]["text"],
                "description": event.get("description", {}).get("text", ""),
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "venue_name": venue.get("name", ""),
                "venue_address": venue.get("address", {}).get("localized_address_display", ""),
                "latitude": float(latitude) if latitude else None,
                "longitude": float(longitude) if longitude else None,
                "category": self._map_category(category.get("name", "")),
                "price": price,
                "currency": currency,
                "is_free": is_free,
                "external_url": event.get("url", ""),
                "image_url": event.get("logo", {}).get("url", ""),
                "api_data": event  # Store original data
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming Eventbrite event: {str(e)}")
            return None
    
    def _map_category(self, eventbrite_category: str) -> str:
        """Map Eventbrite category to our categories"""
        mapping = {
            "Music": "musica",
            "Sports & Fitness": "deportes",
            "Science & Technology": "tech",
            "Performing & Visual Arts": "cultural",
            "Food & Drink": "fiestas",
            "Business & Professional": "tech"
        }
        return mapping.get(eventbrite_category, "cultural")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
```

### **2. Ticketmaster API Service**
```python
# services/ticketmaster.py
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

from config import settings
from utils.cache import cache_result

logger = logging.getLogger(__name__)

class TicketmasterService:
    """Ticketmaster Discovery API integration"""
    
    BASE_URL = "https://app.ticketmaster.com/discovery/v2"
    
    def __init__(self):
        self.api_key = settings.TICKETMASTER_API_KEY
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    @cache_result(ttl=1800)  # 30 minutes cache
    async def search_events(
        self,
        location: str = None,
        latitude: float = None,
        longitude: float = None,
        radius: str = "25",
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 0,
        size: int = 20
    ) -> List[Dict]:
        """Search events using Ticketmaster API"""
        
        session = await self.get_session()
        
        params = {
            "apikey": self.api_key,
            "size": min(size, 200),  # Max 200 per request
            "page": page,
            "sort": "date,asc",
            "embed": "venues,attractions"
        }
        
        # Location parameters
        if latitude and longitude:
            params["geoPoint"] = f"{latitude},{longitude}"
            params["radius"] = radius
            params["unit"] = "km"
        elif location:
            params["city"] = location
        
        # Date filtering
        if start_date:
            params["startDateTime"] = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_date:
            params["endDateTime"] = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Category filtering
        if categories:
            classification_mapping = {
                "musica": "Music",
                "deportes": "Sports", 
                "cultural": "Arts & Theatre"
            }
            tm_categories = [classification_mapping.get(cat) for cat in categories if cat in classification_mapping]
            if tm_categories:
                params["classificationName"] = ",".join(tm_categories)
        
        try:
            async with session.get(f"{self.BASE_URL}/events.json", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("_embedded", {}).get("events", [])
                    
                    logger.info(f"Retrieved {len(events)} events from Ticketmaster")
                    
                    transformed_events = []
                    for event in events:
                        transformed_event = await self._transform_event(event)
                        if transformed_event:
                            transformed_events.append(transformed_event)
                    
                    return transformed_events
                    
                elif response.status == 429:  # Rate limited
                    logger.warning("Ticketmaster API rate limited")
                    await asyncio.sleep(1)  # Wait before retry
                    return []
                else:
                    logger.error(f"Ticketmaster API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Ticketmaster events: {str(e)}")
            return []
    
    async def _transform_event(self, event: Dict) -> Optional[Dict]:
        """Transform Ticketmaster event to our schema"""
        try:
            # Extract venue information
            venues = event.get("_embedded", {}).get("venues", [])
            venue = venues[0] if venues else {}
            
            # Extract pricing
            price_ranges = event.get("priceRanges", [])
            is_free = len(price_ranges) == 0
            price = 0.0
            currency = "USD"
            
            if price_ranges:
                price_range = price_ranges[0]
                price = float(price_range.get("min", 0))
                currency = price_range.get("currency", "USD")
                is_free = price == 0
            
            # Parse dates
            dates = event.get("dates", {})
            start_info = dates.get("start", {})
            start_datetime = None
            
            if start_info.get("dateTime"):
                start_datetime = datetime.fromisoformat(
                    start_info["dateTime"].replace("Z", "+00:00")
                )
            elif start_info.get("localDate"):
                # Only date available, set to 9 PM
                date_str = f"{start_info['localDate']}T21:00:00"
                start_datetime = datetime.fromisoformat(date_str)
            
            # Location data
            location_info = venue.get("location", {})
            latitude = location_info.get("latitude")
            longitude = location_info.get("longitude")
            
            # Extract category
            classifications = event.get("classifications", [])
            category = "cultural"  # Default
            if classifications:
                segment_name = classifications[0].get("segment", {}).get("name", "")
                category = self._map_category(segment_name)
            
            # Images
            images = event.get("images", [])
            image_url = ""
            if images:
                # Find the best image (16_9 ratio preferred)
                for img in images:
                    if img.get("ratio") == "16_9" and img.get("width", 0) >= 640:
                        image_url = img["url"]
                        break
                if not image_url:
                    image_url = images[0]["url"]
            
            transformed = {
                "external_id": event["id"],
                "source_api": "ticketmaster",
                "title": event["name"],
                "description": event.get("info", ""),
                "start_datetime": start_datetime,
                "end_datetime": None,  # Ticketmaster doesn't always provide end time
                "venue_name": venue.get("name", ""),
                "venue_address": f"{venue.get('address', {}).get('line1', '')} {venue.get('city', {}).get('name', '')}".strip(),
                "latitude": float(latitude) if latitude else None,
                "longitude": float(longitude) if longitude else None,
                "category": category,
                "price": price,
                "currency": currency,
                "is_free": is_free,
                "external_url": event.get("url", ""),
                "image_url": image_url,
                "api_data": event
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming Ticketmaster event: {str(e)}")
            return None
    
    def _map_category(self, segment_name: str) -> str:
        """Map Ticketmaster segment to our categories"""
        mapping = {
            "Music": "musica",
            "Sports": "deportes",
            "Arts & Theatre": "cultural",
            "Film": "cultural",
            "Miscellaneous": "hobbies"
        }
        return mapping.get(segment_name, "cultural")
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
```

---

## 📱 PWA IMPLEMENTATION DETALLADA

### **Service Worker Strategy**
```javascript
// public/sw.js - Service Worker principal
const CACHE_NAME = 'eventos-visualizer-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// Cache estratégico para diferentes tipos de contenido
const CACHE_STRATEGIES = {
  API_CACHE: 'api-cache-v1',
  IMAGE_CACHE: 'image-cache-v1',
  EVENTS_CACHE: 'events-cache-v1'
};

// Install event - cache assets estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✅ Service Worker: Caching assets');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('✅ Service Worker: Skip waiting');
        return self.skipWaiting();
      })
  );
});

// Activate event - limpiar caches viejos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              !Object.values(CACHE_STRATEGIES).includes(cacheName)) {
            console.log('🗑️ Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ Service Worker: Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - strategy por tipo de request
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // API requests - Network First con fallback a cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      networkFirstWithCache(event.request, CACHE_STRATEGIES.API_CACHE)
    );
  }
  // Images - Cache First con network fallback
  else if (event.request.destination === 'image') {
    event.respondWith(
      cacheFirstWithNetwork(event.request, CACHE_STRATEGIES.IMAGE_CACHE)
    );
  }
  // Static assets - Cache First
  else if (event.request.destination === 'script' || 
           event.request.destination === 'style') {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
  // Everything else - Network First
  else {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request);
      })
    );
  }
});

// Network First strategy con cache fallback
async function networkFirstWithCache(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      // Cache successful responses (TTL managed by headers)
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('📱 Service Worker: Serving from cache (offline)', request.url);
      return cachedResponse;
    }
    
    // No cache available, return offline fallback
    if (request.url.includes('/api/events')) {
      return new Response(
        JSON.stringify({ events: [], offline: true }),
        { 
          headers: { 'Content-Type': 'application/json' },
          status: 200 
        }
      );
    }
    
    throw error;
  }
}

// Cache First strategy con network fallback
async function cacheFirstWithNetwork(request, cacheName) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Fallback image for failed image loads
    if (request.destination === 'image') {
      return caches.match('/images/event-placeholder.jpg');
    }
    throw error;
  }
}

// Background Sync para actions offline
self.addEventListener('sync', (event) => {
  console.log('🔄 Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'save-event-offline') {
    event.waitUntil(processPendingEventSaves());
  }
  
  if (event.tag === 'sync-calendar-offline') {
    event.waitUntil(processPendingCalendarSyncs());
  }
});

// Process pending event saves cuando vuelve online
async function processPendingEventSaves() {
  try {
    const pendingSaves = await getFromIndexedDB('pendingEventSaves');
    
    for (const saveData of pendingSaves) {
      try {
        const response = await fetch('/api/events/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(saveData)
        });
        
        if (response.ok) {
          await removeFromIndexedDB('pendingEventSaves', saveData.id);
          console.log('✅ Background sync: Event saved successfully');
        }
      } catch (error) {
        console.error('❌ Background sync: Failed to save event:', error);
      }
    }
  } catch (error) {
    console.error('❌ Background sync: Error processing saves:', error);
  }
}

// Push notifications handler
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  console.log('🔔 Service Worker: Push notification received:', data);
  
  const options = {
    body: data.body,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    image: data.image,
    data: data,
    actions: [
      {
        action: 'view',
        title: 'Ver Evento',
        icon: '/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: 'Descartar'
      }
    ],
    tag: data.eventId,
    requireInteraction: true,
    vibrate: [200, 100, 200]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const data = event.notification.data;
  
  if (event.action === 'view') {
    // Abrir evento específico
    event.waitUntil(
      clients.openWindow(`/events/${data.eventId}`)
    );
  } else if (event.action === 'dismiss') {
    // Solo cerrar notification
    return;
  } else {
    // Click en notification body - abrir app
    event.waitUntil(
      clients.matchAll().then((clientList) => {
        if (clientList.length > 0) {
          // Focus existing window
          return clientList[0].focus();
        }
        // Open new window
        return clients.openWindow('/');
      })
    );
  }
});

// Utility functions for IndexedDB
async function getFromIndexedDB(storeName) {
  // IndexedDB implementation for offline storage
  return [];
}

async function removeFromIndexedDB(storeName, id) {
  // Remove item from IndexedDB
}
```

### **PWA Manifest**
```json
{
  "name": "Eventos Visualizer",
  "short_name": "Eventos",
  "description": "Descubre eventos increíbles en tu ciudad",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "theme_color": "#0da487",
  "background_color": "#ffffff",
  "lang": "es-AR",
  "scope": "/",
  "categories": ["lifestyle", "entertainment", "social"],
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png", 
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128", 
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "Eventos Cerca",
      "short_name": "Cerca",
      "description": "Ver eventos cerca de mi ubicación",
      "url": "/nearby",
      "icons": [
        {
          "src": "/icons/shortcut-nearby.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    },
    {
      "name": "Mis Eventos",
      "short_name": "Guardados",
      "description": "Ver eventos guardados",
      "url": "/saved",
      "icons": [
        {
          "src": "/icons/shortcut-saved.png",
          "sizes": "96x96", 
          "type": "image/png"
        }
      ]
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/screenshot1.png",
      "sizes": "540x720",
      "type": "image/png",
      "form_factor": "narrow"
    },
    {
      "src": "/screenshots/screenshot2.png", 
      "sizes": "720x540",
      "type": "image/png",
      "form_factor": "wide"
    }
  ]
}
```

### **Push Notifications Setup**
```typescript
// src/services/NotificationService.ts
class NotificationService {
  private vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;
  
  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('Browser no soporta notificaciones');
      return false;
    }
    
    if (Notification.permission === 'granted') {
      return true;
    }
    
    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    
    return false;
  }
  
  async subscribeToPush(): Promise<PushSubscription | null> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn('Push notifications no soportadas');
      return null;
    }
    
    try {
      const registration = await navigator.serviceWorker.ready;
      
      // Check for existing subscription
      let subscription = await registration.pushManager.getSubscription();
      
      if (!subscription) {
        // Create new subscription
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
        });
      }
      
      // Send subscription to backend
      await this.sendSubscriptionToBackend(subscription);
      
      return subscription;
    } catch (error) {
      console.error('Error suscribiéndose a push notifications:', error);
      return null;
    }
  }
  
  private async sendSubscriptionToBackend(subscription: PushSubscription): Promise<void> {
    try {
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(subscription)
      });
    } catch (error) {
      console.error('Error enviando suscripción al backend:', error);
    }
  }
  
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
  
  async scheduleEventReminder(eventId: string, reminderTime: number): Promise<void> {
    try {
      await fetch('/api/notifications/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          eventId,
          reminderTime,
          type: 'event_reminder'
        })
      });
    } catch (error) {
      console.error('Error programando recordatorio:', error);
    }
  }
}

export const notificationService = new NotificationService();
```

---

## 📋 STEP-BY-STEP IMPLEMENTATION PLAN

### **Phase 1: Backend Foundation + Database (Days 1-3)**

#### **Day 1: PostgreSQL Setup + Core Models**
```bash
# 1. Database Setup
createdb eventos_visualizer
psql eventos_visualizer -f database/init.sql

# 2. Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env
# Edit .env with database credentials and API keys
```

**Deliverables**:
- ✅ PostgreSQL database con schema completo y PostGIS
- ✅ SQLAlchemy models definidos
- ✅ Alembic migrations configuradas
- ✅ FastAPI base application running on port 8001

**Validation Commands**:
```bash
# Test database connection
python -c "from database.connection import test_connection; test_connection()"

# Test FastAPI health
curl http://172.29.228.80:8001/health

# Verify PostGIS
psql eventos_visualizer -c "SELECT PostGIS_Version();"
```

#### **Day 2: External APIs Integration**
**Focus**: Eventbrite API integration como priority #1

**Tasks**:
1. **Eventbrite Service Implementation**
   - Create `services/eventbrite.py` 
   - Implement search_events method
   - Add event transformation logic
   - Add caching layer con Redis

2. **API Endpoints Creation**
   ```python
   # api/external_apis.py
   @router.get("/events/search")
   async def search_events(
       location: str = Query(None),
       latitude: float = Query(None),
       longitude: float = Query(None),
       radius: int = Query(25),
       categories: List[str] = Query([])
   ):
   ```

3. **Background Sync Setup**
   - Celery task para periodic sync
   - Event deduplication logic
   - Error handling y retry mechanisms

**Deliverables**:
- ✅ Eventbrite API integration functional
- ✅ `/api/external/events/search` endpoint working
- ✅ Background task para auto-sync events
- ✅ Basic event CRUD endpoints

**Validation**:
```bash
# Test Eventbrite integration
curl "http://172.29.228.80:8001/api/external/events/search?location=Buenos%20Aires&radius=25"

# Should return real events from Eventbrite API
```

#### **Day 3: User Management + Authentication**
**Focus**: JWT authentication + Google OAuth

**Tasks**:
1. **User Authentication**
   - JWT token generation/validation
   - Google OAuth integration setup
   - Protected routes middleware

2. **User Event Management**  
   - Save/unsave events functionality
   - User preferences storage
   - Event status tracking

**Deliverables**:
- ✅ User authentication system working
- ✅ Google OAuth integration
- ✅ User event management endpoints
- ✅ Protected routes functioning

### **Phase 2: Frontend Base + Template Conversion (Days 4-6)**

#### **Day 4: React + Vite Setup + Template Analysis**
```bash
# Frontend setup
npm create vite@latest frontend --template react-ts
cd frontend
npm install
npm install react-router-dom zustand axios tailwindcss
```

**Tasks**:
1. **Template Conversion Planning**
   - Analyze `docs/templates/SAMPLE-APW.htm` structure
   - Map Bootstrap classes to Tailwind CSS equivalents  
   - Create component hierarchy plan

2. **Core Layout Components**
   ```tsx
   // src/components/Layout/Header.tsx
   // src/components/Layout/Navigation.tsx
   // src/components/Layout/Footer.tsx
   ```

**Deliverables**:
- ✅ Vite React app running en puerto 5174
- ✅ Template structure analysis completa
- ✅ Basic layout components creados
- ✅ Routing structure implementado

#### **Day 5: EventCard Component (Template-Based)**
**CRÍTICO**: Este componente debe ser visualmente idéntico al template

**Tasks**:
1. **EventCard Implementation**
   ```tsx
   // src/components/EventCard/EventCard.tsx
   // MUST replicate exact structure from SAMPLE-APW.htm
   // Product card → Event card conversion
   ```

2. **Template CSS Integration**
   - Import Bootstrap CSS desde template
   - Add custom CSS variables del template
   - Maintain exact styling y animations

3. **EventGrid Layout**
   ```tsx
   // src/components/EventGrid/EventGrid.tsx
   // Exact Bootstrap grid system from template
   ```

**Deliverables**:
- ✅ EventCard visualmente idéntico al template
- ✅ EventGrid con responsive behavior exacto
- ✅ CSS animations y hover effects working
- ✅ Image loading con blur-up effect

**Critical Validation**:
```bash
# Side-by-side comparison
# Template vs React component must be visually identical
```

#### **Day 6: State Management + API Integration**
**Tasks**:
1. **Zustand Store Setup**
   ```typescript
   // src/stores/eventStore.ts
   // src/stores/userStore.ts
   // src/stores/notificationStore.ts
   ```

2. **API Service Layer**
   ```typescript
   // src/services/api.ts
   // src/services/eventService.ts
   // src/services/authService.ts
   ```

3. **Frontend-Backend Integration**
   - Connect EventCard to real API data
   - Handle loading states y error states
   - Implement pagination

**Deliverables**:
- ✅ Frontend consuming backend APIs
- ✅ Real event data displaying en EventCards
- ✅ Loading y error states implemented
- ✅ Pagination working correctly

### **Phase 3: Multi-API Integration + Geolocation (Days 7-9)**

#### **Day 7: Ticketmaster + Meetup Integration**
**Tasks**:
1. **Ticketmaster Service**
   - Implement `services/ticketmaster.py`
   - Add rate limiting y error handling
   - Event data transformation

2. **Meetup Service**
   - OAuth setup for Meetup API
   - Event search implementation
   - Free events focus

3. **Event Aggregation Service**
   ```python
   # services/event_aggregation.py
   class EventAggregationService:
       async def search_all_sources(self, **params):
           # Combine results from all APIs
           # Remove duplicates
           # Rank by relevance
   ```

**Deliverables**:
- ✅ 3+ APIs integrated (Eventbrite, Ticketmaster, Meetup)
- ✅ Event deduplication working
- ✅ Combined search results
- ✅ API failure graceful handling

#### **Day 8: Geolocation + Maps Integration**
**Tasks**:
1. **Geolocation Service**
   ```typescript
   // src/services/geolocationService.ts
   class GeolocationService {
     async getCurrentPosition(): Promise<Position>
     async geocodeAddress(address: string): Promise<LatLng>
     calculateDistance(pos1: LatLng, pos2: LatLng): number
   }
   ```

2. **Google Maps Integration**
   - Map component con event markers
   - Clustering para multiple events
   - Custom markers por category
   - Info windows con event preview

3. **Location-Based Search**
   - GPS detection con fallback a IP
   - Radius selection (5km, 10km, 25km, 50km)
   - "Eventos cerca" functionality

**Deliverables**:
- ✅ Geolocation detection working
- ✅ Google Maps con event markers
- ✅ Distance calculation accurate
- ✅ Location-based event filtering

#### **Day 9: Search + Filtering System**
**Tasks**:
1. **Advanced Search Component**
   ```tsx
   // src/components/Search/SearchFilters.tsx
   // Category filters
   // Date range picker  
   // Price range slider
   // Distance radius selector
   ```

2. **Search Backend Optimization**
   - PostGIS geospatial queries
   - Full-text search implementation
   - Index optimization
   - Search result caching

**Deliverables**:
- ✅ Advanced search filters working
- ✅ Search results bajo 500ms
- ✅ Filter combinations functional
- ✅ Search optimization implemented

### **Phase 4: PWA + Calendar Integration (Days 10-12)**

#### **Day 10: Service Workers + Offline Support**
**Tasks**:
1. **Service Worker Implementation**
   - Cache strategy setup
   - Offline fallbacks  
   - Background sync setup

2. **PWA Manifest**
   - App installable
   - Custom icons y screenshots
   - Shortcuts configuration

3. **Offline Functionality**
   - Saved events available offline
   - Offline action queuing
   - Network status detection

**Deliverables**:
- ✅ PWA installable en mobile devices
- ✅ Offline support functional
- ✅ Background sync working
- ✅ Install prompt implemented

#### **Day 11: Google Calendar Integration**
**Tasks**:
1. **Google Calendar API Setup**
   - OAuth 2.0 configuration
   - Calendar permissions setup
   - API client integration

2. **Bidirectional Sync Service**
   ```python
   # services/google_calendar.py
   class GoogleCalendarService:
       async def create_event(self, event_data: dict) -> str
       async def update_event(self, calendar_event_id: str, event_data: dict)
       async def delete_event(self, calendar_event_id: str)
       async def sync_user_events(self, user_id: str)
   ```

3. **Calendar UI Components**
   - Calendar sync toggle
   - Sync status indicators
   - Conflict resolution UI

**Deliverables**:
- ✅ Google Calendar bidirectional sync
- ✅ Event creation en calendar automatic
- ✅ Sync status visible to user
- ✅ Timezone handling correct

#### **Day 12: Push Notifications Setup**
**Tasks**:
1. **Web Push API Integration**
   - VAPID keys setup
   - Subscription management
   - Notification scheduling

2. **Notification Types Implementation**
   - 24h event reminder
   - 1h event reminder  
   - New events in favorite categories
   - Event updates/cancellations

3. **Backend Notification Service**
   ```python
   # services/notification_service.py
   class NotificationService:
       async def schedule_event_reminder(self, user_id, event_id, reminder_time)
       async def send_push_notification(self, subscription, payload)
       async def process_notification_queue()
   ```

**Deliverables**:
- ✅ Push notifications working
- ✅ Event reminders delivered correctly
- ✅ Notification preferences configurable
- ✅ Background notification processing

### **Phase 5: Performance + Polish + Testing (Days 13-15)**

#### **Day 13: Performance Optimization**
**Tasks**:
1. **Frontend Optimization**
   - Code splitting implementation
   - Image lazy loading optimization
   - Bundle size analysis y reduction
   - Core Web Vitals optimization

2. **Backend Optimization**
   - Database query optimization
   - API response caching improvement
   - Connection pooling optimization
   - Background task performance

3. **Lighthouse Optimization**
   - Performance score >85
   - Accessibility compliance
   - SEO optimization
   - PWA score >90

**Deliverables**:
- ✅ Lighthouse Performance >85
- ✅ Initial load time <3s
- ✅ Navigation time <1s
- ✅ Bundle size optimized

#### **Day 14: Testing Implementation**
**Tasks**:
1. **Frontend Testing**
   ```typescript
   // tests/components/EventCard.test.tsx
   // tests/services/eventService.test.ts
   // tests/stores/eventStore.test.ts
   ```

2. **Backend Testing**
   ```python
   # tests/test_eventbrite_service.py
   # tests/test_event_crud.py
   # tests/test_geolocation.py
   ```

3. **Integration Testing**
   - API endpoint testing
   - External API integration testing
   - Database operation testing

**Deliverables**:
- ✅ Unit tests para core components
- ✅ Integration tests para APIs
- ✅ Test coverage >80%
- ✅ E2E testing key user flows

#### **Day 15: Final Polish + Documentation**
**Tasks**:
1. **UI/UX Polish**
   - Error message improvement
   - Loading state enhancement
   - Accessibility improvements
   - Mobile optimization final tweaks

2. **Documentation Creation**
   - API documentation update
   - Deployment guide creation
   - User manual creation

3. **Final Validation**
   - All success criteria verification
   - Performance benchmarking
   - Security audit
   - Multi-device testing

**Deliverables**:
- ✅ All success criteria met
- ✅ Documentation complete
- ✅ Ready for deployment
- ✅ Security validated

---

## ⚙️ CONFIGURATION & ENVIRONMENT SETUP

### **Environment Variables Required**
```bash
# .env file template
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/eventos_visualizer
REDIS_URL=redis://localhost:6379

# External API Keys
EVENTBRITE_API_KEY=your_eventbrite_private_token
TICKETMASTER_API_KEY=your_ticketmaster_consumer_key
MEETUP_CLIENT_ID=your_meetup_client_id
MEETUP_CLIENT_SECRET=your_meetup_client_secret

# Google APIs
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_CALENDAR_API_KEY=your_google_calendar_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_javascript_api_key

# Push Notifications (VAPID)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_SUBJECT=mailto:your-email@domain.com

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application Settings
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://172.29.228.80:5174,http://localhost:5174

# Network Configuration (WSL)
WSL_HOST_IP=172.29.228.80
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

### **Docker Setup (Optional)**
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 5174
CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      POSTGRES_DB: eventos_visualizer
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/eventos_visualizer
      REDIS_URL: redis://redis:6379
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "5174:5174"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### **Database Migrations Setup**
```python
# database/migrations/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from models import Base  # Import all models

# Enable PostGIS in migration
def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enable PostGIS extension
        connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()
```

### **Performance Monitoring Setup**
```python
# utils/monitoring.py
import time
import logging
from functools import wraps
from prometheus_client import Counter, Histogram

# Metrics
REQUEST_COUNT = Counter('eventos_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('eventos_request_duration_seconds', 'Request duration')

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
            
            if duration > 1.0:  # Log slow operations
                logging.warning(f"Slow operation {func.__name__}: {duration:.2f}s")
    
    return wrapper
```

---

## ✅ TESTING & VALIDATION STRATEGY

### **Component Testing Strategy**
```typescript
// tests/components/EventCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { EventCard } from '../src/components/EventCard/EventCard';
import { mockEvent } from './fixtures/events';

describe('EventCard Component', () => {
  it('renders event information correctly', () => {
    render(<EventCard event={mockEvent} />);
    
    expect(screen.getByText(mockEvent.title)).toBeInTheDocument();
    expect(screen.getByText(mockEvent.venue_name)).toBeInTheDocument();
    expect(screen.getByAltText(mockEvent.title)).toBeInTheDocument();
  });
  
  it('displays price correctly for paid events', () => {
    const paidEvent = { ...mockEvent, is_free: false, price: 25.99 };
    render(<EventCard event={paidEvent} />);
    
    expect(screen.getByText('$25.99')).toBeInTheDocument();
  });
  
  it('displays "GRATIS" for free events', () => {
    const freeEvent = { ...mockEvent, is_free: true };
    render(<EventCard event={freeEvent} />);
    
    expect(screen.getByText('GRATIS')).toBeInTheDocument();
  });
  
  it('handles save event click', () => {
    const onSave = jest.fn();
    render(<EventCard event={mockEvent} onSave={onSave} />);
    
    fireEvent.click(screen.getByRole('button', { name: /heart/i }));
    expect(onSave).toHaveBeenCalledWith(mockEvent.id);
  });
  
  it('matches template styling exactly', () => {
    const { container } = render(<EventCard event={mockEvent} />);
    const cardElement = container.querySelector('.event-card');
    
    // Verify template classes are preserved
    expect(cardElement).toHaveClass('product-box');
    expect(cardElement).toHaveClass('product-box-bg');
    expect(cardElement).toHaveClass('wow');
    expect(cardElement).toHaveClass('fadeInUp');
  });
});
```

### **API Integration Testing**
```python
# tests/test_eventbrite_integration.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from services.eventbrite import EventbriteService

class TestEventbriteIntegration:
    @pytest.fixture
    def eventbrite_service(self):
        return EventbriteService()
    
    @pytest.mark.asyncio
    async def test_search_events_success(self, eventbrite_service):
        """Test successful event search"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "events": [
                    {
                        "id": "123456789",
                        "name": {"text": "Test Event"},
                        "start": {"utc": "2024-12-25T20:00:00Z"},
                        "venue": {
                            "name": "Test Venue",
                            "address": {
                                "latitude": "-34.6037",
                                "longitude": "-58.3816"
                            }
                        }
                    }
                ]
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            events = await eventbrite_service.search_events(
                location="Buenos Aires",
                radius="25km"
            )
            
            assert len(events) == 1
            assert events[0]["title"] == "Test Event"
            assert events[0]["source_api"] == "eventbrite"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, eventbrite_service):
        """Test handling of rate limits"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429  # Rate limited
            mock_get.return_value.__aenter__.return_value = mock_response
            
            events = await eventbrite_service.search_events(location="Test")
            assert events == []
    
    @pytest.mark.asyncio 
    async def test_network_error_handling(self, eventbrite_service):
        """Test network error handling"""
        with patch('aiohttp.ClientSession.get', side_effect=Exception("Network error")):
            events = await eventbrite_service.search_events(location="Test")
            assert events == []
```

### **PWA Functionality Validation**
```javascript
// tests/pwa/service-worker.test.js
describe('Service Worker Functionality', () => {
  beforeAll(async () => {
    // Register service worker for testing
    await navigator.serviceWorker.register('/sw.js');
  });
  
  it('caches static assets on install', async () => {
    const cache = await caches.open('eventos-visualizer-v1');
    const cachedRequests = await cache.keys();
    
    expect(cachedRequests.length).toBeGreaterThan(0);
    expect(cachedRequests.some(req => req.url.includes('bundle.js'))).toBe(true);
  });
  
  it('serves cached content when offline', async () => {
    // Simulate offline mode
    spyOn(navigator, 'onLine').and.returnValue(false);
    
    const response = await fetch('/');
    expect(response.ok).toBe(true);
  });
  
  it('handles push notifications correctly', async () => {
    const registration = await navigator.serviceWorker.ready;
    
    // Mock push event
    const pushEvent = new MessageEvent('push', {
      data: {
        json: () => ({
          title: 'Test Event Reminder',
          body: 'Your event starts in 1 hour!',
          eventId: '123'
        })
      }
    });
    
    // Simulate push notification
    registration.dispatchEvent(pushEvent);
    
    // Verify notification was shown
    // Note: This requires additional setup for testing notifications
  });
});
```

### **Performance Benchmarks**
```typescript
// tests/performance/lighthouse.config.js
module.exports = {
  ci: {
    collect: {
      url: ['http://172.29.228.80:5174'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.85 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'categories:pwa': ['error', { minScore: 0.9 }],
      },
    },
  },
};
```

### **Final Validation Checklist**

#### **Functional Requirements Validation**
- [ ] ✅ **Multi-API Integration**: Eventbrite, Ticketmaster, Meetup APIs working
- [ ] ✅ **Geolocation Accuracy**: <100m precision, múltiples radius options
- [ ] ✅ **Calendar Sync**: Bidirectional Google Calendar integration
- [ ] ✅ **Push Notifications**: 24h/1h reminders delivered correctly  
- [ ] ✅ **PWA Installation**: Installable en Android y iOS
- [ ] ✅ **Offline Support**: Saved events accessible sin internet
- [ ] ✅ **Search Performance**: Results en <500ms
- [ ] ✅ **Mobile Navigation**: Intuitive y responsive

#### **Technical Requirements Validation**  
- [ ] ✅ **Backend Stability**: Puerto 8001, no crashes, proper error handling
- [ ] ✅ **Frontend Optimization**: Puerto 5174, <3s load time
- [ ] ✅ **Database Performance**: Optimized queries, proper indexing
- [ ] ✅ **Cache Strategy**: Redis working, API responses cached
- [ ] ✅ **Service Workers**: Caching y offline functionality
- [ ] ✅ **Error Handling**: Graceful API failure handling
- [ ] ✅ **Type Safety**: TypeScript strict mode, no type errors

#### **Design Requirements Validation (CRITICAL)**
- [ ] ✅ **Template Fidelity**: EventCard visualmente idéntico a template HTML
- [ ] ✅ **Responsive Design**: Mobile-first, all breakpoints working
- [ ] ✅ **Touch Targets**: Minimum 44px, accessible on mobile
- [ ] ✅ **Category Colors**: Consistent color-coding system
- [ ] ✅ **Loading States**: User-friendly loading y error states
- [ ] ✅ **Accessibility**: WCAG 2.1 AA compliance

#### **Performance Requirements Validation**
- [ ] ✅ **Initial Load**: <3s en mobile devices
- [ ] ✅ **Navigation Speed**: <1s between screens  
- [ ] ✅ **API Caching**: 30min TTL for external API responses
- [ ] ✅ **Image Optimization**: Lazy loading, progressive enhancement
- [ ] ✅ **Bundle Size**: <2MB total bundle size
- [ ] ✅ **Core Web Vitals**: LCP <2.5s, FID <100ms, CLS <0.1
- [ ] ✅ **Lighthouse Score**: Performance >85, PWA >90

---

## 🎯 SUCCESS METRICS & KPIs

### **Technical KPIs**
- **Uptime**: >99.5% backend availability
- **Response Time**: API responses <500ms 95th percentile
- **Error Rate**: <1% API error rate
- **PWA Score**: Lighthouse PWA score >90
- **Bundle Size**: Total JS bundle <2MB
- **Cache Hit Ratio**: >85% for API responses

### **User Experience KPIs**
- **Load Time**: Initial page load <3s on 3G networks
- **Engagement**: >60% user interaction with EventCard
- **Install Rate**: >10% PWA installation rate
- **Notification Open Rate**: >25% push notification clicks
- **Search Success**: >90% searches return relevant results

### **Business KPIs**
- **Event Coverage**: >1000 events agregados from external APIs
- **Geographic Coverage**: Events in >50 cities covered
- **API Integration**: 3+ external APIs functioning simultaneously
- **Data Quality**: <5% duplicate events after deduplication

---

## 🔐 SECURITY & PRIVACY CONSIDERATIONS

### **Security Measures**
```python
# Security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["eventos-visualizer.com"])
app.add_middleware(HTTPSRedirectMiddleware)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# API endpoints with rate limiting
@app.get("/api/events/search")
@limiter.limit("100/minute")
async def search_events(request: Request, ...):
    pass
```

### **Privacy Protection**
- **Minimal Data Collection**: Solo datos necesarios para funcionalidad
- **Location Privacy**: Geolocation temporal, user consent explicit
- **API Key Security**: Keys never exposed al frontend
- **User Data Encryption**: Sensitive data encrypted at rest
- **GDPR Compliance**: Data deletion y export capabilities

### **Authentication Security**
- **JWT Token Security**: Short-lived access tokens (24h expiration)
- **Refresh Token Rotation**: Secure token renewal mechanism
- **OAuth 2.0**: Google authentication implementation
- **CORS Policy**: Restrictive CORS configuration
- **CSRF Protection**: Built-in FastAPI CSRF protection

---

## 🚀 DEPLOYMENT STRATEGY

### **Development Environment**
- **Local WSL**: IP 172.29.228.80, ports 8001/5174
- **Database**: Local PostgreSQL con PostGIS
- **Cache**: Local Redis instance
- **APIs**: Development API keys con rate limits

### **Production Environment**
- **Backend**: Railway/Heroku deployment
- **Frontend**: Vercel deployment con CDN
- **Database**: Managed PostgreSQL (Railway/Neon)
- **Cache**: Redis Cloud/Upstash
- **Monitoring**: Sentry error tracking, DataDog metrics

### **CI/CD Pipeline**
```yaml
# .github/workflows/deploy.yml
name: Deploy Eventos Visualizer

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: pytest
      - name: Run Frontend Tests  
        run: npm test
      - name: Lighthouse Performance Test
        run: npm run lighthouse-ci
  
  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        run: railway deploy
  
  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: vercel deploy --prod
```

---

## 🎉 FINAL CONFIDENCE ASSESSMENT: 9/10

### **Confidence Justification**

#### **✅ Strengths (9/10 Confidence)**
1. **Template-Based Design**: Clear visual reference elimina design uncertainty
2. **Proven Tech Stack**: FastAPI + React + PostgreSQL - battle-tested combination  
3. **Real APIs Integration**: Eventbrite, Ticketmaster, Meetup - documented APIs
4. **Clear Implementation Plan**: Step-by-step plan with specific deliverables
5. **Performance Focus**: Measurable performance criteria y optimization strategies
6. **PWA Best Practices**: Modern PWA implementation patterns
7. **Database Design**: Optimized PostgreSQL schema con PostGIS

#### **⚠️ Risk Mitigation Strategies**
1. **API Rate Limits**: Caching y fallback strategies implemented
2. **External Dependencies**: Graceful degradation when APIs fail
3. **Performance Constraints**: Lazy loading y code splitting
4. **Mobile Compatibility**: Template-based design ensures consistency
5. **Offline Functionality**: Service Workers y IndexedDB backup

#### **🔗 Success Probability: 90%**
Based on:
- **Clear Requirements**: Well-defined scope y success criteria
- **Template Reference**: Visual design uncertainty eliminated  
- **Technical Feasibility**: All components technically proven
- **Implementation Plan**: Detailed, realistic timeline
- **Performance Targets**: Achievable benchmarks

### **Delivery Timeline: 15 Days**
- **Phase 1**: Backend foundation (3 days)
- **Phase 2**: Frontend + template conversion (3 days) 
- **Phase 3**: Multi-API integration (3 days)
- **Phase 4**: PWA + calendar features (3 days)
- **Phase 5**: Performance + testing (3 days)

---

**Este PRP proporciona una roadmap completa para implementar un sistema de eventos mobile-first con PWA capabilities, siguiendo exactamente las reglas y templates proporcionados en CLAUDE.md y docs/templates/. La confidence de 9/10 se basa en la especificidad técnica, templates visuales claros, y plan de implementación detallado.**

**🎯 Ready for immediate implementation with zero ambiguity.**