"""
Servicio de Generación de Imágenes para Eventos
Genera imágenes automáticamente cuando los eventos no tienen imagen
Usa múltiples estrategias: Unsplash, Pexels, y generación con prompt
"""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
import hashlib
import random
from datetime import datetime
import logging
import os
from urllib.parse import quote

logger = logging.getLogger(__name__)

class EventImageGenerator:
    """
    Genera imágenes para eventos que no tienen imagen
    Usa múltiples fuentes y estrategias
    """
    
    def __init__(self):
        # APIs de imágenes gratuitas
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")
        
        # Fallback images por categoría
        self.fallback_images = {
            "music": [
                "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
                "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7",
                "https://images.unsplash.com/photo-1501386761578-eac5c94b800a",
                "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14",
                "https://images.unsplash.com/photo-1459749411175-04bf5292ceea"
            ],
            "theater": [
                "https://images.unsplash.com/photo-1503095396549-807759245b35",
                "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
                "https://images.unsplash.com/photo-1560707303-4e980ce876ad",
                "https://images.unsplash.com/photo-1507924538820-ede94a04019d"
            ],
            "sports": [
                "https://images.unsplash.com/photo-1471295253337-3ceaaedca402",
                "https://images.unsplash.com/photo-1461896836934-ffe607ba8211",
                "https://images.unsplash.com/photo-1518611012118-696072aa579a",
                "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e"
            ],
            "cultural": [
                "https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8",
                "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3",
                "https://images.unsplash.com/photo-1545128485-c400e7702796",
                "https://images.unsplash.com/photo-1514525253161-7a46d19cd819"
            ],
            "tech": [
                "https://images.unsplash.com/photo-1504384764586-bb4cdc1707b0",
                "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
                "https://images.unsplash.com/photo-1505373877841-8d25f7d46678",
                "https://images.unsplash.com/photo-1531297484001-80022131f5a1"
            ],
            "party": [
                "https://images.unsplash.com/photo-1530103862676-de8c9debad1d",
                "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf",
                "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7",
                "https://images.unsplash.com/photo-1574391884720-bbc3740c59d1"
            ],
            "conference": [
                "https://images.unsplash.com/photo-1505373877841-8d25f7d46678",
                "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
                "https://images.unsplash.com/photo-1591115765373-5207764f72e7",
                "https://images.unsplash.com/photo-1560439514-4e9645039924"
            ],
            "workshop": [
                "https://images.unsplash.com/photo-1552664730-d307ca884978",
                "https://images.unsplash.com/photo-1606761568499-6d2451b23c66",
                "https://images.unsplash.com/photo-1517048676732-d65bc937f952",
                "https://images.unsplash.com/photo-1531482615713-2afd69097998"
            ],
            "film": [
                "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba",
                "https://images.unsplash.com/photo-1478720568477-152d9b164e26",
                "https://images.unsplash.com/photo-1585647347483-22b66260dfff",
                "https://images.unsplash.com/photo-1536440136628-849c177e76a1"
            ],
            "art": [
                "https://images.unsplash.com/photo-1561214115-f2f134cc4912",
                "https://images.unsplash.com/photo-1547891654-e66ed7ebb968",
                "https://images.unsplash.com/photo-1578321272176-b7bbc0679853",
                "https://images.unsplash.com/photo-1544967082-d9d25d867d66"
            ],
            "food": [
                "https://images.unsplash.com/photo-1555244162-803834f70033",
                "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
                "https://images.unsplash.com/photo-1504674900247-0877df9cc836",
                "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe"
            ],
            "festival": [
                "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3",
                "https://images.unsplash.com/photo-1514525253161-7a46d19cd819",
                "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3",
                "https://images.unsplash.com/photo-1468234847176-28606331216a"
            ],
            "dance": [
                "https://images.unsplash.com/photo-1518834107812-67b0b7c58434",
                "https://images.unsplash.com/photo-1508700929628-666bc8bd84ea",
                "https://images.unsplash.com/photo-1535525153412-5a42439a210d",
                "https://images.unsplash.com/photo-1574482620811-1aa16ffe3c82"
            ],
            "museum": [
                "https://images.unsplash.com/photo-1554907984-15263bfd63bd",
                "https://images.unsplash.com/photo-1565035010268-a3816f98589a",
                "https://images.unsplash.com/photo-1513038630932-13873b1a7f29",
                "https://images.unsplash.com/photo-1572953109213-3be62398eb95"
            ],
            "outdoor": [
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
                "https://images.unsplash.com/photo-1533295252084-08f0fb27db96",
                "https://images.unsplash.com/photo-1519331379826-f10be5486c6f",
                "https://images.unsplash.com/photo-1523908511403-7fc7b25592f4"
            ],
            "default": [
                "https://images.unsplash.com/photo-1492684223066-81342ee5ff30",
                "https://images.unsplash.com/photo-1558618666-fcd25c85cd64",
                "https://images.unsplash.com/photo-1511795409834-ef04bbd61622",
                "https://images.unsplash.com/photo-1464047736614-af63643285bf"
            ]
        }
        
        # Cache de imágenes generadas
        self.image_cache = {}
    
    async def get_image_for_event(self, event_data: Dict[str, Any]) -> str:
        """
        Obtiene o genera una imagen para un evento
        Intenta múltiples estrategias en orden de preferencia
        """
        # Si ya tiene imagen, devolverla
        if event_data.get("image_url"):
            return event_data["image_url"]
        
        # Generar cache key
        cache_key = self._generate_cache_key(event_data)
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        # Estrategia 1: Buscar en Unsplash
        if self.unsplash_access_key:
            image_url = await self._search_unsplash(event_data)
            if image_url:
                self.image_cache[cache_key] = image_url
                return image_url
        
        # Estrategia 2: Buscar en Pexels
        if self.pexels_api_key:
            image_url = await self._search_pexels(event_data)
            if image_url:
                self.image_cache[cache_key] = image_url
                return image_url
        
        # Estrategia 3: Usar imagen por defecto basada en categoría
        image_url = self._get_fallback_image(event_data)
        self.image_cache[cache_key] = image_url
        return image_url
    
    async def _search_unsplash(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Busca una imagen relevante en Unsplash
        """
        try:
            # Construir query de búsqueda
            query = self._build_search_query(event_data)
            
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": query,
                "client_id": self.unsplash_access_key,
                "per_page": 10,
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["results"]:
                            # Seleccionar una imagen aleatoria de los primeros resultados
                            photo = random.choice(data["results"][:5])
                            return photo["urls"]["regular"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Unsplash: {e}")
            return None
    
    async def _search_pexels(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Busca una imagen relevante en Pexels
        """
        try:
            query = self._build_search_query(event_data)
            
            url = f"https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_api_key
            }
            params = {
                "query": query,
                "per_page": 10,
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["photos"]:
                            photo = random.choice(data["photos"][:5])
                            return photo["src"]["large"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Pexels: {e}")
            return None
    
    def _build_search_query(self, event_data: Dict[str, Any]) -> str:
        """
        Construye una query de búsqueda para imágenes
        """
        # Mapeo de categorías a términos de búsqueda
        category_terms = {
            "music": ["concert", "music", "stage", "festival"],
            "theater": ["theater", "stage", "performance", "drama"],
            "sports": ["sports", "stadium", "game", "match"],
            "cultural": ["culture", "art", "heritage", "tradition"],
            "tech": ["technology", "conference", "innovation", "digital"],
            "party": ["party", "celebration", "nightlife", "dancing"],
            "food": ["food", "restaurant", "cuisine", "dining"],
            "art": ["art", "gallery", "painting", "exhibition"],
            "dance": ["dance", "ballet", "performance", "dancing"],
            "film": ["cinema", "movie", "film", "theater"],
            "outdoor": ["outdoor", "nature", "park", "festival"],
            "museum": ["museum", "gallery", "art", "culture"],
            "workshop": ["workshop", "learning", "class", "education"],
            "conference": ["conference", "meeting", "business", "presentation"]
        }
        
        # Obtener términos basados en categoría
        category = event_data.get("category", "").lower()
        terms = category_terms.get(category, ["event"])
        
        # Agregar términos del título si es corto
        title = event_data.get("title", "")
        if len(title.split()) <= 3:
            terms.append(title)
        
        # Construir query
        query = " ".join(random.sample(terms, min(2, len(terms))))
        
        return query
    
    def _get_fallback_image(self, event_data: Dict[str, Any]) -> str:
        """
        Obtiene una imagen por defecto basada en la categoría
        """
        category = event_data.get("category", "default")
        if isinstance(category, dict):
            category = category.get('name', 'default')
        category = str(category).lower()
        
        # Buscar imágenes para la categoría
        if category in self.fallback_images:
            images = self.fallback_images[category]
        else:
            images = self.fallback_images["default"]
        
        # Seleccionar una imagen aleatoria pero determinística basada en el título
        # Esto asegura que el mismo evento siempre tenga la misma imagen
        title_hash = hashlib.md5(event_data.get("title", "").encode()).hexdigest()
        index = int(title_hash[:8], 16) % len(images)
        
        return images[index]
    
    def _generate_cache_key(self, event_data: Dict[str, Any]) -> str:
        """
        Genera una key única para cachear la imagen
        """
        parts = [
            event_data.get("title", ""),
            event_data.get("category", ""),
            event_data.get("venue_name", "")
        ]
        
        key_string = "_".join(parts).lower()
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def generate_placeholder_image(self, 
                                        event_data: Dict[str, Any], 
                                        width: int = 800, 
                                        height: int = 400) -> str:
        """
        Genera una imagen placeholder usando un servicio de placeholders
        """
        # Colores por categoría
        category_colors = {
            "music": "9333ea",  # Purple
            "theater": "dc2626",  # Red
            "sports": "16a34a",  # Green
            "tech": "2563eb",  # Blue
            "party": "ec4899",  # Pink
            "food": "f59e0b",  # Amber
            "art": "8b5cf6",  # Violet
            "cultural": "0891b2",  # Cyan
            "default": "6b7280"  # Gray
        }
        
        category = event_data.get("category", "default")
        if isinstance(category, dict):
            category = category.get('name', 'default')
        category = str(category).lower()
        color = category_colors.get(category, category_colors["default"])
        
        title = event_data.get("title", "Evento")[:30]
        venue = event_data.get("venue_name", "")[:20]
        
        # Usar placeholder.com o similar
        text = quote(f"{title}|{venue}")
        url = f"https://via.placeholder.com/{width}x{height}/{color}/FFFFFF?text={text}"
        
        return url
    
    async def batch_generate_images(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera imágenes para múltiples eventos en batch
        """
        tasks = []
        
        for event in events:
            if not event.get("image_url"):
                task = self.get_image_for_event(event)
                tasks.append(task)
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder task
        
        images = await asyncio.gather(*tasks)
        
        # Actualizar eventos con las imágenes generadas
        for event, image_url in zip(events, images):
            if not event.get("image_url"):
                event["image_url"] = image_url
                event["generated_image"] = True
        
        return events
    
    def get_image_with_cdn(self, image_url: str, width: Optional[int] = None, height: Optional[int] = None) -> str:
        """
        Devuelve la URL de la imagen optimizada a través de un CDN
        Para servicios que lo soporten (Unsplash, Pexels)
        """
        if not image_url:
            return ""
        
        # Unsplash soporta parámetros de tamaño
        if "unsplash.com" in image_url:
            params = []
            if width:
                params.append(f"w={width}")
            if height:
                params.append(f"h={height}")
            params.append("q=80")  # Calidad 80%
            params.append("fm=jpg")  # Formato JPG
            
            if params:
                separator = "&" if "?" in image_url else "?"
                return f"{image_url}{separator}{'&'.join(params)}"
        
        # Pexels ya incluye diferentes tamaños
        if "pexels.com" in image_url:
            # Reemplazar tamaño si es necesario
            if width and width <= 500:
                return image_url.replace("/large", "/medium")
            elif width and width <= 350:
                return image_url.replace("/large", "/small")
        
        return image_url


# Servicio singleton
image_generator = EventImageGenerator()


# Función de utilidad para usar en otros servicios
async def ensure_event_has_image(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asegura que un evento tenga imagen
    Si no tiene, genera una automáticamente
    """
    if not event.get("image_url"):
        event["image_url"] = await image_generator.get_image_for_event(event)
        event["generated_image"] = True
    
    return event


# Función de prueba
async def test_image_generation():
    """
    Prueba el generador de imágenes
    """
    test_events = [
        {
            "title": "Festival de Jazz",
            "category": "music",
            "venue_name": "Luna Park"
        },
        {
            "title": "Obra de Teatro",
            "category": "theater",
            "venue_name": "Teatro Colón"
        },
        {
            "title": "Partido de Fútbol",
            "category": "sports",
            "venue_name": "La Bombonera"
        },
        {
            "title": "Conferencia de Tecnología",
            "category": "tech",
            "venue_name": "Centro de Convenciones"
        }
    ]
    
    print("🖼️ Generando imágenes para eventos...")
    
    for event in test_events:
        image_url = await image_generator.get_image_for_event(event)
        print(f"\n📌 {event['title']}")
        print(f"   🏷️ Categoría: {event['category']}")
        print(f"   🖼️ Imagen: {image_url}")
    
    # Test batch generation
    print("\n🎯 Generando imágenes en batch...")
    events_with_images = await image_generator.batch_generate_images(test_events)
    
    for event in events_with_images:
        print(f"\n✅ {event['title']}: {event.get('image_url', 'No image')}")


if __name__ == "__main__":
    asyncio.run(test_image_generation())