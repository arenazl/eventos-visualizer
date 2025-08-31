"""
Motor de Web Scraping para Redes Sociales
Utiliza Playwright para extraer eventos de Facebook e Instagram
Con técnicas anti-detección y manejo robusto de errores
"""

import asyncio
import json
import random
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SocialMediaScraper:
    """
    Motor principal para scraping de Facebook e Instagram
    Usa Playwright para máxima compatibilidad y anti-detección
    """
    
    def __init__(self, headless: bool = True, use_proxy: bool = False):
        self.headless = headless
        self.use_proxy = use_proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
        # User agents rotativos para evitar detección
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Configuración de proxy si está disponible
        self.proxy_config = None
        if use_proxy and os.getenv('PROXY_SERVER'):
            self.proxy_config = {
                'server': os.getenv('PROXY_SERVER'),
                'username': os.getenv('PROXY_USERNAME'),
                'password': os.getenv('PROXY_PASSWORD')
            }
    
    async def init(self):
        """
        Inicializa el browser con configuración anti-detección
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Configuración del browser
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--start-maximized'
                ]
            }
            
            # Agregar proxy si está configurado
            if self.proxy_config:
                launch_options['proxy'] = self.proxy_config
            
            # Usar Chromium para mejor compatibilidad
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Crear contexto con configuración realista
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent=random.choice(self.user_agents),
                locale='es-ES',
                timezone_id='America/Argentina/Buenos_Aires',
                geolocation={'longitude': -58.3816, 'latitude': -34.6037},
                permissions=['geolocation'],
                color_scheme='light'
            )
            
            # Agregar scripts para evitar detección
            await self.context.add_init_script("""
                // Ocultar propiedades de automatización
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Agregar chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Mock de plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock de idiomas
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-ES', 'es', 'en']
                });
                
                // Mock de vendor
                Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.'
                });
            """)
            
            logger.info("✅ Browser inicializado con anti-detección")
            
        except Exception as e:
            logger.error(f"Error inicializando browser: {e}")
            raise
    
    async def scrape_facebook_events(self, location: str = "Buenos Aires", max_events: int = 50) -> List[Dict]:
        """
        Scraping de eventos de Facebook para una ubicación
        """
        logger.info(f"📘 Scraping Facebook eventos en {location}")
        events = []
        page = None
        
        try:
            page = await self.context.new_page()
            
            # Headers adicionales para parecer más real
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Buscar eventos en Facebook
            search_url = f"https://www.facebook.com/events/search/?q={location.replace(' ', '%20')}"
            
            # Navegar con timeout largo
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            
            # Esperar random para parecer humano
            await self._random_wait(2, 5)
            
            # Scroll para cargar más eventos
            await self._scroll_to_load(page, max_scrolls=5)
            
            # Extraer eventos
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    
                    // Buscar elementos de eventos (los selectores cambian frecuentemente)
                    const eventElements = document.querySelectorAll('[role="article"], [data-testid*="event"], div[class*="event"]');
                    
                    eventElements.forEach((element) => {
                        try {
                            const event = {};
                            
                            // Título
                            const titleEl = element.querySelector('h2, h3, [role="heading"]');
                            if (titleEl) event.title = titleEl.innerText.trim();
                            
                            // Fecha
                            const dateEl = element.querySelector('[aria-label*="2025"], [aria-label*="2026"], [class*="date"]');
                            if (dateEl) event.date = dateEl.innerText.trim();
                            
                            // Ubicación
                            const locationEl = element.querySelector('[data-testid="event-venue"], [aria-label*="location"], [class*="location"]');
                            if (locationEl) event.location = locationEl.innerText.trim();
                            
                            // Link
                            const linkEl = element.querySelector('a[href*="/events/"]');
                            if (linkEl) event.url = linkEl.href;
                            
                            // Imagen
                            const imgEl = element.querySelector('img');
                            if (imgEl) event.image = imgEl.src;
                            
                            // Interesados
                            const interestedEl = element.querySelector('[aria-label*="people"], [aria-label*="personas"]');
                            if (interestedEl) event.interested = interestedEl.innerText.trim();
                            
                            // Solo agregar si tiene datos mínimos
                            if (event.title || event.url) {
                                event.platform = 'facebook';
                                event.scraped_at = new Date().toISOString();
                                events.push(event);
                            }
                        } catch (err) {
                            console.error('Error parsing event:', err);
                        }
                    });
                    
                    return events;
                }
            """)
            
            events = events_data[:max_events]
            logger.info(f"✅ Facebook: {len(events)} eventos encontrados en {location}")
            
        except Exception as e:
            logger.error(f"❌ Error scraping Facebook: {e}")
            
        finally:
            if page:
                await page.close()
        
        return events
    
    async def scrape_instagram_hashtag(self, hashtag: str, max_posts: int = 30) -> List[Dict]:
        """
        Scraping de posts de Instagram por hashtag
        """
        logger.info(f"📸 Scraping Instagram hashtag #{hashtag}")
        posts = []
        page = None
        
        try:
            page = await self.context.new_page()
            
            # Headers para Instagram
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            
            # URL del hashtag
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            
            # Navegar
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Esperar que cargue
            await self._random_wait(3, 6)
            
            # Scroll para cargar posts
            await self._scroll_to_load(page, max_scrolls=3)
            
            # Extraer posts
            posts_data = await page.evaluate("""
                () => {
                    const posts = [];
                    
                    // Buscar posts
                    const postElements = document.querySelectorAll('article a[href*="/p/"], div[role="button"] a[href*="/p/"]');
                    
                    postElements.forEach((element) => {
                        try {
                            const post = {};
                            
                            // URL del post
                            post.url = element.href;
                            
                            // ID del post
                            const match = element.href.match(/\/p\/([^\/]+)/);
                            if (match) post.id = match[1];
                            
                            // Imagen
                            const imgEl = element.querySelector('img');
                            if (imgEl) {
                                post.image = imgEl.src;
                                post.caption = imgEl.alt;
                            }
                            
                            // Tipo de media
                            const videoIcon = element.querySelector('[aria-label*="Video"], [aria-label*="Vídeo"]');
                            const carouselIcon = element.querySelector('[aria-label*="Carousel"], [aria-label*="Carrusel"]');
                            
                            if (videoIcon) {
                                post.type = 'video';
                            } else if (carouselIcon) {
                                post.type = 'carousel';
                            } else {
                                post.type = 'photo';
                            }
                            
                            post.hashtag = '" + hashtag + "';
                            post.platform = 'instagram';
                            post.scraped_at = new Date().toISOString();
                            
                            posts.push(post);
                        } catch (err) {
                            console.error('Error parsing post:', err);
                        }
                    });
                    
                    return posts;
                }
            """)
            
            posts = posts_data[:max_posts]
            logger.info(f"✅ Instagram: {len(posts)} posts encontrados para #{hashtag}")
            
        except Exception as e:
            logger.error(f"❌ Error scraping Instagram: {e}")
            
        finally:
            if page:
                await page.close()
        
        return posts
    
    async def scrape_instagram_profile(self, username: str, max_posts: int = 20) -> Dict:
        """
        Scraping de perfil de Instagram
        """
        logger.info(f"👤 Scraping Instagram perfil @{username}")
        profile_data = {'profile': {}, 'posts': []}
        page = None
        
        try:
            page = await self.context.new_page()
            
            # URL del perfil
            url = f"https://www.instagram.com/{username}/"
            
            # Navegar
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Esperar
            await self._random_wait(2, 5)
            
            # Extraer info del perfil
            profile_info = await page.evaluate("""
                () => {
                    const profile = {};
                    
                    // Username
                    const usernameEl = document.querySelector('h2');
                    if (usernameEl) profile.username = usernameEl.innerText.trim();
                    
                    // Bio
                    const bioEl = document.querySelector('h1 + div');
                    if (bioEl) profile.bio = bioEl.innerText.trim();
                    
                    // Stats
                    const statsEls = document.querySelectorAll('section ul li');
                    if (statsEls.length >= 3) {
                        profile.posts_count = statsEls[0].innerText.split(' ')[0];
                        profile.followers = statsEls[1].innerText.split(' ')[0];
                        profile.following = statsEls[2].innerText.split(' ')[0];
                    }
                    
                    // Avatar
                    const avatarEl = document.querySelector('img[alt*="profile"]');
                    if (avatarEl) profile.avatar = avatarEl.src;
                    
                    // Verified
                    profile.verified = !!document.querySelector('[title="Verified"]');
                    
                    return profile;
                }
            """)
            
            profile_data['profile'] = profile_info
            
            # Scroll para cargar posts
            await self._scroll_to_load(page, max_scrolls=2)
            
            # Extraer posts
            posts = await page.evaluate("""
                () => {
                    const posts = [];
                    
                    const postElements = document.querySelectorAll('article a[href*="/p/"]');
                    
                    postElements.forEach((element) => {
                        try {
                            const post = {};
                            
                            post.url = element.href;
                            
                            const imgEl = element.querySelector('img');
                            if (imgEl) {
                                post.image = imgEl.src;
                                post.alt = imgEl.alt;
                            }
                            
                            posts.push(post);
                        } catch (err) {
                            console.error('Error:', err);
                        }
                    });
                    
                    return posts;
                }
            """)
            
            profile_data['posts'] = posts[:max_posts]
            logger.info(f"✅ Instagram: Perfil @{username} - {len(posts)} posts")
            
        except Exception as e:
            logger.error(f"❌ Error scraping perfil Instagram: {e}")
            
        finally:
            if page:
                await page.close()
        
        return profile_data
    
    async def _scroll_to_load(self, page: Page, max_scrolls: int = 5):
        """
        Scroll para cargar más contenido
        """
        for i in range(max_scrolls):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self._random_wait(1, 3)
            logger.debug(f"📜 Scroll {i+1}/{max_scrolls}")
    
    async def _random_wait(self, min_seconds: float = 1, max_seconds: float = 3):
        """
        Espera aleatoria para parecer humano
        """
        wait_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(wait_time)
    
    async def close(self):
        """
        Cierra el browser
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔚 Browser cerrado")


# Función de prueba
async def test_social_scraper():
    """
    Prueba el scraper de redes sociales
    """
    scraper = SocialMediaScraper(headless=False)  # False para ver el browser
    
    try:
        await scraper.init()
        
        # Test Facebook
        print("\n🔍 Probando Facebook Events...")
        fb_events = await scraper.scrape_facebook_events("Buenos Aires", max_events=10)
        print(f"Encontrados {len(fb_events)} eventos")
        for event in fb_events[:3]:
            print(f"  - {event.get('title', 'Sin título')}")
            print(f"    📍 {event.get('location', 'Sin ubicación')}")
            print(f"    📅 {event.get('date', 'Sin fecha')}")
        
        # Test Instagram Hashtag
        print("\n🔍 Probando Instagram Hashtag...")
        ig_posts = await scraper.scrape_instagram_hashtag("buenosaires", max_posts=10)
        print(f"Encontrados {len(ig_posts)} posts")
        
        # Test Instagram Profile
        print("\n🔍 Probando Instagram Profile...")
        profile = await scraper.scrape_instagram_profile("turismobuenosaires", max_posts=5)
        print(f"Perfil: {profile['profile'].get('username')}")
        print(f"Followers: {profile['profile'].get('followers')}")
        print(f"Posts: {len(profile['posts'])}")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_social_scraper())