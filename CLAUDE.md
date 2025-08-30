### 🚨🚨🚨 REGLA MEGACRÍTICA - PUERTOS INMUTABLES 🚨🚨🚨
**⛔⛔⛔ NUNCA, JAMÁS, BAJO NINGUNA CIRCUNSTANCIA CAMBIAR LOS PUERTOS ⛔⛔⛔**

**🔥 PUERTOS OFICIALES DEL PROYECTO (INTOCABLES): 🔥**
- **BACKEND**: Puerto 8001 (INMUTABLE - NO TOCAR)
- **FRONTEND**: Puerto 5174 (INMUTABLE - NO TOCAR)

**🚨 REGLA CRÍTICA: Si un puerto está ocupado:**
1. ✅ MATAR el proceso: `lsof -ti:PUERTO | xargs kill -9`
2. ✅ LIBERAR puerto: `fuser -k PUERTO/tcp`
3. ✅ REINICIAR en puerto correcto
4. ❌ **PROHIBIDO ABSOLUTO** cambiar a otro puerto

**⚠️ CUALQUIER VIOLACIÓN DE ESTA REGLA ES INACEPTABLE ⚠️**

### 🌐 REGLA CRÍTICA - IPs EN WSL/LINUX
**NUNCA usar localhost o 127.0.0.1 - Estamos en WSL/Linux**
- **IP CORRECTA**: 172.29.228.80 (o la IP actual de WSL)
- **Backend**: http://172.29.228.80:8001
- **Frontend**: http://172.29.228.80:5174
- **NO USAR**: localhost, 127.0.0.1, 0.0.0.0
- **Obtener IP actual**: `hostname -I | awk '{print $1}'`

### 🎉 REGLA CRÍTICA - TEMPLATES HTML OBLIGATORIOS
**🔥🔥🔥 LA CLAVE DEL ÉXITO - NO INVENTAR DISEÑO 🔥🔥🔥**

#### **ANTES DE ESCRIBIR CUALQUIER CÓDIGO:**
1. **📄 LEER** `docs/templates/README.md` completo
2. **📄 ABRIR** `docs/templates/event-card-reference.html`
3. **👀 ESTUDIAR** estructura HTML completa
4. **📋 COPIAR** elementos, clases CSS, jerarquía EXACTA
5. **✅ SOLO CAMBIAR** placeholders {{event.property}} por datos dinámicos

#### **PROHIBIDO ABSOLUTAMENTE:**
- ❌ **Inventar diseño** desde cero
- ❌ **Modificar estructura** HTML del template
- ❌ **Cambiar clases CSS** o TailwindCSS
- ❌ **Alterar colores** o spacing
- ❌ **Crear layout** diferente al template

#### **OBLIGATORIO:**
- ✅ **Copiar estructura** HTML exacta de templates
- ✅ **Usar mismas clases** CSS/TailwindCSS
- ✅ **Mantener jerarquía** de elementos idéntica
- ✅ **Solo cambiar contenido** dinámico
- ✅ **Resultado visualmente** idéntico al template

### 🎉 Project Awareness & Context & Research
- **Proyecto**: Sistema completo de eventos mobile-first con PWA
- **Dominio**: Visualización y gestión de eventos (deportivos, culturales, fiestas, tech)
- **Tecnologías**: FastAPI + PostgreSQL + React (Vite) + PWA + Google Calendar
- **APIs**: Eventbrite, Ticketmaster, Meetup, Facebook Events integradas
- **Base de datos**: PostgreSQL con PostGIS para geolocalización
- **Deployment**: Docker + Railway/Vercel para producción
- **Tiempo real**: WebSockets para notificaciones push

### ⚠️ CONFIGURACIÓN CRÍTICA DEL SERVIDOR
- **BACKEND ÚNICO**: `main.py` en puerto 8001 (NO CREAR NUEVOS SERVIDORES)
- **NO CREAR**: server.py, api_server.py, events_server.py, etc.
- **POOL PostgreSQL**: 20 conexiones configuradas, con try-finally para liberación
- **CONEXIÓN DB**: PostgreSQL con asyncpg para async/await
- **CREDENCIALES DB**: Configuradas en .env
- **IMPORTANTE**: 
  - El servidor DEBE ser estable sin necesidad de "auto-recuperación"
  - Las conexiones SIEMPRE se liberan con try-finally
  - NO crear scripts de restart/monitor - el servidor debe funcionar bien
  - Si hay problemas, ARREGLAR el main.py, NO crear otro servidor

