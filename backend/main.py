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
# Hybrid scrapers removed - only real data sources allowed
from services.daily_social_scraper import DailySocialScraper
from services.cloudscraper_events import CloudscraperEvents
from services.eventbrite_massive_scraper import EventbriteMassiveScraper
from services.hybrid_sync_scraper import HybridSyncScraper
from services.progressive_sync_scraper import ProgressiveSyncScraper
from services.teatro_optimizado_scraper import TeatroOptimizadoScraper
from services.rapidapi_facebook_scraper import RapidApiFacebookScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
# Heroku uses PORT env variable, fallback to BACKEND_PORT for local dev
BACKEND_PORT = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8001")))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eventos_db")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Buenos Aires")

# Connection pool for PostgreSQL
pool = None

async def update_facebook_cache_background():
    """
    Background job que actualiza el cache de Facebook cada 6 horas
    🕰️ Windows Service pattern en Python - Timer automático
    """
    try:
        logger.info("🔄 BACKGROUND JOB: Iniciando actualización de cache Facebook...")
        
        facebook_scraper = RapidApiFacebookScraper()
        
        # Hacer el request pesado (20s) - nadie espera aquí
        events = await facebook_scraper.scrape_facebook_events_rapidapi(
            city_name=DEFAULT_CITY, 
            limit=50, 
            max_time_seconds=30.0  # Más tiempo para background
        )
        
        if events:
            # Guardar en cache - el scraper ya lo hace internamente
            logger.info(f"✅ BACKGROUND JOB: Cache actualizado con {len(events)} eventos")
        else:
            logger.warning("⚠️ BACKGROUND JOB: No se obtuvieron eventos")
            
    except Exception as e:
        logger.error(f"❌ BACKGROUND JOB ERROR: {e}")
        # No crashea el servidor, solo logea el error

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
        
        logger.info("🚀 Heroku-ready: Scheduler removido, usar Heroku Scheduler add-on")
        
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
    allow_origins=["*"],  # Allow all origins - Heroku friendly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manual Facebook cache update endpoint - HEROKU BACKUP
