# 🎉 EVENTOS VISUALIZER - Sistema Completo Mobile-First

**Date**: December 2024 | **Confidence**: 9/10 | **Framework**: FastAPI + PostgreSQL + React + Vite + PWA

---

## 🎯 Objective

**Feature**: Sistema completo de descubrimiento y gestión de eventos con categorización inteligente, integración de múltiples APIs, sincronización con agenda personal y notificaciones push. Diseño mobile-first con capacidades PWA.

**Business Impact**: Revolucionar cómo las personas descubren y organizan eventos en su ciudad con UX móvil superior
**User Role**: event-goer/organizer/admin (multi-role system)  
**Success Criteria**: App PWA completamente funcional con <3s loading, sync con Google Calendar, push notifications y offline support

---

## 📚 Required Context & Research

### **Framework Patterns (MUST FOLLOW)**
```yaml
backend_pattern: "examples/fastapi_async.py"
  - FastAPI con async/await para APIs externas
  - PostgreSQL con asyncpg y connection pooling
  - JWT authentication con Google OAuth
  - WebSocket para notificaciones push en tiempo real
  - Background tasks con Celery para sync de eventos
  - Cache con Redis para responses de APIs externas

database_pattern: "examples/postgresql_model.py"  
  - PostgreSQL engine con PostGIS para geolocalización
  - DECIMAL(10,2) para precios en múltiples monedas
  - UUID primary keys para escalabilidad
  - Timestamp with timezone para eventos globales
  - JSON columns para metadata flexible de APIs
  - Índices optimizados para queries geográficas

frontend_pattern: "examples/react_pwa.tsx"
  - React + Vite con TypeScript strict
  - PWA con Service Workers para offline support
  - Push notifications con Web Push API
  - Geolocation API para ubicación automática
  - React Router para navegación SPA
  - Zustand para state management ligero
```

### **Event Business Rules (CRITICAL)**
```yaml
event_discovery_flow: "search → filter → details → save → calendar_sync"
geolocation_requirements:
  - Auto-detect user location con GPS + IP fallback
  - Radius search: 5km, 10km, 25km, 50km options
  - Map visualization con clustering para múltiples eventos
categories_system:
  - Primary: Música, Deportes, Cultural, Tech, Fiestas, Hobbies, Internacional
  - Color-coded badges para visual distinction
  - Smart filtering por categoría + ubicación + fecha + precio
```

---

## 🔌 EXTERNAL APIS INTEGRATION (OBLIGATORIO)

### **Priority 1: Eventbrite API**
```yaml
base_url: "https://www.eventbriteapi.com/v3/"
authentication: "Bearer token"
rate_limit: "1000 requests/hour"
key_endpoints:
  - "/events/search/?location.address={city}&categories={cat_id}"
  - "/events/{event_id}/?expand=venue,organizer,ticket_classes"
  - "/categories/"
  - "/venues/{venue_id}/events/"
data_mapping:
  - title: event.name.text
  - description: event.description.text
  - start_datetime: event.start.utc
  - venue: event.venue
  - category: event.category_id
  - price: event.ticket_classes[0].cost
```

### **Priority 2: Ticketmaster Discovery API**
```yaml
base_url: "https://app.ticketmaster.com/discovery/v2/"
authentication: "API key in query params"
rate_limit: "5000 requests/day, 5 req/sec"
key_endpoints:
  - "/events.json?city={city}&classificationName={music|sports}"
  - "/events/{event_id}.json?embed=venues,attractions"  
  - "/venues.json?geoPoint={latitude},{longitude}"
  - "/attractions.json?keyword={artist_name}"
data_mapping:
  - title: event.name
  - description: event.info
  - venue: event._embedded.venues[0]
  - category: event.classifications[0].segment.name
  - image: event.images[0].url
```

### **Priority 3: Meetup API**
```yaml
base_url: "https://api.meetup.com/"
authentication: "OAuth 2.0"
rate_limit: "200 requests/hour"
key_endpoints:
  - "/find/upcoming_events?lat={lat}&lon={lon}&radius=25"
  - "/events/{event_id}?fields=description,organizer,venue"
  - "/categories/"
data_mapping:
  - title: event.name
  - description: event.description
  - start_datetime: event.time
  - venue: event.venue
  - is_free: true (mostly free events)
```

