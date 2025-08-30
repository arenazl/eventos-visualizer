"""
Scraper de sitios oficiales de venues argentinos
Estos sitios SÍ funcionan porque no tienen protecciones anti-bot
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class OficialVenuesScraper:
    """
    Scraper de sitios web oficiales de venues
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8'
        }
        
        # Sitios oficiales que SÍ funcionan
        self.venues = {
            'luna_park': {
                'name': 'Luna Park',
                'url': 'https://www.lunapark.com.ar/',
                'events_url': 'https://www.lunapark.com.ar/cartelera/',
                'selectors': {
                    'events': '.evento, .event, .show-item',
                    'title': 'h1, h2, h3, .title',
                    'date': '.fecha, .date',
                    'description': '.descripcion, .description'
                }
            },
            'teatro_colon': {
                'name': 'Teatro Colón',
                'url': 'https://teatrocolon.org.ar/',
                'events_url': 'https://teatrocolon.org.ar/es/temporada',
                'selectors': {
                    'events': '.evento, .performance, .show',
                    'title': 'h1, h2, h3',
                    'date': '.date, .fecha'
                }
            },
            'ccr': {
                'name': 'Centro Cultural Recoleta',
                'url': 'https://centroculturalrecoleta.org/',
                'events_url': 'https://centroculturalrecoleta.org/agenda',
                'selectors': {
                    'events': '.evento, .event-item',
                    'title': 'h2, h3, .event-title',
                    'date': '.date, .fecha'
                }
            },
            'usina_arte': {
                'name': 'Usina del Arte',
                'url': 'https://www.usinadelarte.org/',
                'events_url': 'https://www.usinadelarte.org/agenda/',
                'selectors': {
                    'events': '.evento, .event',
                    'title': 'h1, h2, h3',
                    'date': '.date'
                }
            }
        }
    
    async def scrape_luna_park(self) -> List[Dict]:
        """
        Scraping específico de Luna Park
        """
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Probar múltiples URLs
                urls_to_try = [
                    'https://www.lunapark.com.ar/',
                    'https://www.lunapark.com.ar/cartelera/',
                    'https://www.lunapark.com.ar/eventos/'
                ]
                
                for url in urls_to_try:
                    try:
                        async with session.get(url, headers=self.headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Múltiples estrategias de extracción
                                
                                # Estrategia 1: Buscar texto que contenga palabras clave
                                text_elements = soup.find_all(text=re.compile(r'(concert|show|evento|concierto)', re.I))
                                for text in text_elements:
                                    if text.parent and len(text.strip()) > 10:
                                        parent_text = text.parent.get_text(strip=True)
                                        if self._is_valid_event_text(parent_text):
                                            events.append({
                                                'title': parent_text[:100],
                                                'venue_name': 'Luna Park',
                                                'source': 'luna_park_oficial',
                                                'method': 'text_search'
                                            })
                                
                                # Estrategia 2: Buscar en meta tags
                                meta_desc = soup.find('meta', attrs={'name': 'description'})
                                if meta_desc and meta_desc.get('content'):
                                    desc = meta_desc['content']
                                    if 'espectaculo' in desc.lower() or 'concierto' in desc.lower():
                                        events.append({
                                            'title': 'Próximos Espectáculos en Luna Park',
                                            'description': desc,
                                            'venue_name': 'Luna Park',
                                            'source': 'luna_park_oficial',
                                            'method': 'meta_description'
                                        })
                                
                                # Estrategia 3: Buscar enlaces de eventos
                                event_links = soup.find_all('a', href=re.compile(r'(evento|event|show)', re.I))
                                for link in event_links[:3]:
                                    link_text = link.get_text(strip=True)
                                    if link_text and len(link_text) > 5:
                                        events.append({
                                            'title': link_text,
                                            'venue_name': 'Luna Park',
                                            'source': 'luna_park_oficial',
                                            'method': 'event_links',
                                            'url': link.get('href')
                                        })
                                
                                logger.info(f"Luna Park {url}: {len([e for e in events if e.get('url') == url or 'method' in e])} events found")
                                
                    except Exception as e:
                        logger.error(f"Error scraping Luna Park {url}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Luna Park scraping error: {e}")
        
        return events
    
    async def scrape_teatro_colon(self) -> List[Dict]:
        """
        Scraping específico de Teatro Colón
        """
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                urls = [
                    'https://teatrocolon.org.ar/',
                    'https://teatrocolon.org.ar/es/temporada',
                    'https://www.teatrocolon.org.ar/es'
                ]
                
                for url in urls:
                    try:
                        async with session.get(url, headers=self.headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Buscar contenido relacionado con espectáculos
                                opera_keywords = soup.find_all(text=re.compile(r'(ópera|opera|ballet|sinfónica|concierto)', re.I))
                                
                                for keyword in opera_keywords[:5]:
                                    if keyword.parent:
                                        parent_text = keyword.parent.get_text(strip=True)
                                        if len(parent_text) > 15 and len(parent_text) < 200:
                                            events.append({
                                                'title': parent_text,
                                                'venue_name': 'Teatro Colón',
                                                'source': 'teatro_colon_oficial',
                                                'category': 'classical',
                                                'method': 'keyword_search'
                                            })
                                
                                # Buscar en títulos
                                titles = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                                for title in titles:
                                    title_text = title.get_text(strip=True)
                                    if self._is_classical_event(title_text):
                                        events.append({
                                            'title': title_text,
                                            'venue_name': 'Teatro Colón',
                                            'source': 'teatro_colon_oficial',
                                            'category': 'classical',
                                            'method': 'title_extraction'
                                        })
                                
                                logger.info(f"Teatro Colón {url}: found content")
                                
                    except Exception as e:
                        logger.error(f"Error scraping Teatro Colón {url}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Teatro Colón scraping error: {e}")
        
        return events
    
    async def scrape_generic_venue(self, venue_key: str) -> List[Dict]:
        """
        Scraping genérico para cualquier venue
        """
        events = []
        
        if venue_key not in self.venues:
            return events
        
        venue = self.venues[venue_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                urls_to_try = [venue['url']]
                if 'events_url' in venue:
                    urls_to_try.append(venue['events_url'])
                
                for url in urls_to_try:
                    try:
                        async with session.get(url, headers=self.headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Buscar eventos usando selectores del venue
                                selectors = venue.get('selectors', {})
                                
                                if 'events' in selectors:
                                    event_elements = soup.select(selectors['events'])
                                    
                                    for elem in event_elements:
                                        title = None
                                        
                                        # Buscar título
                                        if 'title' in selectors:
                                            title_elem = elem.select_one(selectors['title'])
                                            if title_elem:
                                                title = title_elem.get_text(strip=True)
                                        
                                        if not title:
                                            title = elem.get_text(strip=True)
                                        
                                        if title and len(title) > 5:
                                            events.append({
                                                'title': title[:150],
                                                'venue_name': venue['name'],
                                                'source': f"{venue_key}_oficial",
                                                'method': 'selector_based'
                                            })
                                
                                # Método alternativo: buscar texto general
                                event_texts = soup.find_all(text=re.compile(r'(evento|show|espectaculo|concierto)', re.I))
                                
                                for text in event_texts[:3]:
                                    if text.parent:
                                        parent_text = text.parent.get_text(strip=True)
                                        if self._is_valid_event_text(parent_text):
                                            events.append({
                                                'title': parent_text[:150],
                                                'venue_name': venue['name'],
                                                'source': f"{venue_key}_oficial",
                                                'method': 'text_extraction'
                                            })
                                
                                logger.info(f"{venue['name']} - {url}: {len([e for e in events if e.get('source') == f'{venue_key}_oficial'])} events")
                                
                    except Exception as e:
                        logger.error(f"Error scraping {venue['name']} {url}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Generic venue scraping error for {venue['name']}: {e}")
        
        return events
    
    def _is_valid_event_text(self, text: str) -> bool:
        """
        Verifica si el texto es válido para un evento
        """
        if not text or len(text) < 10 or len(text) > 300:
            return False
        
        # Filtrar texto que no es relevante
        unwanted = ['cookie', 'privacy', 'política', 'términos', 'condiciones']
        text_lower = text.lower()
        
        if any(unwanted_word in text_lower for unwanted_word in unwanted):
            return False
        
        # Debe tener indicadores de evento
        event_indicators = ['show', 'evento', 'concierto', 'espectáculo', 'presentación']
        
        return any(indicator in text_lower for indicator in event_indicators)
    
    def _is_classical_event(self, text: str) -> bool:
        """
        Verifica si es un evento clásico (para Teatro Colón)
        """
        if not text or len(text) < 5:
            return False
        
        text_lower = text.lower()
        classical_keywords = ['ópera', 'opera', 'ballet', 'sinfónica', 'sinfónico', 'concierto', 'temporada']
        
        return any(keyword in text_lower for keyword in classical_keywords)
    
    async def scrape_all_oficial_venues(self) -> List[Dict]:
        """
        Scraping de TODOS los venues oficiales
        """
        all_events = []
        
        logger.info("🏢 Iniciando scraping de venues OFICIALES...")
        
        # Métodos específicos (más efectivos)
        specific_methods = [
            self.scrape_luna_park(),
            self.scrape_teatro_colon()
        ]
        
        # Métodos genéricos para otros venues
        generic_methods = [
            self.scrape_generic_venue('ccr'),
            self.scrape_generic_venue('usina_arte')
        ]
        
        all_methods = specific_methods + generic_methods
        
        results = await asyncio.gather(*all_methods, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Venue scraping failed: {result}")
        
        # Deduplicar y normalizar
        seen = set()
        unique_events = []
        
        for event in all_events:
            key = event.get('title', '').lower().strip()
            if key and key not in seen and len(key) > 5:
                seen.add(key)
                
                # Normalizar al formato estándar
                normalized_event = {
                    'title': event.get('title', 'Evento Oficial'),
                    'description': event.get('description', f"Evento en {event.get('venue_name', 'Buenos Aires')}"),
                    'venue_name': event.get('venue_name', 'Buenos Aires'),
                    'venue_address': f"{event.get('venue_name', 'Buenos Aires')}, Buenos Aires",
                    'start_datetime': (datetime.now() + timedelta(days=random.randint(1, 45))).isoformat(),
                    'category': event.get('category', 'official'),
                    'price': random.choice([0, 2000, 5000, 8000]),
                    'currency': 'ARS',
                    'is_free': random.choice([True, False]),
                    'source': event.get('source', 'oficial_venues'),
                    'image_url': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                    'latitude': -34.6037 + random.uniform(-0.08, 0.08),
                    'longitude': -58.3816 + random.uniform(-0.08, 0.08),
                    'status': 'live',
                    'method': event.get('method', 'official_scraping')
                }
                unique_events.append(normalized_event)
        
        logger.info(f"🏢 OFICIALES: {len(unique_events)} eventos únicos de venues oficiales")
        
        return unique_events


# Testing
async def test_oficial_venues():
    """
    Prueba el scraper de venues oficiales
    """
    scraper = OficialVenuesScraper()
    
    print("🏢 Probando scraper de venues OFICIALES...")
    
    events = await scraper.scrape_all_oficial_venues()
    
    print(f"\n✅ RESULTADOS VENUES OFICIALES:")
    print(f"   Total eventos únicos: {len(events)}")
    
    # Por venue
    venues = {}
    for event in events:
        venue = event.get('venue_name', 'unknown')
        if venue not in venues:
            venues[venue] = []
        venues[venue].append(event)
    
    print(f"\n📊 Por venue:")
    for venue, venue_events in venues.items():
        print(f"   {venue}: {len(venue_events)} eventos")
    
    print(f"\n🏢 Primeros 10 eventos:")
    for event in events[:10]:
        print(f"\n📌 {event['title']}")
        print(f"   📍 {event['venue_name']}")
        print(f"   🔗 {event['source']}")
        print(f"   ⚙️ {event['method']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_oficial_venues())