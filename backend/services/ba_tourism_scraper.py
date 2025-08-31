"""
🏛️ Buenos Aires Tourism Official Scraper
Web scraping del sitio oficial de turismo de Buenos Aires
https://turismo.buenosaires.gob.ar/es/article/que-hacer-esta-semana
"""

import aiohttp
import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BuenasAiresTourismScraper:
    """
    Scraper oficial del sitio de turismo de Buenos Aires
    Extrae eventos culturales y actividades semanales
    """
    
    def __init__(self):
        self.base_url = "https://turismo.buenosaires.gob.ar"
        self.weekly_url = "https://turismo.buenosaires.gob.ar/es/article/que-hacer-esta-semana"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Cache para evitar requests repetidos
        self.cache = {}
        self.cache_duration = timedelta(hours=6)

    async def fetch_weekly_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtener eventos de la semana del sitio oficial de turismo BA
        """
        try:
            # Verificar cache
            cache_key = "ba_tourism_weekly"
            if self.is_cached(cache_key):
                logger.info(f"🏛️ BA Tourism cache hit")
                return self.cache[cache_key]['data'][:limit]
            
            logger.info(f"🏛️ Scrapeando Turismo BA: {self.weekly_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.weekly_url, headers=self.headers, timeout=15) as response:
                    if response.status != 200:
                        logger.error(f"❌ BA Tourism HTTP {response.status}: {self.weekly_url}")
                        return []
                    
                    html = await response.text()
                    
                    # Extraer eventos del HTML
                    events = await self.extract_events_from_html(html)
                    
                    # Guardar en cache
                    self.cache[cache_key] = {
                        'data': events,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"✅ BA Tourism: {len(events)} eventos reales extraídos")
                    return events[:limit]
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando BA Tourism: {e}")
            return []

    async def extract_events_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extraer eventos reales del HTML de turismo BA
        Solo eventos con datos verificables
        """
        events = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar contenedores de eventos
            event_containers = soup.find_all(['article', 'div'], class_=re.compile(r'event|evento|activity|actividad'))
            
            for container in event_containers:
                try:
                    # Extraer título real
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|titulo|name|nombre'))
                    if not title_elem:
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Extraer descripción real
                    desc_elem = container.find(['p', 'div'], class_=re.compile(r'description|descripcion|content|contenido'))
                    description = desc_elem.get_text(strip=True) if desc_elem else None
                    
                    if not description or len(description) < 20:
                        continue
                    
                    # Extraer fecha real
                    date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|fecha|time|tiempo'))
                    if not date_elem:
                        date_elem = container.find('time')
                    
                    start_date = None
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        start_date = await self.parse_date(date_text)
                    
                    if not start_date:
                        continue  # Skip si no hay fecha válida
                    
                    # Extraer venue real
                    venue_elem = container.find(['span', 'div'], class_=re.compile(r'venue|lugar|location|ubicacion'))
                    venue_name = venue_elem.get_text(strip=True) if venue_elem else None
                    
                    if not venue_name:
                        continue  # Skip si no hay venue
                    
                    # Extraer dirección real
                    address_elem = container.find(['span', 'div'], class_=re.compile(r'address|direccion|location'))
                    venue_address = address_elem.get_text(strip=True) if address_elem else f"{venue_name}, Buenos Aires"
                    
                    # Extraer imagen real
                    img_elem = container.find('img')
                    image_url = ""
                    if img_elem and img_elem.get('src'):
                        image_url = img_elem.get('src')
                        if image_url.startswith('/'):
                            image_url = self.base_url + image_url
                    
                    # Extraer URL del evento
                    link_elem = container.find('a')
                    event_url = ""
                    if link_elem and link_elem.get('href'):
                        event_url = link_elem.get('href')
                        if event_url.startswith('/'):
                            event_url = self.base_url + event_url
                    
                    # Extraer coordenadas si están disponibles
                    lat, lon = await self.extract_coordinates(container, venue_name)
                    
                    if not (lat and lon):
                        continue  # Skip si no hay coordenadas
                    
                    # Extraer precio real
                    price_elem = container.find(['span', 'div'], class_=re.compile(r'price|precio|cost|costo'))
                    price = 0.0
                    is_free = True
                    
                    if price_elem:
                        price_text = price_elem.get_text(strip=True).lower()
                        if 'gratis' in price_text or 'gratuito' in price_text:
                            price = 0.0
                            is_free = True
                        else:
                            price_match = re.search(r'[\d,\.]+', price_text)
                            if price_match:
                                try:
                                    price = float(price_match.group().replace(',', ''))
                                    is_free = price == 0.0
                                except:
                                    price = 0.0
                                    is_free = True
                    
                    event = {
                        "title": title,
                        "description": description,
                        
                        "start_datetime": start_date.isoformat(),
                        "end_datetime": (start_date + timedelta(hours=2)).isoformat(),
                        
                        "venue_name": venue_name,
                        "venue_address": venue_address,
                        "latitude": lat,
                        "longitude": lon,
                        
                        "category": self.detect_category(title, description),
                        "subcategory": "",
                        "tags": ["ba_tourism", "oficial", "cultura", "buenos_aires"],
                        
                        "price": price,
                        "currency": "ARS",
                        "is_free": is_free,
                        
                        "event_url": event_url,
                        "image_url": image_url,
                        
                        "source": "ba_tourism",
                        "source_id": f"bat_{abs(hash(title + venue_name))}",
                        "external_id": str(abs(hash(title + venue_name))),
                        
                        "organizer": "Gobierno de la Ciudad de Buenos Aires",
                        "capacity": 0,
                        "status": "live",
                        
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    events.append(event)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando evento BA Tourism: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing HTML BA Tourism: {e}")
        
        return events

    async def parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parsear fecha del texto español
        """
        try:
            # Limpiar texto
            date_text = date_text.lower().strip()
            
            # Patrones comunes en español
            patterns = [
                r'(\d{1,2})\s*de\s*(\w+)\s*de\s*(\d{4})',  # "15 de marzo de 2024"
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # "15/03/2024"
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # "2024-03-15"
            ]
            
            # Mapeo de meses
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    if 'de' in pattern:  # Formato español
                        day, month_name, year = match.groups()
                        month = meses.get(month_name, None)
                        if month:
                            return datetime(int(year), month, int(day))
                    else:  # Formato numérico
                        if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                            year, month, day = match.groups()
                        else:  # DD/MM/YYYY
                            day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing fecha '{date_text}': {e}")
        
        return None

    async def extract_coordinates(self, container, venue_name: str) -> tuple:
        """
        Extraer coordenadas reales del HTML o mapear venue conocido
        """
        try:
            # Buscar coordenadas en atributos data-*
            lat_elem = container.find(attrs={'data-lat': True})
            lon_elem = container.find(attrs={'data-lng': True})
            
            if lat_elem and lon_elem:
                lat = float(lat_elem.get('data-lat'))
                lon = float(lon_elem.get('data-lng'))
                return lat, lon
            
            # Buscar en script JSON-LD
            script_tags = container.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if 'geo' in data:
                        lat = float(data['geo']['latitude'])
                        lon = float(data['geo']['longitude'])
                        return lat, lon
                except:
                    continue
            
            # Mapeo de venues conocidos de Buenos Aires
            venue_coords = {
                'teatro colón': (-34.6012, -58.3834),
                'centro cultural recoleta': (-34.5889, -58.3930),
                'caminito': (-34.6375, -58.3615),
                'puerto madero': (-34.6096, -58.3635),
                'san telmo': (-34.6212, -58.3731),
                'palermo': (-34.5764, -58.4209),
                'recoleta': (-34.5889, -58.3930),
                'plaza de mayo': (-34.6080, -58.3729),
                'obelisco': (-34.6037, -58.3816)
            }
            
            venue_lower = venue_name.lower()
            for venue, coords in venue_coords.items():
                if venue in venue_lower:
                    return coords
                    
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo coordenadas: {e}")
        
        return None, None

    def detect_category(self, title: str, description: str) -> str:
        """
        Detectar categoría del evento basado en título y descripción
        """
        text = (title + " " + description).lower()
        
        # Arte y cultura
        if any(word in text for word in ['arte', 'museo', 'galería', 'exposición', 'cultura', 'cultural']):
            return 'arts'
        
        # Música
        if any(word in text for word in ['concierto', 'música', 'musical', 'show', 'recital', 'festival']):
            return 'music'
        
        # Teatro
        if any(word in text for word in ['teatro', 'obra', 'espectáculo', 'drama', 'comedia']):
            return 'performing-arts'
        
        # Familia/Niños
        if any(word in text for word in ['niños', 'familia', 'infantil', 'chicos']):
            return 'family'
        
        # Gastronomía
        if any(word in text for word in ['gastronomía', 'food', 'cena', 'degustación', 'vino', 'cerveza']):
            return 'food-drink'
        
        # Deportes
        if any(word in text for word in ['deporte', 'running', 'maratón', 'bicicleta', 'fitness']):
            return 'sports'
        
        return 'arts'  # Default para turismo BA

    def is_cached(self, cache_key: str) -> bool:
        """
        Verificar si los datos están en cache válido
        """
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration


async def test_ba_tourism_scraper():
    """
    Función de testing
    """
    scraper = BuenasAiresTourismScraper()
    
    print(f"\n🏛️ Testing BA Tourism Scraper")
    
    events = await scraper.fetch_weekly_events(limit=10)
    
    print(f"📊 BA Tourism: {len(events)} eventos encontrados")
    
    if events:
        print(f"\n🎯 Eventos de turismo BA:")
        for i, event in enumerate(events[:5]):
            print(f"   {i+1}. {event['title'][:60]}...")
            print(f"      📅 {event['start_datetime'][:10]}")
            print(f"      📍 {event['venue_name']}")
            print(f"      🎪 {event['category']} | 💰 ${event['price']}")
    else:
        print(f"⚠️ No se encontraron eventos en BA Tourism")


if __name__ == "__main__":
    asyncio.run(test_ba_tourism_scraper())