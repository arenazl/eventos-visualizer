"""
Dependency Injection para FastAPI
Proveedores de dependencias compartidas
"""
import asyncpg
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Request
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Cache de conexiones
_connection_pool: Optional[asyncpg.Pool] = None


async def get_database_pool() -> asyncpg.Pool:
    """
    Obtener pool de conexiones PostgreSQL
    """
    global _connection_pool
    
    if _connection_pool is None:
        try:
            database_url = settings.get_database_url()
            _connection_pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                command_timeout=10
            )
            logger.info("✅ Database pool created")
        except Exception as e:
            logger.error(f"❌ Failed to create database pool: {e}")
            raise HTTPException(500, "Database connection failed")
    
    return _connection_pool


async def get_database() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependency para obtener conexión de base de datos
    """
    pool = await get_database_pool()
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(500, "Database operation failed")


def get_settings():
    """
    Dependency para obtener configuración
    """
    return settings


async def verify_api_key(request: Request) -> bool:
    """
    Verificar API key si está configurada
    """
    # Por ahora, sin autenticación
    # En el futuro: verificar headers de auth
    return True


class CommonParams:
    """
    Parámetros comunes para queries
    """
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        location: Optional[str] = None
    ):
        self.skip = skip
        self.limit = min(limit, 100)  # Max 100 items
        self.location = location


def get_common_params(
    skip: int = 0,
    limit: int = 20,
    location: Optional[str] = None
) -> CommonParams:
    """
    Dependency para parámetros comunes
    """
    return CommonParams(skip=skip, limit=limit, location=location)


# Servicios compartidos
class ServiceContainer:
    """
    Container para servicios singleton
    """
    _instance = None
    _services = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_service(self, service_name: str):
        """
        Obtener servicio por nombre
        """
        if service_name not in self._services:
            # Lazy loading de servicios
            self._services[service_name] = self._create_service(service_name)
        
        return self._services[service_name]
    
    def _create_service(self, service_name: str):
        """
        Crear instancia de servicio
        """
        try:
            if service_name == "pattern_service":
                from services.pattern_service import PatternService
                return PatternService()
            elif service_name == "ai_service":
                from services.ai_service import AIEventService
                return AIEventService()
            elif service_name == "industrial_factory":
                from services.industrial_factory import IndustrialFactory
                return IndustrialFactory()
            else:
                logger.warning(f"Unknown service: {service_name}")
                return None
        except ImportError as e:
            logger.warning(f"Could not import service {service_name}: {e}")
            return None


def get_service_container() -> ServiceContainer:
    """
    Dependency para obtener container de servicios
    """
    return ServiceContainer()


def get_pattern_service(container: ServiceContainer = Depends(get_service_container)):
    """
    Dependency para PatternService
    """
    return container.get_service("pattern_service")


def get_ai_service(container: ServiceContainer = Depends(get_service_container)):
    """
    Dependency para AIService
    """
    return container.get_service("ai_service")


def get_industrial_factory(container: ServiceContainer = Depends(get_service_container)):
    """
    Dependency para IndustrialFactory
    """
    return container.get_service("industrial_factory")


async def close_database_pool():
    """
    Cerrar pool de conexiones
    """
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("🔄 Database pool closed")