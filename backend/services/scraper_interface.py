"""
🔌 SCRAPER INTERFACES - Contratos para Scrapers
Interfaces y clases base para mantener consistencia en todos los scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ScraperRequest:
    """📝 Estructura de request para scrapers"""
    location: str
    category: Optional[str] = None
    limit: int = 30
    
@dataclass  
class ScraperResult:
    """📊 Estructura de respuesta de scrapers"""
    events: List[Dict[str, Any]]
    scraper_name: str
    execution_time: float
    status: str  # 'success', 'partial', 'failed'
    error_message: Optional[str] = None

@dataclass
class ScraperConfig:
    """⚙️ Configuración para scrapers"""
    timeout: int = 10
    retry_attempts: int = 3
    use_cache: bool = True
    cache_ttl: int = 1800  # 30 minutos

class BaseGlobalScraper(ABC):
    """
    🌍 CLASE BASE PARA SCRAPERS GLOBALES
    
    Define el contrato que deben cumplir todos los scrapers globales.
    Estos scrapers funcionan en cualquier ubicación del mundo.
    """
    
    # 🎯 PROPERTY HABILITADO POR DEFECTO - CADA SCRAPER DEBE DEFINIR
    enabled_by_default: bool = True
    
    # 🌍 PROPERTY PARA BÚSQUEDA DE CIUDADES CERCANAS - CADA SCRAPER DEBE DEFINIR
    nearby_cities: bool = True
    
    def __init__(self, url_discovery_service, config: ScraperConfig = None):
        """
        Constructor con dependency injection
        
        Args:
            url_discovery_service: Servicio inyectado para descobrir URLs
            config: Configuración específica del scraper
        """
        self.url_discovery_service = url_discovery_service
        self.config = config or ScraperConfig()
        self.scraper_name = self.__class__.__name__.replace('Scraper', '').lower()
        self.context = {}  # Contexto para información adicional como detected_country
        
        # 🖼️ Inicializar servicio de imágenes
        self._image_service = None
    
    def set_context(self, context: Dict[str, Any]):
        """
        🔧 ESTABLECER CONTEXTO ADICIONAL
        
        Args:
            context: Diccionario con información adicional como detected_country
        """
        self.context.update(context)
    
    def _get_image_service(self):
        """
        🖼️ Lazy loading del servicio de imágenes
        
        Returns:
            GlobalImageService: Instancia del servicio de imágenes
        """
        if self._image_service is None:
            try:
                from services.global_image_service import global_image_service
                self._image_service = global_image_service
            except ImportError:
                self._image_service = None
        return self._image_service
    
    def _improve_event_image(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        🖼️ Mejora imagen de un evento individual SOLO SI NO TIENE BUENA IMAGEN
        
        Args:
            event: Evento a mejorar
            
        Returns:
            Dict[str, Any]: Evento con imagen mejorada si es necesario
        """
        try:
            image_service = self._get_image_service()
            if not image_service:
                return event
            
            current_image = event.get('image_url', '')
            
            # Solo mejorar si no tiene buena imagen
            if not image_service.is_good_image(current_image):
                better_image = image_service.get_event_image(
                    title=event.get('title', ''),
                    category=event.get('category', ''),
                    venue=event.get('venue_name', ''),
                    country=self.context.get('detected_country', '')
                )
                
                event['image_url'] = better_image
                event['image_improved'] = True
                # Log solo para debugging del scraper específico
                # logger.debug(f"🖼️ {self.scraper_name}: Imagen mejorada para '{event.get('title', '')[:30]}...'")
            else:
                event['image_improved'] = False
                
        except Exception:
            # Fallar silenciosamente para no romper el scraping
            event['image_improved'] = False
            
        return event
    
    @abstractmethod
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL DE SCRAPING
        
        Args:
            location: Ubicación de búsqueda (ciudad, país, etc.)
            category: Categoría opcional de eventos
            limit: Número máximo de eventos a retornar
            
        Returns:
            Lista de eventos en formato estándar
        """
        pass
    
    def _standardize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        📋 ESTANDARIZACIÓN DE EVENTOS
        
        Convierte evento raw del scraper al formato estándar de la aplicación
        🖼️ Mejora automáticamente imágenes si no tienen buena calidad
        """
        # Crear evento estandarizado
        standardized_event = {
            'title': raw_event.get('title', 'Sin título'),
            'description': raw_event.get('description', 'Sin descripción'),
            'event_url': raw_event.get('event_url', ''),
            'image_url': raw_event.get('image_url', ''),
            'venue_name': raw_event.get('venue_name', 'Ubicación no especificada'),
            'venue_address': raw_event.get('venue_address'),
            'start_datetime': raw_event.get('start_datetime'),
            'end_datetime': raw_event.get('end_datetime'),
            'price': raw_event.get('price'),
            'is_free': raw_event.get('is_free', False),
            'source': f"{self.scraper_name}_scraper",
            'category': raw_event.get('category', 'Eventos'),
            'external_id': raw_event.get('external_id')
        }
        
        # 🖼️ Mejorar imagen automáticamente si es necesario
        standardized_event = self._improve_event_image(standardized_event)
        
        return standardized_event

class BaseRegionalScraper(ABC):
    """
    🏛️ CLASE BASE PARA SCRAPERS REGIONALES
    
    Para scrapers específicos de países o regiones
    """
    
    def __init__(self, url_discovery_service, config: ScraperConfig = None):
        self.url_discovery_service = url_discovery_service
        self.config = config or ScraperConfig()
        self.scraper_name = self.__class__.__name__.replace('Scraper', '').lower()
    
    @abstractmethod
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        pass

class BaseLocalScraper(ABC):
    """
    🏙️ CLASE BASE PARA SCRAPERS LOCALES
    
    Para scrapers específicos de ciudades
    """
    
    def __init__(self, url_discovery_service, config: ScraperConfig = None):
        self.url_discovery_service = url_discovery_service
        self.config = config or ScraperConfig()
        self.scraper_name = self.__class__.__name__.replace('Scraper', '').lower()
    
    @abstractmethod
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        pass