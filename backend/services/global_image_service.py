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

    def get_event_image(self, title: str, category: Optional[str] = None, venue: Optional[str] = None, country: Optional[str] = None, description: Optional[str] = None) -> str:
        """
        🖼️ Obtiene una imagen apropiada y contextual para un evento
        
        Args:
            title: Título del evento
            category: Categoría del evento
            venue: Venue/lugar del evento
            country: País del evento
            description: Descripción del evento
            
        Returns:
            str: URL de imagen apropiada basada en contenido
        """
        try:
            # Crear cache key único incluyendo descripción
            cache_key = hashlib.md5(f"{title}_{category}_{venue}_{description}".encode()).hexdigest()
            
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Analizar contenido completo del evento
            full_content = f"{title} {description or ''} {venue or ''}".lower()
            
            # Determinar tema específico basado en análisis de contenido
            specific_theme = self._analyze_event_content(full_content, category)
            
            # Generar imagen contextual basada en tema específico
            contextual_image = self._generate_contextual_image(title, specific_theme, full_content)
            
            self.cache[cache_key] = contextual_image
            logger.info(f"🎯 Contextual image for '{title[:40]}...': theme={specific_theme}")
            return contextual_image
            
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
    
    def _analyze_event_content(self, content: str, category: Optional[str] = None) -> str:
        """
        🧠 Analiza el contenido del evento para determinar el tema más específico
        
        Args:
            content: Contenido completo del evento (título + descripción + venue)
            category: Categoría base del evento
            
        Returns:
            str: Tema específico determinado del análisis
        """
        # Definir indicadores específicos con sus temas correspondientes
        theme_indicators = {
            "wine": ["vino", "wine", "bodega", "winery", "malbec", "degustación", "vineyard", "maridaje", "cata"],
            "concert": ["concierto", "concert", "música", "music", "band", "festival", "rock", "jazz", "pop", "live"],
            "food": ["gastronom", "comida", "food", "restaurant", "cocina", "chef", "degustación", "culinar"],
            "sports": ["deporte", "sport", "fútbol", "football", "tennis", "basketball", "stadium", "match"],
            "cultural": ["cultural", "arte", "art", "museo", "museum", "exposición", "gallery", "teatro"],
            "business": ["business", "empresa", "conference", "networking", "workshop", "seminario", "corporate"],
            "outdoor": ["outdoor", "aire libre", "parque", "park", "hiking", "camping", "nature", "aventura"],
            "party": ["fiesta", "party", "celebración", "celebration", "baile", "dance", "nightlife"],
            "tech": ["tech", "technology", "startup", "digital", "innovation", "hackathon", "coding", "software"],
            "theater": ["teatro", "theater", "obra", "drama", "performance", "espectáculo", "musical"]
        }
        
        # Contar coincidencias para cada tema
        theme_scores = {}
        for theme, keywords in theme_indicators.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                theme_scores[theme] = score
        
        # Si hay coincidencias específicas, usar el tema con mayor score
        if theme_scores:
            best_theme = max(theme_scores, key=theme_scores.get)
            logger.debug(f"🧠 Content analysis: '{content[:50]}...' → theme: {best_theme}")
            return best_theme
        
        # Fallback a categoría normalizada o default
        normalized_cat = self.normalize_category(category) if category else 'default'
        logger.debug(f"🧠 No specific theme found, using category: {normalized_cat}")
        return normalized_cat
    
    def _generate_contextual_image(self, title: str, theme: str, content: str) -> str:
        """
        🎨 Genera una imagen contextual específica basada en el tema determinado
        
        Args:
            title: Título del evento
            theme: Tema específico determinado del análisis
            content: Contenido completo para hash único
            
        Returns:
            str: URL de imagen contextual
        """
        # Colección de IDs de fotos de Unsplash de alta calidad por tema específico
        theme_photo_collections = {
            "wine": [
                "1506485338023-6ce5f36692df",  # Wine tasting
                "1551218808-419d4f39d7e8",     # Vineyard landscape  
                "1504674900406-8394e5e3e9b4",  # Wine glasses
                "1560472354-b33ff0c44a43",     # Wine barrels
                "1574269909862-7e1d70841ce6"   # Wine bottles
            ],
            "concert": [
                "1514525253161-7a46d19cd819",  # Concert crowd
                "1493225457124-a3eb161ffa5f",  # Live performance
                "1506905925346-21bea4d5618d",  # Music stage
                "1518611012118-696072aa579a",  # Music festival
                "1571019613454-1cb2f99b2d8b"   # Guitar performance
            ],
            "food": [
                "1555939594-f7405c7ecaed",     # Gourmet plating
                "1504674900406-8394e5e3e9b4",  # Fine dining
                "1551218808-419d4f39d7e8",     # Food presentation
                "1565958011703-00e083a8b7e2",  # Restaurant atmosphere
                "1546833999-b9fcbecd74dd"      # Culinary art
            ],
            "sports": [
                "1551698618-1dfe5d97a563",     # Stadium view
                "1577212014992-8f598e5e9b30",  # Sports action
                "1461896836934-ffe607ba8211",  # Athletic event
                "1571019613454-1cb2f99b2d8b",  # Team sports
                "1606107688070-b7f7c9e8f9c5"   # Sports fans
            ],
            "cultural": [
                "1518998053901-5348d3961a04",  # Art gallery
                "1507003211169-0a1dd7228f2d",  # Museum interior
                "1578662996442-48f60103fc96",  # Cultural exhibition
                "1544947950-5b1c4b0d6b8d",     # Art installation
                "1518611012118-696072aa579a"   # Cultural event
            ],
            "business": [
                "1552664730-d307ca884978",     # Business meeting
                "1531482615713-2afd69097998",  # Conference room
                "1542626991-22e93d36c9d8",     # Professional networking
                "1517245386807-bb43f82c33c4",  # Corporate event
                "1523240795612-9a054b0db644"   # Business seminar
            ],
            "outdoor": [
                "1441974231531-c6227db76b6e",  # Outdoor activity
                "1506905925346-21bea4d5618d",  # Park gathering
                "1571019613454-1cb2f99b2d8b",  # Adventure sports
                "1544947950-5b1c4b0d6b8d",     # Nature event
                "1560472354-b33ff0c44a43"      # Outdoor festival
            ],
            "party": [
                "1530103862676-de2619d7c022",  # Party celebration
                "1492684223066-81342ee5ff30",  # Social gathering
                "1516450360452-9312f5e86fc7",  # Nightlife
                "1518611012118-696072aa579a",  # Dance event
                "1571019613454-1cb2f99b2d8b"   # Celebration
            ],
            "tech": [
                "1517077304055-6e89abbcd4df",  # Tech conference
                "1531482615713-2afd69097998",  # Innovation event
                "1542626991-22e93d36c9d8",     # Tech networking
                "1523240795612-9a054b0db644",  # Digital workshop
                "1517245386807-bb43f82c33c4"   # Startup event
            ],
            "theater": [
                "1507003211169-0a1dd7228f2d",  # Theater stage
                "1518998053901-5348d3961a04",  # Performance venue
                "1544947950-5b1c4b0d6b8d",     # Theater interior
                "1578662996442-48f60103fc96",  # Dramatic performance
                "1506905925346-21bea4d5618d"   # Live theater
            ],
            "default": [
                "1492684223066-81342ee5ff30",  # General event
                "1530103862676-de2619d7c022",  # Social gathering
                "1514525253161-7a46d19cd819",  # Community event
                "1518611012118-696072aa579a",  # Celebration
                "1506905925346-21bea4d5618d"   # Group activity
            ]
        }
        
        # Obtener colección de fotos para el tema
        photo_ids = theme_photo_collections.get(theme, theme_photo_collections["default"])
        
        # Seleccionar foto específica basada en hash del título para consistencia
        title_hash = abs(hash(title.lower())) % len(photo_ids)
        selected_photo_id = photo_ids[title_hash]
        
        # Generar URL con parámetros optimizados
        image_url = f"https://images.unsplash.com/photo-{selected_photo_id}?w=400&h=300&fit=crop&crop=center&q=80&fm=jpg&ixlib=rb-4.0.3&auto=format"
        
        logger.debug(f"🎨 Generated contextual image: {title[:30]} → {theme} → photo_{selected_photo_id}")
        return image_url

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
                        country=event.get('country', ''),
                        description=event.get('description', '')
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
def get_event_image(title: str, category: Optional[str] = None, venue: Optional[str] = None, country: Optional[str] = None, description: Optional[str] = None) -> str:
    """Función de conveniencia para obtener imagen de evento"""
    return global_image_service.get_event_image(title, category, venue, country, description)

def is_good_image(image_url: Optional[str]) -> bool:
    """Función de conveniencia para evaluar calidad de imagen"""
    return global_image_service.is_good_image(image_url)

async def improve_events_images(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Función de conveniencia para mejorar imágenes de eventos"""
    return await global_image_service.improve_event_images(events)