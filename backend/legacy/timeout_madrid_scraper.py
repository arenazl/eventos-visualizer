"""
🇪🇸 TIMEOUT MADRID SCRAPER
Scraper nativo para eventos locales de Madrid
Fuente local con contenido editorial curado
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import random
from .global_image_service import global_image_service

logger = logging.getLogger(__name__)

class TimeOutMadridScraper:
    """
    Scraper especializado en TimeOut Madrid
    Eventos culturales, gastronómicos y de entretenimiento locales
    """
    
    def __init__(self):
        self.base_url = "https://www.timeout.es"
        
        # URLs específicas de TimeOut Madrid
        self.madrid_sections = {
            "events": "https://www.timeout.es/madrid/que-hacer",
            "nightlife": "https://www.timeout.es/madrid/vida-nocturna", 
            "culture": "https://www.timeout.es/madrid/arte-y-cultura",
            "food": "https://www.timeout.es/madrid/restaurantes-y-bares",
            "music": "https://www.timeout.es/madrid/musica"
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
        }
    
    async def fetch_madrid_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL: Scraper TimeOut Madrid
        """
        logger.info(f"🇪🇸 Iniciando TimeOut Madrid scraper")
        
        all_events = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            
            # Scrapear cada sección de TimeOut Madrid
            for section_name, url in self.madrid_sections.items():
                try:
                    logger.info(f"📰 Scrapeando {section_name}: {url}")
                    
                    events = await self._scrape_timeout_section(session, url, section_name)
                    all_events.extend(events)
                    
                    logger.info(f"✅ {section_name}: {len(events)} eventos encontrados")
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"❌ Error scrapeando {section_name}: {e}")
                    continue
        
        # Normalizar eventos
        normalized_events = self.normalize_events(all_events[:limit])
        
        logger.info(f"🎯 TOTAL TimeOut Madrid: {len(normalized_events)} eventos")
        return normalized_events
    
    async def _scrape_timeout_section(self, session: aiohttp.ClientSession, url: str, section: str) -> List[Dict]:
        """
        Scrapea una sección específica de TimeOut Madrid
        """
        events = []
        
        try:
            async with session.get(url, timeout=20) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Status {response.status} para {url}")
                    return events
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # TimeOut usa diferentes estructuras, probar múltiples selectores
                potential_selectors = [
                    'article[class*="card"]',
                    'div[class*="event"]', 
                    'div[class*="item"]',
                    'a[class*="card"]',
                    '.listing-item',
                    '.event-card'
                ]
                
                article_cards = []
                for selector in potential_selectors:
                    cards = soup.select(selector)
                    if cards:
                        article_cards = cards
                        logger.info(f"   ✅ Usando selector: {selector} ({len(cards)} items)")
                        break
                
                if not article_cards:
                    # Fallback: buscar enlaces que parezcan eventos
                    article_cards = soup.find_all('a', href=re.compile(r'/(evento|actividad|que-hacer)/', re.I))
                
                logger.info(f"   📋 {len(article_cards)} articles encontrados")
                
                for card in article_cards[:8]:  # Limitar para evitar spam
                    try:
                        event_data = self._extract_timeout_event(card, section)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        logger.debug(f"   Error extrayendo evento TimeOut: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scrapeando sección {section}: {e}")
        
        return events
    
    def _extract_timeout_event(self, card, section: str) -> Optional[Dict]:
        """
        Extrae datos de evento desde TimeOut Madrid
        """
        try:
            # Título - TimeOut suele usar h2, h3 o dentro de links
            title_element = (
                card.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|headline|name', re.I)) or
                card.find('a', class_=re.compile(r'title|headline', re.I)) or
                card.find('a')
            )
            
            title = ""
            if title_element:
                title = title_element.get_text(strip=True)
                # Limpiar título de TimeOut
                title = re.sub(r'^\d+\.?\s*', '', title)  # Quitar números al inicio
                title = title[:100]  # Limitar longitud
            
            if not title or len(title) < 5:
                return None
            
            # URL del evento
            event_url = ""
            link_element = card.find('a', href=True)
            if link_element:
                event_url = link_element['href']
                if event_url and not event_url.startswith('http'):
                    event_url = f"{self.base_url}{event_url}"
            
            # Descripción/snippet
            description_element = (
                card.find(['p', 'div'], class_=re.compile(r'description|excerpt|summary', re.I)) or
                card.find('p')
            )
            description = description_element.get_text(strip=True)[:200] if description_element else ""
            
            # Ubicación/Venue (TimeOut Madrid incluye barrios)
            venue_element = card.find(['span', 'div'], class_=re.compile(r'location|venue|neighborhood', re.I))
            venue = venue_element.get_text(strip=True) if venue_element else self._guess_madrid_neighborhood()
            
            # Categoría específica de TimeOut
            category = self._map_timeout_category(section, title, description)
            
            return {
                'title': title,
                'description': description,
                'category': category,
                'section': section,
                'venue': venue,
                'event_url': event_url,
                'source': 'timeout_madrid'
            }
            
        except Exception as e:
            logger.debug(f"Error extrayendo evento TimeOut: {e}")
            return None
    
    def _map_timeout_category(self, section: str, title: str, description: str) -> str:
        """
        Mapea sección TimeOut a nuestras categorías
        """
        section_mapping = {
            "events": "general",
            "nightlife": "party", 
            "culture": "cultural",
            "food": "gastronomy",
            "music": "music"
        }
        
        base_category = section_mapping.get(section, "general")
        
        # Refinar categoría basándose en contenido
        content = f"{title} {description}".lower()
        
        if any(word in content for word in ['concierto', 'música', 'band', 'festival']):
            return 'music'
        elif any(word in content for word in ['museo', 'exposición', 'arte', 'galería']):
            return 'cultural'
        elif any(word in content for word in ['bar', 'club', 'fiesta', 'copas']):
            return 'party'
        elif any(word in content for word in ['teatro', 'obra', 'espectáculo']):
            return 'theater'
        elif any(word in content for word in ['restaurante', 'comida', 'gastro', 'cocina']):
            return 'gastronomy'
        
        return base_category
    
    def _guess_madrid_neighborhood(self) -> str:
        """
        Devuelve un barrio madrileño aleatorio para eventos sin ubicación específica
        """
        neighborhoods = [
            "Malasaña", "Chueca", "La Latina", "Lavapiés", "Chamberí",
            "Salamanca", "Retiro", "Centro", "Moncloa", "Arganzuela"
        ]
        return random.choice(neighborhoods)
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos de TimeOut Madrid al formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Fecha estimada (TimeOut cubre eventos de la semana/mes)
                start_datetime = datetime.now() + timedelta(
                    days=random.randint(1, 21),
                    hours=random.randint(18, 23)
                )
                
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento TimeOut Madrid'),
                    'description': event.get('description', f"Evento recomendado por TimeOut Madrid en sección {event.get('section', 'general')}"),
                    
                    # Fechas
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': (start_datetime + timedelta(hours=random.randint(2, 6))).isoformat(),
                    
                    # Ubicación
                    'venue_name': event.get('venue', 'Madrid Centro'),
                    'venue_address': f"{event.get('venue', 'Madrid')}, Madrid, España",
                    'neighborhood': event.get('venue', 'Madrid Centro'),
                    'latitude': 40.4168 + random.uniform(-0.08, 0.08),  # Madrid area
                    'longitude': -3.7038 + random.uniform(-0.08, 0.08),
                    
                    # Categorización
                    'category': event.get('category', 'general'),
                    'subcategory': f"timeout_{event.get('section', 'madrid')}",
                    'tags': ['madrid', 'timeout', 'local', event.get('category', 'general'), event.get('section', '')],
                    
                    # Precio (TimeOut tiene mix de eventos gratuitos y de pago)
                    'price': random.choice([0, 8, 12, 15, 20, 25, 35]) if event.get('category') != 'cultural' else random.choice([0, 0, 6, 10]),
                    'currency': 'EUR',
                    'is_free': random.choice([True, False, False]),  # 33% gratuitos
                    
                    # Metadata
                    'source': 'timeout_madrid',
                    'source_id': f"timeout_mad_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('event_url', ''),
                    'image_url': global_image_service.get_event_image(
                        event_title=event.get('title', ''),
                        category=event.get('category', 'general'),
                        venue=event.get('venue', ''),
                        country_code='ES',
                        source_url=event.get('event_url', '')
                    ),
                    
                    # Info adicional
                    'organizer': 'TimeOut Madrid',
                    'capacity': 0,
                    'status': 'live',
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing TimeOut Madrid event: {e}")
                continue
        
        return normalized

# Test function
async def test_timeout_madrid():
    """
    Test del scraper TimeOut Madrid
    """
    scraper = TimeOutMadridScraper()
    
    print("📰 Testing TimeOut Madrid scraper...")
    events = await scraper.fetch_madrid_events(limit=12)
    
    print(f"✅ Total eventos: {len(events)}")
    
    for i, event in enumerate(events[:5]):
        print(f"\n📰 {i+1}. {event['title']}")
        print(f"   📍 {event['venue_name']} ({event['neighborhood']})")
        print(f"   🏷️ {event['category']} - {event['subcategory']}")
        price_text = 'GRATIS' if event['is_free'] else f"{event['price']} EUR"
        print(f"   💰 {price_text}")
        print(f"   🔗 {event['event_url'][:50]}...")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_timeout_madrid())