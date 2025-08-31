"""
Sistema de Scraping Inteligente con Playwright
Extrae eventos de cualquier sitio web usando MCP Context y Playwright
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from playwright.async_api import async_playwright, Page, Browser
import json
import hashlib
from bs4 import BeautifulSoup

class EventScraperPlaywright:
    """
    Scraper universal para eventos usando Playwright
    Soporta sitios con JavaScript pesado, lazy loading, etc.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        
        # Configuración para parecer un navegador real
        self.viewport = {'width': 1920, 'height': 1080}
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # Patrones para extraer información
        self.date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{1,2}\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)',
            r'(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+\d{1,2}',
        ]
        
        self.price_patterns = [
            r'\$\s*[\d,]+',
            r'AR\$\s*[\d,]+',
            r'USD\s*[\d,]+',
            r'desde\s*\$\s*[\d,]+',
            r'gratis|free|entrada libre',
        ]
    
    async def start(self):
        """Inicializa el navegador con Playwright"""
        playwright = await async_playwright().start()
        
        # Usar Chromium para mejor compatibilidad
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
            ]
        )
        
        # Crear contexto con configuración anti-detección
        self.context = await self.browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent,
            locale='es-AR',
            timezone_id='America/Buenos_Aires',
            # Evitar detección de automation
            extra_http_headers={
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            }
        )
        
        # Agregar scripts para evitar detección
        await self.context.add_init_script("""
            // Ocultar que es headless
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Ocultar plugins vacíos
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Fingir que tenemos permisos
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    async def scrape_teatro_colon(self) -> List[Dict[str, Any]]:
        """Scraper específico para Teatro Colón"""
        page = await self.context.new_page()
        events = []
        
        try:
            await page.goto('https://teatrocolon.org.ar/es/calendario', wait_until='networkidle')
            
            # Esperar que carguen los eventos
            await page.wait_for_selector('.event-item, .calendario-item, .show-item', timeout=10000)
            
            # Scrollear para cargar todos los eventos (lazy loading)
            await self.auto_scroll(page)
            
            # Extraer HTML después del scroll
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Buscar eventos con selectores múltiples
            event_selectors = [
                '.event-item',
                '.calendario-item',
                '.show-item',
                'article.event',
                'div[class*="event"]',
                'div[class*="show"]'
            ]
            
            for selector in event_selectors:
                for item in soup.select(selector):
                    event = self.extract_event_from_element(item, 'Teatro Colón')
                    if event:
                        events.append(event)
            
        except Exception as e:
            print(f"Error scraping Teatro Colón: {e}")
        finally:
            await page.close()
        
        return events
    
    async def scrape_luna_park(self) -> List[Dict[str, Any]]:
        """Scraper para Luna Park"""
        page = await self.context.new_page()
        events = []
        
        try:
            await page.goto('https://www.lunapark.com.ar', wait_until='networkidle')
            
            # Click en calendario/eventos si existe
            try:
                await page.click('a:has-text("Calendario"), a:has-text("Eventos")', timeout=3000)
                await page.wait_for_load_state('networkidle')
            except:
                pass
            
            await self.auto_scroll(page)
            
            # Extraer eventos usando MCP Context patterns
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    const eventElements = document.querySelectorAll('[class*="event"], [class*="show"], article, .card');
                    
                    eventElements.forEach(el => {
                        const title = el.querySelector('h1, h2, h3, h4, [class*="title"]')?.innerText;
                        const date = el.querySelector('[class*="date"], [class*="fecha"], time')?.innerText;
                        const price = el.querySelector('[class*="price"], [class*="precio"]')?.innerText;
                        const image = el.querySelector('img')?.src;
                        
                        if (title) {
                            events.push({
                                title: title.trim(),
                                date: date?.trim(),
                                price: price?.trim(),
                                image_url: image,
                                venue: 'Luna Park'
                            });
                        }
                    });
                    
                    return events;
                }
            """)
            
            events = events_data
            
        except Exception as e:
            print(f"Error scraping Luna Park: {e}")
        finally:
            await page.close()
        
        return events
    
    async def scrape_niceto_club(self) -> List[Dict[str, Any]]:
        """Scraper para Niceto Club"""
        page = await self.context.new_page()
        events = []
        
        try:
            await page.goto('https://www.nicetoclub.com', wait_until='networkidle')
            await self.auto_scroll(page)
            
            # Niceto suele tener eventos en Instagram embebido
            # Buscar iframes de Instagram
            instagram_frames = await page.query_selector_all('iframe[src*="instagram"]')
            
            # También buscar en el HTML principal
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    // Buscar cualquier cosa que parezca un evento
                    const possibleEvents = document.body.innerText.match(/\\d{1,2}[/-]\\d{1,2}.*?(fiesta|party|show|live|dj)/gi);
                    if (possibleEvents) {
                        possibleEvents.forEach(match => {
                            events.push({
                                raw_text: match,
                                venue: 'Niceto Club'
                            });
                        });
                    }
                    return events;
                }
            """)
            
            # Procesar los eventos crudos
            for raw_event in events_data:
                event = self.parse_raw_event_text(raw_event['raw_text'], 'Niceto Club')
                if event:
                    events.append(event)
            
        except Exception as e:
            print(f"Error scraping Niceto Club: {e}")
        finally:
            await page.close()
        
        return events
    
    async def scrape_passline(self) -> List[Dict[str, Any]]:
        """Scraper para Passline - Eventos y Fiestas"""
        page = await self.context.new_page()
        events = []
        
        try:
            await page.goto('https://www.passline.com/eventos', wait_until='networkidle')
            
            # Passline tiene paginación infinita
            for _ in range(5):  # Cargar 5 páginas
                await self.auto_scroll(page)
                await page.wait_for_timeout(1000)
            
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    document.querySelectorAll('.event-card, .evento-card, [class*="evento"]').forEach(card => {
                        const title = card.querySelector('.title, h3, h4')?.innerText;
                        const venue = card.querySelector('.venue, .lugar')?.innerText;
                        const date = card.querySelector('.date, .fecha')?.innerText;
                        const price = card.querySelector('.price, .precio')?.innerText;
                        const link = card.querySelector('a')?.href;
                        
                        if (title) {
                            events.push({
                                title,
                                venue,
                                date,
                                price,
                                event_url: link,
                                source: 'Passline'
                            });
                        }
                    });
                    return events;
                }
            """)
            
            events = events_data
            
        except Exception as e:
            print(f"Error scraping Passline: {e}")
        finally:
            await page.close()
        
        return events
    
    async def scrape_timeout_ba(self) -> List[Dict[str, Any]]:
        """Scraper para TimeOut Buenos Aires"""
        page = await self.context.new_page()
        events = []
        
        try:
            urls = [
                'https://www.timeout.com/es/buenos-aires/que-hacer',
                'https://www.timeout.com/es/buenos-aires/musica',
                'https://www.timeout.com/es/buenos-aires/teatro',
                'https://www.timeout.com/es/buenos-aires/arte'
            ]
            
            for url in urls:
                await page.goto(url, wait_until='networkidle')
                await self.auto_scroll(page)
                
                section_events = await page.evaluate("""
                    () => {
                        const events = [];
                        document.querySelectorAll('article, .card, ._article_kc6w6_1').forEach(article => {
                            const title = article.querySelector('h3, h4, .card-title')?.innerText;
                            const description = article.querySelector('p, .card-text')?.innerText;
                            const link = article.querySelector('a')?.href;
                            const image = article.querySelector('img')?.src;
                            
                            if (title) {
                                events.push({
                                    title,
                                    description,
                                    event_url: link,
                                    image_url: image,
                                    source: 'TimeOut Buenos Aires'
                                });
                            }
                        });
                        return events;
                    }
                """)
                
                events.extend(section_events)
            
        except Exception as e:
            print(f"Error scraping TimeOut BA: {e}")
        finally:
            await page.close()
        
        return events
    
    async def scrape_instagram_events(self, hashtags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scraper para eventos en Instagram usando hashtags
        Nota: Instagram es difícil de scrapear, mejor usar su API oficial si es posible
        """
        if not hashtags:
            hashtags = ['#eventosBA', '#fiestasBA', '#teatroBA', '#recitalesBA', '#showsBA']
        
        page = await self.context.new_page()
        events = []
        
        for hashtag in hashtags:
            try:
                # Instagram requiere login para ver más contenido
                # Esta es una versión simplificada
                url = f'https://www.instagram.com/explore/tags/{hashtag.replace("#", "")}/'
                await page.goto(url, wait_until='networkidle')
                
                # Extraer posts públicos visibles
                posts_data = await page.evaluate("""
                    () => {
                        const posts = [];
                        document.querySelectorAll('article img').forEach((img, index) => {
                            if (index < 12) {  // Solo los primeros 12 posts
                                const altText = img.alt || '';
                                posts.push({
                                    description: altText,
                                    image_url: img.src
                                });
                            }
                        });
                        return posts;
                    }
                """)
                
                # Procesar posts para extraer eventos
                for post in posts_data:
                    event = self.extract_event_from_instagram_post(post, hashtag)
                    if event:
                        events.append(event)
                        
            except Exception as e:
                print(f"Error scraping Instagram {hashtag}: {e}")
        
        await page.close()
        return events
    
    async def scrape_generic_venue(self, url: str, venue_name: str) -> List[Dict[str, Any]]:
        """
        Scraper genérico para cualquier venue/sitio web
        Usa heurísticas para encontrar eventos
        """
        page = await self.context.new_page()
        events = []
        
        try:
            await page.goto(url, wait_until='networkidle')
            await self.auto_scroll(page)
            
            # Estrategia 1: Buscar por palabras clave
            events_by_keywords = await page.evaluate("""
                (venueName) => {
                    const events = [];
                    const keywords = ['evento', 'show', 'fiesta', 'concierto', 'obra', 'función'];
                    const months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                                   'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
                    
                    // Buscar elementos que contengan keywords
                    const allElements = document.querySelectorAll('*');
                    const eventElements = [];
                    
                    allElements.forEach(el => {
                        const text = el.innerText?.toLowerCase() || '';
                        const hasKeyword = keywords.some(kw => text.includes(kw));
                        const hasMonth = months.some(m => text.includes(m));
                        
                        if (hasKeyword && hasMonth && text.length < 500) {
                            eventElements.push(el);
                        }
                    });
                    
                    // Extraer información de cada elemento
                    eventElements.forEach(el => {
                        const text = el.innerText;
                        const parent = el.parentElement;
                        
                        // Buscar imagen cercana
                        const img = parent?.querySelector('img') || el.querySelector('img');
                        
                        events.push({
                            raw_text: text,
                            image_url: img?.src,
                            venue: venueName
                        });
                    });
                    
                    return events;
                }
            """, venue_name)
            
            # Procesar eventos crudos
            for raw_event in events_by_keywords:
                event = self.parse_raw_event_text(raw_event['raw_text'], venue_name)
                if event:
                    event['image_url'] = raw_event.get('image_url')
                    events.append(event)
            
        except Exception as e:
            print(f"Error scraping {venue_name}: {e}")
        finally:
            await page.close()
        
        return events
    
    # Métodos auxiliares
    
    async def auto_scroll(self, page: Page, max_scrolls: int = 10):
        """Auto-scroll para cargar contenido lazy-loaded"""
        for _ in range(max_scrolls):
            await page.evaluate('window.scrollBy(0, 500)')
            await page.wait_for_timeout(500)
    
    def extract_event_from_element(self, element, venue: str) -> Optional[Dict[str, Any]]:
        """Extrae información de evento de un elemento HTML"""
        try:
            # Buscar título
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.titulo', '[class*="title"]']
            title = None
            for selector in title_selectors:
                if element.select_one(selector):
                    title = element.select_one(selector).get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Buscar fecha
            date_text = None
            date_selectors = ['.date', '.fecha', 'time', '[class*="date"]', '[class*="fecha"]']
            for selector in date_selectors:
                if element.select_one(selector):
                    date_text = element.select_one(selector).get_text(strip=True)
                    break
            
            # Buscar precio
            price_text = None
            price_selectors = ['.price', '.precio', '[class*="price"]', '[class*="precio"]']
            for selector in price_selectors:
                if element.select_one(selector):
                    price_text = element.select_one(selector).get_text(strip=True)
                    break
            
            # Buscar descripción
            description = None
            desc_selectors = ['p', '.description', '.descripcion', '[class*="desc"]']
            for selector in desc_selectors:
                if element.select_one(selector):
                    description = element.select_one(selector).get_text(strip=True)[:500]
                    break
            
            # Buscar imagen
            image = element.select_one('img')
            image_url = image.get('src') if image else None
            
            # Buscar link
            link = element.select_one('a')
            event_url = link.get('href') if link else None
            
            return {
                'title': title,
                'description': description,
                'date_raw': date_text,
                'price_raw': price_text,
                'venue': venue,
                'image_url': image_url,
                'event_url': event_url,
                'source': f'scraping_{venue.lower().replace(" ", "_")}',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting event: {e}")
            return None
    
    def parse_raw_event_text(self, text: str, venue: str) -> Optional[Dict[str, Any]]:
        """Parsea texto crudo para extraer información del evento"""
        try:
            # Extraer fecha
            date_match = None
            for pattern in self.date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_match = match.group()
                    break
            
            # Extraer precio
            price_match = None
            for pattern in self.price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price_match = match.group()
                    break
            
            # El título podría ser la primera línea o hasta la fecha
            lines = text.strip().split('\n')
            title = lines[0] if lines else text[:100]
            
            # Determinar si es gratis
            is_free = bool(re.search(r'gratis|free|entrada libre', text, re.IGNORECASE))
            
            return {
                'title': title.strip(),
                'description': text[:500],
                'date_raw': date_match,
                'price_raw': price_match,
                'is_free': is_free,
                'venue': venue,
                'source': f'scraping_{venue.lower().replace(" ", "_")}',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing raw text: {e}")
            return None
    
    def extract_event_from_instagram_post(self, post: Dict, hashtag: str) -> Optional[Dict[str, Any]]:
        """Extrae información de evento de un post de Instagram"""
        try:
            description = post.get('description', '')
            
            # Buscar fechas en la descripción
            date_match = None
            for pattern in self.date_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    date_match = match.group()
                    break
            
            # Buscar venue mencionado
            venue_patterns = [
                r'en\s+([A-Z][a-zA-Z\s]+)',
                r'@([a-zA-Z0-9_.]+)',  # Menciones
                r'lugar:\s*([^\n]+)',
            ]
            
            venue = None
            for pattern in venue_patterns:
                match = re.search(pattern, description)
                if match:
                    venue = match.group(1)
                    break
            
            # Solo crear evento si tiene fecha
            if date_match:
                return {
                    'title': description.split('\n')[0][:100],
                    'description': description,
                    'date_raw': date_match,
                    'venue': venue or 'Por confirmar',
                    'image_url': post.get('image_url'),
                    'source': f'instagram_{hashtag}',
                    'scraped_at': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting from Instagram: {e}")
            return None
    
    async def close(self):
        """Cierra el navegador"""
        if self.browser:
            await self.browser.close()


# Clase principal que orquesta todo
class UniversalEventAggregator:
    """
    Agregador que combina APIs y Scraping
    """
    
    def __init__(self):
        self.scraper = EventScraperPlaywright()
        
        # Lista de sitios para scrapear
        self.scraping_targets = {
            'Teatro Colón': 'https://teatrocolon.org.ar/es/calendario',
            'Luna Park': 'https://www.lunapark.com.ar',
            'Niceto Club': 'https://www.nicetoclub.com',
            'La Trastienda': 'https://www.latrastienda.com',
            'Estadio Obras': 'https://www.estadioobras.com.ar',
            'Passline': 'https://www.passline.com/eventos',
            'Centro Cultural Recoleta': 'https://www.centroculturalrecoleta.org',
            'Usina del Arte': 'https://www.usinadelarte.org',
            'CCK': 'https://www.cck.gob.ar',
        }
    
    async def fetch_all_events(self, city: str = "Buenos Aires") -> List[Dict[str, Any]]:
        """
        Obtiene eventos de TODAS las fuentes disponibles
        """
        await self.scraper.start()
        
        all_events = []
        
        try:
            # 1. Scraping de venues específicos
            print("🎭 Scraping Teatro Colón...")
            teatro_events = await self.scraper.scrape_teatro_colon()
            all_events.extend(teatro_events)
            
            print("🏟️ Scraping Luna Park...")
            luna_events = await self.scraper.scrape_luna_park()
            all_events.extend(luna_events)
            
            print("🎵 Scraping Niceto Club...")
            niceto_events = await self.scraper.scrape_niceto_club()
            all_events.extend(niceto_events)
            
            print("🎫 Scraping Passline...")
            passline_events = await self.scraper.scrape_passline()
            all_events.extend(passline_events)
            
            print("📰 Scraping TimeOut BA...")
            timeout_events = await self.scraper.scrape_timeout_ba()
            all_events.extend(timeout_events)
            
            # 2. Instagram hashtags
            print("📱 Scraping Instagram hashtags...")
            instagram_events = await self.scraper.scrape_instagram_events()
            all_events.extend(instagram_events)
            
            # 3. Scraping genérico para otros venues
            for venue_name, url in self.scraping_targets.items():
                if venue_name not in ['Teatro Colón', 'Luna Park', 'Niceto Club', 'Passline']:
                    print(f"🎭 Scraping {venue_name}...")
                    venue_events = await self.scraper.scrape_generic_venue(url, venue_name)
                    all_events.extend(venue_events)
            
            print(f"\n✅ Total eventos encontrados: {len(all_events)}")
            
            # Deduplicar eventos
            unique_events = self.deduplicate_events(all_events)
            print(f"📊 Eventos únicos después de deduplicación: {len(unique_events)}")
            
            return unique_events
            
        finally:
            await self.scraper.close()
    
    def deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Elimina eventos duplicados usando hashing inteligente
        """
        seen = set()
        unique = []
        
        for event in events:
            # Crear una firma única para el evento
            signature_parts = [
                event.get('title', '').lower()[:50],
                event.get('venue', '').lower(),
                event.get('date_raw', '')[:10]
            ]
            
            signature = hashlib.md5(''.join(signature_parts).encode()).hexdigest()
            
            if signature not in seen:
                seen.add(signature)
                unique.append(event)
        
        return unique


# Ejemplo de uso
async def main():
    aggregator = UniversalEventAggregator()
    events = await aggregator.fetch_all_events("Buenos Aires")
    
    # Guardar resultados
    with open('/tmp/scraped_events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📁 Eventos guardados en /tmp/scraped_events.json")
    
    # Mostrar algunos ejemplos
    for event in events[:5]:
        print(f"\n📌 {event.get('title')}")
        print(f"   📍 {event.get('venue')}")
        print(f"   📅 {event.get('date_raw')}")
        print(f"   💰 {event.get('price_raw', 'No especificado')}")
        print(f"   🔗 {event.get('source')}")


if __name__ == "__main__":
    asyncio.run(main())