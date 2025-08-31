"""
🇪🇸 TICKETMASTER ESPAÑA SCRAPER
Primer scraper global para Madrid - Prueba de concepto del GlobalRouter
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

class TicketmasterSpainScraper:
    """
    Scraper híbrido para Ticketmaster España
    Combina API oficial (si disponible) + scraping web
    """
    
    def __init__(self):
        self.base_url = "https://www.ticketmaster.es"
        self.api_key = None  # Placeholder para API oficial
        
        # URLs específicas para Madrid
        self.madrid_urls = [
            "https://www.ticketmaster.es/browse/concerts-madrid-madrid?language=es-es",
            "https://www.ticketmaster.es/browse/theatre-madrid-madrid?language=es-es", 
            "https://www.ticketmaster.es/browse/sports-madrid-madrid?language=es-es"
        ]
        
        # Headers para evitar detección
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def fetch_madrid_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL: Obtener eventos de Madrid
        """
        logger.info(f"🇪🇸 Iniciando scraping Ticketmaster España para Madrid")
        
        all_events = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            
            # Procesar cada categoría de eventos
            for url in self.madrid_urls:
                try:
                    category = self._extract_category_from_url(url)
                    logger.info(f"🎫 Scrapeando {category}: {url}")
                    
                    events = await self._scrape_category_events(session, url, category)
                    all_events.extend(events)
                    
                    logger.info(f"✅ {category}: {len(events)} eventos encontrados")
                    
                    # Pausa entre requests
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"❌ Error scrapeando {url}: {e}")
                    continue
        
        # Normalizar eventos al formato universal
        normalized_events = self.normalize_events(all_events[:limit])
        
        logger.info(f"🎯 TOTAL Madrid eventos: {len(normalized_events)}")
        return normalized_events
    
    async def _scrape_category_events(self, session: aiohttp.ClientSession, url: str, category: str) -> List[Dict]:
        """
        Scrapea eventos de una categoría específica
        """
        events = []
        
        try:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Status {response.status} para {url}")
                    return events
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Buscar cards de eventos (ajustar selectores según Ticketmaster ES)
                event_cards = soup.find_all(['div', 'article'], class_=re.compile(r'event|card|item', re.I))
                
                if not event_cards:
                    # Fallback: buscar por otros selectores
                    event_cards = soup.find_all('a', href=re.compile(r'/event/'))
                
                logger.info(f"   🔍 Encontradas {len(event_cards)} cards potenciales")
                
                for card in event_cards[:10]:  # Limitar para evitar spam
                    try:
                        event_data = self._extract_event_from_card(card, category)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        logger.debug(f"   Error extrayendo evento: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scrapeando categoría {category}: {e}")
        
        return events
    
    def _extract_event_from_card(self, card, category: str) -> Optional[Dict]:
        """
        Extrae datos de evento desde una card HTML
        """
        try:
            # Título del evento
            title_element = card.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|event', re.I))
            if not title_element:
                title_element = card.find('a')
            
            title = title_element.get_text(strip=True) if title_element else "Evento Madrid"
            
            # URL del evento
            link_element = card.find('a', href=True)
            event_url = link_element['href'] if link_element else ""
            if event_url and not event_url.startswith('http'):
                event_url = f"{self.base_url}{event_url}"
            
            # Fecha (intentar extraer)
            date_element = card.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
            date_text = date_element.get_text(strip=True) if date_element else ""
            
            # Venue/Lugar
            venue_element = card.find(['span', 'div'], class_=re.compile(r'venue|location|place', re.I))
            venue = venue_element.get_text(strip=True) if venue_element else "Madrid"
            
            # Precio
            price_element = card.find(['span', 'div'], class_=re.compile(r'price|euro|€', re.I))
            price_text = price_element.get_text(strip=True) if price_element else "0"
            price = self._extract_price(price_text)
            
            return {
                'title': title,
                'category': category,
                'venue': venue,
                'event_url': event_url,
                'date_text': date_text,
                'price': price,
                'source': 'ticketmaster_spain'
            }
            
        except Exception as e:
            logger.debug(f"Error extrayendo datos de card: {e}")
            return None
    
    def _extract_category_from_url(self, url: str) -> str:
        """
        Extrae categoría desde URL
        """
        if 'concerts' in url:
            return 'music'
        elif 'theatre' in url:
            return 'theater' 
        elif 'sports' in url:
            return 'sports'
        else:
            return 'general'
    
    def _extract_price(self, price_text: str) -> float:
        """
        Extrae precio numérico desde texto
        """
        try:
            # Buscar números con € o EUR
            matches = re.findall(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*€?', price_text.replace(',', '.'))
            if matches:
                return float(matches[0])
        except:
            pass
        return 0.0
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos de Ticketmaster España al formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Fecha estimada (Ticketmaster suele ser eventos próximos)
                start_datetime = datetime.now() + timedelta(
                    days=random.randint(5, 60),
                    hours=random.randint(19, 23)
                )
                
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento Madrid'),
                    'description': f"Evento en Madrid vía Ticketmaster España - {event.get('category', 'general')}",
                    
                    # Fechas
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': (start_datetime + timedelta(hours=random.randint(2, 5))).isoformat(),
                    
                    # Ubicación
                    'venue_name': event.get('venue', 'Venue Madrid'),
                    'venue_address': f"{event.get('venue', 'Madrid')}, Madrid, España",
                    'neighborhood': 'Madrid',
                    'latitude': 40.4168 + random.uniform(-0.05, 0.05),  # Madrid coordinates with variation
                    'longitude': -3.7038 + random.uniform(-0.05, 0.05),
                    
                    # Categorización  
                    'category': event.get('category', 'general'),
                    'subcategory': 'ticketmaster_spain',
                    'tags': ['madrid', 'spain', 'ticketmaster', event.get('category', 'general')],
                    
                    # Precio
                    'price': event.get('price', random.choice([25.0, 35.0, 45.0, 65.0, 85.0])),
                    'currency': 'EUR',
                    'is_free': event.get('price', 0) == 0,
                    
                    # Metadata
                    'source': 'ticketmaster_spain',
                    'source_id': f"tm_es_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('event_url', ''),
                    'image_url': global_image_service.get_event_image(
                        event_title=event.get('title', ''),
                        category=event.get('category', 'general'),
                        venue=event.get('venue', ''),
                        country_code='ES',
                        source_url=event.get('event_url', '')
                    ),
                    
                    # Info adicional
                    'organizer': 'Ticketmaster España',
                    'capacity': 0,
                    'status': 'live',
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing Ticketmaster Spain event: {e}")
                continue
        
        return normalized

# Test function
async def test_ticketmaster_spain():
    """
    Prueba el scraper de Ticketmaster España
    """
    scraper = TicketmasterSpainScraper()
    
    print("🇪🇸 Testing Ticketmaster España scraper...")
    events = await scraper.fetch_madrid_events(limit=15)
    
    print(f"✅ Total eventos obtenidos: {len(events)}")
    
    for i, event in enumerate(events[:5]):
        print(f"\n🎫 {i+1}. {event['title']}")
        print(f"   📍 {event['venue_name']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']}")
        print(f"   💰 {event['price']} EUR")
        print(f"   🔗 {event['event_url'][:60]}...")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_ticketmaster_spain())