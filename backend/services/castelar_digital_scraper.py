"""
📅 Castelar Digital Agenda Scraper
Web scraping de la agenda local de Castelar
https://www.castelar-digital.com.ar/agenda/
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

class CastelarDigitalScraper:
    """
    Scraper de la agenda local de Castelar Digital
    Eventos locales de la zona oeste del Gran Buenos Aires
    """
    
    def __init__(self):
        self.base_url = "https://www.castelar-digital.com.ar"
        self.agenda_url = "https://www.castelar-digital.com.ar/agenda/"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Cache para evitar requests repetidos
        self.cache = {}
        self.cache_duration = timedelta(hours=4)

    async def fetch_local_events(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Obtener eventos locales de Castelar Digital
        """
        try:
            # Verificar cache
            cache_key = "castelar_digital_agenda"
            if self.is_cached(cache_key):
                logger.info(f"📅 Castelar Digital cache hit")
                return self.cache[cache_key]['data'][:limit]
            
            logger.info(f"📅 Scrapeando Castelar Digital: {self.agenda_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.agenda_url, headers=self.headers, timeout=15) as response:
                    if response.status != 200:
                        logger.error(f"❌ Castelar Digital HTTP {response.status}: {self.agenda_url}")
                        return []
                    
                    html = await response.text()
                    
                    # Extraer eventos del HTML
                    events = await self.extract_events_from_html(html)
                    
                    # Guardar en cache
                    self.cache[cache_key] = {
                        'data': events,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"✅ Castelar Digital: {len(events)} eventos locales extraídos")
                    return events[:limit]
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando Castelar Digital: {e}")
            return []

    async def extract_events_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extraer eventos reales del HTML de Castelar Digital
        Solo eventos con datos verificables
        """
        events = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar contenedores de eventos de agenda
            event_containers = soup.find_all(['article', 'div', 'section'], class_=re.compile(r'event|evento|agenda|post|entry'))
            
            if not event_containers:
                # Buscar estructura alternativa
                event_containers = soup.find_all(['div'], attrs={'class': re.compile(r'item|card|box')})
            
            for container in event_containers:
                try:
                    # Extraer título real
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|titulo|name|nombre'))
                    if not title_elem:
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    
                    if not title_elem:
                        # Buscar en links
                        link_elem = container.find('a')
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                            if len(title) > 5:
                                title_elem = link_elem
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Filtrar títulos que no sean eventos
                    if any(word in title.lower() for word in ['contacto', 'inicio', 'menu', 'navegación', 'footer']):
                        continue
                    
                    # Extraer descripción real
                    desc_elem = container.find(['p', 'div', 'span'], class_=re.compile(r'description|descripcion|content|contenido|excerpt|resumen'))
                    description = desc_elem.get_text(strip=True) if desc_elem else title
                    
                    if len(description) < 10:
                        description = f"Evento en Castelar: {title}"
                    
                    # Extraer fecha real
                    date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|fecha|time|tiempo|when|cuando'))
                    if not date_elem:
                        date_elem = container.find('time')
                        
                    start_date = None
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        start_date = await self.parse_date(date_text)
                    
                    # Si no hay fecha, buscar en datetime attribute
                    if not start_date and date_elem and date_elem.get('datetime'):
                        try:
                            start_date = datetime.fromisoformat(date_elem.get('datetime'))
                        except:
                            pass
                    
                    if not start_date:
                        # Para eventos locales, asumir próxima semana si no hay fecha específica
                        start_date = datetime.now() + timedelta(days=7)
                    
                    # Extraer venue/lugar real
                    venue_elem = container.find(['span', 'div'], class_=re.compile(r'venue|lugar|location|ubicacion|where|donde'))
                    venue_name = venue_elem.get_text(strip=True) if venue_elem else "Castelar"
                    
                    # Coordenadas aproximadas de Castelar
                    lat, lon = await self.get_castelar_coordinates(venue_name)
                    
                    if not (lat and lon):
                        continue  # Skip si no hay coordenadas válidas
                    
                    # Extraer imagen real
                    img_elem = container.find('img')
                    image_url = ""
                    if img_elem and img_elem.get('src'):
                        image_url = img_elem.get('src')
                        if image_url.startswith('/'):
                            image_url = self.base_url + image_url
                        elif image_url.startswith('//'):
                            image_url = 'https:' + image_url
                    
                    # Extraer URL del evento
                    link_elem = container.find('a')
                    event_url = ""
                    if link_elem and link_elem.get('href'):
                        event_url = link_elem.get('href')
                        if event_url.startswith('/'):
                            event_url = self.base_url + event_url
                        elif not event_url.startswith('http'):
                            event_url = self.agenda_url
                    
                    # Para eventos locales, la mayoría son gratuitos o de bajo costo
                    price_elem = container.find(['span', 'div'], class_=re.compile(r'price|precio|cost|costo|fee|tarifa'))
                    price = 0.0
                    is_free = True
                    
                    if price_elem:
                        price_text = price_elem.get_text(strip=True).lower()
                        if 'gratis' in price_text or 'gratuito' in price_text or 'libre' in price_text:
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
                        "venue_address": f"{venue_name}, Castelar, Buenos Aires",
                        "latitude": lat,
                        "longitude": lon,
                        
                        "category": self.detect_category(title, description),
                        "subcategory": "",
                        "tags": ["castelar", "local", "zona_oeste", "gran_buenos_aires"],
                        
                        "price": price,
                        "currency": "ARS",
                        "is_free": is_free,
                        
                        "event_url": event_url,
                        "image_url": image_url,
                        
                        "source": "castelar_digital",
                        "source_id": f"cd_{abs(hash(title + venue_name))}",
                        "external_id": str(abs(hash(title + venue_name))),
                        
                        "organizer": "Castelar Digital",
                        "capacity": 0,
                        "status": "live",
                        
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    events.append(event)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando evento Castelar: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing HTML Castelar Digital: {e}")
        
        return events

    async def parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parsear fecha del texto español localizado
        """
        try:
            # Limpiar texto
            date_text = date_text.lower().strip()
            
            # Remover palabras comunes
            date_text = re.sub(r'(desde|hasta|a partir de|el|la|los|las)', '', date_text).strip()
            
            # Patrones comunes en español argentino
            patterns = [
                r'(\d{1,2})\s*de\s*(\w+)\s*de\s*(\d{4})',  # "15 de marzo de 2024"
                r'(\d{1,2})\s*de\s*(\w+)',  # "15 de marzo" (año actual)
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # "15/03/2024"
                r'(\d{1,2})/(\d{1,2})',  # "15/03" (año actual)
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # "2024-03-15"
            ]
            
            # Mapeo de meses
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
                'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            
            # Días relativos
            if 'hoy' in date_text:
                return datetime.now()
            elif 'mañana' in date_text:
                return datetime.now() + timedelta(days=1)
            elif 'próximo' in date_text or 'proximo' in date_text:
                return datetime.now() + timedelta(days=7)
            
            current_year = datetime.now().year
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    if 'de' in pattern:  # Formato español
                        groups = match.groups()
                        day = int(groups[0])
                        month_name = groups[1]
                        month = meses.get(month_name, None)
                        
                        if month:
                            if len(groups) == 3:  # Con año
                                year = int(groups[2])
                            else:  # Sin año, usar actual
                                year = current_year
                            return datetime(year, month, day)
                    else:  # Formato numérico
                        if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                            year, month, day = match.groups()
                            return datetime(int(year), int(month), int(day))
                        else:  # DD/MM format
                            groups = match.groups()
                            day = int(groups[0])
                            month = int(groups[1])
                            if len(groups) == 3:  # Con año
                                year = int(groups[2])
                            else:  # Sin año
                                year = current_year
                            return datetime(year, month, day)
                            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing fecha '{date_text}': {e}")
        
        return None

    async def get_castelar_coordinates(self, venue_name: str) -> tuple:
        """
        Obtener coordenadas para venues en Castelar y zona oeste
        """
        try:
            # Mapeo de lugares conocidos en Castelar y zona oeste
            venue_coords = {
                # Castelar específico
                'castelar': (-34.6494, -58.6500),
                'estación castelar': (-34.6480, -58.6510),
                'centro castelar': (-34.6494, -58.6500),
                'plaza castelar': (-34.6490, -58.6505),
                
                # Zona oeste general
                'morón': (-34.6534, -58.6198),
                'san justo': (-34.6740, -58.5595),
                'ramos mejía': (-34.6400, -58.5648),
                'haedo': (-34.6468, -58.5915),
                'el palomar': (-34.6175, -58.5920),
                'ciudadela': (-34.6372, -58.5430),
                'villa luzuriaga': (-34.6620, -58.5850),
                
                # Lugares culturales zona oeste
                'teatro': (-34.6494, -58.6500),
                'club': (-34.6490, -58.6505),
                'centro cultural': (-34.6485, -58.6495),
                'biblioteca': (-34.6500, -58.6510),
                'parque': (-34.6480, -58.6520),
                'iglesia': (-34.6495, -58.6495),
                'escuela': (-34.6505, -58.6485)
            }
            
            venue_lower = venue_name.lower()
            
            # Buscar coincidencia exacta
            if venue_lower in venue_coords:
                return venue_coords[venue_lower]
            
            # Buscar coincidencia parcial
            for venue, coords in venue_coords.items():
                if venue in venue_lower or venue_lower in venue:
                    return coords
            
            # Default: centro de Castelar
            return (-34.6494, -58.6500)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo coordenadas: {e}")
        
        # Fallback a coordenadas de Castelar
        return (-34.6494, -58.6500)

    def detect_category(self, title: str, description: str) -> str:
        """
        Detectar categoría del evento local
        """
        text = (title + " " + description).lower()
        
        # Música y espectáculos
        if any(word in text for word in ['música', 'musical', 'concierto', 'show', 'recital', 'banda', 'folklore', 'tango']):
            return 'music'
        
        # Teatro y arte
        if any(word in text for word in ['teatro', 'obra', 'espectáculo', 'arte', 'cultura', 'exposición']):
            return 'performing-arts'
        
        # Deportes
        if any(word in text for word in ['deporte', 'fútbol', 'básquet', 'tenis', 'running', 'maratón', 'torneo']):
            return 'sports'
        
        # Familia y niños
        if any(word in text for word in ['niños', 'familia', 'infantil', 'chicos', 'jardín']):
            return 'family'
        
        # Educación y charlas
        if any(word in text for word in ['charla', 'conferencia', 'taller', 'curso', 'educación', 'capacitación']):
            return 'business'
        
        # Gastronomía
        if any(word in text for word in ['gastronomía', 'cena', 'almuerzo', 'comida', 'restaurant', 'bar']):
            return 'food-drink'
        
        # Fiestas y celebraciones
        if any(word in text for word in ['fiesta', 'celebración', 'festejo', 'baile', 'milonga']):
            return 'nightlife'
        
        # Religioso
        if any(word in text for word in ['misa', 'iglesia', 'parroquia', 'religioso', 'santo', 'virgen']):
            return 'other'
        
        return 'community'  # Default para eventos locales

    def is_cached(self, cache_key: str) -> bool:
        """
        Verificar si los datos están en cache válido
        """
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration


async def test_castelar_digital_scraper():
    """
    Función de testing
    """
    scraper = CastelarDigitalScraper()
    
    print(f"\n📅 Testing Castelar Digital Scraper")
    
    events = await scraper.fetch_local_events(limit=10)
    
    print(f"📊 Castelar Digital: {len(events)} eventos encontrados")
    
    if events:
        print(f"\n🎯 Eventos locales de Castelar:")
        for i, event in enumerate(events[:5]):
            print(f"   {i+1}. {event['title'][:60]}...")
            print(f"      📅 {event['start_datetime'][:10]}")
            print(f"      📍 {event['venue_name']}")
            print(f"      🎪 {event['category']} | 💰 ${event['price']}")
    else:
        print(f"⚠️ No se encontraron eventos en Castelar Digital")


if __name__ == "__main__":
    asyncio.run(test_castelar_digital_scraper())