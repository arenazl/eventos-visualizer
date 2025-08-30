"""
🌎 Configuración de Países - Sistema Escalable por Etapas
Permite agregar países progresivamente con sus características específicas
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class CountryStatus(Enum):
    ACTIVE = "active"           # País completamente soportado
    BETA = "beta"              # En pruebas, funciones limitadas  
    PLANNED = "planned"        # Planificado para futuro
    MAINTENANCE = "maintenance" # Temporalmente fuera de servicio

class APISupport(Enum):
    FULL = "full"              # Todas las APIs funcionando
    PARTIAL = "partial"        # Algunas APIs disponibles
    SCRAPING_ONLY = "scraping" # Solo web scraping
    NONE = "none"              # Sin APIs externas

@dataclass
class CountryConfig:
    # Información básica
    country_code: str          # ISO 3166-1 alpha-2 (AR, CL, UY, etc.)
    country_name: str          # Nombre completo
    status: CountryStatus      # Estado actual del soporte
    
    # Configuración regional
    default_city: str          # Ciudad principal por defecto
    timezone: str              # Zona horaria principal
    currency: str              # Moneda local (ARS, CLP, USD, etc.)
    locale: str                # Locale (es-AR, es-CL, en-US, etc.)
    
    # Soporte de APIs externas
    api_support: APISupport
    supported_apis: List[str]  # ['eventbrite', 'ticketmaster', 'meetup', 'facebook']
    
    # Configuración específica
    major_cities: List[str]    # Ciudades principales para geolocalización
    event_sources: List[str]   # Fuentes de eventos específicas del país
    search_keywords: Dict[str, List[str]]  # Keywords localizadas por categoría
    
    # Características del mercado
    popular_categories: List[str]  # Categorías más populares en el país
    price_ranges: Dict[str, tuple] # Rangos típicos de precios por categoría
    peak_months: List[int]     # Meses con más eventos (1-12)

# 🇦🇷 ARGENTINA - PAÍS BASE (ACTIVO)
ARGENTINA = CountryConfig(
    country_code="AR",
    country_name="Argentina",
    status=CountryStatus.ACTIVE,
    
    default_city="Buenos Aires",
    timezone="America/Argentina/Buenos_Aires",
    currency="ARS",
    locale="es-AR",
    
    api_support=APISupport.FULL,
    supported_apis=["eventbrite", "ticketmaster", "meetup", "facebook", "instagram"],
    
    major_cities=[
        "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata",
        "Mar del Plata", "Tucumán", "Salta", "Bariloche"
    ],
    event_sources=[
        "ticketek_ar", "plateanet", "tuentrada", "facebook_scraper", "instagram_scraper"
    ],
    search_keywords={
        "music": ["música", "concierto", "recital", "show", "festival", "rock", "pop", "folklore"],
        "sports": ["fútbol", "deporte", "partido", "cancha", "estadio", "racing", "boca", "river"],
        "cultural": ["teatro", "arte", "cultura", "museo", "exposición", "cine", "opera"],
        "tech": ["tecnología", "hackathon", "startup", "conferencia", "meetup", "dev"],
        "party": ["fiesta", "boliche", "after", "electrónica", "rooftop", "bar"]
    },
    
    popular_categories=["music", "sports", "cultural", "party", "tech"],
    price_ranges={
        "free": (0, 0),
        "cheap": (1000, 5000),      # ARS
        "medium": (5000, 15000),    # ARS  
        "expensive": (15000, 50000) # ARS
    },
    peak_months=[3, 4, 5, 9, 10, 11, 12]  # Otoño, Primavera, Verano
)

# 🇨🇱 CHILE - BETA (EN DESARROLLO)
CHILE = CountryConfig(
    country_code="CL",
    country_name="Chile",
    status=CountryStatus.BETA,
    
    default_city="Santiago",
    timezone="America/Santiago", 
    currency="CLP",
    locale="es-CL",
    
    api_support=APISupport.PARTIAL,
    supported_apis=["eventbrite", "facebook"],
    
    major_cities=[
        "Santiago", "Valparaíso", "Concepción", "Antofagasta", "Viña del Mar"
    ],
    event_sources=[
        "puntoticket_cl", "facebook_scraper"
    ],
    search_keywords={
        "music": ["música", "concierto", "festival", "rock", "cumbia", "cueca"],
        "sports": ["fútbol", "deporte", "partido", "colo colo", "universidad"],
        "cultural": ["teatro", "arte", "cultura", "GAM", "centro cultural"],
        "tech": ["tecnología", "startup chile", "meetup", "conferencia"],
        "party": ["carrete", "fiesta", "after", "electrónica"]
    },
    
    popular_categories=["music", "sports", "cultural", "tech"],
    price_ranges={
        "free": (0, 0),
        "cheap": (5000, 15000),      # CLP
        "medium": (15000, 40000),    # CLP
        "expensive": (40000, 100000) # CLP
    },
    peak_months=[1, 2, 3, 11, 12]  # Verano
)

# 🇺🇾 URUGUAY - PLANIFICADO
URUGUAY = CountryConfig(
    country_code="UY", 
    country_name="Uruguay",
    status=CountryStatus.PLANNED,
    
    default_city="Montevideo",
    timezone="America/Montevideo",
    currency="UYU", 
    locale="es-UY",
    
    api_support=APISupport.SCRAPING_ONLY,
    supported_apis=["facebook"],
    
    major_cities=["Montevideo", "Punta del Este", "Maldonado", "Salto"],
    event_sources=["tickantel_uy", "facebook_scraper"],
    search_keywords={
        "music": ["música", "concierto", "candombe", "tango", "festival"],
        "sports": ["fútbol", "deporte", "partido", "peñarol", "nacional"],
        "cultural": ["teatro", "arte", "cultura", "sodre"],
        "tech": ["tecnología", "meetup", "conferencia"],
        "party": ["fiesta", "boliche", "after"]
    },
    
    popular_categories=["music", "sports", "cultural"],
    price_ranges={
        "free": (0, 0),
        "cheap": (200, 800),         # UYU
        "medium": (800, 2000),       # UYU
        "expensive": (2000, 5000)    # UYU
    },
    peak_months=[1, 2, 12]  # Verano
)

# 🇺🇸 ESTADOS UNIDOS - PLANIFICADO (MERCADO GRANDE)
USA = CountryConfig(
    country_code="US",
    country_name="United States", 
    status=CountryStatus.PLANNED,
    
    default_city="New York",
    timezone="America/New_York",
    currency="USD",
    locale="en-US",
    
    api_support=APISupport.FULL,
    supported_apis=["eventbrite", "ticketmaster", "meetup", "facebook"],
    
    major_cities=[
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "Miami"
    ],
    event_sources=[
        "ticketmaster_us", "stubhub", "eventbrite_us", "facebook_scraper"
    ],
    search_keywords={
        "music": ["music", "concert", "festival", "show", "rock", "pop", "jazz"],
        "sports": ["sports", "game", "match", "stadium", "NBA", "NFL", "MLB"],
        "cultural": ["theater", "art", "culture", "museum", "exhibition", "broadway"],
        "tech": ["technology", "hackathon", "startup", "conference", "meetup"],
        "party": ["party", "club", "nightlife", "bar", "rooftop"]
    },
    
    popular_categories=["music", "sports", "cultural", "tech", "party"],
    price_ranges={
        "free": (0, 0),
        "cheap": (10, 50),           # USD
        "medium": (50, 150),         # USD
        "expensive": (150, 500)      # USD
    },
    peak_months=[5, 6, 7, 8, 9, 10]  # Primavera/Verano
)

# 🗺️ REGISTRO GLOBAL DE PAÍSES
SUPPORTED_COUNTRIES: Dict[str, CountryConfig] = {
    "AR": ARGENTINA,
    "CL": CHILE, 
    "UY": URUGUAY,
    "US": USA
}

def get_country_config(country_code: str) -> Optional[CountryConfig]:
    """Obtener configuración de país por código"""
    return SUPPORTED_COUNTRIES.get(country_code.upper())

def get_active_countries() -> List[CountryConfig]:
    """Obtener solo países con soporte activo"""
    return [country for country in SUPPORTED_COUNTRIES.values() 
            if country.status == CountryStatus.ACTIVE]

def get_available_countries() -> List[CountryConfig]:
    """Obtener países disponibles (activos + beta)"""
    return [country for country in SUPPORTED_COUNTRIES.values() 
            if country.status in [CountryStatus.ACTIVE, CountryStatus.BETA]]

def is_country_supported(country_code: str) -> bool:
    """Verificar si un país está soportado"""
    config = get_country_config(country_code)
    return config is not None and config.status in [CountryStatus.ACTIVE, CountryStatus.BETA]

def get_country_keywords(country_code: str, category: str) -> List[str]:
    """Obtener keywords localizadas para búsqueda"""
    config = get_country_config(country_code)
    if not config:
        return []
    return config.search_keywords.get(category, [])

def get_fallback_country() -> CountryConfig:
    """País por defecto si no se detecta ubicación"""
    return ARGENTINA