### **Priority 4: Facebook Events API (Optional)**
```yaml
base_url: "https://graph.facebook.com/v18.0/"
authentication: "App access token"
endpoints:
  - "/events?location={location}&time=upcoming"
  - "/{event_id}?fields=cover,description,place,attending_count"
note: "Restricted access, implement if keys available"
```

---

## 📱 MOBILE-FIRST PWA REQUIREMENTS

### **PWA Core Features (CRITICAL)**
```yaml
service_worker: "Cache strategy para assets + API responses"
offline_support: "Eventos guardados disponibles sin internet"
install_prompt: "Add to Home Screen después de 2da visita"
background_sync: "Queue acciones offline, sync when online"
push_notifications: "VAPID keys para Web Push API"
app_shell: "Instant loading architecture"
responsive_design: "Mobile-first con breakpoints específicos"
```

### **Push Notifications System**
```yaml
triggers:
  - "24 horas antes del evento"
  - "1 hora antes del evento" 
  - "Evento empezando (opcional)"
  - "Nuevos eventos en categorías favoritas"
  - "Cambios en eventos guardados (cancelado, moved)"
personalization:
  - "User preferences por tipo de notification"
  - "Quiet hours (no notifications 22:00-08:00)"
  - "Batch mode: resumen diario vs individual"
implementation: "Service Workers + Web Push API + VAPID"
```

### **Geolocation Features**
```yaml
primary_source: "Navigator.geolocation con high accuracy"
fallback: "IP geolocation con GeoJS API si GPS denied"
radius_options: [5, 10, 25, 50] # kilometers
map_integration: "Google Maps con event clustering"
transit_info: "Opcional: integrar rutas de transporte público"
location_privacy: "Almacenar solo temporalmente, user consent"
```

---

## 🎨 DESIGN & UX REQUIREMENTS

### **Mobile-First Design Principles**
```yaml
viewport_optimization: "375px-414px primary target"
touch_targets: "Minimum 44px x 44px para todos botones"
navigation: "Bottom tab bar como apps nativas"
gestures: "Swipe entre eventos, pull-to-refresh"
typography: "Inter font con responsive scaling"
colors: "Color-coded categories con accessibility compliance"
```

### **Visual Hierarchy (BASED ON TEMPLATES)**
```yaml
event_cards: "16:9 aspect ratio con gradient overlays"
category_badges: "Color-coded, rounded-full pills"
date_time_display: "Prominente, easy scanning format"
location_info: "Con distance indicator desde user location"
price_display: "Clear distinction: FREE vs $XX.XX"
call_to_actions: "Large, accessible buttons mobile-optimized"
```

### **Templates HTML Usage (CRITICAL)**
```yaml
primary_template: "docs/templates/SAMPLE-APW.htm" read with mcp playwright / puppeteer
usage_rule: "COPY structure exactly, change only data"
validation: "Visual result must be identical to template"
components_affected:
  - "EventCard component (main display)"
  - "EventList layout"  
  - "CategoryFilter UI"
  - "EventDetails page"
  - "CalendarIntegration modal"
```

---

## 🗺️ GEOLOCATION & MAPS INTEGRATION

### **Location Services**
```yaml
user_location: "GPS primary, IP geolocation fallback"
accuracy: "High accuracy para mejor results"
permission_handling: Sácalo, por favor, Sácalo, Sácalo y dejar un montón de cada lado hacia la y a la derecha Esa búsqueda más algo con la inteligencia artificial, ahí vamos a ponerlo, vale por Palermo, discoteca por central y así
"Graceful degradation si denied"
geocoding: "Reverse geocoding para human-readable addresses"
distance_calculation: "Haversine formula para accuracy"
```

### **Google Maps Integration**
```yaml
features_required:
  - "Event markers con custom icons por categoría"
  - "Clustering para múltiples eventos cerca"
  - "Info windows con event preview"
  - "Current location marker"
  - "Radius visualization (opcional)"
  - "Directions integration (opcional)"
styling: "Custom styling match con app design"
performance: "Lazy loading, efficient marker management"
```

