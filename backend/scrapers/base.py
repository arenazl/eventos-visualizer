"""
🎯 BASE SCRAPER INTERFACE
Interfaz que todos los scrapers deben implementar para garantizar consistencia
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class EventCategory(str, Enum):
    """Categorías estándar de eventos"""
    MUSIC = "music"
    SPORTS = "sports"
    ARTS = "arts"
    TECH = "tech"
    FOOD = "food"
    BUSINESS = "business"
    COMMUNITY = "community"
    FAMILY = "family"
    FILM = "film"
    HEALTH = "health"
    OTHER = "other"

class Event(BaseModel):
    """
    📅 MODELO ESTÁNDAR DE EVENTO
    Todos los scrapers deben normalizar sus datos a este formato
    """
    # Campos básicos (requeridos)
    title: str = Field(..., description="Título del evento")
    source: str = Field(..., description="Fuente del evento (eventbrite, meetup, etc)")
    
    # Campos opcionales pero importantes
    description: Optional[str] = Field(None, description="Descripción completa del evento")
    
    # Fecha y hora
    start_date: Optional[datetime] = Field(None, description="Fecha/hora de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha/hora de fin")
    date_display: Optional[str] = Field(None, description="Fecha formateada para mostrar")
    
    # Ubicación
    venue_name: Optional[str] = Field(None, description="Nombre del lugar")
    venue_address: Optional[str] = Field(None, description="Dirección completa")
    city: Optional[str] = Field(None, description="Ciudad")
    country: Optional[str] = Field(None, description="País")
    latitude: Optional[float] = Field(None, description="Latitud")
    longitude: Optional[float] = Field(None, description="Longitud")
    
    # Precio y tickets
    price: Optional[float] = Field(None, description="Precio del evento")
    price_display: Optional[str] = Field(None, description="Precio formateado (ej: '$50' o 'Gratis')")
    currency: str = Field("ARS", description="Moneda")
    is_free: bool = Field(False, description="Si el evento es gratuito")
    ticket_url: Optional[str] = Field(None, description="URL para comprar tickets")
    
    # Multimedia
    image_url: Optional[str] = Field(None, description="URL de imagen principal")
    thumbnail_url: Optional[str] = Field(None, description="URL de thumbnail")
    
    # Metadata
    source_url: Optional[str] = Field(None, description="URL original del evento")
    source_id: Optional[str] = Field(None, description="ID en el sistema origen")
    category: Optional[EventCategory] = Field(EventCategory.OTHER, description="Categoría del evento")
    tags: List[str] = Field(default_factory=list, description="Tags/etiquetas del evento")
    
    # Información adicional
    organizer_name: Optional[str] = Field(None, description="Nombre del organizador")
    organizer_url: Optional[str] = Field(None, description="URL del organizador")
    attendee_count: Optional[int] = Field(None, description="Número de asistentes confirmados")
    capacity: Optional[int] = Field(None, description="Capacidad máxima")
    
    # Control
    scraped_at: datetime = Field(default_factory=datetime.now, description="Cuándo se scrapeó")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ScraperStatus(str, Enum):
    """Estados posibles de un scraper"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NO_RESULTS = "no_results"
    RATE_LIMITED = "rate_limited"

class ScraperResult(BaseModel):
    """
    📊 RESULTADO DE UN SCRAPER
    Wrapper para el resultado de cada scraper
    """
    scraper: str = Field(..., description="Nombre del scraper")
    status: ScraperStatus = Field(..., description="Estado de la ejecución")
    events: List[Event] = Field(default_factory=list, description="Eventos encontrados")
    error: Optional[str] = Field(None, description="Mensaje de error si falló")
    execution_time: float = Field(0.0, description="Tiempo de ejecución en segundos")
    events_count: int = Field(0, description="Cantidad de eventos encontrados")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.events_count = len(self.events)

