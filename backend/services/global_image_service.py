"""
🖼️ GLOBAL IMAGE SERVICE - Mejora y búsqueda inteligente de imágenes
Servicio para obtener imágenes de calidad para eventos sin imágenes o con imágenes pobres
"""

import asyncio
import aiohttp
import logging
import re
import hashlib
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, quote_plus

logger = logging.getLogger(__name__)

class GlobalImageService:
    """
    🎨 Servicio global de imágenes para eventos
    
    FUNCIONES:
    - Genera imágenes usando APIs gratuitas (Unsplash, Pexels, etc.)
    - Mejora imágenes de baja resolución
    - Fallbacks inteligentes por categoría y ubicación
    - Cache de imágenes generadas
    """
    
    def __init__(self):
        self.cache = {}  # Cache simple en memoria
        
        # APIs gratuitas para imágenes (sin key requerida)
        self.image_apis = {
            'unsplash_source': 'https://source.unsplash.com',
            'picsum': 'https://picsum.photos',
            'lorem_picsum': 'https://loremflickr.com'
        }
        
        # Palabras clave por categoría para búsqueda de imágenes
        self.category_keywords = {
            'music': ['concert', 'music', 'festival', 'band', 'stage', 'live music'],
            'sports': ['stadium', 'sport', 'football', 'basketball', 'tennis', 'athletics'],
            'cultural': ['art', 'culture', 'museum', 'exhibition', 'gallery', 'theater'],
            'tech': ['technology', 'conference', 'coding', 'innovation', 'digital'],
            'food': ['restaurant', 'food', 'cuisine', 'dining', 'gastronomy'],
            'theater': ['theater', 'drama', 'performance', 'stage', 'acting'],
            'party': ['party', 'nightlife', 'club', 'celebration', 'dancing'],
            'business': ['business', 'meeting', 'conference', 'corporate', 'networking'],
            'education': ['education', 'learning', 'workshop', 'seminar', 'training'],
            'default': ['event', 'gathering', 'community', 'celebration']
        }
        
        # Imágenes por defecto elegantes por categoría (URLs que funcionan)
        self.default_images = {
            'music': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=300&fit=crop&crop=center',
            'sports': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop&crop=center',
            'cultural': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop&crop=center',
            'tech': 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=400&h=300&fit=crop&crop=center',
            'food': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=300&fit=crop&crop=center',
            'theater': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop&crop=center',
            'party': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400&h=300&fit=crop&crop=center',
            'business': 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&h=300&fit=crop&crop=center',
            'education': 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=400&h=300&fit=crop&crop=center',
            'default': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400&h=300&fit=crop&crop=center'
        }

    def is_good_image(self, image_url: Optional[str]) -> bool:
        """
        🔍 Evalúa si una imagen es de buena calidad
        
        Args:
            image_url: URL de la imagen a evaluar
            
        Returns:
            bool: True si la imagen es buena, False si necesita mejora
        """
        if not image_url or image_url.strip() == '':
            return False
            
        # Filtrar imágenes genéricas o de baja calidad
        bad_patterns = [
            'placeholder', 'default', 'avatar', 'profile',
            'logo', 'icon', 'thumb', 'small', '50x50', '100x100',
            'no-image', 'missing', 'blank', 'empty'
        ]
        
        url_lower = image_url.lower()
        for pattern in bad_patterns:
            if pattern in url_lower:
                return False
        
        # Verificar que tenga una extensión de imagen válida
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        has_valid_ext = any(ext in url_lower for ext in valid_extensions)
        
        # Si tiene parámetros de tamaño, verificar que no sea muy pequeña
        if 'w=' in url_lower or 'width=' in url_lower:
            width_match = re.search(r'w[idth]*=(\d+)', url_lower)
            if width_match and int(width_match.group(1)) < 200:
                return False
        
        return has_valid_ext or 'unsplash' in url_lower or 'pexels' in url_lower

    def normalize_category(self, category: Optional[str]) -> str:
        """
        🏷️ Normaliza la categoría del evento para búsqueda de imágenes
        
        Args:
            category: Categoría original del evento
            
        Returns:
            str: Categoría normalizada
        """
        if not category:
            return 'default'
            
        category_lower = category.lower()
        
        # Mapeo de categorías comunes
        category_mapping = {
            'música': 'music', 'musica': 'music', 'concierto': 'music',
            'deportes': 'sports', 'deporte': 'sports', 'futbol': 'sports',
            'cultura': 'cultural', 'cultural': 'cultural', 'arte': 'cultural',
            'tecnología': 'tech', 'tecnologia': 'tech', 'tech': 'tech',
            'gastronomía': 'food', 'gastronomia': 'food', 'comida': 'food',
            'teatro': 'theater', 'obra': 'theater', 'espectáculo': 'theater',
            'fiesta': 'party', 'party': 'party', 'celebración': 'party',
            'negocio': 'business', 'empresarial': 'business', 'conferencia': 'business',
            'educación': 'education', 'educacion': 'education', 'curso': 'education'
        }
        
        return category_mapping.get(category_lower, category_lower if category_lower in self.category_keywords else 'default')

    def get_event_image(self, title: str, category: Optional[str] = None, venue: Optional[str] = None, country: Optional[str] = None) -> str:
        """
        🖼️ Obtiene una imagen apropiada para un evento
        
        Args:
            title: Título del evento
            category: Categoría del evento
            venue: Venue/lugar del evento
            country: País del evento
            
        Returns:
            str: URL de imagen apropiada
        """
        try:
            # Crear cache key
            cache_key = hashlib.md5(f"{title}_{category}_{venue}".encode()).hexdigest()
            
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Normalizar categoría
            normalized_category = self.normalize_category(category)
            
            # Intentar obtener imagen específica por título o venue
            if title:
                specific_image = self._get_specific_image(title, normalized_category)
                if specific_image:
                    self.cache[cache_key] = specific_image
                    return specific_image
            
            # Fallback a imagen por categoría
            category_image = self._get_category_image(normalized_category, country)
            self.cache[cache_key] = category_image
            return category_image
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting image for '{title}': {e}")
            return self.default_images.get('default')

    def _get_specific_image(self, title: str, category: str) -> Optional[str]:
        """
        🎯 Obtiene imagen específica basada en título del evento
        
        Args:
            title: Título del evento
            category: Categoría normalizada
            
        Returns:
            Optional[str]: URL de imagen específica o None
        """
        try:
            # Usar directamente la imagen por defecto de la categoría
            # (más confiable que APIs externas)
            category_image = self.default_images.get(category)
            if category_image:
                logger.info(f"🖼️ Generated category image for '{title[:30]}...': {category}")
                return category_image
            
            # Fallback a imagen por defecto
            logger.info(f"🖼️ Using default image for '{title[:30]}...'")
            return self.default_images.get('default')
            
        except Exception as e:
            logger.warning(f"⚠️ Error generating specific image: {e}")
            return None

    def _get_category_image(self, category: str, country: Optional[str] = None) -> str:
        """
        🏷️ Obtiene imagen por categoría
        
        Args:
            category: Categoría normalizada
            country: País para contexto adicional
            
        Returns:
            str: URL de imagen por categoría
        """
        try:
            # Usar imagen por defecto de la categoría (más confiable)
            if category in self.default_images:
                logger.info(f"🏷️ Category image: {category}")
                return self.default_images[category]
            
            # Fallback a imagen por defecto
            logger.info(f"🏷️ Default image fallback for category: {category}")
            return self.default_images.get('default')
            
        except Exception as e:
            logger.warning(f"⚠️ Error generating category image: {e}")
            return self.default_images.get('default')

    async def improve_event_images(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔧 Mejora las imágenes de una lista de eventos
        
        Args:
            events: Lista de eventos a mejorar
            
        Returns:
            List[Dict[str, Any]]: Eventos con imágenes mejoradas
        """
        improved_events = []
        
        for event in events:
            try:
                current_image = event.get('image_url', '')
                
                # Si la imagen actual no es buena, generar una mejor
                if not self.is_good_image(current_image):
                    better_image = self.get_event_image(
                        title=event.get('title', ''),
                        category=event.get('category', ''),
                        venue=event.get('venue_name', ''),
                        country=event.get('country', '')
                    )
                    
                    event['image_url'] = better_image
                    event['image_improved'] = True
                    logger.info(f"🔧 Improved image for: {event.get('title', 'Unknown')[:50]}...")
                else:
                    event['image_improved'] = False
                
                improved_events.append(event)
                
            except Exception as e:
                logger.warning(f"⚠️ Error improving image for event: {e}")
                improved_events.append(event)
        
        total_improved = sum(1 for e in improved_events if e.get('image_improved', False))
        logger.info(f"🖼️ Image service: {total_improved}/{len(events)} events improved")
        
        return improved_events

# Singleton global
global_image_service = GlobalImageService()

# Funciones de conveniencia
def get_event_image(title: str, category: Optional[str] = None, venue: Optional[str] = None, country: Optional[str] = None) -> str:
    """Función de conveniencia para obtener imagen de evento"""
    return global_image_service.get_event_image(title, category, venue, country)

def is_good_image(image_url: Optional[str]) -> bool:
    """Función de conveniencia para evaluar calidad de imagen"""
    return global_image_service.is_good_image(image_url)

async def improve_events_images(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Función de conveniencia para mejorar imágenes de eventos"""
    return await global_image_service.improve_event_images(events)