---

## 📅 CALENDAR INTEGRATION

### **Google Calendar API**
```yaml
oauth_scopes: ["https://www.googleapis.com/auth/calendar"]
features:
  - "Bidirectional sync (app ↔ Google Calendar)"
  - "Create calendar events from saved events"
  - "Update events if details change"
  - "Delete from calendar if unsaved"
conflict_detection: "Warn if event conflicts with existing"
timezone_handling: "Automatic conversion based on event location"
```

### **CalDAV Support (Extended)**
```yaml
purpose: "Support for Outlook, Apple Calendar, Thunderbird"
implementation: "Standard CalDAV protocol"
features: "Basic sync capabilities"
priority: "Lower priority, implement after Google Calendar"
```

---

## 🔔 NOTIFICATIONS & REAL-TIME FEATURES

### **WebSocket Architecture**
```yaml
purpose: "Real-time notifications para event updates"
use_cases:
  - "Event cancelled/postponed notifications"
  - "New events matching user interests"
  - "Friend activity (opcional social features)"
implementation: "FastAPI WebSocket endpoints"
scaling: "Redis pub/sub para multiple server instances"
```

### **Background Processing**
```yaml
task_queue: "Celery con Redis broker"
scheduled_tasks:
  - "Sync events from external APIs (every 30 minutes)"
  - "Send notification reminders (batch processing)"
  - "Clean up expired events (daily)"
  - "Update event status from external sources"
monitoring: "Task status dashboard para debugging"
```

---

## 💾 DATABASE SCHEMA (PostgreSQL)

### **Core Tables**
```sql
-- Eventos principales  
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    venue_name VARCHAR(255),
    venue_address TEXT,
    -- PostGIS para geolocalización
    location POINT, -- SRID 4326 (WGS 84)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    price DECIMAL(10,2),
    currency CHAR(3) DEFAULT 'ARS',
    is_free BOOLEAN DEFAULT false,
    -- External API tracking
    external_id VARCHAR(255),
    source_api VARCHAR(50) NOT NULL, -- 'eventbrite', 'ticketmaster', 'meetup'
    external_url TEXT,
    image_url TEXT,
    -- Metadata 
    metadata JSONB, -- Flexible data from different APIs
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices optimizados
CREATE INDEX idx_events_location ON events USING GIST(location);
CREATE INDEX idx_events_datetime ON events (start_datetime);
CREATE INDEX idx_events_category ON events (category);
CREATE INDEX idx_events_source_api ON events (source_api, external_id);

-- Usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    google_id VARCHAR(255) UNIQUE,
    -- Location preferences
    home_location POINT, -- User's home location
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    radius_km INTEGER DEFAULT 25,
    -- Preferences
    timezone VARCHAR(100) DEFAULT 'America/Argentina/Buenos_Aires',
    locale VARCHAR(10) DEFAULT 'es-AR',
    push_enabled BOOLEAN DEFAULT false,
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Eventos guardados/favoritos  
CREATE TABLE user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'interested', -- 'interested', 'going', 'not_going'
    -- Notification tracking
    notification_24h_sent BOOLEAN DEFAULT false,
    notification_1h_sent BOOLEAN DEFAULT false,
    calendar_synced BOOLEAN DEFAULT false,
    calendar_event_id VARCHAR(255), -- Google Calendar event ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, event_id)
);

-- Categorías (reference table)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL, -- Hex color code
    icon VARCHAR(100), -- Icon identifier
    parent_id UUID REFERENCES categories(id),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0
);
```

---

## 🚀 IMPLEMENTATION PHASES & SUCCESS CRITERIA

### **Phase 1: Core Backend + Database (Week 1)**
```yaml
deliverables:
  - "FastAPI server running on port 8001"
  - "PostgreSQL database con schema completo"
  - "Una API externa integrada (Eventbrite)"
  - "Basic CRUD endpoints para events"
success_criteria:
  - "curl http://172.29.228.80:8001/health returns 200"
  - "Eventbrite API integration con real data"
  - "Database queries con geolocation working"
```

