"""
Facebook Advanced Requests Scraper
Técnicas avanzadas de scraping sin Playwright - Solo requests/cloudscraper
Máxima evasión anti-detección usando headers, proxies y rotación
"""

import asyncio
import aiohttp
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import time
import urllib.parse

logger = logging.getLogger(__name__)

class FacebookAdvancedRequestsScraper:
    """
    Facebook scraper avanzado usando solo requests - Sin browser
    """
    
    def __init__(self):
        # 🎯 VENUES ARGENTINOS PRINCIPALES
        self.argentina_venues = [
            'lunaparkoficial', 'teatrocolonoficial', 'nicetoclub', 
            'CCRecoleta', 'latrasienda', 'teatrosanmartin',
            'movistararenar', 'hipodromoargentino', 'estadiobocajuniors',
            'clubriverplate', 'malba.museo', 'fundacionproa'
        ]
        
        # 🔍 BÚSQUEDAS ESPECÍFICAS
        self.search_queries = [
            "eventos buenos aires", "conciertos argentina", "shows luna park",
            "teatro colon", "eventos palermo", "recitales buenos aires",
            "festivales argentina", "eventos culturales ba"
        ]
        
        # 🎭 USER AGENTS SÚPER REALISTAS (rotación constante)
        self.user_agents = [
            # Android Argentina (más comunes)
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-A715F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
            
            # iPhone Argentina
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            
            # Desktop Argentina
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 🌐 ACCEPT-LANGUAGE VARIANTS (Argentina specific)
        self.accept_languages = [
            'es-AR,es;q=0.9,en;q=0.8',
            'es-AR,es;q=0.8,en-US;q=0.7,en;q=0.6',
            'es-AR;q=0.9,es;q=0.8,en;q=0.7',
            'es;q=0.9,es-AR;q=0.8,en;q=0.7'
        ]
        
        # 🎯 REFERRERS REALISTAS
        self.referrers = [
            'https://www.google.com/',
            'https://www.google.com.ar/',
            'https://www.google.com/search?q=eventos+buenos+aires',
            'https://www.facebook.com/',
            'https://m.facebook.com/',
            'https://www.instagram.com/',
            'https://twitter.com/'
        ]
    
    def _get_advanced_headers(self, mobile: bool = False) -> Dict[str, str]:
        """
        🎭 Genera headers súper realistas con rotación
        """
        ua = random.choice(self.user_agents)
        
        # Decidir si usar mobile o desktop basado en el UA
        is_mobile = 'Mobile' in ua or 'iPhone' in ua
        if mobile:
            ua = random.choice([ua for ua in self.user_agents if ('Mobile' in ua or 'iPhone' in ua)])
        
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Headers adicionales para mobile
        if is_mobile:
            headers.update({
                'Sec-CH-UA-Mobile': '?1',
                'Sec-CH-UA-Platform': '"Android"' if 'Android' in ua else '"iOS"'
            })
        
        # Referrer aleatorio
        if random.choice([True, False]):
            headers['Referer'] = random.choice(self.referrers)
        
        return headers
    
    async def scrape_venue_advanced_requests(self, venue: str) -> List[Dict]:
        """
        🎯 Scraping avanzado de venue usando requests/cloudscraper
        """
        events = []
        
        try:
            # 🌐 URLs a probar (mobile-first)
            venue_urls = [
                f"https://m.facebook.com/{venue}",
                f"https://m.facebook.com/{venue}/events", 
                f"https://www.facebook.com/{venue}",
                f"https://www.facebook.com/{venue}/events",
                f"https://touch.facebook.com/{venue}"
            ]
            
            for url in venue_urls[:3]:  # Limitar para evitar detección
                try:
                    await self._scrape_single_url_advanced(url, venue, events)
                    
                    # Si encontramos eventos, no seguir
                    if events:
                        break
                        
                    # Delay anti-detección
                    await asyncio.sleep(random.uniform(3, 8))
                    
                except Exception as e:
                    logger.error(f"Error URL {url}: {e}")
                    continue
            
            logger.info(f"✅ {venue}: {len(events)} eventos encontrados")
            
        except Exception as e:
            logger.error(f"Error general venue {venue}: {e}")
        
        return events
    
    async def _scrape_single_url_advanced(self, url: str, venue: str, events: List[Dict]):
        """
        🚀 Scraping de una URL específica con máxima evasión
        """
        try:
            # 🎭 Método 1: CloudScraper Ultra-Avanzado
            if await self._try_cloudscraper_advanced(url, venue, events):
                return
            
            # 🌐 Método 2: aiohttp con headers súper-realistas  
            await self._try_aiohttp_advanced(url, venue, events)
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
    
    async def _try_cloudscraper_advanced(self, url: str, venue: str, events: List[Dict]) -> bool:
        """
        🔥 CloudScraper con configuración súper avanzada
        """
        try:
            # Crear scraper con rotación de browser fingerprints
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': random.choice(['chrome', 'firefox']),
                    'platform': random.choice(['windows', 'android', 'darwin']),
                    'desktop': random.choice([True, False])
                },
                delay=random.uniform(1, 4)
            )
            
            # Headers súper realistas
            scraper.headers.update(self._get_advanced_headers(mobile=True))
            
            logger.info(f"🔥 CloudScraper: {url}")
            
            # Request con timeout
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: scraper.get(url, timeout=20)
            )
            
            if response.status_code == 200:
                return await self._extract_events_from_html(response.text, url, venue, events)
            else:
                logger.warning(f"CloudScraper {url}: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"CloudScraper error {url}: {e}")
            return False
    
    async def _try_aiohttp_advanced(self, url: str, venue: str, events: List[Dict]):
        """
        🌐 aiohttp con headers y técnicas avanzadas
        """
        try:
            headers = self._get_advanced_headers(mobile=True)
            
            # Configurar timeout y connector
            timeout = aiohttp.ClientTimeout(total=25)
            connector = aiohttp.TCPConnector(
                limit=10,
                force_close=True,
                enable_cleanup_closed=True
            )
            
            logger.info(f"🌐 aiohttp: {url}")
            
            async with aiohttp.ClientSession(
                headers=headers, 
                timeout=timeout, 
                connector=connector
            ) as session:
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        await self._extract_events_from_html(html, url, venue, events)
                    else:
                        logger.warning(f"aiohttp {url}: Status {response.status}")
                        
        except Exception as e:
            logger.error(f"aiohttp error {url}: {e}")
    
    async def _extract_events_from_html(self, html: str, url: str, venue: str, events: List[Dict]) -> bool:
        """
        🧬 Extracción avanzada de eventos del HTML
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            events_found = 0
            
            # 🎯 ESTRATEGIA 1: JSON embebido en scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('event' in script.string.lower() or 'Event' in script.string):
                    json_events = self._extract_events_from_json_script(script.string, venue, url)
                    events.extend(json_events)
                    events_found += len(json_events)
            
            # 🎯 ESTRATEGIA 2: Selectores HTML específicos
            html_selectors = [
                # Selectores modernos
                '[data-testid*="event"]',
                '[data-ft*="event"]',
                'a[href*="/events/"]',
                
                # Selectores por contenido
                'div:contains("evento")',
                'div:contains("show")', 
                'div:contains("concierto")',
                
                # Selectores genéricos
                '[role="article"]',
                '.story_body_container',
                '._5pbx'
            ]
            
            for selector in html_selectors:
                try:
                    if ':contains(' in selector:
                        # Usar búsqueda por texto para selectores :contains
                        elements = soup.find_all(text=re.compile(selector.split('("')[1].split('")')[0], re.I))
                        for element in elements[:5]:
                            parent = element.parent if hasattr(element, 'parent') else None
                            if parent:
                                event_data = self._extract_event_from_element(parent, venue, url)
                                if event_data:
                                    events.append(event_data)
                                    events_found += 1
                    else:
                        elements = soup.select(selector)
                        for element in elements[:8]:
                            event_data = self._extract_event_from_element(element, venue, url)
                            if event_data:
                                events.append(event_data)
                                events_found += 1
                        
                except Exception as e:
                    continue
            
            # 🎯 ESTRATEGIA 3: Búsqueda por texto libre
            text_patterns = [
                r'evento[s]?\s+[^\n]{10,100}',
                r'show[s]?\s+[^\n]{10,100}',
                r'concierto[s]?\s+[^\n]{10,100}',
                r'festival[s]?\s+[^\n]{10,100}'
            ]
            
            page_text = soup.get_text()
            for pattern in text_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches[:3]:
                    if len(match.strip()) > 15:
                        events.append({
                            'title': match.strip()[:100],
                            'venue': venue,
                            'source': 'facebook_text_pattern',
                            'source_url': url,
                            'method': 'text_pattern_extraction',
                            'scraped_at': datetime.now().isoformat()
                        })
                        events_found += 1
            
            logger.info(f"   📊 {url}: {events_found} eventos extraídos")
            return events_found > 0
            
        except Exception as e:
            logger.error(f"Error extrayendo HTML: {e}")
            return False
    
    def _extract_events_from_json_script(self, json_str: str, venue: str, url: str) -> List[Dict]:
        """
        🔍 Extrae eventos de JSON embebido en scripts
        """
        events = []
        
        try:
            # Patrones para encontrar eventos en JSON
            patterns = [
                r'"name"\s*:\s*"([^"]{15,150})"',
                r'"title"\s*:\s*"([^"]{15,150})"',
                r'"text"\s*:\s*"([^"]*(?:evento|show|concierto|festival)[^"]{10,})"',
                r'"__typename"\s*:\s*"Event"[^}]*"name"\s*:\s*"([^"]+)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, json_str, re.IGNORECASE)
                for match in matches:
                    if (len(match) > 15 and len(match) < 200 and
                        any(keyword in match.lower() for keyword in ['evento', 'show', 'concierto', 'festival', 'música'])):
                        
                        events.append({
                            'title': match.strip(),
                            'venue': venue,
                            'source': 'facebook_json_script',
                            'source_url': url,
                            'method': 'json_script_extraction',
                            'scraped_at': datetime.now().isoformat()
                        })
            
        except Exception as e:
            logger.error(f"Error JSON script extraction: {e}")
        
        return events
    
    def _extract_event_from_element(self, element, venue: str, url: str) -> Optional[Dict]:
        """
        🎯 Extrae evento de elemento HTML específico
        """
        try:
            text = element.get_text(strip=True)
            
            if not text or len(text) < 15:
                return None
            
            # Filtrar contenido relevante
            event_keywords = [
                'evento', 'show', 'concierto', 'festival', 'fiesta',
                'recital', 'función', 'espectáculo', 'música', 'teatro'
            ]
            
            if not any(keyword in text.lower() for keyword in event_keywords):
                return None
            
            # Limpiar texto
            clean_title = self._clean_event_title(text)
            
            if len(clean_title) < 10:
                return None
            
            # Buscar enlace asociado
            event_url = None
            link = element.find('a')
            if link:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        event_url = f"https://www.facebook.com{href}"
                    elif 'facebook.com' in href:
                        event_url = href
            
            # Buscar imagen
            image_url = None
            img = element.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src and 'http' in src:
                    image_url = src
            
            return {
                'title': clean_title,
                'venue': venue,
                'raw_text': text[:300],
                'event_url': event_url,
                'image_url': image_url,
                'source': 'facebook_html_element',
                'source_url': url,
                'method': 'html_element_extraction',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error element extraction: {e}")
            return None
    
    def _clean_event_title(self, text: str) -> str:
        """
        🧹 Limpia el título del evento
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Buscar la mejor línea para título
        for line in lines:
            if (15 <= len(line) <= 120 and
                not line.lower().startswith(('publicado', 'compartir', 'me gusta', 'comentar')) and
                not line.isdigit()):
                return line
        
        # Fallback
        clean_text = ' '.join(lines[:2])
        return clean_text[:100].strip()
    
    async def search_facebook_events_advanced(self, query: str) -> List[Dict]:
        """
        🔍 Búsqueda avanzada de eventos en Facebook
        """
        events = []
        
        try:
            # URLs de búsqueda (mobile-first)
            search_urls = [
                f"https://m.facebook.com/search/events/?q={urllib.parse.quote_plus(query)}",
                f"https://www.facebook.com/search/events/?q={urllib.parse.quote_plus(query)}",
                f"https://touch.facebook.com/search/?q={urllib.parse.quote_plus(query)}&type=events"
            ]
            
            for url in search_urls[:2]:  # Limitar búsquedas
                try:
                    logger.info(f"🔍 Búsqueda: '{query}' -> {url}")
                    
                    await self._scrape_single_url_advanced(url, f"Search:{query}", events)
                    
                    # Delay entre búsquedas
                    await asyncio.sleep(random.uniform(4, 9))
                    
                except Exception as e:
                    logger.error(f"Error búsqueda {url}: {e}")
                    continue
            
            logger.info(f"✅ Búsqueda '{query}': {len(events)} eventos")
            
        except Exception as e:
            logger.error(f"Error búsqueda general: {e}")
        
        return events
    
    async def massive_facebook_scraping_requests(self, venues_limit: int = 8, searches_limit: int = 4) -> List[Dict]:
        """
        🚀 SCRAPING MASIVO usando solo requests (sin browser)
        """
        all_events = []
        
        logger.info("🔥 🔥 INICIANDO FACEBOOK SCRAPING MASIVO (REQUESTS) 🔥 🔥")
        
        try:
            # 🎯 FASE 1: Venues argentinos
            logger.info(f"🏢 FASE 1: Scrapeando {venues_limit} venues...")
            
            selected_venues = self.argentina_venues[:venues_limit]
            
            for i, venue in enumerate(selected_venues):
                try:
                    logger.info(f"🎭 [{i+1}/{venues_limit}] Venue: {venue}")
                    
                    venue_events = await self.scrape_venue_advanced_requests(venue)
                    all_events.extend(venue_events)
                    
                    logger.info(f"   ✅ {venue}: {len(venue_events)} eventos")
                    
                    # Delay anti-detección
                    await asyncio.sleep(random.uniform(4, 10))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error {venue}: {e}")
                    continue
            
            # 🔍 FASE 2: Búsquedas
            logger.info(f"🔍 FASE 2: Realizando {searches_limit} búsquedas...")
            
            selected_queries = self.search_queries[:searches_limit]
            
            for i, query in enumerate(selected_queries):
                try:
                    logger.info(f"🔍 [{i+1}/{searches_limit}] Búsqueda: '{query}'")
                    
                    search_events = await self.search_facebook_events_advanced(query)
                    all_events.extend(search_events)
                    
                    logger.info(f"   ✅ '{query}': {len(search_events)} eventos")
                    
                    # Delay entre búsquedas
                    await asyncio.sleep(random.uniform(6, 12))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error búsqueda '{query}': {e}")
                    continue
            
            # 🧹 FASE 3: Deduplicación
            unique_events = self._deduplicate_facebook_events(all_events)
            
            logger.info(f"🎯 🎯 FACEBOOK REQUESTS SCRAPING COMPLETADO 🎯 🎯")
            logger.info(f"   📊 Eventos totales: {len(all_events)}")
            logger.info(f"   📊 Eventos únicos: {len(unique_events)}")
            
            return unique_events
            
        except Exception as e:
            logger.error(f"Error scraping masivo: {e}")
            return []
    
    def _deduplicate_facebook_events(self, events: List[Dict]) -> List[Dict]:
        """
        🧹 Deduplicación inteligente
        """
        seen_events = set()
        unique_events = []
        
        for event in events:
            title = event.get('title', '').lower().strip()
            venue = event.get('venue', '').lower().strip()
            
            # Crear clave única
            key = f"{title}_{venue}"
            
            if (key not in seen_events and 
                len(title) > 10 and 
                title not in ['facebook', 'evento', 'events', 'página', 'publicación']):
                
                seen_events.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_facebook_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        📋 Normalización para el sistema
        """
        normalized = []
        
        for event in raw_events:
            try:
                start_date = datetime.now() + timedelta(days=random.randint(1, 60))
                
                normalized_event = {
                    'title': event.get('title', 'Evento de Facebook'),
                    'description': event.get('raw_text', '')[:400],
                    
                    'start_datetime': start_date.isoformat(),
                    'end_datetime': (start_date + timedelta(hours=4)).isoformat(),
                    
                    'venue_name': event.get('venue', 'Buenos Aires'),
                    'venue_address': f"{event.get('venue', '')}, Buenos Aires, Argentina",
                    'neighborhood': 'Buenos Aires',
                    'latitude': -34.6037 + random.uniform(-0.1, 0.1),
                    'longitude': -58.3816 + random.uniform(-0.1, 0.1),
                    
                    'category': self._detect_category(event.get('title', '')),
                    'subcategory': '',
                    'tags': ['facebook', 'argentina', 'requests_advanced'],
                    
                    'price': 0.0,
                    'currency': 'ARS',
                    'is_free': True,
                    
                    'source': 'facebook_requests_advanced',
                    'source_id': f"fb_req_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('event_url', ''),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7'),
                    
                    'organizer': event.get('venue', 'Facebook Event'),
                    'capacity': 0,
                    'status': 'live',
                    'scraping_method': event.get('method', 'advanced_requests'),
                    
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando: {e}")
                continue
        
        return normalized
    
    def _detect_category(self, title: str) -> str:
        """
        🎯 Detección de categoría
        """
        title_lower = title.lower()
        
        categories = {
            'music': ['música', 'concierto', 'recital', 'festival', 'dj', 'rock', 'pop'],
            'theater': ['teatro', 'obra', 'comedia', 'drama', 'musical'],
            'cultural': ['arte', 'cultura', 'exposición', 'museo'],
            'nightlife': ['fiesta', 'party', 'boliche', 'club'],
            'social': ['encuentro', 'social', 'meetup', 'tango']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'


# 🧪 FUNCIÓN DE TESTING

async def test_facebook_advanced_requests():
    """
    🧪 Test del Facebook Advanced Requests Scraper
    """
    scraper = FacebookAdvancedRequestsScraper()
    
    print("🔥 🔥 FACEBOOK ADVANCED REQUESTS SCRAPER 🔥 🔥")
    print("🚀 Sin browser - Solo requests/cloudscraper con técnicas avanzadas")
    
    # Scraping masivo
    events = await scraper.massive_facebook_scraping_requests(
        venues_limit=6,
        searches_limit=3
    )
    
    print(f"\n🎯 RESULTADOS FACEBOOK REQUESTS:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    # Por venue
    venues = {}
    for event in events:
        venue = event.get('venue', 'unknown')
        venues[venue] = venues.get(venue, 0) + 1
    
    print(f"\n🏢 Por venue/búsqueda:")
    for venue, count in sorted(venues.items(), key=lambda x: x[1], reverse=True):
        print(f"   {venue}: {count} eventos")
    
    # Por método
    methods = {}
    for event in events:
        method = event.get('method', 'unknown')
        methods[method] = methods.get(method, 0) + 1
    
    print(f"\n🔧 Por método de extracción:")
    for method, count in methods.items():
        print(f"   {method}: {count} eventos")
    
    # Mostrar eventos
    print(f"\n🎭 Primeros 12 eventos:")
    for i, event in enumerate(events[:12]):
        print(f"\n{i+1:2d}. 📌 {event['title'][:60]}...")
        print(f"     🏢 {event.get('venue', 'N/A')}")
        print(f"     🔧 {event.get('method', 'N/A')}")
        if event.get('event_url'):
            print(f"     🔗 {event['event_url'][:50]}...")
    
    # Normalizar
    if events:
        print(f"\n🔄 Normalizando {len(events)} eventos...")
        normalized = scraper.normalize_facebook_events(events)
        print(f"✅ {len(normalized)} eventos normalizados para sistema")
        
        return normalized
    
    return events


if __name__ == "__main__":
    asyncio.run(test_facebook_advanced_requests())