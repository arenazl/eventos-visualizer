# 🚀 ESTRATEGIA DE INTEGRACIÓN MASIVA DE EVENTOS

## 📊 APIS DISPONIBLES (CON ACCESO DIRECTO)

### 🎫 APIS PRINCIPALES DE EVENTOS

#### 1. **Eventbrite API** ✅
- **URL**: https://www.eventbrite.com/platform/api
- **Datos**: Eventos públicos, conciertos, conferencias, meetups
- **Cobertura**: Mundial
- **Límite**: 1000 req/hora (gratis), ilimitado (pago)
- **Auth**: OAuth2 / API Key
```python
# Endpoint: https://www.eventbriteapi.com/v3/events/search/
# Filtros: location, date, category, price, format
```

#### 2. **Ticketmaster Discovery API** ✅
- **URL**: https://developer.ticketmaster.com
- **Datos**: Conciertos, deportes, teatro, festivales
- **Cobertura**: América, Europa, Asia
- **Límite**: 5000 req/día (gratis)
- **Auth**: API Key
```python
# Endpoint: https://app.ticketmaster.com/discovery/v2/events
# Incluye: venues, attractions, classifications
```

#### 3. **Meetup API** ⚠️ (Ahora GraphQL)
- **URL**: https://www.meetup.com/api/
- **Datos**: Meetups tech, sociales, profesionales
- **Límite**: Variable
- **Auth**: OAuth2
```graphql
# GraphQL endpoint con eventos locales
```

#### 4. **Facebook Events API** ⚠️ (Restricciones)
- **URL**: https://developers.facebook.com/docs/graph-api/reference/event
- **Datos**: Eventos públicos de páginas
- **Restricción**: Solo eventos de páginas que administras
- **Solución**: Scraping de páginas públicas

#### 5. **SeatGeek API** ✅
- **URL**: https://platform.seatgeek.com
- **Datos**: Deportes, conciertos, teatro
- **Cobertura**: USA principalmente
- **Auth**: Client ID + Secret

#### 6. **PredictHQ API** 💰
- **URL**: https://www.predicthq.com/apis
- **Datos**: Eventos globales, festivales, conferencias
- **Precio**: Desde $99/mes
- **Ventaja**: Data normalizada de múltiples fuentes

#### 7. **Bandsintown API** ✅
- **URL**: https://artists.bandsintown.com/support/api-installation
- **Datos**: Conciertos, tours de artistas
- **Gratis**: Para apps no comerciales
```python
# Endpoint: https://rest.bandsintown.com/artists/{artist}/events
```

#### 8. **Songkick API** ✅
- **URL**: https://www.songkick.com/developer
- **Datos**: Conciertos, festivales musicales
- **Límite**: Por aplicación

#### 9. **StubHub API** 💰
- **URL**: https://developer.stubhub.com
- **Datos**: Eventos con reventa de tickets
- **Auth**: OAuth2

#### 10. **Eventful API** ⚠️ (Deprecated pero funcional)
- **URL**: http://api.eventful.com
- **Datos**: Eventos variados
- **Estado**: No mantenida pero aún funciona

### 🏢 APIS LOCALES ARGENTINA

#### 11. **Gobierno Buenos Aires - Agenda Cultural**
- **URL**: https://data.buenosaires.gob.ar/dataset/agenda-cultural
- **Datos**: Eventos culturales oficiales
- **Formato**: JSON/CSV
- **Gratis**: Sí

#### 12. **Alternativa Teatral API** (No oficial)
- **Scraping necesario**: https://www.alternativateatral.com
- **Datos**: Obras de teatro independiente

#### 13. **Passline** 
- **URL**: https://www.passline.com
- **Datos**: Eventos, fiestas, recitales en Argentina

## 🕷️ ESTRATEGIA DE SCRAPING

### SITIOS PRINCIPALES PARA SCRAPING

