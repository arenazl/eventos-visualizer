# Generar PRP Comprensivo para Eventos Visualizer

Eres un **arquitecto de software senior especializado en aplicaciones de eventos mobile-first con PWA**.

## Tu misión:
1. **Lee CLAUDE.md completamente** - Reglas críticas del proyecto
2. **Lee el archivo `$ARGUMENTS`** (docs/setup/INITIAL.md) - Especificaciones detalladas
3. **Verifica templates HTML** en docs/templates/ - Base para diseño
4. **Research con Puppeteer** de referencias mencionadas
5. **Genera PRP súper detallado** con confidence 9/10

## ANTES DE EMPEZAR - VALIDACIONES CRÍTICAS:

### **1. Verificar Templates HTML**
```bash
# OBLIGATORIO: Verificar que templates existen
ls -la docs/templates/
# Debe contener event-card-reference.html y otros templates
```

### **2. Leer Reglas del Proyecto** 
```bash
# CRÍTICO: Leer reglas antes de continuar
cat CLAUDE.md | grep -A 5 "TEMPLATES HTML"
```

### **3. Entender Puertos y IPs**
- Backend: Puerto 8001 (INMUTABLE)
- Frontend: Puerto 5174 (INMUTABLE)  
- IP: WSL IP, nunca localhost

## Research obligatorio con Puppeteer:

### **Referencias de Diseño a Scrapear:**
- **Eventbrite Mobile**: https://mobbin.com/apps/eventbrite-ios
- **Meetup App**: https://mobbin.com/apps/meetup
- **Facebook Events**: https://facebook.com/events/discovery/
- **Bandsintown**: https://bandsintown.com/
- **SeatGeek**: https://seatgeek.com/
- **Fever**: https://feverup.com/

### **APIs Documentation Research:**
- **Eventbrite API**: https://www.eventbrite.com/platform/api
- **Ticketmaster API**: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
- **Google Calendar API**: https://developers.google.com/calendar/api/guides/overview

## Proceso paso a paso:

### 1. **Análisis Completo del Contexto**
```
Combina información de:
- docs/setup/INITIAL.md (especificaciones base)
- CLAUDE.md (reglas técnicas críticas)
- docs/templates/ (diseño base a seguir)
- Research de apps similares (Puppeteer)
- APIs documentation (integraciones)
```

### 2. **Arquitectura Técnica Detallada**
```
Define específicamente:
- FastAPI backend structure (puerto 8001)
- React + Vite frontend (puerto 5174) 
- PostgreSQL schema optimizado para eventos
- PWA implementation con Service Workers
- Multi-API integration (Eventbrite, Ticketmaster, Meetup)
- Templates HTML to React components mapping
```

### 3. **Plan de Implementación Paso a Paso**
```
Fases específicas:
1. Backend base + Database schema
2. Template HTML to React conversion
3. API integrations (external services)
4. PWA features + offline support
5. Google Calendar integration
6. Push notifications + WebSockets
```

### 4. **Usar Templates HTML Como Base**
```
CRÍTICO:
- Leer docs/templates/event-card-reference.html
- Mapear estructura HTML a React components
- Definir exactamente cómo convertir template a código
- NO inventar diseño - copiar template exacto
```

## Output esperado en PRPs/:

### **PRPs/eventos-visualizer-completo.md debe contener:**

#### **Sección 1: Contexto del Proyecto**
- Descripción completa del sistema de eventos
- Stack tecnológico específico
- APIs integradas y their purposes
- Success criteria definidos

#### **Sección 2: Template HTML to React Mapping**
- Análisis de docs/templates/event-card-reference.html
- Conversión exacta a React components
- CSS classes mapping (TailwindCSS)
- Estructura de components basada en templates

#### **Sección 3: Backend Architecture**
- FastAPI structure con async endpoints
- PostgreSQL schema con PostGIS
- External APIs integration patterns
- WebSocket implementation para notifications

#### **Sección 4: PWA Implementation**
- Service Workers strategy
- Offline support architecture
- Push notifications setup
- Install prompt implementation

#### **Sección 5: Step-by-Step Implementation Plan**
- Phase 1: Core backend + templates conversion
- Phase 2: API integrations + geolocation
- Phase 3: PWA features + calendar sync
- Phase 4: Notifications + performance optimization

#### **Sección 6: Configuration & Environment Setup**
- Environment variables needed
- Docker setup (opcional)
- Database migrations
- External API keys setup

#### **Sección 7: Testing & Validation**
- Component testing strategy
- API integration testing
- PWA functionality validation
- Performance benchmarks

## Confidence Target: 9/10

### **Para lograr 9/10 confidence:**
- ✅ **Templates HTML analysis** completo
- ✅ **External APIs** research profundo
- ✅ **PWA patterns** well-defined
- ✅ **Mobile-first** approach clear
- ✅ **Implementation phases** realistic y achievable
- ✅ **Success criteria** measurable y specific

## Reglas críticas a seguir:

1. **NUNCA inventar diseño** - siempre basar en templates HTML
2. **Puertos inmutables** - 8001 backend, 5174 frontend
3. **APIs reales** - nunca mock data, siempre external services
4. **Mobile-first** - PWA capabilities obligatorias
5. **PostgreSQL + PostGIS** - para geolocalización optimizada

**¡Genera un PRP tan detallado que la implementación sea automática y perfecta!**

Usa CLAUDE.md como contexto obligatorio y docs/templates/ como base de diseño.
