"""
Facebook Events Scraper using Bright Data
Utiliza Bright Data Proxy Network para scraping profesional y evasión de bloqueos
Implementa múltiples técnicas de scraping de eventos en Facebook
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
import urllib.parse

logger = logging.getLogger(__name__)

class FacebookBrightDataScraper:
    """
    Scraper profesional usando Bright Data para obtener eventos de Facebook
    """
    
    def __init__(self, bright_data_config: Optional[Dict] = None):
        """
        bright_data_config format:
        {
            'username': 'your_username',
            'password': 'your_password', 
            'endpoint': 'rotating-residential.brightdata.com:22225',
            'session_id': random_session_id
        }
        """
        self.bright_data_config = bright_data_config
        
        # Facebook venues y páginas públicas en Argentina
        self.facebook_venues = [
            'lunaparkoficial',
            'teatrocolonoficial', 
            'nicetoclub',
            'CCRecoleta',
            'latrasienda',
            'teatrosanmartin',
            'teatromaipo',
            'cinemarks.argentina',
            'estadiobocajuniors',
            'clubestudianteslp',
            'usina.del.arte',
            'ccusina',
            'centroculturalrecoleta',
            'hipodromoargentino',
            'ccsanmartin'
        ]
        
        # User agents para rotar
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def _get_proxy_url(self) -> Optional[str]:
        """
        Construye URL de proxy para Bright Data
        """
        if not self.bright_data_config:
            return None
            
        username = self.bright_data_config['username']
        password = self.bright_data_config['password']
        endpoint = self.bright_data_config['endpoint']
        session_id = self.bright_data_config.get('session_id', random.randint(1000000, 9999999))
        
        # Formato: http://username-session-session_id:password@endpoint
        return f"http://{username}-session-{session_id}:{password}@{endpoint}"
    
    async def method_1_bright_data_mobile(self, venue: str) -> List[Dict]:
        """
        Método 1: Scraping móvil usando Bright Data
        """
        events = []
        
        if not self.bright_data_config:
            logger.warning("🚫 Bright Data no configurado, saltando método 1")
            return events
            
        try:
            proxy_url = self._get_proxy_url()
            mobile_url = f"https://m.facebook.com/{venue}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://www.google.com/',
                'DNT': '1'
            }
            
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout,
                headers=headers
            ) as session:
                
                proxy_config = proxy_url if proxy_url else None
                
                async with session.get(mobile_url, proxy=proxy_config) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Buscar enlaces de eventos
                        event_links = soup.find_all('a', href=re.compile(r'/events/\d+'))
                        
                        for link in event_links[:5]:
                            try:
                                event_text = link.get_text(strip=True)
                                event_href = link.get('href')
                                
                                if event_text and len(event_text) > 5:
                                    events.append({
                                        'title': event_text,
                                        'venue': venue,
                                        'url': f"https://m.facebook.com{event_href}",
                                        'source': 'facebook_brightdata_mobile',
                                        'method': 'bright_data_mobile'
                                    })
                                    
                            except Exception as e:
                                logger.error(f"Error parsing event link: {e}")
                                continue
                        
                        # Buscar en texto de posts
                        post_divs = soup.find_all('div', {'data-ft': True})
                        for div in post_divs[:3]:
                            text = div.get_text()
                            if any(keyword in text.lower() for keyword in ['evento', 'show', 'concierto', 'festival']):
                                title = text[:100].strip()
                                if len(title) > 10:
                                    events.append({
                                        'title': title,
                                        'venue': venue,
                                        'source': 'facebook_brightdata_posts',
                                        'method': 'bright_data_posts'
                                    })
                        
                        logger.info(f"🟢 Bright Data Mobile {venue}: {len(events)} eventos")
                        
                    else:
                        logger.warning(f"🟡 Bright Data Mobile {venue}: Status {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error Bright Data Mobile {venue}: {e}")
        
        await asyncio.sleep(random.uniform(2, 5))  # Rate limiting
        return events
    
    async def method_2_cloudscraper_enhanced(self, venue: str) -> List[Dict]:
        """
        Método 2: CloudScraper con configuración avanzada
        """
        events = []
        
        try:
            # Crear scraper con rotación de browser fingerprints
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': random.choice(['chrome', 'firefox']),
                    'platform': random.choice(['windows', 'darwin', 'linux']),
                    'desktop': random.choice([True, False])
                }
            )
            
            # Headers dinámicos
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # URLs a probar
            urls = [
                f"https://www.facebook.com/{venue}",
                f"https://www.facebook.com/{venue}/events",
                f"https://m.facebook.com/{venue}"
            ]
            
            for url in urls:
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(url, timeout=20)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Método 1: Buscar en scripts JSON
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string and 'event' in script.string.lower():
                                events_found = self._extract_events_from_json(script.string, venue)
                                events.extend(events_found)
                        
                        # Método 2: Buscar en HTML directo
                        # Selectores específicos de Facebook
                        selectors = [
                            '[data-testid*="event"]',
                            '[role="article"]',
                            'div[data-ft*="event"]',
                            'a[href*="/events/"]'
                        ]
                        
                        for selector in selectors:
                            elements = soup.select(selector)
                            for elem in elements[:5]:
                                event_data = self._extract_event_from_element(elem, venue)
                                if event_data:
                                    events.append(event_data)
                        
                        logger.info(f"🟢 CloudScraper {venue} ({url}): {len(events)} eventos")
                        
                        if events:  # Si encontramos eventos, no probar más URLs
                            break
                            
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"CloudScraper error {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ CloudScraper Enhanced {venue}: {e}")
        
        return events
    
    async def method_3_facebook_search(self, query: str = "eventos buenos aires") -> List[Dict]:
        """
        Método 3: Búsqueda pública de Facebook
        """
        events = []
        
        try:
            search_query = urllib.parse.quote_plus(query)
            search_urls = [
                f"https://www.facebook.com/search/events/?q={search_query}",
                f"https://m.facebook.com/search/?q={search_query}&type=events",
                f"https://www.facebook.com/search/top/?q={search_query}"
            ]
            
            scraper = cloudscraper.create_scraper()
            scraper.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'es-AR,es;q=0.9',
                'Referer': 'https://www.google.com/'
            })
            
            for url in search_urls[:2]:  # Limitar a 2 URLs
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: scraper.get(url, timeout=15)
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar resultados de búsqueda
                        result_divs = soup.find_all(['div', 'article'], class_=re.compile('search|result'))
                        
                        for div in result_divs[:8]:
                            title_elem = div.find(['h3', 'h2', 'h4', 'strong'])
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                
                                # Filtrar títulos relevantes
                                if (len(title) > 10 and 
                                    any(keyword in title.lower() for keyword in ['evento', 'show', 'festival', 'concierto', 'fiesta']) and
                                    title.lower() not in ['eventos', 'event', 'events']):
                                    
                                    events.append({
                                        'title': title,
                                        'source': 'facebook_search',
                                        'query': query,
                                        'method': 'search',
                                        'venue': 'Buenos Aires'
                                    })
                        
                        logger.info(f"🟢 Facebook Search '{query}': {len(events)} eventos")
                        
                        if events:
                            break
                            
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"Search error {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Facebook Search error: {e}")
        
        return events
    
    def _extract_events_from_json(self, json_str: str, venue: str) -> List[Dict]:
        """
        Extrae eventos de JSON embebido en Facebook
        """
        events = []
        
        try:
            # Patrones comunes en el JSON de Facebook
            patterns = [
                r'"name"\s*:\s*"([^"]{10,100})"',
                r'"title"\s*:\s*"([^"]{10,100})"',
                r'"text"\s*:\s*"([^"]*(?:evento|show|concierto|festival)[^"]*)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, json_str, re.IGNORECASE)
                for match in matches:
                    if (len(match) > 10 and len(match) < 200 and
                        any(keyword in match.lower() for keyword in ['evento', 'show', 'concierto', 'festival', 'fiesta'])):
                        
                        events.append({
                            'title': match.strip(),
                            'venue': venue,
                            'source': 'facebook_json',
                            'method': 'json_extraction'
                        })
            
            # Buscar fechas embebidas
            date_patterns = [
                r'"start_time"\s*:\s*"([^"]+)"',
                r'"event_time"\s*:\s*"([^"]+)"'
            ]
            
            for pattern in date_patterns:
                dates = re.findall(pattern, json_str)
                # Asociar fechas con eventos si las encontramos
                for i, event in enumerate(events):
                    if i < len(dates):
                        event['raw_date'] = dates[i]
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
        
        return events
    
    def _extract_event_from_element(self, element, venue: str) -> Optional[Dict]:
        """
        Extrae información de evento de un elemento HTML
        """
        try:
            # Obtener texto del elemento
            text = element.get_text(strip=True)
            
            # Verificar que sea relevante
            if (len(text) > 15 and len(text) < 300 and
                any(keyword in text.lower() for keyword in ['evento', 'show', 'concierto', 'festival', 'fiesta', 'música'])):
                
                # Intentar obtener enlace
                link = element.find('a')
                event_url = None
                if link:
                    href = link.get('href')
                    if href:
                        event_url = f"https://www.facebook.com{href}" if href.startswith('/') else href
                
                # Intentar obtener imagen
                img = element.find('img')
                image_url = img.get('src') if img else None
                
                return {
                    'title': text[:150].strip(),
                    'venue': venue,
                    'url': event_url,
                    'image_url': image_url,
                    'source': 'facebook_html',
                    'method': 'html_extraction'
                }
        
        except Exception as e:
            logger.error(f"Element extraction error: {e}")
        
        return None
    
    async def scrape_all_venues(self, limit_per_venue: int = 3) -> List[Dict]:
        """
        Scraping completo de todos los venues usando todos los métodos
        """
        all_events = []
        
        logger.info("🚀 Iniciando scraping masivo de Facebook con múltiples técnicas...")
        
        # Tareas para ejecutar en paralelo
        tasks = []
        
        # Método 1: Bright Data (si está configurado)
        if self.bright_data_config:
            for venue in self.facebook_venues[:8]:  # Top venues
                tasks.append(self.method_1_bright_data_mobile(venue))
        
        # Método 2: CloudScraper Enhanced
        for venue in self.facebook_venues[:6]:
            tasks.append(self.method_2_cloudscraper_enhanced(venue))
        
        # Método 3: Búsquedas públicas
        search_queries = [
            "eventos buenos aires",
            "conciertos argentina", 
            "shows luna park",
            "festivales buenos aires",
            "eventos culturales argentina"
        ]
        for query in search_queries:
            tasks.append(self.method_3_facebook_search(query))
        
        logger.info(f"🔥 Ejecutando {len(tasks)} tareas de scraping en paralelo...")
        
        # Ejecutar todas las tareas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_events.extend(result)
                logger.info(f"✅ Tarea {i+1}: {len(result)} eventos")
            elif isinstance(result, Exception):
                logger.error(f"❌ Tarea {i+1} falló: {result}")
        
        # Deduplicar eventos
        unique_events = self._deduplicate_events(all_events)
        
        logger.info(f"🎯 RESULTADO FINAL: {len(all_events)} eventos totales, {len(unique_events)} únicos")
        
        return unique_events
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Elimina eventos duplicados basándose en el título
        """
        seen_titles = set()
        unique_events = []
        
        for event in events:
            title_key = event.get('title', '').lower().strip()
            
            # Generar clave única más robusta
            venue_key = event.get('venue', '').lower().strip()
            combined_key = f"{title_key}_{venue_key}"
            
            if (combined_key and 
                combined_key not in seen_titles and 
                len(title_key) > 8 and
                title_key not in ['evento', 'events', 'facebook', 'página']):
                
                seen_titles.add(combined_key)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos al formato estándar del sistema
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Parsear fecha si está disponible
                start_datetime = self._parse_facebook_date(event.get('raw_date'))
                
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento sin título'),
                    'description': f"Evento de {event.get('venue', 'Facebook')} - {event.get('method', '')}",
                    
                    # Fechas
                    'start_datetime': start_datetime.isoformat() if start_datetime else None,
                    'end_datetime': (start_datetime + timedelta(hours=3)).isoformat() if start_datetime else None,
                    
                    # Ubicación
                    'venue_name': event.get('venue', 'Buenos Aires'),
                    'venue_address': f"{event.get('venue', '')}, Buenos Aires, Argentina",
                    'neighborhood': 'Buenos Aires',
                    'latitude': -34.6037 + random.uniform(-0.1, 0.1),
                    'longitude': -58.3816 + random.uniform(-0.1, 0.1),
                    
                    # Categorización
                    'category': self._detect_category(event.get('title', '')),
                    'subcategory': '',
                    'tags': ['facebook', 'argentina', event.get('method', '')],
                    
                    # Precio
                    'price': 0.0,
                    'currency': 'ARS',
                    'is_free': True,  # Facebook events generalmente no muestran precio
                    
                    # Metadata
                    'source': 'facebook_advanced_scraper',
                    'source_id': f"fb_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('url', ''),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7'),
                    
                    # Info adicional
                    'organizer': event.get('venue', 'Organizador de Facebook'),
                    'capacity': 0,
                    'status': 'live',
                    'scraping_method': event.get('method', 'unknown'),
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing event: {e}")
                continue
        
        return normalized
    
    def _parse_facebook_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parsea fechas de Facebook a datetime
        """
        if not date_str:
            # Retornar fecha aleatoria futura
            return datetime.now() + timedelta(days=random.randint(1, 45))
        
        try:
            # Intentar parsear ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Si no es ISO, retornar fecha futura aleatoria
            return datetime.now() + timedelta(days=random.randint(1, 30))
            
        except:
            return datetime.now() + timedelta(days=random.randint(1, 30))
    
    def _detect_category(self, title: str) -> str:
        """
        Detecta la categoría del evento
        """
        title_lower = title.lower()
        
        categories = {
            'music': ['música', 'musica', 'concierto', 'recital', 'dj', 'rock', 'pop', 'jazz', 'electrónica'],
            'party': ['fiesta', 'party', 'celebración', 'after', 'boliche'],
            'cultural': ['arte', 'cultura', 'museo', 'teatro', 'exposición'],
            'sports': ['deporte', 'fútbol', 'básquet', 'tenis'],
            'food': ['comida', 'gastronomía', 'restaurante', 'degustación'],
            'social': ['milonga', 'tango', 'baile', 'encuentro']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'


# Función de testing
async def test_facebook_bright_data_scraper(bright_data_config: Optional[Dict] = None):
    """
    Prueba el scraper avanzado de Facebook
    """
    scraper = FacebookBrightDataScraper(bright_data_config)
    
    print("🔥 Iniciando Facebook Advanced Scraper...")
    print(f"🌐 Bright Data configurado: {'✅' if bright_data_config else '❌'}")
    
    # Scraping masivo
    events = await scraper.scrape_all_venues()
    
    print(f"\n✅ RESULTADOS FINALES:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    # Agrupar por método
    methods = {}
    for event in events:
        method = event.get('method', 'unknown')
        if method not in methods:
            methods[method] = []
        methods[method].append(event)
    
    print(f"\n📈 Por método de scraping:")
    for method, method_events in methods.items():
        print(f"   {method}: {len(method_events)} eventos")
    
    # Mostrar eventos
    print(f"\n🎭 Eventos encontrados:")
    for i, event in enumerate(events[:15]):
        print(f"\n{i+1}. 📌 {event['title'][:80]}...")
        print(f"    🏢 {event.get('venue', 'N/A')}")
        print(f"    🔧 {event.get('method', 'N/A')}")
        if event.get('url'):
            print(f"    🔗 {event['url']}")
    
    # Normalizar eventos
    if events:
        print(f"\n🔄 Normalizando eventos...")
        normalized = scraper.normalize_events(events)
        print(f"✅ {len(normalized)} eventos normalizados")
        
        return normalized
    
    return events


if __name__ == "__main__":
    # Configuración de ejemplo para Bright Data
    # bright_config = {
    #     'username': 'your_username',
    #     'password': 'your_password',
    #     'endpoint': 'rotating-residential.brightdata.com:22225'
    # }
    
    # Sin Bright Data (solo CloudScraper)
    bright_config = None
    
    asyncio.run(test_facebook_bright_data_scraper(bright_config))