#### Argentina 🇦🇷
```python
ARGENTINA_SOURCES = {
    # Teatros
    "teatro_colon": "https://teatrocolon.org.ar/es/calendario",
    "complejo_teatral": "https://complejoteatral.gob.ar",
    "paseo_la_plaza": "https://www.paseolaaplaza.com.ar",
    "teatro_gran_rex": "https://www.teatrogranrex.com.ar",
    
    # Música/Fiestas
    "la_trastienda": "https://www.latrastienda.com",
    "niceto_club": "https://www.nicetoclub.com",
    "luna_park": "https://www.lunapark.com.ar",
    "estadio_obras": "https://www.estadioobras.com.ar",
    
    # Deportes
    "ticketek": "https://www.ticketek.com.ar",
    "platea_net": "https://plateanet.com.ar",
    
    # Culturales
    "centro_cultural_recoleta": "https://www.centroculturalrecoleta.org",
    "usina_del_arte": "https://www.usinadelarte.org",
    "cck": "https://www.cck.gob.ar",
    
    # Agregadores
    "voy_de_viaje": "https://www.voydeviaje.com.ar",
    "buenos_aires_ciudad": "https://turismo.buenosaires.gob.ar/es/events",
    "agenda_cultural": "https://www.buenosaires.gob.ar/cultura/agenda-cultural",
    
    # Revistas/Medios
    "la_nacion_espectaculos": "https://www.lanacion.com.ar/espectaculos/agenda",
    "clarin_espectaculos": "https://www.clarin.com/espectaculos",
    "timeout_ba": "https://www.timeout.com/buenos-aires/things-to-do",
}
```

#### Internacional 🌍
```python
INTERNATIONAL_SOURCES = {
    # Agregadores Globales
    "allevents": "https://allevents.in",
    "eventful": "https://eventful.com",
    "10times": "https://10times.com",  # Conferencias/Expos
    "festicket": "https://www.festicket.com",  # Festivales
    
    # Redes Sociales
    "instagram_events": "Instagram hashtags: #eventosBA #fiestasBA",
    "facebook_pages": "Páginas públicas de venues",
}
```

## 💻 ESTRATEGIA DE IMPLEMENTACIÓN

### 1. **ARQUITECTURA MULTI-FUENTE**

```python
# backend/services/event_aggregator.py

class EventAggregator:
    def __init__(self):
        self.sources = {
            'eventbrite': EventbriteConnector(),
            'ticketmaster': TicketmasterConnector(),
            'seatgeek': SeatGeekConnector(),
            'bandsintown': BandsintownConnector(),
            'gov_ba': GobiernoBsAsConnector(),
            'scraper_teatros': TeatrosScraper(),
            'scraper_venues': VenuesScraper(),
        }
    
    async def fetch_all_events(self, location, date_range):
        """Obtiene eventos de TODAS las fuentes en paralelo"""
        tasks = []
        for source_name, connector in self.sources.items():
            tasks.append(connector.fetch_events(location, date_range))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Normalizar y deduplicar
        all_events = self.normalize_events(results)
        unique_events = self.deduplicate(all_events)
        
        return unique_events
```

### 2. **NORMALIZACIÓN DE DATOS**

```python
# Esquema universal para todos los eventos
class UniversalEvent:
    title: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    venue_name: str
    venue_address: str
    latitude: float
    longitude: float
    category: str  # música, teatro, deportes, etc
    subcategory: str
    price_min: float
    price_max: float
    currency: str
    is_free: bool
    image_url: str
    event_url: str
    source: str  # eventbrite, ticketmaster, scraping_teatro_colon, etc
    source_id: str  # ID original de la fuente
    tags: List[str]
    capacity: int
    available_tickets: int
    artist: str  # Para conciertos
    team_home: str  # Para deportes
    team_away: str  # Para deportes
```

### 3. **SISTEMA DE SCRAPING INTELIGENTE**

```python
# backend/scrapers/smart_scraper.py

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio

class SmartScraper:
    def __init__(self):
        self.browser = None
        
    async def scrape_with_js(self, url):
        """Para sitios con JavaScript pesado"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            await browser.close()
            return BeautifulSoup(content, 'html.parser')
    
    async def scrape_teatro_colon(self):
        """Scraper específico para Teatro Colón"""
        soup = await self.scrape_with_js('https://teatrocolon.org.ar/es/calendario')
        events = []
        
        for event in soup.select('.event-card'):
            events.append({
                'title': event.select_one('.title').text,
                'date': event.select_one('.date').text,
                'venue': 'Teatro Colón',
                'category': 'cultural',
                'subcategory': 'opera' if 'ópera' in title else 'concierto'
            })
        
        return events
```