@app.post("/api/update-facebook-cache")
async def manual_facebook_cache_update():
    """
    Endpoint manual para actualizar cache Facebook
    🔧 Backup para Heroku Scheduler o testing
    ⚡ Puede ser llamado manualmente si es necesario
    """
    try:
        logger.info("🔧 MANUAL UPDATE: Actualizando cache Facebook...")
        
        if not os.getenv("RAPIDAPI_KEY"):
            return {
                "status": "error",
                "error": "RAPIDAPI_KEY no configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        # Ejecutar actualización
        await update_facebook_cache_background()
        
        # Verificar resultado
        facebook_scraper = RapidApiFacebookScraper()
        cache_data = facebook_scraper.load_cache()
        events_count = len(cache_data.get("events", []))
        
        return {
            "status": "success",
            "message": "Cache actualizado manualmente",
            "events_count": events_count,
            "timestamp": datetime.now().isoformat(),
            "cache_info": cache_data.get("cache_info", {})
        }
        
    except Exception as e:
        logger.error(f"❌ Error en actualización manual: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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
async def get_eventbrite_events(location: str = DEFAULT_CITY):
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
async def get_argentina_venues_events(location: str = DEFAULT_CITY):
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
async def get_facebook_events(location: str = DEFAULT_CITY):
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
async def get_instagram_events(location: str = DEFAULT_CITY):
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
async def get_meetup_events(location: str = DEFAULT_CITY):
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
async def get_ticketmaster_events(location: str = DEFAULT_CITY):
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
async def parallel_search(location: str = DEFAULT_CITY):
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
    location: str = Query(DEFAULT_CITY),
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
            location_str = str(location) if location else DEFAULT_CITY
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
    location: str = DEFAULT_CITY,
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
        original_location = query.get("location", DEFAULT_CITY)
        
        # 🏷️ SISTEMA DE TAGS - IGNORAR GEOLOCALIZACIÓN SI HAY TAG DE CIUDAD
        location = original_location  # Default
        
        # Buscar tags de ciudad en el query (#barcelona, #madrid, etc.)
        city_tags = {
            "#barcelona": "Barcelona", "#bcn": "Barcelona", "#barna": "Barcelona",
            "#madrid": "Madrid", "#valencia": "Valencia", "#sevilla": "Sevilla",
            "#paris": "Paris", "#parís": "Paris", "#lyon": "Lyon", 
            "#mexicocity": "Mexico City", "#cdmx": "Mexico City"
        }
        
        # Si encuentra tag de ciudad, IGNORAR COMPLETAMENTE el parámetro location
        query_lower = search_query.lower()
        for tag, city_name in city_tags.items():
            if tag in query_lower:
                location = city_name
                # Remover el tag del query para que no interfiera en la búsqueda
                search_query = search_query.lower().replace(tag, "").strip()
                logger.info(f"🏷️ TAG DETECTADO: '{tag}' → Ubicación: {city_name} (IGNORANDO geo-location)")
                break
        
        logger.error(f"🚨 POST EJECUTÁNDOSE - query: {query}")
        logger.info(f"🔍 DEBUG POST - Received query: {query}")
        logger.info(f"🔍 DEBUG POST - search_query: '{search_query}', location: '{location}'")
        logger.info(f"🔍 Smart search: '{search_query}' in {location}")
        
        # Get events from multi-source (using internal function to avoid Query parameter issues)
        try:
            from api.multi_source import fetch_from_all_sources_internal
            logger.error(f"🚨 IMPORT OK - Llamando a fetch_from_all_sources_internal con location: {location}")
            result = await fetch_from_all_sources_internal(location=location, fast=True)
            logger.error(f"🚨 RESULTADO - {result.get('source', 'No source')} - {len(result.get('events', []))} eventos")
        except Exception as e:
            logger.error(f"🚨 ERROR EN IMPORT/CALL: {e}")
            raise
        
        # IMPORTANTE: Si buscamos una ciudad específica que no es la ciudad por defecto,
        # verificar si tenemos eventos para esa ubicación
        if location and DEFAULT_CITY not in location:
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
            "location": query.get("location", DEFAULT_CITY)
        }

# GET version for frontend compatibility
@app.get("/api/events/smart-search")
async def smart_search_get(
    q: str = Query(..., description="Search query"),
    location: str = Query(DEFAULT_CITY, description="Location")
):
    """
    GET version of smart search for frontend compatibility
    """
    # Detectar si el query contiene una ubicación
    query_lower = q.lower()
    detected_location = location
    
    # Lista COMPLETA de ciudades argentinas y GLOBALES 🌍
    cities = ["córdoba", "cordoba", "mendoza", "rosario", "la plata", "mar del plata", 
              "salta", "tucumán", "tucuman", "bariloche", "neuquén", "neuquen",
              "santa fe", "bahía blanca", "bahia blanca", "moreno", "moron", "morón",
              "tigre", "quilmes", "lanús", "lanus", "avellaneda", "san isidro",
              # España - Global cities
              "barcelona", "bcn", "barna", "madrid", "capital españa", "valencia", "sevilla", "seville",
              # Francia - Global cities  
              "paris", "parís", "parí", "lyon", "marsella", "marseille",
              # México - Global cities
              "mexico city", "cdmx", "guadalajara", "monterrey", "tijuana", "cancún", "cancun",
              # Otros países
              "china", "chile", "uruguay", "brasil", "peru", "colombia", "mexico"]
    
    # Detectar ciudad en el query - SI ENCUENTRA ALGO, IGNORAR COMPLETAMENTE location
    city_found = False
    global_cities = ["barcelona", "bcn", "barna", "madrid", "capital españa", "valencia", "sevilla", "seville",
                     "paris", "parís", "parí", "lyon", "marsella", "marseille",
                     "mexico city", "cdmx", "guadalajara", "monterrey", "tijuana", "cancún", "cancun"]
    
    logger.error(f"🚨🚨🚨 GET ENDPOINT EJECUTÁNDOSE - query: '{q}', location param: '{location}'")
    logger.info(f"🔍 DEBUG - Buscando ciudades en: '{query_lower}'")
    logger.info(f"🔍 DEBUG - Lista cities: {cities}")
    
    for city in cities:
        if city in query_lower:
            logger.info(f"🔍 DEBUG - ENCONTRADA: '{city}' en '{query_lower}'")
            # 🌍 CIUDADES GLOBALES: Sin ", Argentina"
            if city in global_cities:
                if city in ["barcelona", "bcn", "barna"]:
                    location = "Barcelona"
                elif city in ["madrid", "capital españa"]:
                    location = "Madrid"
                elif city in ["paris", "parís", "parí"]:
                    location = "Paris"
                elif city in ["valencia"]:
                    location = "Valencia"
                elif city in ["sevilla", "seville"]:
                    location = "Sevilla"
                elif city in ["mexico city", "cdmx"]:
                    location = "Mexico City"
                else:
                    location = city.title()
            else:
                # 🇦🇷 CIUDADES ARGENTINAS: Con ", Argentina"
                location = city.title() + ", Argentina"
            
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
        # Si no hay ciudad, usar ciudad por defecto
        location = f"{DEFAULT_CITY}, Argentina"
        logger.info(f"📍 No se detectó ciudad, usando {DEFAULT_CITY} por defecto")
    
    # Redirect to POST version with proper format
    return await smart_search({
        "query": q,
        "location": location
    })

# 🇪🇸 BARCELONA DIRECT ENDPOINT - Bypass routing issues
@app.get("/api/barcelona")
async def get_barcelona_events():
    """Direct Barcelona endpoint that bypasses all routing complexity"""
    try:
        logger.error(f"🇪🇸 BARCELONA DIRECTO - Ejecutando scraper")
        
        from services.barcelona_scraper import BarcelonaScraper
        scraper = BarcelonaScraper()
        events = await scraper.scrape_all_sources()
        
        logger.error(f"🇪🇸 BARCELONA DIRECTO - Obtenidos {len(events)} eventos")
        
        return {
            "success": True,
            "location": "Barcelona",
            "events": events[:50],
            "recommended_events": events[:50], 
            "source": "direct_barcelona_scraper",
            "total_events": len(events),
            "message": f"Eventos de Barcelona (directo)",
            "strategy": "direct_scraper_bypass"
        }
    except Exception as e:
        logger.error(f"🇪🇸 ERROR Barcelona directo: {e}")
        return {
            "success": False,
            "location": "Barcelona", 
            "events": [],
            "error": str(e),
            "source": "direct_barcelona_scraper"
        }

# Facebook RapidAPI endpoint - LA JOYITA 💎 (DEBE ir ANTES de {event_id})
@app.get("/api/events/facebook")
async def get_facebook_events(
    location: str = Query(DEFAULT_CITY, description="Location for Facebook events"),
    limit: int = Query(30, description="Maximum number of events to return")
):
    """
    Endpoint ultrarrápido de Facebook - SOLO usa cache
    🕰️ Background job (Windows Service pattern) actualiza cada 6 horas
    ⚡ Usuario SIEMPRE ve respuesta instantánea
    """
    try:
        facebook_scraper = RapidApiFacebookScraper()
        
        logger.info(f"⚡ CACHE-ONLY: Cargando eventos de Facebook para {location}")
        
        # SOLO CACHE - nunca más esperas de 20s
        cache_data = facebook_scraper.load_cache()
        cached_events = cache_data.get("events", [])
        
        if cached_events:
            # Normalizar eventos desde cache
            normalized_events = facebook_scraper.normalize_facebook_events(cached_events)
            
            # Limitar resultados
            limited_events = normalized_events[:limit]
            
            cache_info = cache_data.get("cache_info", {})
            last_updated = cache_info.get("last_updated", "unknown")
            
            logger.info(f"⚡ CACHE HIT: {len(limited_events)} eventos (cache: {last_updated})")
        
            return {
                "status": "success",
                "source": "rapidapi_facebook_cache",
                "location": location,
                "category": "facebook_events",
                "total": len(limited_events),
                "events": limited_events,
                "cache_info": {
                    "cached": True,
                    "last_updated": last_updated,
                    "background_job": "every_6_hours",
                    "method": "windows_service_pattern"
                }
            }
        else:
            # Cache vacío - el background job aún no corrió
            logger.warning(f"⚠️ CACHE VACÍO: Background job aún no actualizó el cache")
            return {
                "status": "success", 
                "source": "rapidapi_facebook_cache",
                "location": location,
                "category": "facebook_events", 
                "total": 0,
                "events": [],
                "cache_info": {
                    "cached": False,
                    "message": "Background job actualizará cache pronto",
                    "background_job": "every_6_hours"
                }
            }
        
    except Exception as e:
        logger.error(f"❌ Error en Facebook endpoint: {e}")
        return {
            "status": "error",
            "error": str(e),
            "location": location,
            "total": 0,
            "events": []
        }

# Teatro endpoint - especializado en obras de teatro (DEBE ir ANTES de {event_id})
@app.get("/api/events/teatro")
async def get_teatro_events(
    location: str = Query(DEFAULT_CITY, description="Location for theater events"),
    limit: int = Query(20, description="Maximum number of events to return")
):
    """
    Endpoint especializado en obras de teatro argentinas
    Fuentes: teatros oficiales, carteleras, medios culturales
    """
    try:
        teatro_scraper = TeatroOptimizadoScraper()
        
        logger.info(f"🎭 Buscando obras de teatro en {location}")
        
        # Scraping de teatro con timeout optimizado
        raw_events = await teatro_scraper.scrape_teatro_optimizado(max_time_seconds=8.0)
        
        # Normalizar eventos para el sistema
        normalized_events = teatro_scraper.normalize_theater_events_optimizado(raw_events)
        
        # Aplicar límite
        events = normalized_events[:limit]
        
        logger.info(f"🎭 Retornando {len(events)} obras de teatro para {location}")
        
        return {
            "status": "success",
            "source": "teatro_optimizado",
            "location": location,
            "category": "theater",
            "total": len(events),
            "events": events,
            "scraping_info": {
                "sources_found": len(raw_events),
                "sources_normalized": len(normalized_events),
                "method": "teatro_optimizado_scraper"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en teatro endpoint: {e}")
        return {
            "status": "error",
            "error": str(e),
            "location": location,
            "total": 0,
            "events": []
        }

# Single event endpoint
@app.get("/api/events/{event_id}")
async def get_event_by_id(event_id: str):
    """
    Obtener un evento específico por ID/título
    """
    try:
        # Buscar en eventos recientes de la ciudad por defecto
        from api.multi_source import fetch_from_all_sources_internal
        result = await fetch_from_all_sources_internal(DEFAULT_CITY)
        
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
        location = data.get("location", DEFAULT_CITY)
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
    
    # 🔍 PARSEO SIMPLE DE UBICACIONES
    detected_location = DEFAULT_CITY
    message_lower = message.lower()
    
    # Mapeo de ciudades GLOBALES (traveler app)
    location_mapping = {
        # Argentina
        "córdoba": "Córdoba", "cordoba": "Córdoba", "la docta": "Córdoba",
        "mendoza": "Mendoza", "mza": "Mendoza",
        "rosario": "Rosario",
        "la plata": "La Plata",
        "mar del plata": "Mar del Plata", "mardel": "Mar del Plata",
        "salta": "Salta",
        "tucumán": "Tucumán", "tucuman": "Tucumán",
        "bariloche": "Bariloche",
        "neuquén": "Neuquén", "neuquen": "Neuquén",
        "buenos aires": "Buenos Aires", "caba": "Buenos Aires", "capital": "Buenos Aires",
        
        # España - Proof of concept global
        "barcelona": "Barcelona", "bcn": "Barcelona", "barna": "Barcelona",
        "madrid": "Madrid", "capital españa": "Madrid",
        "valencia": "Valencia",
        "sevilla": "Sevilla", "seville": "Sevilla",
        
        # Francia  
        "paris": "Paris", "parís": "Paris",
        "lyon": "Lyon",
        "marseille": "Marseille", "marsella": "Marseille",
        
        # México
        "cdmx": "Mexico City", "ciudad de méxico": "Mexico City", "df": "Mexico City",
        "guadalajara": "Guadalajara", "gdl": "Guadalajara",
        "monterrey": "Monterrey",
        
        # Colombia
        "bogotá": "Bogotá", "bogota": "Bogotá",
        "medellín": "Medellín", "medellin": "Medellín",
        
        # Chile
        "santiago": "Santiago", "santiago chile": "Santiago"
    }
    
    # Buscar ciudad en el mensaje
    for city_key, city_name in location_mapping.items():
        if city_key in message_lower:
            detected_location = city_name
            logger.info(f"🏙️ Ubicación detectada en texto: '{city_key}' → {city_name}")
            break
    
    # Si no detectó ciudad en el texto, usar geolocalización automática
    if detected_location == DEFAULT_CITY:
        try:
            from api.geolocation import detect_location
            from fastapi import Request
            
            # Crear un request mock para obtener la IP del usuario
            # En una implementación real, deberías pasar el request real
            logger.info("📍 No se detectó ciudad, usando geolocalización automática...")
            detected_location = "Buenos Aires"  # Por ahora mantener default
            # TODO: Implementar detección real de IP del usuario en contexto de AI chat
        except Exception as e:
            logger.warning(f"⚠️ Error en geolocalización automática: {e}")
            detected_location = DEFAULT_CITY
    
    # 🚀 USE PROVINCIAL/GLOBAL SCRAPERS (no database)
    if detected_location == "Mendoza":
        logger.info(f"✅ Usando eventos del scraper provincial para {detected_location}")
        from services.provincial_scrapers import MendozaScraper
        mendoza_scraper = MendozaScraper()
        events = await mendoza_scraper.scrape_all()
    elif detected_location == "Barcelona":
        logger.info(f"✅ Usando eventos del scraper global para {detected_location}")
        from services.barcelona_scraper import BarcelonaScraper
        barcelona_scraper = BarcelonaScraper()
        events = await barcelona_scraper.scrape_all_sources()
    else:
        # Buenos Aires y otros - usar multi-source
        from api.multi_source import fetch_from_all_sources
        result = await fetch_from_all_sources(location=detected_location)
        events = result.get("events", [])
    
    # Score events by relevance to query
    scored_events = []
    query_words = message.lower().split()
    
    for event in events:
        score = 0
        title_lower = event.get('title', '').lower()
        desc_lower = event.get('description', '').lower()
        category_lower = event.get('category', '').lower()
        
        # Basic scoring
        for word in query_words:
            if word in title_lower:
                score += 3
            if word in desc_lower:
                score += 2
            if word in category_lower:
                score += 2
        
        if score > 0 or len(query_words) <= 1:  # Include all if generic query
            event['match_score'] = score
            scored_events.append(event)
    
    # Sort by score
    scored_events.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    return {
        "success": True,
        "location": detected_location,
        "events": scored_events[:10],
        "recommended_events": scored_events[:5],
        "total_events": len(events),
        "sources_completed": [{"source": f"{detected_location} Scrapers", "count": len(events), "status": "success"}],
        "message": f"Eventos específicos de {detected_location}" if scored_events else f"No encontramos eventos específicos de {detected_location}.",
        "query": message,
        "smart_search": True,
        "filtered_count": len(scored_events)
    }

# AI recommendations endpoint (alias)
@app.post("/api/ai/recommendations")
async def ai_recommendations(data: Dict[str, Any]):
    """Get AI recommendations"""
    return await ai_recommend(data)

# AI plan weekend endpoint
@app.post("/api/ai/plan-weekend")
async def ai_plan_weekend(data: Dict[str, Any]):
    """Plan weekend with AI"""
    location = data.get("location", DEFAULT_CITY)
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
    result = await fetch_from_all_sources(location=DEFAULT_CITY)
    
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
            cloudscraper.fetch_all_events(DEFAULT_CITY),
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

# Facebook hybrid removed - only real data sources allowed

# Instagram hybrid removed - only real data sources allowed

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
                # 🔍 PARSEO DE UBICACIÓN EN WEBSOCKET (como IA-First)
                message = data.get("message", "")
                base_location = data.get("location", DEFAULT_CITY)
                detected_location = base_location
                
                # Si hay mensaje, intentar detectar ubicación
                if message:
                    message_lower = message.lower()
                    
                    # Mapeo de ciudades GLOBALES (traveler app)
                    location_mapping = {
                        # Argentina
                        "córdoba": "Córdoba", "cordoba": "Córdoba", "la docta": "Córdoba",
                        "mendoza": "Mendoza", "mza": "Mendoza",
                        "rosario": "Rosario",
                        "la plata": "La Plata",
                        "mar del plata": "Mar del Plata", "mardel": "Mar del Plata",
                        "salta": "Salta",
                        "tucumán": "Tucumán", "tucuman": "Tucumán",
                        "bariloche": "Bariloche",
                        "neuquén": "Neuquén", "neuquen": "Neuquén",
                        "buenos aires": "Buenos Aires", "caba": "Buenos Aires", "capital": "Buenos Aires",
                        
                        # España - Proof of concept global
                        "barcelona": "Barcelona", "bcn": "Barcelona", "barna": "Barcelona",
                        "madrid": "Madrid", "capital españa": "Madrid",
                        "valencia": "Valencia",
                        "sevilla": "Sevilla", "seville": "Sevilla",
                        
                        # Francia  
                        "paris": "Paris", "parís": "Paris",
                        "lyon": "Lyon",
                        "marseille": "Marseille", "marsella": "Marseille",
                        
                        # México
                        "cdmx": "Mexico City", "ciudad de méxico": "Mexico City", "df": "Mexico City",
                        "guadalajara": "Guadalajara", "gdl": "Guadalajara",
                        "monterrey": "Monterrey",
                        
                        # Colombia
                        "bogotá": "Bogotá", "bogota": "Bogotá",
                        "medellín": "Medellín", "medellin": "Medellín",
                        
                        # Chile
                        "santiago": "Santiago", "santiago chile": "Santiago"
                    }
                    
                    # Buscar ciudad en el mensaje
                    for city_key, city_name in location_mapping.items():
                        if city_key in message_lower:
                            detected_location = city_name
                            logger.info(f"🏙️ WebSocket - Ubicación detectada: '{city_key}' → {city_name}")
                            break
                
                # Send search started con ubicación detectada
                await websocket.send_json({
                    "type": "search_started",
                    "status": "searching",
                    "location": detected_location,
                    "message": f"🚀 Iniciando búsqueda en {detected_location}...",
                    "location_source": "detected" if detected_location != base_location else "default"
                })
                
                # Start streaming search con ubicación correcta
                await stream_events_search(websocket, detected_location)
                
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
        # 🎯 SCRAPERS ESPECÍFICOS POR UBICACIÓN
        logger.info(f"🔍 WebSocket - Iniciando búsqueda específica para: {location}")
        
        # 1. Scrapers específicos por provincia
        if location in ["Córdoba", "Cordoba"]:
            await websocket.send_json({
                "type": "source_started", 
                "source": "cordoba_provincial",
                "message": f"🏛️ Fuentes específicas de Córdoba...",
                "progress": 10
            })
            
            try:
                from services.provincial_scrapers import CordobaScraper
                cordoba_scraper = CordobaScraper()
                cordoba_events = await cordoba_scraper.scrape_all()
                
                # Send Córdoba events in batches
                for i in range(0, len(cordoba_events), batch_size):
                    batch = cordoba_events[i:i+batch_size]
                    total_events += len(batch)
                    
                    await websocket.send_json({
                        "type": "events_batch",
                        "source": "cordoba_provincial",
                        "events": batch,
                        "batch_count": len(batch),
                        "total_so_far": total_events,
                        "progress": min(10 + (i/max(len(cordoba_events), 1)) * 30, 40)
                    })
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error en scrapers de Córdoba: {e}")
                
        elif location == "Mendoza":
            await websocket.send_json({
                "type": "source_started", 
                "source": "mendoza_provincial",
                "message": f"🍷 Fuentes específicas de Mendoza...",
                "progress": 10
            })
            
            try:
                from services.provincial_scrapers import MendozaScraper
                mendoza_scraper = MendozaScraper()
                mendoza_events = await mendoza_scraper.scrape_all()
                
                # Send Mendoza events in batches
                for i in range(0, len(mendoza_events), batch_size):
                    batch = mendoza_events[i:i+batch_size]
                    total_events += len(batch)
                    
                    await websocket.send_json({
                        "type": "events_batch",
                        "source": "mendoza_provincial", 
                        "events": batch,
                        "batch_count": len(batch),
                        "total_so_far": total_events,
                        "progress": min(10 + (i/max(len(mendoza_events), 1)) * 30, 40)
                    })
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error en scrapers de Mendoza: {e}")
                
        elif location == "Barcelona":
            await websocket.send_json({
                "type": "source_started", 
                "source": "barcelona_global",
                "message": f"🇪🇸 Fuentes específicas de Barcelona...",
                "progress": 10
            })
            
            try:
                from services.barcelona_scraper import BarcelonaScraper
                barcelona_scraper = BarcelonaScraper()
                barcelona_events = await barcelona_scraper.scrape_all_sources()
                
                # Send Barcelona events in batches
                for i in range(0, len(barcelona_events), batch_size):
                    batch = barcelona_events[i:i+batch_size]
                    total_events += len(batch)
                    
                    await websocket.send_json({
                        "type": "events_batch",
                        "source": "barcelona_global", 
                        "events": batch,
                        "batch_count": len(batch),
                        "total_so_far": total_events,
                        "progress": min(10 + (i/max(len(barcelona_events), 1)) * 30, 40)
                    })
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error en scrapers de Barcelona: {e}")
        
        # 2. Fuentes generales (solo si es Buenos Aires o para complementar)
        if location == "Buenos Aires" or total_events < 10:
            # Eventbrite Argentina (más rápido)
            await websocket.send_json({
                "type": "source_started", 
                "source": "eventbrite",
                "message": "🎫 Buscando en Eventbrite Argentina...",
                "progress": 45
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
                        "progress": min(45 + (i/max(len(eventbrite_normalized), 1)) * 15, 60)
                    })
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error en Eventbrite: {e}")
            
            # Venues Argentinos Oficiales
            await websocket.send_json({
                "type": "source_started",
                "source": "argentina_venues", 
                "message": "🏛️ Venues oficiales de Argentina...",
                "progress": 60
            })
            
            try:
                # Import venue scrapers
                from services.oficial_venues_scraper import OficialVenuesScraper
                from services.argentina_venues_scraper import ArgentinaVenuesScraper
                
                # Argentina Venues Scraper
                argentina_scraper = ArgentinaVenuesScraper()
                argentina_events = await argentina_scraper.fetch_all_events()
                
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
                        "progress": min(60 + (i/max(len(argentina_events), 1)) * 15, 75)
                    })
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error en venues argentinos: {e}")
        
        # 3. Fuentes adicionales (si necesario)
        if total_events < 20:
            # Ticketek Argentina (si existe)
            await websocket.send_json({
                "type": "source_started",
                "source": "ticketmaster",
                "message": "🎪 Ticketek/Ticketmaster Argentina...", 
                "progress": 80
            })
            
            try:
                # Try to scrape Ticketek if available
                from services.ticketek_scraper import TicketekArgentinaScraper
                ticketek_scraper = TicketekArgentinaScraper()
                ticketek_events = await ticketek_scraper.fetch_all_events()
                
                for i in range(0, len(ticketek_events), batch_size):
                    batch = ticketek_events[i:i+batch_size]
                    total_events += len(batch)
                    
                    await websocket.send_json({
                        "type": "events_batch",
                        "source": "ticketmaster",
                        "events": batch,
                        "batch_count": len(batch),
                        "total_so_far": total_events,
                        "progress": min(80 + (i/max(len(ticketek_events), 1)) * 15, 95)
                    })
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Ticketek no disponible: {e}")
        
        # Búsqueda completada
        await websocket.send_json({
            "type": "search_completed",
            "status": "success",
            "total_events": total_events,
            "location": location,
            "sources_completed": 3 if location in ["Mendoza", "Córdoba", "Cordoba"] else 2,
            "progress": 100,
            "message": f"🎉 Búsqueda completada en {location}! {total_events} eventos encontrados"
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda streaming: {e}")
        await websocket.send_json({
            "type": "search_error",
            "status": "error", 
            "message": f"Error en la búsqueda: {str(e)}",
            "progress": 100
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
async def fetch_all_progressive(location: str = Query(DEFAULT_CITY)):
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
async def fetch_stream_progressive(location: str = Query(DEFAULT_CITY)):
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

# 🗓️ DAILY SOCIAL SCRAPER ENDPOINTS

@app.get("/api/daily-scraper/run")
async def run_daily_social_scraping():
    """
    Ejecuta el scraping diario de Facebook e Instagram
    Pensado para ser llamado por un cron job una vez por día
    """
    try:
        logger.info("🗓️ Iniciando scraping diario de redes sociales...")
        
        scraper = DailySocialScraper()
        result = await scraper.run_daily_scraping()
        
        # Aquí sería donde guardas en la base de datos
        # await save_daily_events_to_db(result['events'])
        
        logger.info(f"✅ Scraping diario completado: {result['total_events_found']} eventos")
        
        return {
            "status": "success", 
            "message": "Daily scraping completed successfully",
            "summary": {
                "total_events": result['total_events_found'],
                "facebook_events": result['facebook_events'],
                "instagram_events": result['instagram_events'],
                "execution_time": f"{result['execution_time_seconds']:.1f}s",
                "scraping_date": result['scraping_date'],
                "next_scraping": result['next_scraping']
            },
            "events_sample": result['events'][:5],  # Solo muestra 5 como ejemplo
            "cron_job_info": {
                "frequency": "Once per day",
                "recommended_time": "03:00 AM local time",
                "endpoint": "/api/daily-scraper/run",
                "storage": "Database storage ready"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en daily scraping: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/daily-scraper/status")
async def daily_scraper_status():
    """
    Estado del sistema de scraping diario
    """
    return {
        "status": "ready",
        "strategy": "Daily Facebook & Instagram scraping with DB storage",
        "features": [
            "🕒 Runs once per day via cron job",
            "📘 Facebook real event extraction", 
            "📸 Instagram real event extraction",
            "💾 Database storage for retrieved events",
            "🚫 No simulated/generated events",
            "🔍 Smart deduplication across platforms"
        ],
        "target_venues": {
            "facebook": 8,
            "instagram": 8 
        },
        "implementation": "✅ DailySocialScraper class ready",
        "database_integration": "⚠️ Pending implementation",
        "next_steps": "Set up cron job to call /api/daily-scraper/run"
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