### 🧱 Estructura del Código
- **Máximo líneas por archivo**: 500 líneas
- **Backend**: FastAPI con arquitectura modular por dominio (events, users, notifications)
- **Frontend**: React + Vite con componentes reutilizables, diseño mobile-first
- **API**: REST + WebSockets para notificaciones en tiempo real
- **Base de datos**: PostgreSQL con migraciones Alembic, modelos con SQLAlchemy

### 📚 Documentación Obligatoria (Research Automático)
- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **SQLAlchemy PostgreSQL**: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- **React**: https://react.dev/learn
- **Vite**: https://vitejs.dev/guide/
- **React Router**: https://reactrouter.com/en/main
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Google Calendar API**: https://developers.google.com/calendar/api/guides/overview
- **Eventbrite API**: https://www.eventbrite.com/platform/api
- **Ticketmaster API**: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

### 🎨 GUÍA DE ESTILO VISUAL (SEGUIR TEMPLATES)
- **PRIMARIO**: Usar diseño del template HTML proporcionado
- **Colors**: Los definidos en template (no modificar)
- **Typography**: Inter font si no especifica template
- **Components**: Estructura exacta de template HTML
- **Responsive**: Mobile-first como template
- **Animations**: Solo las del template original

### 🎉 REGLAS DEL NEGOCIO DE EVENTOS (CRÍTICAS)
- **Categorías**: Música, Deportes, Cultural, Tech, Fiestas, Hobbies, Internacional
- **Geolocalización**: Radio de búsqueda 5km, 10km, 25km, 50km
- **APIs**: Mínimo 3 APIs integradas (Eventbrite, Ticketmaster, Meetup)
- **Calendar**: Sincronización bidireccional con Google Calendar
- **PWA**: Service Workers, offline support, push notifications
- **Mobile**: Optimizado para touch, gestures, mobile-first responsive

### 🔍 REGLA CRÍTICA - Verificación Antes de Afirmar Soluciones
**OBLIGATORIO**: Antes de afirmar que algo está funcionando:
1. **NUNCA decir "está funcionando" sin verificar**
2. **SIEMPRE ejecutar pruebas reales**:
   - Para backends: hacer curl al health endpoint
   - Para APIs: verificar respuestas de Eventbrite/Ticketmaster
   - Para frontend: verificar en browser real
3. **Usar comandos de verificación**:
   ```bash
   curl http://172.29.228.80:8001/health
   curl http://172.29.228.80:8001/api/events?location=Mendoza
   ```
4. **Si algo falla, ser honesto** y mostrar el error exacto

### 🔍 Research con Puppeteer (Referencias de Diseño)
- **Eventbrite Mobile**: https://mobbin.com/apps/eventbrite-ios - UI patterns y navigation
- **Meetup App**: https://mobbin.com/apps/meetup - Community events interface
- **Facebook Events**: https://facebook.com/events/discovery/ - Discovery y social features
- **Bandsintown**: https://bandsintown.com/ - Music events y artist tracking
- **SeatGeek**: https://seatgeek.com/ - Sports events y ticket integration
- **Fever**: https://feverup.com/ - Cultural events y experiences
- **Dice**: https://dice.fm/ - Music events mobile-first design
- **Universe**: https://universe.com/ - Event creation y management

### ✅ Task Completion
- **Marcar tareas completadas** inmediatamente en documentación
- **Agregar sub-tareas descubiertas** durante desarrollo
- **Validar funcionalidad** en cada step usando templates como referencia

### 📎 Style & Conventions
- **Backend**: Python con FastAPI, type hints obligatorios, formato con black
- **Frontend**: TypeScript con React + Vite, ESLint + Prettier
- **Base de datos**: PostgreSQL con naming snake_case, foreign keys siempre indexadas
- **API**: Rutas RESTful + WebSocket endpoints para notifications
- **Documentación**: Docstrings estilo Google para todas las funciones

### 📚 Documentation & Explainability
- **README.md actualizado** cuando se agreguen features o cambien dependencias
- **Comentarios en código no obvio** especialmente lógica de APIs externas
- **Inline comments con `# Razón:`** explicando el por qué, no el qué

### 🧠 AI Behavior Rules
- **Nunca asumir contexto faltante** - preguntar si no está claro
- **Nunca inventar diseño** - SIEMPRE usar templates HTML proporcionados
- **Confirmar estructura de templates** antes de crear componentes
- **Nunca borrar templates** a menos que sea parte de una tarea específica

