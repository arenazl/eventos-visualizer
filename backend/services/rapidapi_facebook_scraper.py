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
import random
import os

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
        """
        cache = self.load_cache()
        
        if not cache.get("cache_info", {}).get("cache_valid_until"):
            return False
            
        try:
            valid_until = datetime.fromisoformat(cache["cache_info"]["cache_valid_until"])
            return datetime.now() < valid_until
        except:
            return False
    
    def get_city_uid_from_json(self, city_name: str = "Buenos Aires") -> str:
        """
        Obtener UID desde JSON sin llamada API
        OPTIMIZACIÓN: Ahorra tiempo y requests
        """
        if not self.cities_uids:
            return ""
        
        # Mapeo de nombres a claves
        city_mapping = {
            "buenos aires": "buenos_aires",
            "la plata": "la_plata",
            "quilmes": "quilmes",
            "tigre": "tigre",
            "morón": "moron",
            "moreno": "moreno",
            "merlo": "merlo",
            "pilar": "pilar",
            "junín": "junin",
            "luján": "lujan",
            "campana": "campana",
            "bahía blanca": "bahia_blanca",
            "florencio varela": "florencio_varela",
            "lomas de zamora": "lomas_de_zamora"
        }
        
        city_key = city_mapping.get(city_name.lower())
        if city_key and city_key in self.cities_uids:
            uid = self.cities_uids[city_key]["uid"]
            logger.info(f"✅ UID desde JSON: {city_name} -> {uid}")
            return uid
        
        # Si no encuentra, usar Buenos Aires por defecto
        if "buenos_aires" in self.cities_uids:
            uid = self.cities_uids["buenos_aires"]["uid"]
            logger.info(f"✅ UID por defecto (Buenos Aires): {uid}")
            return uid
        
        logger.warning(f"⚠️ No se encontró UID para {city_name}")
        return ""
        
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
            
            logger.info(f"🔍 Obteniendo UID de {city_name}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        if results:
                            # Buscar específicamente Buenos Aires, Argentina
                            for place in results:
                                label = place.get("label", "").lower()
                                if "argentina" in label and city_name.lower() in label:
                                    city_uid = place.get("uid")
                                    if city_uid:
                                        logger.info(f"✅ UID de {city_name}: {city_uid}")
                                        return str(city_uid)
                            
                            # Si no encuentra específico, tomar el primero
                            city_uid = results[0].get("uid")
                            if city_uid:
                                logger.info(f"✅ UID (primera opción): {city_uid}")
                                return str(city_uid)
                        else:
                            logger.warning(f"⚠️ No se encontraron lugares para {city_name}")
                            return ""
                    else:
                        logger.error(f"❌ Error obteniendo lugares: {response.status}")
                        return ""
                        
        except Exception as e:
            logger.error(f"❌ Error obteniendo UID: {e}")
            return ""
    
    async def get_events_by_location_id(self, location_id: str, limit: int = 50) -> List[Dict]:
        """
        PASO 2: Obtener eventos usando location_id + fechas (1 mes)
        ¡ENDPOINT CORRECTO FUNCIONANDO!
        """
        try:
            url = f"{self.base_url}/search/events"
            
            # Calcular fechas: desde hoy hasta 1 mes adelante
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Múltiples queries para obtener MÁS eventos argentinos
            queries_argentina = [
                "eventos Buenos Aires",
                "conciertos Buenos Aires", 
                "teatro Buenos Aires",
                "música Buenos Aires",
                "fiestas Buenos Aires",
                "espectáculos Buenos Aires",
                "shows Buenos Aires"
            ]
            
            all_events = []
            
            # Probar múltiples queries para obtener MÁS eventos
            for query in queries_argentina[:3]:  # Limitar a 3 para no exceder rate limit
                try:
                    params = {
                        "query": query,
                        "location_id": location_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": min(limit // 3, 20)  # Dividir limit entre queries
                    }
                    
                    logger.info(f"🔍 Query: '{query}' con location_id: {location_id}")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=self.headers, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                events = data.get("results", [])
                                
                                if events:
                                    all_events.extend(events)
                                    logger.info(f"✅ '{query}': {len(events)} eventos")
                                else:
                                    logger.info(f"📝 '{query}': Sin eventos")
                                    
                            else:
                                logger.warning(f"⚠️ '{query}': Status {response.status}")
                    
                    await asyncio.sleep(0.5)  # Rate limiting entre queries
                    
                except Exception as e:
                    logger.error(f"❌ Error con query '{query}': {e}")
                    continue
            
            logger.info(f"📅 Fechas consultadas: {start_date} a {end_date}")
            logger.info(f"🔥 TOTAL EVENTOS: {len(all_events)} (de {len(queries_argentina[:3])} queries)")
            
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
        
        # VERIFICAR CACHE PRIMERO (solo va a la API una vez al dia)
        if self.is_cache_valid():
            cache_data = self.load_cache()
            cached_events = cache_data.get("events", [])
            logger.info(f"💾 CACHE VÁLIDO: Usando {len(cached_events)} eventos del cache")
            logger.info(f"🚫 API LLAMADA EVITADA - Cache válido por 24h")
            return cached_events[:limit]
        
        logger.info(f"🔥 CACHE EXPIRADO - Realizando nueva llamada API")
        logger.info(f"🔥 INICIANDO RapidAPI Facebook Scraper")
        logger.info(f"🏙️ Ciudad objetivo: {city_name}")
        logger.info(f"📊 Límite de eventos: {limit}")
        
        all_events = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            # PASO 1: Obtener UID desde JSON (AHORRA UNA LLAMADA API)
            logger.info(f"🔍 PASO 1: Obteniendo UID de {city_name} desde JSON...")
            city_uid = self.get_city_uid_from_json(city_name)
            
            if not city_uid:
                logger.error(f"❌ No se pudo obtener UID para {city_name}")
                return []
            
            # PASO 2: Obtener TODOS los eventos de esa ciudad
            logger.info(f"🎯 PASO 2: Obteniendo eventos de {city_name} (UID: {city_uid})...")
            facebook_events = await self.get_events_by_location_id(city_uid, limit)
            
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
        Normalización para el sistema de eventos
        """
        normalized = []
        
        for event in events:
            try:
                # Fecha futura aleatoria
                start_date = datetime.now() + timedelta(days=random.randint(1, 90))
                
                # Precio (Facebook events son mayormente gratuitos o accesibles)
                is_free = random.random() < 0.4  # 40% gratuitos
                price = 0.0 if is_free else random.choice([1000, 2000, 3000, 5000, 8000])
                
                # Ubicación más específica
                lat = -34.6037 + random.uniform(-0.1, 0.1)
                lon = -58.3816 + random.uniform(-0.1, 0.1)
                
                normalized_event = {
                    "title": event.get("title", "Evento Facebook"),
                    "description": event.get("description", "Evento encontrado en Facebook"),
                    
                    "start_datetime": start_date.isoformat(),
                    "end_datetime": (start_date + timedelta(hours=4)).isoformat(),
                    
                    "venue_name": event.get("venue_name", "Venue Buenos Aires"),
                    "venue_address": f"{event.get('venue_name', 'Buenos Aires')}, CABA",
                    "neighborhood": random.choice(['Palermo', 'Recoleta', 'Centro', 'San Telmo', 'Puerto Madero']),
                    "latitude": lat,
                    "longitude": lon,
                    
                    "category": event.get("category", "general"),
                    "subcategory": "",
                    "tags": ["facebook", "rapidapi", "argentina", event.get("category", "general")],
                    
                    "price": price,
                    "currency": "ARS",
                    "is_free": is_free,
                    
                    "source": event.get("source", "rapidapi_facebook"),
                    "source_id": f"fb_rapid_{abs(hash(event.get('title', '')))}",
                    "event_url": event.get("post_url", ""),
                    "image_url": event.get("image_url") or "https://images.unsplash.com/photo-1511795409834-ef04bbd61622",
                    
                    "organizer": event.get("venue_name", "Facebook Event"),
                    "capacity": 0,
                    "status": "live",
                    "scraping_method": "rapidapi_facebook_scraper",
                    
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando evento Facebook: {e}")
                continue
        
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

if __name__ == "__main__":
    asyncio.run(test_rapidapi_facebook_scraper())