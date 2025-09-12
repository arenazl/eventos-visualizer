"""
Configuración específica para Heroku
Sobrescribe configuraciones locales para production
"""
import os
from typing import Dict, Any

def get_heroku_config() -> Dict[str, Any]:
    """Configuración optimizada para Heroku"""
    return {
        # Server config
        "HOST": "0.0.0.0",
        "PORT": int(os.environ.get("PORT", 8000)),
        
        # Database - Heroku PostgreSQL
        "DATABASE_URL": os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://"),
        
        # APIs
        "EVENTBRITE_API_KEY": os.environ.get("EVENTBRITE_API_KEY", ""),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GOOGLE_MAPS_API_KEY": os.environ.get("GOOGLE_MAPS_API_KEY", ""),
        
        # Production settings
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": "production",
        
        # CORS - Allow frontend domains
        "CORS_ORIGINS": [
            "https://eventos-visualizer-frontend.vercel.app",
            "https://eventos-visualizer.netlify.app",
            "https://your-frontend-domain.com"
        ],
        
        # Cache settings
        "REDIS_URL": os.environ.get("REDIS_URL", ""),
        
        # Rate limiting for production
        "RATE_LIMIT": "100/hour",
        
        # Heroku-specific
        "DYNO_TYPE": os.environ.get("DYNO", "web"),
        "HEROKU_APP_NAME": os.environ.get("HEROKU_APP_NAME", ""),
        "HEROKU_SLUG_COMMIT": os.environ.get("HEROKU_SLUG_COMMIT", ""),
    }

def is_heroku() -> bool:
    """Detecta si estamos ejecutando en Heroku"""
    return "DYNO" in os.environ

def apply_heroku_config():
    """Aplica configuración de Heroku al entorno"""
    if is_heroku():
        config = get_heroku_config()
        for key, value in config.items():
            if isinstance(value, (str, int, bool)):
                os.environ[key] = str(value)