### 🔒 Seguridad Específica para Eventos
- **API Keys**: Nunca expuestas al frontend, solo en .env
- **Geolocation**: Solo almacenar temporalmente, con user consent
- **External APIs**: Rate limiting y error handling apropiado
- **User data**: Mínimo necesario, GDPR compliance
- **Push notifications**: Opt-in explicito del usuario

### 🚀 Performance Requirements
- **PWA**: Service Workers para offline support
- **Initial load**: <3 segundos en mobile
- **API responses**: Cache apropiado para external APIs
- **Images**: Lazy loading y optimization automática
- **Bundle size**: <2MB total para mobile optimization

### 🐳 Development Environment
- **Docker recomendado** para desarrollo consistente
- **PostgreSQL en container** o servicio cloud
- **Hot reload** para desarrollo rápido React + FastAPI
- **Variables de entorno** para todas las configuraciones de APIs

### 📊 Monitoring y Analytics
- **Logs estructurados** para debugging APIs externas
- **Métricas de uso**: eventos más vistos, categorías populares
- **API health checks** para servicios externos
- **Performance tracking**: load times, API response times

### 🎯 Frontend Específico con React + Vite
- **Build tool**: Vite para desarrollo rápido y hot reload
- **Routing**: React Router para navegación SPA
- **State management**: Zustand para estado global ligero
- **Components**: Basados en templates HTML proporcionados
- **Testing**: Vitest + React Testing Library
- **Bundle**: Optimización automática para mobile

### 💾 PostgreSQL Específico
- **Engine**: PostgreSQL 14+ con PostGIS para geolocalización
- **Charset**: UTF8 para caracteres internacionales
- **Indices**: Optimizados para queries de geolocalización y fechas
- **Migrations**: Alembic para schema changes
- **Connection pool**: AsyncPG con pool de conexiones

### 🎨 REGLA CRÍTICA - TEMPLATES HTML
**📄 ANTES DE CUALQUIER COMPONENTE UI:**

1. **Abrir** `docs/templates/README.md` y leer completo
2. **Verificar** que `docs/templates/event-card-reference.html` existe
3. **Estudiar** estructura HTML del template
4. **Copiar** estructura exacta en React/HTML
5. **Solo cambiar** datos dinámicos, mantener todo lo demás

**NUNCA INVENTAR DISEÑO - SIEMPRE COPIAR TEMPLATE**

## 🗂️ REGLA CRÍTICA: Gestión de Archivos
**NUNCA** guardes archivos temporales, logs o scripts en el directorio raíz.

**SIEMPRE** usar las carpetas apropiadas:
- Templates HTML: `docs/templates/`
- Research y docs: `docs/research/`, `docs/guides/`
- Scripts de deployment: `scripts/`
- Logs de desarrollo: `logs/` (en .gitignore)

## 🔧 SOLUCIONES A PROBLEMAS CONOCIDOS

### APIs Externas Rate Limited
**Problema**: "Rate limit exceeded" de Eventbrite/Ticketmaster
**Causa**: Demasiadas requests sin cache
**Solución**:
1. Cache Redis con TTL de 30 minutos para responses
2. Background jobs para sync periódico
3. Exponential backoff para retry
```python
@cached(ttl=1800)  # 30 minutos
async def get_events_from_api(location: str):
    # API call con retry logic
```

### Frontend Mobile Performance
**Problema**: App lenta en mobile
**Causa**: Bundle size grande, imágenes no optimizadas
**Solución**:
1. Lazy loading de componentes
2. Image optimization automática
3. Service Workers para cache
4. Bundle splitting por routes

## 📝 ESTADO ACTUAL Y ARQUITECTURA

### 🔄 Arquitectura del Sistema

#### **Backend (Puerto 8001)**
- **main.py**: Aplicación FastAPI principal
- **Módulos**: events, users, notifications, external_apis
- **Database**: PostgreSQL con modelos SQLAlchemy
- **APIs externas**: Eventbrite, Ticketmaster, Meetup integradas
- **WebSockets**: Para push notifications en tiempo real

#### **Frontend (Puerto 5174)**  
- **React + Vite**: SPA con routing
- **Components**: Basados en templates HTML proporcionados
- **PWA**: Service Workers para offline support
- **State**: Zustand para manejo de estado global

