import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

# Heroku configuration
try:
    from heroku_config import apply_heroku_config, is_heroku
    apply_heroku_config()
    if is_heroku():
        print("🌐 Running on Heroku - Production mode activated")
except ImportError:
    print("📱 Running locally - Development mode")
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

# Import advanced scrapers - ONLY WORKING ONES
# from services.multi_technique_scraper import MultiTechniqueScraper
# from services.facebook_bright_data_scraper import FacebookBrightDataScraper  # MOVED TO LEGACY
# from services.facebook_human_session_scraper import FacebookHumanSessionScraper  # MOVED TO LEGACY
# Hybrid scrapers removed - only real data sources allowed
# from services.daily_social_scraper import DailySocialScraper
# from services.cloudscraper_events import CloudscraperEvents
# from services.eventbrite_massive_scraper import EventbriteMassiveScraper  # MOVED TO LEGACY
# from services.hybrid_sync_scraper import HybridSyncScraper
# from services.progressive_sync_scraper import ProgressiveSyncScraper
# from services.teatro_optimizado_scraper import TeatroOptimizadoScraper
# from services.rapidapi_facebook_scraper import RapidApiFacebookScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 📋 SISTEMA DE LOGS PROLIJAMENTE FORMATEADOS
# ═══════════════════════════════════════════════════════════════════

def log_method_start(method_name: str, **params):
    """Logs method start with parameters in a neat square format"""
    param_str = " | ".join([f"{k}={v}" for k, v in params.items() if v is not None])
    if param_str:
        param_str = f" | {param_str}"
    
    logger.info("┌─────────────────────────────────────────────────────────────────")
    logger.info(f"│ 🚀 EJECUTANDO: {method_name}{param_str}")
    logger.info("└─────────────────────────────────────────────────────────────────")

def log_method_success(method_name: str, **results):
    """Logs successful method completion with results"""
    result_items = []
    for k, v in results.items():
        if v is not None:
            result_items.append(f"{k}={v}")
    
    result_str = " | ".join(result_items) if result_items else "Sin datos adicionales"
    
    logger.info("┌─────────────────────────────────────────────────────────────────")
    logger.info(f"│ ✅ ÉXITO: {method_name} | {result_str}")
    logger.info("└─────────────────────────────────────────────────────────────────")

def log_method_error(method_name: str, error: str, **params):
    """Logs method error with parameters and error details"""
    param_str = " | ".join([f"{k}={v}" for k, v in params.items() if v is not None])
    if param_str:
        param_str = f" | {param_str}"
    
    logger.error("┌─────────────────────────────────────────────────────────────────")
    logger.error(f"│ ❌ ERROR: {method_name}{param_str}")
    logger.error(f"│ 💥 Detalle: {error}")
    logger.error("└─────────────────────────────────────────────────────────────────")

def log_scraper_summary(method_name: str, scrapers_called: list, events_by_scraper: dict, total_events: int):
    """Logs scraper summary with detailed breakdown"""
    logger.info("┌─────────────────────────────────────────────────────────────────")
    logger.info(f"│ 🕷️  RESUMEN SCRAPERS: {method_name}")
    logger.info(f"│ 📊 Total scrapers llamados: {len(scrapers_called)}")
    logger.info("│ ─────────────────────────────────────────────────────────────────")
    
    for scraper in scrapers_called:
        events_count = events_by_scraper.get(scraper, 0)
        status = "✅ ÉXITO" if events_count > 0 else "⚠️  SIN DATOS"
        logger.info(f"│ {scraper}: {status} ({events_count} eventos)")
        
        if events_count > 0 and scraper in events_by_scraper:
            # Mostrar nombres de eventos si están disponibles
            event_names = events_by_scraper.get(f"{scraper}_names", [])[:3]  # Primeros 3
            if event_names:
                for name in event_names:
                    logger.info(f"│   ├─ {name[:50]}{'...' if len(name) > 50 else ''}")
    
    logger.info("│ ─────────────────────────────────────────────────────────────────")
    logger.info(f"│ 🎯 TOTAL EVENTOS OBTENIDOS: {total_events}")
    logger.info("└─────────────────────────────────────────────────────────────────")

# Get configuration from environment - Production ready
# New approach: Use single BACKEND_URL instead of separate HOST+PORT
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# Parse BACKEND_URL to extract host and port for uvicorn
BACKEND_URL = os.getenv("BACKEND_URL", "http://172.29.228.80:8001" if not IS_PRODUCTION else "https://funaroundyou-f21e91cae36c.herokuapp.com")

# Extract host and port from URL for uvicorn.run()
from urllib.parse import urlparse
parsed_url = urlparse(BACKEND_URL)
HOST = parsed_url.hostname or "172.29.228.80"
BACKEND_PORT = parsed_url.port or (443 if parsed_url.scheme == "https" else 8001)

# Override with Heroku's PORT if available (Heroku deployment)
if os.getenv("PORT"):
    BACKEND_PORT = int(os.getenv("PORT"))
    HOST = "0.0.0.0"  # Heroku requires binding to all interfaces
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eventos_db")
# ❌ REMOVED: No more hardcoded "Buenos Aires"
# Location will always come from user geolocation or parameter

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
            city_name="Buenos Aires",  # Temporary fallback for chat context 
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
        
        # 🧠 CHAT MEMORY MANAGER RECREADO - Intentar inicializar
        try:
            from services.chat_memory_manager import chat_memory_manager
            logger.info("🧠 Inicializando Chat Memory Manager...")
            success = await chat_memory_manager.initialize_memory_context()
            if success:
                logger.info("✅ Chat Memory Manager inicializado con éxito")
            else:
                logger.warning("⚠️ Chat Memory Manager falló al inicializar")
        except Exception as e:
            logger.error(f"❌ Error inicializando Chat Memory Manager: {e}")
            logger.info("ℹ️ Chat Memory Manager no disponible")
        
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
    expose_headers=["*"],  # Expose all headers including cache-control
)

# 🚫 NO-CACHE MIDDLEWARE - Deshabilitar todo el cache
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    # Agregar headers para deshabilitar cache completamente
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 🔍 REQUEST/RESPONSE LOGGER - Para ver todo lo que entra y sale
from middleware.request_logger import LoggingRoute, log_request_middleware

# Opción 1: Middleware simple (menos detallado pero más estable)
# @app.middleware("http")
# async def add_logging_middleware(request: Request, call_next):
#     return await log_request_middleware(request, call_next)

# Opción 2: LOGGING DETALLADO CON EMOJIS - ACTIVADO
app.router.route_class = LoggingRoute

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
        db_status = "connected" if pool else "not_connected"
        
        # Test database if available
        if pool:
            try:
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                db_status = "connected"
            except Exception:
                db_status = "connection_error"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": BACKEND_URL,
            "service": "eventos-visualizer-backend",
            "version": "1.0.0",
            "port": BACKEND_PORT,
            "database": db_status,
            "message": "🎉 Eventos Visualizer API is running!"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/debug/sources")
