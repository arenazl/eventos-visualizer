"""
Modelo Universal de Eventos
Interfaz única para todos los eventos sin importar la fuente
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class EventCategory(str, Enum):
    """Categorías universales de eventos"""
    MUSIC = "music"
    THEATER = "theater"
    SPORTS = "sports"
    CULTURAL = "cultural"
    TECH = "tech"
    PARTY = "party"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    FILM = "film"
    ART = "art"
    FOOD = "food"
    FESTIVAL = "festival"
    DANCE = "dance"
    MUSEUM = "museum"
    LITERATURE = "literature"
    EDUCATION = "education"
    FAMILY = "family"
    OUTDOOR = "outdoor"
    OTHER = "other"

class EventSource(str, Enum):
    """Fuentes de eventos"""
    # APIs
    EVENTBRITE = "eventbrite"
    TICKETMASTER = "ticketmaster"
    BUENOS_AIRES_DATA = "buenos_aires_data"
    MEETUP = "meetup"
    SYMPLA = "sympla"
    BANDSINTOWN = "bandsintown"
    SEATGEEK = "seatgeek"
    ALLEVENTS = "allevents"
    
    # Scraping Argentina
    TICKETEK_AR = "ticketek_ar"
    PLATEANET = "plateanet"
    ALTERNATIVA_TEATRAL = "alternativa_teatral"
    TEATRO_COLON = "teatro_colon"
    LUNA_PARK = "luna_park"
    NICETO_CLUB = "niceto_club"
    LA_TRASTIENDA = "la_trastienda"
    
    # Scraping México
    TICKETMASTER_MX = "ticketmaster_mx"
    BOLETIA = "boletia"
    SUPERBOLETOS = "superboletos"
    
    # Scraping Colombia
    TUBOLETA = "tuboleta"
    PRIMERA_FILA = "primera_fila"
    
    # Scraping Chile
    PUNTOTICKET = "puntoticket"
    TICKETEK_CL = "ticketek_cl"
    
    # Scraping Brasil
    SYMPLA_SCRAPING = "sympla_scraping"
    INGRESSO_COM = "ingresso_com"
    
    # Social Media
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    
    # Other
    MANUAL = "manual"
    OTHER = "other"

class PriceRange(BaseModel):
    """Rango de precios del evento"""
    min_price: float = Field(0, ge=0, description="Precio mínimo")
    max_price: float = Field(0, ge=0, description="Precio máximo")
    currency: str = Field("ARS", description="Código de moneda ISO")
    is_free: bool = Field(False, description="Si el evento es gratuito")

class Location(BaseModel):
    """Ubicación del evento"""
    venue_name: str = Field(..., description="Nombre del lugar")
    venue_address: Optional[str] = Field(None, description="Dirección completa")
    city: Optional[str] = Field(None, description="Ciudad")
    state: Optional[str] = Field(None, description="Estado/Provincia")
    country: str = Field("Argentina", description="País")
    neighborhood: Optional[str] = Field(None, description="Barrio/Zona")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    postal_code: Optional[str] = Field(None)
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v, values):
        """Valida que si hay una coordenada, debe haber ambas"""
        if v is not None:
            if 'latitude' in values and values['latitude'] is None:
                raise ValueError("Si hay longitud, debe haber latitud")
        return v

class EventTiming(BaseModel):
    """Información temporal del evento"""
    start_datetime: datetime = Field(..., description="Fecha y hora de inicio")
    end_datetime: Optional[datetime] = Field(None, description="Fecha y hora de fin")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Duración en minutos")
    is_recurring: bool = Field(False, description="Si el evento es recurrente")
    recurrence_pattern: Optional[str] = Field(None, description="Patrón de recurrencia")
    timezone: str = Field("America/Argentina/Buenos_Aires", description="Zona horaria")
    
    @validator('end_datetime')
    def validate_end_after_start(cls, v, values):
        """Valida que la fecha de fin sea posterior al inicio"""
        if v and 'start_datetime' in values and v < values['start_datetime']:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return v

class EventMedia(BaseModel):
    """Medios asociados al evento"""
    image_url: Optional[str] = Field(None, description="URL de imagen principal")
    thumbnail_url: Optional[str] = Field(None, description="URL de miniatura")
    gallery_urls: List[str] = Field(default_factory=list, description="URLs de galería")
    video_url: Optional[str] = Field(None, description="URL de video")
    generated_image: bool = Field(False, description="Si la imagen fue generada por AI")
    image_prompt: Optional[str] = Field(None, description="Prompt usado para generar imagen")

class EventOrganizer(BaseModel):
    """Información del organizador"""
    name: Optional[str] = Field(None, description="Nombre del organizador")
    contact_email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    social_media: Dict[str, str] = Field(default_factory=dict)

class EventTicketing(BaseModel):
    """Información de tickets/entradas"""
    ticket_url: Optional[str] = Field(None, description="URL para comprar tickets")
    available_tickets: Optional[int] = Field(None, ge=0)
    total_capacity: Optional[int] = Field(None, ge=0)
    sales_start_date: Optional[datetime] = Field(None)
    sales_end_date: Optional[datetime] = Field(None)
    is_sold_out: bool = Field(False)
    requires_registration: bool = Field(False)

class EventMetadata(BaseModel):
    """Metadata del evento"""
    source: EventSource = Field(..., description="Fuente del evento")
    source_id: str = Field(..., description="ID único en la fuente original")
    source_url: Optional[str] = Field(None, description="URL en la fuente original")
    scraped_at: Optional[datetime] = Field(None, description="Fecha de scraping")
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(1.0, ge=0, le=1, description="Confianza en los datos")
    is_verified: bool = Field(False, description="Si el evento fue verificado")
    deduplication_hash: Optional[str] = Field(None, description="Hash para deduplicación")

class UniversalEvent(BaseModel):
    """
    Modelo universal para todos los eventos
    Combina información de todas las fuentes posibles
    """
    
    # Identificación
    id: str = Field(..., description="ID único universal")
    
    # Información básica
    title: str = Field(..., min_length=1, max_length=500, description="Título del evento")
    description: Optional[str] = Field(None, max_length=5000, description="Descripción completa")
    short_description: Optional[str] = Field(None, max_length=500, description="Descripción corta")
    
    # Categorización
    category: EventCategory = Field(..., description="Categoría principal")
    subcategory: Optional[str] = Field(None, description="Subcategoría")
    tags: List[str] = Field(default_factory=list, description="Etiquetas")
    keywords: List[str] = Field(default_factory=list, description="Palabras clave para búsqueda")
    
    # Timing
    timing: EventTiming = Field(..., description="Información temporal")
    
    # Ubicación
    location: Location = Field(..., description="Información de ubicación")
    
    # Precio
    pricing: PriceRange = Field(..., description="Información de precio")
    
    # Media
    media: EventMedia = Field(default_factory=EventMedia, description="Medios del evento")
    
    # Organizador
    organizer: EventOrganizer = Field(default_factory=EventOrganizer, description="Información del organizador")
    
    # Ticketing
    ticketing: EventTicketing = Field(default_factory=EventTicketing, description="Información de tickets")
    
    # Metadata
    metadata: EventMetadata = Field(..., description="Metadata del evento")
    
    # Información adicional específica
    age_restriction: Optional[str] = Field(None, description="Restricción de edad")
    dress_code: Optional[str] = Field(None, description="Código de vestimenta")
    accessibility: Optional[str] = Field(None, description="Información de accesibilidad")
    parking_info: Optional[str] = Field(None, description="Información de estacionamiento")
    public_transport: Optional[str] = Field(None, description="Información de transporte público")
    
    # Para eventos especiales (deportes, música, etc)
    performers: List[str] = Field(default_factory=list, description="Artistas/Performers")
    lineup: Optional[str] = Field(None, description="Lineup completo")
    home_team: Optional[str] = Field(None, description="Equipo local (deportes)")
    away_team: Optional[str] = Field(None, description="Equipo visitante (deportes)")
    
    # Engagement
    attendance_count: Optional[int] = Field(None, ge=0, description="Cantidad de asistentes")
    interested_count: Optional[int] = Field(None, ge=0, description="Cantidad de interesados")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Calificación")
    
    # Flags
    is_featured: bool = Field(False, description="Si es evento destacado")
    is_cancelled: bool = Field(False, description="Si está cancelado")
    is_postponed: bool = Field(False, description="Si está pospuesto")
    is_online: bool = Field(False, description="Si es evento online")
    is_hybrid: bool = Field(False, description="Si es evento híbrido")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "evt_123456",
                "title": "Festival de Jazz en el Parque",
                "description": "Un festival de jazz al aire libre con artistas locales",
                "category": "music",
                "subcategory": "jazz",
                "tags": ["jazz", "música en vivo", "aire libre", "gratis"],
                "timing": {
                    "start_datetime": "2024-02-15T19:00:00",
                    "end_datetime": "2024-02-15T23:00:00",
                    "timezone": "America/Argentina/Buenos_Aires"
                },
                "location": {
                    "venue_name": "Parque Centenario",
                    "venue_address": "Av. Díaz Vélez 4950",
                    "city": "Buenos Aires",
                    "country": "Argentina",
                    "neighborhood": "Caballito",
                    "latitude": -34.6064,
                    "longitude": -58.4357
                },
                "pricing": {
                    "min_price": 0,
                    "max_price": 0,
                    "currency": "ARS",
                    "is_free": True
                },
                "media": {
                    "image_url": "https://example.com/jazz-festival.jpg",
                    "generated_image": False
                },
                "metadata": {
                    "source": "buenos_aires_data",
                    "source_id": "ba_jazz_2024",
                    "last_updated": "2024-01-15T10:00:00",
                    "confidence_score": 0.95
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return self.dict(exclude_none=True)
    
    def to_json(self) -> str:
        """Convierte el evento a JSON"""
        return self.json(exclude_none=True, ensure_ascii=False)
    
    def generate_search_text(self) -> str:
        """Genera texto para búsqueda full-text"""
        parts = [
            self.title,
            self.description or "",
            self.location.venue_name,
            self.location.neighborhood or "",
            self.location.city or "",
            self.category,
            self.subcategory or "",
            " ".join(self.tags),
            " ".join(self.keywords),
            " ".join(self.performers),
        ]
        return " ".join(filter(None, parts)).lower()
    
    def calculate_relevance_score(self, user_preferences: Dict) -> float:
        """
        Calcula un score de relevancia basado en preferencias del usuario
        """
        score = 0.5  # Base score
        
        # Boost por categoría preferida
        if self.category in user_preferences.get("preferred_categories", []):
            score += 0.2
        
        # Boost por precio gratis
        if self.pricing.is_free and user_preferences.get("prefers_free", False):
            score += 0.15
        
        # Boost por cercanía
        if self.location.neighborhood in user_preferences.get("preferred_neighborhoods", []):
            score += 0.15
        
        # Penalización por evento cancelado o pospuesto
        if self.is_cancelled or self.is_postponed:
            score *= 0.3
        
        return min(1.0, score)
    
    def needs_image_generation(self) -> bool:
        """Determina si necesita generar una imagen"""
        return not self.media.image_url or self.media.image_url == ""
    
    def get_image_generation_prompt(self) -> str:
        """
        Genera un prompt para crear una imagen con AI
        """
        category_visuals = {
            EventCategory.MUSIC: "concert stage with lights and crowd",
            EventCategory.THEATER: "theater stage with red curtains",
            EventCategory.SPORTS: "sports stadium with field",
            EventCategory.ART: "art gallery with paintings",
            EventCategory.FOOD: "gourmet dishes on elegant table",
            EventCategory.TECH: "modern conference with screens and technology",
            EventCategory.PARTY: "vibrant party with colorful lights",
            EventCategory.CULTURAL: "cultural celebration with traditional elements",
            EventCategory.DANCE: "dancers on stage with dramatic lighting",
            EventCategory.FILM: "cinema screen with audience",
            EventCategory.OUTDOOR: "outdoor event in park with nature"
        }
        
        base_visual = category_visuals.get(self.category, "event venue with people")
        
        prompt = f"Professional event poster for {self.title}, {base_visual}, "
        prompt += f"located at {self.location.venue_name}, "
        
        if self.location.neighborhood:
            prompt += f"in {self.location.neighborhood} neighborhood, "
        
        prompt += f"vibrant colors, high quality, photorealistic, promotional poster style"
        
        return prompt


# Función helper para convertir desde diferentes formatos
def create_universal_event(source_data: Dict, source: EventSource) -> UniversalEvent:
    """
    Factory function para crear un UniversalEvent desde datos de cualquier fuente
    """
    # Mapeo básico común a todas las fuentes
    base_mapping = {
        "id": f"{source.value}_{source_data.get('id', hash(str(source_data)))}",
        "title": source_data.get("title") or source_data.get("name") or "Sin título",
        "description": source_data.get("description") or source_data.get("summary") or "",
    }
    
    # Crear timing
    timing = EventTiming(
        start_datetime=source_data.get("start_datetime") or datetime.now(),
        end_datetime=source_data.get("end_datetime"),
        timezone=source_data.get("timezone", "America/Argentina/Buenos_Aires")
    )
    
    # Crear location
    location = Location(
        venue_name=source_data.get("venue_name") or source_data.get("venue", {}).get("name") or "Lugar por confirmar",
        venue_address=source_data.get("venue_address") or source_data.get("venue", {}).get("address"),
        city=source_data.get("city", "Buenos Aires"),
        country=source_data.get("country", "Argentina"),
        neighborhood=source_data.get("neighborhood"),
        latitude=source_data.get("latitude"),
        longitude=source_data.get("longitude")
    )
    
    # Crear pricing
    pricing = PriceRange(
        min_price=source_data.get("price", 0) or source_data.get("min_price", 0),
        max_price=source_data.get("price", 0) or source_data.get("max_price", 0),
        currency=source_data.get("currency", "ARS"),
        is_free=source_data.get("is_free", False) or source_data.get("price", 1) == 0
    )
    
    # Crear media
    media = EventMedia(
        image_url=source_data.get("image_url") or source_data.get("logo", {}).get("url"),
        generated_image=False
    )
    
    # Crear metadata
    metadata = EventMetadata(
        source=source,
        source_id=str(source_data.get("id", hash(str(source_data)))),
        source_url=source_data.get("url") or source_data.get("event_url"),
        scraped_at=source_data.get("scraped_at"),
        last_updated=datetime.now()
    )
    
    # Determinar categoría
    category = EventCategory.OTHER
    category_str = source_data.get("category", "").lower()
    for cat in EventCategory:
        if cat.value in category_str:
            category = cat
            break
    
    # Crear el evento universal
    return UniversalEvent(
        **base_mapping,
        category=category,
        subcategory=source_data.get("subcategory"),
        tags=source_data.get("tags", []),
        keywords=source_data.get("keywords", []),
        timing=timing,
        location=location,
        pricing=pricing,
        media=media,
        metadata=metadata,
        organizer=EventOrganizer(
            name=source_data.get("organizer", {}).get("name")
        ),
        ticketing=EventTicketing(
            ticket_url=source_data.get("ticket_url")
        )
    )