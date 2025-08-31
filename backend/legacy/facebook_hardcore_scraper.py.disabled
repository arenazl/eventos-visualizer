"""
Facebook HARDCORE Scraper
Múltiples estrategias para bypasear todas las protecciones
"""

import aiohttp
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
import random
import time
import json
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FacebookHardcoreScraper:
    """
    Scraper hardcore que prueba TODOS los métodos posibles
    """
    
    def __init__(self):
        # Múltiples User-Agents para rotar
        self.user_agents = [
            # iPhone
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            
            # Android
            'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36',
            
            # Desktop Chrome (older versions)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        # Páginas públicas de venues argentinos
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
            'clubestudianteslp'
        ]
        
        # Diferentes endpoints de Facebook a probar
        self.facebook_endpoints = [
            'https://www.facebook.com/{page}',
            'https://m.facebook.com/{page}', 
            'https://www.facebook.com/pg/{page}/events',
            'https://m.facebook.com/{page}/events',
            'https://www.facebook.com/{page}/events',
            'https://graph.facebook.com/{page}/events',
            'https://www.facebook.com/events/search/?q={page}'
        ]
    
    async def method_1_basic_requests(self, page: str) -> List[Dict]:
        """
        Método 1: Requests básicos con rotación de User-Agents
        """
        events = []
        
        for ua in self.user_agents[:3]:  # Probar 3 User-Agents
            try:
                headers = {
                    'User-Agent': ua,
                    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                url = f"https://www.facebook.com/{page}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Buscar JSON embebido
                            soup = BeautifulSoup(html, 'html.parser')
                            scripts = soup.find_all('script')
                            
                            for script in scripts:
                                if script.string and 'event' in script.string.lower():
                                    # Intentar extraer eventos
                                    events_found = self._extract_events_from_json(script.string)
                                    events.extend(events_found)
                            
                            # Buscar en HTML directo
                            event_divs = soup.find_all(['div', 'article'], string=re.compile('event|show|concert', re.I))
                            for div in event_divs:
                                event = self._extract_event_from_html(div, page)
                                if event:
                                    events.append(event)
                            
                            logger.info(f"Method 1 - {page} with {ua[:20]}...: {len(events)} events")
                            
                            if events:  # Si encontramos algo, no probar más User-Agents
                                break
                                
                await asyncio.sleep(random.uniform(1, 3))  # Delay anti-detección
                
            except Exception as e:
                logger.error(f"Method 1 error for {page}: {e}")
                continue
        
        return events
    
    async def method_2_mobile_facebook(self, page: str) -> List[Dict]:
        """
        Método 2: Facebook móvil (menos protecciones)
        """
        events = []
        
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        mobile_urls = [
            f"https://m.facebook.com/{page}",
            f"https://mobile.facebook.com/{page}", 
            f"https://touch.facebook.com/{page}"
        ]
        
        for url in mobile_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=mobile_headers, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Buscar contenido más simple en móvil
                            event_links = soup.find_all('a', href=re.compile('event'))
                            for link in event_links:
                                event_text = link.get_text(strip=True)
                                if event_text and len(event_text) > 3:
                                    events.append({
                                        'title': event_text,
                                        'source': 'facebook_mobile',
                                        'page': page,
                                        'method': 'mobile'
                                    })
                            
                            logger.info(f"Method 2 - {url}: {len(events)} events")
                            
                            if events:
                                break
                                
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Method 2 error for {url}: {e}")
                continue
        
        return events
    
    async def method_3_cloudscraper_advanced(self, page: str) -> List[Dict]:
        """
        Método 3: CloudScraper con configuraciones avanzadas
        """
        events = []
        
        try:
            # Crear scraper con configuración específica
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'android',
                    'mobile': True
                },
                delay=random.uniform(1, 3)
            )
            
            # Headers adicionales
            scraper.headers.update({
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            })
            
            urls_to_try = [
                f"https://www.facebook.com/{page}",
                f"https://www.facebook.com/{page}/events",
                f"https://m.facebook.com/{page}"
            ]
            
            for url in urls_to_try:
                try:
                    response = scraper.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar scripts con datos JSON
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string:
                                # Buscar patrones específicos de eventos
                                if '"event"' in script.string or '"Event"' in script.string:
                                    events_found = self._extract_events_from_json(script.string)
                                    events.extend(events_found)
                        
                        # Buscar en HTML
                        event_elements = soup.find_all(text=re.compile(r'(concert|show|event|música|concierto)', re.I))
                        for element in event_elements[:5]:  # Limitamos a 5
                            parent = element.parent
                            if parent:
                                event_text = parent.get_text(strip=True)
                                if len(event_text) > 10 and len(event_text) < 200:
                                    events.append({
                                        'title': event_text,
                                        'source': 'facebook_cloudscraper',
                                        'page': page,
                                        'method': 'cloudscraper'
                                    })
                        
                        logger.info(f"Method 3 - {url}: {len(events)} events")
                        
                        if events:
                            break
                            
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"CloudScraper error for {url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Method 3 general error: {e}")
        
        return events
    
    async def method_4_facebook_search(self, query: str = "eventos buenos aires") -> List[Dict]:
        """
        Método 4: Búsqueda pública de Facebook
        """
        events = []
        
        try:
            search_url = f"https://www.facebook.com/search/events/?q={query.replace(' ', '%20')}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-AR,es;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Buscar resultados de búsqueda
                        search_results = soup.find_all(['div', 'article'], class_=re.compile('search|result'))
                        
                        for result in search_results[:10]:
                            title_elem = result.find(['h3', 'h2', 'a'])
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                if title and 'event' not in title.lower():  # Evitar textos genéricos
                                    events.append({
                                        'title': title,
                                        'source': 'facebook_search',
                                        'query': query,
                                        'method': 'search'
                                    })
                        
                        logger.info(f"Method 4 - Facebook search '{query}': {len(events)} events")
            
        except Exception as e:
            logger.error(f"Method 4 error: {e}")
        
        return events
    
    def _extract_events_from_json(self, json_str: str) -> List[Dict]:
        """
        Extrae eventos de JSON embebido en scripts
        """
        events = []
        
        try:
            # Buscar patrones de eventos en JSON
            event_patterns = [
                r'"name":"([^"]+event[^"]*)"',
                r'"title":"([^"]+)"',
                r'"Event":\s*{[^}]*"name":"([^"]+)"'
            ]
            
            for pattern in event_patterns:
                matches = re.findall(pattern, json_str, re.I)
                for match in matches:
                    if len(match) > 5 and len(match) < 200:
                        events.append({
                            'title': match,
                            'source': 'facebook_json',
                            'method': 'json_extraction'
                        })
        
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
        
        return events
    
    def _extract_event_from_html(self, element, page: str) -> Dict:
        """
        Extrae evento de elemento HTML
        """
        try:
            text = element.get_text(strip=True)
            
            if text and len(text) > 10 and len(text) < 300:
                # Verificar que sea un evento real
                event_keywords = ['concert', 'show', 'event', 'música', 'concierto', 'festival', 'fiesta']
                
                if any(keyword in text.lower() for keyword in event_keywords):
                    return {
                        'title': text,
                        'source': 'facebook_html',
                        'page': page,
                        'method': 'html_extraction'
                    }
        
        except:
            pass
        
        return None
    
    async def scrape_all_methods(self) -> List[Dict]:
        """
        Ejecuta TODOS los métodos en paralelo para máxima efectividad
        """
        all_events = []
        
        logger.info("🔥 Iniciando Facebook HARDCORE Scraping...")
        
        # Lista de todas las tareas a ejecutar
        tasks = []
        
        # Método 1: Básico con múltiples páginas
        for page in self.facebook_venues[:5]:  # Primeras 5 páginas
            tasks.append(self.method_1_basic_requests(page))
        
        # Método 2: Móvil con páginas principales
        for page in ['lunaparkoficial', 'teatrocolonoficial', 'nicetoclub']:
            tasks.append(self.method_2_mobile_facebook(page))
        
        # Método 3: CloudScraper con páginas top
        for page in ['lunaparkoficial', 'CCRecoleta']:
            tasks.append(self.method_3_cloudscraper_advanced(page))
        
        # Método 4: Búsqueda pública
        search_queries = ['eventos buenos aires', 'conciertos argentina', 'shows luna park']
        for query in search_queries:
            tasks.append(self.method_4_facebook_search(query))
        
        logger.info(f"🚀 Ejecutando {len(tasks)} tareas de scraping...")
        
        # Ejecutar todo en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
        
        # Deduplicar por título
        seen_titles = set()
        unique_events = []
        
        for event in all_events:
            title_key = event.get('title', '').lower().strip()
            if title_key and title_key not in seen_titles and len(title_key) > 5:
                seen_titles.add(title_key)
                unique_events.append(event)
        
        logger.info(f"🎯 Facebook HARDCORE: {len(all_events)} eventos totales, {len(unique_events)} únicos")
        
        return unique_events


# Testing
async def test_facebook_hardcore():
    """
    Prueba el scraper hardcore de Facebook
    """
    scraper = FacebookHardcoreScraper()
    
    print("🔥 Iniciando Facebook HARDCORE Scraper...")
    
    events = await scraper.scrape_all_methods()
    
    print(f"\n✅ RESULTADOS FACEBOOK HARDCORE:")
    print(f"   Total eventos únicos: {len(events)}")
    
    # Mostrar por método
    methods = {}
    for event in events:
        method = event.get('method', 'unknown')
        if method not in methods:
            methods[method] = []
        methods[method].append(event)
    
    print(f"\n📊 Por método:")
    for method, method_events in methods.items():
        print(f"   {method}: {len(method_events)} eventos")
    
    print(f"\n🎯 Primeros 10 eventos:")
    for event in events[:10]:
        print(f"\n📌 {event['title']}")
        print(f"   🔗 Fuente: {event['source']}")
        print(f"   ⚙️ Método: {event['method']}")
        if 'page' in event:
            print(f"   📄 Página: {event['page']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_facebook_hardcore())