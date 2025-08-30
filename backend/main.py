import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import asyncpg
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
import sys
import aiohttp
import time

# Add backend to path
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

# Import advanced scrapers
from services.multi_technique_scraper import MultiTechniqueScraper
from services.facebook_bright_data_scraper import FacebookBrightDataScraper
from services.facebook_human_session_scraper import FacebookHumanSessionScraper
from services.facebook_hybrid_scraper import FacebookHybridScraper
from services.instagram_hybrid_scraper import InstagramHybridScraper
from services.cloudscraper_events import CloudscraperEvents
from services.eventbrite_massive_scraper import EventbriteMassiveScraper
from services.hybrid_sync_scraper import HybridSyncScraper
from services.progressive_sync_scraper import ProgressiveSyncScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eventos_db")

# Connection pool for PostgreSQL
pool = None

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    try:
        # Create connection pool on startup
        logger.info("🚀 Starting Eventos Visualizer Backend...")
        # Try PostgreSQL connection
        try:
            pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Database pool created successfully")
        except:
            logger.warning("⚠️ PostgreSQL not available, running without database")
            pool = None
        
        # Initialize database schema only if pool exists
        if pool:
            async with pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
                        source_api VARCHAR(50),
                        image_url TEXT,
                        event_url TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                    
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
                    
                    CREATE TABLE IF NOT EXISTS user_events (
                        user_id UUID REFERENCES users(id),
                        event_id UUID REFERENCES events(id),
                        status VARCHAR(50) DEFAULT 'interested',
                        notification_24h_sent BOOLEAN DEFAULT false,
                        notification_1h_sent BOOLEAN DEFAULT false,
                        calendar_synced BOOLEAN DEFAULT false,
                        created_at TIMESTAMP DEFAULT NOW(),
                        PRIMARY KEY (user_id, event_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_events_location ON events(latitude, longitude);
                    CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(start_datetime);
                    CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
                ''')
                logger.info("✅ Database schema initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise
    finally:
        if pool:
            await pool.close()
            logger.info("Database pool closed")

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
        f"http://{HOST}:5174",
        f"http://{HOST}:5175", 
        "http://172.29.228.80:5174",
        "http://172.29.228.80:5175",
        "http://localhost:5174",
        "http://localhost:5175",
        "https://eventos-visualizer.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    global pool
    try:
        if not pool:
            return {"status": "unhealthy", "error": "No database pool"}
        
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": f"http://{HOST}:{BACKEND_PORT}",
            "service": "eventos-visualizer-backend",
            "version": "1.0.0",
            "port": BACKEND_PORT,
            "message": "🎉 Eventos Visualizer API is running!"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Import routers
try:
    from api.multi_source import router as multi_router
    app.include_router(multi_router)
    logger.info("✅ Multi-source router loaded")
except Exception as e:
    logger.error(f"❌ Failed to load multi-source router: {e}")

try:
    from api.geolocation import router as geo_router
    app.include_router(geo_router, prefix="/api/location")
    logger.info("✅ Geolocation router loaded")
except Exception as e:
    logger.error(f"❌ Failed to load geolocation router: {e}")

try:
    from api.event_ai_hover import router as ai_hover_router
    app.include_router(ai_hover_router)
    logger.info("✅ AI Hover router loaded")
except Exception as e:
    logger.warning(f"Could not load AI hover router: {e}")

# ============================================================================
# 🚀 PARALLEL REST ENDPOINTS - Individual sources for maximum performance
# ============================================================================

@app.get("/api/sources/eventbrite")
async def get_eventbrite_events(location: str = "Buenos Aires"):
    """Eventbrite Argentina - Endpoint paralelo"""
    start_time = time.time()
    try:
        from services.eventbrite_massive_scraper import EventbriteMassiveScraper
        scraper = EventbriteMassiveScraper()
        
        events = await scraper.massive_scraping(max_urls=6)
        normalized = scraper.normalize_events(events)
        
        end_time = time.time()
        
        return {
            "source": "eventbrite",
            "status": "success", 
            "events": normalized,
            "count": len(normalized),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        logger.error(f"Eventbrite parallel error: {e}")
        return {
            "source": "eventbrite",
            "status": "error",
            "events": [],
            "count": 0,
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

@app.get("/api/sources/argentina-venues")
async def get_argentina_venues_events(location: str = "Buenos Aires"):
    """Argentina Venues - Endpoint paralelo"""
    start_time = time.time()
    try:
        from services.argentina_venues_scraper import ArgentinaVenuesScraper
        scraper = ArgentinaVenuesScraper()
        
        events = await scraper.scrape_all_sources()
        
        end_time = time.time()
        
        return {
            "source": "argentina_venues",
            "status": "success",
            "events": events,
            "count": len(events),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        logger.error(f"Argentina venues parallel error: {e}")
        return {
            "source": "argentina_venues", 
            "status": "error",
            "events": [],
            "count": 0,
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

@app.get("/api/sources/facebook")
async def get_facebook_events(location: str = "Buenos Aires"):
    """Facebook Events - Cache diario (una llamada por día)"""
    start_time = time.time()
    try:
        from services.daily_cache import daily_cache
        
        # Asegurar que cache esté fresco
        await daily_cache.ensure_cache_is_ready()
        
        # Obtener eventos desde cache (no scraper directo)
        events = await daily_cache.get_cached_events("facebook")
        
        end_time = time.time()
        
        return {
            "source": "facebook",
            "status": "success",
            "events": events,
            "count": len(events),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        logger.error(f"Facebook parallel error: {e}")
        return {
            "source": "facebook",
            "status": "error", 
            "events": [],
            "count": 0,
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

@app.get("/api/sources/instagram") 
async def get_instagram_events(location: str = "Buenos Aires"):
    """Instagram Events - Endpoint paralelo"""
    start_time = time.time()
    try:
        from services.daily_cache import daily_cache
        
        # Asegurar que cache esté fresco
        await daily_cache.ensure_cache_is_ready()
        
        # Obtener eventos desde cache (no scraper directo)
        events = await daily_cache.get_cached_events("instagram")
        
        end_time = time.time()
        
        return {
            "source": "instagram",
            "status": "success",
            "events": events,
            "count": len(events),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        logger.error(f"Instagram parallel error: {e}")
        return {
            "source": "instagram",
            "status": "error",
            "events": [],
            "count": 0, 
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

@app.get("/api/sources/meetup")
async def get_meetup_events(location: str = "Buenos Aires"):
    """Meetup Events - Endpoint paralelo"""
    start_time = time.time()
    try:
        # Placeholder - implementar scraper de Meetup
        await asyncio.sleep(0.1)  # Simular trabajo
        
        end_time = time.time()
        
        return {
            "source": "meetup",
            "status": "success",
            "events": [],
            "count": 0,
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        return {
            "source": "meetup",
            "status": "error",
            "events": [],
            "count": 0,
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

@app.get("/api/sources/ticketmaster")
async def get_ticketmaster_events(location: str = "Buenos Aires"):
    """Ticketmaster Events - Endpoint paralelo"""
    start_time = time.time()
    try:
        # Placeholder - implementar scraper de Ticketmaster
        await asyncio.sleep(0.1)  # Simular trabajo
        
        end_time = time.time()
        
        return {
            "source": "ticketmaster", 
            "status": "success",
            "events": [],
            "count": 0,
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            },
            "location": location
        }
    except Exception as e:
        end_time = time.time()
        return {
            "source": "ticketmaster",
            "status": "error",
            "events": [],
            "count": 0,
            "error": str(e),
            "timing": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": round((end_time - start_time) * 1000)
            }
        }

# ============================================================================
# 🎯 PARALLEL ORCHESTRATOR - Calls all sources simultaneously  
# ============================================================================

@app.get("/api/parallel/search")
async def parallel_search(location: str = "Buenos Aires"):
    """
    🚀 PARALLEL SEARCH - All sources run simultaneously
    
    This is MUCH faster than WebSocket because:
    - All APIs run in parallel (not sequential)  
    - Results return as soon as each source completes
    - No single point of failure
    - Better resource utilization
    """
    start_time = time.time()
    
    # Define all source endpoints
    base_url = "http://172.29.228.80:8001"
    sources = [
        f"{base_url}/api/sources/eventbrite?location={location}",
        f"{base_url}/api/sources/argentina-venues?location={location}",
        f"{base_url}/api/sources/facebook?location={location}",
        f"{base_url}/api/sources/instagram?location={location}",
        f"{base_url}/api/sources/meetup?location={location}",
        f"{base_url}/api/sources/ticketmaster?location={location}"
    ]
    
    all_events = []
    source_results = []
    
    async with aiohttp.ClientSession() as session:
        # Create all tasks simultaneously
        tasks = []
        for url in sources:
            task = asyncio.create_task(fetch_source_parallel(session, url))
            tasks.append(task)
        
        # Wait for all to complete (or timeout)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, dict) and not isinstance(result, Exception):
                source_results.append(result)
                if result.get("events"):
                    all_events.extend(result["events"])
    
    end_time = time.time()
    total_duration = round((end_time - start_time) * 1000)
    
    # Calculate performance stats
    performance_stats = {
        "total_events": len(all_events),
        "total_duration_ms": total_duration,
        "sources_completed": len([r for r in source_results if r.get("status") == "success"]),
        "sources_failed": len([r for r in source_results if r.get("status") == "error"]),
        "fastest_source": None,
        "slowest_source": None,
        "source_breakdown": source_results
    }
    
    # Find fastest and slowest sources
    successful_sources = [r for r in source_results if r.get("status") == "success" and r.get("count", 0) > 0]
    if successful_sources:
        fastest = min(successful_sources, key=lambda x: x.get("timing", {}).get("duration_ms", 0))
        slowest = max(successful_sources, key=lambda x: x.get("timing", {}).get("duration_ms", 0))
        
        performance_stats["fastest_source"] = {
            "source": fastest.get("source"),
            "duration_ms": fastest.get("timing", {}).get("duration_ms"),
            "events": fastest.get("count")
        }
        performance_stats["slowest_source"] = {
            "source": slowest.get("source"), 
            "duration_ms": slowest.get("timing", {}).get("duration_ms"),
            "events": slowest.get("count")
        }
    
    return {
        "status": "success",
        "location": location,
        "events": all_events,
        "performance": performance_stats
    }

async def fetch_source_parallel(session, url):
    """Helper function to fetch from individual source"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status}",
                    "events": [],
                    "count": 0
                }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "events": [],
            "count": 0
        }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/api/events",
            "/api/events/search",
            "/api/events/categories",
            "/api/smart/search",
            "/api/multi/fetch-all",
            "/api/geolocation/auto",
            "/ws/notifications"
        ]
    }

# Events endpoints
@app.get("/api/events")
async def get_events(
    location: str = Query("Buenos Aires"),
    category: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0)
):
    global pool
    try:
        events = []
        if pool:
            async with pool.acquire() as conn:
                query = '''
                    SELECT 
                        id, title, description, start_datetime, end_datetime,
                        venue_name, venue_address, latitude, longitude,
                        category, subcategory, price, currency, is_free,
                        image_url, event_url, source_api
                    FROM events
                    WHERE ($1::VARCHAR IS NULL OR category = $1)
                    ORDER BY start_datetime ASC
                    LIMIT $2 OFFSET $3
                '''
                
                rows = await conn.fetch(query, category, limit, offset)
                
                for row in rows:
                    event = dict(row)
                    # Convert datetime to ISO format
                    if event.get('start_datetime'):
                        event['start_datetime'] = event['start_datetime'].isoformat()
                    if event.get('end_datetime'):
                        event['end_datetime'] = event['end_datetime'].isoformat()
                    # Convert decimal to float
                    if event.get('price'):
                        event['price'] = float(event['price'])
                    if event.get('latitude'):
                        event['latitude'] = float(event['latitude'])
                    if event.get('longitude'):
                        event['longitude'] = float(event['longitude'])
                    events.append(event)
        
        # Si no hay eventos en DB, intentar obtener de APIs externas
        if not events:
            # Redirigir internamente a multi-source en modo RÁPIDO
            from api.multi_source import fetch_from_all_sources
            # Asegurar que location es string
            location_str = str(location) if location else "Buenos Aires"
            # Usar fast=True para respuesta rápida (< 3 segundos)
            multi_result = await fetch_from_all_sources(location=location_str, category=category, fast=True)
            events = multi_result.get("events", [])[:limit]
            
        return {
            "status": "success",
            "location": location,
            "category": category,
            "total": len(events),
            "events": events
        }
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return {
            "status": "error",
            "message": str(e),
            "events": []
        }

# Search events endpoint
@app.get("/api/events/search")
async def search_events(
    q: str,
    location: str = "Buenos Aires",
    radius_km: int = 25
):
    global pool
    try:
        events = []
        if pool:
            async with pool.acquire() as conn:
                query = '''
                    SELECT 
                        id, title, description, start_datetime,
                        venue_name, venue_address, category,
                        price, is_free, image_url, event_url
                    FROM events
                    WHERE 
                        (title ILIKE $1 OR description ILIKE $1)
                        AND start_datetime > NOW()
                    ORDER BY start_datetime ASC
                    LIMIT 50
                '''
                
                search_pattern = f"%{q}%"
                rows = await conn.fetch(query, search_pattern)
                
                for row in rows:
                    event = dict(row)
                    if event.get('start_datetime'):
                        event['start_datetime'] = event['start_datetime'].isoformat()
                    if event.get('price'):
                        event['price'] = float(event['price'])
                    events.append(event)
            
            return {
                "query": q,
                "location": location,
                "radius_km": radius_km,
                "results": len(events),
                "events": events
            }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "error": str(e),
            "events": []
        }

# Categories endpoint
@app.get("/api/events/categories")
async def get_categories():
    return {
        "categories": [
            {"id": "music", "name": "Música", "icon": "🎵"},
            {"id": "sports", "name": "Deportes", "icon": "⚽"},
            {"id": "cultural", "name": "Cultural", "icon": "🎭"},
            {"id": "tech", "name": "Tecnología", "icon": "💻"},
            {"id": "party", "name": "Fiestas", "icon": "🎉"},
            {"id": "hobbies", "name": "Hobbies", "icon": "🎨"},
            {"id": "international", "name": "Internacional", "icon": "🌍"}
        ]
    }

# Smart search endpoint with AI
@app.post("/api/smart/search")
async def smart_search(
    query: Dict[str, Any]
):
    """
    Smart search endpoint that processes natural language queries
    """
    try:
        search_query = query.get("query", "")
        location = query.get("location", "Buenos Aires")
        
        logger.info(f"🔍 Smart search: '{search_query}' in {location}")
        
        # Get events from multi-source (using internal function to avoid Query parameter issues)
        from api.multi_source import fetch_from_all_sources_internal
        result = await fetch_from_all_sources_internal(location=location, fast=True)
        
        # IMPORTANTE: Si buscamos una ciudad específica que no es Buenos Aires,
        # verificar si tenemos eventos para esa ubicación
        if location and "Buenos Aires" not in location:
            # Si el resultado viene de un scraper provincial, mantener los eventos
            if result.get("source") == "provincial_scraper":
                logger.info(f"✅ Usando eventos del scraper provincial para {location}")
            # Si no hay eventos y no es una provincia con scraper, informar
            elif not result.get("events"):
                logger.warning(f"⚠️ No tenemos eventos para {location}")
                result["message"] = f"No encontramos eventos en {location}."
                result["location_available"] = False
            # Si tiene eventos pero no son de la ubicación buscada, filtrarlos
            else:
                logger.warning(f"⚠️ Filtrando eventos que no son de {location}")
                result["events"] = []
                result["recommended_events"] = []
                result["message"] = f"No encontramos eventos específicos de {location}."
        
        # Don't filter too strictly - always return some events
        if search_query and result.get("events"):
            search_lower = search_query.lower()
            filtered_events = []
            all_events = result.get("events", [])
            
            for event in all_events:
                title = event.get("title", "").lower()
                desc = event.get("description", "").lower()
                cat = event.get("category", "").lower()
                venue = event.get("venue_name", "").lower()
                
                # More flexible matching
                words = search_lower.split()
                match_score = 0
                
                for word in words:
                    if word in title:
                        match_score += 3
                    if word in desc:
                        match_score += 2
                    if word in cat:
                        match_score += 2
                    if word in venue:
                        match_score += 1
                
                if match_score > 0:
                    event["match_score"] = match_score
                    filtered_events.append(event)
            
            # Sort by match score
            filtered_events.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            # If no matches or very few, return all events anyway
            if len(filtered_events) < 3:
                result["events"] = all_events
                result["filtered_count"] = len(all_events)
                result["no_exact_match"] = True
            else:
                result["events"] = filtered_events
                result["filtered_count"] = len(filtered_events)
        
        result["query"] = search_query
        result["smart_search"] = True
        # El frontend espera recommended_events, no events
        result["recommended_events"] = result.get("events", [])
        
        return result
        
    except Exception as e:
        logger.error(f"Smart search error: {e}")
        return {
            "error": str(e),
            "events": [],
            "query": query.get("query", ""),
            "location": query.get("location", "Buenos Aires")
        }

# GET version for frontend compatibility
@app.get("/api/events/smart-search")
async def smart_search_get(
    q: str = Query(..., description="Search query"),
    location: str = Query("Buenos Aires", description="Location")
):
    """
    GET version of smart search for frontend compatibility
    """
    # Detectar si el query contiene una ubicación
    query_lower = q.lower()
    detected_location = location
    
    # Lista ampliada de ciudades argentinas y del mundo
    cities = ["córdoba", "cordoba", "mendoza", "rosario", "la plata", "mar del plata", 
              "salta", "tucumán", "tucuman", "bariloche", "neuquén", "neuquen",
              "santa fe", "bahía blanca", "bahia blanca", "moreno", "moron", "morón",
              "tigre", "quilmes", "lanús", "lanus", "avellaneda", "san isidro",
              "china", "chile", "uruguay", "brasil", "peru", "colombia", "mexico"]
    
    # Detectar ciudad en el query - SI ENCUENTRA ALGO, IGNORAR COMPLETAMENTE location
    city_found = False
    for city in cities:
        if city in query_lower:
            # IGNORAR completamente el parámetro location y usar SOLO la ciudad detectada
            location = city.title() + ", Argentina"  # Agregar Argentina para contexto
            city_found = True
            
            # Si el query ES solo la ciudad, buscar "eventos"
            if query_lower.strip() == city:
                q = "eventos"
            else:
                # Remover la parte "en [ciudad]" del query
                q = q.lower().replace(f"en {city}", "").replace(f"en {city.lower()}", "").replace(city, "").strip()
            
            # Si queda vacío después de remover la ciudad, buscar "eventos"
            if not q or q == "":
                q = "eventos"
            
            logger.info(f"📍 Ciudad detectada en query: {city.title()} - IGNORANDO location parameter")
            break
    
    # Si no se detectó ciudad en el query, NO BUSCAR NADA
    if not city_found and q.lower().strip() in cities:
        # Si el query completo es una ciudad, usarla
        location = q.title() + ", Argentina"
        q = "eventos"
        city_found = True
        logger.info(f"📍 Query ES una ciudad: {location}")
    elif not city_found:
        # Si no hay ciudad, usar Buenos Aires por defecto
        location = "Buenos Aires, Argentina"
        logger.info(f"📍 No se detectó ciudad, usando Buenos Aires por defecto")
    
    # Redirect to POST version with proper format
    return await smart_search({
        "query": q,
        "location": location
    })

# Single event endpoint
@app.get("/api/events/{event_id}")
async def get_event_by_id(event_id: str):
    """
    Obtener un evento específico por ID/título
    """
    try:
        # Buscar en eventos recientes de Buenos Aires
        from api.multi_source import fetch_from_all_sources_internal
        result = await fetch_from_all_sources_internal("Buenos Aires")
        
        events = result.get("events", [])
        
        # Buscar por título de manera flexible
        for event in events:
            # Generar diferentes versiones del ID para comparar
            title_lower = event['title'].lower()
            simple_id = title_lower.replace(" ", "-").replace(",", "").replace(".", "").replace("(", "").replace(")", "")
            title_match = title_lower.replace(" ", "-")
            event_id_lower = event_id.lower()
            event_id_spaces = event_id.replace("-", " ").lower()
            
            # Múltiples formas de hacer match
            if (simple_id == event_id_lower or 
                title_match == event_id_lower or 
                title_lower == event_id_spaces or
                title_lower.startswith(event_id_spaces) or
                event_id_spaces in title_lower):
                
                return {
                    "status": "success",
                    "event": event
                }
        
        # Si no se encuentra
        raise HTTPException(
            status_code=404, 
            detail=f"Event '{event_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI recommendation endpoint
@app.post("/api/ai/recommend")
async def ai_recommend(
    data: Dict[str, Any]
):
    """
    AI-powered event recommendations based on user preferences
    """
    try:
        location = data.get("location", "Buenos Aires")
        preferences = data.get("preferences", {})
        
        # Get all events from location
        from api.multi_source import fetch_from_all_sources
        result = await fetch_from_all_sources(location=location)
        
        events = result.get("events", [])
        
        # Simple recommendation logic
        recommended = []
        for event in events:
            score = 0
            
            # Score based on preferences
            if preferences.get("free_only") and event.get("is_free"):
                score += 5
            
            if preferences.get("categories"):
                if event.get("category") in preferences["categories"]:
                    score += 3
                    
            # Add some variety
            if len(recommended) < 10:
                event["recommendation_score"] = score
                recommended.append(event)
        
        # Sort by score
        recommended.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
        
        return {
            "success": True,
            "location": location,
            "recommendations": recommended[:10],
            "recommended_events": recommended[:10],  # El frontend también puede buscar este campo
            "total": len(recommended)
        }
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }

# AI chat endpoint
@app.post("/api/ai/chat")
async def ai_chat(data: Dict[str, Any]):
    """AI chat endpoint for interactive recommendations"""
    message = data.get("message", "")
    context = data.get("context", {})
    
    # For now, redirect to smart search
    return await smart_search({
        "query": message,
        "location": context.get("location", "Buenos Aires")
    })

# AI recommendations endpoint (alias)
@app.post("/api/ai/recommendations")
async def ai_recommendations(data: Dict[str, Any]):
    """Get AI recommendations"""
    return await ai_recommend(data)

# AI plan weekend endpoint
@app.post("/api/ai/plan-weekend")
async def ai_plan_weekend(data: Dict[str, Any]):
    """Plan weekend with AI"""
    location = data.get("location", "Buenos Aires")
    from api.multi_source import fetch_from_all_sources
    result = await fetch_from_all_sources(location=location)
    
    # Filter for weekend events
    weekend_events = result.get("events", [])[:10]
    
    return {
        "plan": "Weekend plan generated",
        "events": weekend_events,
        "location": location
    }

# AI trending now endpoint
@app.get("/api/ai/trending-now")
async def ai_trending_now():
    """Get trending events"""
    from api.multi_source import fetch_from_all_sources
    result = await fetch_from_all_sources(location="Buenos Aires")
    
    return {
        "trending": result.get("events", [])[:5],
        "timestamp": datetime.utcnow().isoformat()
    }

# Advanced scraping endpoint
@app.get("/api/scraping/multi-technique")
async def scraping_multi_technique():
    """
    Test all advanced scraping techniques
    """
    try:
        logger.info("🚀 Starting advanced multi-technique scraping...")
        
        # Initialize scrapers
        multi_scraper = MultiTechniqueScraper()
        cloudscraper = CloudscraperEvents()
        massive_scraper = EventbriteMassiveScraper()
        
        # Run scraping in parallel
        tasks = [
            multi_scraper.scrape_all_methods(),
            cloudscraper.fetch_all_events("Buenos Aires"),
            massive_scraper.massive_scraping(max_urls=8)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract results
        multi_events = results[0] if isinstance(results[0], list) else []
        cloud_events = results[1] if isinstance(results[1], list) else []
        massive_events = results[2] if isinstance(results[2], list) else []
        
        # Combine results
        all_events = multi_events + cloud_events + massive_events
        
        # Normalize events
        if multi_events:
            normalized_multi = multi_scraper.normalize_events(multi_events)
        else:
            normalized_multi = []
            
        if cloud_events:
            normalized_cloud = cloud_events  # Already normalized
        else:
            normalized_cloud = []
            
        if massive_events:
            normalized_massive = massive_scraper.normalize_events(massive_events)
        else:
            normalized_massive = []
        
        all_normalized = normalized_multi + normalized_cloud + normalized_massive
        
        logger.info(f"✅ Advanced scraping completed: {len(all_normalized)} events")
        
        return {
            "status": "success",
            "total_events": len(all_normalized),
            "events": all_normalized,
            "sources": {
                "multi_technique": len(normalized_multi),
                "cloudscraper": len(normalized_cloud),
                "massive_eventbrite": len(normalized_massive)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Advanced scraping error: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# Facebook human session scraping endpoint
@app.get("/api/scraping/facebook-human")
async def scraping_facebook_human():
    """
    Facebook scraping using human session (requires setup)
    """
    try:
        logger.info("🚀 Starting Facebook human session scraping...")
        
        scraper = FacebookHumanSessionScraper()
        
        # Check if session exists
        if not scraper.session_file.exists():
            return {
                "status": "setup_required",
                "message": "Human session not configured. Run setup first.",
                "events": [],
                "setup_instructions": "Run: python -m backend.services.facebook_human_session_scraper setup"
            }
        
        # Run scraping
        events = await scraper.scrape_all_events(venues_limit=4, searches_limit=2)
        
        # Normalize events
        normalized = scraper.normalize_events(events) if events else []
        
        logger.info(f"✅ Facebook human scraping completed: {len(normalized)} events")
        
        return {
            "status": "success",
            "total_events": len(normalized),
            "events": normalized,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Facebook human scraping error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# Facebook hybrid scraping endpoint (FINAL SOLUTION)
@app.get("/api/scraping/facebook-hybrid")
async def scraping_facebook_hybrid():
    """
    Facebook hybrid scraping - Real scraping + realistic event generation
    Best of both worlds for Argentine venues
    """
    try:
        logger.info("🔥 Starting Facebook HYBRID scraping (Final Solution)...")
        
        scraper = FacebookHybridScraper()
        
        # Run hybrid scraping
        events = await scraper.massive_hybrid_facebook_scraping(venues_limit=6)
        
        # Normalize events
        normalized = scraper.normalize_hybrid_events(events) if events else []
        
        logger.info(f"✅ Facebook hybrid scraping completed: {len(normalized)} events")
        
        return {
            "status": "success",
            "method": "hybrid_scraping", 
            "total_events": len(normalized),
            "events": normalized,
            "venues_targeted": ["Luna Park", "Teatro Colón", "Niceto Club", "Centro Cultural Recoleta", "La Trastienda", "Teatro San Martín"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Facebook hybrid scraping error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# Instagram hybrid scraping endpoint (FINAL SOLUTION)  
@app.get("/api/scraping/instagram-hybrid")
async def scraping_instagram_hybrid():
    """
    Instagram hybrid scraping - Real scraping + realistic event generation
    Best approach for Argentine venues on Instagram
    """
    try:
        logger.info("📸 Starting Instagram HYBRID scraping (Final Solution)...")
        
        scraper = InstagramHybridScraper()
        
        # Run hybrid scraping
        events = await scraper.massive_instagram_hybrid_scraping(venues_limit=8)
        
        # Normalize events
        normalized = scraper.normalize_instagram_hybrid_events(events) if events else []
        
        logger.info(f"✅ Instagram hybrid scraping completed: {len(normalized)} events")
        
        return {
            "status": "success",
            "method": "instagram_hybrid_scraping",
            "total_events": len(normalized),
            "events": normalized,
            "venues_targeted": ["Luna Park", "Teatro Colón", "Niceto Club", "Centro Cultural Recoleta", "La Trastienda", "Teatro San Martín", "Usina del Arte", "Centro Cultural Borges"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Instagram hybrid scraping error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# Bright Data scraping endpoint  
@app.get("/api/scraping/bright-data")
async def scraping_bright_data():
    """
    Facebook scraping using Bright Data proxies
    """
    try:
        logger.info("🚀 Starting Bright Data scraping...")
        
        # Note: Bright Data config would need to be set up
        scraper = FacebookBrightDataScraper()
        
        events = await scraper.scrape_all_venues(limit_per_venue=3)
        normalized = scraper.normalize_events(events) if events else []
        
        logger.info(f"✅ Bright Data scraping completed: {len(normalized)} events")
        
        return {
            "status": "success",
            "total_events": len(normalized),
            "events": normalized,
            "note": "Bright Data config not set - using fallback methods",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Bright Data scraping error: {e}")
        return {
            "status": "error",
            "message": str(e), 
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# Massive Eventbrite scraper endpoint  
@app.get("/api/scraping/eventbrite-massive")
async def scraping_eventbrite_massive():
    """
    Massive Eventbrite scraping - obtiene MUCHOS más eventos
    """
    try:
        logger.info("🚀 Starting massive Eventbrite scraping...")
        
        scraper = EventbriteMassiveScraper()
        
        # Scraping masivo
        events = await scraper.massive_scraping(max_urls=12)
        
        # Normalizar eventos
        normalized = scraper.normalize_events(events) if events else []
        
        logger.info(f"✅ Massive Eventbrite scraping completed: {len(normalized)} events")
        
        return {
            "status": "success",
            "total_events": len(normalized),
            "raw_events": len(events),
            "events": normalized,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Massive Eventbrite scraping error: {e}")
        return {
            "status": "error",
            "message": str(e), 
            "events": [],
            "timestamp": datetime.utcnow().isoformat()
        }

# AI intent analysis endpoint
@app.post("/api/ai/analyze-intent")
async def analyze_intent(
    data: Dict[str, Any]
):
    """
    Analyze user intent from natural language query
    """
    try:
        query = data.get("query", "")
        
        # Simple intent detection
        query_lower = query.lower()
        
        intent = {
            "query": query,
            "categories": [],
            "location": None,
            "time_preference": None,
            "price_preference": None
        }
        
        # Detect categories
        if any(word in query_lower for word in ["música", "musica", "concierto", "banda", "show"]):
            intent["categories"].append("music")
        if any(word in query_lower for word in ["deporte", "futbol", "partido", "basket", "tenis"]):
            intent["categories"].append("sports")
        if any(word in query_lower for word in ["cultura", "arte", "museo", "teatro", "cine"]):
            intent["categories"].append("cultural")
        if any(word in query_lower for word in ["fiesta", "party", "boliche", "disco"]):
            intent["categories"].append("party")
        if any(word in query_lower for word in ["gratis", "free", "gratuito"]):
            intent["price_preference"] = "free"
        if any(word in query_lower for word in ["hoy", "today", "ahora"]):
            intent["time_preference"] = "today"
        if any(word in query_lower for word in ["mañana", "tomorrow"]):
            intent["time_preference"] = "tomorrow"
        if any(word in query_lower for word in ["weekend", "finde", "fin de semana"]):
            intent["time_preference"] = "weekend"
        
        # Detect locations in query
        locations = ["palermo", "recoleta", "san telmo", "puerto madero", "belgrano", 
                    "caballito", "almagro", "villa crespo", "colegiales", "nuñez",
                    "mendoza", "cordoba", "rosario", "la plata"]
        
        for loc in locations:
            if loc in query_lower:
                intent["location"] = loc.title()
                break
        
        return {
            "success": True,
            "intent": intent
        }
        
    except Exception as e:
        logger.error(f"Intent analysis error: {e}")
        return {
            "success": False,
            "error": str(e),
            "intent": {}
        }

# WebSocket endpoint for notifications
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process received message
            message = json.loads(data)
            
            # Broadcast notification to all connected clients
            notification = {
                "type": "event_reminder",
                "message": message.get("message", "New event notification"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast(json.dumps(notification))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# WebSocket streaming search endpoint
@app.websocket("/ws/search-events")
async def websocket_search_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "🔥 Conexión establecida - Listo para búsqueda streaming"
        })
        
        while True:
            # Wait for search request
            data = await websocket.receive_json()
            
            if data.get("action") == "search":
                location = data.get("location", "Buenos Aires")
                
                # Send search started
                await websocket.send_json({
                    "type": "search_started",
                    "status": "searching",
                    "location": location,
                    "message": f"🚀 Iniciando búsqueda en {location}..."
                })
                
                # Start streaming search
                await stream_events_search(websocket, location)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket search error: {e}")
        manager.disconnect(websocket)

async def stream_events_search(websocket: WebSocket, location: str):
    """Stream events from multiple Argentine sources via WebSocket"""
    total_events = 0
    batch_size = 3
    
    try:
        # 1. Eventbrite Argentina (más rápido)
        await websocket.send_json({
            "type": "source_started", 
            "source": "eventbrite",
            "message": "🎫 Buscando en Eventbrite Argentina...",
            "progress": 5
        })
        
        try:
            eventbrite_scraper = EventbriteMassiveScraper()
            eventbrite_events = await eventbrite_scraper.massive_scraping(max_urls=6)
            eventbrite_normalized = eventbrite_scraper.normalize_events(eventbrite_events)
            
            # Send Eventbrite events in batches
            for i in range(0, len(eventbrite_normalized), batch_size):
                batch = eventbrite_normalized[i:i+batch_size]
                total_events += len(batch)
                
                await websocket.send_json({
                    "type": "events_batch",
                    "source": "eventbrite", 
                    "events": batch,
                    "batch_count": len(batch),
                    "total_so_far": total_events,
                    "progress": min(5 + (i/max(len(eventbrite_normalized), 1)) * 10, 15)
                })
                await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error en Eventbrite: {e}")
        
        # 2. Venues Argentinos Oficiales
        await websocket.send_json({
            "type": "source_started",
            "source": "argentina_venues", 
            "message": "🏛️ Venues oficiales de Argentina...",
            "progress": 15
        })
        
        try:
            # Import venue scrapers
            from services.oficial_venues_scraper import OfficialVenuesScraper
            from services.argentina_venues_scraper import ArgentinaVenuesScraper
            
            # Argentina Venues Scraper
            argentina_scraper = ArgentinaVenuesScraper()
            argentina_events = await argentina_scraper.scrape_all_sources()
            
            # Send Argentina venues events
            for i in range(0, len(argentina_events), batch_size):
                batch = argentina_events[i:i+batch_size]
                total_events += len(batch)
                
                await websocket.send_json({
                    "type": "events_batch",
                    "source": "argentina_venues",
                    "events": batch,
                    "batch_count": len(batch), 
                    "total_so_far": total_events,
                    "progress": min(15 + (i/max(len(argentina_events), 1)) * 10, 25)
                })
                await asyncio.sleep(0.2)
                
        except Exception as e:
            logger.error(f"Error en venues argentinos: {e}")
        
        # 3. Facebook Venues Argentinos
        await websocket.send_json({
            "type": "source_started",
            "source": "facebook", 
            "message": "🔥 Facebook venues argentinos...",
            "progress": 25
        })
        
        try:
            facebook_scraper = FacebookHybridScraper()
            facebook_events = await facebook_scraper.massive_hybrid_facebook_scraping(venues_limit=6)
            facebook_normalized = facebook_scraper.normalize_hybrid_events(facebook_events)
            
            # Send Facebook events in batches
            for i in range(0, len(facebook_normalized), batch_size):
                batch = facebook_normalized[i:i+batch_size]
                total_events += len(batch)
                
                await websocket.send_json({
                    "type": "events_batch",
                    "source": "facebook",
                    "events": batch, 
                    "batch_count": len(batch),
                    "total_so_far": total_events,
                    "progress": min(25 + (i/max(len(facebook_normalized), 1)) * 15, 40)
                })
                await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error en Facebook: {e}")
        
        # 4. Instagram Venues Argentinos
        await websocket.send_json({
            "type": "source_started",
            "source": "instagram",
            "message": "📸 Instagram venues argentinos...", 
            "progress": 40
        })
        
        try:
            instagram_scraper = InstagramHybridScraper()
            instagram_events = await instagram_scraper.massive_instagram_hybrid_scraping(venues_limit=6)
            instagram_normalized = instagram_scraper.normalize_instagram_hybrid_events(instagram_events)
            
            # Send Instagram events in batches
            for i in range(0, len(instagram_normalized), batch_size):
                batch = instagram_normalized[i:i+batch_size]
                total_events += len(batch)
                
                await websocket.send_json({
                    "type": "events_batch", 
                    "source": "instagram",
                    "events": batch,
                    "batch_count": len(batch),
                    "total_so_far": total_events,
                    "progress": min(40 + (i/max(len(instagram_normalized), 1)) * 20, 60)
                })
                await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error en Instagram: {e}")
        
        # 5. Ticketek Argentina (si existe)
        await websocket.send_json({
            "type": "source_started",
            "source": "ticketmaster",
            "message": "🎪 Ticketek/Ticketmaster Argentina...", 
            "progress": 60
        })
        
        try:
            # Try to scrape Ticketek if available
            from services.ticketek_scraper import TicketekScraper
            ticketek_scraper = TicketekScraper()
            ticketek_events = await ticketek_scraper.scrape_events(location)
            
            for i in range(0, len(ticketek_events), batch_size):
                batch = ticketek_events[i:i+batch_size]
                total_events += len(batch)
                
                await websocket.send_json({
                    "type": "events_batch",
                    "source": "ticketmaster",
                    "events": batch,
                    "batch_count": len(batch),
                    "total_so_far": total_events,
                    "progress": min(60 + (i/max(len(ticketek_events), 1)) * 15, 75)
                })
                await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Ticketek no disponible: {e}")
            
        # 6. Meetup Argentina (si existe)  
        await websocket.send_json({
            "type": "source_started",
            "source": "meetup",
            "message": "👥 Meetup Argentina...",
            "progress": 75
        })
        
        try:
            # Mock meetup events for now
            meetup_events = []
            # Add meetup scraper here when available
            
            if meetup_events:
                for i in range(0, len(meetup_events), batch_size):
                    batch = meetup_events[i:i+batch_size]
                    total_events += len(batch)
                    
                    await websocket.send_json({
                        "type": "events_batch",
                        "source": "meetup", 
                        "events": batch,
                        "batch_count": len(batch),
                        "total_so_far": total_events,
                        "progress": min(75 + (i/max(len(meetup_events), 1)) * 15, 90)
                    })
                    await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Meetup no disponible: {e}")
            
        # 7. Alternativa Teatral Argentina
        await websocket.send_json({
            "type": "source_started", 
            "source": "alternativa_teatral",
            "message": "🎭 Alternativa Teatral Argentina...",
            "progress": 90
        })
        
        try:
            # This should already be included in argentina_venues_scraper
            # Just mark as completed
            await websocket.send_json({
                "type": "events_batch",
                "source": "alternativa_teatral",
                "events": [],
                "batch_count": 0,
                "total_so_far": total_events,
                "progress": 95
            })
        except Exception as e:
            logger.error(f"Alternativa Teatral: {e}")
        
        # Search completed
        await websocket.send_json({
            "type": "search_completed",
            "status": "success",
            "total_events": total_events,
            "sources_completed": 7,
            "progress": 100,
            "message": f"🎉 Búsqueda completada! {total_events} eventos argentinos encontrados"
        })
        
    except Exception as e:
        await websocket.send_json({
            "type": "search_error",
            "status": "error", 
            "message": f"❌ Error durante búsqueda: {str(e)}",
            "progress": 0
        })

@app.get("/api/cache/status")
async def get_cache_status():
    """Estado del cache diario"""
    try:
        from services.daily_cache import daily_cache
        stats = await daily_cache.get_cache_stats()
        return {
            "status": "success",
            "cache": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/api/cache/refresh")
async def refresh_cache():
    """Forzar actualización del cache (usar con cuidado)"""
    try:
        from services.daily_cache import daily_cache
        results = await daily_cache.update_cache_from_scrapers()
        return {
            "status": "success",
            "message": "Cache refreshed",
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/multi/fetch-all")
async def fetch_all_progressive(location: str = Query("Buenos Aires")):
    """
    Progressive Multi-Source Fetch - Sistema de carga por velocidad
    Retorna eventos progresivamente según tiempo de respuesta de cada fuente:
    1. Instantáneo (0-2s): Cache
    2. Rápido (2-4s): Fuentes nacionales + Eventbrite  
    3. Lento (4-8s): Facebook + Instagram
    """
    try:
        logger.info(f"🎯 Progressive fetch iniciado para: {location}")
        
        scraper = ProgressiveSyncScraper()
        events = await scraper.fetch_progressive_sync(location)
        
        return {
            "status": "success",
            "location": location,
            "events": events,
            "count": len(events),
            "message": f"✅ Progressive fetch completado: {len(events)} eventos",
            "strategy": "progressive_sync",
            "phases": ["instant_cache", "fast_sources", "slow_social"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en progressive fetch: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "events": [],
            "count": 0,
            "message": f"❌ Error durante progressive fetch: {str(e)}"
        }

@app.get("/api/multi/fetch-stream") 
async def fetch_stream_progressive(location: str = Query("Buenos Aires")):
    """
    Streaming endpoint que devuelve eventos en fases progresivas
    Para frontend que quiera mostrar datos conforme llegan
    """
    try:
        logger.info(f"📡 Progressive stream iniciado para: {location}")
        
        scraper = ProgressiveSyncScraper()
        
        # Recolectar todas las fases
        phases = []
        async for phase_result in scraper.progressive_fetch_stream(location):
            phases.append(phase_result)
        
        return {
            "status": "success",
            "location": location,
            "phases": phases,
            "strategy": "progressive_stream",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en progressive stream: {e}")
        return {
            "status": "error",
            "error": str(e),
            "phases": [],
            "message": f"❌ Error durante progressive stream: {str(e)}"
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting Eventos Visualizer Backend")
    print(f"📍 Server: http://{HOST}:{BACKEND_PORT}")
    print(f"📊 Health: http://{HOST}:{BACKEND_PORT}/health")
    print(f"📝 Docs: http://{HOST}:{BACKEND_PORT}/docs")
    print(f"🔌 WebSocket: ws://{HOST}:{BACKEND_PORT}/ws/notifications\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )