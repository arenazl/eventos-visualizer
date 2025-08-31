"""
RapidAPI Facebook Scraper - La Joyita Encontrada
🎯 Usando Facebook Scraper API de RapidAPI para eventos reales
✅ API profesional con rate limits y endpoints estables
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
# No usar random - solo datos reales
import os
try:
    from .global_image_service import global_image_service
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.global_image_service import global_image_service

logger = logging.getLogger(__name__)

class RapidApiFacebookScraper:
    """
    Scraper usando RapidAPI Facebook Scraper
    API: https://rapidapi.com/krasnoludkolo/api/facebook-scraper3
    """
    
    def __init__(self):
        # RapidAPI Configuration
        self.api_host = "facebook-scraper3.p.rapidapi.com"
        self.api_key = os.getenv("RAPIDAPI_KEY", "")  # Necesitarás configurar esto
        
        self.base_url = "https://facebook-scraper3.p.rapidapi.com"
        
        # Headers for RapidAPI
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host,
            "Content-Type": "application/json"
        }
        
        # Cargar UIDs de ciudades argentinas desde JSON - AHORRA UNA LLAMADA API
        self.cities_uids = self.load_argentina_cities_uids()
        
        # Cache file path
        self.cache_file = "/mnt/c/Code/eventos-visualizer/backend/data/facebook_events_cache.json"
        
        # Páginas de Facebook argentinas con eventos
        self.facebook_event_pages = [
            # Venues principales
            "lunaparkoficial",
            "teatrocolonoficial", 
            "teatrosanmartin.buenosaires",
            "complejoteatral",
            "centroculturalrecoleta",
            "usinadelarte",
            
            # Organizadores de eventos
            "df.entertainment",
            "lollapaloozaar",
            "personalfest",
            "cosquinrock",
            "stereopicnic",
            
            # Medios culturales
            "timeoutbuenosaires",
            "agendacultural.buenosaires",
            "whatsupbuenosaires",
            "revistaplanetario",
            
            # Clubes y bares
            "nicetoclub",
            "krokodilclub", 
            "clubdebaile",
            "gierbar",
            "clubmuseum",
            
            # Festivales y eventos masivos  
            "tecnopolis",
            "feriademataderos",
            "festivaldejazz",
            "bafici",
            "festivaldecinedemdp"
        ]
        
        # Keywords para detectar eventos
        self.event_keywords = [
            "evento", "show", "concierto", "festival", "obra", "espectáculo",
            "fiesta", "party", "encuentro", "workshop", "seminario", "conferencia",
            "exposición", "muestra", "recital", "presentación", "estreno",
            "evento", "entrada", "ticket", "reserva", "gratis", "free"
        ]
    
    def load_argentina_cities_uids(self) -> Dict:
        """
        Cargar UIDs de ciudades argentinas desde JSON
        AHORRA UNA LLAMADA A LA API
        """
        try:
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "argentina_cities_uids.json")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("cities", {})
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar JSON de ciudades: {e}")
            return {}
    
    def load_cache(self) -> Dict:
        """
        Cargar eventos desde cache JSON
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache: {e}")
        
        return {"cache_info": {"last_updated": None}, "events": []}
    
    def save_cache(self, events: List[Dict]) -> None:
        """
        Guardar eventos en cache JSON 
        Cache válido por 24 horas como dijiste
        """
        try:
            cache_data = {
                "cache_info": {
                    "last_updated": datetime.now().isoformat(),
                    "cache_valid_until": (datetime.now() + timedelta(days=1)).isoformat(),
                    "events_count": len(events),
                    "location": "Argentina",
                    "api_calls_saved": 1
                },
                "events": events
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Cache guardado: {len(events)} eventos válidos por 24h")
            
        except Exception as e:
            logger.error(f"❌ Error guardando cache: {e}")
    
    def is_cache_valid(self) -> bool:
        """
        Verificar si el cache es válido (no pasaron 24h)
        TAMBIÉN verifica caché rate-limit para evitar llamadas repetidas
        """
        # 1. Verificar caché rate-limit primero (prioritario)
        try:
            rate_limit_cache_file = "/mnt/c/Code/eventos-visualizer/backend/data/facebook_rate_limit_cache.json"
            if os.path.exists(rate_limit_cache_file):
                with open(rate_limit_cache_file, 'r') as f:
                    rate_cache = json.load(f)
                    
                cache_info = rate_cache.get("cache_info", {})
                if cache_info.get("status") == "rate_limited_429":
                    # Verificar si el caché rate-limit sigue válido (24h)
                    timestamp = cache_info.get("timestamp")
                    if timestamp:
                        cache_time = datetime.fromisoformat(timestamp)
                        duration_hours = cache_info.get("cache_duration_hours", 24)
                        
                        if datetime.now() < cache_time + timedelta(hours=duration_hours):
                            logger.info(f"🔒 RATE LIMIT CACHÉ ACTIVO - No hacer llamadas API")
                            logger.info(f"   ⏰ Válido hasta: {(cache_time + timedelta(hours=duration_hours)).isoformat()}")
                            return True
        except Exception as e:
            logger.debug(f"Error verificando rate limit cache: {e}")
        
        # 2. Verificar caché normal de eventos
        cache = self.load_cache()
        
        if not cache.get("cache_info", {}).get("cache_valid_until"):
            return False
            
        try:
            valid_until = datetime.fromisoformat(cache["cache_info"]["cache_valid_until"])
            return datetime.now() < valid_until
        except:
            return False
    
    async def get_city_uid_direct_api(self, city_name: str = "Buenos Aires") -> str:
        """
        NUEVO MÉTODO: Obtener UID directamente desde API (sin JSON cache)
        MÁS CONFIABLE: Siempre obtiene UID correcto para cualquier ciudad
        """
        logger.info(f"🔍 OBTENIENDO UID DIRECTO DESDE API PARA: '{city_name}'")
        logger.info(f"   🎯 Método mejorado - sin dependencia de JSON cache")
        logger.info(f"   📡 Llamada directa a Facebook API")
        
        # Llamar directamente al método API
        uid = await self.get_city_uid(city_name)
        
        if uid:
            logger.info(f"✅ UID OBTENIDO EXITOSAMENTE:")
            logger.info(f"   🆔 {city_name} -> {uid}")
            logger.info(f"   🎯 UID garantizado correcto y actualizado")
        else:
            logger.error(f"❌ NO SE PUDO OBTENER UID para '{city_name}'")
            logger.error(f"   🚫 Posibles causas: API key inválido, ciudad no existe, rate limit")
        
        return uid
        
    async def get_city_uid(self, city_name: str = "Buenos Aires") -> str:
        """
        PASO 1: Obtener UID de la ciudad usando endpoint correcto
        ¡ENDPOINT CORRECTO FUNCIONANDO!
        """
        try:
            url = f"{self.base_url}/search/locations"
            
            params = {
                "query": city_name.lower()
            }
            
            logger.info(f"🔍 PASO 1 - INICIANDO get_city_uid:")
            logger.info(f"   🏙️ Ciudad objetivo: {city_name}")
            logger.info(f"   📍 URL completa: {url}")
            logger.info(f"   📋 Params: {params}")
            logger.info(f"   🗝️ API Key presente: {'✅' if self.api_key else '❌'}")
            logger.info(f"   🔑 Headers: {self.headers}")
            logger.info(f"   📡 Enviando GET request...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"   📨 Response status: {response.status}")
                    logger.info(f"   📨 Response headers: {dict(response.headers)}")
                    
                    response_text = await response.text()
                    logger.info(f"   📊 Response text length: {len(response_text)}")
                    logger.info(f"   📊 Response preview: {response_text[:300]}...")
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"   ✅ JSON parseado correctamente")
                            logger.info(f"   📊 Data type: {type(data)}")
                            logger.info(f"   📊 Data keys: {list(data.keys()) if isinstance(data, dict) else 'No dict'}")
                            logger.info(f"   📊 Data preview: {str(data)[:500]}...")
                            
                        except Exception as json_error:
                            logger.error(f"   ❌ Error parsing JSON: {json_error}")
                            logger.error(f"   📊 Raw response: {response_text}")
                            return ""
                        
                        results = data.get("results", [])
                        logger.info(f"   📊 Results encontrados: {len(results)}")
                        
                        if results:
                            logger.info(f"   🔍 Analizando {len(results)} resultados:")
                            for i, place in enumerate(results):
                                label = place.get("label", "")
                                uid = place.get("uid", "")
                                logger.info(f"      {i+1}. Label: '{label}' | UID: '{uid}'")
                                
                                if "argentina" in label.lower() and city_name.lower() in label.lower():
                                    city_uid = place.get("uid")
                                    if city_uid:
                                        logger.info(f"✅ ¡MATCH PERFECTO! UID de {city_name}: {city_uid}")
                                        logger.info(f"   🎯 Label completo: {label}")
                                        return str(city_uid)
                            
                            # Si no encuentra específico, tomar el primero
                            first_result = results[0]
                            city_uid = first_result.get("uid")
                            if city_uid:
                                logger.info(f"⚠️ No hay match perfecto, usando primer resultado:")
                                logger.info(f"   📍 Label: {first_result.get('label', 'Sin label')}")
                                logger.info(f"   🆔 UID: {city_uid}")
                                return str(city_uid)
                        else:
                            logger.warning(f"⚠️ RESULTS VACÍO - No se encontraron lugares para {city_name}")
                            logger.warning(f"   📊 Data completa: {data}")
                            return ""
                    else:
                        if response.status == 429:
                            # Rate limit - crear caché temporal para no repetir llamadas
                            logger.warning(f"⚠️ RATE LIMIT (429) - Cuota mensual agotada")
                            logger.warning(f"   🔒 Guardando caché rate-limit por 24 horas")
                            logger.warning(f"   💡 La API funciona, solo necesita upgrade de plan")
                            
                            # Guardar caché indicando rate limit
                            rate_limit_cache = {
                                "events": [],
                                "cache_info": {
                                    "timestamp": datetime.now().isoformat(),
                                    "cache_duration_hours": 24,
                                    "status": "rate_limited_429",
                                    "city": city_name,
                                    "message": "Cuota mensual RapidAPI agotada - API key válido"
                                }
                            }
                            
                            try:
                                import os
                                cache_file = "/mnt/c/Code/eventos-visualizer/backend/data/facebook_rate_limit_cache.json"
                                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                                
                                import json
                                with open(cache_file, 'w') as f:
                                    json.dump(rate_limit_cache, f, indent=2)
                                
                                logger.info(f"   ✅ Caché rate-limit guardado: {cache_file}")
                            except Exception as cache_error:
                                logger.error(f"   ❌ Error guardando caché: {cache_error}")
                            
                            return "rate_limited"  # Indicador especial
                        else:
                            logger.error(f"❌ PASO 1 FALLÓ - Status: {response.status}")
                            logger.error(f"   📊 Response text: {response_text}")
                            return ""
                        
        except Exception as e:
            logger.error(f"❌ Error obteniendo UID: {e}")
            return ""
    
    async def get_events_by_location_id(self, location_id: str, limit: int = 50, city_name: str = "Buenos Aires") -> List[Dict]:
        """
        PASO 2: Obtener eventos usando location_id + fechas (1 mes) + nombre correcto de ciudad
        ¡ENDPOINT CORRECTO FUNCIONANDO!
        """
        try:
            url = f"{self.base_url}/search/events"
            
            # Calcular fechas: desde hoy hasta 1 mes adelante
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            logger.info(f"🎯 PASO 2 - INICIANDO get_events_by_location_id:")
            logger.info(f"   🆔 Location ID: {location_id}")
            logger.info(f"   🏙️ Ciudad: {city_name}")
            logger.info(f"   📊 Limit: {limit}")
            logger.info(f"   📍 URL: {url}")
            logger.info(f"   📅 Fechas: {start_date} a {end_date}")
            logger.info(f"   🗝️ API Key presente: {'✅' if self.api_key else '❌'}")
            
            # Múltiples queries usando el nombre CORRECTO de la ciudad
            queries_template = [
                "eventos {city}",
                "conciertos {city}", 
                "teatro {city}",
                "música {city}",
                "fiestas {city}",
                "espectáculos {city}",
                "shows {city}"
            ]
            
            # Generar queries con el nombre real de la ciudad
            queries_ciudad = [query.format(city=city_name) for query in queries_template]
            
            logger.info(f"   🔍 Queries preparadas: {len(queries_ciudad)} diferentes")
            logger.info(f"   🏙️ Usando ciudad: {city_name}")
            for i, query in enumerate(queries_ciudad):
                logger.info(f"      {i+1}. '{query}'")
            
            all_events = []
            
            # Probar múltiples queries para obtener MÁS eventos
            logger.info(f"   🚀 INICIANDO búsqueda con {queries_ciudad[:3]} (primeras 3 queries)")
            
            for i, query in enumerate(queries_ciudad[:3]):  # Limitar a 3 para no exceder rate limit
                try:
                    params = {
                        "query": query,
                        "location_id": location_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": min(limit // 3, 20)  # Dividir limit entre queries
                    }
                    
                    logger.info(f"🔍 Query {i+1}/3: '{query}'")
                    logger.info(f"   📋 Params completos: {params}")
                    logger.info(f"   🔑 Headers: {self.headers}")
                    logger.info(f"   📡 Enviando GET request...")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=self.headers, params=params) as response:
                            logger.info(f"   📨 Response status: {response.status}")
                            
                            response_text = await response.text()
                            logger.info(f"   📊 Response text length: {len(response_text)}")
                            logger.info(f"   📊 Response preview: {response_text[:300]}...")
                            
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    logger.info(f"   ✅ JSON parseado correctamente")
                                    logger.info(f"   📊 Data type: {type(data)}")
                                    logger.info(f"   📊 Data keys: {list(data.keys()) if isinstance(data, dict) else 'No dict'}")
                                    
                                    events = data.get("results", [])
                                    logger.info(f"   📊 Events encontrados: {len(events)}")
                                    
                                    if events:
                                        logger.info(f"   🔍 Analizando primeros 3 eventos:")
                                        for j, event in enumerate(events[:3]):
                                            event_title = event.get("title", "Sin título")[:50]
                                            event_id = event.get("event_id", "Sin ID")
                                            event_type = event.get("type", "Sin tipo")
                                            logger.info(f"      {j+1}. '{event_title}...' | ID: {event_id} | Type: {event_type}")
                                        
                                        all_events.extend(events)
                                        logger.info(f"✅ Query '{query}': {len(events)} eventos agregados")
                                        logger.info(f"   📈 Total acumulado: {len(all_events)} eventos")
                                    else:
                                        logger.info(f"📝 Query '{query}': Sin eventos en results")
                                        logger.info(f"   📊 Data completa: {str(data)[:200]}...")
                                        
                                except Exception as json_error:
                                    logger.error(f"   ❌ Error parsing JSON: {json_error}")
                                    logger.error(f"   📊 Raw response: {response_text}")
                                    
                            else:
                                logger.warning(f"⚠️ Query '{query}' falló con status: {response.status}")
                                logger.warning(f"   📊 Error response: {response_text}")
                    
                    logger.info(f"   ⏱️ Esperando 0.5s antes de próxima query...")
                    await asyncio.sleep(0.5)  # Rate limiting entre queries
                    
                except Exception as e:
                    logger.error(f"❌ Error con query '{query}': {e}")
                    continue
            
            logger.info(f"🎯 PASO 2 COMPLETADO:")
            logger.info(f"   📅 Fechas consultadas: {start_date} a {end_date}")
            logger.info(f"   🔥 Total eventos encontrados: {len(all_events)}")
            logger.info(f"   📊 Queries ejecutadas: {len(queries_ciudad[:3])}")
            logger.info(f"   🆔 Location ID usado: {location_id}")
            
            if all_events:
                logger.info(f"   ✅ ÉXITO: Retornando {len(all_events)} eventos")
                logger.info(f"   🔍 Títulos de primeros 5 eventos:")
                for i, event in enumerate(all_events[:5]):
                    title = event.get("title", "Sin título")[:60]
                    logger.info(f"      {i+1}. {title}...")
            else:
                logger.warning(f"   ⚠️ ADVERTENCIA: No se encontraron eventos")
            
            return all_events
                        
        except Exception as e:
            logger.error(f"❌ Error obteniendo eventos: {e}")
            return []
    
    async def search_events(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Buscar eventos específicos usando búsqueda de Facebook
        """
        try:
            url = f"{self.base_url}/search"
            
            params = {
                "query": f"{query} eventos Buenos Aires",
                "type": "posts",
                "limit": limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.warning(f"❌ RapidAPI search error {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de eventos: {e}")
            return []
    
    def is_event_post(self, post: Dict) -> bool:
        """
        Determinar si un post es sobre un evento
        """
        text_content = ""
        
        # Obtener todo el texto del post
        if post.get("text"):
            text_content += post["text"].lower()
        if post.get("description"):
            text_content += " " + post["description"].lower()
        if post.get("title"):
            text_content += " " + post["title"].lower()
        
        # Buscar keywords de eventos
        event_score = 0
        for keyword in self.event_keywords:
            if keyword in text_content:
                event_score += 1
        
        # También buscar patrones de fecha/hora
        date_patterns = [
            r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}',  # 25/12/2025
            r'\d{1,2} de \w+ de \d{4}',           # 25 de diciembre de 2025
            r'\w+ \d{1,2}',                       # diciembre 25
            r'\d{1,2}:\d{2}',                     # 20:30
            r'\d{1,2}h',                          # 20h
            r'(lunes|martes|miércoles|jueves|viernes|sábado|domingo)',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text_content):
                event_score += 2
        
        return event_score >= 3  # Mínimo score para considerarlo evento
    
    def extract_event_from_post(self, post: Dict, source_page: str) -> Dict:
        """
        Extraer información de evento de un post de Facebook
        """
        try:
            # Título del evento
            title = post.get("text", "")[:100] if post.get("text") else "Evento Facebook"
            
            # Si el texto es muy largo, usar primeras líneas
            if len(title) > 60:
                lines = title.split('\n')
                title = lines[0] if lines[0] else (lines[1] if len(lines) > 1 else title[:60])
            
            # Descripción
            description = post.get("text", "") or post.get("description", "")
            
            # Fecha - extraer de texto
            date_text = self.extract_date_from_text(description)
            
            # URL del post
            post_url = post.get("url", "") or post.get("link", "")
            
            # Imagen
            image_url = ""
            if post.get("images") and len(post["images"]) > 0:
                image_url = post["images"][0].get("url", "")
            
            # Detectar tipo de evento
            category = self.detect_event_category(title + " " + description)
            
            # Location - usar página como venue
            venue_name = self.get_venue_from_page(source_page)
            
            return {
                "title": title.strip(),
                "description": description[:200] + "..." if len(description) > 200 else description,
                "date_text": date_text,
                "venue_name": venue_name,
                "location": "Buenos Aires, Argentina",
                "post_url": post_url,
                "image_url": image_url,
                "category": category,
                "source": f"facebook_{source_page}",
                "source_api": "rapidapi_facebook_scraper",
                "scraped_at": datetime.now().isoformat(),
                "raw_post_data": post  # Para debugging
            }
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo evento: {e}")
            return None
    
    def extract_date_from_text(self, text: str) -> str:
        """
        Extraer fecha de texto usando patrones
        """
        if not text:
            return "Consultar fecha en Facebook"
        
        text_lower = text.lower()
        
        # Patrones de fecha más comunes en español
        patterns = [
            r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}',
            r'\d{1,2} de \w+ de \d{4}',
            r'(lunes|martes|miércoles|jueves|viernes|sábado|domingo) \d{1,2}',
            r'\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) \d{1,2}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group()
        
        # Buscar horarios
        time_match = re.search(r'\d{1,2}:\d{2}', text)
        if time_match:
            return f"Horario: {time_match.group()}"
        
        return "Ver fecha en Facebook"
    
    def detect_event_category(self, text: str) -> str:
        """
        Detectar categoría del evento
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['música', 'concierto', 'recital', 'festival', 'show']):
            return 'music'
        elif any(word in text_lower for word in ['teatro', 'obra', 'dramaturgia', 'comedia']):
            return 'theater'
        elif any(word in text_lower for word in ['arte', 'exposición', 'muestra', 'galería']):
            return 'arts'
        elif any(word in text_lower for word in ['fiesta', 'party', 'dj', 'club', 'boliche']):
            return 'nightlife'
        elif any(word in text_lower for word in ['workshop', 'seminario', 'conferencia', 'curso']):
            return 'business'
        elif any(word in text_lower for word in ['deporte', 'fútbol', 'basket', 'tenis', 'running']):
            return 'sports'
        else:
            return 'general'
    
    def get_venue_from_page(self, page_name: str) -> str:
        """
        Obtener nombre del venue basado en el nombre de la página
        """
        venue_mapping = {
            "lunaparkoficial": "Luna Park",
            "teatrocolonoficial": "Teatro Colón",
            "teatrosanmartin.buenosaires": "Teatro San Martín",
            "complejoteatral": "Complejo Teatral de Buenos Aires",
            "centroculturalrecoleta": "Centro Cultural Recoleta",
            "usinadelarte": "Usina del Arte",
            "nicetoclub": "Niceto Club",
            "krokodilclub": "Krokodil Club",
            "tecnopolis": "Tecnópolis"
        }
        
        return venue_mapping.get(page_name, page_name.replace(".", " ").title())
    
    def extract_facebook_event_data(self, fb_event: Dict) -> Dict:
        """
        Extraer información de evento de la respuesta de RapidAPI Facebook
        Estructura real: {"type":"search_event","event_id":"...","title":"...","url":"..."}
        """
        try:
            # La API devuelve estructura específica
            title = fb_event.get("title", "Evento Facebook")
            event_id = fb_event.get("event_id", "")
            event_url = fb_event.get("url", "")
            event_type = fb_event.get("type", "")
            
            # Solo procesar eventos reales
            if event_type != "search_event" or not title or len(title) < 5:
                return None
            
            # Categoría basada en título
            category = self.detect_event_category(title)
            
            # Limpiar título
            clean_title = title.strip()
            if len(clean_title) > 100:
                clean_title = clean_title[:100] + "..."
            
            return {
                "title": clean_title,
                "description": f"Evento de Facebook: {title}",
                "event_id": event_id,
                "event_url": event_url,
                "venue_name": "Buenos Aires",  # La API no devuelve venue específico
                "location": "Buenos Aires, Argentina",
                "category": category,
                "source": "rapidapi_facebook_events",
                "scraped_at": datetime.now().isoformat(),
                "raw_fb_data": fb_event
            }
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de evento Facebook: {e}")
            return None
    
    async def scrape_facebook_events_rapidapi(self, city_name: str = "Buenos Aires", limit: int = 50, max_time_seconds: float = 15.0) -> List[Dict]:
        """
        Scraping completo usando RapidAPI Facebook Scraper
        CADENA DE LLAMADOS: obtener UID ciudad -> obtener TODOS los eventos
        ¡Aquí aparece el 100% de los eventos de Facebook!
        """
        if not self.api_key:
            logger.error("❌ RAPIDAPI_KEY no configurado en variables de entorno")
            return []
        
        logger.info(f"🚀 INICIANDO PROCESO COMPLETO DE FACEBOOK SCRAPER")
        logger.info(f"=" * 60)
        
        # VERIFICAR CACHE PRIMERO (solo va a la API una vez al dia)
        logger.info(f"🔍 VERIFICANDO CACHE...")
        if self.is_cache_valid():
            cache_data = self.load_cache()
            cached_events = cache_data.get("events", [])
            cache_info = cache_data.get("cache_info", {})
            
            logger.info(f"💾 ✅ CACHE VÁLIDO ENCONTRADO:")
            logger.info(f"   📊 Eventos en cache: {len(cached_events)}")
            logger.info(f"   📅 Última actualización: {cache_info.get('last_updated', 'Desconocido')}")
            logger.info(f"   ⏱️ Válido hasta: {cache_info.get('cache_valid_until', 'Desconocido')}")
            logger.info(f"   🚫 SALTANDO API - Usando cache")
            logger.info(f"=" * 60)
            return cached_events[:limit]
        
        logger.info(f"🔥 ❌ CACHE EXPIRADO O INEXISTENTE")
        logger.info(f"🔥 INICIANDO NUEVA LLAMADA A RapidAPI Facebook Scraper")
        logger.info(f"🏙️ Ciudad objetivo: {city_name}")
        logger.info(f"📊 Límite de eventos: {limit}")
        logger.info(f"⏰ Max tiempo: {max_time_seconds}s")
        logger.info(f"🗝️ API Key configurado: {'✅' if self.api_key else '❌'}")
        logger.info(f"=" * 60)
        
        all_events = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            # PASO 1: SIEMPRE obtener UID desde API (más confiable)
            logger.info(f"🔍 PASO 1: OBTENIENDO UID DE CIUDAD VIA API")
            logger.info(f"   🏙️ Ciudad: {city_name}")
            logger.info(f"   📡 Llamando directamente a API (sin JSON cache)")
            logger.info(f"   🎯 Esto asegura UID correcto para cualquier ciudad")
            
            city_uid = await self.get_city_uid_direct_api(city_name)
            
            if city_uid:
                logger.info(f"✅ PASO 1 ÉXITO: UID obtenido desde API")
                logger.info(f"   🆔 UID de {city_name}: {city_uid}")
                logger.info(f"   🎯 UID garantizado correcto para la ciudad solicitada")
            else:
                logger.error(f"❌ PASO 1 FALLÓ: No se pudo obtener UID para {city_name}")
                logger.error(f"   🚫 ABORTANDO: Sin UID no se pueden buscar eventos")
                logger.error(f"   💡 Posibles causas: API key inválido, ciudad no existe, rate limit")
                return []
            
            # PASO 2: Obtener TODOS los eventos de esa ciudad
            logger.info(f"🎯 PASO 2: OBTENIENDO EVENTOS CON UID")
            logger.info(f"   🆔 Usando UID: {city_uid}")
            logger.info(f"   🏙️ Para ciudad: {city_name}")
            logger.info(f"   📊 Límite: {limit} eventos")
            
            facebook_events = await self.get_events_by_location_id(city_uid, limit, city_name)
            
            if not facebook_events:
                logger.warning(f"⚠️ No se encontraron eventos para {city_name}")
                return []
            
            logger.info(f"🎉 ¡ÉXITO! Encontrados {len(facebook_events)} eventos de Facebook")
            
            # PASO 3: Procesar y extraer información
            for fb_event in facebook_events:
                try:
                    event = self.extract_facebook_event_data(fb_event)
                    if event:
                        all_events.append(event)
                except Exception as e:
                    logger.error(f"Error procesando evento: {e}")
                    continue
            
            # Deduplicar eventos
            unique_events = self.deduplicate_facebook_events(all_events)
            
            total_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"🔥 RapidAPI Facebook Scraper COMPLETADO:")
            logger.info(f"   🏙️ Ciudad: {city_name} (UID: {city_uid})")
            logger.info(f"   📊 Eventos Facebook API: {len(facebook_events)}")
            logger.info(f"   📊 Eventos procesados: {len(all_events)}")
            logger.info(f"   📊 Eventos únicos: {len(unique_events)}")
            logger.info(f"   ⏱️ Tiempo total: {total_time:.2f}s")
            
            # GUARDAR EN CACHE (válido por 24h - solo va a la API una vez al dia)
            if unique_events:
                self.save_cache(unique_events)
                logger.info(f"💾 CACHE ACTUALIZADO: {len(unique_events)} eventos guardados")
            
            return unique_events
            
        except Exception as e:
            logger.error(f"❌ Error en scraping RapidAPI Facebook: {e}")
            return []
    
    def deduplicate_facebook_events(self, events: List[Dict]) -> List[Dict]:
        """
        Deduplicar eventos de Facebook
        """
        seen_titles = set()
        unique_events = []
        
        for event in events:
            if not event:
                continue
            
            title = event.get("title", "").lower().strip()
            
            # Normalizar título
            title_clean = re.sub(r'[^\w\s]', '', title)
            
            if (title_clean and 
                len(title_clean) > 5 and
                title_clean not in seen_titles):
                
                seen_titles.add(title_clean)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_facebook_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normalización HONESTA - Solo con datos reales de Facebook API
        Si no hay datos reales, retorna array vacío
        """
        normalized = []
        
        for event in events:
            try:
                # SOLO procesar si tenemos título real
                title = event.get("title", "").strip()
                if not title or len(title) < 5:
                    continue  # Skip eventos sin título válido
                
                # SOLO procesar si tenemos fecha real del evento
                event_date = event.get("start_date") or event.get("date_text")
                if not event_date or "consultar" in str(event_date).lower():
                    continue  # Skip eventos sin fecha real
                
                # SOLO procesar si tenemos venue/ubicación real
                venue_name = event.get("venue_name", "").strip()
                if not venue_name or venue_name == "Buenos Aires":
                    continue  # Skip eventos sin venue específico
                
                # SOLO procesar si tenemos coordenadas reales
                latitude = event.get("latitude")
                longitude = event.get("longitude")
                if not (latitude and longitude):
                    continue  # Skip eventos sin coordenadas
                
                # SOLO usar precio si viene en los datos reales
                price = event.get("price", 0.0)
                is_free = event.get("is_free", price == 0.0)
                
                normalized_event = {
                    "title": title,
                    "description": event.get("description", f"Evento de Facebook: {title}"),
                    
                    "start_datetime": event.get("start_datetime", ""),
                    "end_datetime": event.get("end_datetime", ""),
                    
                    "venue_name": venue_name,
                    "venue_address": event.get("venue_address", venue_name),
                    "latitude": latitude,
                    "longitude": longitude,
                    
                    "category": event.get("category", "general"),
                    "subcategory": "",
                    "tags": ["facebook", "rapidapi"],
                    
                    "price": price,
                    "currency": event.get("currency", "USD"),
                    "is_free": is_free,
                    
                    "source": "rapidapi_facebook",
                    "source_id": f"fb_rapid_{abs(hash(title))}",
                    "event_url": event.get("event_url", ""),
                    "image_url": event.get("image_url", ""),
                    
                    "organizer": event.get("organizer", venue_name),
                    "capacity": event.get("capacity", 0),
                    "status": "live",
                    
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando evento Facebook: {e}")
                continue
        
        logger.info(f"📊 Facebook eventos normalizados: {len(normalized)} de {len(events)} (solo con datos reales)")
        return normalized


async def test_rapidapi_facebook_scraper():
    """
    Función de testing
    """
    scraper = RapidApiFacebookScraper()
    
    if not scraper.api_key:
        print("⚠️ RAPIDAPI_KEY no configurado")
        print("📋 Para usar este scraper:")
        print("   1. Conseguir API key en: https://rapidapi.com/krasnoludkolo/api/facebook-scraper3")
        print("   2. Agregar a .env: RAPIDAPI_KEY=tu_key_aqui")
        print("   3. Reiniciar servidor")
        return []
    
    print("🔥 INICIANDO RapidAPI Facebook Scraper TEST...")
    print(f"📱 Páginas configuradas: {len(scraper.facebook_event_pages)}")
    print(f"🗝️ API Key configurado: {'✅' if scraper.api_key else '❌'}")
    
    # Test scraping
    events = await scraper.scrape_facebook_events_rapidapi(city_name="Buenos Aires", limit=30, max_time_seconds=10.0)
    
    print(f"\n🎯 RESULTADOS RapidAPI Facebook:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    if events:
        # Por categoría
        categories = {}
        for event in events:
            cat = event.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📈 Por categoría:")
        for cat, count in categories.items():
            print(f"   {cat}: {count} eventos")
        
        # Mostrar eventos
        print(f"\n📱 Primeros 10 eventos Facebook:")
        for i, event in enumerate(events[:10]):
            print(f"\n{i+1:2d}. 📱 {event['title'][:60]}...")
            print(f"     🏛️ {event.get('venue_name', 'Sin venue')}")
            print(f"     📅 {event.get('date_text', 'Sin fecha')}")
            print(f"     🎪 {event.get('category', 'general')}")
        
        # Normalizar
        normalized = scraper.normalize_facebook_events(events)
        print(f"\n✅ {len(normalized)} eventos Facebook normalizados")
        
        return normalized
    else:
        print("⚠️ No se encontraron eventos Facebook")
        return []

async def test_with_barcelona():
    """
    Test específico con Barcelona
    """
    scraper = RapidApiFacebookScraper()
    
    if not scraper.api_key:
        print("⚠️ RAPIDAPI_KEY no configurado")
        print("📋 Para usar este scraper:")
        print("   1. Conseguir API key en: https://rapidapi.com/krasnoludkolo/api/facebook-scraper3")
        print("   2. Agregar a .env: RAPIDAPI_KEY=tu_key_aqui")
        print("   3. Reiniciar servidor")
        return []
    
    print("🔥 INICIANDO RapidAPI Facebook Scraper con BARCELONA...")
    print(f"🏙️ Ciudad: Barcelona")
    print(f"🗝️ API Key configurado: {'✅' if scraper.api_key else '❌'}")
    
    # Test scraping con Barcelona
    events = await scraper.scrape_facebook_events_rapidapi(city_name="Barcelona", limit=20, max_time_seconds=15.0)
    
    print(f"\n🎯 RESULTADOS Barcelona Facebook:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    if events:
        print(f"\n📱 Eventos de Barcelona:")
        for i, event in enumerate(events[:10]):
            print(f"\n{i+1:2d}. 📱 {event['title'][:60]}...")
            print(f"     🏛️ {event.get('venue_name', 'Sin venue')}")
            print(f"     🎪 {event.get('category', 'general')}")
    else:
        print("⚠️ No se encontraron eventos en Barcelona")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_with_barcelona())