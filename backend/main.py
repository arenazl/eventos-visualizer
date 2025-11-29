import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from colorama import init, Fore, Back, Style
init(autoreset=True)  # Initialize colorama

# Heroku configuration
try:
    from heroku_config import apply_heroku_config, is_heroku
    apply_heroku_config()
    if is_heroku():
        print("🌐 Running on Heroku - Production mode activated")
except ImportError:
    print("Running locally - Development mode")
import asyncpg
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
import sys
import aiohttp
import time

# Add backend to path
import platform
if platform.system() == 'Windows':
    sys.path.append(r'C:\Code\eventos-visualizer\backend')
else:
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
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001" if not IS_PRODUCTION else "https://funaroundyou-f21e91cae36c.herokuapp.com")

# Force localhost on Windows
if platform.system() == 'Windows' and not IS_PRODUCTION:
    BACKEND_URL = "http://localhost:8001"

# Extract host and port from URL for uvicorn.run()
from urllib.parse import urlparse
parsed_url = urlparse(BACKEND_URL)
HOST = parsed_url.hostname or "localhost"
BACKEND_PORT = parsed_url.port or (443 if parsed_url.scheme == "https" else 8001)

# Override with Heroku's PORT if available (Heroku deployment)
if os.getenv("PORT"):
    BACKEND_PORT = int(os.getenv("PORT"))
    HOST = "0.0.0.0"  # Heroku requires binding to all interfaces

# Force localhost for Windows
if platform.system() == 'Windows':
    HOST = "localhost"
    BACKEND_URL = f"http://localhost:{BACKEND_PORT}"

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

# Session middleware for OAuth
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-here"))

# ═══════════════════════════════════════════════════════════════════
# 🔐 AUTENTICACIÓN CON GOOGLE OAUTH2
# ═══════════════════════════════════════════════════════════════════
try:
    from api.auth import router as auth_router
    app.include_router(auth_router)
    logger.info("🔐 Autenticación Google OAuth2 habilitada")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo cargar autenticación: {e}")
except Exception as e:
    logger.warning(f"⚠️ Error al configurar autenticación: {e}")

# ═══════════════════════════════════════════════════════════════════
# 📍 GEOLOCALIZACIÓN
# ═══════════════════════════════════════════════════════════════════
try:
    from api.geolocation import router as geolocation_router
    app.include_router(geolocation_router, prefix="/api/location", tags=["location"])
    logger.info("📍 Geolocalización habilitada")
except ImportError as e:
    logger.warning(f"⚠️ No se pudo cargar geolocalización: {e}")
except Exception as e:
    logger.warning(f"⚠️ Error al configurar geolocalización: {e}")

# 🚫 NO-CACHE MIDDLEWARE - Deshabilitar todo el cache
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)

    # 🔥 NO aplicar no-cache a SSE streams - preservar Content-Type
    if not request.url.path.startswith("/api/events/stream"):
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

# Opción 2: LOGGING DETALLADO CON EMOJIS - DESACTIVADO TEMPORALMENTE PARA DEBUG
# app.router.route_class = LoggingRoute

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
    return {"status": "healthy", "message": "OK"}


@app.get("/api/youtube/search")
async def search_youtube_video(q: str):
    """
    Busca un video de YouTube relacionado con el evento
    Retorna el video_id del primer resultado
    """
    try:
        from youtubesearchpython import VideosSearch

        # Buscar video corto relacionado con el evento
        search = VideosSearch(f"{q} official", limit=1)
        results = search.result()

        if results and results.get('result') and len(results['result']) > 0:
            video = results['result'][0]
            return {
                "status": "success",
                "video_id": video.get('id'),
                "title": video.get('title'),
                "duration": video.get('duration'),
                "thumbnail": video.get('thumbnails', [{}])[0].get('url') if video.get('thumbnails') else None
            }

        return {"status": "not_found", "video_id": None}
    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return {"status": "error", "error": str(e), "video_id": None}


@app.get("/api/test/gemini")
async def test_gemini_api():
    """
    🧪 Test endpoint para verificar que la API key de Gemini funciona
    """
    # 1. Primero mostrar qué API key está configurada
    api_key = os.getenv("GEMINI_API_KEY", "NO_CONFIGURADA")
    api_key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key

    try:
        from services.gemini_factory import gemini_factory

        # 2. Probar detección de ciudad principal
        test_location = "Moron"
        parent_city = await gemini_factory.get_parent_location(test_location)

        return {
            "status": "success",
            "gemini_working": True,
            "api_key_configured": api_key_preview,
            "test_query": test_location,
            "detected_parent_city": parent_city,
            "message": f"✅ Gemini API funcionando - Detectó: {test_location} → {parent_city}"
        }
    except Exception as e:
        logger.error(f"❌ Error testing Gemini API: {e}")
        return {
            "status": "error",
            "gemini_working": False,
            "api_key_configured": api_key_preview,
            "error": str(e),
            "message": "❌ Gemini API no está funcionando"
        }

@app.get("/api/debug/sources")
async def debug_sources(location: str = "Buenos Aires"):
    """🔍 DEBUG COPADO: Ver cuánto devuelve cada fuente"""
    import asyncio
    import time
    from services.gemini_factory import gemini_factory
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
        factory = gemini_factory  # Singleton - no need to instantiate
        all_events = await factory.execute_global_scrapers(location, context_data={})
        factory_time = time.time() - start_time
        debug_info["fuentes_debug"]["gemini_factory"] = {
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

# SERVICIOS DE CHAT RECREADOS - Router api/ai.py DESHABILITADO
# ❌ api/ai.py usa chat_memory_manager/ai_assistant/gemini_brain que no existen
# ✅ Los endpoints funcionales están en main.py directamente (líneas 3869+)
# try:
#     from api.ai import router as ai_router
#     app.include_router(ai_router, prefix="/api/ai")
#     logger.info("✅ AI Gemini router loaded - servicios recreados")
# except Exception as e:
#     logger.warning(f"Could not load AI Gemini router: {e}")
#     logger.info("ℹ️ AI Gemini router temporalmente deshabilitado")
logger.info("ℹ️ AI router de api/ai.py deshabilitado - usando endpoints de main.py")

# API V1 con SSE Streaming
try:
    from api.v1 import router as v1_router
    app.include_router(v1_router)
    logger.info("✅ API V1 with SSE streaming loaded")
except Exception as e:
    logger.warning(f"⚠️ Could not load API V1 router: {e}")

# External Events Router (BrightData, Claude Desktop, etc.)
try:
    from api.external_events import router as external_router
    app.include_router(external_router)
    logger.info("✅ External Events router loaded (BrightData/Claude Desktop)")
except Exception as e:
    logger.warning(f"⚠️ Could not load External Events router: {e}")

# Events DB Router (Fast queries from PostgreSQL)
try:
    from api.events_db import router as events_db_router
    app.include_router(events_db_router)
    logger.info("✅ Events DB router loaded (Fast PostgreSQL queries)")
except Exception as e:
    logger.warning(f"⚠️ Could not load Events DB router: {e}")

# ============================================================================
# 🧹 HELPER FUNCTIONS - Deduplication
# ============================================================================

def deduplicate_events_by_title(events: list) -> list:
    """
    MARCA eventos duplicados basándose en similitud de títulos (>80%)

    NUEVA ESTRATEGIA (NO ELIMINA, SOLO MARCA):
    - Compara cada evento con los ya procesados
    - Si encuentra un título >80% similar, marca el peor como duplicado
    - Agrega campos: is_duplicate=True, duplicate_of=[id del principal]
    - RETORNA TODOS LOS EVENTOS (principales + duplicados marcados)

    Args:
        events: Lista de eventos (dicts)

    Returns:
        Lista completa con duplicados marcados
    """
    if not events:
        return events

    # Source priority (mayor = mejor)
    SOURCE_PRIORITY = {
        'database': 10,
        'gemini': 9,
        'felo': 8,
        'gemini_scraper': 7,
        'felo_scraper': 6,
        'nightclub': 5,
    }

    def get_source_priority(source: str) -> int:
        """Retorna prioridad del source (mayor = mejor)"""
        return SOURCE_PRIORITY.get(source, 1)  # Default: 1 (bajo)

    def calculate_title_similarity(title1: str, title2: str) -> float:
        """Calcula similitud entre 2 títulos (0.0 - 1.0)"""
        if not title1 or not title2:
            return 0.0

        # Normalizar: lowercase y quitar caracteres especiales
        t1 = title1.lower().replace('-', ' ').replace('(', '').replace(')', '')
        t2 = title2.lower().replace('-', ' ').replace('(', '').replace(')', '')

        # Extraer palabras
        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return 0.0

        # Palabras comunes
        common = words1 & words2

        # Similitud = palabras comunes / total palabras únicas
        total_unique = words1 | words2
        similarity = len(common) / len(total_unique) if total_unique else 0.0

        return similarity

    def is_better_event(event1: dict, event2: dict) -> bool:
        """Retorna True si event1 es mejor que event2"""
        # Criterio 1: Prioridad por source
        priority1 = get_source_priority(event1.get('source', ''))
        priority2 = get_source_priority(event2.get('source', ''))

        if priority1 != priority2:
            return priority1 > priority2

        # Criterio 2: Tiene imagen
        has_image1 = bool(event1.get('image_url'))
        has_image2 = bool(event2.get('image_url'))

        if has_image1 != has_image2:
            return has_image1

        # Criterio 3: Título más largo (más descriptivo)
        return len(event1.get('title', '')) > len(event2.get('title', ''))

    # NUEVA LÓGICA: Marcar duplicados (NO eliminar)
    all_events = []
    duplicate_count = 0

    for event in events:
        title = event.get('title', '')
        found_similar = False

        # Inicializar campos de duplicado
        event['is_duplicate'] = False
        event['duplicate_of'] = None

        # Comparar con eventos ya procesados
        for existing in all_events:
            # Saltar eventos ya marcados como duplicados
            if existing.get('is_duplicate'):
                continue

            existing_title = existing.get('title', '')
            similarity = calculate_title_similarity(title, existing_title)

            # Si es muy similar (>80%), marcar como duplicado
            if similarity >= 0.80:
                found_similar = True

                # Determinar cuál es mejor
                if is_better_event(event, existing):
                    # El nuevo es mejor → marcar el existente como duplicado
                    existing['is_duplicate'] = True
                    existing['duplicate_of'] = event.get('id')
                    logger.debug(f"🔄 '{existing_title[:40]}...' marcado como duplicado de '{title[:40]}...' (similarity: {similarity:.0%})")
                    duplicate_count += 1
                else:
                    # El existente es mejor → marcar el nuevo como duplicado
                    event['is_duplicate'] = True
                    event['duplicate_of'] = existing.get('id')
                    logger.debug(f"⏭️ '{title[:40]}...' marcado como duplicado de '{existing_title[:40]}...' (similarity: {similarity:.0%})")
                    duplicate_count += 1

                break

        # Agregar TODOS los eventos (duplicados y no duplicados)
        all_events.append(event)

    if duplicate_count > 0:
        logger.info(f"🏷️ Total duplicados marcados: {duplicate_count} de {len(all_events)} eventos")

    return all_events

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

# Simple test endpoint
@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "test": "working"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Eventos Visualizer API",
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

# Cache global para evitar enriquecer la misma ubicación múltiples veces
_last_enriched_location = None

@app.get("/api/events/stream")
async def stream_events(
    location: Optional[str] = Query(None, description="Ubicación requerida"),
    category: Optional[str] = Query(None),
    limit: int = Query(100),
    parent_city: Optional[str] = Query(None, description="Ciudad padre desde metadata del frontend")
):
    """
    🚀 SSE STREAMING ENDPOINT - Devuelve eventos en tiempo real

    Usa async generators para devolver resultados apenas estén listos
    NO espera a que terminen todos los scrapers
    """
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        """Generator para SSE - Consulta MySQL en vez de Gemini"""
        import time
        try:
            if not location:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Ubicación requerida'})}\n\n"
                return

            # Enviar evento de inicio
            yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos en {location}', 'location': location})}\n\n"

            # 🗄️ BUSCAR EN MYSQL EN VEZ DE GEMINI
            from services.events_db_service import search_events_by_location

            start_time = time.time()
            logger.info(f"🔍 Consultando MySQL para ubicación: {location}")
            logger.info(f"🔍 Parámetros: category={category}, limit={limit}, days_ahead=180")

            # Consultar base de datos (180 días = 6 meses hacia adelante)
            # ✨ Si parent_city viene del frontend, usarlo directamente (sin IA)
            # Si no viene, include_parent_city=False → NO llamar IA
            try:
                if parent_city:
                    logger.info(f"🏙️ parent_city recibido del frontend: {parent_city}")

                result = await search_events_by_location(
                    location=location,
                    category=category,
                    limit=limit,
                    days_ahead=180,
                    include_parent_city=False,  # Sin IA
                    parent_city=parent_city  # ✨ Pasado desde metadata del frontend
                )
                # Extraer eventos del resultado (es un dict con 'events', 'parent_city_detected', etc.)
                events = result.get('events', []) if isinstance(result, dict) else result
                parent_city_detected = result.get('parent_city_detected') if isinstance(result, dict) else None
                original_location = result.get('original_location') if isinstance(result, dict) else location
                expanded_search = result.get('expanded_search', False) if isinstance(result, dict) else False

                logger.info(f"✅ search_events_by_location devolvió {len(events)} eventos")
                logger.info(f"🔍 DEBUG - parent_city: {parent_city_detected}, expanded: {expanded_search}, result type: {type(result)}")
            except Exception as search_err:
                logger.error(f"❌ Error en search_events_by_location: {search_err}")
                events = []
                parent_city_detected = None
                original_location = location
                expanded_search = False

            # 🧹 DEDUPLICACIÓN: Marcar eventos con títulos similares
            events_before_dedup = len(events)
            if events_before_dedup > 0:
                events = deduplicate_events_by_title(events)
                duplicates_marked = sum(1 for e in events if e.get('is_duplicate'))
                if duplicates_marked > 0:
                    main_events = events_before_dedup - duplicates_marked
                    logger.info(f"🏷️ Duplicados marcados: {duplicates_marked} ({main_events} principales + {duplicates_marked} duplicados = {events_before_dedup} total)")

            execution_time = f"{time.time() - start_time:.2f}s"
            total_events = len(events)
            logger.info(f"📊 Total eventos después de búsqueda: {total_events} en {execution_time}")

            if total_events > 0:
                # Enviar eventos desde base de datos con metadata de búsqueda expandida
                event_data = {
                    'type': 'events',
                    'scraper': 'mysql_database',
                    'events': events,  # ← Ahora es el array correcto
                    'count': total_events,
                    'total_events': total_events,
                    'execution_time': execution_time
                }

                # Agregar metadata de búsqueda expandida si existe
                if parent_city_detected:
                    event_data['parent_city'] = parent_city_detected
                    event_data['original_location'] = original_location
                    event_data['expanded_search'] = expanded_search

                yield f"data: {json.dumps(event_data)}\n\n"
                logger.info(f"📡 SSE: MySQL - {total_events} eventos enviados en {execution_time}")
            else:
                # ❌ NO HAY EVENTOS - NO buscar en ciudades cercanas (solo mostrar mensaje)
                logger.info(f"❌ No hay eventos en {location}")
                yield f"data: {json.dumps({'type': 'no_events', 'scraper': 'mysql_database', 'count': 0, 'message': f'No hay eventos disponibles para {location}'})}\n\n"

                # 🔒 BÚSQUEDA AUTOMÁTICA EN CIUDADES CERCANAS DESHABILITADA
                # El usuario debe buscar manualmente en otras ciudades
                # (El frontend mostrará shake animation en el search bar)

            # ✅ Enviar evento de completado INMEDIATAMENTE (eventos ya enviados)
            yield f"data: {json.dumps({'type': 'complete', 'total_events': total_events, 'scrapers_completed': 1})}\n\n"
            logger.info(f"🏁 SSE: Streaming completado - {total_events} eventos totales")

            # 🚫 ENRIQUECIMIENTO DESACTIVADO
            # NO buscar ciudades cercanas automáticamente
            # El usuario debe buscar manualmente si quiere ver otras ciudades

        except Exception as e:
            logger.error(f"❌ Error en SSE streaming desde MySQL: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    # 🔥 RETORNAR EL STREAMING RESPONSE
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.get("/api/location/enrichment")
async def get_location_enrichment(
    location: str = Query(..., description="Ubicación original del usuario"),
    
    force_refresh: bool = Query(False, description="Forzar nuevo enriquecimiento ignorando caché")
):
    """
    🌍 ENRIQUECIMIENTO DE UBICACIÓN - Solo obtiene info sin buscar eventos

    Retorna:vscode-webview://1d0l9k4dlisibkf6diqq2no75k7u891dcvs5vm2g0kvv31dus3kn/backend/services/gemini_factory.py#L221-L298
        - city: Ciudad
        - state: Provincia/Estado
        - country: País
        - nearby_cities: Array de 3 ciudades cercanas
        - needs_expansion: Si necesita expansión
    """
    try:
        from services.gemini_factory import gemini_factory
        import json
        import os

        factory = gemini_factory  # Singleton - no need to instantiate

        # Si force_refresh, limpiar caché de esta ubicación específica
        if force_refresh:
            # 1. Limpiar caché en memoria del factory
            keys_to_remove_memory = [key for key in factory._location_cache.keys() if location.lower() in key.lower()]
            for key in keys_to_remove_memory:
                del factory._location_cache[key]
                logger.info(f"🗑️ Memory cache cleared: {key}")

            # 2. Limpiar caché en archivo JSON
            cache_path = os.path.join(os.path.dirname(__file__), 'data', 'location_enrichments_cache.json')
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    # Eliminar todas las entradas que contengan esta ubicación
                    enrichments = cache_data.get('enrichments', {})
                    keys_to_remove = [key for key in enrichments.keys() if location.lower() in key.lower()]

                    for key in keys_to_remove:
                        del enrichments[key]
                        logger.info(f"🗑️ Cache entry removed: {key}")

                    cache_data['metadata']['total_enrichments'] = len(enrichments)

                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2, ensure_ascii=False)

                    logger.info(f"✅ Cache cleared for: {location}")
            except Exception as cache_err:
                logger.warning(f"⚠️ Error clearing cache: {cache_err}")

        # Enriquecer ubicación
        enriched = await factory._enrich_location_once(location)

        return {
            "success": True,
            "location_info": enriched
        }

    except Exception as e:
        logger.error(f"❌ Error enriqueciendo ubicación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cities/available")
async def get_available_cities(
    q: str = Query(..., min_length=2, description="Search query for location (city, province, country)"),
    limit: int = Query(10, description="Maximum number of locations to return")
):
    """
    🌍 UBICACIONES DISPONIBLES - Retorna ciudades, provincias y países con eventos

    Autocomplete optimizado que busca en múltiples niveles geográficos:
    - 🏙️ Ciudades (prioridad 1)
    - 📍 Provincias/Estados (prioridad 2)
    - 🌍 Países (prioridad 3)

    Args:
        q: Búsqueda (mínimo 2 caracteres)
        limit: Máximo de resultados (default: 10)

    Returns:
        - locations: Lista de ubicaciones con eventos (ciudades, provincias, países)
        - total: Total de ubicaciones encontradas
    """
    try:
        from services.events_db_service import get_available_cities_with_events
        from services.gemini_factory import gemini_factory

        logger.info(f"🔍 Buscando ubicaciones (ciudades/provincias/países) con eventos para: '{q}'")

        # Buscar ubicaciones en MySQL que coincidan y tengan eventos
        locations = await get_available_cities_with_events(search_query=q, limit=limit)

        logger.info(f"✅ Encontradas {len(locations)} ubicaciones con eventos")

        # 🔥 SI NO HAY RESULTADOS, intentar detectar ciudad principal con Gemini
        if len(locations) == 0 and len(q) >= 3:
            logger.info(f"🤖 No hay resultados directos para '{q}', intentando detectar ciudad principal...")

            try:
                parent_city = await gemini_factory.get_parent_location(q)

                if parent_city:
                    logger.info(f"✅ Gemini detectó: '{q}' es parte de '{parent_city}'")

                    # Buscar eventos de la ciudad principal
                    parent_locations = await get_available_cities_with_events(search_query=parent_city, limit=1)

                    if parent_locations:
                        # Agregar como sugerencia con indicador especial
                        # Usar el mismo formato que get_available_cities_with_events
                        suggestion = {
                            "location": parent_city,
                            "location_type": "city",
                            "event_count": parent_locations[0].get("event_count", 0),
                            "displayName": f"{parent_city} (cerca de {q.title()})",
                            "is_suggestion": True,
                            "original_query": q
                        }
                        locations = [suggestion]
                        logger.info(f"💡 Sugiriendo '{parent_city}' como alternativa")
            except Exception as gemini_err:
                logger.warning(f"⚠️ Error en detección con Gemini: {gemini_err}")

        return {
            "success": True,
            "locations": locations,
            "total": len(locations)
        }

    except Exception as e:
        logger.error(f"❌ Error buscando ubicaciones disponibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neighborhoods/{city}")
async def get_neighborhoods_by_city(city: str):
    """
    🏘️ BARRIOS POR CIUDAD - Retorna barrios con conteo de eventos

    Args:
        city: Nombre de la ciudad (ej: "Buenos Aires")

    Returns:
        - city: Ciudad consultada
        - neighborhoods: Lista de barrios con event_count
        - total_neighborhoods: Total de barrios con eventos
        - total_events: Total de eventos en todos los barrios
    """
    try:
        import pymysql

        logger.info(f"🏘️ Obteniendo barrios de {city}")

        # Conectar a MySQL
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        # Query para obtener barrios con conteo
        query = '''
            SELECT neighborhood, COUNT(*) as event_count
            FROM events
            WHERE city = %s
            AND neighborhood IS NOT NULL
            AND neighborhood != ''
            GROUP BY neighborhood
            ORDER BY event_count DESC, neighborhood ASC
        '''

        cursor.execute(query, (city,))
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        # Formatear respuesta
        neighborhoods = [
            {
                "name": row['neighborhood'],
                "event_count": row['event_count']
            }
            for row in results
        ]

        total_events = sum(n['event_count'] for n in neighborhoods)

        logger.info(f"✅ Encontrados {len(neighborhoods)} barrios con {total_events} eventos")

        return {
            "success": True,
            "city": city,
            "neighborhoods": neighborhoods,
            "total_neighborhoods": len(neighborhoods),
            "total_events": total_events
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo barrios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/popular-places/{location}")
async def get_popular_places_nearby(location: str):
    """
    🎯 LUGARES POPULARES - Barrios/zonas con eventos REALES en la base de datos

    Obtiene los barrios con más eventos directamente de MySQL.
    NO usa IA - solo datos reales.

    Args:
        location: Ciudad de referencia (ej: "Buenos Aires", "Madrid", "Miami")

    Returns:
        - places: Lista con barrios que tienen eventos (ordenados por cantidad)
    """
    try:
        import pymysql

        logger.info(f"🎯 Buscando barrios populares en: {location}")

        # Conectar a MySQL
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        try:
            cursor = connection.cursor()

            # Query: Obtener barrios con eventos en esta ciudad (con info completa)
            query = '''
                SELECT
                    neighborhood,
                    city,
                    country,
                    province,
                    COUNT(*) as event_count
                FROM events
                WHERE city LIKE %s
                AND neighborhood IS NOT NULL
                AND neighborhood != ''
                AND start_datetime >= NOW()
                GROUP BY neighborhood, city, country, province
                ORDER BY event_count DESC
                LIMIT 10
            '''

            cursor.execute(query, (f'%{location}%',))
            results = cursor.fetchall()

            # Guardar info completa de cada barrio
            verified_places = []
            places_info = {}  # {nombre: {city, country, province}}
            for row in results:
                if row['neighborhood']:
                    verified_places.append(row['neighborhood'])
                    places_info[row['neighborhood']] = {
                        'city': row['city'],
                        'country': row['country'],
                        'province': row['province'],
                        'event_count': row['event_count']
                    }

            logger.info(f"✅ Encontrados {len(verified_places)} barrios con eventos en {location}")

            cursor.close()
        finally:
            connection.close()

        top_places = verified_places
        logger.info(f"✅ Lugares verificados con eventos: {top_places}")

        # 🔄 FALLBACK: Si hay menos de 5 barrios, ampliar búsqueda con IA
        if len(top_places) < 5:
            logger.warning(f"⚠️ Solo {len(top_places)} barrios encontrados. Ampliando búsqueda con IA...")

            # Pedirle a Grok barrios y ciudades cercanas para tener más opciones de match
            fallback_prompt = f"""Dame 15 barrios, zonas o ciudades cercanas a {location} donde pueda haber eventos culturales, fiestas o conciertos.

IMPORTANTE: Incluye barrios populares de {location} Y ciudades cercanas.

Responde SOLO con los 15 nombres separados por comas, sin números ni explicaciones:
nombre1, nombre2, nombre3, nombre4, nombre5, nombre6, nombre7, nombre8, nombre9, nombre10, nombre11, nombre12, nombre13, nombre14, nombre15
"""

            # 🔧 FIX: Importar y usar ai_manager correctamente
            from services.ai_manager import AIServiceManager
            ai_mgr = AIServiceManager()
            fallback_response = await ai_mgr.generate(
                prompt=fallback_prompt,
                temperature=0.3
            )

            fallback_places = [name.strip() for name in fallback_response.split(',')[:15]]
            logger.info(f"🔄 Fallback: IA sugirió 15 barrios/ciudades: {fallback_places}")

            # Verificar cuáles tienen eventos
            verify_connection_fallback = pymysql.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'events'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            try:
                verify_cursor_fallback = verify_connection_fallback.cursor()

                for place_name in fallback_places:
                    verify_query = '''
                        SELECT COUNT(*) as event_count
                        FROM events
                        WHERE start_datetime >= NOW()
                        AND (
                            city LIKE %s
                            OR neighborhood LIKE %s
                        )
                    '''

                    verify_cursor_fallback.execute(verify_query, (f'%{place_name}%', f'%{place_name}%'))
                    result = verify_cursor_fallback.fetchone()

                    if result and result['event_count'] > 0:
                        # Evitar duplicados (case-insensitive)
                        if place_name.lower() not in [p.lower() for p in top_places]:
                            top_places.append(place_name)
                            logger.info(f"✅ Fallback: '{place_name}' tiene {result['event_count']} eventos")

                verify_cursor_fallback.close()
            finally:
                verify_connection_fallback.close()

            logger.info(f"✅ Fallback completado. Total lugares: {top_places}")

        # Construir respuesta con info completa
        places_with_info = []
        for place in top_places:
            info = places_info.get(place, {
                'city': location,
                'country': None,
                'province': None,
                'event_count': 0
            })
            places_with_info.append({
                'name': place,
                'city': info.get('city', location),
                'country': info.get('country'),
                'province': info.get('province'),
                'event_count': info.get('event_count', 0)
            })

        return {
            "success": True,
            "places": top_places,  # Para compatibilidad (solo nombres)
            "places_info": places_with_info  # Info completa
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo lugares populares: {e}")
        # En caso de error, retornar vacío
        return {
            "success": False,
            "places": []
        }


@app.get("/api/events/related")
async def get_related_events_endpoint(
    category: Optional[str] = Query(None, description="Categoría del evento actual"),
    city: Optional[str] = Query(None, description="Ciudad del evento actual"),
    exclude: Optional[str] = Query(None, description="ID del evento a excluir"),
    limit: int = Query(6, description="Cantidad de eventos relacionados")
):
    """
    🔗 EVENTOS RELACIONADOS - Busca eventos de la misma categoría y/o ciudad

    Prioridad:
    1. Misma categoría + misma ciudad
    2. Misma categoría (cualquier ciudad)
    3. Misma ciudad (cualquier categoría)
    """
    from services.events_db_service import get_related_events

    result = get_related_events(
        category=category,
        city=city,
        exclude_id=exclude,
        limit=limit
    )

    return {
        "events": result.get('events', []),
        "total": result.get('total', 0),
        "filters": {
            "category": category,
            "city": city,
            "exclude": exclude
        },
        "error": result.get('error')
    }


@app.get("/api/events/city")
async def get_city_events(
    city: str = Query(..., description="Ciudad donde buscar eventos"),
    original_location: Optional[str] = Query(None, description="Ubicación original del usuario"),
    category: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """
    🏙️ EVENTOS EN CIUDAD ESPECÍFICA - Busca en una ciudad específica (solo MySQL)

    Args:
        city: Ciudad donde buscar (ej: "Merlo", "Morón", etc.)
        original_location: Ubicación original del usuario (ej: "Paso del Rey")

    Returns:
        - events: Lista de eventos
        - city: Ciudad donde se buscaron eventos
        - original_location: Ubicación original
    """
    try:
        from services.events_db_service import search_events_by_location
        import time

        # Buscar eventos en la ciudad específica
        logger.info(f"🏙️ Buscando eventos en: {city}" + (f" (desde {original_location})" if original_location else ""))

        start_time = time.time()

        # 🗄️ BUSCAR EN MYSQL (UN SOLO LLAMADO)
        events = await search_events_by_location(
            location=city,
            category=category,
            limit=limit,
            days_ahead=180
        )

        execution_time = f"{time.time() - start_time:.2f}s"

        # Agregar metadata a cada evento
        for event in events:
            event['search_city'] = city
            if original_location:
                event['original_location'] = original_location
                event['distance_note'] = f"Evento en {city}"

        logger.info(f"✅ Encontrados {len(events)} eventos en {city} en {execution_time}")

        return {
            "events": events,
            "city": city,
            "original_location": original_location,
            "total_events": len(events),
            "message": f"Se encontraron {len(events)} eventos en {city}",
            "execution_time": execution_time,
            "source": "mysql_database"
        }

    except Exception as e:
        logger.error(f"❌ Error buscando eventos en ciudad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 💾 CACHE GLOBAL DE CATEGORÍAS (evitar llamadas a IA repetidas)
_categories_cache = {}
_categories_cache_ttl = {}
import time

@app.get("/api/events/categories")
async def get_event_categories(
    location: Optional[str] = Query(None, description="Ubicación para filtrar categorías")
):
    """🏷️ CATEGORÍAS DINÁMICAS - Obtiene categorías únicas de eventos (CON CACHE)"""
    try:
        cache_key = location or "Buenos Aires"
        current_time = time.time()

        # ✅ Revisar caché (válido por 5 minutos)
        if cache_key in _categories_cache:
            if current_time - _categories_cache_ttl.get(cache_key, 0) < 300:  # 5 minutos
                logger.info(f"✅ Categorías CACHEADAS para {cache_key}")
                return _categories_cache[cache_key]

        logger.info(f"🔄 Generando categorías NUEVAS para {cache_key}...")

        # Consulta DIRECTA a MySQL sin IA (mucho más rápido)
        import os
        import pymysql
        from datetime import datetime, timedelta

        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            charset='utf8mb4'
        )

        cursor = connection.cursor()

        # Query rápida para categorías
        future_date = datetime.now() + timedelta(days=180)
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM events
            WHERE city LIKE %s
            AND (start_datetime >= NOW() OR start_datetime IS NULL)
            AND start_datetime <= %s
            GROUP BY category
            ORDER BY count DESC
        """, (f"%{cache_key}%", future_date))

        results = cursor.fetchall()
        cursor.close()
        connection.close()

        # Mapeo de categorías para normalizar
        category_mapping = {
            # Música
            'music': 'Música',
            'musica': 'Música',
            'música': 'Música',
            # Deportes
            'sports': 'Deportes',
            'deportes': 'Deportes',
            # Cultural
            'cultural': 'Cultural',
            # Tech
            'tech': 'Tech',
            'technology': 'Tech',
            'tecnologia': 'Tech',
            'tecnología': 'Tech',
            # Fiestas
            'party': 'Fiestas',
            'fiestas': 'Fiestas',
            'nightlife': 'Fiestas',
            # Festival
            'festival': 'Festival',
            # Teatro
            'theater': 'Teatro',
            'theatre': 'Teatro',
            'teatro': 'Teatro',
            # Comedy
            'comedy': 'Comedia',
            'comedia': 'Comedia',
            # General/Other
            'general': 'General',
            'other': 'General'
        }

        # Procesar categorías con sus counts reales de la DB
        category_counts = {}
        for row in results:
            category = row[0]
            count = row[1]  # ✅ Usar el count real de la DB, no contar como 1

            if category and category.strip():
                # Normalizar: lowercase y sin acentos
                normalized = category.lower().strip()
                # Usar mapeo si existe, sino capitalizar la original
                display_name = category_mapping.get(normalized, category.capitalize())
                # Sumar counts (por si múltiples categorías mapean a la misma)
                category_counts[display_name] = category_counts.get(display_name, 0) + count

        # Formatear resultado
        categories = [
            {'name': cat, 'count': count}
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        result = {'categories': categories, 'total': len(categories)}

        # 💾 Guardar en caché para próximas requests (TTL 5 minutos)
        _categories_cache[cache_key] = result
        _categories_cache_ttl[cache_key] = current_time

        logger.info(f"✅ {len(categories)} categorías" + (f" para {location}" if location else "") + " (guardadas en caché)")

        return result

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/nearby")
async def get_nearby_events(
    location: str = Query(..., description="Ubicación para detectar ciudades cercanas")
):
    """
    📍 CIUDADES CERCANAS - Usa IA para detectar ciudades cercanas

    Este endpoint NO busca eventos, solo retorna nombres de ciudades cercanas
    para que el frontend muestre botones. Cuando el usuario presiona un botón,
    el frontend llama a /api/events/stream con esa ciudad para buscar en MySQL.

    Args:
        location: Ubicación original (ej: "Villa Gesell", "Moreno")

    Returns:
        - nearby_cities: Lista de nombres de ciudades cercanas (para los botones)
        - original_location: Ubicación original
    """
    try:
        from services.gemini_factory import gemini_factory

        # Extraer ciudad de location (puede venir como "Villa Gesell, Argentina")
        city = location.split(',')[0].strip()

        logger.info(f"📍 Detectando ciudades cercanas a: {city}")

        # Usar Gemini para enriquecer ubicación y obtener ciudades cercanas
        enriched = await gemini_factory._enrich_location_once(city)

        nearby_cities = enriched.get('nearby_cities', [])

        logger.info(f"✅ Encontradas {len(nearby_cities)} ciudades cercanas: {nearby_cities}")

        return {
            "success": True,
            "nearby_cities": nearby_cities[:3],  # Solo 3 para los botones
            "original_location": city,
            "message": f"Encontradas {len(nearby_cities[:3])} ciudades cercanas a {city}" if nearby_cities else f"No se encontraron ciudades cercanas a {city}"
        }

    except Exception as e:
        logger.error(f"❌ Error detectando ciudades cercanas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/province")
async def get_province_events(
    location: str = Query(..., description="Ubicación original del usuario"),
    category: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """
    🌍 EVENTOS EN LA PROVINCIA/ESTADO - Busca en toda la provincia

    Para localidades chicas como "Paso del Rey", busca eventos
    en toda la provincia (ej: "Buenos Aires")

    Returns:
        - events: Lista de eventos de la provincia
        - location_info: Información de enriquecimiento
        - province: Provincia donde se buscaron eventos
    """
    try:
        from services.gemini_factory import gemini_factory

        factory = gemini_factory  # Singleton - no need to instantiate

        # Enriquecer ubicación UNA VEZ
        enriched = await factory._enrich_location_once(location)

        # Obtener la provincia
        province = enriched.get('state', '')

        if not province:
            return {
                "events": [],
                "location_info": enriched,
                "province": None,
                "message": f"No se pudo detectar la provincia para '{location}'"
            }

        # Buscar eventos en la provincia
        logger.info(f"🌍 Buscando eventos en provincia: {location} → {province}")

        result = await factory.execute_global_scrapers_with_details(
            location=province,
            category=category,
            limit=limit
        )

        events = result.get('events', [])

        # Agregar metadata a cada evento indicando que es de la provincia
        for event in events:
            event['is_province'] = True
            event['original_location'] = location
            event['province_location'] = province
            event['distance_note'] = f"Evento en {province}"

        return {
            "events": events,
            "location_info": enriched,
            "province": province,
            "total_events": len(events),
            "message": f"Se encontraron {len(events)} eventos en {province}",
            "scrapers_execution": result.get('scrapers_execution', {})
        }

    except Exception as e:
        logger.error(f"❌ Error buscando eventos de provincia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_events(
    location: Optional[str] = Query(None, description="Ubicación requerida"),
    category: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """
    🚀 SSE STREAMING ENDPOINT - Devuelve eventos de MySQL en tiempo real

    IMPORTANTE: Frontend usa EventSource, requiere formato SSE
    """
    from fastapi.responses import StreamingResponse
    import json
    import time

    async def event_generator():
        """Generator para SSE - Consulta MySQL directamente"""
        try:
            if not location:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Ubicación requerida'})}\n\n"
                return

            # Enviar evento de inicio
            yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos en {location}', 'location': location})}\n\n"

            # 🗄️ BUSCAR EN MYSQL
            from services.events_db_service import search_events_by_location

            start_time = time.time()
            logger.info(f"🔍 [/api/events] Consultando MySQL para ubicación: {location}")

            # Consultar base de datos (180 días = 6 meses hacia adelante)
            search_result = await search_events_by_location(
                location=location,
                category=category,
                limit=limit,
                days_ahead=180
            )

            # Extraer eventos y metadata de parent_city
            events = search_result.get('events', []) if isinstance(search_result, dict) else search_result
            parent_city = search_result.get('parent_city_detected') if isinstance(search_result, dict) else None
            original_location = search_result.get('original_location', location) if isinstance(search_result, dict) else location
            expanded_search = search_result.get('expanded_search', False) if isinstance(search_result, dict) else False

            execution_time = f"{time.time() - start_time:.2f}s"
            total_events = len(events)

            if total_events > 0:
                # Preparar datos del evento
                event_data = {
                    'type': 'events',
                    'scraper': 'mysql_database',
                    'events': events,
                    'count': total_events,
                    'total_events': total_events,
                    'execution_time': execution_time
                }

                # Agregar metadata de ciudad principal si existe
                if parent_city and expanded_search:
                    event_data['parent_city'] = parent_city
                    event_data['original_location'] = original_location
                    event_data['expanded_search'] = expanded_search
                    logger.info(f"📍 [/api/events] Búsqueda expandida: {original_location} → {parent_city}")

                # Enviar eventos desde base de datos
                yield f"data: {json.dumps(event_data)}\n\n"
                logger.info(f"📡 [/api/events] MySQL - {total_events} eventos enviados en {execution_time}")
            else:
                # No se encontraron eventos
                no_events_data = {
                    'type': 'no_events',
                    'scraper': 'mysql_database',
                    'count': 0,
                    'execution_time': execution_time,
                    'message': f'No hay eventos disponibles para {location}'
                }

                # Agregar metadata de ciudad principal si existe (incluso sin eventos)
                if parent_city and expanded_search:
                    no_events_data['parent_city'] = parent_city
                    no_events_data['original_location'] = original_location
                    no_events_data['expanded_search'] = expanded_search
                    logger.info(f"📍 [/api/events] Búsqueda expandida sin eventos: {original_location} → {parent_city}")

                yield f"data: {json.dumps(no_events_data)}\n\n"
                logger.info(f"📡 [/api/events] MySQL - 0 eventos para '{location}' en {execution_time}")

            # Enviar evento de completado
            yield f"data: {json.dumps({'type': 'complete', 'total_events': total_events, 'scrapers_completed': 1})}\n\n"
            logger.info(f"🏁 [/api/events] Streaming completado - {total_events} eventos desde MySQL")

        except Exception as e:
            logger.error(f"❌ [/api/events] Error en SSE streaming desde MySQL: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    # 🔥 RETORNAR EL STREAMING RESPONSE
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/events/categories")
async def get_event_categories(
    location: Optional[str] = Query("Buenos Aires", description="Ubicación para filtrar categorías")
):
    """
    📊 CATEGORÍAS DE EVENTOS - Devuelve categorías únicas con conteo

    Args:
        location: Ciudad/ubicación (default: "Buenos Aires")

    Returns:
        [{'name': 'music', 'count': 50}, {'name': 'sports', 'count': 30}, ...]
    """
    try:
        log_method_start("get_event_categories", location=location)

        # 🗄️ BUSCAR TODOS LOS EVENTOS DE LA UBICACIÓN
        from services.events_db_service import search_events_by_location

        # Consultar con límite alto para obtener todas las categorías
        logger.info(f"🔵 ANTES de llamar search_events_by_location")
        search_result = await search_events_by_location(
            location=location,
            limit=1000,  # Alto límite para capturar todas las categorías
            days_ahead=180  # 6 meses hacia adelante
        )
        logger.info(f"🟢 DESPUÉS de llamar search_events_by_location")

        # Debug: Ver qué tipo de resultado obtuvimos
        logger.info(f"🔍 search_result type: {type(search_result)}")
        logger.info(f"🔍 search_result value: {search_result}")

        # Extraer eventos (manejar diferentes tipos de respuesta)
        events = []
        if isinstance(search_result, dict):
            events = search_result.get('events', [])
        elif isinstance(search_result, list):
            events = search_result
        else:
            logger.error(f"❌ Tipo inesperado de search_result: {type(search_result)}")
            events = []

        logger.info(f"📊 Total events encontrados: {len(events)}")

        # 📊 CALCULAR CATEGORÍAS ÚNICAS CON CONTEO
        category_counts = {}
        for event in events:
            if isinstance(event, dict):
                category = event.get('category')
            else:
                logger.warning(f"⚠️ Evento no es dict: {type(event)}")
                continue
            if category:
                # Normalizar categoría (lowercase)
                category = category.lower()
                category_counts[category] = category_counts.get(category, 0) + 1

        # Convertir a lista de objetos
        categories = [
            {'name': cat, 'count': count}
            for cat, count in category_counts.items()
        ]

        # Ordenar por count descendente
        categories.sort(key=lambda x: x['count'], reverse=True)

        log_method_success(
            "get_event_categories",
            location=location,
            total_categories=len(categories),
            total_events=len(events)
        )

        return {
            'success': True,
            'location': location,
            'categories': categories,
            'total_categories': len(categories),
            'total_events': len(events)
        }

    except Exception as e:
        log_method_error("get_event_categories", str(e), location=location)
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
# Smart search endpoint with AI
@app.post("/api/smart/search")
async def smart_search(
    query: Dict[str, Any]
):
    """
    Smart search endpoint that processes natural language queries
    """
    try:
        # Handle both "query" and "search_query" fields
        search_query = query.get("query") or query.get("search_query", "")
        original_location = query.get("location", "Buenos Aires")

        logger.info(f"📍 SMART SEARCH - Query: '{search_query}', Location received: '{original_location}'")

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
                from services.gemini_factory import gemini_factory
                factory = gemini_factory  # Singleton - no need to instantiate
                
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
                    "scraper_used": "GeminiFactory",
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
                from services.gemini_factory import gemini_factory
                factory = gemini_factory  # Singleton - no need to instantiate
                
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
                    "scraper_used": "GeminiFactory",
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
    🔍 Obtener un evento específico por ID/título desde MySQL
    CRÍTICO: Este endpoint SIEMPRE retorna datos frescos con imágenes actualizadas
    """
    try:
        import pymysql
        import unicodedata

        logger.info(f"🔍 Buscando evento en MySQL: {event_id}")

        # Conectar a MySQL
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()
        event = None

        # 🔥 ESTRATEGIA 0: Buscar por UUID exacto (nueva URL format: /event/{uuid}/{slug})
        is_uuid = len(event_id) == 36 and event_id.count('-') == 4  # UUID format check
        if is_uuid:
            logger.info(f"🔍 Buscando por UUID exacto: {event_id}")
            cursor.execute('SELECT * FROM events WHERE id = %s LIMIT 1', (event_id,))
            event = cursor.fetchone()
            if event:
                logger.info(f"✅ Encontrado por UUID exacto: {event['title']}")

        # Si no es UUID o no encontró, continuar con estrategias de slug/keywords
        if not event:
            # Normalizar el event_id (remover guiones, convertir a espacios)
            event_id_normalized = event_id.lower().replace("-", " ")

            # Extraer palabras clave (filtrar palabras cortas/comunes)
            stop_words = {'de', 'la', 'el', 'y', 'en', 'del', 'los', 'las', 'con', 'por', 'para', 'a'}
            keywords = [word for word in event_id_normalized.split() if len(word) > 2 and word not in stop_words]

            logger.info(f"🔍 Keywords extraídas: {keywords}")

            # Estrategia 1: Buscar con todas las keywords (más estricto)
            if len(keywords) >= 3:
                conditions = []
                for kw in keywords:
                    conditions.append(f"LOWER(title) LIKE '%{kw}%'")

                query = f'''
                    SELECT *
                    FROM events
                    WHERE {' AND '.join(conditions)}
                    LIMIT 1
                '''

                cursor.execute(query)
                event = cursor.fetchone()

                if event:
                    logger.info(f"✅ Encontrado con TODAS las keywords: {event['title']}")

            # Estrategia 2: Si no encontró, buscar con 2+ keywords principales
            if not event and len(keywords) >= 2:
                # Usar las 2 keywords más largas (más específicas)
                main_keywords = sorted(keywords, key=len, reverse=True)[:2]
                conditions = [f"LOWER(title) LIKE '%{kw}%'" for kw in main_keywords]

                query = f'''
                    SELECT *
                    FROM events
                    WHERE {' AND '.join(conditions)}
                    LIMIT 1
                '''

                cursor.execute(query)
                event = cursor.fetchone()

                if event:
                    logger.info(f"✅ Encontrado con keywords principales {main_keywords}: {event['title']}")

            # Estrategia 3: Fallback al método original
            if not event:
                query = '''
                    SELECT *
                    FROM events
                    WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                        title, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
                        'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'))
                    LIKE LOWER(%s)
                    LIMIT 1
                '''

                search_pattern = f'%{event_id_normalized}%'
                cursor.execute(query, (search_pattern,))
                event = cursor.fetchone()

                if event:
                    logger.info(f"✅ Encontrado con búsqueda original: {event['title']}")

        # Agregar campos faltantes que el frontend espera
        if event and 'currency' not in event:
            event['currency'] = 'ARS'  # Default currency
        if event and 'is_free' not in event:
            event['is_free'] = False  # Default not free

        cursor.close()
        connection.close()

        if not event:
            logger.warning(f"⚠️ Evento no encontrado en MySQL: {event_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Event '{event_id}' not found in database"
            )

        logger.info(f"✅ Evento obtenido desde MySQL con imagen actualizada: {event['title']}")

        return {
            "status": "success",
            "event": event
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting event {event_id} from MySQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Update event category endpoint
@app.patch("/api/events/{event_id}/category")
async def update_event_category(event_id: str, request: dict):
    """
    Actualizar la categoría de un evento
    """
    try:
        import pymysql

        new_category = request.get('category')
        if not new_category:
            raise HTTPException(status_code=400, detail="Category is required")

        # Conectar a MySQL
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        # Normalizar el event_id para buscar por título
        event_id_normalized = event_id.replace('-', ' ')

        # Actualizar categoría
        update_query = '''
            UPDATE events
            SET category = %s
            WHERE LOWER(REPLACE(title, ' ', '-')) = LOWER(%s)
            OR LOWER(title) LIKE LOWER(%s)
        '''

        cursor.execute(update_query, (new_category, event_id, f'%{event_id_normalized}%'))
        connection.commit()

        rows_affected = cursor.rowcount

        cursor.close()
        connection.close()

        if rows_affected > 0:
            logger.info(f"✅ Categoría actualizada para evento {event_id}: {new_category}")
            return {
                "success": True,
                "message": f"Category updated to {new_category}",
                "rows_affected": rows_affected
            }
        else:
            raise HTTPException(status_code=404, detail="Event not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating category for {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Update event image endpoint
@app.post("/api/events/{event_id}/update-image")
async def update_event_image(event_id: str, request: Request):
    """
    Buscar y actualizar la imagen de un evento usando Google Images
    Si se pasa force_url, usa esa URL directamente sin buscar
    """
    try:
        import pymysql

        # 🔥 Parsear el body JSON correctamente
        body = await request.json()

        title = body.get('title')
        venue_name = body.get('venue_name', '')
        city = body.get('city', '')
        force_url = body.get('force_url')  # 🆕 URL forzada (opcional)

        if not title and not force_url:
            raise HTTPException(status_code=400, detail="Title or force_url is required")

        # 🆕 Si hay force_url, usarla directamente sin buscar
        if force_url:
            logger.info(f"🖼️ Usando imagen forzada para: {title or event_id}")
            image_url = force_url
        else:
            logger.info(f"🖼️ Buscando imagen para: {title} (venue: {venue_name}, city: {city})")

            # Usar el servicio de Google Images con 5 estrategias:
            # 1. Solo título
            # 2. Título + venue
            # 3. Solo venue
            # 4. Primeras 3 palabras
            # 5. Solo ciudad
            from services.google_images_service import search_google_image

            image_url = await search_google_image(title, venue=venue_name, city=city)

        if not image_url or 'gstatic' in image_url:
            logger.warning(f"⚠️ No se encontró imagen válida para: {title}")
            return {
                "success": False,
                "message": "No valid image found"
            }

        # Solo retornar la imagen encontrada (no actualizar DB porque eventos son de APIs)
        logger.info(f"✅ Imagen encontrada para '{title}': {image_url[:50]}...")

        # Actualizar en MySQL - Primero intentar por ID, luego por título
        try:
            connection = pymysql.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'events'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            cursor = connection.cursor()
            rows_affected = 0

            # 🔥 ESTRATEGIA 1: Intentar actualizar por UUID exacto (event_id del path)
            # El UUID viene de la URL /api/events/{event_id}/update-image
            is_uuid = len(event_id) == 36 and event_id.count('-') == 4  # UUID format check

            if is_uuid:
                logger.info(f"🔍 Actualizando evento por UUID exacto: {event_id}")
                update_query = 'UPDATE events SET image_url = %s WHERE id = %s'
                cursor.execute(update_query, (image_url, event_id))
                connection.commit()
                rows_affected = cursor.rowcount
                logger.info(f"✅ Actualización por UUID: {rows_affected} filas")

            # 🔥 ESTRATEGIA 2 (FALLBACK): Si no es UUID o no encontró, usar LIKE
            if rows_affected == 0 and title:
                import unicodedata

                # Extraer palabra clave principal del título (primera palabra significativa)
                title_words = title.lower().split()
                significant_words = [w for w in title_words if len(w) > 3 and w not in ['para', 'desde', 'hasta', 'como', 'este', 'esta', 'sobre']]

                if significant_words:
                    keyword = max(significant_words, key=len)
                    keyword_normalized = ''.join(
                        c for c in unicodedata.normalize('NFD', keyword)
                        if unicodedata.category(c) != 'Mn'
                    )
                    search_pattern = f'%%{keyword_normalized}%%'
                else:
                    title_normalized = ''.join(
                        c for c in unicodedata.normalize('NFD', title)
                        if unicodedata.category(c) != 'Mn'
                    )
                    search_pattern = f'%%{title_normalized}%%'

                logger.info(f"🔍 Fallback: Buscando eventos con patrón LIKE: {search_pattern}")

                update_query = '''
                    UPDATE events
                    SET image_url = %s
                    WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                        title, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
                        'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'))
                    LIKE LOWER(%s)
                '''
                cursor.execute(update_query, (image_url, search_pattern))
                connection.commit()
                rows_affected = cursor.rowcount
                logger.info(f"✅ Actualización LIKE '{search_pattern}': {rows_affected} filas")

            cursor.close()
            connection.close()

            if rows_affected > 0:
                logger.info(f"✅ Imagen guardada en MySQL para evento: {event_id} ({rows_affected} filas)")
                return {
                    "success": True,
                    "image_url": image_url,
                    "db_updated": True,
                    "rows_affected": rows_affected,
                    "message": "Image found and saved to database"
                }
            else:
                logger.warning(f"⚠️ No se encontró evento en MySQL para actualizar: {event_id} / {title}")
                return {
                    "success": True,
                    "image_url": image_url,
                    "db_updated": False,
                    "rows_affected": 0,
                    "message": "Image found but event not found in database"
                }
        except Exception as db_error:
            logger.error(f"❌ Error actualizando imagen en DB: {db_error}")
            return {
                "success": True,
                "image_url": image_url,
                "db_updated": False,
                "db_error": str(db_error),
                "message": "Image found but database update failed"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating image for {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/force-image")
async def force_event_image(request: Request):
    """
    🔥 FORZAR IMAGEN DIRECTAMENTE EN MYSQL
    Actualiza TODOS los eventos que coincidan con el patrón de título

    Body:
    {
        "title_pattern": "calamaro",  // Patrón para buscar (LIKE %pattern%)
        "image_url": "https://..."    // URL de imagen a establecer
    }
    """
    try:
        import pymysql

        body = await request.json()
        title_pattern = body.get('title_pattern', '')
        image_url = body.get('image_url', '')

        if not title_pattern or not image_url:
            raise HTTPException(status_code=400, detail="title_pattern and image_url are required")

        logger.info(f"🔥 Forzando imagen para patrón '{title_pattern}': {image_url[:50]}...")

        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        # Actualizar TODOS los eventos que coincidan con el patrón
        search_pattern = f'%%{title_pattern}%%'
        update_query = 'UPDATE events SET image_url = %s WHERE LOWER(title) LIKE LOWER(%s)'
        cursor.execute(update_query, (image_url, search_pattern))
        connection.commit()
        rows_affected = cursor.rowcount

        # Obtener los eventos actualizados para verificar
        cursor.execute('SELECT id, title FROM events WHERE LOWER(title) LIKE LOWER(%s) LIMIT 5', (search_pattern,))
        updated_events = cursor.fetchall()

        cursor.close()
        connection.close()

        logger.info(f"✅ {rows_affected} eventos actualizados con patrón '{title_pattern}'")

        return {
            "success": True,
            "rows_affected": rows_affected,
            "title_pattern": title_pattern,
            "image_url": image_url,
            "sample_events": updated_events
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error forzando imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/bulk-update-images-stream")
async def bulk_update_images_stream(request: Request):
    """
    🚀 ACTUALIZACIÓN MASIVA DE IMÁGENES CON STREAMING

    Procesa eventos y envía actualizaciones en tiempo real vía SSE.
    El frontend puede actualizar las tarjetas a medida que se procesan.
    """
    try:
        body = await request.json()
        events = body.get('events', [])

        if not events:
            async def error_generator():
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "No events provided"})
                }
            return EventSourceResponse(error_generator())

        logger.info(f"🚀 Iniciando actualización masiva con streaming para {len(events)} eventos")

        async def image_update_generator():
            import asyncio
            from asyncio import Queue

            # Cola para comunicar resultados entre tasks
            result_queue = Queue()

            # Enviar evento de inicio
            yield {
                "event": "update_start",
                "data": json.dumps({
                    "total": min(len(events), 50),
                    "message": "Iniciando actualización de imágenes en paralelo..."
                })
            }

            # Función que procesa un evento y pone resultado en la cola
            async def update_single_event(event, idx):
                try:
                    title = event.get('title', '')
                    venue_name = event.get('venue_name', '')
                    city = event.get('city', '')
                    description = event.get('description', '')
                    current_image = event.get('image_url', '')
                    event_id = event.get('id', '')

                    # SIEMPRE buscar la mejor imagen disponible (no omitir)
                    logger.debug(f"🔍 Buscando mejor imagen para: {title}")

                    # Buscar nueva imagen con 3 etapas: título → keywords → venue
                    from services.google_images_service import search_google_image
                    image_url = await search_google_image(title, venue=venue_name, city=city, description=description)

                    if not image_url or 'gstatic' in image_url:
                        logger.debug(f"⚠️ No se encontró imagen para: {title}")
                        await result_queue.put({"failed": True})
                        return

                    # Detectar placeholders genéricos
                    placeholder_patterns = [
                        'unsplash', 'placeholder', 'lorem', 'picsum', 'via.placeholder',
                        'placehold', 'dummyimage', 'fakeimg', 'lorempixel'
                    ]

                    current_is_placeholder = any(p in (current_image or '').lower() for p in placeholder_patterns)
                    new_is_placeholder = any(p in image_url.lower() for p in placeholder_patterns)

                    # Si ambas son placeholders → omitir (no hay mejora)
                    if current_is_placeholder and new_is_placeholder:
                        logger.debug(f"⏭️ Ambas son placeholders para '{title}' - omitiendo")
                        await result_queue.put({"skipped": True})
                        return

                    # Si la nueva también es placeholder pero actual no → omitir (empeoraría)
                    if new_is_placeholder and not current_is_placeholder:
                        logger.debug(f"⏭️ Nueva imagen es placeholder para '{title}' - omitiendo")
                        await result_queue.put({"skipped": True})
                        return

                    # Si URLs son iguales y no son placeholders → omitir
                    if current_image == image_url:
                        logger.debug(f"⏭️ Misma imagen para '{title}' - omitiendo")
                        await result_queue.put({"skipped": True})
                        return

                    # ACTUALIZAR: placeholder → real, o real → real diferente
                    if current_is_placeholder and not new_is_placeholder:
                        logger.info(f"✨ Reemplazando placeholder con imagen real: {title}")
                    else:
                        logger.info(f"🔄 Actualizando imagen: {title}")

                    # Actualizar en MySQL
                    import unicodedata
                    title_normalized = ''.join(
                        c for c in unicodedata.normalize('NFD', title)
                        if unicodedata.category(c) != 'Mn'
                    )

                    connection = pymysql.connect(
                        host=os.getenv('MYSQL_HOST', 'localhost'),
                        port=int(os.getenv('MYSQL_PORT', 3306)),
                        user=os.getenv('MYSQL_USER', 'root'),
                        password=os.getenv('MYSQL_PASSWORD', ''),
                        database=os.getenv('MYSQL_DATABASE', 'events'),
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor
                    )

                    cursor = connection.cursor()

                    update_query = '''
                        UPDATE events
                        SET image_url = %s
                        WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                            title, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
                            'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'))
                        LIKE LOWER(%s)
                    '''

                    search_pattern = f'%{title_normalized}%'
                    cursor.execute(update_query, (image_url, search_pattern))
                    connection.commit()
                    rows_affected = cursor.rowcount

                    cursor.close()
                    connection.close()

                    if rows_affected > 0:
                        logger.info(f"✅ Imagen mejorada: {title}")
                        await result_queue.put({
                            "success": True,
                            "id": event_id,
                            "title": title,
                            "image_url": image_url
                        })
                    else:
                        await result_queue.put({"failed": True})

                except Exception as e:
                    logger.error(f"❌ Error procesando '{event.get('title', 'unknown')}': {e}")
                    await result_queue.put({"failed": True})

            # Lanzar todas las tareas en paralelo con semaphore
            semaphore = asyncio.Semaphore(5)  # Máximo 5 en paralelo

            async def bounded_update(event, idx):
                async with semaphore:
                    await update_single_event(event, idx)

            # Crear todas las tareas (SOLO 1 PARA PRUEBA)
            tasks = [asyncio.create_task(bounded_update(event, idx))
                     for idx, event in enumerate(events[:1])]  # Solo primer evento

            # Procesar resultados a medida que llegan
            successful = 0
            skipped = 0
            failed = 0
            total_events = len(tasks)
            processed = 0

            while processed < total_events:
                result = await result_queue.get()
                processed += 1

                if result.get('success'):
                    successful += 1
                    # Enviar update al frontend
                    yield {
                        "event": "image_updated",
                        "data": json.dumps({
                            "id": result['id'],
                            "title": result['title'],
                            "image_url": result['image_url'],
                            "progress": int(processed / total_events * 100)
                        })
                    }
                elif result.get('skipped'):
                    skipped += 1
                else:
                    failed += 1

            # Esperar que todas las tareas terminen
            await asyncio.gather(*tasks, return_exceptions=True)

            # Enviar evento de finalización
            yield {
                "event": "update_complete",
                "data": json.dumps({
                    "successful": successful,
                    "skipped": skipped,
                    "failed": failed,
                    "total": total_events
                })
            }

        return EventSourceResponse(image_update_generator())

    except Exception as e:
        logger.error(f"❌ Error en bulk update stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Test endpoint para probar búsqueda de imágenes con palabra hardcodeada
@app.get("/api/test/image-search")
async def test_image_search():
    """
    🧪 Endpoint de prueba para búsqueda de imágenes en Google
    Busca imágenes para palabras fáciles como "pizza", "cafe", "music"
    """
    try:
        from services.google_images_service import search_google_image

        # Probar con palabras fáciles
        test_queries = [
            ("pizza", ""),
            ("cafe", "Buenos Aires"),
            ("music concert", ""),
            ("football", "")
        ]

        results = []
        for query, venue in test_queries:
            logger.info(f"🧪 Probando búsqueda: '{query}' (venue: '{venue}')")
            image_url = await search_google_image(query, venue=venue)
            results.append({
                "query": query,
                "venue": venue,
                "image_url": image_url,
                "found": image_url is not None
            })

        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Similar events streaming endpoint
@app.get("/api/events/{event_id}/similar/stream")
async def stream_similar_events(event_id: str):
    """
    🎯 SSE STREAMING - Eventos similares del mismo lugar

    Envía progresivamente eventos similares basados en:
    - Mismo lugar/ciudad
    - Misma categoría
    - Precio similar
    - Fechas próximas
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    async def similar_events_generator():
        try:
            # 1. Buscar el evento principal primero
            from services.hierarchical_factory import fetch_from_all_sources_internal
            result = await fetch_from_all_sources_internal("Buenos Aires")

            events = result.get("events", [])

            # Encontrar el evento solicitado
            found_event = None
            for event in events:
                title_lower = event['title'].lower()
                simple_id = title_lower.replace(" ", "-").replace(",", "").replace(".", "").replace("(", "").replace(")", "")
                title_match = title_lower.replace(" ", "-")
                event_id_lower = event_id.lower()
                event_id_spaces = event_id.replace("-", " ").lower()

                if (simple_id == event_id_lower or
                    title_match == event_id_lower or
                    title_lower == event_id_spaces or
                    title_lower.startswith(event_id_spaces) or
                    event_id_spaces in title_lower):
                    found_event = event
                    break

            if not found_event:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Evento no encontrado'})}\n\n"
                return

            # 2. Extraer criterios del evento principal
            event_category = found_event.get('category', '').lower()
            event_location = found_event.get('location', 'Buenos Aires')
            event_price = found_event.get('price', 0) if not found_event.get('is_free') else 0
            event_title = found_event.get('title', '')
            event_venue = found_event.get('venue_name', '')

            yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos similares en {event_location}'})}\n\n"
            logger.info(f"🎯 Buscando eventos similares para '{event_title}' en {event_location}")

            # 3. Calcular score de similitud para cada evento
            similar_events = []
            for event in events:
                # Skip el evento actual
                if event.get('title') == event_title:
                    continue

                # Score de similitud
                score = 0

                # 1️⃣ Mismo lugar/ciudad (+50 puntos - MÁS IMPORTANTE)
                if event.get('location', '').lower() == event_location.lower():
                    score += 50

                # 2️⃣ Misma categoría (+30 puntos)
                if event.get('category', '').lower() == event_category:
                    score += 30

                # 3️⃣ Precio similar (+15 puntos)
                event_event_price = event.get('price', 0) if not event.get('is_free') else 0
                if event_price == 0 and event_event_price == 0:
                    score += 15  # Ambos gratis
                elif event_price > 0 and event_event_price > 0:
                    price_ratio = min(event_price, event_event_price) / max(event_price, event_event_price)
                    if price_ratio > 0.5:  # Precios similares (dentro del 50%)
                        score += 15

                # 4️⃣ Mismo venue (+5 puntos bonus)
                if event.get('venue_name') == event_venue:
                    score += 5

                # Solo agregar eventos con score >= 50 (al menos mismo lugar)
                if score >= 50:
                    similar_events.append({
                        **event,
                        'similarity_score': score
                    })

            # 4. Ordenar por score y enviar progresivamente
            similar_events.sort(key=lambda x: x['similarity_score'], reverse=True)

            # Enviar eventos de a uno con delay para efecto progresivo
            sent_count = 0
            for similar_event in similar_events[:6]:  # Top 6 eventos similares
                yield f"data: {json.dumps({'type': 'event', 'event': similar_event, 'index': sent_count})}\n\n"
                sent_count += 1
                logger.info(f"📡 SSE: Evento similar enviado ({sent_count}/6): {similar_event['title']} (score: {similar_event['similarity_score']})")

                # Delay de 100ms entre eventos para efecto visual
                await asyncio.sleep(0.1)

            # 5. Enviar evento de completado
            yield f"data: {json.dumps({'type': 'complete', 'total': sent_count})}\n\n"
            logger.info(f"✅ SSE completado: {sent_count} eventos similares enviados")

        except Exception as e:
            logger.error(f"❌ Error en stream de eventos similares: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(similar_events_generator(), media_type="text/event-stream")


# AI recommendation endpoint
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
        # 🔧 FIX: result puede ser lista o dict dependiendo del scraper
        if isinstance(result, list):
            events = result
        else:
            events = result.get("events", []) if result else []
    
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

# AI nearby cities endpoint
@app.get("/api/ai/nearby-cities")
async def ai_nearby_cities(location: str, limit: int = 10):
    """Get nearby cities using Gemini AI"""
    try:
        from services.ai_service import get_nearby_cities_with_ai

        logger.info(f"🌍 Getting nearby cities for: {location}")

        # Use AI to get nearby cities
        cities = await get_nearby_cities_with_ai(location, limit)

        if not cities:
            return {
                "success": False,
                "error": "No nearby cities found",
                "cities": []
            }

        return {
            "success": True,
            "location": location,
            "cities": cities,
            "count": len(cities)
        }

    except Exception as e:
        logger.error(f"❌ Error getting nearby cities: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "cities": []
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


@app.post("/api/ai/event-insight")
async def event_insight(data: Dict[str, Any]):

    try:

        from services.ai_manager import AIServiceManager


        title = data.get("title", "")

        category = data.get("category", "")

        venue_name = data.get("venue_name", "")

        price = data.get("price", "")



        logger.info(f"✨ Generando insight con IA para: {title[:40]}... ({category})")



        # Prompt detallado para describir qué esperar del evento

        prompt = f"""Genera una descripción detallada y atractiva (2-3 oraciones, máximo 250 caracteres) de qué puede esperar el asistente en este evento:

Título: {title}

Categoría: {category}

Lugar: {venue_name}

Precio: {price if price else 'Gratis'}



Describe la experiencia, ambiente, y qué hace especial a este evento. Sé específico y entusiasta. Responde SOLO la descripción, sin títulos ni explicaciones adicionales."""



        manager = AIServiceManager()



        # Generar con IA (Grok es muy rápido, <1 segundo)

        response = await manager.generate(

            prompt=prompt,

            temperature=0.7,

            use_fallback=True

        )



        if response:

            result = {

                "success": True,

                "insight": {

                    "quick_insight": response[:300]  # Limitar a 300 caracteres para descripciones detalladas

                }

            }

            logger.info(f"✅ Insight generado: {response[:50]}...")

            return result

        else:

            # Fallback a texto genérico si IA falla

            fallback_text = f"Gran evento de {category} en {venue_name or 'la ciudad'}"

            return {

                "success": True,

                "fallback": {

                    "quick_insight": fallback_text

                },

                "insight": {

                    "quick_insight": fallback_text

                }

            }



    except Exception as e:

        logger.error(f"❌ Error generando insight: {e}")



        # Fallback genérico en caso de error

        fallback_text = f"Evento imperdible de {data.get('category', 'entretenimiento')}"

        return {

            "success": False,

            "error": str(e),

            "fallback": {

                "quick_insight": fallback_text

            },

            "insight": {

                "quick_insight": fallback_text

            }

        }

# ============================================
# 🤖 ENDPOINTS DE GESTIÓN DE AI PROVIDERS
# ============================================

@app.get("/api/ai/provider/status")
async def get_ai_provider_status():
    """
    📊 ESTADO DE PROVIDERS DE IA

    Retorna el estado de todos los providers de IA disponibles
    y cuál está configurado como preferido

    Returns:
        {
            "preferred": "grok",
            "providers": {
                "grok": {"configured": true, "name": "GrokProvider"},
                "groq": {"configured": false, "name": "GroqProvider"},
                "gemini": {"configured": true, "name": "GeminiProvider"},
                ...
            }
        }
    """
    try:
        from services.ai_manager import AIServiceManager

        manager = AIServiceManager()
        status = manager.get_provider_status()

        logger.info(f"📊 Estado de providers solicitado - Preferido: {status['preferred']}")
        return status

    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de providers: {e}")
        return {
            "error": str(e),
            "preferred": "unknown",
            "providers": {}
        }


@app.post("/api/ai/provider/set")
async def set_ai_provider(data: Dict[str, Any]):
    """
    🔄 CAMBIAR PROVIDER DE IA PREFERIDO

    Args:
        provider: Nombre del provider (grok, groq, gemini, perplexity, openrouter)

    Returns:
        {
            "success": true,
            "provider": "grok",
            "message": "Provider cambiado exitosamente"
        }
    """
    try:
        from services.ai_manager import AIServiceManager

        provider = data.get("provider", "").lower()

        if not provider:
            return {
                "success": False,
                "error": "Provider no especificado"
            }

        manager = AIServiceManager()
        success = manager.set_preferred_provider(provider)

        if success:
            logger.info(f"✅ Provider cambiado a: {provider}")
            return {
                "success": True,
                "provider": provider,
                "message": f"Provider cambiado a {provider} exitosamente"
            }
        else:
            logger.warning(f"⚠️ No se pudo cambiar a provider: {provider}")
            return {
                "success": False,
                "error": f"Provider {provider} no está configurado o no es válido"
            }

    except Exception as e:
        logger.error(f"❌ Error cambiando provider: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/ai/generate-event-context")
async def generate_event_context_endpoint(data: Dict[str, Any]):
    """
    🎨 GENERAR CONTEXTO ADICIONAL PARA EVENTO

    Usa IA para generar información adicional interesante sobre un evento:
    - Curiosidades
    - Qué llevar
    - Ambiente esperado
    - Tips locales

    Args:
        event_data: {
            title, category, venue_name, city, start_datetime
        }

    Returns:
        {
            "curiosidades": [...],
            "que_llevar": [...],
            "ambiente_esperado": "...",
            "tip_local": "..."
        }
    """
    try:
        from services.ai_manager import generate_event_context

        event_data = data.get("event_data", data)  # Soportar ambos formatos

        logger.info(f"🎨 Generando contexto para: {event_data.get('title', 'Unknown')}")

        context = await generate_event_context(event_data)

        if context:
            return {
                "success": True,
                **context
            }
        else:
            return {
                "success": False,
                "error": "No se pudo generar contexto"
            }

    except Exception as e:
        logger.error(f"❌ Error generando contexto de evento: {e}")
        return {
            "success": False,
            "error": str(e)
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
        from services.gemini_factory import gemini_factory
        factory = gemini_factory  # Singleton - no need to instantiate
        
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
        from services.gemini_factory import gemini_factory
        factory = gemini_factory  # Singleton - no need to instantiate
        
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


# ═══════════════════════════════════════════════════════════════════
# 🖼️ CLOUDINARY IMAGE MIGRATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

from services.cloudinary_service import (
    upload_image_from_url,
    test_cloudinary_connection,
    batch_migrate_images
)

@app.get("/api/admin/cloudinary/status")
async def cloudinary_status():
    """Check Cloudinary configuration status"""
    return await test_cloudinary_connection()


@app.post("/api/admin/cloudinary/migrate-image")
async def migrate_single_image(image_url: str, event_id: Optional[str] = None):
    """
    Migrate a single image to Cloudinary

    Args:
        image_url: URL of the image to migrate
        event_id: Optional event ID for naming
    """
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")

    public_id = f"event_{event_id}" if event_id else None
    new_url = await upload_image_from_url(image_url, folder="eventos", public_id=public_id)

    if new_url:
        return {
            "success": True,
            "original_url": image_url,
            "cloudinary_url": new_url
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to upload image to Cloudinary")


@app.post("/api/admin/cloudinary/migrate-all")
async def migrate_all_images(limit: int = 50, city: Optional[str] = None):
    """
    Migrate all event images to Cloudinary

    Args:
        limit: Maximum number of images to migrate (default 50)
        city: Optional city filter
    """
    import pymysql

    try:
        # Connect to MySQL (same as other endpoints)
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        # Get events with non-cloudinary images
        if city:
            cursor.execute("""
                SELECT id, title, image_url, city, category
                FROM events
                WHERE image_url IS NOT NULL
                AND image_url != ''
                AND image_url NOT LIKE '%%cloudinary.com%%'
                AND image_url NOT LIKE '%%example.com%%'
                AND city LIKE %s
                LIMIT %s
            """, (f"%{city}%", limit))
        else:
            cursor.execute("""
                SELECT id, title, image_url, city, category
                FROM events
                WHERE image_url IS NOT NULL
                AND image_url != ''
                AND image_url NOT LIKE '%%cloudinary.com%%'
                AND image_url NOT LIKE '%%example.com%%'
                LIMIT %s
            """, (limit,))

        events = cursor.fetchall()

        stats = {
            "total": len(events),
            "migrated": 0,
            "failed": 0,
            "updated_events": []
        }

        for event in events:
            event_id = str(event["id"])
            original_url = event["image_url"]

            # Upload to Cloudinary
            new_url = await upload_image_from_url(
                original_url,
                folder="eventos",
                public_id=f"event_{event_id[:8]}"
            )

            if new_url:
                # Update database
                cursor.execute(
                    "UPDATE events SET image_url = %s WHERE id = %s",
                    (new_url, event["id"])
                )
                connection.commit()

                stats["migrated"] += 1
                stats["updated_events"].append({
                    "id": event_id,
                    "title": event["title"],
                    "old_url": original_url,
                    "new_url": new_url
                })
            else:
                stats["failed"] += 1

        cursor.close()
        connection.close()

        return {
            "success": True,
            "stats": stats
        }

    except pymysql.Error as e:
        logger.error(f"MySQL connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/cloudinary/pending")
async def get_pending_images(limit: int = 100, city: Optional[str] = None):
    """
    Get list of events with images not yet in Cloudinary
    """
    import pymysql

    try:
        # Connect to MySQL (same as other endpoints)
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        if city:
            cursor.execute("""
                SELECT id, title, image_url, city, category
                FROM events
                WHERE image_url IS NOT NULL
                AND image_url != ''
                AND image_url NOT LIKE '%%cloudinary.com%%'
                AND city LIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (f"%{city}%", limit))
        else:
            cursor.execute("""
                SELECT id, title, image_url, city, category
                FROM events
                WHERE image_url IS NOT NULL
                AND image_url != ''
                AND image_url NOT LIKE '%%cloudinary.com%%'
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

        events = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "total_pending": len(events),
            "events": events
        }

    except pymysql.Error as e:
        logger.error(f"MySQL connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting pending images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Fix encoding for Windows console to support emojis
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # Beautiful startup banner with colors
    print("\n" + Fore.CYAN + "="*60)
    print(Fore.YELLOW + " "*20 + "🎉 EVENTOS VISUALIZER 🎉")
    print(Fore.WHITE + " "*18 + "Backend Server Starting...")
    print(Fore.CYAN + "="*60 + Style.RESET_ALL)

    print(Fore.MAGENTA + "\n📍 ENDPOINTS DISPONIBLES:")
    print(Fore.BLUE + "─"*60)
    print(Fore.GREEN + f"  🏠 Server:     {Fore.WHITE}{BACKEND_URL}")
    print(Fore.GREEN + f"  💚 Health:     {Fore.WHITE}{BACKEND_URL}/health")
    print(Fore.GREEN + f"  📚 API Docs:   {Fore.WHITE}{BACKEND_URL}/docs")
    print(Fore.GREEN + f"  🔧 Swagger UI: {Fore.WHITE}{BACKEND_URL}/redoc")

    ws_url = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    print(f"  🔌 WebSocket:  {ws_url}/ws/notifications")

    print(Fore.MAGENTA + "\n🔥 SERVICIOS ACTIVOS:")
    print(Fore.BLUE + "─"*60)
    print(Fore.GREEN + "  ✅ Gemini AI Integration")
    print(Fore.GREEN + "  ✅ Location Detection Service")
    print(Fore.GREEN + "  ✅ Multi-Source Event Scraping")
    print(Fore.GREEN + "  ✅ Real-time WebSocket Support")
    print(Fore.GREEN + "  ✅ Chat Memory Manager")

    print(Fore.MAGENTA + "\n🎯 APIS CONFIGURADAS:")
    print(Fore.BLUE + "─"*60)
    if os.getenv("EVENTBRITE_API_KEY"):
        print(Fore.GREEN + "  ✅ Eventbrite API")
    else:
        print(Fore.YELLOW + "  ⚠️  Eventbrite API (no key)")
    if os.getenv("TICKETMASTER_API_KEY"):
        print(Fore.GREEN + "  ✅ Ticketmaster API")
    else:
        print(Fore.YELLOW + "  ⚠️  Ticketmaster API (no key)")
    if os.getenv("RAPIDAPI_KEY"):
        print(Fore.GREEN + "  ✅ Facebook Events (RapidAPI)")
    else:
        print(Fore.YELLOW + "  ⚠️  Facebook Events (no key)")
    if os.getenv("GEMINI_API_KEY"):
        print(Fore.GREEN + "  ✅ Google Gemini AI")
    else:
        print(Fore.YELLOW + "  ⚠️  Google Gemini AI (no key)")

    print(Fore.MAGENTA + "\n💾 DATABASE STATUS:")
    print(Fore.BLUE + "─"*60)
    if os.getenv("DATABASE_URL"):
        print(Fore.GREEN + "  🔗 PostgreSQL: Configured")
    else:
        print(Fore.YELLOW + "  ⚠️  PostgreSQL: Not configured (using in-memory)")

    print("\n" + Fore.CYAN + "="*60)
    print(Fore.YELLOW + Style.BRIGHT + " "*15 + "🚀 SERVER READY TO ROCK! 🚀")
    print(Fore.CYAN + "="*60 + Style.RESET_ALL + "\n")
    
    # Use app directly instead of module string to avoid re-import issues
    # 🔥 REGLA CRÍTICA: Escuchar en todas las interfaces (0.0.0.0) para SSE desde frontend
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",  # Todas las interfaces - permite SSE desde frontend
            port=BACKEND_PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(Fore.RED + "\n" + "="*60)
        print(Fore.RED + Style.BRIGHT + "❌ ERROR FATAL AL INICIAR SERVIDOR:")
        print(Fore.RED + "="*60)
        print(Fore.YELLOW + f"\n{type(e).__name__}: {str(e)}")
        print(Fore.WHITE + "\nDetalles completos del error:")
        import traceback
        traceback.print_exc()
        print(Fore.RED + "\n" + "="*60 + Style.RESET_ALL)
        raise# Force reload do., 23 de nov. de 2025 13:33:42