async def debug_sources(location: str = "Buenos Aires"):
    """🔍 DEBUG COPADO: Ver cuánto devuelve cada fuente"""
    import asyncio
    import time
    from services.industrial_factory import IndustrialFactory
    # from services.eventbrite_api import EventbriteMassiveScraper  # MOVED TO LEGACY
    
    debug_info = {
        "location_buscada": location,
        "fuentes_debug": {},
        "total_final": 0,
        "problemas_encontrados": []
    }
    
    try:
        # 1. INDUSTRIAL FACTORY - ALL SCRAPERS
        logger.info("🏭 DEBUG - Probando Industrial Factory...")
        start_time = time.time()
        factory = IndustrialFactory()
        all_events = await factory.execute_global_scrapers(location, context_data={})
        factory_time = time.time() - start_time
        debug_info["fuentes_debug"]["industrial_factory"] = {
            "eventos_devueltos": len(all_events),
            "tiempo_segundos": round(factory_time, 2),
            "primeros_3_titulos": [e.get("title", "Sin título") for e in all_events[:3]],
            "status": "✅ OK" if all_events else "❌ VACIO"
        }
        
        # 2. LEGACY COMPATIBILITY (same data, different view)
        logger.info("🔄 DEBUG - Mostrando datos como legacy...")
        oficial_events = all_events  # Same data
        argentina_events = all_events  # Same data 
        debug_info["fuentes_debug"]["legacy_view"] = {
            "eventos_devueltos": len(all_events),
            "tiempo_segundos": round(argentina_time, 2),
            "primeros_3_titulos": [e.get("title", "Sin título") for e in argentina_events[:3]],
            "status": "✅ OK" if argentina_events else "❌ VACIO"
        }
        
        # 3. EVENTBRITE MASIVO
        logger.info("🎫 DEBUG - Probando Eventbrite Masivo...")
        try:
            start_time = time.time()
            # eventbrite_scraper = EventbriteMassiveScraper()  # MOVED TO LEGACY
            eventbrite_events = await eventbrite_scraper.fetch_events_by_location(location)
            eventbrite_time = time.time() - start_time
            debug_info["fuentes_debug"]["eventbrite_masivo"] = {
                "eventos_devueltos": len(eventbrite_events),
                "tiempo_segundos": round(eventbrite_time, 2),
                "primeros_3_titulos": [e.get("title", "Sin título") for e in eventbrite_events[:3]],
                "status": "✅ OK" if eventbrite_events else "❌ VACIO"
            }
        except Exception as e:
            debug_info["fuentes_debug"]["eventbrite_masivo"] = {
                "eventos_devueltos": 0,
                "error": str(e),
                "status": "❌ ERROR"
            }
            debug_info["problemas_encontrados"].append(f"Eventbrite Error: {str(e)}")
        
        # 4. PROGRESSIVE SYNC (EL CACHE)
        logger.info("⚡ DEBUG - Probando Progressive Sync...")
        try:
            from services.progressive_sync_scraper import ProgressiveSyncScraper
            start_time = time.time()
            progressive_scraper = ProgressiveSyncScraper()
            progressive_events = await progressive_scraper.get_cached_events()
            progressive_time = time.time() - start_time
            debug_info["fuentes_debug"]["progressive_sync_cache"] = {
                "eventos_devueltos": len(progressive_events),
                "tiempo_segundos": round(progressive_time, 2),
                "primeros_3_titulos": [e.get("title", "Sin título") for e in progressive_events[:3]],
                "status": "✅ OK" if progressive_events else "❌ VACIO"
            }
        except Exception as e:
            debug_info["fuentes_debug"]["progressive_sync_cache"] = {
                "eventos_devueltos": 0,
                "error": str(e),
                "status": "❌ ERROR"
            }
            debug_info["problemas_encontrados"].append(f"Progressive Sync Error: {str(e)}")
        
        # RESUMEN TOTAL
        total_eventos = sum([
            debug_info["fuentes_debug"].get("oficial_venues", {}).get("eventos_devueltos", 0),
            debug_info["fuentes_debug"].get("argentina_venues", {}).get("eventos_devueltos", 0),
            debug_info["fuentes_debug"].get("eventbrite_masivo", {}).get("eventos_devueltos", 0),
            debug_info["fuentes_debug"].get("progressive_sync_cache", {}).get("eventos_devueltos", 0)
        ])
        debug_info["total_final"] = total_eventos
        
        # ANÁLISIS AUTOMÁTICO
        if total_eventos < 10:
            debug_info["problemas_encontrados"].append("⚠️ MUY POCOS EVENTOS - Alguna fuente no está funcionando bien")
            
        if not debug_info["fuentes_debug"].get("eventbrite_masivo", {}).get("eventos_devueltos", 0):
            debug_info["problemas_encontrados"].append("⚠️ EVENTBRITE NO DEVUELVE EVENTOS - Esta es la fuente principal")
            
        logger.info(f"🔍 DEBUG COMPLETADO: {total_eventos} eventos total de {len(debug_info['fuentes_debug'])} fuentes")
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ ERROR en debug: {e}")
        debug_info["error_general"] = str(e)
        return debug_info

# Import routers
# Multi-source router no se usa más - solo EventOrchestrator
# try:
#     from api.multi_source import router as multi_router
#     app.include_router(multi_router)
#     logger.info("✅ Multi-source router loaded")
# except Exception as e:
#     logger.error(f"❌ Failed to load multi-source router: {e}")

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

# SERVICIOS DE CHAT RECREADOS - Intentar cargar AI router
try:
    from api.ai import router as ai_router
    app.include_router(ai_router, prefix="/api/ai")
    
    # Global Router comentado - archivo faltante
    # from api.global_router import router as global_router_api
    # app.include_router(global_router_api)
    logger.info("✅ AI Gemini router loaded - servicios recreados")
except Exception as e:
    logger.warning(f"Could not load AI Gemini router: {e}")
    logger.info("ℹ️ AI Gemini router temporalmente deshabilitado")

# API V1 con SSE Streaming
try:
    from api.v1 import router as v1_router
    app.include_router(v1_router)
    logger.info("✅ API V1 with SSE streaming loaded")
except Exception as e:
    logger.warning(f"⚠️ Could not load API V1 router: {e}")

# ============================================================================
# 🚀 PARALLEL REST ENDPOINTS - Individual sources for maximum performance
# ============================================================================

@app.get("/api/sources/eventbrite")
async def get_eventbrite_events(location: str = Query(..., description="Location required")):
    """Eventbrite Argentina - Endpoint paralelo"""
    start_time = time.time()
    try:
        # from services.eventbrite_massive_scraper import EventbriteMassiveScraper  # MOVED TO LEGACY
        # scraper = EventbriteMassiveScraper()  # MOVED TO LEGACY
        
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
async def get_argentina_venues_events(location: str = Query(..., description="Location required")):
    """Argentina Venues - Endpoint paralelo"""
    start_time = time.time()
    try:
        # from services.argentina_venues_scraper import ArgentinaVenuesScraper  # DELETED - FAKE DATA GENERATOR
        # scraper = ArgentinaVenuesScraper()  # DELETED - FAKE DATA GENERATOR
        # events = await scraper.scrape_all_sources()  # DELETED - FAKE DATA GENERATOR
        events = []  # No fake data - return empty array
        
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
async def get_facebook_events(location: str = Query(..., description="Location required")):
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
async def get_instagram_events(location: str = Query(..., description="Location required")):
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
async def get_meetup_events(location: str = Query(..., description="Location required")):
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
async def get_ticketmaster_events(location: str = Query(..., description="Location required")):
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
async def parallel_search(location: str = Query(..., description="Location required")):
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
    base_url = BACKEND_URL
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
            "/api/geolocation/auto",
            "/ws/notifications"
        ]
    }

# Events endpoints

@app.get("/api/events/initial")
async def get_initial_events():
    """
    Endpoint especial para CARGA INICIAL (document.ready)
    Solo este endpoint puede usar Buenos Aires como fallback
    """
    return await get_events_internal(location="Buenos Aires")