class IScraper(ABC):
    """
    🔧 INTERFAZ BASE PARA SCRAPERS
    Todos los scrapers deben heredar de esta clase e implementar sus métodos
    """
    
    # Configuración básica del scraper
    name: str = "base_scraper"
    timeout: int = 5  # Timeout en segundos
    enabled: bool = True
    priority: int = 10  # Prioridad de ejecución (menor = más prioritario)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Constructor base
        
        Args:
            api_key: API key si el scraper la necesita
        """
        self.api_key = api_key
    
    @abstractmethod
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        🎯 MÉTODO PRINCIPAL DE SCRAPING
        Debe ser implementado por cada scraper
        
        Args:
            location: Ubicación para buscar eventos
            limit: Cantidad máxima de eventos a retornar
            **kwargs: Parámetros adicionales específicos del scraper
            
        Returns:
            Dict con los datos crudos del scraper
        """
        pass
    
    @abstractmethod
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        🔄 NORMALIZACIÓN DE DATOS
        Convierte los datos crudos del scraper al formato Event estándar
        
        Args:
            raw_data: Datos crudos retornados por scrape()
            
        Returns:
            Lista de eventos normalizados
        """
        pass
    
    async def execute(self, location: str, limit: int = 10, **kwargs) -> ScraperResult:
        """
        ⚡ EJECUCIÓN COMPLETA
        Ejecuta el scraping y normalización, manejando errores
        
        Args:
            location: Ubicación para buscar eventos
            limit: Cantidad máxima de eventos
            
        Returns:
            ScraperResult con eventos normalizados o error
        """
        import time
        start_time = time.time()
        
        try:
            # Ejecutar scraping
            raw_data = await self.scrape(location, limit, **kwargs)
            
            # Normalizar datos
            events = self.normalize_output(raw_data)
            
            execution_time = time.time() - start_time
            
            return ScraperResult(
                scraper=self.name,
                status=ScraperStatus.SUCCESS if events else ScraperStatus.NO_RESULTS,
                events=events,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            return ScraperResult(
                scraper=self.name,
                status=ScraperStatus.TIMEOUT,
                error=f"Timeout después de {self.timeout} segundos",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ScraperResult(
                scraper=self.name,
                status=ScraperStatus.ERROR,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        🗓️ HELPER: Parser de fechas común
        """
        if not date_str:
            return None
            
        from dateutil import parser
        try:
            return parser.parse(date_str)
        except:
            return None
    
    def clean_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        💰 HELPER: Limpieza de precios
        """
        if not price_str:
            return None
            
        import re
        # Remover símbolos de moneda y espacios
        clean = re.sub(r'[^\d.,]', '', str(price_str))
        clean = clean.replace(',', '.')
        
        try:
            return float(clean)
        except:
            return None
    
    def detect_category(self, text: str) -> EventCategory:
        """
        🏷️ HELPER: Detección automática de categoría
        """
        text_lower = text.lower()
        
        # Keywords por categoría
        categories = {
            EventCategory.MUSIC: ['concert', 'concierto', 'music', 'música', 'band', 'banda', 'dj', 'festival'],
            EventCategory.SPORTS: ['sport', 'deporte', 'football', 'fútbol', 'basketball', 'tennis', 'match', 'partido'],
            EventCategory.ARTS: ['art', 'arte', 'exhibition', 'exposición', 'gallery', 'galería', 'museum', 'museo'],
            EventCategory.TECH: ['tech', 'technology', 'tecnología', 'programming', 'developer', 'startup', 'code'],
            EventCategory.FOOD: ['food', 'comida', 'restaurant', 'gastro', 'wine', 'vino', 'cooking', 'cocina'],
            EventCategory.BUSINESS: ['business', 'negocio', 'networking', 'conference', 'conferencia', 'workshop'],
            EventCategory.COMMUNITY: ['community', 'comunidad', 'meetup', 'social', 'volunteer', 'voluntario'],
            EventCategory.FAMILY: ['family', 'familia', 'kids', 'niños', 'children', 'parents'],
            EventCategory.FILM: ['film', 'movie', 'película', 'cinema', 'cine', 'screening'],
            EventCategory.HEALTH: ['health', 'salud', 'wellness', 'bienestar', 'yoga', 'meditation', 'fitness']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
                
        return EventCategory.OTHER

import asyncio