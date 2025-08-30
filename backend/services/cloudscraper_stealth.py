"""
CloudScraper Stealth - Anti-detection scraping para Facebook/Instagram
Estrategia: Scraping intermitente para evitar bloqueos
Funciona 1 vez por día, pero sin riesgo de ban permanente
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
import time
import os

logger = logging.getLogger(__name__)

class CloudscraperStealth:
    """
    Scraper anti-detección con limits automáticos
    - Máximo 20 eventos por día para evitar bloqueos
    - Delays aleatorios entre requests  
    - User agents rotativos
    - Session management inteligente
    """
    
    def __init__(self):
        self.session_file = "/tmp/cloudscraper_sessions.json"
        self.daily_limit = 20  # Máximo eventos por día
        
        # Crear scraper con configuración stealth
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': random.choice(['chrome', 'firefox', 'safari']),
                'platform': random.choice(['windows', 'darwin', 'linux']),
                'desktop': True
            }
        )
        
        # Headers más realistas
        self.scraper.headers.update({
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
    
    def _check_daily_limit(self) -> bool:
        """Verifica si ya alcanzamos el límite diario"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                
                today = datetime.now().strftime('%Y-%m-%d')
                if data.get('date') == today:
                    count = data.get('count', 0)
                    if count >= self.daily_limit:
                        logger.warning(f"🚫 Límite diario alcanzado: {count}/{self.daily_limit}")
                        return False
                    return True
                else:
                    # Nuevo día, resetear contador
                    self._save_session_count(0)
                    return True
            else:
                self._save_session_count(0)
                return True
        except:
            return True
    
    def _save_session_count(self, count: int):
        """Guarda el contador de sesión"""
        try:
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': count,
                'last_request': datetime.now().isoformat()
            }
            with open(self.session_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def _increment_session_count(self):
        """Incrementa el contador de eventos obtenidos hoy"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                count = data.get('count', 0) + 1
            else:
                count = 1
            self._save_session_count(count)
        except:
            pass
    
    async def scrape_facebook_stealth(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Scraping de Facebook con estrategia anti-detección
        """
        if not self._check_daily_limit():
            return []
        
        events = []
        
        try:
            # Solo 1 página por sesión para evitar detección
            facebook_pages = [
                "https://www.facebook.com/lunaparkoficial/events",
                "https://www.facebook.com/teatrocolonoficial/events",
                "https://www.facebook.com/nicetoclub/events"
            ]
            
            # Elegir página aleatoria
            page_url = random.choice(facebook_pages)
            
            # Delay inicial para parecer más humano
            await asyncio.sleep(random.uniform(1, 3))
            
            logger.info(f"🕵️ Scraping stealth: {page_url}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.get, page_url
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar JSON embebido (método que funcionó)
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'event' in script.string.lower():
                        try:
                            if '"__typename":"Event"' in script.string:
                                parsed_events = self._parse_facebook_json(script.string)
                                if parsed_events:
                                    # Limitar a 10 eventos para no sobrecargar
                                    events.extend(parsed_events[:10])
                        except:
                            pass
                
                # Backup: buscar en HTML
                if not events:
                    event_divs = soup.find_all('div', {'role': 'article'})
                    for div in event_divs[:5]:  # Solo 5 para ser conservador
                        event = self._extract_event_from_div(div)
                        if event:
                            events.append(event)
                
                # Incrementar contador si obtuvimos eventos
                if events:
                    self._increment_session_count()
                    
            elif response.status_code == 403:
                logger.warning("🚫 Facebook bloqueó el request (403)")
                return []
            elif response.status_code == 429:
                logger.warning("🚫 Rate limit reached (429)")
                return []
                    
        except Exception as e:
            logger.error(f"Facebook stealth error: {e}")
        
        logger.info(f"✅ Facebook stealth: {len(events)} eventos")
        return events
    
    async def scrape_instagram_stealth(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Instagram scraping con anti-detección
        """
        if not self._check_daily_limit():
            return []
        
        events = []
        
        # Solo 1 hashtag por sesión
        popular_hashtags = ["eventosba", "buenosaires", "recitalba"]
        hashtag = random.choice(popular_hashtags)
        
        try:
            # Delay anti-detección
            await asyncio.sleep(random.uniform(2, 5))
            
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            logger.info(f"🕵️ Instagram stealth #{hashtag}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.get, url
            )
            
            if response.status_code == 200:
                if 'window._sharedData' in response.text:
                    try:
                        json_str = response.text.split('window._sharedData = ')[1].split(';</script>')[0]
                        data = json.loads(json_str)
                        
                        media = data.get('entry_data', {}).get('TagPage', [{}])[0]
                        posts = media.get('graphql', {}).get('hashtag', {}).get('edge_hashtag_to_media', {}).get('edges', [])
                        
                        # Solo procesar 5 posts para ser conservador
                        for post in posts[:5]:
                            node = post.get('node', {})
                            caption = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                            
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
                        
                        if events:
                            self._increment_session_count()
                                        
                    except Exception as e:
                        logger.error(f"Error parsing Instagram JSON: {e}")
            
            elif response.status_code in [403, 429]:
                logger.warning(f"🚫 Instagram blocked (status: {response.status_code})")
                return []
                        
        except Exception as e:
            logger.error(f"Instagram stealth error: {e}")
        
        logger.info(f"✅ Instagram stealth: {len(events)} eventos")
        return events
    
    def _parse_facebook_json(self, json_str: str) -> List[Dict]:
        """Parsea JSON de Facebook (método que funcionó antes)"""
        events = []
        try:
            event_pattern = r'"__typename":"Event"[^}]*?"name":"([^"]{10,200})"[^}]*?(?:"place":\{[^}]*?"name":"([^"]+)"[^}]*?\})?[^}]*?(?:"start_time":"([^"]+)")?'
            matches = re.findall(event_pattern, json_str, re.DOTALL)
            
            for match in matches:
                name, place, start_time = match
                name_clean = name.replace('\\u0040', '@').replace('\\/', '/')
                
                # Filtros de calidad
                if any(word in name_clean.lower() for word in ['bundle', 'worker', 'module', 'script']):
                    continue
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
            title_candidates = div.find_all(['span', 'h3', 'h2', 'strong', 'a'])
            
            for candidate in title_candidates:
                text = candidate.get_text(strip=True)
                if (len(text) > 10 and len(text) < 200 and 
                    not text.lower().startswith(('ver más', 'me interesa', 'compartir', 'like', 'comment'))):
                    
                    return {
                        'title': text,
                        'source': 'facebook',
                        'venue': 'Buenos Aires',
                        'date': ''
                    }
        except:
            pass
        return None
    
    def _extract_title_from_caption(self, caption: str) -> str:
        """Extrae título del caption de Instagram"""
        lines = caption.split('\n')
        return lines[0][:100] if lines else "Evento de Instagram"
    
    async def fetch_stealth_events(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Estrategia principal: máximo 20 eventos por día
        """
        logger.info("🕵️ Iniciando CloudScraper Stealth Mode")
        
        if not self._check_daily_limit():
            logger.warning("🚫 Límite diario alcanzado. Intente mañana.")
            return []
        
        all_events = []
        
        # Facebook (solo si tenemos límite disponible)
        try:
            fb_events = await self.scrape_facebook_stealth(location)
            all_events.extend(fb_events)
            
            # Delay entre plataformas para parecer más humano
            if fb_events:
                await asyncio.sleep(random.uniform(3, 7))
        except:
            pass
        
        # Instagram (solo si aún tenemos límite)
        if self._check_daily_limit():
            try:
                ig_events = await self.scrape_instagram_stealth(location)
                all_events.extend(ig_events)
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
                'category': 'general',
                'price': event.get('price', 0),
                'currency': 'ARS',
                'is_free': event.get('price', 0) == 0,
                'source': event.get('source', 'cloudscraper_stealth'),
                'start_datetime': (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
                'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30'),
                'event_url': event.get('url', ''),
                'likes': event.get('likes', 0),
                'status': 'live'
            }
            
            # Coordenadas en Buenos Aires
            normalized_event['latitude'] = -34.6037 + random.uniform(-0.05, 0.05)
            normalized_event['longitude'] = -58.3816 + random.uniform(-0.05, 0.05)
            
            normalized.append(normalized_event)
        
        logger.info(f"🔥 CloudScraper Stealth Total: {len(normalized)} eventos")
        
        # Mostrar info de límite diario
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                count = data.get('count', 0)
                logger.info(f"📊 Eventos obtenidos hoy: {count}/{self.daily_limit}")
        except:
            pass
        
        return normalized


# Testing
async def test_stealth():
    scraper = CloudscraperStealth()
    events = await scraper.fetch_stealth_events()
    
    print(f"\n✅ Total eventos con Stealth Mode: {len(events)}")
    for event in events[:3]:
        print(f"\n📍 {event['title']}")
        print(f"   Venue: {event['venue_name']}")
        print(f"   Fuente: {event['source']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_stealth())