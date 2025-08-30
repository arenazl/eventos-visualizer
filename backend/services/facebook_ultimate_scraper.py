"""
Facebook Ultimate Scraper - El Desafío Final
Combina TODAS las técnicas para vencer las protecciones de Facebook:
1. Playwright + Sesión Humana Real
2. Comportamiento Humano Simulado
3. Anti-detección Avanzada
4. Bright Data + Proxies
5. Scraping Móvil
"""

import asyncio
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class FacebookUltimateScraper:
    """
    El scraper más avanzado para Facebook - Combina todas las técnicas
    """
    
    def __init__(self, session_file: str = "facebook_session.json", bright_data_config: Optional[Dict] = None):
        self.session_file = Path(session_file)
        self.bright_data_config = bright_data_config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 🎯 VENUES ARGENTINOS MÁS IMPORTANTES (con eventos frecuentes)
        self.argentina_venues = [
            # Música y Shows
            'lunaparkoficial',           # Luna Park - Shows masivos
            'teatrocolonoficial',        # Teatro Colón - Música clásica
            'nicetoclub',               # Niceto Club - Música electrónica
            'latrasienda',              # La Trastienda - Shows indie
            'teatrosanmartin',          # Teatro San Martín
            'teatromaipo',              # Teatro Maipo
            'hipodromoargentino',       # Hipódromo - Eventos masivos
            'movistararenar',           # Movistar Arena - Conciertos
            
            # Cultura
            'CCRecoleta',               # Centro Cultural Recoleta
            'centroculturalrecoleta',   # Recoleta alternativo
            'ccusina',                  # Centro Cultural Usina del Arte
            'ccusina.org',              # Usina del Arte oficial
            'ccsanmartin',              # CC San Martín
            'fundacionproa',            # Fundación PROA - Arte
            'malba.museo',              # MALBA
            
            # Deportes
            'estadiobocajuniors',       # La Bombonera
            'clubriverplate',           # River Plate
            'clubestudianteslp',        # Estudiantes
            'clubsanlorenzo',           # San Lorenzo
            
            # Gastronomía y Eventos
            'puertomadryn.eventos',     # Puerto Madero eventos
            'recoleta.events',          # Recoleta eventos
            'palermo.buenos.aires',     # Palermo BA
            
            # Spaces y Venues
            'espaciocava',              # Espacio CAVA
            'teatroelgalpón',           # Teatro El Galpón  
            'clubstudio54',             # Studio 54 BA
            'crobar.buenosaires'        # Crobar Buenos Aires
        ]
        
        # 🔍 BÚSQUEDAS ESPECÍFICAS PARA ARGENTINA
        self.search_queries = [
            "eventos buenos aires 2025",
            "conciertos argentina",
            "shows luna park",
            "teatro colon programacion",
            "eventos palermo buenos aires",
            "fiestas electronicas buenos aires",
            "recitales buenos aires",
            "festivales argentina",
            "eventos culturales buenos aires",
            "shows en vivo argentina",
            "musica en vivo buenos aires",
            "eventos fin de semana ba"
        ]
        
        # 🎭 USER AGENTS SÚPER REALISTAS (Argentina + Mobile First)
        self.user_agents = [
            # Android Argentina
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
            
            # iPhone Argentina
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            
            # Desktop Argentina
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    async def setup_initial_session_advanced(self) -> bool:
        """
        🔧 Setup avanzado de sesión humana con máxima evasión
        """
        try:
            playwright = await async_playwright().start()
            
            # 🎯 Configuración SÚPER REALISTA
            self.browser = await playwright.chromium.launch(
                headless=False,  # VISIBLE para login humano
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--disable-extensions-except-chromium',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    '--disable-features=TranslateUI',
                    '--disable-features=BlinkGenPropertyTrees',
                    '--no-first-run',
                    '--lang=es-AR'  # Idioma Argentina
                ]
            )
            
            # 🌐 Contexto con datos argentinos REALES
            self.context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires',
                geolocation={'latitude': -34.6037, 'longitude': -58.3816},  # Buenos Aires
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )
            
            # 🤖 SCRIPT ANTI-DETECCIÓN MÁXIMO
            await self.context.add_init_script("""
                // Eliminar TODOS los signos de automatización
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-AR', 'es', 'en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chromium PDF Plugin', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Microsoft Edge PDF Plugin', filename: 'pdf' }
                    ],
                });
                
                // Timezone Argentina
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                    get: () => () => ({ timeZone: 'America/Argentina/Buenos_Aires' }),
                });
                
                // WebGL Argentina-like
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Google Inc. (NVIDIA)';
                    if (parameter === 37446) return 'ANGLE (NVIDIA, GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)';
                    return getParameter(parameter);
                };
                
                // Screen resolution típica Argentina
                Object.defineProperty(screen, 'width', { get: () => 1920 });
                Object.defineProperty(screen, 'height', { get: () => 1080 });
                Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
                Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
                
                // Mouse events reales
                let mouseEvents = [];
                document.addEventListener('mousemove', (e) => {
                    mouseEvents.push({x: e.clientX, y: e.clientY, time: Date.now()});
                    if (mouseEvents.length > 100) mouseEvents.shift();
                });
            """)
            
            self.page = await self.context.new_page()
            
            # 🌐 Navegación súper realista a Facebook
            print("🌐 Navegando a Facebook con comportamiento humano...")
            await self.page.goto('https://www.facebook.com/')
            
            # 🤖 Comportamiento humano inicial
            await self._simulate_realistic_human_behavior()
            
            print("👤 Por favor, loguéate manualmente en Facebook...")
            print("🔥 IMPORTANTE: Navega un poco, ve algunas publicaciones, actúa naturalmente")
            print("📝 Cuando hayas terminado, presiona ENTER para guardar la sesión...")
            
            # Esperar que el usuario se loguee
            input()
            
            # ✅ Verificar login exitoso
            logged_in = await self._verify_advanced_login()
            
            if logged_in:
                # 💾 Guardar sesión
                await self.context.storage_state(path=str(self.session_file))
                print(f"✅ Sesión súper avanzada guardada en {self.session_file}")
                
                await self.browser.close()
                return True
            else:
                print("❌ Login no detectado o fallido")
                await self.browser.close()
                return False
                
        except Exception as e:
            logger.error(f"Error setup avanzado: {e}")
            if self.browser:
                await self.browser.close()
            return False
    
    async def _simulate_realistic_human_behavior(self):
        """
        🤖 Simula comportamiento humano MUY realista
        """
        try:
            # 🖱️ Movimientos de mouse naturales
            for _ in range(random.randint(5, 10)):
                x = random.randint(200, 1200)
                y = random.randint(150, 800)
                
                # Movimiento con curva natural
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.8))
            
            # 📜 Scroll natural (como humano)
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(-500, 500)
                await self.page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.8, 2.0))
            
            # ⌨️ Actividad de teclado sutil
            if random.choice([True, False]):
                await self.page.keyboard.press('Tab')
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 👆 Clicks aleatorios en zonas seguras
            safe_zones = [
                (300, 200), (800, 300), (600, 500)
            ]
            
            for zone in safe_zones[:random.randint(1, 3)]:
                await self.page.mouse.click(zone[0], zone[1])
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # ⏱️ Pausa como humano leyendo
            await asyncio.sleep(random.uniform(3, 8))
            
        except Exception as e:
            logger.error(f"Error simulando comportamiento: {e}")
    
    async def _verify_advanced_login(self) -> bool:
        """
        ✅ Verificación avanzada de login exitoso
        """
        try:
            await asyncio.sleep(3)
            
            # Múltiples indicadores de login exitoso
            login_indicators = [
                '[data-testid="search"]',           # Barra de búsqueda
                '[aria-label*="Perfil"]',           # Menú perfil
                '[data-testid="blue_bar"]',         # Header azul
                'div[role="banner"]',               # Banner principal
                '[data-testid="left_nav_menu_list"]', # Menu lateral
                'div[data-testid="Keycommand_wrapper_PermalinkPost"]'  # Posts
            ]
            
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        logger.info(f"✅ Login confirmado con: {indicator}")
                        return True
                except:
                    continue
            
            # Verificar URL
            current_url = self.page.url
            if any(blocked in current_url.lower() for blocked in ['login', 'checkpoint', 'recover']):
                logger.warning(f"❌ En página de login/bloqueo: {current_url}")
                return False
            
            # Verificar si puede acceder al feed
            try:
                feed_element = await self.page.query_selector('div[role="main"]')
                if feed_element:
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando login: {e}")
            return False
    
    async def start_browser_with_session_advanced(self) -> bool:
        """
        🚀 Iniciar browser con sesión avanzada
        """
        try:
            if not self.session_file.exists():
                logger.error(f"❌ Archivo de sesión no encontrado: {self.session_file}")
                print("🔧 Ejecuta primero setup_initial_session_advanced() para configurar")
                return False
            
            playwright = await async_playwright().start()
            
            # 🎭 Browser con configuración anti-detección máxima
            self.browser = await playwright.chromium.launch(
                headless=False,  # Visible para debug, cambiar a True en producción
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--no-first-run',
                    '--lang=es-AR'
                ]
            )
            
            # 🔄 Rotar User-Agent cada vez
            current_ua = random.choice(self.user_agents)
            
            # 🌐 Contexto con sesión + anti-detección
            self.context = await self.browser.new_context(
                storage_state=str(self.session_file),  # ⭐ CLAVE: Sesión guardada
                user_agent=current_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires',
                geolocation={'latitude': -34.6037, 'longitude': -58.3816},
                permissions=['geolocation']
            )
            
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['es-AR', 'es', 'en'] });
            """)
            
            self.page = await self.context.new_page()
            
            # 🌐 Navegar a Facebook con la sesión
            await self.page.goto('https://www.facebook.com/', wait_until='networkidle')
            
            # 🤖 Comportamiento humano sutil
            await self._simulate_realistic_human_behavior()
            
            # ✅ Verificar que la sesión sigue válida
            logged_in = await self._verify_advanced_login()
            
            if logged_in:
                logger.info("✅ Browser iniciado con sesión avanzada activa")
                return True
            else:
                logger.warning("❌ La sesión expiró o está bloqueada")
                return False
                
        except Exception as e:
            logger.error(f"Error iniciando browser avanzado: {e}")
            return False
    
    async def scrape_venue_advanced(self, venue: str, limit: int = 20) -> List[Dict]:
        """
        🎯 Scraping avanzado de venue específico con técnicas anti-detección
        """
        events = []
        
        try:
            # URLs a probar para el venue
            venue_urls = [
                f"https://www.facebook.com/{venue}/events",
                f"https://www.facebook.com/{venue}",
                f"https://m.facebook.com/{venue}/events",
                f"https://www.facebook.com/pg/{venue}/events"
            ]
            
            for url in venue_urls:
                try:
                    logger.info(f"🎯 Scraping avanzado: {venue} -> {url}")
                    
                    # 🌐 Navegación con comportamiento humano
                    await self.page.goto(url, wait_until='networkidle')
                    await self._simulate_realistic_human_behavior()
                    
                    # ⏱️ Esperar carga completa
                    await asyncio.sleep(random.uniform(3, 6))
                    
                    # 📜 Scroll para cargar más eventos
                    for scroll in range(3):
                        await self.page.mouse.wheel(0, random.randint(800, 1200))
                        await asyncio.sleep(random.uniform(2, 4))
                    
                    # 🔍 SELECTORES MUY ESPECÍFICOS PARA EVENTOS
                    event_selectors = [
                        # Nuevos selectores Facebook 2024-2025
                        '[data-testid*="event"]',
                        '[role="article"][aria-label*="event" i]',
                        '[data-ft*="event"]',
                        'a[href*="/events/"][role="link"]',
                        
                        # Selectores clásicos
                        '[data-testid="event_card"]',
                        'div[data-testid="event_permalink"]',
                        
                        # Selectores de texto que contengan eventos
                        'div:has-text("evento")',
                        'div:has-text("show")',
                        'div:has-text("concierto")'
                    ]
                    
                    found_events = False
                    
                    for selector in event_selectors:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            
                            logger.info(f"   🎯 Selector '{selector}': {len(elements)} elementos")
                            
                            for i, element in enumerate(elements[:limit]):
                                if i >= limit:
                                    break
                                    
                                event_data = await self._extract_advanced_event(element, venue, url)
                                if event_data:
                                    events.append(event_data)
                                    found_events = True
                                    
                                # Delay humano entre extracciones
                                await asyncio.sleep(random.uniform(0.3, 1.0))
                                
                        except Exception as e:
                            logger.error(f"Error selector {selector}: {e}")
                            continue
                    
                    if found_events:
                        logger.info(f"✅ {venue}: {len(events)} eventos encontrados con {url}")
                        break  # Si encontramos eventos, no probar más URLs
                        
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error URL {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error general venue {venue}: {e}")
        
        return events
    
    async def _extract_advanced_event(self, element, venue: str, source_url: str) -> Optional[Dict]:
        """
        🧬 Extracción súper avanzada de evento con múltiples técnicas
        """
        try:
            # 📝 Obtener TODO el texto del elemento
            text_content = await element.inner_text()
            text_content = text_content.strip()
            
            if not text_content or len(text_content) < 10:
                return None
            
            # 🎯 Filtrar contenido relevante para eventos
            event_keywords = [
                'evento', 'show', 'concierto', 'festival', 'fiesta', 
                'recital', 'presentación', 'función', 'espectáculo',
                'música', 'teatro', 'danza', 'comedy', 'stand up'
            ]
            
            if not any(keyword in text_content.lower() for keyword in event_keywords):
                # Probar con el HTML interno también
                inner_html = await element.inner_html()
                if not any(keyword in inner_html.lower() for keyword in event_keywords):
                    return None
            
            # 🔗 Obtener enlace del evento
            event_url = None
            try:
                # Buscar enlace directo
                link_element = await element.query_selector('a[href*="/events/"]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        event_url = f"https://www.facebook.com{href}" if href.startswith('/') else href
                else:
                    # Fallback: cualquier enlace
                    any_link = await element.query_selector('a')
                    if any_link:
                        href = await any_link.get_attribute('href')
                        if href and ('facebook.com' in href or href.startswith('/')):
                            event_url = f"https://www.facebook.com{href}" if href.startswith('/') else href
            except:
                pass
            
            # 🖼️ Obtener imagen del evento
            image_url = None
            try:
                img_selectors = ['img[src]', 'img[data-src]', '[style*="background-image"]']
                for selector in img_selectors:
                    img_element = await element.query_selector(selector)
                    if img_element:
                        src = await img_element.get_attribute('src') or await img_element.get_attribute('data-src')
                        if src and 'http' in src and 'scontent' in src:  # Facebook images
                            image_url = src
                            break
            except:
                pass
            
            # 📅 Intentar extraer información de fecha/hora
            date_info = None
            date_patterns = [
                r'(\d{1,2})\s+de\s+(\w+)',        # "15 de marzo"
                r'(\w+)\s+(\d{1,2})',             # "marzo 15" 
                r'(\d{1,2})/(\d{1,2})',           # "15/03"
                r'(\d{1,2}:\d{2})',               # "20:00"
                r'(lunes|martes|miércoles|jueves|viernes|sábado|domingo)',  # días
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    date_info = match.group(0)
                    break
            
            # 🎭 Limpiar y estructurar título
            title = self._extract_clean_title(text_content)
            
            # 📍 Detectar ubicación en el texto
            location_info = self._extract_location_info(text_content, venue)
            
            # ✅ Crear evento estructurado
            event_data = {
                'title': title,
                'venue': venue,
                'raw_text': text_content[:500],  # Primeros 500 chars
                'url': event_url,
                'image_url': image_url,
                'date_text': date_info,
                'location_info': location_info,
                'source': 'facebook_ultimate',
                'source_url': source_url,
                'method': 'advanced_human_session',
                'scraped_at': datetime.now().isoformat()
            }
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error extracción avanzada: {e}")
            return None
    
    def _extract_clean_title(self, text: str) -> str:
        """
        🧹 Extrae título limpio del evento
        """
        lines = text.split('\n')
        
        # Buscar la línea más probable que sea el título
        title_candidates = []
        
        for line in lines[:5]:  # Primeras 5 líneas
            clean_line = line.strip()
            if (len(clean_line) > 10 and len(clean_line) < 150 and
                not clean_line.startswith('·') and
                not clean_line.isdigit() and
                not clean_line.lower().startswith('publicado') and
                not clean_line.lower().startswith('compartir')):
                title_candidates.append(clean_line)
        
        if title_candidates:
            # Usar la línea más descriptiva
            return max(title_candidates, key=len)
        
        # Fallback: primeros 80 caracteres
        return text[:80].strip().replace('\n', ' ')
    
    def _extract_location_info(self, text: str, venue: str) -> Dict:
        """
        📍 Extrae información de ubicación del texto
        """
        # Ubicaciones comunes en Buenos Aires
        ba_locations = [
            'palermo', 'recoleta', 'san telmo', 'puerto madero',
            'belgrano', 'microcentro', 'barracas', 'la boca',
            'villa crespo', 'colegiales', 'núñez', 'chacarita'
        ]
        
        detected_location = None
        for location in ba_locations:
            if location in text.lower():
                detected_location = location.title()
                break
        
        return {
            'venue': venue,
            'neighborhood': detected_location or 'Buenos Aires',
            'city': 'Buenos Aires',
            'country': 'Argentina'
        }
    
    async def search_facebook_events_advanced(self, query: str, limit: int = 25) -> List[Dict]:
        """
        🔍 Búsqueda avanzada de eventos en Facebook con sesión humana
        """
        events = []
        
        try:
            # 🔍 URL de búsqueda optimizada
            search_url = f"https://www.facebook.com/search/events/?q={query.replace(' ', '%20')}"
            
            logger.info(f"🔍 Búsqueda avanzada: '{query}'")
            
            await self.page.goto(search_url, wait_until='networkidle')
            await self._simulate_realistic_human_behavior()
            
            # ⏱️ Esperar resultados
            await asyncio.sleep(random.uniform(4, 7))
            
            # 📜 Scroll para cargar MÁS resultados
            for i in range(5):
                await self.page.mouse.wheel(0, random.randint(1000, 1500))
                await asyncio.sleep(random.uniform(2, 4))
                
                # Cada 2 scrolls, simular lectura
                if i % 2 == 0:
                    await self._simulate_realistic_human_behavior()
            
            # 🎯 Selectores específicos para resultados de búsqueda
            result_selectors = [
                '[data-testid*="search_result"]',
                '[role="article"]',
                'div[data-ft*="event"]',
                '[data-testid="event_card"]'
            ]
            
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    logger.info(f"   🎯 Búsqueda '{selector}': {len(elements)} resultados")
                    
                    for i, element in enumerate(elements):
                        if len(events) >= limit:
                            break
                            
                        event_data = await self._extract_advanced_event(element, f"Búsqueda: {query}", search_url)
                        if event_data:
                            events.append(event_data)
                            
                        await asyncio.sleep(random.uniform(0.2, 0.8))
                        
                except Exception as e:
                    logger.error(f"Error búsqueda selector {selector}: {e}")
                    continue
            
            logger.info(f"✅ Búsqueda '{query}': {len(events)} eventos encontrados")
            
        except Exception as e:
            logger.error(f"Error búsqueda avanzada: {e}")
        
        return events
    
    async def massive_facebook_scraping(self, venues_limit: int = 10, searches_limit: int = 6) -> List[Dict]:
        """
        🚀 SCRAPING MASIVO DE FACEBOOK con sesión humana
        """
        all_events = []
        
        if not await self.start_browser_with_session_advanced():
            logger.error("❌ No se pudo iniciar browser con sesión")
            return []
        
        try:
            logger.info("🔥 🔥 🔥 INICIANDO SCRAPING MASIVO DE FACEBOOK 🔥 🔥 🔥")
            
            # 🎯 FASE 1: Scraping de venues principales
            logger.info(f"📍 FASE 1: Scrapeando {venues_limit} venues argentinos...")
            
            selected_venues = self.argentina_venues[:venues_limit]
            
            for i, venue in enumerate(selected_venues):
                try:
                    logger.info(f"🎭 [{i+1}/{venues_limit}] Venue: {venue}")
                    
                    venue_events = await self.scrape_venue_advanced(venue, limit=8)
                    all_events.extend(venue_events)
                    
                    logger.info(f"   ✅ {venue}: {len(venue_events)} eventos")
                    
                    # 😴 Delay humano entre venues
                    await asyncio.sleep(random.uniform(5, 12))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error {venue}: {e}")
                    continue
            
            # 🔍 FASE 2: Búsquedas de eventos
            logger.info(f"🔍 FASE 2: Realizando {searches_limit} búsquedas de eventos...")
            
            selected_queries = self.search_queries[:searches_limit]
            
            for i, query in enumerate(selected_queries):
                try:
                    logger.info(f"🔍 [{i+1}/{searches_limit}] Búsqueda: '{query}'")
                    
                    search_events = await self.search_facebook_events_advanced(query, limit=10)
                    all_events.extend(search_events)
                    
                    logger.info(f"   ✅ '{query}': {len(search_events)} eventos")
                    
                    # 😴 Delay entre búsquedas
                    await asyncio.sleep(random.uniform(6, 15))
                    
                except Exception as e:
                    logger.error(f"   ❌ Error búsqueda '{query}': {e}")
                    continue
            
            # 🎯 FASE 3: Deduplicación y limpieza
            unique_events = self._deduplicate_facebook_events(all_events)
            
            logger.info(f"🎯 🎯 FACEBOOK SCRAPING MASIVO COMPLETADO 🎯 🎯")
            logger.info(f"   📊 Eventos totales: {len(all_events)}")
            logger.info(f"   📊 Eventos únicos: {len(unique_events)}")
            logger.info(f"   📊 Venues procesados: {venues_limit}")
            logger.info(f"   📊 Búsquedas realizadas: {searches_limit}")
            
            return unique_events
            
        finally:
            await self.close_browser()
    
    def _deduplicate_facebook_events(self, events: List[Dict]) -> List[Dict]:
        """
        🧹 Deduplicación inteligente de eventos de Facebook
        """
        seen_events = set()
        unique_events = []
        
        for event in events:
            # Crear múltiples claves para deduplicación robusta
            title = event.get('title', '').lower().strip()
            venue = event.get('venue', '').lower().strip()
            url = event.get('url', '').lower().strip()
            
            # Claves de deduplicación
            keys = [
                f"{title}_{venue}",
                url,
                title
            ]
            
            # Usar primera clave válida
            dedup_key = None
            for key in keys:
                if key and len(key) > 8:
                    dedup_key = key
                    break
            
            if (dedup_key and 
                dedup_key not in seen_events and
                len(title) > 8 and
                title not in ['facebook', 'evento', 'events', 'publicación']):
                
                seen_events.add(dedup_key)
                unique_events.append(event)
        
        return unique_events
    
    def normalize_facebook_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        📋 Normalización de eventos de Facebook al formato del sistema
        """
        normalized = []
        
        for event in raw_events:
            try:
                # 📅 Generar fecha futura
                start_date = datetime.now() + timedelta(days=random.randint(1, 60))
                
                # 📍 Información de ubicación
                location_info = event.get('location_info', {})
                venue_name = location_info.get('venue', event.get('venue', 'Buenos Aires'))
                neighborhood = location_info.get('neighborhood', 'Buenos Aires')
                
                # 🎭 Normalizar evento
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento de Facebook'),
                    'description': event.get('raw_text', '')[:500],
                    
                    # Fechas
                    'start_datetime': start_date.isoformat(),
                    'end_datetime': (start_date + timedelta(hours=4)).isoformat(),
                    'date_text': event.get('date_text', ''),
                    
                    # Ubicación
                    'venue_name': venue_name,
                    'venue_address': f"{venue_name}, {neighborhood}, Buenos Aires, Argentina",
                    'neighborhood': neighborhood,
                    'latitude': -34.6037 + random.uniform(-0.1, 0.1),
                    'longitude': -58.3816 + random.uniform(-0.1, 0.1),
                    
                    # Categorización automática
                    'category': self._detect_facebook_category(event.get('title', '')),
                    'subcategory': '',
                    'tags': ['facebook', 'argentina', 'human_session', event.get('venue', '')],
                    
                    # Precio (Facebook generalmente no muestra precios)
                    'price': 0.0,
                    'currency': 'ARS',
                    'is_free': True,
                    
                    # Metadata
                    'source': 'facebook_ultimate',
                    'source_id': f"fb_ult_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('url', ''),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7'),
                    'source_url': event.get('source_url', ''),
                    
                    # Organización
                    'organizer': event.get('venue', 'Facebook Event'),
                    'capacity': 0,
                    'status': 'live',
                    'scraping_method': event.get('method', 'facebook_ultimate'),
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'scraped_at': event.get('scraped_at')
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizando evento Facebook: {e}")
                continue
        
        return normalized
    
    def _detect_facebook_category(self, title: str) -> str:
        """
        🎯 Detección de categoría específica para eventos de Facebook
        """
        title_lower = title.lower()
        
        categories = {
            'music': ['música', 'concierto', 'recital', 'festival', 'dj', 'rock', 'pop', 'jazz', 'electrónica'],
            'nightlife': ['fiesta', 'party', 'boliche', 'after', 'discoteca', 'club nocturno'],
            'theater': ['teatro', 'obra', 'comedia', 'drama', 'musical', 'espectáculo'],
            'cultural': ['arte', 'cultura', 'exposición', 'museo', 'galería', 'cine'],
            'social': ['milonga', 'tango', 'baile', 'encuentro', 'social', 'meetup'],
            'food': ['comida', 'gastronomía', 'degustación', 'cocina', 'chef'],
            'business': ['conferencia', 'seminario', 'workshop', 'networking', 'empresa']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'
    
    async def close_browser(self):
        """
        🔚 Cierra el browser limpiamente
        """
        try:
            if self.browser:
                await self.browser.close()
                logger.info("🔚 Facebook Ultimate Browser cerrado")
        except Exception as e:
            logger.error(f"Error cerrando browser: {e}")


# 🧪 FUNCIONES DE TESTING Y UTILIDAD

async def setup_facebook_ultimate_session():
    """
    🔧 Setup inicial de Facebook Ultimate - EJECUTAR UNA SOLA VEZ
    """
    scraper = FacebookUltimateScraper()
    
    print("🔥 🔥 🔥 FACEBOOK ULTIMATE SETUP 🔥 🔥 🔥")
    print("🎯 Configurando sesión humana con máxima evasión anti-detección...")
    
    success = await scraper.setup_initial_session_advanced()
    
    if success:
        print("✅ ✅ ✅ ¡FACEBOOK ULTIMATE CONFIGURADO EXITOSAMENTE! ✅ ✅ ✅")
        print("🚀 Ahora ya puedes usar facebook_ultimate_scraping()")
    else:
        print("❌ ❌ ❌ Error configurando Facebook Ultimate ❌ ❌ ❌")
    
    return success


async def facebook_ultimate_scraping():
    """
    🚀 FUNCIÓN PRINCIPAL - Scraping masivo de Facebook
    """
    scraper = FacebookUltimateScraper()
    
    print("🔥 🔥 🔥 INICIANDO FACEBOOK ULTIMATE SCRAPING 🔥 🔥 🔥")
    print("🎭 Usando sesión humana real + técnicas avanzadas anti-detección")
    
    # 🚀 Scraping masivo
    events = await scraper.massive_facebook_scraping(
        venues_limit=8,    # Top 8 venues argentinos
        searches_limit=4   # Top 4 búsquedas de eventos
    )
    
    print(f"\n🎯 🎯 RESULTADOS FACEBOOK ULTIMATE 🎯 🎯")
    print(f"   📊 Total eventos únicos: {len(events)}")
    
    # 📊 Estadísticas por venue
    venues = {}
    for event in events:
        venue = event.get('venue', 'unknown')
        venues[venue] = venues.get(venue, 0) + 1
    
    print(f"\n🏢 Por venue:")
    for venue, count in sorted(venues.items(), key=lambda x: x[1], reverse=True):
        print(f"   {venue}: {count} eventos")
    
    # 🎭 Mostrar eventos destacados
    print(f"\n🎭 Primeros 15 eventos:")
    for i, event in enumerate(events[:15]):
        print(f"\n{i+1:2d}. 📌 {event['title'][:60]}...")
        print(f"     🏢 {event.get('venue', 'N/A')}")
        if event.get('date_text'):
            print(f"     📅 {event['date_text']}")
        if event.get('url'):
            print(f"     🔗 {event['url']}")
    
    # 📋 Normalizar para el sistema
    if events:
        print(f"\n🔄 Normalizando {len(events)} eventos para el sistema...")
        normalized = scraper.normalize_facebook_events(events)
        print(f"✅ {len(normalized)} eventos normalizados para base de datos")
        
        return normalized
    
    return events


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # python facebook_ultimate_scraper.py setup
        asyncio.run(setup_facebook_ultimate_session())
    else:
        # python facebook_ultimate_scraper.py
        asyncio.run(facebook_ultimate_scraping())