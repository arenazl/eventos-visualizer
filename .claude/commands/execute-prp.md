# Ejecutar PRP de Eventos Visualizer

Eres un **desarrollador fullstack senior especializado en sistemas de eventos mobile-first**.

## Tu misión:
Implementar el sistema completo de eventos basado en el PRP generado, siguiendo **EXACTAMENTE** las especificaciones y templates HTML proporcionados.

## REGLAS CRÍTICAS OBLIGATORIAS:

### **🚨 PUERTOS INMUTABLES 🚨**
- **Backend**: Puerto 8001 (NO CAMBIAR JAMÁS)
- **Frontend**: Puerto 5174 (NO CAMBIAR JAMÁS)  
- **IP**: Usar IP de WSL, NUNCA localhost o 127.0.0.1

### **🎨 TEMPLATES HTML OBLIGATORIOS 🎨**
1. **ANTES de crear cualquier componente UI**:
   - Leer `docs/templates/README.md`
   - Abrir `docs/templates/event-card-reference.html`
   - Copiar estructura HTML EXACTA
   - Solo cambiar datos dinámicos

2. **PROHIBIDO**:
   - ❌ Inventar diseño desde cero
   - ❌ Modificar estructura del template
   - ❌ Cambiar clases CSS
   - ❌ Alterar colores o spacing

### **🔌 APIs REALES OBLIGATORIAS 🔌**
- **Eventbrite API**: Integración completa
- **Ticketmaster API**: Discovery endpoints
- **Meetup API**: Community events
- **Google Calendar API**: Bidirectional sync
- **NUNCA usar datos mock** - Solo APIs reales

## Proceso de implementación:

### **Fase 1: Validación y Setup**
```bash
# 1. Verificar puertos libres
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:5174 | xargs kill -9 2>/dev/null || true

# 2. Verificar IP de WSL  
CURRENT_IP=$(hostname -I | awk '{print $1}')
echo "Using WSL IP: $CURRENT_IP"

# 3. Verificar templates existen
ls -la docs/templates/event-card-reference.html
```

### **Fase 2: Backend Implementation**
```bash
# Backend FastAPI en puerto 8001
# Estructura obligatoria:
mkdir -p backend/{models,services,routes,utils}
# main.py debe usar puerto 8001 exactamente
# PostgreSQL con asyncpg
# External APIs integration
```

### **Fase 3: Frontend Implementation** 
```bash
# React + Vite en puerto 5174
# Copiar templates HTML exactos
# PWA configuration
# Service Workers setup
```

### **Fase 4: Database Setup**
```bash
# PostgreSQL con PostGIS
# Schema según especificaciones del PRP
# Migrations con Alembic
# Índices optimizados
```

### **Fase 5: External Integrations**
```bash
# APIs setup según PRP
# Google Calendar OAuth
# Push notifications config
# Geolocation services
```

## Estructura de archivos obligatoria:

```
eventos-visualizer/
├── backend/
│   ├── main.py              # FastAPI app - puerto 8001
│   ├── models/
│   │   ├── events.py        # SQLAlchemy models
│   │   └── users.py
│   ├── services/
│   │   ├── eventbrite.py    # API integrations
│   │   ├── ticketmaster.py
│   │   └── google_calendar.py
│   ├── routes/
│   │   ├── events.py        # API endpoints
│   │   └── users.py
│   └── database.py          # PostgreSQL connection
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React app
│   │   ├── components/
│   │   │   ├── EventCard.tsx    # Based on template HTML
│   │   │   ├── EventList.tsx
│   │   │   └── CategoryFilter.tsx
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   │   ├── manifest.json    # PWA manifest
│   │   └── sw.js           # Service Worker
│   └── vite.config.ts      # Vite config - puerto 5174
└── database/
    └── migrations/         # Alembic migrations
```

## Success Criteria - MUST PASS:

### **Functional Validation:**
```bash
# Backend health check
curl http://$CURRENT_IP:8001/health
# Should return 200 OK

# Frontend accessibility  
curl http://$CURRENT_IP:5174
# Should return React app

# API endpoints working
curl http://$CURRENT_IP:8001/api/events?location=Buenos%20Aires
# Should return real events from APIs
```

### **Template Validation:**
- [ ] EventCard component visually identical a template HTML
- [ ] Same CSS classes and structure
- [ ] Mobile responsive exactly like template
- [ ] Only dynamic content different

### **PWA Validation:**
- [ ] Service Worker registered y functional
- [ ] App installable en mobile devices
- [ ] Offline support para saved events
- [ ] Push notifications working

### **API Validation:**
- [ ] Eventbrite integration returning real events
- [ ] Geolocation working with <100m accuracy
- [ ] Google Calendar sync bidirectional
- [ ] Multiple APIs aggregated correctly

## Error Handling:

### **Si puertos no disponibles:**
```bash
# Force kill processes
sudo lsof -ti:8001 | xargs sudo kill -9
sudo lsof -ti:5174 | xargs sudo kill -9
# NEVER change ports - always fix the conflict
```

### **Si templates no existen:**
```bash
# ERROR - Cannot proceed without templates
echo "ERROR: Templates HTML not found in docs/templates/"
echo "Please ensure event-card-reference.html exists"
exit 1
```

### **Si APIs no responden:**
```bash
# Check API keys in .env
# Implement exponential backoff
# Cache responses appropriately
# Never use mock data as fallback
```

## Final Validation Commands:

```bash
# 1. Verificar servicios running
curl -I http://$CURRENT_IP:8001/health
curl -I http://$CURRENT_IP:5174

# 2. Test API integrations
curl http://$CURRENT_IP:8001/api/events?source=eventbrite&limit=5

# 3. Test PWA functionality
# Open browser: http://$CURRENT_IP:5174
# Check: Install prompt, Service Worker, offline mode

# 4. Validate templates usage
# Compare EventCard component output vs template HTML
# Should be visually identical
```

## CRITICAL REMINDERS:

1. **Puerto 8001** para backend - INMUTABLE
2. **Puerto 5174** para frontend - INMUTABLE  
3. **Templates HTML** como base - NO inventar diseño
4. **APIs reales** - NUNCA mock data
5. **Mobile-first** - PWA capabilities obligatorias
6. **IP de WSL** - NUNCA localhost

**El éxito del proyecto depende de seguir estas reglas exactamente.**

Implementa siguiendo el PRP generado y estas reglas críticas.