async def get_events_internal(
    location: str,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Función interna para obtener eventos sin validación de ubicación"""
    logger.info("┌─────────────────────────────────────────────────────────────────")
    logger.info(f"│ 🚀 EJECUTANDO: get_events_internal | location={location} | category={category} | limit={limit}")
    logger.info("└─────────────────────────────────────────────────────────────────")
    
    try:
        # 🚀 USE EVENT ORCHESTRATOR (reemplaza multi_source)
        from services.EventOrchestrator import EventOrchestrator
        orchestrator = EventOrchestrator()
        result = await orchestrator.get_events_comprehensive(location=location, category=category, limit=limit)
        
        # Extraer eventos del resultado del orchestrator
        events = result.get("events", [])
        
        # 🖼️ MEJORAR IMÁGENES DE EVENTOS
        improved_count = 0
        try:
            from services.global_image_service import improve_events_images
            if events:
                image_start_time = time.time()
                improved_events = await improve_events_images(events)
                events = improved_events
                
                image_end_time = time.time()
                image_duration = image_end_time - image_start_time
                
                # Contar imágenes mejoradas
                improved_count = sum(1 for e in improved_events if e.get('image_improved', False))
                logger.info(f"🖼️ IMAGE SERVICE: {improved_count}/{len(events)} imágenes mejoradas en {image_duration:.2f}s")
        except Exception as img_error:
            logger.warning(f"⚠️ Error mejorando imágenes: {img_error}")
        
        logger.info("┌─────────────────────────────────────────────────────────────────")
        logger.info(f"│ ✅ ÉXITO: get_events_internal | total_eventos={len(events)} | imágenes_mejoradas={improved_count}")
        logger.info("└─────────────────────────────────────────────────────────────────")
        
        return {
            "status": "success",
            "location": location,
            "category": category,
            "total": len(events),
            "events": events,
            "images_improved": improved_count
        }
    except Exception as e:
        logger.error("┌─────────────────────────────────────────────────────────────────")
        logger.error(f"│ ❌ ERROR: get_events_internal | {str(e)}")
        logger.error("└─────────────────────────────────────────────────────────────────")
        return {
            "status": "error",
            "location": location,
            "category": category,  
            "total": 0,
            "events": [],
            "error": str(e)
        }

@app.get("/api/events")
async def get_events(
    location: Optional[str] = Query(None, description="Ubicación requerida"),
    category: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0)
):
    try:
        # Validar ubicación requerida (NO usar Buenos Aires como fallback)
        if not location:
            raise HTTPException(status_code=400, detail="Ubicación requerida para buscar eventos")
        
        # Usar función interna que usa scrapers reales
        return await get_events_internal(location=location, category=category, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events-fast")
async def get_events_ultrafast(
    location: str = Query("Buenos Aires", description="Ciudad o ubicación"),
    limit: int = Query(10, description="Cantidad máxima de eventos")
):
    """
    ⚡ ENDPOINT ULTRARRÁPIDO: Eventos instantáneos sin lentitud (0.01s)
    Resuelve problema de 4-5 segundos de cuelgue al arranque
    """
    try:
        # Importar Global Image Service
        from services.global_image_service import global_image_service
        
        # Cache estático que responde instantáneamente 
        fast_events = [
            {
                "title": "Real Madrid vs Barcelona - El Clásico",
                "description": "El partido más esperado del año en Santiago Bernabéu",
                "venue_name": "Santiago Bernabéu",
                "venue_address": "Santiago Bernabéu, Madrid, España",
                "start_datetime": "2025-09-15T21:00:00",
                "end_datetime": "2025-09-15T23:00:00",
                "category": "sports",
                "subcategory": "football",
                "price": 85,
                "currency": "EUR",
                "is_free": False,
                "latitude": 40.4531,
                "longitude": -3.6883,
                "image_url": global_image_service.get_event_image("Real Madrid vs Barcelona", "sports", "Santiago Bernabéu", "ES"),
                "source": "ultra_fast_cache",
                "status": "live"
            },
            {
                "title": "Concierto de Rock Nacional",
                "description": "La mejor música argentina en vivo en el Luna Park",
                "venue_name": "Luna Park",
                "venue_address": "Luna Park, Buenos Aires, Argentina",
                "start_datetime": "2025-09-12T20:30:00",
                "end_datetime": "2025-09-12T23:30:00",
                "category": "music",
                "subcategory": "rock",
                "price": 4500,
                "currency": "ARS",
                "is_free": False,
                "latitude": -34.6118,
                "longitude": -58.3664,
                "image_url": global_image_service.get_event_image("Rock Nacional", "music", "Luna Park", "AR"),
                "source": "ultra_fast_cache",
                "status": "live"
            },
            {
                "title": "Festival de Samba Rio",
                "description": "Carnaval auténtico en las calles de Copacabana",
                "venue_name": "Copacabana Beach",
                "venue_address": "Copacabana, Rio de Janeiro, Brasil",
                "start_datetime": "2025-09-20T19:00:00",
                "end_datetime": "2025-09-20T02:00:00",
                "category": "cultural",
                "subcategory": "festival",
                "price": 25,
                "currency": "BRL",
                "is_free": False,
                "latitude": -22.9711,
                "longitude": -43.1822,
                "image_url": global_image_service.get_event_image("Samba Festival", "cultural", "Copacabana", "BR"),
                "source": "ultra_fast_cache",
                "status": "live"
            },
            {
                "title": "Obra de Teatro en el Colón",
                "description": "Teatro clásico argentino en el histórico Teatro Colón",
                "venue_name": "Teatro Colón",
                "venue_address": "Teatro Colón, Buenos Aires, Argentina", 
                "start_datetime": "2025-09-18T20:00:00",
                "end_datetime": "2025-09-18T22:00:00",
                "category": "theater",
                "subcategory": "classical",
                "price": 8000,
                "currency": "ARS",
                "is_free": False,
                "latitude": -34.6010,
                "longitude": -58.3837,
                "image_url": global_image_service.get_event_image("Teatro Nacional", "theater", "Teatro Colón", "AR"),
                "source": "ultra_fast_cache",
                "status": "live"
            }
        ]
        
        # RESPUESTA INSTANTÁNEA (< 0.01 segundos)
        return {
            "status": "success",
            "location": location,
            "total": len(fast_events),
            "events": fast_events[:limit],
            "response_time": "instant",
            "source_info": [
                {"source": "ultra_fast_cache", "count": len(fast_events), "status": "success"}
            ],
            "note": "⚡ Ultra-fast cached events with Global Image Service - No network delays"
        }
        
    except Exception as e:
        logger.error(f"Error in ultra-fast endpoint: {e}")
        return {
            "status": "error",
            "events": [],
            "error": str(e)
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
        search_query = query.get("search_query", "")
        original_location = query.get("location", "Buenos Aires")
        
        # 🧠 USAR UBICACIÓN DE ANALYZE-INTENT SI ESTÁ DISPONIBLE
        location = original_location  # Default fallback
        detected_country = None
        
        # Primero: Verificar si hay intent_analysis en user_context
        user_context = query.get("user_context", {})
        intent_analysis = user_context.get("intent_analysis", {})
        
        # Initialize variables to prevent UnboundLocalError
        detected_country = ""
        detected_province = ""
        detected_city = ""
        
        if intent_analysis.get("success") and intent_analysis.get("intent", {}).get("location"):
            # ✅ USAR UBICACIÓN YA DETECTADA POR ANALYZE-INTENT
            location = intent_analysis["intent"]["location"]
            detected_country = intent_analysis["intent"].get("detected_country", intent_analysis["intent"].get("country", ""))
            detected_province = intent_analysis["intent"].get("detected_province", "")
            detected_city = intent_analysis["intent"].get("detected_city", location)
            logger.info(f"✅ USANDO UBICACIÓN DE ANALYZE-INTENT: '{location}' ({detected_country})")
        else:
            # Fallback: Usar intent recognition como antes
            try:
                from services.intent_recognition import intent_service
                ai_result = await intent_service.get_all_api_parameters(search_query)
                if ai_result.get("success") and ai_result.get("intent"):
                    detected_city = ai_result["intent"].get("city") or ai_result["intent"].get("location", "")
                    detected_country = ai_result["intent"].get("country", "")
                    detected_province = ai_result["intent"].get("province", "")
                    if detected_city and detected_city != "Buenos Aires":
                        location = detected_city
                        logger.info(f"🧠 FALLBACK INTENT AI: query='{search_query}' → localidad: '{location}', provincia: '{detected_province}', país: '{detected_country}'")
            except Exception as e:
                logger.warning(f"⚠️ Error en análisis Intent AI: {e}, usando detección manual")
            
            # 🔍 FALLBACK: DETECTAR CIUDAD EN QUERY MANUALMENTE
            query_lower = search_query.lower()
            city_detection = {
                "madrid": "Madrid", "barcelona": "Barcelona", "valencia": "Valencia",
                "sevilla": "Sevilla", "paris": "Paris", "miami": "Miami",
                "new york": "New York", "london": "London"
            }
            
            for city_keyword, city_name in city_detection.items():
                if city_keyword in query_lower:
                    location = city_name
                    logger.info(f"🔍 DETECCIÓN MANUAL: '{city_keyword}' → location: {city_name}")
                    break
        
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
        
        # LOG: Inicio de búsqueda inteligente
        logger.info("┌─────────────────────────────────────────────────────────────────")
        logger.info(f"│ 🎨 SMART SEARCH INICIADO")
        logger.info(f"│ 🔍 Query: '{search_query}'")
        logger.info(f"│ 📍 Ubicación: {location}")
        logger.info(f"│ 🏭 Método: Factory Pattern + Fallbacks")
        logger.info("└─────────────────────────────────────────────────────────────────")
        
        # ⏱️ LOG: Timing total del smart search
        smart_search_start_time = time.time()
        
        # 🏭 HIERARCHICAL FACTORY PATTERN - Country -> Provincial delegation
        try:
            from services.hierarchical_factory import fetch_from_all_sources_internal
            logger.info(f"🏭 FACTORY JERÁRQUICO - Procesando ubicación: {location}")
            
            # ⏱️ LOG: Timing del factory jerárquico
            hierarchical_start_time = time.time()
            
            # Pasar todos los datos detectados al factory
            context_data = {
                'detected_country': detected_country,
                'detected_province': detected_province,
                'detected_city': detected_city
            }
            result = await fetch_from_all_sources_internal(location, detected_country=detected_country, context_data=context_data)
            
            hierarchical_end_time = time.time()
            hierarchical_duration = hierarchical_end_time - hierarchical_start_time
            
            logger.info(f"⏱️ HIERARCHICAL TIMING: {hierarchical_duration:.2f}s para {result.get('count', 0)} eventos")
            
            # 🎯 FALLBACK JERÁRQUICO: Si hay pocos eventos y es carga inicial, buscar en provincia
            is_initial_load = query.get("is_initial_load", False) or search_query == ""
            event_count = result.get("count", 0) if result else 0
            original_location = location  # Guardar ubicación original
            
            # Solo aplicar si es carga inicial Y la ubicación original (detectada) es una ciudad específica
            should_apply_fallback = (
                is_initial_load and 
                event_count < 10 and 
                detected_city and 
                detected_province and
                original_location.lower() != "buenos aires" and  # No aplicar si ya es Buenos Aires
                detected_city.lower() != detected_province.lower()  # Solo si ciudad != provincia
            )
            
            if should_apply_fallback:
                # Mapeo ciudad -> provincia para Argentina
                city_to_province = {
                    "merlo": "Buenos Aires",
                    "la plata": "Buenos Aires", 
                    "quilmes": "Buenos Aires",
                    "san miguel": "Buenos Aires",
                    "tigre": "Buenos Aires",
                    "san isidro": "Buenos Aires",
                    "vicente lopez": "Buenos Aires",
                    "lomas de zamora": "Buenos Aires",
                    "avellaneda": "Buenos Aires",
                    "moron": "Buenos Aires",
                    "tres de febrero": "Buenos Aires",
                    "cordoba": "Córdoba",
                    "rosario": "Santa Fe",
                    "mendoza": "Mendoza",
                    "tucuman": "Tucumán",
                    "salta": "Salta",
                    "neuquen": "Neuquén",
                    "bahia blanca": "Buenos Aires"
                }
                
                city_lower = detected_city.lower()
                parent_province = city_to_province.get(city_lower, detected_province)
                
                if parent_province and parent_province != detected_city:
                    logger.info(f"🎯 FALLBACK JERÁRQUICO: {detected_city} ({event_count} eventos) -> {parent_province}")
                    
                    try:
                        # Buscar en la provincia padre
                        province_context = {
                            'detected_country': detected_country,
                            'detected_province': parent_province,
                            'detected_city': parent_province
                        }
                        province_result = await fetch_from_all_sources_internal(
                            parent_province, 
                            detected_country=detected_country, 
                            context_data=province_context
                        )
                        
                        if province_result and province_result.get("count", 0) > event_count:
                            logger.info(f"✅ FALLBACK SUCCESS: {parent_province} -> {province_result.get('count')} eventos")
                            result = province_result
                            result["fallback_applied"] = f"Expandido de {detected_city} a {parent_province}"
                        else:
                            logger.info(f"⚠️ FALLBACK: {parent_province} no mejoró resultados")
                    
                    except Exception as e:
                        logger.warning(f"❌ Error en fallback jerárquico: {e}")
            
            # El resultado ya viene en formato esperado con scrapers_execution
            if result and result.get("count", 0) > 0:
                # Agregar source compatible con el formato existente
                scraper_name = result.get("scraper_used", "Unknown_Factory")
                result["source"] = f"hierarchical_{scraper_name.replace(' ', '_')}"
                
                logger.info(f"🏭 FACTORY JERÁRQUICO SUCCESS - {scraper_name} - {result.get('count')} eventos")
                
                # LOG: Factory jerárquico maneja su propio logging interno
                logger.info(f"🏭 FACTORY JERÁRQUICO - Total eventos: {result.get('count', 0)}")
                logger.info(f"🏭 SCRAPER USADO: {result.get('scraper_used', 'Unknown')}")
                
                # LOG: Scrapers execution details
                scrapers_execution = result.get("scrapers_execution", {})
                if scrapers_execution:
                    logger.info(f"🏭 SCRAPERS EXECUTION: {scrapers_execution.get('summary', 'No summary')}")
            else:
                # Fallback to IndustrialFactory if hierarchical factory fails
                logger.warning(f"⚠️ Hierarchical factory failed for {location}, using IndustrialFactory fallback")
                from services.industrial_factory import IndustrialFactory
                factory = IndustrialFactory()
                
                # ⏱️ LOG: Timing del fallback
                fallback_start_time = time.time()
                
                detailed_result = await factory.execute_global_scrapers_with_details(location)
                events = detailed_result.get('events', [])
                
                fallback_end_time = time.time()
                fallback_duration = fallback_end_time - fallback_start_time
                
                logger.info(f"⏱️ FALLBACK TIMING: {fallback_duration:.2f}s para {len(events)} eventos")
                
                result = {
                    "events": events, 
                    "count": len(events), 
                    "scraper_used": "IndustrialFactory",
                    "scrapers_execution": detailed_result.get('scrapers_execution', {}),
                    "execution_time": f"{fallback_duration:.2f}s"
                }
                
                # LOG: Resultados del fallback multi_source
                if result.get("source_info"):
                    logger.info("🔄 FALLBACK MULTI_SOURCE - Resultados por servicio:")
                    for source_info in result.get("source_info", []):
                        service_name = source_info.get("source", "unknown")
                        event_count = source_info.get("count", 0)
                        logger.info(f"  📌 {service_name}: {event_count} eventos")
                else:
                    logger.info("🔄 FALLBACK MULTI_SOURCE - Sin información detallada de servicios")
                
        except Exception as e:
            logger.error(f"🚨 ERROR EN FACTORY: {e}")
            # Ultimate fallback to prevent crashes
            try:
                logger.warning("🔄 Using IndustrialFactory ultimate fallback...")
                from services.industrial_factory import IndustrialFactory
                factory = IndustrialFactory()
                
                # ⏱️ LOG: Timing del ultimate fallback
                ultimate_start_time = time.time()
                
                detailed_result = await factory.execute_global_scrapers_with_details(location)
                events = detailed_result.get('events', [])
                
                ultimate_end_time = time.time()
                ultimate_duration = ultimate_end_time - ultimate_start_time
                
                logger.info(f"⏱️ ULTIMATE FALLBACK TIMING: {ultimate_duration:.2f}s para {len(events)} eventos")
                
                result = {
                    "events": events, 
                    "count": len(events), 
                    "scraper_used": "IndustrialFactory-Ultimate",
                    "scrapers_execution": detailed_result.get('scrapers_execution', {}),
                    "execution_time": f"{ultimate_duration:.2f}s"
                }
                
                # LOG: Resultados del ultimate fallback
                if result.get("source_info"):
                    logger.info("🆘 ULTIMATE FALLBACK - Resultados por servicio:")
                    total_fallback_events = 0
                    for source_info in result.get("source_info", []):
                        service_name = source_info.get("source", "unknown")
                        event_count = source_info.get("count", 0)
                        total_fallback_events += event_count
                        if event_count > 0:
                            logger.info(f"  ✅ {service_name}: {event_count} eventos")
                        else:
                            logger.info(f"  ❌ {service_name}: 0 eventos")
                    logger.info(f"🆘 ULTIMATE FALLBACK - Total eventos: {total_fallback_events}")
                else:
                    event_count = len(result.get("events", []))
                    logger.info(f"🆘 ULTIMATE FALLBACK - {event_count} eventos (sin detalle por servicio)")
                    
            except Exception as fallback_error:
                logger.error(f"❌ Fallback también falló: {fallback_error}")
                logger.error(f"🔴 TODOS LOS SERVICIOS FALLARON - Devolviendo array vacío")
                result = {"status": "error", "events": [], "message": f"All systems failed: {e}"}
        
        # IMPORTANTE: Si buscamos una ciudad específica que no es la ciudad por defecto,
        # verificar si tenemos eventos para esa ubicación
        if location and "Buenos Aires" not in location:
            # Si el resultado viene de scrapers específicos, mantener los eventos
            source = result.get("source", "")
            if (source == "provincial_scraper" or 
                source.startswith("global_scraper_") or 
                source.startswith("factory_")):
                logger.info(f"✅ Usando eventos del scraper específico para {location} (source: {source})")
            # Si no hay eventos y no es un scraper específico, informar
            elif not result.get("events"):
                logger.warning(f"⚠️ No tenemos eventos para {location}")
                result["message"] = f"No encontramos eventos en {location}."
                result["location_available"] = False
            # ELIMINADO: Ya no filtramos eventos válidos de scrapers específicos
        
        # Don't filter too strictly - always return some events
        if search_query and result.get("events"):
            search_lower = search_query.lower()
            filtered_events = []
            all_events = result.get("events", [])
            
            logger.info(f"🔍 SMART SEARCH: Procesando {len(all_events)} eventos para query '{search_query}'")
            
            for event in all_events:
                title = event.get("title", "").lower()
                desc = event.get("description", "").lower()
                cat = event.get("category", "").lower()
                venue = event.get("venue_name", "").lower()
                
                logger.info(f"  📋 Procesando evento: '{event.get('title', 'Sin título')[:50]}...' (categoria: {event.get('category', 'N/A')})")
                
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
                    logger.info(f"    ✅ MATCH encontrado! Score: {match_score} - '{event.get('title', 'Sin título')[:40]}...'")
                else:
                    logger.info(f"    ❌ Sin match (score: {match_score}) - '{event.get('title', 'Sin título')[:40]}...')")
            
            # Sort by match score
            filtered_events.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            logger.info(f"🎯 FILTRADO COMPLETADO: {len(filtered_events)} eventos con match de {len(all_events)} totales")
            
            # If no matches or very few, return all events anyway
            if len(filtered_events) < 3:
                logger.info(f"⚠️  Pocos matches ({len(filtered_events)}), devolviendo TODOS los eventos ({len(all_events)})")
                result["events"] = all_events
                result["filtered_count"] = len(all_events)
                result["no_exact_match"] = True
            else:
                logger.info(f"✅ Suficientes matches, devolviendo {len(filtered_events)} eventos filtrados")
                result["events"] = filtered_events
                result["filtered_count"] = len(filtered_events)
        
        result["query"] = search_query
        result["smart_search"] = True
        
        # 🖼️ MEJORAR IMÁGENES DE EVENTOS
        try:
            from services.global_image_service import improve_events_images
            events_list = result.get("events", [])
            if events_list:
                image_start_time = time.time()
                improved_events = await improve_events_images(events_list)
                result["events"] = improved_events
                
                image_end_time = time.time()
                image_duration = image_end_time - image_start_time
                
                # Contar imágenes mejoradas
                improved_count = sum(1 for e in improved_events if e.get('image_improved', False))
                logger.info(f"🖼️ IMAGE SERVICE: {improved_count}/{len(events_list)} imágenes mejoradas en {image_duration:.2f}s")
                
                result["images_improved"] = improved_count
        except Exception as img_error:
            logger.warning(f"⚠️ Error mejorando imágenes: {img_error}")
        
        # El frontend espera recommended_events, no events
        result["recommended_events"] = result.get("events", [])
        
        # LOG: Resumen final de smart search
        final_events = len(result.get("events", []))
        logger.info("┌─────────────────────────────────────────────────────────────────")
        if final_events == 0:
            logger.info(f"│ ❌ SMART SEARCH COMPLETADO - CERO EVENTOS ENCONTRADOS")
            logger.info(f"│ 🔴 NINGÚN SERVICIO DEVOLVIÓ EVENTOS")
        else:
            logger.info(f"│ ✅ SMART SEARCH COMPLETADO")
            logger.info(f"│ 🎯 Total eventos retornados: {final_events}")
        logger.info(f"│ 📍 Ubicación final: {location}")
        logger.info(f"│ 🏭 Fuente: {result.get('source', 'unknown')}")
        if result.get("filtered_count"):
            logger.info(f"│ 🔍 Eventos filtrados: {result.get('filtered_count')}")
        if result.get("no_exact_match"):
            logger.info(f"│ ⚠️ Sin coincidencias exactas - retornando todos")
            
        # ⏱️ LOG: Timing total del smart search
        smart_search_end_time = time.time()
        smart_search_total_duration = smart_search_end_time - smart_search_start_time
        logger.info(f"│ ⏱️ SMART SEARCH TOTAL: {smart_search_total_duration:.2f}s")
        
        # Add scrapers execution to result if available
        if "scrapers_execution" not in result and hasattr(result, 'scrapers_execution'):
            result["scrapers_execution"] = getattr(result, 'scrapers_execution')
        
        logger.info("└─────────────────────────────────────────────────────────────────")
        
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
    location: str = Query(..., description="Location required")
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
        # Si no hay ciudad, intentar detectar la ubicación automáticamente
        try:
            from api.geolocation import detect_location
            detected_location = await detect_location(request=None)
            if detected_location and detected_location.get('city'):
                location = f"{detected_location['city']}, {detected_location.get('country', 'Argentina')}"
                logger.info(f"📍 Ubicación autodetectada: {location}")
            else:
                logger.warning(f"📍 No se pudo detectar ubicación, eventos limitados")
                location = None  # No usar fallback hardcodeado
        except Exception as e:
            logger.warning(f"⚠️ Error en detección automática: {e}")
            location = None  # No usar fallback hardcodeado
    
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
    location: str = Query(..., description="Location required"),
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
    location: str = Query(..., description="Location required"),
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
        from services.hierarchical_factory import fetch_from_all_sources_internal
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
        from services.hierarchical_factory import fetch_from_all_sources
        events = await fetch_from_all_sources(location=location)
        
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
    detected_location = "Buenos Aires"
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
    if detected_location == "Buenos Aires":
        try:
            from api.geolocation import detect_location
            from fastapi import Request
            
            # Crear un request mock para obtener la IP del usuario
            # En una implementación real, deberías pasar el request real
            logger.info("📍 No se detectó ciudad, usando geolocalización automática...")
            detected_location_data = await detect_location(request=None)
            if detected_location_data and detected_location_data.get('city'):
                detected_location = detected_location_data['city']
                logger.info(f"📍 Ciudad autodetectada: {detected_location}")
            else:
                logger.warning("📍 No se pudo autodetectar ubicación")
                detected_location = None  # No usar fallback hardcodeado
        except Exception as e:
            logger.warning(f"⚠️ Error en geolocalización automática: {e}")
            detected_location = "Buenos Aires"
    
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
        from services.hierarchical_factory import fetch_from_all_sources
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
    location = data.get("location", "Buenos Aires")
    from services.hierarchical_factory import fetch_from_all_sources
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
    from services.hierarchical_factory import fetch_from_all_sources
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
        # massive_scraper = EventbriteMassiveScraper()  # MOVED TO LEGACY
        
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
        # scraper = FacebookBrightDataScraper()  # MOVED TO LEGACY
        
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

# 🧠 AI intent analysis endpoint - POWERED BY GEMINI
@app.post("/api/ai/analyze-intent")
async def analyze_intent(
    data: Dict[str, Any]
):
    """
    🧠 Analyze user intent from natural language using GEMINI AI
    """
    try:
        query = data.get("query", "")
        current_location = data.get("current_location", "Buenos Aires")
        
        logger.info("┌─────────────────────────────────────────────────────────────────")
        logger.info(f"│ 🚀 EJECUTANDO: analyze_intent | query='{query[:40]}...' | location={current_location}")
        logger.info("└─────────────────────────────────────────────────────────────────")
        
        if not query.strip():
            logger.error("┌─────────────────────────────────────────────────────────────────")
            logger.error(f"│ ❌ ERROR: analyze_intent | Query vacío requerido")
            logger.error("└─────────────────────────────────────────────────────────────────")
            return {
                "success": False,
                "error": "Query is required",
                "intent": {}
            }
        
        # Usar servicio unificado de reconocimiento de intenciones
        from services.intent_recognition import intent_service
        
        result = await intent_service.get_all_api_parameters(query)
        
        # Formatear respuesta para compatibilidad con frontend existente
        intent = {
            "query": query,
            "categories": [result['intent']['category']] if result['intent']['category'] != 'Todos' else [],
            "location": result['intent']['location'],
            "time_preference": None,  # Se puede agregar después
            "price_preference": None,
            
            # Información adicional de Gemini - ESTRUCTURA CORREGIDA
            "confidence": result['intent']['confidence'],
            "detected_country": result['intent']['country'],  # Usar 'country' en lugar de 'detected_country'
            "detected_city": result['intent']['city'],        # Usar 'city' en lugar de 'location'
            "detected_province": result['intent'].get('province', ''),
            "keywords": result['intent'].get('keywords', []),
            "intent_type": result['intent']['type'],
            
            # Agregar jerarquía geográfica completa
            "geographic_hierarchy": result['intent'].get('geographic_hierarchy', {}),
            "scraper_config": result['intent'].get('scraper_config', {})
        }
        
        # Crear user_context con lógica de prioridades
        # 1. PRIORIDAD: Ubicación detectada por IA (override)
        # 2. FALLBACK: current_location del frontend
        detected_location = result['intent']['location']
        final_location = detected_location if detected_location else current_location
        
        user_context = {
            "location": final_location,
            "coordinates": None,  # Se podría agregar geocoding después
            "detected_country": result['intent']['country']  # Usar 'country' en lugar de 'detected_country'
        }
        
        logger.info("┌─────────────────────────────────────────────────────────────────")
        logger.info(f"│ ✅ ÉXITO: analyze_intent | categoría={result['intent']['category']} | ubicación={detected_location}")
        logger.info(f"│ confianza={result['intent']['confidence']:.2f} | país={result['intent']['country']} | tipo={result['intent']['type']}")
        logger.info(f"│ 🗺️ JERARQUÍA: {result['intent'].get('geographic_hierarchy', {}).get('full_location', 'N/A')}")
        logger.info("└─────────────────────────────────────────────────────────────────")
        
        return {
            "success": True,
            "intent": intent,
            "user_context": user_context,  # ← Nuevo: contexto actualizado
            "apis": {
                "location": detected_location,
                "category": result['intent']['category']
            }
        }
        
    except Exception as e:
        logger.error("┌─────────────────────────────────────────────────────────────────")
        logger.error(f"│ ❌ ERROR: analyze_intent | {str(e)}")
        logger.error("└─────────────────────────────────────────────────────────────────")
        return {
            "success": False,
            "error": str(e),
            "intent": {
                "query": query,
                "categories": [],
                "location": None,
                "fallback": True
            },
            "user_context": {
                "location": current_location,  # Usar current_location si falla
                "coordinates": None,
                "detected_country": None
            }
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

# WebSocket streaming scrapers progress endpoint
@app.websocket("/ws/scrapers-progress")
async def websocket_scrapers_progress(websocket: WebSocket):
    """🔄 WebSocket para mostrar progreso de scrapers en tiempo real"""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "🔄 Conexión establecida - Streaming de scrapers activado"
        })
        
        while True:
            # Wait for scraping request
            data = await websocket.receive_json()
            
            if data.get("action") == "start_scraping":
                location = data.get("location", "Buenos Aires")
                category = data.get("category")
                limit = data.get("limit", 30)
                
                # Stream scrapers with real-time progress
                await stream_scrapers_with_progress(websocket, location, category, limit)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket scrapers progress error: {e}")
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
                base_location = data.get("location", "Buenos Aires")
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
                await stream_events_optimized(websocket, detected_location)
                
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
                # eventbrite_scraper = EventbriteMassiveScraper()  # MOVED TO LEGACY
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
                # from services.argentina_venues_scraper import ArgentinaVenuesScraper  # DELETED
                
                # Argentina Venues Scraper - DELETED - FAKE DATA GENERATOR
                # argentina_scraper = ArgentinaVenuesScraper()  # DELETED - FAKE DATA GENERATOR
                # argentina_events = await argentina_scraper.fetch_all_events()  # DELETED - FAKE DATA GENERATOR
                argentina_events = []  # No fake data - return empty array
                
                # Send Argentina venues events (now empty)
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

@app.get("/api/multi/fetch-stream") 
async def fetch_stream_progressive(location: str = Query(..., description="Location required")):
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

@app.get("/api/debug/scrapers-status")
async def get_scrapers_debug():
    """
    🔍 DEBUG ENDPOINT - Para inspector del browser
    Muestra estado de todos los scrapers: execution_status y results_count
    """
    try:
        from services.country_scraper_factory import get_events_by_location
        
        # Test con Miami para obtener debug info
        result = await get_events_by_location("Miami")
        
        debug_info = []
        if result.get("scrapers_executed"):
            for scraper_name, scraper_info in result["scrapers_executed"].items():
                debug_info.append({
                    "scraper_name": scraper_name,
                    "execution_status": scraper_info.get("status", "unknown"),
                    "results_count": scraper_info.get("events", 0),
                    "execution_time": "N/A",  # Lo agregaremos después
                    "country": "USA" if "Miami" in scraper_name else "Unknown",
                    "city": "Miami" if "Miami" in scraper_name else "Unknown"
                })
        
        return {
            "total_scrapers": len(debug_info),
            "scrapers": debug_info,
            "timestamp": datetime.utcnow().isoformat(),
            "inspector_info": "🔍 Use this endpoint to debug scrapers from browser inspector"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "scrapers": [],
            "total_scrapers": 0
        }

# 🧹 DAILY CLEANUP ENDPOINTS
@app.post("/api/admin/cleanup")
async def run_manual_cleanup():
    """
    🧹 Ejecutar limpieza manual de eventos expirados
    Útil para testing o limpieza bajo demanda
    """
    try:
        from services.daily_cleanup import run_manual_cleanup
        result = await run_manual_cleanup()
        return result
    except Exception as e:
        logger.error(f"❌ Error en limpieza manual: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/admin/cleanup/status")
async def get_cleanup_status():
    """
    🔍 Obtener estado del sistema de limpieza
    """
    try:
        from services.daily_cleanup import DailyCleanupManager
        
        cleanup_manager = DailyCleanupManager()
        now = datetime.now()
        
        return {
            "current_time": now.isoformat(),
            "cleanup_hour": cleanup_manager.cleanup_hour,
            "should_run_now": cleanup_manager.should_run_cleanup(),
            "time_until_next_cleanup": f"{(cleanup_manager.cleanup_hour - now.hour) % 24} horas",
            "retention_days": cleanup_manager.retention_days,
            "cache_files_monitored": len(cleanup_manager.cache_files),
            "status": "active"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e)
        }

# 🧪 ADMIN TESTING ENDPOINTS - Individual Source Testing
@app.post("/api/test/facebook")
async def test_facebook_source(request: Request):
    """Test Facebook scraping individual"""
    start_time = time.time()
    try:
        body = await request.json()
        location = body.get("location", "Barcelona")
        
        # from services.rapidapi_facebook_scraper import RapidApiFacebookScraper
        scraper = RapidApiFacebookScraper()
        events = await scraper.scrape_facebook_events_rapidapi(location)
        
        execution_time = time.time() - start_time
        return {
            "source": "Facebook",
            "location": location,
            "events": events,
            "count": len(events),
            "execution_time": f"{execution_time:.3f}s",
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Facebook",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test/eventbrite")
async def test_eventbrite_source(request: Request):
    """Test Eventbrite scraping individual"""
    start_time = time.time()
    try:
        body = await request.json()
        location = body.get("location", "Barcelona")
        
        from services.eventbrite_web_scraper import EventbriteWebScraper
        scraper = EventbriteWebScraper()
        events = await scraper.fetch_events_by_location(location)
        
        execution_time = time.time() - start_time
        return {
            "source": "Eventbrite",
            "location": location,
            "events": events,
            "count": len(events),
            "execution_time": f"{execution_time:.3f}s",
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Eventbrite",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test/venues")
async def test_venues_source(request: Request):
    """Test Official Venues scraping individual"""
    start_time = time.time()
    try:
        from services.oficial_venues_scraper import OficialVenuesScraper
        scraper = OficialVenuesScraper()
        events = await scraper.scrape_all_oficial_venues()
        
        execution_time = time.time() - start_time
        return {
            "source": "Official Venues",
            "events": events,
            "count": len(events),
            "execution_time": f"{execution_time:.3f}s",
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Official Venues",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test/provincial")
async def test_provincial_source(request: Request):
    """Test Provincial scrapers individual"""
    start_time = time.time()
    try:
        body = await request.json()
        location = body.get("location", "Córdoba")
        
        from services.provincial_scrapers import get_events_by_province
        events = await get_events_by_province(location)
        
        execution_time = time.time() - start_time
        return {
            "source": "Provincial",
            "location": location,
            "events": events.get("events", []) if isinstance(events, dict) else events,
            "count": len(events.get("events", [])) if isinstance(events, dict) else len(events) if events else 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Provincial",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test/multi-source")
async def test_multi_source(request: Request):
    """Test Multi-Source API individual"""
    start_time = time.time()
    try:
        body = await request.json()
        location = body.get("location", "Buenos Aires")
        
        from services.hierarchical_factory import fetch_from_all_sources
        result = await fetch_from_all_sources(location=location, fast=True)
        events = result.get("events", []) if result else []
        
        execution_time = time.time() - start_time
        return {
            "source": "Multi-Source",
            "location": location,
            "events": events,
            "count": len(events),
            "execution_time": f"{execution_time:.3f}s",
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Multi-Source",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test/factory")
async def test_factory_source(request: Request):
    """Test Hierarchical Factory individual"""
    start_time = time.time()
    try:
        body = await request.json()
        location = body.get("location", "Córdoba")
        
        from services.hierarchical_factory import get_events_hierarchical
        result = await get_events_hierarchical(location)
        events = result.get("events", []) if result else []
        
        execution_time = time.time() - start_time
        return {
            "source": "Hierarchical Factory",
            "location": location,
            "events": events,
            "count": len(events),
            "execution_time": f"{execution_time:.3f}s",
            "status": "success",
            "scraper_used": result.get("scraper_used", "Unknown") if result else "Unknown"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "source": "Hierarchical Factory",
            "events": [],
            "count": 0,
            "execution_time": f"{execution_time:.3f}s",
            "status": "error",
            "error": str(e)
        }

async def stream_scrapers_with_progress(websocket: WebSocket, location: str, category: Optional[str] = None, limit: int = 30):
    """
    🔄 STREAMING DE SCRAPERS CON PROGRESO EN TIEMPO REAL
    
    Envía información detallada de cada scraper mientras se ejecuta:
    - Estado de inicio/ejecución/finalización
    - Tiempo de ejecución en vivo
    - Eventos encontrados por scraper
    - Detalles técnicos (URLs generadas, PatternService, etc.)
    """
    try:
        # Inicializar contexto para scrapers
        from services.intent_recognition import intent_service
        
        await websocket.send_json({
            "type": "scraping_started",
            "message": f"🧠 Analizando ubicación: {location}",
            "location": location,
            "progress": 0,
            "timestamp": datetime.now().isoformat()
        })
        
        # Análisis de ubicación con IA
        start_ai = time.time()
        ai_result = await intent_service.get_all_api_parameters(location)
        end_ai = time.time()
        
        detected_location = ai_result.get("location", location)
        detected_country = ai_result.get("country", "")
        detected_province = ai_result.get("province", "")
        detected_city = ai_result.get("city", "")
        
        await websocket.send_json({
            "type": "location_analyzed",
            "message": f"✅ Ubicación analizada: {detected_city}, {detected_province}, {detected_country}",
            "location_data": {
                "original": location,
                "detected": detected_location,
                "city": detected_city,
                "province": detected_province,
                "country": detected_country
            },
            "analysis_time": f"{end_ai - start_ai:.2f}s",
            "progress": 15,
            "timestamp": datetime.now().isoformat()
        })
        
        # Preparar contexto para scrapers
        context_data = {
            'detected_country': detected_country,
            'detected_province': detected_province,
            'detected_city': detected_city
        }
        
        await websocket.send_json({
            "type": "scrapers_discovery",
            "message": "🔍 Descubriendo scrapers disponibles...",
            "progress": 20,
            "timestamp": datetime.now().isoformat()
        })
        
        # Usar IndustrialFactory con streaming personalizado
        from services.industrial_factory import IndustrialFactory
        factory = IndustrialFactory()
        
        # Auto-descubrir scrapers
        scrapers_map = factory.discovery_engine.discover_all_scrapers()
        global_scrapers = scrapers_map.get('global', {})
        
        await websocket.send_json({
            "type": "scrapers_discovered",
            "message": f"🌍 {len(global_scrapers)} scrapers globales descubiertos",
            "scrapers": list(global_scrapers.keys()),
            "progress": 30,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ejecutar cada scraper individualmente con progreso detallado
        total_events = []
        scraper_results = []
        progress_step = 60 // len(global_scrapers) if global_scrapers else 60
        current_progress = 30
        
        for i, (scraper_name, scraper_instance) in enumerate(global_scrapers.items()):
            scraper_start = time.time()
            
            await websocket.send_json({
                "type": "scraper_started",
                "scraper_name": scraper_name.title(),
                "message": f"🚀 Ejecutando {scraper_name.title()}Scraper...",
                "progress": current_progress,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                # Configurar contexto si el scraper lo soporta
                if hasattr(scraper_instance, 'set_context'):
                    scraper_instance.set_context(context_data)
                
                # Ejecutar scraper con timeout
                events = await asyncio.wait_for(
                    scraper_instance.scrape_events(detected_location, category, limit),
                    timeout=5.0
                )
                
                scraper_end = time.time()
                execution_time = scraper_end - scraper_start
                events_count = len(events) if isinstance(events, list) else 0
                
                if events_count > 0:
                    total_events.extend(events)
                
                scraper_results.append({
                    'name': scraper_name.title(),
                    'status': 'success',
                    'events_count': events_count,
                    'execution_time': f'{execution_time:.2f}s'
                })
                
                await websocket.send_json({
                    "type": "scraper_completed",
                    "scraper_name": scraper_name.title(),
                    "message": f"✅ {scraper_name.title()}: {events_count} eventos en {execution_time:.2f}s",
                    "events_count": events_count,
                    "execution_time": f"{execution_time:.2f}s",
                    "events": events[:3] if events_count > 0 else [],  # Solo primeros 3 como preview
                    "progress": current_progress + progress_step,
                    "timestamp": datetime.now().isoformat()
                })
                
            except asyncio.TimeoutError:
                scraper_end = time.time()
                execution_time = scraper_end - scraper_start
                
                scraper_results.append({
                    'name': scraper_name.title(),
                    'status': 'timeout',
                    'events_count': 0,
                    'execution_time': f'{execution_time:.2f}s'
                })
                
                await websocket.send_json({
                    "type": "scraper_timeout",
                    "scraper_name": scraper_name.title(),
                    "message": f"⏰ {scraper_name.title()}: Timeout después de 5s",
                    "execution_time": f"{execution_time:.2f}s",
                    "progress": current_progress + progress_step,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                scraper_end = time.time()
                execution_time = scraper_end - scraper_start
                
                scraper_results.append({
                    'name': scraper_name.title(),
                    'status': 'error',
                    'events_count': 0,
                    'execution_time': f'{execution_time:.2f}s'
                })
                
                await websocket.send_json({
                    "type": "scraper_error",
                    "scraper_name": scraper_name.title(),
                    "message": f"❌ {scraper_name.title()}: {str(e)}",
                    "error": str(e),
                    "execution_time": f"{execution_time:.2f}s",
                    "progress": current_progress + progress_step,
                    "timestamp": datetime.now().isoformat()
                })
            
            current_progress += progress_step
        
        # Enviar resultado final
        await websocket.send_json({
            "type": "scraping_completed",
            "message": f"🎯 Scraping completado: {len(total_events)} eventos totales",
            "total_events": len(total_events),
            "scrapers_summary": scraper_results,
            "successful_scrapers": len([s for s in scraper_results if s['status'] == 'success']),
            "total_scrapers": len(global_scrapers),
            "events": total_events,  # Todos los eventos
            "progress": 100,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error en streaming de scrapers: {str(e)}")
        await websocket.send_json({
            "type": "scraping_error",
            "message": f"❌ Error general: {str(e)}",
            "error": str(e),
            "progress": 0,
            "timestamp": datetime.now().isoformat()
        })

async def stream_events_optimized(websocket: WebSocket, location: str):
    """
    🚀 STREAMING OPTIMIZADO CON INDUSTRIAL FACTORY
    
    Entrega eventos en tiempo real usando:
    - Sistema de caché JSON (0 llamadas a IA)
    - Solo scrapers habilitados (2 en lugar de 9) 
    - Streaming por scraper individual (no esperar a todos)
    """
    try:
        await websocket.send_json({
            "type": "search_started",
            "message": f"🚀 Búsqueda optimizada iniciada para {location}",
            "location": location,
            "enabled_scrapers": ["Eventbrite", "Meetup"],
            "progress": 0
        })
        
        # Usar IndustrialFactory para obtener scrapers optimizados
        from services.industrial_factory import IndustrialFactory
        factory = IndustrialFactory()
        
        # Auto-discovery con flags - solo scrapers habilitados
        scrapers_map = factory.discovery_engine.discover_all_scrapers()
        global_scrapers = scrapers_map.get('global', {})
        
        await websocket.send_json({
            "type": "scrapers_discovered",
            "message": f"🔧 {len(global_scrapers)} scrapers habilitados listos",
            "scrapers": list(global_scrapers.keys()),
            "progress": 10
        })
        
        # Ejecutar scrapers INDIVIDUALMENTE con streaming
        total_events = 0
        scraper_count = len(global_scrapers)
        
        for i, (scraper_name, scraper_instance) in enumerate(global_scrapers.items()):
            scraper_progress = 10 + (i * 80 // scraper_count)
            
            await websocket.send_json({
                "type": "scraper_started",
                "scraper": scraper_name.title(),
                "message": f"⚡ {scraper_name.title()} iniciado...",
                "progress": scraper_progress
            })
            
            # Ejecutar scraper individual con timeout
            start_time = time.time()
            try:
                events = await asyncio.wait_for(
                    scraper_instance.scrape_events(location, None, 30),
                    timeout=5.0
                )
                execution_time = time.time() - start_time
                
                if events and len(events) > 0:
                    total_events += len(events)
                    
                    # ENTREGAR EVENTOS INMEDIATAMENTE
                    await websocket.send_json({
                        "type": "events_batch",
                        "scraper": scraper_name.title(),
                        "events": events,
                        "count": len(events),
                        "execution_time": f"{execution_time:.2f}s",
                        "total_events": total_events,
                        "progress": scraper_progress + 15,
                        "status": "success"
                    })
                    
                    logger.info(f"🚀 WebSocket - {scraper_name.title()}: {len(events)} eventos enviados en {execution_time:.2f}s")
                else:
                    await websocket.send_json({
                        "type": "scraper_completed",
                        "scraper": scraper_name.title(),
                        "count": 0,
                        "execution_time": f"{execution_time:.2f}s",
                        "message": f"❌ {scraper_name.title()}: 0 eventos",
                        "progress": scraper_progress + 15,
                        "status": "empty"
                    })
                    
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "scraper_timeout",
                    "scraper": scraper_name.title(),
                    "message": f"⏰ {scraper_name.title()}: Timeout después de 5s",
                    "progress": scraper_progress + 15,
                    "status": "timeout"
                })
                logger.warning(f"⏰ WebSocket - {scraper_name.title()}: Timeout")
                
            except Exception as e:
                await websocket.send_json({
                    "type": "scraper_error",
                    "scraper": scraper_name.title(),
                    "message": f"❌ {scraper_name.title()}: {str(e)}",
                    "progress": scraper_progress + 15,
                    "status": "error"
                })
                logger.error(f"❌ WebSocket - {scraper_name.title()}: {str(e)}")
        
        # Enviar resumen final
        await websocket.send_json({
            "type": "search_completed",
            "total_events": total_events,
            "scrapers_used": len(global_scrapers),
            "message": f"✅ Búsqueda completada: {total_events} eventos totales",
            "progress": 100
        })
        
        logger.info(f"🎯 WebSocket - Búsqueda completada: {total_events} eventos de {len(global_scrapers)} scrapers")
        
    except Exception as e:
        await websocket.send_json({
            "type": "search_error",
            "message": f"❌ Error en búsqueda: {str(e)}",
            "progress": 100
        })
        logger.error(f"❌ WebSocket streaming error: {str(e)}")

@app.get("/api/admin")
async def admin_page():
    """Serve admin test page"""
    try:
        with open("/mnt/c/Code/eventos-visualizer/backend/templates/admin.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading admin page: {e}</h1>", status_code=500)

if __name__ == "__main__":
    print(f"\n🚀 Starting Eventos Visualizer Backend")
    print(f"📍 Server: {BACKEND_URL}")
    print(f"📊 Health: {BACKEND_URL}/health")
    print(f"📝 Docs: {BACKEND_URL}/docs")
    ws_url = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    print(f"🔌 WebSocket: {ws_url}/ws/notifications\n")
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )