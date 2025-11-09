"""
FastAPI App Factory
Configuración centralizada de la aplicación
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
# from middleware.timeout_interceptor import TimeoutInterceptor  # Comentado - middleware no existe


def setup_logging():
    """
    Configurar logging de la aplicación
    """
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    # Startup
    logging.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logging.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logging.info(f"🌐 Host: {settings.HOST}:{settings.PORT}")
    
    # Inicializar servicios aquí si es necesario
    # await initialize_database()
    # await initialize_cache()
    
    yield
    
    # Shutdown
    logging.info("🔄 Shutting down application")
    # Cleanup servicios aquí
    # await close_database()
    # await close_cache()


def create_app() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI
    """
    # Configurar logging
    setup_logging()
    
    # Crear aplicación
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="API para agregación de eventos de múltiples fuentes",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Middleware de timeout (comentado - middleware no existe)
    # app.add_middleware(TimeoutInterceptor, timeout_seconds=settings.REQUEST_TIMEOUT)
    
    # Handlers de errores globales
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.DEBUG else "Something went wrong"
            }
        )
    
    # Incluir routers
    register_routers(app)
    
    return app


def register_routers(app: FastAPI):
    """
    Registrar todos los routers de la aplicación
    """
    # Import solo los routers que existen
    from api.v1.routers import sources, search, websocket

    # Health endpoint básico
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "eventos-visualizer",
            "version": settings.APP_VERSION
        }

    # 🌍 Location enrichment endpoint
    @app.get("/api/location/enrichment")
    async def location_enrichment(location: str):
        """Enriquecer ubicación con ciudades cercanas y provincia"""
        logging.info(f"📍 Location enrichment request: {location}")

        # Parse location
        parts = location.split(',')
        city = parts[0].strip() if parts else location

        return {
            "success": True,
            "location_info": {
                "city": city,
                "state": "Buenos Aires",  # Mock
                "country": "Argentina",
                "nearby_cities": [
                    f"{city} Centro",
                    f"{city} Norte",
                    f"{city} Sur"
                ],
                "needs_expansion": False
            }
        }

    # 📍 Nearby events endpoint
    @app.get("/api/events/nearby")
    async def nearby_events(location: str):
        """Buscar eventos en ciudades cercanas"""
        logging.info(f"📍 Nearby events request: {location}")

        return {
            "success": True,
            "events": [],
            "message": f"No hay eventos cercanos disponibles para {location}"
        }

    # 🌍 Province events endpoint
    @app.get("/api/events/province")
    async def province_events(location: str):
        """Buscar eventos en toda la provincia"""
        logging.info(f"🌍 Province events request: {location}")

        return {
            "success": True,
            "events": [],
            "message": f"No hay eventos de provincia disponibles para {location}"
        }

    # Registrar routers con prefijos apropiados
    app.include_router(
        sources.router,
        prefix="/api",
        tags=["Sources"]
    )

    app.include_router(
        search.router,
        prefix="/api",
        tags=["Search"]
    )

    app.include_router(
        websocket.router,
        tags=["WebSocket"]
    )


# Crear instancia de la app
app = create_app()