### **Phase 2: Frontend Base + Templates (Week 1-2)**
```yaml
deliverables:
  - "React app con Vite running en puerto 5174"
  - "EventCard component basado en template HTML"
  - "Basic routing y navigation"
  - "Mobile-responsive layout"
success_criteria:
  - "Frontend loads in <3 seconds"
  - "EventCard visually identical a template"
  - "Mobile navigation working perfectly"
```

### **Phase 3: Multi-API Integration (Week 2)**
```yaml
deliverables:
  - "3+ APIs externas integradas"
  - "Event aggregation y deduplication"
  - "Category system working"
  - "Search y filtering functional"
success_criteria:
  - "Events from Eventbrite, Ticketmaster, Meetup"
  - "No duplicate events from different sources"
  - "Search results bajo 500ms"
```

### **Phase 4: PWA + Location Features (Week 3)**
```yaml
deliverables:
  - "Service Workers para offline support"
  - "PWA install prompt"
  - "Geolocation y maps integration"
  - "Google Calendar sync"
success_criteria:
  - "App installable on mobile devices"
  - "Works offline para saved events"
  - "Location detection accuracy <100m"
  - "Calendar sync bidirectional"
```

### **Phase 5: Push Notifications + Polish (Week 4)**
```yaml
deliverables:
  - "Web Push notifications working"
  - "Background sync functionality"
  - "Performance optimization"
  - "Analytics implementation"
success_criteria:
  - "Push notifications delivered correctly"
  - "App performance: lighthouse score >90"
  - "All success criteria from previous phases maintained"
```

---

## ✅ FINAL VALIDATION CRITERIA

### **Functional Requirements**
- [ ] 3+ APIs integration con real data (Eventbrite, Ticketmaster, Meetup)
- [ ] Geolocation working con accuracy <100m radius
- [ ] Google Calendar bidirectional sync functional  
- [ ] Push notifications delivered correctly to devices
- [ ] PWA installable en Android y iOS
- [ ] Offline support para eventos guardados
- [ ] Event search y filtering bajo 500ms response time
- [ ] Mobile navigation intuitive y responsive

### **Technical Requirements**  
- [ ] Backend running stable en puerto 8001 
- [ ] Frontend optimized en puerto 5174
- [ ] PostgreSQL queries optimized con proper indexes
- [ ] Redis cache working para API responses
- [ ] Service Workers caching strategy implemented
- [ ] Error handling graceful para API failures
- [ ] TypeScript strict mode sin errors

### **Design Requirements (CRITICAL)**
- [ ] EventCard component identical a template HTML proporcionado
- [ ] Mobile-first responsive design perfect
- [ ] Touch targets minimum 44px height
- [ ] Category color-coding consistent
- [ ] Loading states y error states user-friendly
- [ ] Accessibility compliance WCAG 2.1 AA

### **Performance Requirements**
- [ ] Initial page load <3 segundos en mobile
- [ ] Navigation between screens <1 segundo
- [ ] API responses cached apropriadamente (30min TTL)
- [ ] Images lazy-loaded y optimized
- [ ] Bundle size <2MB total
- [ ] Lighthouse Performance score >85
- [ ] Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1

---

## 🎯 TECHNICAL ARCHITECTURE SUMMARY

```yaml
architecture_overview:
  backend: "FastAPI + PostgreSQL + Redis + Celery"
  frontend: "React + Vite + TypeScript + PWA"
  external_apis: "Eventbrite + Ticketmaster + Meetup + Google Calendar"
  infrastructure: "Docker containers + Railway/Vercel deployment"
  
key_differentiators:
  - "Template-based design (no custom UI invention)"
  - "Multi-API aggregation con smart deduplication"
  - "True PWA con offline-first approach"
  - "Real-time notifications via WebSockets + Web Push"
  - "Geolocation-centric event discovery"
```

Esta especificación detalla un sistema de eventos **mobile-first con capacidades enterprise** usando tecnologías modernas y siguiendo patterns probados. El focus en templates HTML asegura diseño consistente mientras que la integración multi-API proporciona cobertura completa de eventos.

**Confidence Level: 9/10** - Basado en patterns exitosos de context-test con scope bien definido.