#### **Base de Datos PostgreSQL**
```sql
-- Eventos principales
events (
  id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  start_datetime TIMESTAMP WITH TIME ZONE,
  end_datetime TIMESTAMP WITH TIME ZONE,
  venue_name VARCHAR(255),
  venue_address TEXT,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  category VARCHAR(100),
  subcategory VARCHAR(100),
  price DECIMAL(10,2),
  currency CHAR(3) DEFAULT 'ARS',
  is_free BOOLEAN DEFAULT false,
  external_id VARCHAR(255),
  source_api VARCHAR(50),  -- 'eventbrite', 'ticketmaster', 'meetup'
  image_url TEXT,
  event_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Usuarios
users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url TEXT,
  google_id VARCHAR(255),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  radius_km INTEGER DEFAULT 25,
  timezone VARCHAR(100) DEFAULT 'America/Argentina/Buenos_Aires',
  locale VARCHAR(10) DEFAULT 'es-AR',
  push_enabled BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Eventos favoritos/guardados
user_events (
  user_id UUID REFERENCES users(id),
  event_id UUID REFERENCES events(id),
  status VARCHAR(50) DEFAULT 'interested',  -- 'interested', 'going', 'not_going'
  notification_24h_sent BOOLEAN DEFAULT false,
  notification_1h_sent BOOLEAN DEFAULT false,
  calendar_synced BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, event_id)
);
```

## 📋 ESTADO ACTUAL (Sesión 29 Agosto 2025) - PUNTO DE PARTIDA PARA PRÓXIMO AGENTE

### 🚀 **LO QUE ESTÁ FUNCIONANDO:**
- ✅ **Servidor Backend**: Funcionando en puerto 8001 sin errores de sintaxis
- ✅ **Servidor Frontend**: Funcionando en puerto 5174 
- ✅ **CloudScraper instalado**: `pip install cloudscraper --break-system-packages` (EXITOSO)
- ✅ **Endpoints sincronizados**: Frontend y backend tienen los mismos endpoints
- ✅ **Sin datos simulados**: Todo el código limpio de eventos mockup

### 🔧 **LIBRERÍAS Y DEPENDENCIAS INSTALADAS:**
```bash
# Instalado correctamente:
pip3 install cloudscraper --break-system-packages  # ✅ FUNCIONANDO
python3 -c "import cloudscraper; print('✅ OK')"    # ✅ VERIFICADO
```

### 📂 **ARCHIVOS CRÍTICOS MODIFICADOS:**

#### **BACKEND** (Sin eventos simulados):
- ✅ `/backend/services/cloud_scraper.py` - Limpio, solo APIs reales
- ✅ `/backend/services/firecrawl_scraper.py` - Limpio, solo APIs reales  
- ✅ `/backend/services/lightweight_scraper.py` - Limpio, errores sintaxis arreglados
- ✅ `/backend/services/cloudscraper_events.py` - Importación `Optional` agregada
- ✅ `/backend/main.py` - Todos los endpoints agregados para compatibilidad frontend

#### **FRONTEND** (Ubicación dinámica arreglada):
- ✅ `/frontend/src/stores/EventsStore.tsx` - **CAMBIO CRÍTICO**:
  ```typescript
  // ANTES (hardcodeado):
  apiUrl += `&location=${encodeURIComponent("Mendoza")}`
  apiUrl += `&location=${encodeURIComponent("Cordoba")}`
  
  // AHORA (dinámico):
  apiUrl += `&location=${encodeURIComponent(searchLocation.name || "Buenos Aires")}`
  ```
- ✅ `/frontend/src/services/api.ts` - Endpoints que el frontend espera (sin cambios necesarios)
- ✅ `/frontend/src/pages/HomePageModern.tsx` - Flujo de geolocalización existente (funcional)
- ✅ **Frontend reiniciado** en puerto 5174 para aplicar cambios
- ✅ **Caché del navegador**: Debe limpiarse (Ctrl+Shift+R) para ver cambios

### 🌐 **ENDPOINTS SINCRONIZADOS (Frontend ↔ Backend):**
```bash
# VERIFICAR que estos funcionen:
curl http://172.29.228.80:8001/api/location/detect     # ✅ Agregado
curl http://172.29.228.80:8001/api/location/set        # ✅ Agregado  
curl http://172.29.228.80:8001/api/location/cities     # ✅ Agregado
curl http://172.29.228.80:8001/api/events/smart-search # ✅ Agregado
curl http://172.29.228.80:8001/api/ai/chat             # ✅ Agregado
curl http://172.29.228.80:8001/api/ai/recommendations  # ✅ Agregado
curl http://172.29.228.80:8001/api/ai/plan-weekend     # ✅ Agregado
curl http://172.29.228.80:8001/api/ai/trending-now     # ✅ Agregado
```

