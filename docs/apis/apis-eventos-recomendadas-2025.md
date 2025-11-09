<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-01-12 22:30
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-01-12 22:30: Creación inicial - Investigación de mejores APIs de eventos 2025
📋 TAGS: #apis #events #eventbrite #ticketmaster #predicthq #research
-->

# 🌐 MEJORES APIs DE EVENTOS - 2025

## 🎯 RESUMEN EJECUTIVO

Después de investigar el mercado actual de APIs de eventos, encontramos **10 APIs** analizadas en detalle:

### ✅ **TIER 1: APIs Recomendadas (Implementar YA)**
1. **Ticketmaster Discovery API** ⭐⭐⭐⭐⭐ - La mejor, free tier generoso (5K/día)
2. **Eventbrite API** ⭐⭐⭐⭐ - Ya implementada, buenos resultados confirmados
3. **SeatGeek API** ⭐⭐⭐⭐ - Agregador de 60+ plataformas, excelente cobertura

### 🔶 **TIER 2: APIs Complementarias (Considerar después)**
4. **PredictHQ API** ⭐⭐⭐⭐⭐ - Cobertura masiva pero CARA ($500/año)
5. **Meetup API** ⭐⭐⭐ - Eventos comunitarios/meetups
6. **Resident Advisor** ⭐⭐⭐ - Música electrónica (requiere scraping)

### 🚫 **TIER 3: APIs No Recomendadas (Limitaciones críticas)**
7. **Bandsintown API** ⭐⭐⭐⭐ - Solo búsqueda por artista (NO geográfica)
8. **Songkick API** ⭐⭐⭐ - Ya NO es gratis, requiere license fee
9. **Dice.fm API** ⭐⭐⭐ - Solo para partners, no público
10. **Instagram Scraping** ⭐⭐ - MUY difícil, alto mantenimiento, riesgos legales

### 📊 **RESULTADO:**
- **3 APIs viables** para implementar inmediatamente (Ticketmaster, Eventbrite, SeatGeek)
- **2 APIs de backup** si se necesita más cobertura (PredictHQ cara, Meetup nicho)
- **5 APIs descartadas** por limitaciones (no free tier, no búsqueda geo, partners only)

---

## 📊 ANÁLISIS DETALLADO POR API

### 1️⃣ TICKETMASTER DISCOVERY API ⭐⭐⭐⭐⭐

**🔗 Documentación**: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

#### ✅ **PROS:**
- **Free tier generoso**: 5,000 llamadas/día, 5 requests/segundo
- **Cobertura global**: Partner oficial de NFL, NBA, NHL, USTA
- **Datos estructurados**: JSON bien formateado, fácil de parsear
- **Categorías completas**: Deportes, música, teatro, familia, artes
- **Geolocalización**: Búsqueda por latitud/longitud con radio
- **Imágenes de calidad**: URLs de imágenes en alta resolución
- **API Explorer**: Herramienta de testing en vivo
- **Sin autenticación OAuth**: Solo API key (más simple)

#### ⚠️ **CONTRAS:**
- Rate limits ajustados (5 req/seg puede ser poco en picos)
- Enfocado en eventos masivos/comerciales (menos eventos pequeños)

#### 🎯 **USO RECOMENDADO:**
```python
# Endpoint principal
GET https://app.ticketmaster.com/discovery/v2/events.json
    ?apikey={API_KEY}
    &city={CITY}
    &countryCode={COUNTRY_CODE}
    &radius=50
    &size=50
```

#### 💰 **PRICING:**
- **Free**: 5,000 llamadas/día ✅
- **Upgrade**: Caso por caso (contactar Ticketmaster)

#### 🚀 **PRIORIDAD:** ALTA - Implementar primero

---

### 2️⃣ EVENTBRITE API ⭐⭐⭐⭐

**🔗 Documentación**: https://www.eventbrite.com/platform/api

#### ✅ **PROS:**
- **Ya implementado**: Tenemos scraper funcionando ✅
- **Buenos eventos**: Confirmado por el usuario
- **Rate limits razonables**: 1,000 llamadas/hora (48K/día)
- **Eventos variados**: Desde pequeños meetups hasta festivales
- **Datos de tickets**: Info de precios y disponibilidad
- **OAuth2**: Autenticación estándar
- **Categorías ricas**: 20+ categorías de eventos

#### ⚠️ **CONTRAS:**
- **API Search deshabilitada**: Desde Feb 2020 no hay endpoint público `/events/search/`
- **Solo eventos propios**: Necesitas OAuth para ver eventos de organizadores
- **Requiere cuenta**: No hay acceso anónimo
- **Límites estrictos**: 1K/hora puede ser limitante

#### 🎯 **ESTADO ACTUAL:**
```python
# TENEMOS: Web scraping funcionando
# URL: https://www.eventbrite.com/d/{location}/events/

# MIGRACION RECOMENDADA:
# Si conseguimos OAuth token → Usar API oficial
# Si no → Mantener web scraping actual
```

#### 💰 **PRICING:**
- **Free**: 1,000 req/hora con OAuth token ✅
- **Límites**: No hay upgrade público conocido

#### 🚀 **PRIORIDAD:** MEDIA - Ya funciona con scraping

---

### 3️⃣ SEATGEEK API ⭐⭐⭐⭐

**🔗 Documentación**: https://seatgeek.com/build (developer.seatgeek.com)

#### ✅ **PROS:**
- **Agregador masivo**: 60+ sitios de tickets (StubHub, TicketsNow, etc.)
- **API de eventos**: Devuelve eventos, performers, venues
- **Seat maps interactivos**: Mapas de asientos visuales
- **Sin OAuth**: API key simple
- **Datos de inventario**: Disponibilidad en tiempo real
- **Búsqueda flexible**: Por ciudad, venue, performer, fecha

#### ⚠️ **CONTRAS:**
- **Solo lectura**: NO permite comprar tickets via API
- **Rate limits desconocidos**: Docs no especifican límites públicos
- **Enfoque en reventa**: Más orientado a ticketing que a discovery

#### 🎯 **USO RECOMENDADO:**
```python
# Endpoints principales
GET /events - Lista eventos
GET /performers - Buscar artistas/equipos
GET /venues - Buscar venues

# Filtros útiles
?geoip=true  # Detecta ubicación automática
?per_page=100
?taxonomies.name=concert
```

#### 💰 **PRICING:**
- **Free tier**: Parece existir pero sin límites publicados
- **Contactar**: Para límites altos

#### 🚀 **PRIORIDAD:** ALTA - Complementa Ticketmaster

---

### 4️⃣ PREDICTHQ API ⭐⭐⭐⭐⭐ (Pero $$$)

**🔗 Documentación**: https://docs.predicthq.com/

#### ✅ **PROS:**
- **Cobertura MASIVA**: 25,000+ ciudades worldwide
- **19 categorías**: Incluye eventos NO programados (clima, política)
- **Scores de impacto**: ML-powered impact predictions
- **Datos enriquecidos**: Info contextual rica (attendance estimates)
- **APIs múltiples**: REST, Python SDK, JavaScript SDK
- **Integraciones**: Snowflake, AWS Data Exchange
- **Calidad enterprise**: Usada por corporaciones grandes

#### ⚠️ **CONTRAS:**
- **CARA**: $500/año mínimo (no es free tier real)
- **Trial de 14 días**: Luego requiere pago
- **Overkill**: Demasiado para app consumer
- **Complejidad**: Diseñada para BI/forecasting, no consumer apps

#### 🎯 **USO RECOMENDADO:**
```python
# Si eventualmente escalamos a enterprise
GET /v1/events/
    ?location_around={lat},{lon},{radius}
    &category=concerts,festivals,sports
    &rank_level=4,5  # Solo eventos importantes
```

#### 💰 **PRICING:**
- **Trial**: 14 días gratis con límite de 1K exports
- **Paid**: Desde $500/año ❌
- **Enterprise**: Contactar para custom pricing

#### 🚀 **PRIORIDAD:** BAJA - Muy cara para MVP

---

### 5️⃣ MEETUP API ⭐⭐⭐

**🔗 Documentación**: https://www.meetup.com/api/

#### ✅ **PROS:**
- **Eventos comunitarios**: Perfect para meetups, grupos locales
- **Audience building**: Bueno para community management
- **Gratuitos mayormente**: Mayoría de eventos son free
- **API GraphQL**: Moderna y flexible
- **Meetup Pro**: Features avanzadas para orgs

#### ⚠️ **CONTRAS:**
- **Nicho específico**: Solo eventos tipo "meetup"
- **No masivos**: Pocos conciertos/deportes grandes
- **OAuth requerido**: Flujo de auth complejo
- **Rate limits estrictos**: Limits no publicados pero reportados como bajos

#### 🚀 **PRIORIDAD:** MEDIA-BAJA - Complementario

---

### 6️⃣ BANDSINTOWN API ⭐⭐⭐⭐

**🔗 Documentación**: https://www.artists.bandsintown.com/bandsintown-api

