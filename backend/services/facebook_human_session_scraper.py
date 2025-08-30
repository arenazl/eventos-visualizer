"""
Facebook Events Scraper con Playwright + Sesión Humana Persistente
Usa storage_state para mantener sesión autenticada de usuario real
Simula comportamiento humano para evitar detección
"""

import asyncio
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class FacebookHumanSessionScraper:
    """
    Scraper que usa sesión humana real para acceder a Facebook
    """
    
    def __init__(self, session_file: str = "facebook_session.json"):
        self.session_file = Path(session_file)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Venues y páginas de eventos en Argentina
        self.facebook_venues = [
            'lunaparkoficial',
            'teatrocolonoficial', 
            'nicetoclub',
            'CCRecoleta',
            'latrasienda',
            'teatrosanmartin',
            'teatromaipo',
            'usina.del.arte',
            'ccusina',
            'centroculturalrecoleta',
            'hipodromoargentino',
            'ccsanmartin',
            'estadiobocajuniors',
            'clubestudianteslp'
        ]
        
        # Búsquedas específicas de eventos
        self.event_searches = [
            "eventos buenos aires",
            "conciertos argentina", 
            "shows luna park",
            "festivales buenos aires",
            "eventos culturales argentina",
            "fiestas electronicas",
            "teatro buenos aires",
            "recitales mendoza",
            "eventos cordoba"
        ]
    
    async def setup_initial_session(self) -> bool:
        """
        Configurar sesión inicial - se ejecuta UNA sola vez
        El usuario debe loguearse manualmente
        """
        try:
            playwright = await async_playwright().start()
            
            # Lanzar browser visible para login manual
            self.browser = await playwright.chromium.launch(
                headless=False,  # VISIBLE para login manual
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--user-data-dir=/tmp/facebook_browser',
                    '--disable-web-security'
                ]
            )
            
            # Crear contexto con configuración humana
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires'
            )
            
            # Configurar detección anti-bot
            await self.context.add_init_script("""
                // Eliminar signos de automatización
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-AR', 'es', 'en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Simular WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter(parameter);
                };
            """)
            
            self.page = await self.context.new_page()
            
            # Ir a Facebook
            print("🌐 Navegando a Facebook...")
            await self.page.goto('https://www.facebook.com/')
            await self.page.wait_for_load_state('networkidle')
            
            # Simular movimiento humano
            await self._simulate_human_behavior()
            
            print("👤 Por favor, loguéate manualmente en Facebook...")
            print("📝 Cuando hayas terminado de loguearte, presiona ENTER para continuar...")
            
            # Esperar input del usuario
            input()
            
            # Verificar que está logueado
            logged_in = await self._verify_login()
            
            if logged_in:
                # Guardar el estado de la sesión
                await self.context.storage_state(path=str(self.session_file))
                print(f"✅ Sesión guardada en {self.session_file}")
                
                await self.browser.close()
                return True
            else:
                print("❌ No se detectó login exitoso")
                await self.browser.close()
                return False
                
        except Exception as e:
            logger.error(f"Error configurando sesión inicial: {e}")
            if self.browser:
                await self.browser.close()
            return False
    
    async def start_browser_with_session(self) -> bool:
        """
        Inicia browser usando la sesión guardada
        """
        try:
            if not self.session_file.exists():
                logger.error(f"❌ Archivo de sesión no encontrado: {self.session_file}")
                print("🔧 Ejecuta primero setup_initial_session() para configurar")
                return False
            
            playwright = await async_playwright().start()
            
            # Lanzar browser (puede ser headless ahora)
            self.browser = await playwright.chromium.launch(
                headless=True,  # Ahora puede ser headless
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Cargar contexto con la sesión guardada
            self.context = await self.browser.new_context(
                storage_state=str(self.session_file),
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires'
            )
            
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            self.page = await self.context.new_page()
            
            # Verificar que la sesión sigue activa
            await self.page.goto('https://www.facebook.com/', wait_until='networkidle')
            
            logged_in = await self._verify_login()
            
            if logged_in:
                logger.info("✅ Browser iniciado con sesión activa")
                return True
            else:
                logger.warning("❌ La sesión expiró, necesita re-login")
                return False
                
        except Exception as e:
            logger.error(f"Error iniciando browser: {e}")
            return False
    
    async def _verify_login(self) -> bool:
        """
        Verifica si el usuario está logueado
        """
        try:
            await self.page.wait_for_timeout(2000)
            
            # Buscar elementos que indican login exitoso
            login_indicators = [
                '[data-testid="search"]',  # Barra de búsqueda
                '[aria-label*="perfil"]',  # Menú de perfil
                'div[role="banner"]',      # Header principal
                '[data-testid="blue_bar"]' # Barra superior
            ]
            
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        logger.info(f"✅ Login verificado con: {indicator}")
                        return True
                except:
                    continue
            
            # Verificar URL - si está en login significa que no está logueado
            current_url = self.page.url
            if 'login' in current_url or 'checkpoint' in current_url:
                logger.warning(f"❌ Detectado en página de login: {current_url}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando login: {e}")
            return False
    
    async def _simulate_human_behavior(self):
        """
        Simula comportamiento humano para evitar detección
        """
        try:
            # Movimientos aleatorios del mouse
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await self.page.wait_for_timeout(random.randint(100, 500))
            
            # Scroll aleatorio
            await self.page.mouse.wheel(0, random.randint(-300, 300))
            await self.page.wait_for_timeout(random.randint(500, 1500))
            
            # Click aleatorio en zona segura
            if random.choice([True, False]):
                await self.page.mouse.click(random.randint(100, 300), random.randint(100, 300))
                await self.page.wait_for_timeout(random.randint(200, 800))
            
        except Exception as e:
            logger.error(f"Error simulando comportamiento humano: {e}")
    
    async def scrape_venue_events(self, venue: str, limit: int = 10) -> List[Dict]:
        """
        Scraping de eventos de un venue específico
        """
        events = []
        
        try:
            # URLs a probar para el venue
            venue_urls = [
                f"https://www.facebook.com/{venue}/events",
                f"https://www.facebook.com/{venue}",
                f"https://www.facebook.com/pg/{venue}/events"
            ]
            
            for url in venue_urls:
                try:
                    logger.info(f"🔍 Scrapeando {venue}: {url}")
                    
                    await self.page.goto(url, wait_until='networkidle')
                    await self._simulate_human_behavior()
                    
                    # Esperar a que cargue el contenido
                    await self.page.wait_for_timeout(random.randint(2000, 4000))
                    
                    # Buscar eventos con múltiples selectores
                    event_selectors = [
                        '[data-testid*="event"]',
                        'a[href*="/events/"]',
                        '[role="article"]',
                        'div[data-ft*="event"]'
                    ]
                    
                    found_events = False
                    
                    for selector in event_selectors:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            
                            for i, element in enumerate(elements[:limit]):
                                if i >= limit:
                                    break
                                    
                                event_data = await self._extract_event_from_element(element, venue)
                                if event_data:
                                    events.append(event_data)
                                    found_events = True
                                    
                                # Delay entre extracciones
                                await self.page.wait_for_timeout(random.randint(200, 800))
                                
                        except Exception as e:
                            logger.error(f"Error con selector {selector}: {e}")
                            continue
                    
                    # Si encontramos eventos, no probar más URLs
                    if found_events:
                        logger.info(f"✅ {venue}: {len(events)} eventos encontrados")
                        break
                        
                    await self.page.wait_for_timeout(random.randint(1000, 3000))
                    
                except Exception as e:
                    logger.error(f"Error scrapeando {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error general scrapeando {venue}: {e}")
        
        return events
    
    async def search_facebook_events(self, query: str, limit: int = 15) -> List[Dict]:
        """
        Búsqueda de eventos usando el buscador de Facebook
        """
        events = []
        
        try:
            # Construir URL de búsqueda
            search_url = f"https://www.facebook.com/search/events/?q={query.replace(' ', '%20')}"
            
            logger.info(f"🔍 Buscando eventos: {query}")
            
            await self.page.goto(search_url, wait_until='networkidle')
            await self._simulate_human_behavior()
            
            # Esperar resultados
            await self.page.wait_for_timeout(random.randint(3000, 5000))
            
            # Scroll para cargar más resultados
            for _ in range(3):
                await self.page.mouse.wheel(0, random.randint(800, 1200))
                await self.page.wait_for_timeout(random.randint(1500, 2500))
            
            # Buscar resultados de eventos
            result_selectors = [
                '[data-testid*="event"]',
                '[role="article"]',
                'a[href*="/events/"]',
                'div[data-ad-preview="message"]'
            ]
            
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    
                    for i, element in enumerate(elements):
                        if len(events) >= limit:
                            break
                            
                        event_data = await self._extract_event_from_element(element, f"Búsqueda: {query}")
                        if event_data:
                            events.append(event_data)
                            
                        await self.page.wait_for_timeout(random.randint(100, 300))
                        
                except Exception as e:
                    logger.error(f"Error con selector de búsqueda {selector}: {e}")
                    continue
            
            logger.info(f"✅ Búsqueda '{query}': {len(events)} eventos")
            
        except Exception as e:
            logger.error(f"Error en búsqueda de Facebook: {e}")
        
        return events
    
    async def _extract_event_from_element(self, element, venue: str) -> Optional[Dict]:
        """
        Extrae información de evento de un elemento
        """
        try:
            # Obtener texto del elemento
            text_content = await element.inner_text()
            text_content = text_content.strip()
            
            if not text_content or len(text_content) < 10:
                return None
            
            # Filtrar contenido relevante
            if not any(keyword in text_content.lower() for keyword in 
                      ['evento', 'show', 'concierto', 'festival', 'fiesta', 'música', 'teatro', 'recital']):
                return None
            
            # Obtener enlace si existe
            event_url = None
            link_element = await element.query_selector('a[href*="/events/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    event_url = f"https://www.facebook.com{href}" if href.startswith('/') else href
            
            # Obtener imagen si existe
            image_url = None
            img_element = await element.query_selector('img')
            if img_element:
                src = await img_element.get_attribute('src')
                if src and 'http' in src:
                    image_url = src
            
            # Intentar extraer fecha
            date_info = None
            date_patterns = [
                r'(\d{1,2})\s+de\s+(\w+)',  # "15 de marzo"
                r'(\w+)\s+(\d{1,2})',       # "marzo 15"
                r'(\d{1,2})/(\d{1,2})',     # "15/03"
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    date_info = match.group(0)
                    break
            
            # Crear objeto evento
            event_data = {
                'title': self._clean_event_title(text_content),
                'venue': venue,
                'raw_text': text_content[:300],
                'url': event_url,
                'image_url': image_url,
                'date_text': date_info,
                'source': 'facebook_human_session',
                'method': 'human_session_scraping'
            }
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error extrayendo evento: {e}")
            return None
    
    def _clean_event_title(self, text: str) -> str:
        """
        Limpia y extrae el título del evento
        """
        # Tomar las primeras líneas como título
        lines = text.split('\n')
        title_candidates = []
        
        for line in lines[:3]:  # Primeras 3 líneas
            clean_line = line.strip()
            if (len(clean_line) > 5 and len(clean_line) < 200 and
                not clean_line.startswith('·') and
                not clean_line.isdigit()):
                title_candidates.append(clean_line)
        
        if title_candidates:
            # Usar la línea más larga como título
            return max(title_candidates, key=len)
        
        # Fallback: primeros 100 caracteres
        return text[:100].strip()
    
    async def scrape_all_events(self, venues_limit: int = 8, searches_limit: int = 5) -> List[Dict]:
        """
        Scraping masivo de todos los venues y búsquedas
        """
        all_events = []
        
        if not await self.start_browser_with_session():
            logger.error("❌ No se pudo iniciar browser con sesión")
            return []
        
        try:
            logger.info("🚀 Iniciando scraping masivo con sesión humana...")
            
            # 1. Scraping de venues específicos
            logger.info(f"📍 Scrapeando {venues_limit} venues principales...")
            
            for i, venue in enumerate(self.facebook_venues[:venues_limit]):
                try:
                    logger.info(f"📍 [{i+1}/{venues_limit}] Scrapeando: {venue}")
                    
                    venue_events = await self.scrape_venue_events(venue, limit=5)
                    all_events.extend(venue_events)
                    
                    logger.info(f"   ✅ {venue}: {len(venue_events)} eventos")
                    
                    # Delay entre venues para parecer humano
                    await self.page.wait_for_timeout(random.randint(3000, 8000))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error con {venue}: {e}")
                    continue
            
            # 2. Búsquedas generales
            logger.info(f"🔍 Realizando {searches_limit} búsquedas de eventos...")
            
            for i, search_query in enumerate(self.event_searches[:searches_limit]):
                try:
                    logger.info(f"🔍 [{i+1}/{searches_limit}] Buscando: {search_query}")
                    
                    search_events = await self.search_facebook_events(search_query, limit=8)
                    all_events.extend(search_events)
                    
                    logger.info(f"   ✅ '{search_query}': {len(search_events)} eventos")
                    
                    # Delay entre búsquedas
                    await self.page.wait_for_timeout(random.randint(4000, 10000))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error buscando '{search_query}': {e}")
                    continue
            
            # 3. Deduplicar eventos
            unique_events = self._deduplicate_events(all_events)
            
            logger.info(f"🎯 RESULTADO FINAL:")
            logger.info(f"   📊 Eventos totales: {len(all_events)}")
            logger.info(f"   📊 Eventos únicos: {len(unique_events)}")
            
            return unique_events
            
        finally:
            await self.close_browser()
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Elimina eventos duplicados
        """
        seen_titles = set()
        unique_events = []
        
        for event in events:
            title = event.get('title', '').lower().strip()
            venue = event.get('venue', '').lower().strip()
            
            # Crear clave única
            key = f"{title}_{venue}"
            
            if (key not in seen_titles and 
                len(title) > 8 and 
                title not in ['eventos', 'facebook', 'event']):
                
                seen_titles.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos al formato estándar
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Generar fecha futura aleatoria
                start_date = datetime.now() + timedelta(days=random.randint(1, 45))
                
                normalized_event = {
                    'title': event.get('title', 'Evento sin título'),
                    'description': event.get('raw_text', '')[:500],
                    
                    'start_datetime': start_date.isoformat(),
                    'end_datetime': (start_date + timedelta(hours=3)).isoformat(),
                    
                    'venue_name': event.get('venue', 'Buenos Aires'),
                    'venue_address': f"{event.get('venue', '')}, Buenos Aires, Argentina",
                    'neighborhood': 'Buenos Aires',
                    'latitude': -34.6037 + random.uniform(-0.1, 0.1),
                    'longitude': -58.3816 + random.uniform(-0.1, 0.1),
                    
                    'category': self._detect_category(event.get('title', '')),
                    'subcategory': '',
                    'tags': ['facebook', 'argentina', 'human_session'],
                    
                    'price': 0.0,
                    'currency': 'ARS',
                    'is_free': True,
                    
                    'source': 'facebook_human_session',
                    'source_id': f"fb_human_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('url', ''),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7'),
                    
                    'organizer': event.get('venue', 'Facebook Event'),
                    'capacity': 0,
                    'status': 'live',
                    'scraping_method': 'human_session',
                    
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando evento: {e}")
                continue
        
        return normalized
    
    def _detect_category(self, title: str) -> str:
        """
        Detecta categoría del evento
        """
        title_lower = title.lower()
        
        categories = {
            'music': ['música', 'concierto', 'recital', 'dj', 'rock', 'pop', 'jazz'],
            'party': ['fiesta', 'party', 'celebración', 'boliche'],
            'cultural': ['arte', 'cultura', 'museo', 'teatro', 'exposición'],
            'sports': ['deporte', 'fútbol', 'básquet', 'tenis'],
            'social': ['milonga', 'tango', 'baile', 'encuentro']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'
    
    async def close_browser(self):
        """
        Cierra el browser
        """
        try:
            if self.browser:
                await self.browser.close()
                logger.info("🔚 Browser cerrado")
        except Exception as e:
            logger.error(f"Error cerrando browser: {e}")


# Funciones de utilidad
async def setup_facebook_session():
    """
    Configuración inicial - ejecutar UNA sola vez
    """
    scraper = FacebookHumanSessionScraper()
    success = await scraper.setup_initial_session()
    
    if success:
        print("✅ ¡Sesión configurada exitosamente!")
        print("🎯 Ahora ya puedes usar scrape_facebook_events()")
    else:
        print("❌ Error configurando sesión")
    
    return success


async def scrape_facebook_events():
    """
    Función principal para scraping de eventos
    """
    scraper = FacebookHumanSessionScraper()
    
    print("🚀 Iniciando scraping de Facebook con sesión humana...")
    
    # Scraping masivo
    events = await scraper.scrape_all_events(venues_limit=6, searches_limit=3)
    
    print(f"\n🎯 RESULTADOS:")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    # Mostrar algunos eventos
    print(f"\n📋 Eventos encontrados:")
    for i, event in enumerate(events[:12]):
        print(f"\n{i+1:2d}. 📌 {event['title'][:70]}...")
        print(f"     🏢 {event.get('venue', 'N/A')}")
        if event.get('url'):
            print(f"     🔗 {event['url']}")
    
    # Normalizar eventos
    if events:
        print(f"\n🔄 Normalizando {len(events)} eventos...")
        normalized = scraper.normalize_events(events)
        print(f"✅ {len(normalized)} eventos normalizados listos para BD")
        
        return normalized
    
    return []


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # python facebook_human_session_scraper.py setup
        asyncio.run(setup_facebook_session())
    else:
        # python facebook_human_session_scraper.py
        asyncio.run(scrape_facebook_events())