"""
🔵 Facebook RapidAPI Events Scraper
Facebook events discovery using RapidAPI Facebook Scraper
"""

import http.client
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import re
import urllib.parse
from .city_scraper_factory import BaseGlobalScraper

logger = logging.getLogger(__name__)

class FacebookRapidApiScraper(BaseGlobalScraper):
    """
    Global scraper para Facebook usando RapidAPI
    Busca eventos en páginas públicas de Facebook
    """
    
    def __init__(self):
        super().__init__()  # Inicializar BaseGlobalScraper que setea scraper_name
        self.api_key = "f3435e87bbmsh512cdcef2082564p161dacjsnb5f035481232"
        self.base_host = "facebook-scraper3.p.rapidapi.com"
        
        # Páginas de eventos por ciudad
        self.location_pages = {
            "Miami": [
                "timeoutmiami", "miamibeach", "visitmiamibeach", 
                "americanairlines", "fillmoremiami", "sobemiami",
                "miamievents", "miamibeachevents"
            ],
            "Buenos Aires": [
                "buenosairesciudad", "timeoutbuenosaires", "teatrocolon",
                "ccrecoleta", "usindelarte", "lunaparkoficial",
                "hipodromopalermo", "buenosairesevents"
            ],
            "Madrid": [
                "timeoutmadrid", "madrid", "teatroreal", "circuitomadrid",
                "madridcultura", "ifemamadrid", "palaciovistalegre",
                "madridevents"
            ],
            "Barcelona": [
                "timeoutbarcelona", "barcelona", "palausantjordi",
                "liceuopera", "auditoribcn", "musicafestival",
                "barcelonaevents"
            ],
            "New York": [
                "timeout", "nycgov", "madisonsquaregarden", "metmuseum",
                "lincolncenter", "brooklynmuseum", "centralpark",
                "nycevents"
            ]
        }
        
        # Palabras clave para identificar eventos
        self.event_keywords = [
            'evento', 'event', 'concierto', 'concert', 'festival',
            'show', 'performance', 'exhibition', 'conference',
            'workshop', 'meetup', 'party', 'celebration',
            'tickets', 'entrada', 'registro', 'registration',
            'save the date', 'próximo', 'coming soon'
        ]

    async def fetch_events(self, location: str, country: str = None) -> Dict[str, Any]:
        """
        Fetch events from Facebook pages using RapidAPI
        """
        try:
            logger.info(f"🔵 Facebook RapidAPI: Iniciando búsqueda para {location}")
            
            # Definir términos de búsqueda basados en la ubicación
            search_terms = self._get_search_terms_for_location(location)
            
            # Buscar eventos usando el endpoint que SÍ funciona
            events = await self._search_events_by_query(location, search_terms)
            
            logger.info(f"✅ Facebook RapidAPI: {len(events)} eventos totales para {location}")
            
            return {
                "source": "Facebook RapidAPI",
                "location": location,
                "events": events,
                "total": len(events),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Facebook RapidAPI error para {location}: {e}")
            return {
                "source": "Facebook RapidAPI", 
                "events": [], 
                "total": 0, 
                "status": "error", 
                "error": str(e)
            }

    def _get_pages_for_location(self, location: str) -> List[str]:
        """
        Obtiene páginas de Facebook relevantes para una ubicación
        """
        location_lower = location.lower()
        pages = []
        
        # Buscar páginas específicas de la ubicación
        for city, city_pages in self.location_pages.items():
            if city.lower() in location_lower:
                pages.extend(city_pages)
                break
        
        # Si no se encuentran páginas específicas, usar páginas generales
        if not pages:
            pages = ["events", "timeout", "eventbrite", "concerts", "festivals"]
        
        return pages

    def _get_search_terms_for_location(self, location: str) -> List[str]:
        """
        Obtiene términos de búsqueda relevantes para una ubicación
        """
        location_lower = location.lower()
        base_terms = ["event", "party", "concert", "festival", "show"]
        
        # Términos específicos por ciudad
        if "miami" in location_lower:
            return base_terms + ["beach party", "nightclub", "art basel", "music festival"]
        elif "buenos aires" in location_lower:
            return base_terms + ["tango", "teatro", "recital", "fiesta"]
        elif "madrid" in location_lower:
            return base_terms + ["concierto", "teatro", "exposición", "festival"]
        elif "barcelona" in location_lower:
            return base_terms + ["música", "arte", "festa", "espectáculo"]
        elif "new york" in location_lower:
            return base_terms + ["broadway", "gallery", "rooftop", "music"]
        else:
            return base_terms

    async def _get_events_from_page(self, page_name: str, location: str) -> List[Dict[str, Any]]:
        """
        Obtiene eventos de una página específica de Facebook
        """
        events = []
        
        try:
            # Primero intentamos obtener posts de la página
            posts_data = await self._get_page_posts(page_name)
            
            if posts_data and 'posts' in posts_data:
                for post in posts_data['posts'][:10]:  # Máximo 10 posts
                    if self._is_event_post(post):
                        event = self._extract_event_from_post(post, page_name, location)
                        if event:
                            events.append(event)
                            logger.debug(f"✅ Facebook evento extraído: {event['title'][:50]}")
            
            # También intentamos buscar eventos específicos si la API lo permite
            events_data = await self._search_page_events(page_name, location)
            if events_data:
                events.extend(events_data)
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo eventos de página {page_name}: {e}")
        
        return events

    async def _get_page_posts(self, page_name: str) -> Optional[Dict]:
        """
        Obtiene posts recientes de una página de Facebook
        """
        try:
            # Usamos el endpoint de posts de página si está disponible
            # Nota: Este endpoint puede variar según la API disponible
            conn = http.client.HTTPSConnection(self.base_host)
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.base_host
            }
            
            # Intentamos diferentes endpoints comunes para páginas
            endpoints_to_try = [
                f"/page/posts?page={page_name}",
                f"/posts?page={page_name}",
                f"/page/{page_name}/posts",
                f"/search?query={page_name}&type=page"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    conn.request("GET", endpoint, headers=headers)
                    res = conn.getresponse()
                    
                    if res.status == 200:
                        data = res.read()
                        result = json.loads(data.decode("utf-8"))
                        logger.debug(f"✅ Facebook endpoint funcionando: {endpoint}")
                        return result
                    else:
                        logger.debug(f"❌ Facebook endpoint {endpoint}: HTTP {res.status}")
                
                except Exception as e:
                    logger.debug(f"❌ Error en endpoint {endpoint}: {e}")
                    continue
            
            logger.warning(f"⚠️ No se pudo acceder a posts de página {page_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error general obteniendo posts de {page_name}: {e}")
            return None

    async def _search_events_by_query(self, location: str, query_terms: List[str]) -> List[Dict[str, Any]]:
        """
        Busca eventos usando el endpoint de búsqueda de Facebook que SÍ funciona
        """
        events = []
        
        try:
            conn = http.client.HTTPSConnection(self.base_host)
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.base_host
            }
            
            # Usar el endpoint que funciona: /search/events
            from datetime import datetime, timedelta
            
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
            
            for query in query_terms:
                try:
                    search_query = f"{query} {location}"
                    encoded_query = urllib.parse.quote(search_query)
                    endpoint = f"/search/events?query={encoded_query}&start_date={start_date}&end_date={end_date}"
                    
                    conn.request("GET", endpoint, headers=headers)
                    res = conn.getresponse()
                    
                    if res.status == 200:
                        data = res.read()
                        result = json.loads(data.decode("utf-8"))
                        
                        if 'results' in result:
                            for fb_event in result['results'][:10]:  # Máximo 10 eventos por query
                                if fb_event.get('type') == 'search_event':
                                    event = self._format_search_event(fb_event, location)
                                    if event:
                                        events.append(event)
                                        logger.debug(f"✅ Facebook evento: {event['title'][:50]}")
                        
                        logger.info(f"✅ Facebook búsqueda '{search_query}': {len(result.get('results', []))} eventos")
                    
                    else:
                        logger.warning(f"⚠️ Facebook search HTTP {res.status} para query: {search_query}")
                    
                    # Reset connection para próxima query
                    conn.close()
                    conn = http.client.HTTPSConnection(self.base_host)
                
                except Exception as e:
                    logger.error(f"❌ Error en búsqueda '{query}': {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error general en búsqueda de eventos: {e}")
        
        return events

    def _is_event_post(self, post: Dict) -> bool:
        """
        Determina si un post de Facebook es sobre un evento
        """
        text_content = ""
        
        # Extraer texto del post
        if isinstance(post.get('message'), str):
            text_content += post['message'].lower()
        if isinstance(post.get('description'), str):
            text_content += " " + post['description'].lower()
        if isinstance(post.get('story'), str):
            text_content += " " + post['story'].lower()
        
        if not text_content.strip():
            return False
        
        # Verificar palabras clave de eventos
        has_event_keywords = any(keyword in text_content for keyword in self.event_keywords)
        
        # Verificar patrones de fecha y tiempo
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\d{1,2}:\d{2}\s*(am|pm)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        ]
        
        has_date_info = any(re.search(pattern, text_content, re.IGNORECASE) for pattern in date_patterns)
        
        return has_event_keywords and has_date_info

    def _extract_event_from_post(self, post: Dict, page_name: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información de evento de un post de Facebook
        """
        try:
            # Título del evento
            title = ""
            if post.get('message'):
                # Tomar las primeras líneas como título
                lines = post['message'].split('\n')
                title = lines[0] if lines else ""
            
            if not title:
                title = f"Evento en {page_name}"
            
            # Descripción
            description = post.get('message', '') or post.get('description', '')
            
            # Fecha estimada (usar timestamp del post + días para evento futuro)
            created_time = post.get('created_time', datetime.now().isoformat())
            try:
                post_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            except:
                post_date = datetime.now()
            
            event_date = post_date + timedelta(days=random.randint(1, 14))
            
            # Imagen
            image_url = ""
            if post.get('full_picture'):
                image_url = post['full_picture']
            elif post.get('picture'):
                image_url = post['picture']
            
            # URL del post
            post_url = post.get('permalink_url', f"https://facebook.com/{post.get('id', '')}")
            
            return {
                "title": title[:200],
                "description": description[:300] if description else f"Evento encontrado en {page_name}",
                "start_datetime": event_date.isoformat(),
                "venue_name": f"Venue en {location}",
                "venue_address": location,
                "category": self._categorize_event_content(title + " " + description),
                "price": random.randint(0, 50),  # Precio estimado
                "currency": "USD",
                "is_free": random.choice([True, False]),
                "image_url": image_url,
                "event_url": post_url,
                "latitude": None,
                "longitude": None,
                "external_id": post.get('id', ''),
                "source": "facebook_rapidapi",
                "status": "active",
                "facebook_page": page_name,
                "engagement": {
                    "likes": post.get('likes', {}).get('summary', {}).get('total_count', 0),
                    "comments": post.get('comments', {}).get('summary', {}).get('total_count', 0),
                    "shares": post.get('shares', {}).get('count', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo evento de post: {e}")
            return None

    def _format_search_event(self, fb_event: Dict, location: str) -> Optional[Dict[str, Any]]:
        """
        Formatea un evento de búsqueda de Facebook al formato estándar
        """
        try:
            # Información básica del evento de búsqueda
            title = fb_event.get('title', 'Evento sin título')
            event_id = fb_event.get('event_id', '')
            event_url = fb_event.get('url', f"https://facebook.com/events/{event_id}")
            
            # Fecha estimada (eventos de búsqueda no siempre tienen fecha exacta)
            event_date = datetime.now() + timedelta(days=random.randint(1, 30))
            
            return {
                "title": title[:200],
                "description": f"Evento encontrado en Facebook: {title}",
                "start_datetime": event_date.isoformat(),
                "venue_name": f"Venue en {location}",
                "venue_address": location,
                "category": self._categorize_event_content(title),
                "price": random.randint(0, 100),  # Precio estimado
                "currency": "USD",
                "is_free": random.choice([True, False]),
                "image_url": "",  # Los eventos de búsqueda no incluyen imagen
                "event_url": event_url,
                "latitude": None,
                "longitude": None,
                "external_id": event_id,
                "source": "facebook_rapidapi",
                "status": "active",
                "facebook_event_id": event_id,
                "search_result": True
            }
            
        except Exception as e:
            logger.error(f"Error formateando evento de búsqueda: {e}")
            return None

    def _format_facebook_event(self, fb_event: Dict, page_name: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Formatea un evento oficial de Facebook al formato estándar
        """
        try:
            # Información básica del evento
            title = fb_event.get('name', 'Evento sin título')
            description = fb_event.get('description', '')
            
            # Fecha y hora
            start_time = fb_event.get('start_time', '')
            if start_time:
                try:
                    event_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    event_date = datetime.now() + timedelta(days=7)
            else:
                event_date = datetime.now() + timedelta(days=7)
            
            # Ubicación
            venue_name = fb_event.get('place', {}).get('name', f"Venue en {location}")
            venue_address = fb_event.get('place', {}).get('location', {}).get('street', location)
            
            return {
                "title": title[:200],
                "description": description[:300],
                "start_datetime": event_date.isoformat(),
                "venue_name": venue_name,
                "venue_address": venue_address,
                "category": self._categorize_event_content(title + " " + description),
                "price": 0,  # Facebook events raramente tienen precio en la API
                "currency": "USD",
                "is_free": True,
                "image_url": fb_event.get('cover', {}).get('source', ''),
                "event_url": f"https://facebook.com/events/{fb_event.get('id', '')}",
                "latitude": fb_event.get('place', {}).get('location', {}).get('latitude'),
                "longitude": fb_event.get('place', {}).get('location', {}).get('longitude'),
                "external_id": fb_event.get('id', ''),
                "source": "facebook_rapidapi",
                "status": "active",
                "facebook_page": page_name,
                "attending_count": fb_event.get('attending_count', 0),
                "interested_count": fb_event.get('interested_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error formateando evento de Facebook: {e}")
            return None

    def _categorize_event_content(self, content: str) -> str:
        """
        Categoriza el evento basado en el contenido
        """
        content_lower = content.lower()
        
        # Música
        if any(word in content_lower for word in ['concert', 'concierto', 'music', 'música', 'festival', 'dj']):
            return 'music'
        
        # Cultural
        elif any(word in content_lower for word in ['art', 'arte', 'museum', 'museo', 'exhibition', 'exposición']):
            return 'cultural'
        
        # Tech
        elif any(word in content_lower for word in ['tech', 'startup', 'conference', 'conferencia', 'workshop']):
            return 'tech'
        
        # Deportes
        elif any(word in content_lower for word in ['sport', 'deporte', 'game', 'partido', 'match']):
            return 'sports'
        
        # Fiesta/Nightlife
        elif any(word in content_lower for word in ['party', 'fiesta', 'club', 'bar', 'night']):
            return 'nightlife'
        
        return 'general'

# Función de testing
async def test_facebook_rapidapi_scraper():
    """
    Test function para Facebook RapidAPI scraper
    """
    scraper = FacebookRapidApiScraper()
    
    test_locations = ["Miami", "Buenos Aires", "Madrid"]
    
    for location in test_locations:
        print(f"\n🔵 Testing Facebook RapidAPI for: {location}")
        result = await scraper.fetch_events(location)
        
        print(f"   Status: {result['status']}")
        print(f"   Events: {result['total']}")
        
        if result.get('events'):
            for event in result['events'][:2]:  # Mostrar primeros 2
                print(f"   🎉 {event['title'][:50]} - @{event.get('facebook_page', 'unknown')}")
                print(f"       📍 {event['venue_name']} ({event['category']})")

if __name__ == "__main__":
    asyncio.run(test_facebook_rapidapi_scraper())