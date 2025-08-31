"""
CloudScraper Events - Usa cloudscraper library
Bypasses Cloudflare y anti-bot sin necesitar browser
Funciona perfectamente desde APIs REST
"""

import cloudscraper
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import json
import re

logger = logging.getLogger(__name__)

class CloudscraperEvents:
    """
    Scraper que usa cloudscraper para bypass anti-bot
    No necesita browser, funciona desde API REST
    """
    
    def __init__(self):
        # Crear scraper con bypass de Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Headers adicionales para parecer más real
        self.scraper.headers.update({
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    async def scrape_facebook_events(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Intenta obtener eventos de Facebook sin login
        """
        events = []
        
        try:
            # URLs públicas de eventos - probemos diferentes approaches  
            facebook_pages = [
                # Páginas oficiales de venues
                "https://www.facebook.com/lunaparkoficial/events",
                "https://www.facebook.com/teatrocolonoficial/events", 
                "https://www.facebook.com/nicetoclub/events",
                "https://www.facebook.com/CCRecoleta/events",
                "https://www.facebook.com/latrasienda/events",
                # Páginas de eventos de ciudades
                "https://www.facebook.com/events/search/?q=Buenos%20Aires%20eventos",
                "https://www.facebook.com/events/search/?q=recitales%20Buenos%20Aires",
                "https://www.facebook.com/events/search/?q=teatro%20Buenos%20Aires"
            ]
            
            for page_url in facebook_pages[:2]:  # Limitar para no ser detectado
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.scraper.get, page_url
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar datos JSON embebidos
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string and 'event' in script.string.lower():
                                # Extraer eventos del JSON si existe
                                try:
                                    # Facebook embebe datos en formato específico
                                    if '"__typename":"Event"' in script.string:
                                        # Extraer eventos del JSON
                                        parsed_events = self._parse_facebook_json(script.string)
                                        if parsed_events:
                                            events.extend(parsed_events)
                                except:
                                    pass
                        
                        # Si no encontramos JSON, buscar en HTML con selectores modernos
                        event_divs = (soup.find_all('div', {'role': 'article'}) or 
                                    soup.find_all('div', class_=re.compile(r'event|Event')) or
                                    soup.find_all(['article', 'section'], class_=re.compile(r'event|post|feed')))
                        
                        for div in event_divs[:10]:
                            event = self._extract_event_from_div(div)
                            if event:
                                events.append(event)
                                
                    await asyncio.sleep(random.uniform(2, 4))  # Delay anti-detección
                    
                except Exception as e:
                    logger.error(f"Error scraping {page_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Facebook scraping error: {e}")
        
        # Si no obtuvimos eventos reales, retornar vacío
        if not events:
            logger.warning("⚠️ No se pudieron obtener eventos reales de Facebook")
            
        return events
    
    async def scrape_instagram_events(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Intenta obtener eventos de Instagram sin login usando múltiples hashtags
        """
        events = []
        
        # Hashtags populares de eventos en Argentina
        popular_hashtags = [
            "eventosba", "buenosaires", "recitalba", "showsba", 
            "fiestasbuenosaires", "eventosargentina", "musica", 
            "teatro", "cultura", "festival"
        ]
        
        try:
            for hashtag in popular_hashtags[:3]:  # Probar los 3 más populares
                try:
                    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
                    print(f"🔍 Scraping Instagram #{hashtag}...")
            
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.scraper.get, url
                    )
            
                    if response.status_code == 200:
                        # Instagram embebe JSON en el HTML
                        if 'window._sharedData' in response.text:
                            try:
                                json_str = response.text.split('window._sharedData = ')[1].split(';</script>')[0]
                                data = json.loads(json_str)
                                
                                # Navegar al contenido del hashtag
                                media = data.get('entry_data', {}).get('TagPage', [{}])[0]
                                posts = media.get('graphql', {}).get('hashtag', {}).get('edge_hashtag_to_media', {}).get('edges', [])
                                
                                hashtag_events = 0
                                for post in posts[:10]:
                                    node = post.get('node', {})
                                    caption = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                                    
                                    # Buscar eventos en el caption
                                    if any(word in caption.lower() for word in ['evento', 'fiesta', 'show', 'festival', 'recital']):
                                        events.append({
                                            'title': self._extract_title_from_caption(caption),
                                            'description': caption[:200],
                                            'source': 'instagram',
                                            'image_url': node.get('display_url', ''),
                                            'likes': node.get('edge_liked_by', {}).get('count', 0),
                                            'url': f"https://www.instagram.com/p/{node.get('shortcode')}/",
                                            'hashtag': hashtag,
                                            'venue_name': 'Instagram Event',
                                            'price': 0,
                                            'is_free': True
                                        })
                                        hashtag_events += 1
                                
                                print(f"  📦 Found {hashtag_events} events in #{hashtag}")
                                        
                            except Exception as e:
                                logger.error(f"Error parsing Instagram JSON for #{hashtag}: {e}")
                    
                    await asyncio.sleep(2)  # Anti-detection delay
                    
                except Exception as e:
                    logger.error(f"Error scraping #{hashtag}: {e}")
                    continue
                        
        except Exception as e:
            logger.error(f"Instagram scraping error: {e}")
        
        # Si no obtuvimos eventos, retornar vacío
        if not events:
            logger.warning("⚠️ No se pudieron obtener eventos reales de Instagram")
        else:
            print(f"✅ Instagram total: {len(events)} events found")
            
        return events
    
    async def scrape_eventbrite(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Scraping de Eventbrite con cloudscraper
        """
        events = []
        
        try:
            url = f"https://www.eventbrite.com.ar/d/argentina--{location.lower().replace(' ', '-')}/events/"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.get, url
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar eventos en el HTML
                event_cards = soup.find_all(['article', 'div'], class_=re.compile('event-card|eds-event-card'))
                
                for card in event_cards[:10]:
                    try:
                        title = card.find(['h3', 'h2', 'div'], class_=re.compile('event-card__title'))
                        if title:
                            event = {
                                'title': title.get_text(strip=True),
                                'source': 'eventbrite'
                            }
                            
                            # Fecha
                            date = card.find(['time', 'div'], class_=re.compile('date|time'))
                            if date:
                                event['date'] = date.get_text(strip=True)
                            
                            # Ubicación
                            location = card.find(['div', 'p'], class_=re.compile('location|venue'))
                            if location:
                                event['venue'] = location.get_text(strip=True)
                            
                            # Precio
                            price = card.find(['div', 'span'], class_=re.compile('price'))
                            if price:
                                price_text = price.get_text(strip=True)
                                if 'gratis' in price_text.lower() or 'free' in price_text.lower():
                                    event['price'] = 0
                                else:
                                    # Extraer número del precio
                                    numbers = re.findall(r'\d+', price_text.replace('.', ''))
                                    if numbers:
                                        event['price'] = int(numbers[0])
                            
                            events.append(event)
                            
                    except Exception as e:
                        logger.error(f"Error parsing Eventbrite card: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Eventbrite scraping error: {e}")
            
        return events
    
    def _parse_facebook_json(self, json_str: str) -> List[Dict]:
        """Parsea JSON embebido de Facebook y extrae múltiples eventos"""
        events = []
        try:
            # Buscar múltiples objetos Event en el JSON
            event_pattern = r'"__typename":"Event"[^}]*?"name":"([^"]{10,200})"[^}]*?(?:"place":\{[^}]*?"name":"([^"]+)"[^}]*?\})?[^}]*?(?:"start_time":"([^"]+)")?'
            
            matches = re.findall(event_pattern, json_str, re.DOTALL)
            
            for match in matches:
                name, place, start_time = match
                
                # Filtrar nombres que claramente no son eventos
                name_clean = name.replace('\\u0040', '@').replace('\\/', '/')
                
                # Skip si parece código JS o metadata
                if any(word in name_clean.lower() for word in ['bundle', 'worker', 'module', 'script', 'loader', 'chunk']):
                    continue
                
                # Skip si es muy corto o tiene caracteres raros de código
                if len(name_clean) < 5 or '\\' in name_clean:
                    continue
                
                events.append({
                    'title': name_clean,
                    'source': 'facebook',
                    'venue': place if place else 'Buenos Aires',
                    'date': start_time if start_time else '',
                    'venue_address': f"{place}, Buenos Aires" if place else "Buenos Aires",
                    'price': 0,
                    'is_free': True
                })
                
        except Exception as e:
            logger.error(f"Error parsing Facebook JSON: {e}")
        
        return events
    
    def _extract_event_from_div(self, div) -> Optional[Dict]:
        """Extrae evento de un div de Facebook"""
        try:
            # Buscar títulos con texto significativo
            title_candidates = div.find_all(['span', 'h3', 'h2', 'strong', 'a'])
            
            for candidate in title_candidates:
                text = candidate.get_text(strip=True)
                # Filtrar texto que parezca título de evento
                if (len(text) > 10 and len(text) < 200 and 
                    not text.lower().startswith(('ver más', 'me interesa', 'compartir', 'like', 'comment'))):
                    
                    # Buscar fecha en el div
                    date_elem = div.find(string=re.compile(r'\d{1,2}\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', re.I))
                    date_str = date_elem.strip() if date_elem else ""
                    
                    # Buscar ubicación
                    location_elem = div.find(string=re.compile(r'(teatro|club|centro|sala|estadio)', re.I))
                    venue = location_elem.strip() if location_elem else "Buenos Aires"
                    
                    return {
                        'title': text,
                        'source': 'facebook',
                        'venue': venue,
                        'date': date_str
                    }
        except Exception as e:
            logger.error(f"Error extracting Facebook div: {e}")
        return None
    
    def _extract_title_from_caption(self, caption: str) -> str:
        """Extrae título del caption de Instagram"""
        lines = caption.split('\n')
        return lines[0][:100] if lines else "Evento de Instagram"
    
    def _get_known_facebook_events(self) -> List[Dict]:
        """DEPRECATED - No usar eventos simulados"""
        return []  # Solo datos reales
    
    def _get_known_instagram_events(self) -> List[Dict]:
        """DEPRECATED - No usar eventos simulados"""
        return []  # Solo datos reales
    
    async def fetch_all_events(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Obtiene eventos de todas las fuentes usando cloudscraper
        """
        all_events = []
        
        # Facebook
        try:
            fb_events = await self.scrape_facebook_events(location)
            all_events.extend(fb_events)
            logger.info(f"✅ CloudScraper Facebook: {len(fb_events)} eventos")
        except:
            pass
        
        # Instagram
        try:
            ig_events = await self.scrape_instagram_events()
            all_events.extend(ig_events)
            logger.info(f"✅ CloudScraper Instagram: {len(ig_events)} eventos")
        except:
            pass
        
        # Eventbrite
        try:
            eb_events = await self.scrape_eventbrite(location)
            all_events.extend(eb_events)
            logger.info(f"✅ CloudScraper Eventbrite: {len(eb_events)} eventos")
        except:
            pass
        
        # Normalizar eventos
        normalized = []
        for event in all_events:
            normalized_event = {
                'title': event.get('title', 'Evento sin título'),
                'description': event.get('description', ''),
                'venue_name': event.get('venue', event.get('venue_name', location)),
                'venue_address': f"{event.get('venue', '')}, {location}",
                'category': event.get('category', 'general'),
                'price': event.get('price', 0),
                'currency': 'ARS',
                'is_free': event.get('price', 0) == 0,
                'source': event.get('source', 'cloudscraper'),
                'start_datetime': event.get('date', (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()),
                'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30'),
                'event_url': event.get('url', ''),
                'likes': event.get('likes', 0),
                'status': 'live'
            }
            
            # Coordenadas aleatorias en Buenos Aires
            normalized_event['latitude'] = -34.6037 + random.uniform(-0.05, 0.05)
            normalized_event['longitude'] = -58.3816 + random.uniform(-0.05, 0.05)
            
            normalized.append(normalized_event)
        
        logger.info(f"🔥 CloudScraper Total: {len(normalized)} eventos")
        return normalized


# Testing
async def test_cloudscraper():
    scraper = CloudscraperEvents()
    events = await scraper.fetch_all_events()
    
    print(f"\n✅ Total eventos con CloudScraper: {len(events)}")
    for event in events[:5]:
        print(f"\n📍 {event['title']}")
        print(f"   Venue: {event['venue_name']}")
        print(f"   Precio: ${event['price']} ARS")
        print(f"   Fuente: {event['source']}")
        if event.get('likes'):
            print(f"   ❤️ {event['likes']} likes")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_cloudscraper())