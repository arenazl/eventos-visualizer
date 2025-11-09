"""
Configuración centralizada de la aplicación
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings
    """
    # App Config
    APP_NAME: str = "Eventos Visualizer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    RELOAD: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5174",
        "http://172.29.228.80:5174",
        "http://localhost:5173",
        "http://172.29.228.80:5173",
        "https://eventos-visualizer.netlify.app",
        "https://eventos-visualizer.vercel.app"
    ]
    
    # Database
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0
    
    # PostgreSQL específico
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "eventos_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    
    # API Keys
    EVENTBRITE_API_KEY: Optional[str] = None
    EVENTBRITE_PRIVATE_TOKEN: Optional[str] = None
    TICKETMASTER_API_KEY: Optional[str] = None
    MEETUP_API_KEY: Optional[str] = None
    RAPIDAPI_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour default
    
    # Timeout
    REQUEST_TIMEOUT: int = 8  # seconds
    SCRAPER_TIMEOUT: int = 5  # seconds
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS: int = 100
    
    # Scrapers Config
    SCRAPERS_ENABLED: List[str] = [
        "eventbrite",
        "facebook",
        "ticketmaster",
        "meetup"
    ]
    SCRAPERS_PARALLEL: bool = True
    SCRAPERS_MAX_WORKERS: int = 5
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = 'ignore'  # Ignorar campos del .env que no están en el modelo
    
    def get_database_url(self) -> str:
        """
        Construir URL de base de datos
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Construir URL desde componentes
        if self.POSTGRES_PASSWORD:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            return f"postgresql://{self.POSTGRES_USER}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def is_production(self) -> bool:
        """
        Verificar si estamos en producción
        """
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """
        Verificar si estamos en desarrollo
        """
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Obtener instancia de configuración (cached)
    """
    return Settings()


# Instancia global de settings
settings = get_settings()