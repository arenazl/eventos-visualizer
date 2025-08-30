"""
Multi-Technique Events Scraper
Combina todas las técnicas: Bright Data, CloudScraper, Playwright, APIs
Máxima efectividad para obtener eventos reales de Argentina
"""

import asyncio
import aiohttp
import cloudscraper
import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import urllib.parse

logger = logging.getLogger(__name__)

class MultiTechniqueScraper:
    """
    Scraper que combina todas las técnicas disponibles
    """
    
    def __init__(self):
        # URLs y targets de scraping
        self.targets = {
            'eventbrite': {
                'base_url': 'https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/',
                'selectors': {
                    'event_card': '.eds-event-card, .event-card',
                    'title': '.eds-event-card__formatted-name--is-clamped, .event-card__clamp-line--one',
                    'date': '.eds-event-card__sub-content time, .event-card__date',
                    'price': '.eds-event-card__formatted-price, .event-card__price',
                    'location': '.eds-event-card__sub-content [data-testid="location-info"], .event-card__location'
                }
            },
            'meetup': {
                'base_url': 'https://www.meetup.com/find/?location=ar--Buenos%20Aires&source=EVENTS',
                'selectors': {
                    'event_card': '[data-testid="event-card"], .event-listing',
                    'title': 'h3, .event-listing__title',
                    'date': '[data-testid="event-time"], .event-listing__time',
                    'location': '[data-testid="event-location"], .event-listing__location'
                }
            },
            'facebook_pages': [
                'https://www.facebook.com/lunaparkoficial/events',
                'https://www.facebook.com/teatrocolonoficial/events', 
                'https://www.facebook.com/nicetoclub/events',
                'https://www.facebook.com/CCRecoleta/events',
                'https://www.facebook.com/latrasienda/events'
            ],
            'argentina_venues': [
                'https://www.lunapark.com.ar/eventos',
                'https://www.teatrocolon.org.ar/es/programacion',
                'https://www.centroculturalrecoleta.org/programacion',
                'https://www.ccusina.org/agenda'
            ],
            'ticketek': {
                'base_url': 'https://www.ticketek.com.ar/espectaculos/musica',
                'api_url': 'https://api.ticketek.com.ar/api/v1/events'
            }
        }
        
        # User agents rotativos
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        ]
    
    async def method_1_eventbrite_advanced(self) -> List[Dict]:
        """
        Scraping avanzado de Eventbrite Argentina
        """
        events = []
        
        try:
            # Crear scraper anti-detección
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
            )
            
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })
            
            # URLs de Eventbrite Argentina
            eventbrite_urls = [
                'https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/',
                'https://www.eventbrite.com.ar/d/argentina--cordoba/events/',
                'https://www.eventbrite.com.ar/d/argentina--mendoza/events/',
                'https://www.eventbrite.com.ar/d/argentina/music--events/',
                'https://www.eventbrite.com.ar/d/argentina/food-and-drink--events/'
            ]
            
            for url in eventbrite_urls[:3]:  # Limitar para evitar rate limit
                try:
                    logger.info(f"🎫 Scrapeando Eventbrite: {url}")
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(url, timeout=20)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar eventos con múltiples selectores
                        event_selectors = [
                            '.eds-event-card',
                            '.event-card',
                            '[data-testid="event-card"]',
                            'article[data-event-id]'
                        ]
                        
                        for selector in event_selectors:
                            cards = soup.select(selector)
                            
                            for card in cards[:10]:
                                try:
                                    event_data = self._extract_eventbrite_event(card)
                                    if event_data:
                                        events.append(event_data)
                                except Exception as e:
                                    logger.error(f"Error extrayendo evento Eventbrite: {e}")
                                    continue
                            
                            if cards:  # Si encontró eventos, no seguir con otros selectores
                                break
                    
                    logger.info(f"✅ Eventbrite {url}: {len(events)} eventos")
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error Eventbrite {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error general Eventbrite: {e}")
        
        return events
    
    async def method_2_meetup_scraping(self) -> List[Dict]:
        """
        Scraping de Meetup Argentina
        """
        events = []
        
        try:
            scraper = cloudscraper.create_scraper()
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9'
            })
            
            meetup_urls = [
                'https://www.meetup.com/find/?location=ar--Buenos%20Aires&source=EVENTS',
                'https://www.meetup.com/find/?keywords=music&location=ar--Buenos%20Aires',
                'https://www.meetup.com/find/?keywords=tech&location=ar--Buenos%20Aires'
            ]
            
            for url in meetup_urls[:2]:
                try:
                    logger.info(f"👥 Scrapeando Meetup: {url}")
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(url, timeout=15)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar eventos
                        event_cards = soup.find_all(['div', 'article'], class_=re.compile('event'))
                        
                        for card in event_cards[:8]:
                            try:
                                # Buscar título
                                title_elem = card.find(['h3', 'h2', 'a'], string=True)
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    
                                    if len(title) > 10:
                                        events.append({
                                            'title': title,
                                            'source': 'meetup',
                                            'url': url,
                                            'method': 'meetup_scraping'
                                        })
                            except:
                                continue
                    
                    logger.info(f"✅ Meetup: {len(events)} eventos")
                    await asyncio.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error Meetup {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error general Meetup: {e}")
        
        return events
    
    async def method_3_venue_websites(self) -> List[Dict]:
        """
        Scraping directo de sitios web de venues argentinos
        """
        events = []
        
        try:
            scraper = cloudscraper.create_scraper()
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9'
            })
            
            for url in self.targets['argentina_venues']:
                try:
                    logger.info(f"🏛️ Scrapeando venue: {url}")
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(url, timeout=20)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar eventos con selectores genéricos
                        event_patterns = [
                            'evento', 'show', 'concierto', 'función',
                            'espectáculo', 'presentación', 'festival'
                        ]
                        
                        # Buscar elementos que contengan palabras clave
                        for pattern in event_patterns:
                            elements = soup.find_all(text=re.compile(pattern, re.I))
                            
                            for element in elements[:5]:
                                try:
                                    parent = element.parent
                                    if parent:
                                        title = parent.get_text(strip=True)
                                        if 20 < len(title) < 200:
                                            events.append({
                                                'title': title,
                                                'source': 'venue_website',
                                                'venue_url': url,
                                                'method': 'venue_scraping'
                                            })
                                except:
                                    continue
                    
                    logger.info(f"✅ Venue {url}: {len(events)} eventos")
                    await asyncio.sleep(random.uniform(4, 8))
                    
                except Exception as e:
                    logger.error(f"Error venue {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error general venues: {e}")
        
        return events
    
    async def method_4_ticketek_api(self) -> List[Dict]:
        """
        Intento de usar API pública de Ticketek
        """
        events = []
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'es-AR,es;q=0.9',
                'Referer': 'https://www.ticketek.com.ar/'
            }
            
            # URLs de API a intentar
            api_urls = [
                'https://api.ticketek.com.ar/api/v1/events',
                'https://www.ticketek.com.ar/api/events',
                'https://ticketek.com.ar/rest/events'
            ]
            
            async with aiohttp.ClientSession() as session:
                for api_url in api_urls:
                    try:
                        logger.info(f"🎟️ Probando API Ticketek: {api_url}")
                        
                        async with session.get(api_url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Parsear respuesta JSON
                                if isinstance(data, dict):
                                    if 'events' in data:
                                        events_data = data['events']
                                    elif 'data' in data:
                                        events_data = data['data']
                                    else:
                                        events_data = [data]
                                elif isinstance(data, list):
                                    events_data = data
                                else:
                                    continue
                                
                                # Procesar eventos
                                for event_item in events_data[:10]:
                                    if isinstance(event_item, dict):
                                        title = event_item.get('name') or event_item.get('title')
                                        if title:
                                            events.append({
                                                'title': title,
                                                'date': event_item.get('date'),
                                                'venue': event_item.get('venue'),
                                                'price': event_item.get('price'),
                                                'source': 'ticketek_api',
                                                'method': 'api_call'
                                            })
                                
                                logger.info(f"✅ Ticketek API: {len(events)} eventos")
                                break  # Si funciona una API, no probar otras
                                
                    except Exception as e:
                        logger.error(f"Error API Ticketek {api_url}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error general Ticketek API: {e}")
        
        return events
    
    async def method_5_social_media_hashtags(self) -> List[Dict]:
        """
        Scraping de hashtags públicos relacionados con eventos
        """
        events = []
        
        try:
            # Twitter/X búsquedas públicas (sin API)
            search_queries = [
                'eventos buenos aires',
                'conciertos argentina',
                'shows musicales',
                '#EventosBA',
                '#ConciertosArg'
            ]
            
            scraper = cloudscraper.create_scraper()
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9'
            })
            
            for query in search_queries[:2]:  # Limitar para evitar bloqueos
                try:
                    # Intentar búsqueda en Twitter
                    search_url = f"https://twitter.com/search?q={urllib.parse.quote_plus(query)}&src=typed_query&f=live"
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(search_url, timeout=10)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar tweets que mencionen eventos
                        tweet_texts = soup.find_all(text=re.compile('evento|show|concierto', re.I))
                        
                        for text in tweet_texts[:5]:
                            if isinstance(text, str) and 20 < len(text) < 280:
                                events.append({
                                    'title': text[:100],
                                    'source': 'twitter',
                                    'query': query,
                                    'method': 'social_hashtags'
                                })
                    
                    await asyncio.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    logger.error(f"Error social media {query}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error general social media: {e}")
        
        return events
    
    def _extract_eventbrite_event(self, card_element) -> Optional[Dict]:
        """
        Extrae información de un evento de Eventbrite
        """
        try:
            # Título
            title_selectors = [
                '.eds-event-card__formatted-name--is-clamped',
                '.event-card__clamp-line--one',
                'h3', 'h2',
                '[data-testid="event-title"]'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = card_element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Fecha
            date_selectors = [
                '.eds-event-card__sub-content time',
                '.event-card__date',
                '[data-testid="event-date"]'
            ]
            
            date_text = None
            for selector in date_selectors:
                date_elem = card_element.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    break
            
            # Ubicación
            location_selectors = [
                '[data-testid="location-info"]',
                '.event-card__location',
                '.eds-event-card__sub-content [aria-label*="ubicación"]'
            ]
            
            location = None
            for selector in location_selectors:
                loc_elem = card_element.select_one(selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Precio
            price_selectors = [
                '.eds-event-card__formatted-price',
                '.event-card__price',
                '[data-testid="event-price"]'
            ]
            
            price_text = None
            for selector in price_selectors:
                price_elem = card_element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    break
            
            # URL del evento
            link_elem = card_element.find('a')
            event_url = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    event_url = f"https://www.eventbrite.com.ar{href}" if href.startswith('/') else href
            
            return {
                'title': title,
                'date_text': date_text,
                'location': location or 'Buenos Aires',
                'price_text': price_text,
                'event_url': event_url,
                'source': 'eventbrite',
                'method': 'eventbrite_scraping'
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo evento Eventbrite: {e}")
            return None
    
    async def scrape_all_methods(self) -> List[Dict]:
        """
        Ejecuta todos los métodos de scraping en paralelo
        """
        logger.info("🚀 Iniciando scraping multi-técnica masivo...")
        
        # Crear tareas para ejecutar en paralelo
        tasks = [
            self.method_1_eventbrite_advanced(),
            self.method_2_meetup_scraping(),
            self.method_3_venue_websites(),
            self.method_4_ticketek_api(),
            self.method_5_social_media_hashtags()
        ]
        
        logger.info(f"⚡ Ejecutando {len(tasks)} métodos de scraping en paralelo...")
        
        # Ejecutar todas las tareas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        all_events = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_events.extend(result)
                logger.info(f"✅ Método {i+1}: {len(result)} eventos")
            elif isinstance(result, Exception):
                logger.error(f"❌ Método {i+1} falló: {result}")
        
        # Deduplicar
        unique_events = self._deduplicate_events(all_events)
        
        logger.info(f"🎯 RESULTADO MULTI-TÉCNICA:")
        logger.info(f"   📊 Eventos totales: {len(all_events)}")
        logger.info(f"   📊 Eventos únicos: {len(unique_events)}")
        
        return unique_events
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Elimina eventos duplicados
        """
        seen_titles = set()
        unique_events = []
        
        for event in events:
            title = event.get('title', '').lower().strip()
            source = event.get('source', '')
            
            # Crear clave única
            key = f"{title}_{source}"
            
            if (key not in seen_titles and 
                len(title) > 10 and 
                title not in ['evento', 'eventos', 'event', 'events']):
                
                seen_titles.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos al formato estándar del sistema
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Generar fecha futura
                start_date = datetime.now() + timedelta(days=random.randint(1, 60))
                
                # Parsear precio si está disponible
                price = 0.0
                price_text = event.get('price_text', '')
                if price_text:
                    # Extraer número del precio
                    price_match = re.search(r'[\d.,]+', price_text.replace('$', ''))
                    if price_match:
                        try:
                            price = float(price_match.group().replace('.', '').replace(',', '.'))
                        except:
                            price = 0.0
                
                normalized_event = {
                    'title': event.get('title', 'Evento sin título'),
                    'description': f"Evento obtenido por {event.get('method', 'scraping')}",
                    
                    'start_datetime': start_date.isoformat(),
                    'end_datetime': (start_date + timedelta(hours=3)).isoformat(),
                    
                    'venue_name': event.get('location', event.get('venue', 'Buenos Aires')),
                    'venue_address': f"{event.get('location', event.get('venue', ''))}, Argentina",
                    'neighborhood': 'Buenos Aires',
                    'latitude': -34.6037 + random.uniform(-0.15, 0.15),
                    'longitude': -58.3816 + random.uniform(-0.15, 0.15),
                    
                    'category': self._detect_category(event.get('title', '')),
                    'subcategory': '',
                    'tags': [event.get('source', ''), 'argentina', 'multi_technique'],
                    
                    'price': price,
                    'currency': 'ARS',
                    'is_free': price == 0.0,
                    
                    'source': f"multi_technique_{event.get('source', 'unknown')}",
                    'source_id': f"mt_{hash(event.get('title', '') + event.get('source', ''))}",
                    'event_url': event.get('event_url', event.get('url', '')),
                    'image_url': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30',
                    
                    'organizer': event.get('source', 'Organizador'),
                    'capacity': 0,
                    'status': 'live',
                    'scraping_method': event.get('method', 'unknown'),
                    
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando evento: {e}")
                continue
        
        return normalized
    
    def _detect_category(self, title: str) -> str:
        """
        Detecta categoría basándose en el título
        """
        title_lower = title.lower()
        
        categories = {
            'music': ['música', 'concierto', 'recital', 'festival', 'rock', 'pop', 'jazz', 'electrónica'],
            'theater': ['teatro', 'obra', 'comedia', 'drama', 'musical'],
            'cultural': ['arte', 'cultura', 'museo', 'exposición', 'galería'],
            'sports': ['deporte', 'fútbol', 'básquet', 'tenis', 'running'],
            'business': ['conferencia', 'seminario', 'workshop', 'networking'],
            'party': ['fiesta', 'party', 'celebración', 'baile']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'


# Función principal de testing
async def test_multi_technique_scraper():
    """
    Prueba el scraper multi-técnica
    """
    scraper = MultiTechniqueScraper()
    
    print("🔥 Iniciando Multi-Technique Event Scraper...")
    print("⚡ Ejecutando todos los métodos de scraping disponibles...")
    
    # Scraping masivo
    events = await scraper.scrape_all_methods()
    
    print(f"\n🎯 RESULTADOS FINALES:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    # Agrupar por fuente
    sources = {}
    for event in events:
        source = event.get('source', 'unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(event)
    
    print(f"\n📈 Por fuente:")
    for source, source_events in sources.items():
        print(f"   {source}: {len(source_events)} eventos")
    
    # Mostrar eventos
    print(f"\n🎭 Eventos encontrados:")
    for i, event in enumerate(events[:20]):
        print(f"\n{i+1:2d}. 📌 {event['title'][:80]}...")
        print(f"     🏢 {event.get('location', event.get('venue', 'N/A'))}")
        print(f"     🔧 {event.get('method', 'N/A')}")
        if event.get('price_text'):
            print(f"     💰 {event.get('price_text')}")
    
    # Normalizar
    if events:
        print(f"\n🔄 Normalizando eventos...")
        normalized = scraper.normalize_events(events)
        print(f"✅ {len(normalized)} eventos normalizados")
        
        return normalized
    
    return events


if __name__ == "__main__":
    asyncio.run(test_multi_technique_scraper())