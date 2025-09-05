"""
📘 Facebook Events API Scraper con Caché Mensual
Sistema inteligente que minimiza llamadas a API paga
"""

import asyncio
import aiohttp
import json
import os
import http.client
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from urllib.parse import quote
from services.scraper_interface import BaseGlobalScraper

logger = logging.getLogger(__name__)

class Facebook_ApiScraper(BaseGlobalScraper):
    """
    Facebook API Scraper con sistema de caché mensual
    - Solo hace requests a la API si no existe caché para esa ciudad/mes
    - Guarda resultados en archivos JSON por mes
    - Minimiza costos de API paga
    """
    
    # 🎯 HABILITADO POR DEFECTO - API PAGA DISPONIBLE
    enabled_by_default: bool = True
    nearby_cities: bool = False  # Facebook NO se usa para recommend - evitar costos
    priority: int = 1  # Fastest - API call ~800ms
    
    def __init__(self, url_discovery_service=None):
        """Inicializa con la interfaz base requerida"""
        super().__init__(url_discovery_service)
        
        # Configuración de caché
        self.cache_dir = Path("/mnt/c/Code/eventos-visualizer/backend/data/facebook_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # RapidAPI Facebook Scraper configuration
        self.api_key = os.getenv('RAPIDAPI_KEY', 'f3435e87bbmsh512cdcef2082564p161dacjsnb5f035481232')
        self.api_base_url = "https://facebook-scraper3.p.rapidapi.com"
        
        # Headers para RapidAPI
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': "facebook-scraper3.p.rapidapi.com",
            'User-Agent': 'Mozilla/5.0 (compatible; EventosScraper/1.0)'
        }
        
        logger.info("📘 Facebook API Scraper inicializado con caché de eventos")
    
    async def fetch_events(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Implementación del método requerido por BaseGlobalScraper
        Primero busca en caché, si no existe llama a la API
        """
        logger.info(f"📘 Facebook API: Buscando eventos en '{location}'")
        
        # Generar nombre de archivo de caché para el mes actual
        cache_filename = self._get_cache_filename(location)
        cache_file = self.cache_dir / cache_filename
        
        # Intentar cargar eventos desde caché
        cached_events = self._load_from_cache(cache_file, location)
        if cached_events is not None:
            logger.info(f"✅ Facebook: Usando caché de eventos para '{location}' (GRATIS)")
            return cached_events[:limit]
        
        # Si no hay caché, hacer request a la API de eventos
        logger.info(f"💰 Facebook: Llamando API de eventos para '{location}' (PAGO)")
        events = await self._fetch_from_api(location, category, limit)
        
        # Guardar en caché para futuros requests
        self._save_to_cache(cache_file, location, events)
        
        return events[:limit]
    
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Implementación del método requerido por BaseGlobalScraper
        """
        return await self.fetch_events(location, category, limit)
    
    def _get_cache_filename(self, location: str) -> str:
        """
        Genera el nombre del archivo de caché para cada ciudad específica
        Ejemplo: facebook_cache_month_09_year_2025_miami.json
        """
        now = datetime.now()
        month = now.strftime("%m")
        year = now.strftime("%Y")
        # Normalizar nombre de ciudad para el archivo
        city_name = location.lower().strip().replace(' ', '_').replace(',', '')
        return f"facebook_cache_month_{month}_year_{year}_{city_name}.json"
    
    def _load_from_cache(self, cache_file: Path, location: str) -> Optional[List[Dict]]:
        """
        Carga eventos desde el archivo JSON específico de la ciudad
        Cada ciudad tiene su propio archivo, no hay búsqueda dentro del JSON
        """
        if not cache_file.exists():
            logger.info(f"📁 No hay caché para '{location}': {cache_file.name}")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            events = cache_data.get('events', [])
            last_updated = cache_data.get('last_updated', '')
            request_count = cache_data.get('request_count', 0)
            
            logger.info(f"📊 Caché encontrado para '{location}':")
            logger.info(f"   - Archivo: {cache_file.name}")
            logger.info(f"   - Última actualización: {last_updated}")
            logger.info(f"   - Requests históricos: {request_count}")
            logger.info(f"   - Eventos en caché: {len(events)}")
            
            return events
                
        except Exception as e:
            logger.error(f"❌ Error leyendo caché: {e}")
            return None
    
    def _save_to_cache(self, cache_file: Path, location: str, events: List[Dict]):
        """
        Guarda eventos en un archivo JSON específico para esta ciudad
        Un archivo por ciudad = no hay búsquedas complejas
        """
        try:
            # Si existe el archivo, cargar para mantener el contador
            request_count = 1
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                        request_count = old_data.get('request_count', 0) + 1
                except:
                    pass
            
            # Estructura simple: todo en el nivel raíz del JSON
            cache_data = {
                'location': location,
                'events': events,
                'last_updated': datetime.now().isoformat(),
                'request_count': request_count,
                'month': datetime.now().strftime("%B %Y")
            }
            
            # Guardar archivo
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Caché guardado: {cache_file.name}")
            logger.info(f"📊 Ciudad: {location} | Eventos: {len(events)} | Requests totales: {request_count}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando caché: {e}")
    
    async def _fetch_from_api(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Hace el request real a la API de Facebook (PAGO)
        Este método solo se llama cuando no hay caché disponible
        """
        events = []
        
        try:
            # Si no tienes API key configurada, devolver vacío
            if not self.api_key:
                logger.warning("⚠️ Facebook API key no configurada, devolviendo array vacío")
                return []
            
            # RapidAPI Facebook Scraper para eventos usando http.client
            # Aumentar timeout a 10 segundos para evitar timeouts prematuros
            conn = http.client.HTTPSConnection("facebook-scraper3.p.rapidapi.com", timeout=10)
            
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': "facebook-scraper3.p.rapidapi.com"
            }
            
            # Configurar fechas (próximos 30 días)
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Construir query string para eventos - Solo query con ciudad
            # URL encode la ubicación para manejar espacios correctamente
            from urllib.parse import quote
            location_encoded = quote(location)
            query_string = f"query={location_encoded}&start_date={start_date}&end_date={end_date}"
            logger.info(f"🎯 Búsqueda de eventos para: {location}")
            
            # Si hay límite, agregarlo
            if limit and limit < 50:  # RapidAPI puede tener límites
                query_string += f"&limit={limit}"
            
            try:
                full_url = f"/search/events?{query_string}"
                logger.info(f"📘 Facebook Events API request: {full_url}")
                logger.info(f"📘 Query string: {query_string}")
                conn.request("GET", full_url, headers=headers)
                res = conn.getresponse()
                data = res.read()
                
                if res.status == 200:
                    response_text = data.decode("utf-8")
                    logger.info(f"📘 Facebook Events API response: {response_text[:200]}...")
                    
                    try:
                        data_json = json.loads(response_text)
                        events = self._parse_rapidapi_response(data_json, location)
                        logger.info(f"✅ RapidAPI Facebook: {len(events)} eventos obtenidos para '{location}'")
                        conn.close()
                    except json.JSONDecodeError:
                        logger.error(f"❌ Error parseando JSON de eventos: {response_text}")
                        # NO generar eventos de ejemplo - mejor devolver vacío
                        events = []
                        conn.close()
                else:
                    logger.error(f"❌ RapidAPI Facebook error: HTTP {res.status}")
                    response_text = data.decode("utf-8")
                    logger.error(f"❌ Response: {response_text}")
                    # NO generar eventos de ejemplo - mejor devolver vacío
                    events = []
                    conn.close()
            except Exception as conn_error:
                logger.error(f"❌ Connection error: {conn_error}")
                # NO generar eventos de ejemplo - mejor devolver vacío
                events = []
                try:
                    conn.close()
                except:
                    pass
        
        except Exception as e:
            logger.error(f"❌ Error llamando Facebook API: {e}")
            # NO generar eventos de ejemplo - mejor devolver vacío
            events = []
        
        return events
    
    def _parse_rapidapi_response(self, data: Dict, location: str) -> List[Dict[str, Any]]:
        """
        Parsea la respuesta de RapidAPI Facebook Scraper al formato estándar
        La API devuelve 'results' no 'events'
        """
        events = []
        
        # RapidAPI devuelve 'results' con estructura diferente
        events_data = data.get('results', []) if isinstance(data, dict) else []
        if not events_data and isinstance(data, list):
            events_data = data
        
        logger.info(f"📘 Parseando {len(events_data)} eventos de Facebook API")
        
        for fb_event in events_data:
            try:
                event = {
                    'title': fb_event.get('title', 'Evento sin título'),
                    'description': '',  # Esta API no devuelve descripción
                    'event_url': fb_event.get('url', ''),
                    'image_url': '',  # Esta API no devuelve imagen
                    'venue_name': location,  # Esta API no devuelve venue
                    'venue_address': '',
                    'start_datetime': None,  # Esta API no devuelve fecha
                    'end_datetime': None,
                    'price': None,
                    'is_free': True,
                    'source': 'facebook_rapidapi',
                    'category': 'eventos',
                    'external_id': fb_event.get('event_id', ''),
                    'attending_count': 0
                }
                events.append(event)
                
            except Exception as e:
                logger.warning(f"⚠️ Error parseando evento: {e}")
                continue
        
        return events
    
    def _parse_api_response(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parsea la respuesta de la API de Facebook al formato estándar
        """
        events = []
        
        for fb_event in data.get('data', []):
            event = {
                'title': fb_event.get('name', 'Evento sin título'),
                'description': fb_event.get('description', ''),
                'event_url': f"https://www.facebook.com/events/{fb_event.get('id', '')}",
                'image_url': fb_event.get('cover', {}).get('source', ''),
                'venue_name': fb_event.get('place', {}).get('name', location),
                'venue_address': fb_event.get('place', {}).get('location', {}).get('street', ''),
                'start_datetime': fb_event.get('start_time'),
                'end_datetime': fb_event.get('end_time'),
                'price': None,
                'is_free': True,
                'source': 'facebook_api',
                'category': 'eventos',
                'external_id': fb_event.get('id')
            }
            events.append(event)
        
        return events
    
    def _generate_sample_events(self, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        Genera eventos de ejemplo cuando no hay API key o falla el request
        """
        events = []
        categories = ['música', 'teatro', 'deportes', 'cultural', 'social']
        
        for i in range(min(limit, 5)):
            event = {
                'title': f'Evento {i+1} en {location}',
                'description': f'Evento de ejemplo en {location}',
                'event_url': f'https://facebook.com/events/example{i}',
                'image_url': f'https://picsum.photos/400/300?random={i}',
                'venue_name': f'Venue {location}',
                'venue_address': f'Dirección en {location}',
                'start_datetime': (datetime.now() + timedelta(days=i+1)).isoformat(),
                'end_datetime': None,
                'price': None,
                'is_free': True,
                'source': 'facebook_api_cache',
                'category': categories[i % len(categories)],
                'external_id': f'fb_sample_{i}'
            }
            events.append(event)
        
        return events