#### ✅ **PROS:**
- **Cobertura masiva**: 95M+ fans, 645K artistas, 45K venues
- **Especializado en música**: Conciertos, festivales, tours
- **Base de datos grande**: 6M+ eventos (upcoming + past)
- **Free tier**: Disponible para partners
- **Tracking de artistas**: Usuarios pueden seguir bandas favoritas
- **Read-only**: Fácil de integrar

#### ⚠️ **CONTRAS:**
- **Limitado a artistas**: Solo funciona si buscas por artista específico
- **NO búsqueda geográfica**: No puedes hacer "todos los eventos en Buenos Aires"
- **Partnership requerido**: Requiere aplicar como partner
- **Solo música**: No cubre deportes, cultura, etc.

#### 🎯 **USO RECOMENDADO:**
```python
# Solo funciona con artistas conocidos
GET /artists/{artist_name}
GET /artists/{artist_id}/events

# NO FUNCIONA para búsqueda por ciudad genérica
# ❌ GET /events?location=Buenos Aires  # No existe
```

#### 💰 **PRICING:**
- **Partner program**: Requiere aplicación
- **Limitaciones**: No para búsqueda geográfica general

#### 🚀 **PRIORIDAD:** BAJA - Muy limitada (solo por artista)

---

### 7️⃣ SONGKICK API ⭐⭐⭐

**🔗 Documentación**: https://www.songkick.com/developer

#### ✅ **PROS:**
- **Base de datos masiva**: 6M+ eventos de música en vivo
- **Búsqueda por ubicación**: Sí soporta búsquedas geográficas ✅
- **Filtros avanzados**: Por fecha, venue, artista, metro area
- **API REST**: Fácil de integrar
- **Tracking histórico**: Eventos pasados disponibles

#### ⚠️ **CONTRAS:**
- **PAGO OBLIGATORIO**: Ya no aceptan free tier
- **No student projects**: Rechazan proyectos educativos/hobbies
- **Solo música**: No eventos de otros tipos
- **Partnership required**: Requiere acuerdo comercial + license fee

#### 💰 **PRICING:**
- **Free tier**: ❌ YA NO DISPONIBLE
- **Paid**: License fee (monto no público)
- **Restricción**: Solo proyectos comerciales

#### 🚀 **PRIORIDAD:** BAJA - Ya no es gratis

---

### 8️⃣ DICE.FM API ⭐⭐⭐

**🔗 Documentación**: https://partners-endpoint.dice.fm/graphql/docs/

#### ✅ **PROS:**
- **Adquirida por Fever**: Plataforma grande (Fever + Dice)
- **GraphQL API**: Moderna y flexible
- **Enfoque electrónica**: Música electrónica, underground, DJ sets
- **GitHub activo**: 47 repositorios disponibles
- **Partnership API**: Para integración downstream

#### ⚠️ **CONTRAS:**
- **Solo para partners**: Ticket Holders API requiere credenciales
- **Documentación limitada**: No hay API pública documentada
- **Nicho específico**: Principalmente electrónica/techno
- **Scraping alternativo**: Existe scraper de terceros (Apify)

#### 🎯 **ALTERNATIVA:**
```bash
# Como no hay API pública fácil:
# Opción 1: Aplicar como partner (difícil)
# Opción 2: Usar scraper de Apify/terceros
# Opción 3: Web scraping directo
```

#### 🚀 **PRIORIDAD:** BAJA - API no accesible públicamente

---

### 9️⃣ RESIDENT ADVISOR (RA) ⭐⭐⭐

**🔗 Website**: https://ra.co/events

#### ✅ **PROS:**
- **Autoridad en electrónica**: LA plataforma para techno/house/electronic
- **Cobertura global**: Eventos en todo el mundo
- **Calidad de curaduría**: Eventos bien seleccionados
- **Búsqueda geográfica**: Soporta búsqueda por ciudad/país

#### ⚠️ **CONTRAS:**
- **NO HAY API PÚBLICA**: No existe documentación de API oficial
- **Solo web scraping**: Única forma de obtener datos
- **Anti-scraping**: Pueden tener protecciones
- **Nicho específico**: Solo música electrónica

#### 🎯 **SOLUCIÓN:**
```python
# Scraping directo de ra.co/events/
# URL pattern: https://ra.co/events/{country}/{city}
# Parsing de HTML con BeautifulSoup
```

#### 🚀 **PRIORIDAD:** MEDIA - Si queremos electrónica, vale la pena

---

### 🔟 INSTAGRAM SCRAPING ⭐⭐

**🔗 Tools**: Instagrapi (Python), RapidAPI Instagram Scraper

