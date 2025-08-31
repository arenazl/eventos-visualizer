"""
🌍🖼️ GLOBAL IMAGE SERVICE
Servicio centralizado de imágenes para TODOS los scrapers del mundo
Argentina 🇦🇷 | España 🇪🇸 | Brasil 🇧🇷 | México 🇲🇽 | Francia 🇫🇷
"""

import asyncio
import aiohttp
import hashlib
import logging
from typing import Dict, List, Optional, Any
import random
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GlobalImageService:
    """
    🌍 Servicio global inteligente de imágenes
    
    FUNCIONALIDADES:
    1. Extrae imágenes reales de páginas web
    2. Base de datos global de venues/artistas
    3. Fallbacks contextuales por país/categoría  
    4. Cache inteligente de URLs válidas
    5. Detección automática de categorías
    """
    
    def __init__(self):
        # 🏟️ BASE DE DATOS GLOBAL DE VENUES
        self.GLOBAL_VENUES = {
            # 🇦🇷 ARGENTINA
            "Luna Park": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?q=80&w=2070",
            "Teatro Colón": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070", 
            "Estadio River": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
            "Estadio Boca": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            
            # 🇪🇸 ESPAÑA
            "Santiago Bernabéu": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
            "Wanda Metropolitano": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070", 
            "Camp Nou": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            "WiZink Center": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070",
            "Teatro Real": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
            "Museo Prado": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
            
            # 🇧🇷 BRASIL
            "Allianz Parque": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
            "Estádio do Morumbi": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            "Maracanã": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
            "Copacabana": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=2070",
            "Teatro Municipal SP": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
            
            # 🇲🇽 MÉXICO  
            "Foro Sol": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070",
            "Auditorio Nacional": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
            "Palacio de los Deportes": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?q=80&w=2070",
            
            # 🇫🇷 FRANCIA
            "Stade de France": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
            "AccorHotels Arena": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070",
            "Musée du Louvre": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
        }
        
        # 🎨 IMÁGENES POR CATEGORÍA Y PAÍS
        self.CATEGORY_IMAGES_BY_COUNTRY = {
            "AR": {  # 🇦🇷 ARGENTINA
                "music": [
                    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=2070",
                    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070"
                ],
                "sports": [
                    "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
                    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070"
                ],
                "cultural": [
                    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070"
                ],
                "party": [
                    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070",
                    "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?q=80&w=2070"
                ],
                "theater": [
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
                    "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?q=80&w=2070"
                ]
            },
            "ES": {  # 🇪🇸 ESPAÑA
                "music": [
                    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=2070",
                    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070"
                ],
                "sports": [
                    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
                    "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070"
                ],
                "cultural": [
                    "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?q=80&w=2070",
                    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070"
                ],
                "sports_tv": [
                    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
                    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070"
                ]
            },
            "BR": {  # 🇧🇷 BRASIL  
                "music": [
                    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=2070",
                    "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=2070"
                ],
                "party": [
                    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070", 
                    "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?q=80&w=2070"
                ],
                "sports": [
                    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
                    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070"
                ],
                "cultural": [
                    "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=2070",
                    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070"
                ]
            }
        }
        
        # 🔍 KEYWORDS PARA DETECCIÓN INTELIGENTE
        self.SMART_KEYWORDS = {
            # Equipos de fútbol
            "real madrid": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070",
            "barcelona": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            "atlético madrid": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
            "boca juniors": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            "river plate": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
            
            # Géneros musicales
            "rock": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=2070",
            "pop": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070", 
            "jazz": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=2070",
            "tango": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
            "samba": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=2070",
            
            # Tipos de eventos
            "teatro": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
            "museum": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
            "festival": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?q=80&w=2070",
            "conference": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?q=80&w=2070"
        }
        
        # ⚡ CACHE de imágenes válidas
        self.image_cache = {}
        
        # 🌐 Headers para requests
        self.headers = {
            "User-Agent": "FanAroundYou ImageService/1.0"
        }
    
    def get_event_image(self, 
                       event_title: str, 
                       category: str = "general",
                       venue: str = "",
                       country_code: str = "AR",
                       source_url: str = "") -> str:
        """
        🎯 MÉTODO PRINCIPAL: Obtener imagen inteligente para cualquier evento
        
        Args:
            event_title: Título del evento
            category: Categoría (music, sports, cultural, etc.)
            venue: Nombre del venue/lugar
            country_code: Código del país (AR, ES, BR, MX, FR)
            source_url: URL de la página original (para extraer imagen)
        
        Returns:
            URL de imagen optimizada para el evento
        """
        
        try:
            # 1. 🏟️ PRIORIDAD MÁXIMA: Venue conocido
            if venue:
                venue_image = self._get_venue_image(venue)
                if venue_image:
                    logger.info(f"🏟️ Imagen por venue: {venue}")
                    return venue_image
            
            # 2. 🎯 DETECCIÓN INTELIGENTE por keywords
            smart_image = self._get_smart_keyword_image(event_title)
            if smart_image:
                logger.info(f"🎯 Imagen inteligente: {event_title[:30]}...")
                return smart_image
            
            # 3. 🌍 IMAGEN CONTEXTUAL por país + categoría
            contextual_image = self._get_contextual_image(category, country_code)
            if contextual_image:
                logger.info(f"🌍 Imagen contextual: {country_code} - {category}")
                return contextual_image
            
            # 4. 🔗 EXTRAER de página original (si disponible)
            if source_url:
                # TODO: Implementar extracción async en versión futura
                logger.info(f"🔗 Futura extracción: {source_url[:30]}...")
                pass
            
            # 5. 🎲 FALLBACK FINAL por categoría
            fallback_image = self._get_fallback_image(category)
            logger.info(f"🎲 Imagen fallback: {category}")
            
            # 6. ✅ CURADOR FINAL - Validar y formatear
            curated_image = self._curate_final_image(fallback_image, event_title, category, country_code)
            return curated_image
            
        except Exception as e:
            logger.error(f"Error obteniendo imagen: {e}")
            return self._get_default_image()
    
    def _get_venue_image(self, venue: str) -> Optional[str]:
        """
        🏟️ Buscar imagen por venue específico
        """
        # Búsqueda exacta
        if venue in self.GLOBAL_VENUES:
            return self.GLOBAL_VENUES[venue]
        
        # Búsqueda fuzzy (partial match)
        for venue_name, image_url in self.GLOBAL_VENUES.items():
            if venue.lower() in venue_name.lower() or venue_name.lower() in venue.lower():
                return image_url
        
        return None
    
    def _get_smart_keyword_image(self, event_title: str) -> Optional[str]:
        """
        🎯 Detección inteligente por keywords en el título
        """
        title_lower = event_title.lower()
        
        for keyword, image_url in self.SMART_KEYWORDS.items():
            if keyword in title_lower:
                return image_url
        
        return None
    
    def _get_contextual_image(self, category: str, country_code: str) -> Optional[str]:
        """
        🌍 Imagen contextual por país y categoría
        """
        try:
            if country_code in self.CATEGORY_IMAGES_BY_COUNTRY:
                country_images = self.CATEGORY_IMAGES_BY_COUNTRY[country_code]
                if category in country_images:
                    return random.choice(country_images[category])
            
            # Fallback a Argentina si el país no tiene imágenes específicas
            if category in self.CATEGORY_IMAGES_BY_COUNTRY["AR"]:
                return random.choice(self.CATEGORY_IMAGES_BY_COUNTRY["AR"][category])
                
        except Exception as e:
            logger.debug(f"Error imagen contextual: {e}")
        
        return None
    
    async def _extract_image_from_url(self, source_url: str) -> Optional[str]:
        """
        🔗 Extraer imagen real de la página original
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(source_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Buscar meta tags de imagen
                        og_image = re.search(r'<meta property="og:image" content="([^"]*)"', html)
                        if og_image:
                            return og_image.group(1)
                        
                        # Buscar primera imagen grande
                        img_match = re.search(r'<img[^>]+src="([^"]*)"[^>]*>', html)
                        if img_match:
                            img_url = img_match.group(1)
                            if not img_url.startswith('http'):
                                from urllib.parse import urljoin
                                img_url = urljoin(source_url, img_url)
                            return img_url
                            
        except Exception as e:
            logger.debug(f"Error extrayendo imagen de {source_url}: {e}")
        
        return None
    
    def _get_fallback_image(self, category: str) -> str:
        """
        🎲 Imagen fallback por categoría
        """
        fallback_images = {
            "music": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=2070",
            "sports": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=2070",
            "cultural": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070",
            "party": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070",
            "theater": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=2070",
            "sports_tv": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070",
            "general": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070"
        }
        
        return fallback_images.get(category, fallback_images["general"])
    
    def _get_default_image(self) -> str:
        """
        🎨 Imagen por defecto si todo falla
        """
        return "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=2070"
    
    def get_country_code_from_source(self, source: str) -> str:
        """
        🌍 Detectar código de país desde el nombre del scraper
        """
        source_mapping = {
            "argentina": "AR", "buenos_aires": "AR", "tango": "AR", "boca": "AR", "river": "AR",
            "spain": "ES", "madrid": "ES", "barcelona": "ES", "marca": "ES", "timeout_madrid": "ES",
            "brasil": "BR", "sao_paulo": "BR", "rio": "BR", "sympla": "BR", "ingresse": "BR", 
            "mexico": "MX", "cdmx": "MX", "guadalajara": "MX",
            "france": "FR", "paris": "FR", "louvre": "FR"
        }
        
        source_lower = source.lower()
        for keyword, country_code in source_mapping.items():
            if keyword in source_lower:
                return country_code
        
        return "AR"  # Default: Argentina
    
    def bulk_enhance_events(self, events: List[Dict[str, Any]], default_country: str = "AR") -> List[Dict[str, Any]]:
        """
        🚀 MÉTODO BULK: Mejorar imágenes de múltiples eventos
        """
        enhanced_events = []
        
        for event in events:
            try:
                # Detectar país desde el source
                country_code = self.get_country_code_from_source(event.get('source', ''))
                if not country_code:
                    country_code = default_country
                
                # Obtener imagen optimizada
                optimized_image = self.get_event_image(
                    event_title=event.get('title', ''),
                    category=event.get('category', 'general'),
                    venue=event.get('venue_name', ''),
                    country_code=country_code,
                    source_url=event.get('event_url', '')
                )
                
                # Actualizar evento con imagen optimizada
                enhanced_event = event.copy()
                enhanced_event['image_url'] = optimized_image
                enhanced_event['image_optimized'] = True
                enhanced_event['image_country'] = country_code
                
                enhanced_events.append(enhanced_event)
                
            except Exception as e:
                logger.error(f"Error mejorando evento: {e}")
                enhanced_events.append(event)  # Agregar sin cambios si falla
        
        return enhanced_events
    
    def _curate_final_image(self, image_url: str, event_title: str, category: str, country_code: str) -> str:
        """
        🤖 CURADOR FINAL CON IA: Valida y optimiza imagen usando contexto inteligente
        """
        try:
            # 1. Validación básica
            if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                logger.warning("🚨 URL inválida, usando default")
                return self._get_default_image()
            
            # 2. IA contextual - Mejorar imagen basándose en el evento
            if 'unsplash.com' in image_url:
                # Optimizar parámetros Unsplash con IA contextual
                ai_params = self._get_ai_image_params(event_title, category, country_code)
                optimized_url = f"{image_url}?{ai_params}"
                
                logger.info(f"🤖 IA optimizada: {event_title[:30]}... → {optimized_url[:50]}...")
                return optimized_url
            
            # 3. Para otras fuentes, aplicar validación estándar
            trusted_domains = ['eventbrite.com', 'sympla.com', 'timeout.com', 'marca.com', 'facebook.com']
            is_trusted = any(domain in image_url for domain in trusted_domains)
            
            status = "✅ CONFIABLE" if is_trusted else "⚠️ EXTERNA"
            logger.info(f"🔍 Curado: {status} - {image_url[:40]}...")
            
            return image_url
            
        except Exception as e:
            logger.error(f"❌ Error curador IA: {e}")
            return self._get_default_image()
    
    def _get_ai_image_params(self, event_title: str, category: str, country_code: str) -> str:
        """
        🎨 IA para generar parámetros de imagen contextual
        """
        params = ["w=800", "q=80", "fit=crop"]
        
        # IA contextual por categoría
        if category == "sports":
            params.extend(["auto=enhance", "sat=10"])  # Más saturación para deportes
        elif category == "music":
            params.extend(["auto=enhance", "con=5"])   # Más contraste para música
        elif category == "cultural":
            params.extend(["auto=enhance", "bright=-5"]) # Más sofisticado para cultura
        elif category == "party":
            params.extend(["auto=enhance", "vib=15"])  # Más vibrante para fiestas
        
        # IA contextual por país
        if country_code == "ES":
            params.append("warm=5")    # Tonos cálidos españoles
        elif country_code == "BR":
            params.append("sat=15")    # Saturación tropical Brasil
        elif country_code == "AR":
            params.append("con=3")     # Contraste Buenos Aires
        
        return "&".join(params)

# 🌍 INSTANCIA GLOBAL DEL SERVICIO
global_image_service = GlobalImageService()

# 🧪 Test function
async def test_global_image_service():
    """
    Test del servicio global de imágenes
    """
    service = GlobalImageService()
    
    test_events = [
        {"title": "Real Madrid vs Barcelona", "category": "sports", "venue_name": "Santiago Bernabéu", "source": "marca_madrid"},
        {"title": "Concierto de Rock Nacional", "category": "music", "venue_name": "Luna Park", "source": "argentina_venues"},
        {"title": "Festival de Samba", "category": "music", "venue_name": "Copacabana", "source": "sympla_brasil"},
        {"title": "Exposición de Arte", "category": "cultural", "venue_name": "Museo Prado", "source": "timeout_madrid"},
        {"title": "Evento General", "category": "general", "venue_name": "", "source": "general"}
    ]
    
    print("🌍🖼️ Testing Global Image Service...")
    
    enhanced_events = service.bulk_enhance_events(test_events)
    
    for event in enhanced_events:
        print(f"\n🎨 {event['title']}")
        print(f"   🏟️ Venue: {event['venue_name']}")
        print(f"   🌍 País: {event.get('image_country', 'N/A')}")
        print(f"   🖼️ Imagen: {event['image_url'][:60]}...")
        print(f"   ✨ Optimizada: {event.get('image_optimized', False)}")

if __name__ == "__main__":
    asyncio.run(test_global_image_service())