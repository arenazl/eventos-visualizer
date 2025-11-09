"""
📘 FACEBOOK AUTHENTICATED SCRAPER
Scraper especial para Facebook Events con login automático
Accede a eventos locales con credenciales específicas
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("⚠️ Playwright no está instalado")

class FacebookAuthScraper:
    """
    📘 SCRAPER DE FACEBOOK EVENTS CON AUTENTICACIÓN
    
    CARACTERÍSTICAS:
    - Login automático con credenciales específicas
    - Acceso a Facebook Events (eventos locales)
    - Navegación a URL específica con filtros de fecha
    - Extracción de eventos del mes actual
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_url = 'https://www.facebook.com'
        self.login_email = 'arenazl@hotmail.com'
        self.login_password = 'arenazl@hotmail.com'  # Según especificaste
        logger.info("📘 Facebook Auth Scraper inicializado")
    
    async def search_events(self, location: str = "LOCAL", category: str = None, max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN FACEBOOK EVENTS CON LOGIN
        
        Args:
            location: Ubicación (por defecto LOCAL para eventos locales)
            category: Categoría (opcional)
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos encontrados
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Playwright no está disponible")
            return []
        
        try:
            # URL específica de Facebook Events con filtros
            events_url = "https://www.facebook.com/events/?date_filter_option=THIS_MONTH&discover_tab=LOCAL&end_date=2025-09-30T03%3A00%3A00.000Z&start_date=2025-09-02T03%3A00%3A00.000Z"
            
            logger.info(f"📘 Iniciando Facebook Events scraper con login")
            logger.info(f"🔗 URL objetivo: {events_url}")
            
            async with async_playwright() as p:
                # Configurar navegador con opciones especiales para Facebook
                browser = await p.chromium.launch(
                    headless=False,  # Visible para debugging login
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Crear contexto con user agent real
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Paso 1: Hacer login en Facebook
                logger.info("🔑 Iniciando proceso de login...")
                login_success = await self._facebook_login(page)
                
                if not login_success:
                    logger.error("❌ Error en login de Facebook")
                    await browser.close()
                    return []
                
                # Paso 2: Navegar a la página de eventos
                logger.info("📅 Navegando a Facebook Events...")
                await page.goto(events_url, wait_until='networkidle', timeout=30000)
                
                # Esperar que cargue el contenido
                await page.wait_for_timeout(5000)
                
                # Paso 3: Extraer eventos
                events = await self._extract_facebook_events(page, max_events)
                
                await browser.close()
                
                logger.info(f"✅ Facebook Events: {len(events)} eventos extraídos")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error en Facebook Events scraper: {e}")
            return []
    
    async def _facebook_login(self, page) -> bool:
        """
        🔑 REALIZAR LOGIN EN FACEBOOK
        
        Args:
            page: Página de Playwright
            
        Returns:
            True si login exitoso, False si falló
        """
        
        try:
            logger.info("🌐 Navegando a Facebook login...")
            
            # Ir a la página de login
            await page.goto('https://www.facebook.com/login', wait_until='networkidle')
            
            # Esperar que aparezcan los campos de login
            await page.wait_for_selector('#email', timeout=10000)
            
            logger.info("✍️ Ingresando credenciales...")
            
            # Ingresar email
            await page.fill('#email', self.login_email)
            await page.wait_for_timeout(1000)
            
            # Ingresar password
            await page.fill('#pass', self.login_password)
            await page.wait_for_timeout(1000)
            
            # Hacer click en login
            logger.info("🔐 Enviando login...")
            await page.click('button[name="login"]')
            
            # Esperar navegación después del login
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Verificar si el login fue exitoso
            current_url = page.url
            
            if 'facebook.com' in current_url and 'login' not in current_url:
                logger.info("✅ Login exitoso en Facebook")
                return True
            else:
                logger.error("❌ Login falló - aún en página de login")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en login de Facebook: {e}")
            return False
    
    async def _extract_facebook_events(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📅 EXTRAER EVENTOS DE FACEBOOK EVENTS
        
        Args:
            page: Página de Playwright
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos extraídos
        """
        
        try:
            logger.info("🔍 Buscando eventos en Facebook Events...")
            
            # Esperar que aparezcan los eventos
            await page.wait_for_selector('[role="article"], [data-testid*="event"], .event', timeout=15000)
            
            # Selectores posibles para eventos de Facebook
            event_selectors = [
                '[role="article"]',
                '[data-testid*="event"]',
                '.event',
                '[aria-label*="evento"]',
                '[aria-label*="event"]',
                'div[style*="cursor: pointer"]'
            ]
            
            events = []
            
            for selector in event_selectors:
                event_elements = await page.query_selector_all(selector)
                if event_elements:
                    logger.info(f"🎯 Facebook: Encontrados {len(event_elements)} elementos con selector: {selector}")
                    
                    for i, element in enumerate(event_elements[:max_events]):
                        try:
                            event_data = await self._extract_single_facebook_event(element)
                            if event_data:
                                events.append(event_data)
                                if len(events) >= max_events:
                                    break
                        except Exception as e:
                            logger.warning(f"⚠️ Error extrayendo evento Facebook {i}: {e}")
                    
                    break  # Usar el primer selector que funcione
            
            if not events:
                logger.warning("⚠️ No se encontraron eventos con selectores estándar")
                # Intentar extracción genérica
                events = await self._generic_facebook_extraction(page, max_events)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de Facebook: {e}")
            return []
    
    async def _extract_single_facebook_event(self, element) -> Optional[Dict[str, Any]]:
        """
        📘 EXTRAER DATOS DE UN EVENTO INDIVIDUAL DE FACEBOOK
        
        Args:
            element: Elemento HTML del evento
            
        Returns:
            Datos del evento o None si falla
        """
        
        try:
            # Extraer texto completo del elemento
            full_text = await element.text_content()
            
            if not full_text or len(full_text.strip()) < 10:
                return None
            
            # Buscar enlaces dentro del elemento
            links = await element.query_selector_all('a')
            event_url = ''
            title = ''
            
            for link in links:
                href = await link.get_attribute('href')
                link_text = await link.text_content()
                
                # Si el enlace parece ser de un evento
                if href and ('/events/' in href or link_text and len(link_text.strip()) > 10):
                    if href.startswith('/'):
                        event_url = f"https://www.facebook.com{href}"
                    else:
                        event_url = href
                    
                    if link_text and not title:
                        title = link_text.strip()
                    break
            
            # Si no encontramos título en enlaces, usar texto del elemento
            if not title:
                lines = full_text.strip().split('\n')
                for line in lines:
                    if line.strip() and len(line.strip()) > 5:
                        title = line.strip()
                        break
            
            # Buscar fecha en el texto
            date_text = ''
            date_keywords = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                           'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
                           'jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                           'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                           'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                           'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            
            text_lower = full_text.lower()
            for keyword in date_keywords:
                if keyword in text_lower:
                    # Extraer línea que contiene la fecha
                    lines = full_text.split('\n')
                    for line in lines:
                        if keyword in line.lower():
                            date_text = line.strip()
                            break
                    break
            
            # Buscar ubicación en el texto
            venue = ''
            location_keywords = ['en ', 'at ', 'ubicación', 'location', '@']
            for line in full_text.split('\n'):
                line_lower = line.lower()
                for loc_key in location_keywords:
                    if loc_key in line_lower and len(line.strip()) < 100:
                        venue = line.strip()
                        break
                if venue:
                    break
            
            if title and len(title) > 3:
                return {
                    'title': title[:200],  # Limitar longitud
                    'date': date_text[:100],
                    'venue': venue[:100],
                    'price': '',  # Facebook generalmente no muestra precios
                    'url': event_url,
                    'source': 'facebook_auth',
                    'scraped_at': datetime.now().isoformat(),
                    'raw_text': full_text[:300]  # Para debugging
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento individual de Facebook: {e}")
        
        return None
    
    async def _generic_facebook_extraction(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        🔍 EXTRACCIÓN GENÉRICA PARA FACEBOOK EVENTS
        
        Args:
            page: Página de Playwright
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos extraídos genéricamente
        """
        
        try:
            logger.info("🔍 Facebook: Intentando extracción genérica...")
            
            # Buscar todos los enlaces que parezcan eventos
            event_links = await page.query_selector_all('a[href*="/events/"]')
            
            events = []
            for link in event_links[:max_events * 2]:  # Buscar más para filtrar
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if text and text.strip() and len(text.strip()) > 5:
                        event_url = href if href.startswith('http') else f"https://www.facebook.com{href}"
                        
                        events.append({
                            'title': text.strip()[:200],
                            'date': '',
                            'venue': '',
                            'price': '',
                            'url': event_url,
                            'source': 'facebook_auth_generic',
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                        if len(events) >= max_events:
                            break
                            
                except Exception:
                    continue
            
            logger.info(f"🔍 Facebook genérico: {len(events)} eventos")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en extracción genérica de Facebook: {e}")
            return []

# Función de prueba
async def test_facebook_auth():
    """
    🧪 FUNCIÓN DE PRUEBA DEL SCRAPER DE FACEBOOK CON AUTH
    """
    
    print("📘 PROBANDO FACEBOOK AUTH SCRAPER")
    print("=" * 50)
    print("🔑 Login: arenazl@hotmail.com")
    print("🔗 URL: Facebook Events (THIS_MONTH, LOCAL)")
    print()
    
    scraper = FacebookAuthScraper()
    
    # Probar búsqueda de eventos locales
    events = await scraper.search_events("LOCAL", max_events=5)
    
    print(f"\n✅ Eventos encontrados en Facebook: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   📅 Fecha: {event['date']}")
        print(f"   📍 Venue: {event['venue']}")
        print(f"   🔗 URL: {event['url'][:70]}..." if event['url'] else "   URL: N/A")

if __name__ == "__main__":
    # Ejecutar prueba
    asyncio.run(test_facebook_auth())