### 4. **DEDUPLICACIÓN INTELIGENTE**

```python
def deduplicate_events(events):
    """
    Detecta eventos duplicados usando:
    - Similitud de título (fuzzy matching)
    - Mismo venue + fecha cercana
    - Mismo artista + fecha
    """
    from fuzzywuzzy import fuzz
    
    unique = []
    seen = set()
    
    for event in events:
        # Crear firma del evento
        signature = f"{event['venue']}_{event['date']}"
        
        # Buscar duplicados por título similar
        is_duplicate = False
        for unique_event in unique:
            similarity = fuzz.ratio(event['title'], unique_event['title'])
            same_date = event['date'] == unique_event['date']
            same_venue = event['venue'] == unique_event['venue']
            
            if similarity > 85 and same_date and same_venue:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(event)
    
    return unique
```

### 5. **CACHE Y ACTUALIZACIÓN**

```python
# Redis para cache de 30 minutos
CACHE_CONFIG = {
    'eventbrite': 1800,  # 30 min
    'ticketmaster': 1800,
    'scraping': 3600,  # 1 hora para scraping
    'gobierno': 86400,  # 24 horas para datos gobierno
}
```

### 6. **MONITOREO Y FALLBACK**

```python
class SourceMonitor:
    def __init__(self):
        self.health_status = {}
        
    async def check_source_health(self, source_name):
        """Verifica si una fuente está funcionando"""
        try:
            response = await source.test_connection()
            self.health_status[source_name] = 'healthy'
        except:
            self.health_status[source_name] = 'down'
            # Usar fuentes alternativas
            return self.get_fallback_source(source_name)
```

## 🔑 CONFIGURACIÓN DE API KEYS

```env
# .env file
# APIs Principales
EVENTBRITE_API_KEY=your_key_here
EVENTBRITE_PRIVATE_TOKEN=your_token_here
TICKETMASTER_API_KEY=your_key_here
SEATGEEK_CLIENT_ID=your_id_here
SEATGEEK_CLIENT_SECRET=your_secret_here
BANDSINTOWN_APP_ID=your_app_id

# APIs Opcionales (Pagas)
PREDICTHQ_ACCESS_TOKEN=your_token_here
STUBHUB_API_KEY=your_key_here

# Scraping Config
SCRAPING_USER_AGENT="Mozilla/5.0 EventosApp/1.0"
SCRAPING_DELAY_MS=1000  # Delay entre requests
PROXY_URL=http://proxy.com:8080  # Opcional para evitar bloqueos
```

## 🚦 PRIORIDAD DE IMPLEMENTACIÓN

1. **FASE 1 - APIs Gratuitas** (1 semana)
   - ✅ Eventbrite API
   - ✅ Ticketmaster Discovery API
   - ✅ Bandsintown API
   - ✅ Gobierno Buenos Aires

2. **FASE 2 - Scraping Venues Principales** (1 semana)
   - Teatro Colón
   - Luna Park
   - Estadio Obras
   - Niceto Club
   - La Trastienda

3. **FASE 3 - Agregadores** (3 días)
   - AllEvents
   - Timeout Buenos Aires
   - Agenda Cultural BA

4. **FASE 4 - Redes Sociales** (1 semana)
   - Instagram hashtags
   - Facebook páginas públicas
   - Twitter eventos

## 📈 RESULTADO ESPERADO

Con esta estrategia obtendrás:
- **+5000 eventos** por ciudad
- **Cobertura 95%** de eventos públicos
- **Actualización** cada 30 minutos
- **Categorías**: Música, Teatro, Deportes, Cultural, Tech, Fiestas, Conferencias
- **Fuentes**: 15+ APIs y 20+ sitios scrapeados

## 🔧 PRÓXIMOS PASOS

1. Comenzar con Eventbrite + Ticketmaster (ya tienes algo implementado)
2. Agregar Bandsintown para conciertos
3. Implementar scrapers para teatros locales
4. Sistema de deduplicación
5. Cache con Redis
6. Monitoreo de fuentes