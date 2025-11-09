"""
Fever Scraper - Experiencias y eventos únicos
Plataforma global de descubrimiento de experiencias
"""

import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import quote

from services.scraper_interface import BaseGlobalScraper

logger = logging.getLogger(__name__)

class FeverScraper(BaseGlobalScraper):
    def __init__(self, url_discovery_service=None):
        super().__init__(url_discovery_service)
        self.name = "fever"
        self.display_name = "Fever"
        self.base_url = "https://feverup.com"
        self.enabled_by_default = True
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://feverup.com',
        }

    def _get_city_slug(self, location: str) -> str:
        """Obtiene el slug de ciudad para Fever"""
        city = location.lower().split(',')[0].strip()

        # Mapeo de ciudades a slugs de Fever
        city_slugs = {
            'barcelona': 'barcelona',
            'madrid': 'madrid',
            'valencia': 'valencia',
            'sevilla': 'seville',
            'bilbao': 'bilbao',
            'malaga': 'malaga',
            'buenos aires': 'buenos-aires',
            'mexico city': 'mexico-city',
            'ciudad de mexico': 'mexico-city',
            'cdmx': 'mexico-city',
            'sao paulo': 'sao-paulo',
            'santiago': 'santiago',
            'lima': 'lima',
            'bogota': 'bogota',
            'miami': 'miami',
            'new york': 'new-york',
            'los angeles': 'los-angeles',
            'london': 'london',
            'paris': 'paris',
            'rome': 'rome',
            'milan': 'milan',
            'lisbon': 'lisbon',
            'berlin': 'berlin'
        }

        return city_slugs.get(city, city.replace(' ', '-'))

    async def fetch_events(self, location: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Obtiene eventos de Fever para una ubicación"""
        logger.info(f"🎪 Fever Scraper: Iniciando para '{location}'")

        events = []
        try:
            city_slug = self._get_city_slug(location)

            # Fever tiene varias URLs posibles
            urls = [
                f"{self.base_url}/{city_slug}",
                f"{self.base_url}/en/{city_slug}/events",
                f"{self.base_url}/es/{city_slug}/events"
            ]

            for url in urls:
                try:
                    events = await self._fetch_from_url(url, location, limit)
                    if events:
                        break
                except:
                    continue

            if events:
                logger.info(f"✅ Fever: {len(events)} experiencias encontradas")
            else:
                logger.warning(f"⚠️ Fever: No se encontraron eventos reales en {location}")

        except Exception as e:
            logger.error(f"❌ Error scrapeando Fever: {str(e)}")

        return events[:limit]

    async def _fetch_from_url(self, url: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Intenta obtener eventos desde una URL específica"""
        events = []

        logger.info(f"🔗 Fever URL: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Buscar JSON-LD con datos estructurados
                    scripts = soup.find_all('script', type='application/ld+json')
                    for script in scripts:
                        try:
                            data = json.loads(script.string)
                            if isinstance(data, list):
                                for item in data:
                                    if item.get('@type') == 'Event':
                                        events.append(self._parse_json_event(item, location))
                            elif data.get('@type') == 'Event':
                                events.append(self._parse_json_event(data, location))
                        except:
                            pass

                    # Buscar eventos en el HTML
                    event_cards = soup.find_all(['article', 'div', 'li'], class_=re.compile('event|experience|card'))

                    for card in event_cards[:limit]:
                        event = self._parse_html_event(card, location)
                        if event:
                            events.append(event)

        return events

    def _parse_json_event(self, data: Dict, location: str) -> Dict[str, Any]:
        """Parsea evento desde JSON-LD"""
        return {
            'id': f"fever_{data.get('url', '').split('/')[-1]}",
            'title': data.get('name', 'Experiencia Fever'),
            'description': data.get('description', ''),
            'start_datetime': data.get('startDate'),
            'end_datetime': data.get('endDate'),
            'venue_name': data.get('location', {}).get('name', ''),
            'venue_address': data.get('location', {}).get('address', location),
            'category': 'Experiencias',
            'subcategory': self._categorize_experience(data.get('name', '')),
            'price': self._extract_price(data.get('offers', {})),
            'currency': 'EUR',
            'is_free': False,
            'image_url': data.get('image'),
            'event_url': data.get('url'),
            'source': 'fever',
            'source_display': '🎪 Fever'
        }

    def _parse_html_event(self, card, location: str) -> Optional[Dict[str, Any]]:
        """Parsea evento desde HTML - SOLO eventos con datos reales"""
        try:
            # Título
            title_elem = card.find(['h2', 'h3', 'h4'], class_=re.compile('title|name'))
            if not title_elem:
                title_elem = card.find('a')
            title = title_elem.text.strip() if title_elem else None

            if not title:
                return None

            # Buscar fecha REAL
            date_elem = card.find(['time', 'span', 'div'], class_=re.compile('date|time'))
            date_text = date_elem.get('datetime') if date_elem and date_elem.has_attr('datetime') else None
            if not date_text and date_elem:
                date_text = date_elem.text.strip()

            # Si no hay fecha real, NO devolver el evento
            if not date_text:
                return None

            # URL
            url_elem = card.find('a', href=True)
            event_url = url_elem['href'] if url_elem else None
            if event_url and not event_url.startswith('http'):
                event_url = f"{self.base_url}{event_url}"

            # Sin URL real, no devolver
            if not event_url:
                return None

            # Descripción REAL
            desc_elem = card.find(['p', 'div'], class_=re.compile('description|desc|summary'))
            description = desc_elem.text.strip() if desc_elem else None

            # Venue REAL
            venue_elem = card.find(['span', 'div'], class_=re.compile('venue|location|place'))
            venue_name = venue_elem.text.strip() if venue_elem else None

            # Precio
            price_elem = card.find(['span', 'div'], class_=re.compile('price'))
            price_text = price_elem.text.strip() if price_elem else ''

            # Imagen REAL
            img_elem = card.find('img')
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            if image_url and not image_url.startswith('http'):
                image_url = f"{self.base_url}{image_url}"

            # Solo devolver si tenemos datos suficientes REALES
            if not (description and venue_name and image_url):
                logger.debug(f"⚠️ Evento '{title}' incompleto, saltando (faltan datos reales)")
                return None

            return {
                'id': f"fever_{hash(title)}",
                'title': title,
                'description': description,
                'start_datetime': date_text,
                'venue_name': venue_name,
                'venue_address': f"{venue_name}, {location}",
                'category': 'Experiencias',
                'subcategory': self._categorize_experience(title),
                'price': self._extract_price_from_text(price_text),
                'currency': 'EUR',
                'is_free': 'gratis' in price_text.lower() or 'free' in price_text.lower(),
                'image_url': image_url,
                'event_url': event_url,
                'source': 'fever',
                'source_display': '🎪 Fever'
            }
        except Exception as e:
            logger.debug(f"⚠️ Error parseando evento Fever: {str(e)}")
            return None

    def _generate_demo_experiences(self, location: str, count: int) -> List[Dict[str, Any]]:
        """Genera experiencias demo variadas tipo Fever"""
        events = []

        experiences = [
            {
                'title': 'Candlelight: Tributo a Coldplay',
                'category': 'Conciertos a la luz de las velas',
                'price': 25.0,
                'venue': 'Basílica de Santa María del Pi'
            },
            {
                'title': 'Exposición Inmersiva Van Gogh',
                'category': 'Arte Digital',
                'price': 18.0,
                'venue': 'Centro de Artes Digitales'
            },
            {
                'title': 'Cena en las Alturas con Vistas 360°',
                'category': 'Gastronomía',
                'price': 75.0,
                'venue': 'Torre Panorámica'
            },
            {
                'title': 'Escape Room: El Misterio del Museo',
                'category': 'Aventura',
                'price': 22.0,
                'venue': 'Escape Barcelona'
            },
            {
                'title': 'Flamenco Show + Tapas',
                'category': 'Espectáculo',
                'price': 45.0,
                'venue': 'Tablao Flamenco'
            },
            {
                'title': 'Tour Nocturno de Leyendas y Misterios',
                'category': 'Tours',
                'price': 15.0,
                'venue': 'Barrio Gótico'
            },
            {
                'title': 'Brunch con Jazz en Vivo',
                'category': 'Gastronomía',
                'price': 35.0,
                'venue': 'Jazz Café'
            },
            {
                'title': 'Clase de Coctelería Premium',
                'category': 'Experiencias',
                'price': 40.0,
                'venue': 'Cocktail Academy'
            },
            {
                'title': 'Museo de Ilusiones - Entrada Sin Colas',
                'category': 'Museos',
                'price': 12.0,
                'venue': 'Museo de Ilusiones'
            },
            {
                'title': 'Sunset Yoga en la Azotea',
                'category': 'Bienestar',
                'price': 20.0,
                'venue': 'Rooftop Studio'
            },
            {
                'title': 'Cata de Vinos y Maridaje',
                'category': 'Gastronomía',
                'price': 55.0,
                'venue': 'Bodega Boutique'
            },
            {
                'title': 'Stand-up Comedy Night',
                'category': 'Espectáculo',
                'price': 18.0,
                'venue': 'Comedy Club'
            }
        ]

        for i in range(min(count, len(experiences))):
            exp = experiences[i]
            date = datetime.now() + timedelta(days=i+2, hours=19)

            events.append({
                'id': f"fever_demo_{i}",
                'title': exp['title'],
                'description': f"{exp['category']} - Una experiencia única que no te puedes perder en {location}",
                'start_datetime': date.isoformat(),
                'end_datetime': (date + timedelta(hours=2)).isoformat(),
                'venue_name': exp['venue'],
                'venue_address': f"{location}",
                'category': 'Experiencias',
                'subcategory': exp['category'],
                'price': exp['price'],
                'currency': 'EUR',
                'is_free': False,
                'image_url': f"https://picsum.photos/400/200?random={hash(exp['title'])}",
                'event_url': f"https://feverup.com/experience/{i}",
                'source': 'fever',
                'source_display': '🎪 Fever',
                'tags': ['experiencia', 'fever', exp['category'].lower()]
            })

        return events

    def _categorize_experience(self, title: str) -> str:
        """Categoriza la experiencia según el título"""
        title_lower = title.lower()

        if 'candlelight' in title_lower or 'concierto' in title_lower:
            return 'Conciertos'
        elif 'museo' in title_lower or 'exposición' in title_lower or 'arte' in title_lower:
            return 'Arte y Cultura'
        elif 'cena' in title_lower or 'brunch' in title_lower or 'cata' in title_lower:
            return 'Gastronomía'
        elif 'escape' in title_lower or 'aventura' in title_lower:
            return 'Aventura'
        elif 'flamenco' in title_lower or 'show' in title_lower or 'comedy' in title_lower:
            return 'Espectáculos'
        elif 'tour' in title_lower or 'visita' in title_lower:
            return 'Tours'
        elif 'yoga' in title_lower or 'wellness' in title_lower:
            return 'Bienestar'
        else:
            return 'Experiencias'

    def _extract_price(self, offers: Any) -> Optional[float]:
        """Extrae precio desde objeto offers"""
        try:
            if isinstance(offers, dict):
                return float(offers.get('price', 0))
            elif isinstance(offers, list) and offers:
                return float(offers[0].get('price', 0))
        except:
            pass
        return None

    async def scrape_events(self, location: str, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Implementación del método abstracto requerido"""
        return await self.fetch_events(location, limit)

    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extrae precio desde texto"""
        try:
            # Buscar números en el texto
            import re
            numbers = re.findall(r'\d+[\.,]?\d*', text)
            if numbers:
                return float(numbers[0].replace(',', '.'))
        except:
            pass
        return None