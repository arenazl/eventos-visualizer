from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./eventos_visualizer.db"
    
    # External API Keys
    eventbrite_api_key: Optional[str] = None
    ticketmaster_api_key: Optional[str] = None
    meetup_client_id: Optional[str] = None
    meetup_client_secret: Optional[str] = None
    
    # Google APIs
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_calendar_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Application Settings
    environment: str = "development"
    debug: bool = True
    
    # Network Configuration (WSL)
    wsl_host_ip: str = "172.29.228.80"
    backend_port: int = 8001
    frontend_port: int = 5174
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()