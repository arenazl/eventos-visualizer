"""
Schemas de Pydantic para eventos
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class EventCategory(str, Enum):
    """
    Categorías de eventos disponibles
    """
    MUSICA = "música"
    DEPORTES = "deportes" 
    CULTURAL = "cultural"
    TECH = "tech"
    GASTRONOMIA = "gastronomía"
    ARTE = "arte"
    TEATRO = "teatro"
    CINE = "cine"
    FAMILIA = "familia"
    NEGOCIOS = "negocios"
    GENERAL = "general"


class EventSource(str, Enum):
    """
    Fuentes de eventos
    """
    EVENTBRITE = "eventbrite"
    FACEBOOK = "facebook"
    TICKETMASTER = "ticketmaster"
    MEETUP = "meetup"
    INSTAGRAM = "instagram"
    ARGENTINA_VENUES = "argentina_venues"
    SAMPLE = "sample"
    SMART_SEARCH = "smart_search"


class VenueSchema(BaseModel):
    """
    Schema para venue/lugar del evento
    """
    name: str = Field(..., description="Nombre del lugar")
    address: Optional[str] = Field(None, description="Dirección del lugar")
    city: Optional[str] = Field(None, description="Ciudad")
    country: Optional[str] = Field(None, description="País")
    latitude: Optional[float] = Field(None, description="Latitud", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Longitud", ge=-180, le=180)
    capacity: Optional[int] = Field(None, description="Capacidad del lugar", ge=0)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Teatro Colón",
                "address": "Cerrito 628",
                "city": "Buenos Aires",
                "country": "Argentina",
                "latitude": -34.6010,
                "longitude": -58.3831,
                "capacity": 2500
            }
        }


class PriceSchema(BaseModel):
    """
    Schema para precios de eventos
    """
    min_price: Optional[float] = Field(None, description="Precio mínimo", ge=0)
    max_price: Optional[float] = Field(None, description="Precio máximo", ge=0)
    currency: str = Field("ARS", description="Moneda del precio")
    is_free: bool = Field(False, description="Si el evento es gratuito")
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        if v is not None and values.get('min_price') is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "min_price": 50.0,
                "max_price": 100.0,
                "currency": "ARS",
                "is_free": False
            }
        }


class OrganizerSchema(BaseModel):
    """
    Schema para organizador del evento
    """
    name: str = Field(..., description="Nombre del organizador")
    email: Optional[str] = Field(None, description="Email de contacto")
    phone: Optional[str] = Field(None, description="Teléfono de contacto")
    website: Optional[HttpUrl] = Field(None, description="Sitio web del organizador")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Eventbrite Productions",
                "email": "info@eventbrite.com",
                "website": "https://eventbrite.com"
            }
        }


class EventSchema(BaseModel):
    """
    Schema principal para eventos
    """
    id: str = Field(..., description="ID único del evento")
    title: str = Field(..., description="Título del evento", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Descripción del evento", max_length=2000)
    
    # Fechas
    start_date: datetime = Field(..., description="Fecha y hora de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha y hora de fin")
    
    # Ubicación
    venue: Union[str, VenueSchema] = Field(..., description="Lugar del evento")
    
    # Categorización
    category: EventCategory = Field(EventCategory.GENERAL, description="Categoría del evento")
    subcategory: Optional[str] = Field(None, description="Subcategoría específica")
    tags: List[str] = Field(default=[], description="Tags del evento")
    
    # Precio
    price: Union[float, PriceSchema] = Field(0, description="Precio del evento")
    
    # Organizador
    organizer: Optional[OrganizerSchema] = Field(None, description="Organizador del evento")
    
    # Media
    image_url: Optional[HttpUrl] = Field(None, description="URL de imagen del evento")
    images: List[HttpUrl] = Field(default=[], description="URLs de imágenes adicionales")
    
    # Enlaces
    event_url: Optional[HttpUrl] = Field(None, description="URL externa del evento")
    booking_url: Optional[HttpUrl] = Field(None, description="URL para reservar/comprar")
    
    # Metadatos
    source: EventSource = Field(..., description="Fuente del evento")
    external_id: Optional[str] = Field(None, description="ID en la fuente externa")
    
    # Estadísticas
    attendees_count: Optional[int] = Field(None, description="Número de asistentes", ge=0)
    likes_count: Optional[int] = Field(None, description="Número de likes", ge=0)
    views_count: Optional[int] = Field(None, description="Número de visualizaciones", ge=0)
    
    # Relevancia (para búsquedas)
    relevance_score: Optional[float] = Field(None, description="Score de relevancia", ge=0, le=1)
    matched_keywords: List[str] = Field(default=[], description="Keywords que coincidieron en búsqueda")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de actualización")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date'):
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": "event_12345",
                "title": "Concierto de Rock Nacional",
                "description": "Gran concierto con las mejores bandas de rock del país",
                "start_date": "2025-09-15T20:00:00",
                "end_date": "2025-09-15T23:30:00",
                "venue": {
                    "name": "Estadio Luna Park",
                    "address": "Bouchard 465",
                    "city": "Buenos Aires",
                    "latitude": -34.6027,
                    "longitude": -58.3686
                },
                "category": "música",
                "subcategory": "rock",
                "tags": ["rock", "nacional", "música en vivo"],
                "price": {
                    "min_price": 75.0,
                    "max_price": 150.0,
                    "currency": "ARS",
                    "is_free": False
                },
                "organizer": {
                    "name": "Rock Productions",
                    "email": "info@rockproductions.com"
                },
                "image_url": "https://example.com/event-image.jpg",
                "event_url": "https://eventbrite.com/event/12345",
                "source": "eventbrite",
                "attendees_count": 1500
            }
        }


class EventListSchema(BaseModel):
    """
    Schema para lista de eventos
    """
    events: List[EventSchema] = Field(..., description="Lista de eventos")
    total: int = Field(..., description="Número total de eventos", ge=0)
    page: Optional[int] = Field(None, description="Página actual", ge=1)
    page_size: Optional[int] = Field(None, description="Tamaño de página", ge=1, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "events": [
                    {
                        "id": "event_1",
                        "title": "Festival de Música",
                        "start_date": "2025-09-15T20:00:00",
                        "venue": "Estadio Principal",
                        "category": "música",
                        "source": "eventbrite"
                    }
                ],
                "total": 25,
                "page": 1,
                "page_size": 20
            }
        }


class EventSearchParams(BaseModel):
    """
    Schema para parámetros de búsqueda de eventos
    """
    location: Optional[str] = Field(None, description="Ciudad o ubicación")
    category: Optional[EventCategory] = Field(None, description="Categoría de eventos")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    price_min: Optional[float] = Field(None, description="Precio mínimo", ge=0)
    price_max: Optional[float] = Field(None, description="Precio máximo", ge=0)
    is_free: Optional[bool] = Field(None, description="Solo eventos gratuitos")
    sources: Optional[List[EventSource]] = Field(None, description="Fuentes específicas")
    tags: Optional[List[str]] = Field(None, description="Tags a buscar")
    limit: int = Field(20, description="Límite de resultados", ge=1, le=100)
    offset: int = Field(0, description="Offset para paginación", ge=0)
    
    @validator('date_to')
    def validate_date_to(cls, v, values):
        if v and values.get('date_from'):
            if v <= values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v
    
    @validator('price_max')
    def validate_price_max(cls, v, values):
        if v is not None and values.get('price_min') is not None:
            if v < values['price_min']:
                raise ValueError('price_max must be greater than or equal to price_min')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "location": "Buenos Aires",
                "category": "música",
                "date_from": "2025-09-15T00:00:00",
                "date_to": "2025-09-30T23:59:59",
                "price_max": 100.0,
                "is_free": False,
                "sources": ["eventbrite", "ticketmaster"],
                "limit": 20
            }
        }