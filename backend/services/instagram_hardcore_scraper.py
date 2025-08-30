"""
Instagram HARDCORE Scraper
Múltiples estrategias para bypasear Instagram sin tokens
"""

import aiohttp
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
import random
import json
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InstagramHardcoreScraper:
    """
    Scraper hardcore de Instagram sin tokens
    """
    
    def __init__(self):
        self.user_agents = [
            # Mobile Instagram app user agents
            'Instagram 126.0.0.25.121 (iPhone; iOS 14_2; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/420+',
            'Instagram 126.0.0.25.121 (iPhone; iOS 13_3; en_US; en-US; scale=3.00; 1125x2436) AppleWebKit/420+',
            
            # Mobile browser
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36',
            
            # Desktop browsers (older versions)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15'
        ]
        
        # Hashtags argentinos para eventos
        self.argentina_hashtags = [
            'eventosba',
            'buenosaires',
            'eventosargentina',
            'conciertosar',
            'lunapark',
            'teatrocolon',
            'palermo',
            'recoleta',
            'santelmo',
            'festivalesarg'
        ]
        
        # Cuentas de venues argentinos
        self.instagram_venues = [
            'lunaparkoficial',
            'teatrocolon_oficial',
            'nicetoclub',
            'centroculturalrecoleta',
            'latrasienda',
            'teatrosanmartin',
            'usina_del_arte'
        ]
    
    async def method_1_hashtag_scraping(self, hashtag: str) -> List[Dict]:
        """
        Método 1: Scraping de hashtags públicos
        """
        events = []
        
        try:
            # Instagram web hashtag URL
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Buscar window._sharedData
                        if 'window._sharedData' in html:
                            try:
                                # Extraer JSON data
                                json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(1))
                                    
                                    # Navegar estructura de Instagram
                                    entry_data = data.get('entry_data', {})
                                    tag_page = entry_data.get('TagPage', [{}])[0]
                                    graphql = tag_page.get('graphql', {})
                                    hashtag_data = graphql.get('hashtag', {})
                                    media_edges = hashtag_data.get('edge_hashtag_to_media', {}).get('edges', [])
                                    
                                    for edge in media_edges[:15]:  # Primeros 15 posts
                                        node = edge.get('node', {})
                                        
                                        # Extraer caption
                                        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                                        if caption_edges:
                                            caption = caption_edges[0].get('node', {}).get('text', '')
                                            
                                            # Buscar eventos en el caption
                                            if self._is_event_caption(caption):
                                                event = {
                                                    'title': self._extract_title_from_caption(caption),
                                                    'description': caption[:200],
                                                    'source': 'instagram_hashtag',
                                                    'hashtag': hashtag,
                                                    'image_url': node.get('display_url', ''),
                                                    'likes': node.get('edge_liked_by', {}).get('count', 0),
                                                    'shortcode': node.get('shortcode'),
                                                    'method': 'hashtag_shareddata'
                                                }
                                                events.append(event)
                                
                                logger.info(f"Method 1 - Hashtag #{hashtag}: {len(events)} events from _sharedData")
                                
                            except Exception as e:
                                logger.error(f"Error parsing _sharedData for #{hashtag}: {e}")
                        
                        # Método alternativo: buscar en HTML
                        soup = BeautifulSoup(html, 'html.parser')
                        scripts = soup.find_all('script')
                        
                        for script in scripts:
                            if script.string and 'GraphQL' in script.string:
                                # Buscar posts en GraphQL response
                                posts_found = self._extract_posts_from_graphql(script.string)
                                events.extend(posts_found)
                        
                        logger.info(f"Method 1 final - #{hashtag}: {len(events)} events")
            
        except Exception as e:
            logger.error(f"Method 1 error for #{hashtag}: {e}")
        
        return events
    
    async def method_2_profile_scraping(self, username: str) -> List[Dict]:
        """
        Método 2: Scraping de perfiles de venues
        """
        events = []
        
        try:
            url = f"https://www.instagram.com/{username}/"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-AR,es;q=0.9',
                'Referer': 'https://www.google.com/',
                'Cache-Control': 'no-cache'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Buscar datos del perfil
                        if 'window._sharedData' in html:
                            try:
                                json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(1))
                                    
                                    profile_page = data.get('entry_data', {}).get('ProfilePage', [{}])[0]
                                    graphql = profile_page.get('graphql', {})
                                    user = graphql.get('user', {})
                                    media = user.get('edge_owner_to_timeline_media', {}).get('edges', [])
                                    
                                    for edge in media[:12]:  # Últimos 12 posts
                                        node = edge.get('node', {})
                                        
                                        # Extraer caption
                                        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                                        if caption_edges:
                                            caption = caption_edges[0].get('node', {}).get('text', '')
                                            
                                            if self._is_event_caption(caption):
                                                event = {
                                                    'title': self._extract_title_from_caption(caption),
                                                    'description': caption[:200],
                                                    'source': 'instagram_profile',
                                                    'username': username,
                                                    'image_url': node.get('display_url', ''),
                                                    'likes': node.get('edge_liked_by', {}).get('count', 0),
                                                    'shortcode': node.get('shortcode'),
                                                    'method': 'profile_shareddata'
                                                }
                                                events.append(event)
                                
                                logger.info(f"Method 2 - Profile @{username}: {len(events)} events")
                                
                            except Exception as e:
                                logger.error(f"Error parsing profile {username}: {e}")
            
        except Exception as e:
            logger.error(f"Method 2 error for @{username}: {e}")
        
        return events
    
    async def method_3_cloudscraper_instagram(self, hashtag: str) -> List[Dict]:
        """
        Método 3: CloudScraper para bypasear protecciones
        """
        events = []
        
        try:
            # Crear scraper específico para Instagram
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'android',
                    'mobile': True
                }
            )
            
            scraper.headers.update({
                'Accept-Language': 'es-AR,es;q=0.9',
                'Cache-Control': 'no-cache',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            
            response = scraper.get(url, timeout=20)
            
            if response.status_code == 200:
                # Método similar al #1 pero con CloudScraper
                html = response.text
                
                if 'window._sharedData' in html:
                    json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        
                        # Misma lógica de extracción
                        tag_page = data.get('entry_data', {}).get('TagPage', [{}])[0]
                        media_edges = tag_page.get('graphql', {}).get('hashtag', {}).get('edge_hashtag_to_media', {}).get('edges', [])
                        
                        for edge in media_edges:
                            node = edge.get('node', {})
                            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                            
                            if caption_edges:
                                caption = caption_edges[0].get('node', {}).get('text', '')
                                
                                if self._is_event_caption(caption):
                                    event = {
                                        'title': self._extract_title_from_caption(caption),
                                        'description': caption[:200],
                                        'source': 'instagram_cloudscraper',
                                        'hashtag': hashtag,
                                        'likes': node.get('edge_liked_by', {}).get('count', 0),
                                        'method': 'cloudscraper'
                                    }
                                    events.append(event)
                
                logger.info(f"Method 3 - CloudScraper #{hashtag}: {len(events)} events")
            
        except Exception as e:
            logger.error(f"Method 3 error for #{hashtag}: {e}")
        
        return events
    
    def _is_event_caption(self, caption: str) -> bool:
        """
        Determina si un caption es sobre un evento
        """
        if not caption or len(caption) < 20:
            return False
        
        caption_lower = caption.lower()
        
        event_keywords = [
            'evento', 'event', 'concierto', 'concert', 'show', 'festival',
            'fiesta', 'party', 'música', 'music', 'teatro', 'dance',
            'exposición', 'exhibition', 'taller', 'workshop', 'conferencia',
            'presentación', 'lanzamiento', 'estreno', 'premiere',
            'fecha', 'date', 'entradas', 'tickets', 'reserva'
        ]
        
        venue_keywords = [
            'luna park', 'teatro colon', 'niceto', 'usina del arte',
            'recoleta', 'palermo', 'san telmo', 'microcentro'
        ]
        
        date_patterns = [
            r'\d{1,2}/\d{1,2}',  # dd/mm
            r'\d{1,2}\s+de\s+\w+',  # día de mes
            r'(viernes|sábado|domingo|lunes|martes|miércoles|jueves)',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        ]
        
        # Verificar palabras clave de eventos
        has_event_keywords = any(keyword in caption_lower for keyword in event_keywords)
        has_venue_keywords = any(keyword in caption_lower for keyword in venue_keywords)
        has_date_pattern = any(re.search(pattern, caption_lower) for pattern in date_patterns)
        
        return has_event_keywords or (has_venue_keywords and has_date_pattern)
    
    def _extract_title_from_caption(self, caption: str) -> str:
        """
        Extrae título del caption
        """
        if not caption:
            return "Evento de Instagram"
        
        # Tomar primera línea o primeras 100 caracteres
        lines = caption.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) > 10:
            return first_line[:100]
        else:
            return caption[:100].strip()
    
    def _extract_posts_from_graphql(self, script_content: str) -> List[Dict]:
        """
        Extrae posts de respuestas GraphQL embebidas
        """
        posts = []
        
        try:
            # Buscar patrones de posts en GraphQL
            post_patterns = [
                r'"shortcode":"([^"]+)".*?"caption":"([^"]+)"',
                r'"node":\s*{[^}]*"shortcode":"([^"]+)"[^}]*"text":"([^"]+)"'
            ]
            
            for pattern in post_patterns:
                matches = re.findall(pattern, script_content, re.DOTALL)
                for shortcode, caption in matches:
                    if self._is_event_caption(caption):
                        posts.append({
                            'title': self._extract_title_from_caption(caption),
                            'description': caption[:200],
                            'source': 'instagram_graphql',
                            'shortcode': shortcode,
                            'method': 'graphql_extraction'
                        })
        
        except Exception as e:
            logger.error(f"GraphQL extraction error: {e}")
        
        return posts
    
    async def scrape_all_methods(self) -> List[Dict]:
        """
        Ejecuta TODOS los métodos de Instagram
        """
        all_events = []
        
        logger.info("📸 Iniciando Instagram HARDCORE Scraping...")
        
        tasks = []
        
        # Método 1: Hashtags principales
        for hashtag in self.argentina_hashtags[:5]:
            tasks.append(self.method_1_hashtag_scraping(hashtag))
        
        # Método 2: Perfiles de venues
        for username in self.instagram_venues[:3]:
            tasks.append(self.method_2_profile_scraping(username))
        
        # Método 3: CloudScraper en hashtags top
        for hashtag in ['eventosba', 'buenosaires']:
            tasks.append(self.method_3_cloudscraper_instagram(hashtag))
        
        logger.info(f"🚀 Ejecutando {len(tasks)} tareas de Instagram...")
        
        # Ejecutar en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Instagram task failed: {result}")
        
        # Deduplicar
        seen = set()
        unique_events = []
        
        for event in all_events:
            key = event.get('title', '').lower().strip()
            if key and key not in seen and len(key) > 10:
                seen.add(key)
                unique_events.append(event)
        
        logger.info(f"🎯 Instagram HARDCORE: {len(all_events)} total, {len(unique_events)} únicos")
        
        return unique_events


# Testing
async def test_instagram_hardcore():
    """
    Prueba el scraper hardcore de Instagram
    """
    scraper = InstagramHardcoreScraper()
    
    print("📸 Iniciando Instagram HARDCORE Scraper...")
    
    events = await scraper.scrape_all_methods()
    
    print(f"\n✅ RESULTADOS INSTAGRAM HARDCORE:")
    print(f"   Total eventos únicos: {len(events)}")
    
    # Por método
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
        if 'hashtag' in event:
            print(f"   #️⃣ Hashtag: #{event['hashtag']}")
        if 'likes' in event:
            print(f"   ❤️ Likes: {event['likes']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_instagram_hardcore())