#### ✅ **PROS:**
- **Eventos orgánicos**: Muchos locales/bares publican eventos en IG
- **Data rica**: Imágenes, descriptions, ubicaciones, hashtags
- **Alcance local**: Eventos pequeños que no están en otras plataformas
- **Unofficial APIs**: Herramientas como Instagrapi, RapidAPI

#### ⚠️ **CONTRAS:**
- **MUY DIFÍCIL**: Instagram actualiza bloqueos cada 2-4 semanas
- **TLS Fingerprinting**: Detecta bots por handshake SSL
- **Rate limiting severo**: Ban fácil de IPs
- **Requires proxies**: Necesitas proxies residenciales/4G
- **NO API oficial de eventos**: Graph API no expone eventos
- **Data no estructurada**: Posts no tienen formato estándar
- **Alto mantenimiento**: Constante adaptación a cambios

#### 🎯 **OPCIONES DE IMPLEMENTACIÓN:**

**Opción A - RapidAPI (Más fácil pero pago):**
```python
# APIs disponibles en RapidAPI:
# - Instagram Scraper Stable API
# - Instagram API Fast & Reliable
# Costo: Variable, desde ~$10-50/mes
```

**Opción B - Instagrapi (Free pero complejo):**
```python
# pip install instagrapi
from instagrapi import Client

# Requiere:
# - Cuenta real de Instagram
# - Manejo de sesiones
# - Proxies rotativos
# - Delays/rate limiting manual
```

**Opción C - Cloud scraper (Apify):**
```bash
# Apify Instagram Scraper
# Maneja bloqueos automáticamente
# Costo: Desde $49/mes
```

#### 💰 **PRICING:**
- **Instagrapi (self-hosted)**: Free pero requiere infraestructura
- **RapidAPI**: $10-50/mes según volumen
- **Apify**: Desde $49/mes

#### 🚨 **RIESGOS:**
- **Ban de cuenta**: Instagram puede banear cuentas scrapeadoras
- **IP blacklist**: IPs pueden ser bloqueadas permanentemente
- **Legal concerns**: TOS de Instagram prohíben scraping
- **Mantenimiento constante**: Cada actualización de IG rompe el scraper

#### 🚀 **PRIORIDAD:** BAJA-MEDIA - Solo si necesitamos eventos ultra-locales

**RECOMENDACIÓN**: Implementar SOLO si:
1. Ya tenemos las otras 3-4 APIs funcionando
2. Detectamos que nos faltan eventos locales pequeños
3. Estamos dispuestos a mantenerlo activamente
4. Podemos pagar un servicio como RapidAPI (más confiable que self-host)

---

## 🎯 PLAN DE IMPLEMENTACIÓN RECOMENDADO

### ✅ **FASE 1: MVP (Implementar AHORA)**
```bash
1. Ticketmaster Discovery API    # Eventos masivos
2. Mantener Eventbrite scraping  # Eventos variados
3. SeatGeek API                   # Agregador secundario
```

**Resultado esperado**: 3 fuentes de datos robustas, 90% cobertura global

---

### 🔶 **FASE 2: Expansión (Si se necesita más)**
```bash
4. Implementar Meetup API        # Eventos comunitarios
5. Considerar APIs regionales    # Fever, Songkick
```

---

### 🚫 **NO IMPLEMENTAR (Por ahora)**
```bash
❌ PredictHQ - Muy cara ($500/año)
❌ Facebook API - Scraping ya funciona
❌ APIs rotas - 12 scrapers con errores
```

---

## 📝 PASOS SIGUIENTES

### 1. **Ticketmaster Discovery API** (PRIORITARIO)
```bash
# Paso 1: Registrarse
https://developer.ticketmaster.com/

# Paso 2: Obtener API Key
# Paso 3: Crear scraper con requests
# Paso 4: Testear con Moreno, Buenos Aires, Argentina
```

### 2. **SeatGeek API** (SECUNDARIO)
```bash
# Paso 1: Documentación en developer.seatgeek.com
# Paso 2: Verificar si requiere API key
# Paso 3: Implementar como fallback de Ticketmaster
```

### 3. **Limpieza de scrapers rotos**
```bash
# Mover a carpeta _disabled/:
- allevents_scraper.py
- facebook_auth_scraper.py
- residentadvisor_scraper.py
- stubhub_scraper.py
- ticketleap_scraper.py
- ticketmaster_scraper.py (reemplazar con API)
- ticombo_scraper.py
- bandsintown_scraper.py
- dice_scraper.py
- events_scraper.py
- universe_scraper.py
- showpass_scraper.py

# Mantener SOLO los 5 funcionando:
✅ eventbrite_scraper.py
✅ facebook_scraper.py
✅ fever_scraper.py
✅ meetup_scraper.py
✅ songkick_scraper.py
```

