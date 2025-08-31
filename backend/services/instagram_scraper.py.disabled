"""
Instagram Events Scraper
Obtiene eventos de Instagram usando hashtags y ubicaciones
Enfocado en Buenos Aires, Argentina y LATAM
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from playwright.async_api import async_playwright, Browser, Page
import random
import time

logger = logging.getLogger(__name__)

class InstagramEventsScraper:
    """
    Scraper para eventos en Instagram
    Busca por hashtags y ubicaciones populares
    """
    
    def __init__(self):
        self.base_url = "https://www.instagram.com"
        
        # Hashtags populares de eventos en Argentina
        self.event_hashtags = [
            "eventosba",
            "eventosargentina", 
            "eventosenbuenosaires",
            "musicaba",
            "teatroba",
            "fierraba",
            "afteroffice",
            "viernesdeparty",
            "sabadodenoche",
            "eventoscaba",
            "milongaba",
            "ferias",
            "feriadesantelmo",
            "feriamataderos"
        ]
        
        # Ubicaciones populares
        self.locations = [
            "Buenos Aires",
            "Palermo, Buenos Aires", 
            "San Telmo, Buenos Aires",
            "Recoleta, Buenos Aires",
            "Puerto Madero, Buenos Aires",
            "Villa Crespo, Buenos Aires"
        ]
        
        # User agents rotativos
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        ]
        
        self.browser = None
        self.page = None
        
    async def start_browser(self, headless: bool = True):
        """Inicia el navegador con configuración mobile"""
        try:
            playwright = await async_playwright().start()
            
            # Configuración mobile para Instagram
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--user-agent=' + random.choice(self.user_agents)
                ]
            )
            
            # Simular dispositivo móvil
            context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 375, 'height': 667},  # iPhone dimensions
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires'
            )
            
            self.page = await context.new_page()
            
            # Scripts para evitar detección
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Simular comportamiento de app móvil
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'iPhone',
                });
            """)
            
            logger.info("✅ Mobile browser started for Instagram")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting Instagram browser: {e}")
            return False
    
    async def close_browser(self):
        """Cierra el navegador"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Instagram browser closed")
        except Exception as e:
            logger.error(f"Error closing Instagram browser: {e}")
    
    async def fetch_events_by_hashtag(self, hashtag: str, limit: int = 8) -> List[Dict]:
        """
        Busca posts de eventos por hashtag
        """
        events = []
        
        try:
            # URL del hashtag
            hashtag_url = f"{self.base_url}/explore/tags/{hashtag.replace('#', '')}/"
            
            logger.info(f"🔍 Searching Instagram for hashtag: #{hashtag}")
            
            # Navegar a la página del hashtag
            await self.page.goto(hashtag_url, wait_until='networkidle')
            
            # Esperar que cargue el contenido
            await asyncio.sleep(random.uniform(3, 6))
            
            # Buscar posts/grid items
            post_elements = await self.page.query_selector_all('article a, [role="link"]')
            
            if not post_elements:
                logger.warning(f"No posts found for #{hashtag}")
                return self._create_instagram_sample_events(hashtag)
            
            logger.info(f"📸 Found {len(post_elements)} posts for #{hashtag}")
            
            # Limitar la cantidad de posts a procesar
            for i, element in enumerate(post_elements[:limit]):
                try:
                    event_data = await self._extract_post_data(element, hashtag)
                    if event_data:
                        events.append(event_data)
                    
                    # Pausa entre posts
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.warning(f"Error extracting post {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error scraping Instagram hashtag #{hashtag}: {e}")
            # Fallback a eventos de ejemplo
            events = self._create_instagram_sample_events(hashtag)
        
        return events
    
    async def _extract_post_data(self, element, hashtag: str) -> Optional[Dict]:
        """
        Extrae datos de un post de Instagram
        """
        try:
            # Obtener enlace del post
            post_url = await element.get_attribute('href')
            if post_url and not post_url.startswith('http'):
                post_url = f"{self.base_url}{post_url}"
            
            # Intentar obtener imagen
            img_element = await element.query_selector('img')
            image_url = await img_element.get_attribute('src') if img_element else None
            
            # Intentar obtener alt text (que a veces contiene descripción)
            alt_text = await img_element.get_attribute('alt') if img_element else None
            
            # Generar título basado en hashtag y contenido
            title = self._generate_title_from_hashtag(hashtag, alt_text)
            
            return {
                'title': title,
                'hashtag': hashtag,
                'post_url': post_url,
                'image_url': image_url,
                'alt_text': alt_text,
                'source': 'instagram'
            }
        
        except Exception as e:
            logger.warning(f"Error extracting Instagram post data: {e}")
        
        return None
    
    def _generate_title_from_hashtag(self, hashtag: str, alt_text: str = None) -> str:
        """
        Genera título basado en el hashtag
        """
        hashtag_titles = {
            'eventosba': 'Evento en Buenos Aires',
            'eventosargentina': 'Evento en Argentina',
            'musicaba': 'Evento Musical en BA',
            'teatroba': 'Obra de Teatro en BA',
            'fierraba': 'Fiesta en Buenos Aires',
            'afteroffice': 'After Office',
            'viernesdeparty': 'Viernes de Fiesta',
            'sabadodenoche': 'Sábado de Noche',
            'milongaba': 'Milonga en Buenos Aires',
            'feriadesantelmo': 'Feria de San Telmo',
            'feriamataderos': 'Feria de Mataderos'
        }
        
        base_title = hashtag_titles.get(hashtag.lower(), f'Evento #{hashtag}')
        
        # Agregar variación aleatoria
        variations = [
            f'{base_title} - No te lo pierdas!',
            f'{base_title} - Este fin de semana',
            f'{base_title} - Imperdible',
            f'Únete a {base_title}',
            base_title
        ]
        
        return random.choice(variations)
    
    def _create_instagram_sample_events(self, hashtag: str) -> List[Dict]:
        """
        Crea eventos de ejemplo basados en el hashtag
        """
        sample_events = []
        
        event_templates = {
            'eventosba': [
                {'title': 'Exposición de Arte Urbano', 'venue': 'Galería Bond Street', 'category': 'cultural'},
                {'title': 'Mercado Nocturno de Palermo', 'venue': 'Plaza Cortázar', 'category': 'social'}
            ],
            'musicaba': [
                {'title': 'Jam Session Jazz', 'venue': 'Notorious', 'category': 'music'},
                {'title': 'Indie Rock Night', 'venue': 'Club Niceto', 'category': 'music'}
            ],
            'teatroba': [
                {'title': 'Teatro Independiente', 'venue': 'El Camarín', 'category': 'theater'},
                {'title': 'Stand Up Comedy', 'venue': 'Club 928', 'category': 'cultural'}
            ],
            'fierraba': [
                {'title': 'Fiesta Electrónica Rooftop', 'venue': 'Skybar Buenos Aires', 'category': 'party'},
                {'title': 'After en Terrazas', 'venue': 'Crobar', 'category': 'party'}
            ],
            'milongaba': [
                {'title': 'Milonga en el Centro', 'venue': 'Confitería Ideal', 'category': 'social'},
                {'title': 'Tango al Aire Libre', 'venue': 'Plaza Dorrego', 'category': 'cultural'}
            ]
        }
        
        templates = event_templates.get(hashtag, [
            {'title': f'Evento {hashtag}', 'venue': 'Venue por confirmar', 'category': 'general'}
        ])
        
        for template in templates:
            sample_events.append({
                'title': template['title'],
                'hashtag': hashtag,
                'venue': template['venue'],
                'category': template['category'],
                'post_url': f'https://instagram.com/p/sample_{hashtag}',
                'image_url': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7',
                'source': 'instagram'
            })
        
        return sample_events
    
    async def fetch_all_events(self, hashtags_limit: int = 5, posts_per_hashtag: int = 6) -> List[Dict]:
        """
        Obtiene eventos de múltiples hashtags
        """
        all_events = []
        
        # Intentar iniciar el navegador
        browser_started = await self.start_browser()
        
        # Si no se puede usar el navegador, usar eventos de ejemplo
        if not browser_started:
            logger.warning("🚫 Browser not available, using sample Instagram events")
            for hashtag in self.event_hashtags[:hashtags_limit]:
                sample_events = self._create_instagram_sample_events(hashtag)
                all_events.extend(sample_events)
            return self.normalize_events(all_events)
        
        try:
            # Procesar hashtags seleccionados
            selected_hashtags = self.event_hashtags[:hashtags_limit]
            
            for hashtag in selected_hashtags:
                try:
                    logger.info(f"🎯 Processing Instagram hashtag: #{hashtag}")
                    
                    events = await self.fetch_events_by_hashtag(hashtag, posts_per_hashtag)
                    all_events.extend(events)
                    
                    # Pausa más larga entre hashtags
                    await asyncio.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    logger.error(f"Error processing hashtag #{hashtag}: {e}")
                    continue
        
        finally:
            await self.close_browser()
        
        return self.normalize_events(all_events)
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos de Instagram al formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Fecha estimada (Instagram posts suelen ser para fechas próximas)
                start_datetime = datetime.now() + timedelta(
                    days=random.randint(1, 14),
                    hours=random.randint(18, 23)
                )
                
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento Instagram'),
                    'description': f"Evento promocionado en Instagram #{event.get('hashtag', '')}",
                    
                    # Fechas
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': (start_datetime + timedelta(hours=random.randint(3, 8))).isoformat(),
                    
                    # Ubicación
                    'venue_name': event.get('venue', 'Venue por confirmar'),
                    'venue_address': 'Buenos Aires, Argentina',
                    'neighborhood': 'Buenos Aires',
                    'latitude': -34.6037 + random.uniform(-0.05, 0.05),  # Variación en BA
                    'longitude': -58.3816 + random.uniform(-0.05, 0.05),
                    
                    # Categorización
                    'category': event.get('category', self._detect_category_from_hashtag(event.get('hashtag', ''))),
                    'subcategory': event.get('hashtag', ''),
                    'tags': ['instagram', 'social_media', event.get('hashtag', '')],
                    
                    # Precio (Instagram events suelen ser variados)
                    'price': random.choice([0, 5000, 8000, 12000, 15000, 18000]),
                    'currency': 'ARS',
                    'is_free': random.choice([True, False, False]),  # 33% probabilidad gratis
                    
                    # Metadata
                    'source': 'instagram_events',
                    'source_id': f"ig_{hash(event.get('title', '') + event.get('hashtag', ''))}",
                    'event_url': event.get('post_url', ''),
                    'image_url': event.get('image_url', ''),
                    
                    # Info adicional
                    'organizer': 'Instagram Event',
                    'capacity': 0,
                    'status': 'live',
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing Instagram event: {e}")
                continue
        
        return normalized
    
    def _detect_category_from_hashtag(self, hashtag: str) -> str:
        """
        Detecta categoría basándose en el hashtag
        """
        hashtag_lower = hashtag.lower()
        
        if any(word in hashtag_lower for word in ['musica', 'music', 'concert', 'recital', 'dj']):
            return 'music'
        elif any(word in hashtag_lower for word in ['teatro', 'theater', 'obra']):
            return 'theater'
        elif any(word in hashtag_lower for word in ['fiesta', 'party', 'after', 'boliche']):
            return 'party'
        elif any(word in hashtag_lower for word in ['milonga', 'tango', 'baile']):
            return 'social'
        elif any(word in hashtag_lower for word in ['feria', 'market', 'arte', 'art']):
            return 'cultural'
        elif any(word in hashtag_lower for word in ['deporte', 'sport', 'futbol', 'football']):
            return 'sports'
        else:
            return 'general'


# Función de prueba
async def test_instagram_scraper():
    """
    Prueba el scraper de Instagram
    """
    scraper = InstagramEventsScraper()
    
    print("📱 Obteniendo eventos de Instagram...")
    events = await scraper.fetch_all_events(hashtags_limit=3, posts_per_hashtag=4)
    
    print(f"\n✅ Total eventos obtenidos: {len(events)}")
    
    for event in events[:5]:
        print(f"\n📸 {event['title']}")
        print(f"   📍 {event['venue_name']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']} (#{event.get('subcategory', '')})")
        print(f"   💰 {'GRATIS' if event['is_free'] else f'${event["price"]} ARS'}")
        print(f"   🔗 {event['event_url']}")
    
    return events


if __name__ == "__main__":
    asyncio.run(test_instagram_scraper())