"""
Cloud-based Web Scraper for Social Media
Uses external APIs to bypass local browser requirements
No sudo or system dependencies needed
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CloudScraper:
    """
    Scraper que usa servicios externos para obtener contenido
    No requiere Playwright ni dependencias del sistema
    """
    
    def __init__(self):
        # Opciones de servicios de scraping (muchos tienen tier gratuito)
        self.scraping_services = {
            'scraperapi': {
                'url': 'http://api.scraperapi.com',
                'key': os.getenv('SCRAPERAPI_KEY', ''),
                'free_tier': 1000  # requests/month
            },
            'scrapingbee': {
                'url': 'https://app.scrapingbee.com/api/v1',
                'key': os.getenv('SCRAPINGBEE_KEY', ''),
                'free_tier': 1000
            },
            'brightdata': {
                'url': 'https://api.brightdata.com',
                'key': os.getenv('BRIGHTDATA_KEY', ''),
                'free_tier': 'limited'
            }
        }
        
        # Fallback: uso directo con headers anti-detección
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_url_direct(self, url: str) -> Optional[str]:
        """
        Intenta obtener contenido directamente sin browser
        Funciona para muchos sitios que no requieren JavaScript
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)  # Evitar problemas SSL
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url, headers=self.headers, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Direct scrape failed: {response.status} for {url}")
                        return None
        except Exception as e:
            logger.error(f"Error in direct scrape of {url}: {e}")
            return None
    
    async def scrape_facebook_events_api(self, location: str) -> List[Dict]:
        """
        Usa Graph API de Facebook (requiere app token)
        O alternativas públicas sin autenticación
        """
        events = []
        
        # Opción 1: Facebook Graph API (requiere token)
        fb_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        if fb_token:
            url = f"https://graph.facebook.com/v18.0/search"
            params = {
                'type': 'event',
                'q': location,
                'fields': 'name,description,start_time,place,cover',
                'access_token': fb_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for event in data.get('data', []):
                            events.append(self._parse_facebook_event(event))
        
        # Sin API token no podemos obtener eventos reales de Facebook
        if not events:
            logger.warning("⚠️ Facebook Graph API requires access token")
        
        return events
    
    async def scrape_instagram_hashtag_api(self, hashtag: str) -> List[Dict]:
        """
        Instagram scraping sin Playwright
        Usa endpoints públicos o APIs alternativas
        """
        posts = []
        
        # Opción 1: Instagram Basic Display API (requiere token)
        ig_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        if ig_token:
            url = f"https://graph.instagram.com/v18.0/ig_hashtag_search"
            params = {
                'user_id': os.getenv('INSTAGRAM_USER_ID'),
                'q': hashtag,
                'access_token': ig_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Process hashtag data
                        pass
        
        # Sin API token no podemos obtener posts reales de Instagram
        if not posts:
            logger.warning("⚠️ Instagram Basic Display API requires access token")
        
        return posts
    
    async def scrape_eventbrite_public(self, location: str) -> List[Dict]:
        """
        Scraping de Eventbrite sin API key
        Usa la búsqueda pública
        """
        events = []
        
        # Eventbrite tiene una búsqueda pública accesible
        search_url = f"https://www.eventbrite.com/d/{location.lower().replace(' ', '-')}--events/"
        
        html = await self.scrape_url_direct(search_url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar tarjetas de eventos
            event_cards = soup.find_all('article', class_='event-card')
            
            for card in event_cards[:20]:
                try:
                    event = {
                        'title': card.find('h3').get_text(strip=True) if card.find('h3') else '',
                        'date': card.find('time').get_text(strip=True) if card.find('time') else '',
                        'location': card.find('div', class_='location').get_text(strip=True) if card.find('div', class_='location') else location,
                        'url': card.find('a')['href'] if card.find('a') else '',
                        'image': card.find('img')['src'] if card.find('img') else '',
                        'price': card.find('span', class_='price').get_text(strip=True) if card.find('span', class_='price') else 'Free',
                        'source': 'eventbrite_public'
                    }
                    
                    if event['title']:
                        events.append(event)
                        
                except Exception as e:
                    logger.error(f"Error parsing Eventbrite event: {e}")
        
        return events
    
    def _parse_facebook_event(self, event_data: Dict) -> Dict:
        """
        Parsea evento de Facebook API
        """
        return {
            'title': event_data.get('name', ''),
            'description': event_data.get('description', ''),
            'start_datetime': event_data.get('start_time', ''),
            'venue_name': event_data.get('place', {}).get('name', ''),
            'venue_address': event_data.get('place', {}).get('location', {}).get('street', ''),
            'latitude': event_data.get('place', {}).get('location', {}).get('latitude'),
            'longitude': event_data.get('place', {}).get('location', {}).get('longitude'),
            'image_url': event_data.get('cover', {}).get('source', ''),
            'event_url': f"https://www.facebook.com/events/{event_data.get('id')}",
            'source': 'facebook',
            'platform': 'facebook'
        }
    
    def _extract_event_from_html(self, element) -> Optional[Dict]:
        """
        Extrae información de evento del HTML
        """
        try:
            title = element.find('span', {'dir': 'auto'})
            date = element.find('span', string=lambda x: x and ('2024' in x or '2025' in x))
            location = element.find('span', {'aria-label': True})
            
            if title:
                return {
                    'title': title.get_text(strip=True),
                    'date': date.get_text(strip=True) if date else '',
                    'location': location.get_text(strip=True) if location else '',
                    'source': 'facebook_public'
                }
        except:
            pass
        return None
    
    async def use_scraping_service(self, url: str, service: str = 'scraperapi') -> Optional[str]:
        """
        Usa un servicio de scraping externo con API
        Muchos tienen tier gratuito (1000 requests/month)
        """
        if service == 'scraperapi' and self.scraping_services['scraperapi']['key']:
            api_url = f"http://api.scraperapi.com?api_key={self.scraping_services['scraperapi']['key']}&url={url}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        return await response.text()
        
        elif service == 'scrapingbee' and self.scraping_services['scrapingbee']['key']:
            api_url = self.scraping_services['scrapingbee']['url']
            params = {
                'api_key': self.scraping_services['scrapingbee']['key'],
                'url': url,
                'render_js': 'true'  # Para contenido JavaScript
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        return await response.text()
        
        return None


# Testing
async def test_cloud_scraper():
    """
    Prueba el scraper cloud
    """
    scraper = CloudScraper()
    
    print("🌐 Testing Cloud Scraper (No sudo required)")
    
    # Test Eventbrite público
    print("\n📅 Testing Eventbrite public search...")
    events = await scraper.scrape_eventbrite_public("Buenos Aires")
    print(f"Found {len(events)} events")
    for event in events[:3]:
        print(f"  - {event.get('title', 'No title')}")
    
    # Test Instagram hashtag (sin login)
    print("\n📸 Testing Instagram hashtag (public)...")
    posts = await scraper.scrape_instagram_hashtag_api("buenosaires")
    print(f"Found {len(posts)} posts")
    for post in posts[:3]:
        print(f"  - {post.get('shortcode', 'No code')}: {post.get('likes', 0)} likes")
    
    # Test Facebook events (público)
    print("\n📘 Testing Facebook events (public)...")
    fb_events = await scraper.scrape_facebook_events_api("Buenos Aires")
    print(f"Found {len(fb_events)} events")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_cloud_scraper())