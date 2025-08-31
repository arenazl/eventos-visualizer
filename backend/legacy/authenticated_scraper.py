"""
Authenticated Social Media Scraper
Usa login con usuario/contraseña para acceder a más contenido
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

class AuthenticatedScraper:
    """
    Scraper con capacidad de login para Facebook e Instagram
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
        
        # Headers más realistas
        self.scraper.headers.update({
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        })
        
        self.logged_in_facebook = False
        self.logged_in_instagram = False
    
    async def login_facebook(self, email: str, password: str) -> bool:
        """
        Login a Facebook para acceder a más eventos
        """
        try:
            print("🔑 Intentando login a Facebook...")
            
            # 1. Obtener página de login
            login_url = "https://www.facebook.com/login"
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.get, login_url
            )
            
            if response.status_code != 200:
                logger.error(f"No se pudo cargar página de login: {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2. Buscar formulario de login
            form = soup.find('form', {'id': 'login_form'}) or soup.find('form', {'method': 'post'})
            if not form:
                logger.error("No se encontró formulario de login")
                return False
            
            # 3. Extraer campos ocultos
            hidden_fields = {}
            for hidden in form.find_all('input', {'type': 'hidden'}):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    hidden_fields[name] = value
            
            # 4. Preparar datos de login
            login_data = {
                'email': email,
                'pass': password,
                **hidden_fields
            }
            
            # 5. Enviar login
            post_url = form.get('action') or login_url
            if not post_url.startswith('http'):
                post_url = f"https://www.facebook.com{post_url}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.scraper.post(post_url, data=login_data, allow_redirects=True)
            )
            
            # 6. Verificar login exitoso
            if "login" not in response.url and "checkpoint" not in response.url:
                self.logged_in_facebook = True
                print("✅ Login a Facebook exitoso")
                return True
            else:
                logger.warning("Login falló - posible 2FA o credenciales incorrectas")
                return False
                
        except Exception as e:
            logger.error(f"Error en login Facebook: {e}")
            return False
    
    async def scrape_facebook_events_authenticated(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Scraping de eventos con sesión autenticada
        """
        events = []
        
        if not self.logged_in_facebook:
            logger.warning("No hay sesión de Facebook activa")
            return events
        
        try:
            # URLs de búsqueda de eventos autenticadas
            search_urls = [
                f"https://www.facebook.com/events/search/?q={location}",
                f"https://www.facebook.com/events/discovery/?location={location}",
                "https://www.facebook.com/events/feed/",
                "https://www.facebook.com/events/discovery/"
            ]
            
            for url in search_urls[:2]:
                try:
                    print(f"🔍 Buscando eventos en: {url}")
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.scraper.get, url
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar eventos en diferentes formatos
                        event_containers = soup.find_all(['div', 'article'], 
                            attrs={'data-testid': lambda x: x and 'event' in x.lower() if x else False})
                        
                        if not event_containers:
                            # Buscar por clases comunes de eventos
                            event_containers = soup.find_all('div', class_=re.compile('event|Event'))
                        
                        print(f"📦 Encontrados {len(event_containers)} contenedores de eventos")
                        
                        for container in event_containers[:10]:
                            event = self._extract_facebook_event(container)
                            if event:
                                events.append(event)
                                print(f"  ✅ {event['title'][:50]}...")
                    
                    await asyncio.sleep(2)  # Anti-detección
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error en scraping autenticado Facebook: {e}")
        
        return events
    
    async def login_instagram(self, username: str, password: str) -> bool:
        """
        Login a Instagram para acceder a más contenido
        """
        try:
            print("🔑 Intentando login a Instagram...")
            
            # 1. Obtener página de login
            login_url = "https://www.instagram.com/accounts/login/"
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.get, login_url
            )
            
            if response.status_code != 200:
                logger.error(f"No se pudo cargar Instagram login: {response.status_code}")
                return False
            
            # 2. Extraer csrftoken
            csrf_token = None
            cookies = response.cookies
            for cookie in cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if not csrf_token:
                # Buscar en HTML
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            if not csrf_token:
                logger.error("No se pudo obtener CSRF token")
                return False
            
            # 3. Preparar datos de login
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            }
            
            # 4. Headers para login
            login_headers = {
                'referer': 'https://www.instagram.com/accounts/login/',
                'x-csrftoken': csrf_token,
                'x-requested-with': 'XMLHttpRequest',
            }
            
            # 5. Enviar login
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.scraper.post(
                    "https://www.instagram.com/accounts/login/ajax/",
                    data=login_data,
                    headers=login_headers,
                    allow_redirects=False
                )
            )
            
            # 6. Verificar login
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('authenticated'):
                        self.logged_in_instagram = True
                        print("✅ Login a Instagram exitoso")
                        return True
                except:
                    pass
            
            logger.warning("Login a Instagram falló")
            return False
            
        except Exception as e:
            logger.error(f"Error en login Instagram: {e}")
            return False
    
    async def scrape_instagram_events_authenticated(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Scraping de posts de eventos con sesión autenticada
        """
        events = []
        
        if not self.logged_in_instagram:
            logger.warning("No hay sesión de Instagram activa")
            return events
        
        try:
            # Hashtags de eventos en Argentina
            hashtags = [
                'eventosba', 'eventsbuenosaires', 'eventosargentina', 
                'recitalba', 'fiestasbuenosaires', 'showsba',
                'eventosmendoza', 'eventoscordoba'
            ]
            
            for hashtag in hashtags[:3]:
                try:
                    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
                    print(f"🔍 Buscando en #{hashtag}")
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.scraper.get, url
                    )
                    
                    if response.status_code == 200:
                        # Buscar JSON embebido
                        script_pattern = r'window\._sharedData\s*=\s*({.+?});'
                        match = re.search(script_pattern, response.text)
                        
                        if match:
                            data = json.loads(match.group(1))
                            posts = self._extract_instagram_posts(data, hashtag)
                            events.extend(posts)
                            print(f"  📦 {len(posts)} posts de eventos")
                    
                    await asyncio.sleep(3)  # Anti-detección
                    
                except Exception as e:
                    logger.error(f"Error scraping #{hashtag}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error en scraping autenticado Instagram: {e}")
        
        return events
    
    def _extract_facebook_event(self, container) -> Optional[Dict]:
        """
        Extrae información de evento de Facebook
        """
        try:
            # Buscar título
            title_elem = container.find(['h3', 'h2', 'strong', 'span'], 
                string=lambda x: x and len(x.strip()) > 5)
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Buscar fecha
            date_elem = container.find(['time', 'span'], 
                string=lambda x: x and any(month in x.lower() for month in ['ene', 'feb', 'mar', 'abr', 'may', 'jun']))
            
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # Buscar ubicación
            location_elem = container.find(['span', 'div'], 
                string=lambda x: x and any(word in x.lower() for word in ['teatro', 'club', 'centro', 'sala']))
            
            location = location_elem.get_text(strip=True) if location_elem else "Buenos Aires"
            
            return {
                'title': title,
                'description': f"Evento en {location}",
                'venue_name': location,
                'venue_address': f"{location}, Buenos Aires",
                'source': 'facebook_authenticated',
                'start_datetime': date_str,
                'price': 0,
                'is_free': True
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo evento Facebook: {e}")
            return None
    
    def _extract_instagram_posts(self, data: Dict, hashtag: str) -> List[Dict]:
        """
        Extrae posts de eventos de datos JSON de Instagram
        """
        events = []
        
        try:
            # Navegar a los posts del hashtag
            tag_data = data.get('entry_data', {}).get('TagPage', [{}])[0]
            posts = tag_data.get('graphql', {}).get('hashtag', {}).get('edge_hashtag_to_media', {}).get('edges', [])
            
            event_keywords = ['evento', 'fiesta', 'show', 'recital', 'festival', 'concierto', 'teatro', 'danza']
            
            for post in posts:
                try:
                    node = post.get('node', {})
                    caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                    
                    if caption_edges:
                        caption = caption_edges[0].get('node', {}).get('text', '')
                        
                        # Verificar si es un evento
                        if any(keyword in caption.lower() for keyword in event_keywords):
                            title = self._extract_title_from_caption(caption)
                            
                            events.append({
                                'title': title,
                                'description': caption[:200],
                                'source': 'instagram_authenticated',
                                'image_url': node.get('display_url', ''),
                                'likes': node.get('edge_liked_by', {}).get('count', 0),
                                'hashtag': hashtag,
                                'event_url': f"https://www.instagram.com/p/{node.get('shortcode')}/",
                                'price': 0,
                                'is_free': True
                            })
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error extrayendo posts Instagram: {e}")
        
        return events
    
    def _extract_title_from_caption(self, caption: str) -> str:
        """
        Extrae título del caption de Instagram
        """
        lines = caption.split('\n')
        first_line = lines[0].strip()
        
        # Limpiar emojis y caracteres especiales
        title = re.sub(r'[^\w\s\-\.,!?]', '', first_line)
        
        return title[:100] if title else "Evento de Instagram"
    
    async def fetch_all_authenticated_events(self, location: str = "Buenos Aires", 
                                           fb_email: str = None, fb_password: str = None,
                                           ig_username: str = None, ig_password: str = None) -> List[Dict]:
        """
        Obtiene eventos usando login en ambas plataformas
        """
        all_events = []
        
        # Login Facebook
        if fb_email and fb_password:
            logged_in = await self.login_facebook(fb_email, fb_password)
            if logged_in:
                fb_events = await self.scrape_facebook_events_authenticated(location)
                all_events.extend(fb_events)
                print(f"✅ Facebook autenticado: {len(fb_events)} eventos")
        
        # Login Instagram  
        if ig_username and ig_password:
            logged_in = await self.login_instagram(ig_username, ig_password)
            if logged_in:
                ig_events = await self.scrape_instagram_events_authenticated(location)
                all_events.extend(ig_events)
                print(f"✅ Instagram autenticado: {len(ig_events)} eventos")
        
        return all_events


# Testing
async def test_authenticated_scraper():
    """
    Prueba con credenciales (usar credenciales reales)
    """
    scraper = AuthenticatedScraper()
    
    print("🔐 Testing Authenticated Scraper")
    print("⚠️  IMPORTANTE: Necesitas credenciales reales para probar")
    
    # Usar variables de entorno para credenciales
    fb_email = os.getenv('FACEBOOK_EMAIL')
    fb_password = os.getenv('FACEBOOK_PASSWORD')
    ig_username = os.getenv('INSTAGRAM_USERNAME') 
    ig_password = os.getenv('INSTAGRAM_PASSWORD')
    
    events = await scraper.fetch_all_authenticated_events(
        location="Buenos Aires",
        fb_email=fb_email,
        fb_password=fb_password,
        ig_username=ig_username,
        ig_password=ig_password
    )
    
    print(f"\n🎉 Total eventos autenticados: {len(events)}")
    for event in events[:5]:
        print(f"📍 {event['title']} - {event['source']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_authenticated_scraper())