### ⚠️ **PROBLEMAS IDENTIFICADOS:**
1. **Buenos Aires Data API**: URL no funciona (API cambió o no disponible)
2. **Eventbrite**: Necesita API key (sin API key configurado)
3. **Facebook/Instagram**: APIs muy restrictivas, difícil scrapear sin tokens oficiales
4. **Algunos scrapers**: Requieren configuración adicional

### 🔄 **TRABAJO INTEGRAL COMPLETADO EN ESTA SESIÓN:**

#### **PROBLEMA INICIAL**: Frontend y Backend desincronizados
- **Frontend esperaba**: `/api/location/detect`, `/api/events/smart-search` 
- **Backend tenía**: `/detect`, `/api/smart/search`
- **Solución**: Agregamos todos los endpoints faltantes en backend para compatibilidad total

#### **SINCRONIZACIÓN FRONTEND ↔ BACKEND**:
```bash
# Frontend llamaba → Backend ahora tiene:
/api/location/detect     → ✅ Agregado con prefijo correcto  
/api/location/set        → ✅ Agregado con prefijo correcto
/api/location/cities     → ✅ Agregado con prefijo correcto
/api/events/smart-search → ✅ Agregado como GET redirect a POST /api/smart/search
/api/ai/chat             → ✅ Agregado, redirige a smart search
/api/ai/recommendations  → ✅ Agregado como alias a /api/ai/recommend  
/api/ai/plan-weekend     → ✅ Agregado, retorna eventos filtrados
/api/ai/trending-now     → ✅ Agregado, retorna top eventos
```

#### **LIMPIEZA COMPLETA DE DATOS SIMULADOS**:
- **Eliminados**: Todos los eventos mockup/hardcodeados de TODOS los scrapers
- **Política nueva**: Solo datos reales o arrays vacíos con warnings
- **Resultado**: Sistema honesto que informa cuando no puede obtener datos

### 🛠️ **SIGUIENTE AGENTE DEBE HACER:**

#### **PRIORIDAD 1 - APIs que SÍ pueden funcionar:**
```bash
# 1. Conseguir API key de Eventbrite (GRATIS):
# - Ir a https://www.eventbrite.com/platform/api  
# - Crear cuenta developer
# - Agregar a .env: EVENTBRITE_API_KEY=tu_key_aqui

# 2. CloudScraper ya está instalado, debería intentar scrapear:
curl http://172.29.228.80:8001/api/multi/fetch-all
```

#### **PRIORIDAD 2 - Verificar funcionalidad:**
```bash
# Probar endpoints principales:
curl http://172.29.228.80:8001/health
curl http://172.29.228.80:8001/api/events?limit=10
curl http://172.29.228.80:8001/api/multi/test-apis
```

### 🎯 **Para el Próximo Agente:**

1. **SERVIDOR YA ESTÁ FUNCIONANDO** - No recrear, solo usar
2. **CloudScraper INSTALADO** - Debería intentar scrapear Facebook/Instagram
3. **Código LIMPIO** - Sin datos simulados, solo APIs reales o vacío
4. **Enfoque**: Conseguir API keys reales o mejorar scraping existente

### 🔗 **REGLAS CRÍTICAS (Inmutables):**
- Puerto 8001 (backend) y 5174 (frontend) - NO CAMBIAR
- IP: 172.29.228.80 (WSL) - NO usar localhost
- Solo datos reales - NO crear eventos simulados
- Frontend y backend YA sincronizados - NO modificar endpoints

### 💡 **PUNTO DE PARTIDA RECOMENDADO:**
```bash
# 1. Verificar servidores:
curl http://172.29.228.80:8001/health
curl http://172.29.228.80:5174

# 2. Probar multi-source:
curl http://172.29.228.80:8001/api/multi/fetch-all

# 3. Si no hay eventos, conseguir API key de Eventbrite
```

---
**Estado: SERVIDORES FUNCIONANDO, CÓDIGO LIMPIO, LISTO PARA APIS REALES**
**Próximo paso: Configurar API keys o mejorar scraping real**