---

## 🔍 COMPARACIÓN RÁPIDA

| API | Free Tier | Rate Limits | Cobertura | Calidad | Facilidad | Búsqueda Geo | Prioridad |
|-----|-----------|-------------|-----------|---------|-----------|--------------|-----------|
| **Ticketmaster** | ✅ Sí | 5K/día, 5/seg | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Sí | **ALTA** |
| **Eventbrite** | ✅ Sí | 1K/hora | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Limitada | MEDIA |
| **SeatGeek** | ✅ Probable | ❓ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Sí | **ALTA** |
| **PredictHQ** | ❌ No ($500) | Enterprise | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Sí | BAJA |
| **Meetup** | ✅ Sí | ❓ Bajo | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Sí | MEDIA-BAJA |
| **Bandsintown** | ⚠️ Partner | ❓ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ No | BAJA |
| **Songkick** | ❌ No (Paid) | Comercial | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Sí | BAJA |
| **Dice.fm** | ❌ Partners | ❓ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⚠️ Scraping | BAJA |
| **Resident Advisor** | ❌ No API | N/A | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⚠️ Scraping | MEDIA |
| **Instagram** | ⚠️ RapidAPI | $10-50/mes | ⭐⭐ | ⭐⭐ | ⭐ | ⚠️ Hashtags | BAJA-MEDIA |

---

## 🎯 CONCLUSIÓN

**ESTRATEGIA ÓPTIMA CALIDAD > CANTIDAD:**

### 🚀 **IMPLEMENTAR AHORA (PRIORIDAD ALTA):**
1. **Ticketmaster Discovery API** → Mejor relación calidad/precio (5K/día gratis) ⭐⭐⭐⭐⭐
2. **Mantener Eventbrite scraping** → Ya funciona, usuario confirmó buenos eventos ✅
3. **SeatGeek API** → Agregador de 60+ plataformas, cobertura complementaria

### 🧹 **LIMPIAR (REDUCIR COMPLEJIDAD):**
4. **Desactivar 12 scrapers rotos** → Están ocupando recursos y generando errores
5. **Mantener solo 5 scrapers funcionando** → Eventbrite, Facebook, Fever, Meetup, Songkick

### ❓ **EVALUAR DESPUÉS (Si necesitamos MÁS cobertura):**
6. **Resident Advisor scraping** → Si queremos música electrónica/techno
7. **Meetup API oficial** → Si queremos más eventos comunitarios
8. **Instagram RapidAPI** → SOLO si nos faltan eventos locales (caro, $10-50/mes)

### ❌ **NO IMPLEMENTAR:**
- ❌ PredictHQ ($500/año - muy cara)
- ❌ Songkick (ya no es gratis)
- ❌ Bandsintown (no búsqueda geográfica)
- ❌ Dice.fm (API solo para partners)
- ❌ Instagram self-hosted (muy complejo, alto riesgo de ban)

---

**Resultado esperado con TIER 1:**
- ✅ 3 fuentes robustas de datos (Ticketmaster + Eventbrite + SeatGeek)
- ✅ Cobertura global > 90%
- ✅ **GRATIS** (todo free tier)
- ✅ **Calidad > Cantidad** (eventos verificados, no basura)
- ✅ Mantenimiento bajo (APIs oficiales, no scraping frágil)

---

**📋 RESPUESTA A TU PREGUNTA:**

**Instagram scraping:**
- ✅ **Técnicamente posible** con Instagrapi (Python) o RapidAPI
- ⚠️ **MUY complicado**: Bloqueos cada 2-4 semanas, TLS fingerprinting, proxies requeridos
- 💰 **Opciones viables**: RapidAPI ($10-50/mes) o Apify ($49/mes)
- 🚨 **Riesgos**: Ban de cuenta, IP blacklist, violación TOS Instagram
- 🎯 **Recomendación**: Implementar **SOLO** si las otras 3 APIs no son suficientes

**Bandsintown, Songkick, Dice.fm, Resident Advisor:**
- ⚠️ Todas tienen limitaciones (no free tier, no búsqueda geo, o solo scraping)
- 🎯 **Recomendación**: Ignorar por ahora, enfocarse en las 3 TIER 1

---

**💡 PRÓXIMO PASO INMEDIATO:**

¿Quieres que registremos Ticketmaster API y creemos un scraper de prueba? Es la mejor inversión de tiempo ahora mismo.
