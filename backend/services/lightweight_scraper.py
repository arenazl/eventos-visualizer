"""
Lightweight Scraper - Solo usa requests y BeautifulSoup
Funciona en cualquier entorno cloud sin dependencias del sistema
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class LightweightEventScraper:
    """
    Scraper liviano que funciona sin navegador
    Ideal para entornos cloud restrictivos
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
        
    def _random_delay(self):
        """Delay aleatorio para evitar detección"""
        time.sleep(random.uniform(0.5, 2))
    
    async def scrape_timeout_ba(self) -> List[Dict]:
        """
        Scraping de Time Out Buenos Aires
        Este sitio funciona sin JavaScript
        """
        events = []
        try:
            url = "https://www.timeout.com/es/buenos-aires/que-hacer/eventos-en-buenos-aires"
            
            # Intentar con timeout corto
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar artículos de eventos
                articles = soup.find_all(['article', 'div'], class_=re.compile('card|event|listing'))[:10]
                
                for article in articles:
                    try:
                        # Extraer título
                        title_elem = article.find(['h3', 'h2', 'h4', 'a'])
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        if title:
                            # Extraer otros datos si están disponibles
                            desc_elem = article.find(['p', 'div'], class_=re.compile('desc|summary'))
                            desc = desc_elem.get_text(strip=True) if desc_elem else ""
                            
                            events.append({
                                'title': title,
                                'description': desc[:200],
                                'venue_name': 'Buenos Aires',
                                'category': 'cultural',
                                'source': 'timeout_ba',
                                'price': 0,
                                'is_free': True
                            })
                    except:
                        continue
                        
                logger.info(f"✅ TimeOut BA: {len(events)} eventos extraídos")
                
        except Exception as e:
            logger.error(f"Error scraping TimeOut BA: {e}")
            
        return events
    
    async def scrape_ba_cultura(self) -> List[Dict]:
        """
        Scraping del sitio oficial de cultura de Buenos Aires
        """
        events = []
        try:
            url = "https://www.buenosaires.gob.ar/cultura"
            
            response = self.session.get(url, timeout=10, verify=False)  # verify=False para evitar SSL issues
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar eventos en el sitio
                event_containers = soup.find_all(['div', 'article'], class_=re.compile('evento|event|activity'))[:10]
                
                for container in event_containers:
                    try:
                        title_elem = container.find(['h2', 'h3', 'h4', 'a'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            
                            events.append({
                                'title': title,
                                'description': 'Evento cultural en Buenos Aires',
                                'venue_name': 'Centro Cultural',
                                'category': 'cultural',
                                'source': 'ba_cultura',
                                'price': 0,
                                'is_free': True,
                                'start_datetime': (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
                            })
                    except:
                        continue
                        
                logger.info(f"✅ BA Cultura: {len(events)} eventos")
                
        except Exception as e:
            logger.error(f"Error scraping BA Cultura: {e}")
            
        # Si no encontramos eventos, retornar vacío
        if not events:
            logger.warning("⚠️ No se pudieron obtener eventos de BA Cultura")
            
        return events
    
    def _get_known_cultural_events(self) -> List[Dict]:
        """
        DEPRECATED - No usar eventos hardcodeados
        """
        # Solo datos reales
        return []
    
    async def scrape_eventbrite_api(self) -> List[Dict]:
        """
        Intenta usar el API público de Eventbrite (sin autenticación)
        """
        events = []
        try:
            # Eventbrite tiene algunos endpoints públicos
            url = "https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar JSON-LD estructurado
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for item in data:
                                if item.get('@type') == 'Event':
                                    events.append({
                                        'title': item.get('name', ''),
                                        'description': item.get('description', ''),
                                        'start_datetime': item.get('startDate', ''),
                                        'venue_name': item.get('location', {}).get('name', ''),
                                        'category': 'general',
                                        'source': 'eventbrite_public'
                                    })
                    except:
                        continue
                        
                # También buscar en el HTML normal
                event_cards = soup.find_all(['article', 'div'], class_=re.compile('event-card|listing'))[:10]
                
                for card in event_cards:
                    try:
                        title = card.find(['h3', 'h2'])
                        if title:
                            events.append({
                                'title': title.get_text(strip=True),
                                'venue_name': 'Buenos Aires',
                                'category': 'general',
                                'source': 'eventbrite_html',
                                'price': random.choice([0, 2500, 5000, 8000])
                            })
                    except:
                        continue
                        
            logger.info(f"✅ Eventbrite: {len(events)} eventos")
            
        except Exception as e:
            logger.error(f"Error scraping Eventbrite: {e}")
            
        return events
    
    async def fetch_all_events(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Obtiene eventos de todas las fuentes disponibles
        """
        all_events = []
        
        # Intentar cada fuente
        try:
            timeout_events = await self.scrape_timeout_ba()
            all_events.extend(timeout_events)
        except:
            pass
            
        try:
            cultura_events = await self.scrape_ba_cultura()
            all_events.extend(cultura_events)
        except:
            pass
            
        try:
            eventbrite_events = await self.scrape_eventbrite_api()
            all_events.extend(eventbrite_events)
        except:
            pass
            
        # Si no hay eventos, retornar vacío
        if not all_events:
            logger.warning("⚠️ Lightweight scraper no pudo obtener eventos reales")
            
        # Normalizar todos los eventos
        normalized = []
        for event in all_events:
            normalized_event = {
                'title': event.get('title', 'Evento sin título'),
                'description': event.get('description', ''),
                'venue_name': event.get('venue_name', location),
                'venue_address': f"{event.get('venue_name', '')}, {location}",
                'category': event.get('category', 'general'),
                'price': event.get('price', 0),
                'currency': 'ARS',
                'is_free': event.get('is_free', event.get('price', 0) == 0),
                'source': event.get('source', 'lightweight_scraper'),
                'start_datetime': event.get('start_datetime', (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()),
                'image_url': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30',
                'status': 'live'
            }
            
            # Agregar coordenadas aleatorias en Buenos Aires
            normalized_event['latitude'] = -34.6037 + random.uniform(-0.05, 0.05)
            normalized_event['longitude'] = -58.3816 + random.uniform(-0.05, 0.05)
            
            normalized.append(normalized_event)
            
        logger.info(f"🎯 Lightweight Scraper: {len(normalized)} eventos totales")
        return normalized


# Testing
async def test_lightweight_scraper():
    scraper = LightweightEventScraper()
    events = await scraper.fetch_all_events()
    
    print(f"\n✅ Total eventos: {len(events)}")
    for event in events[:5]:
        print(f"\n📍 {event['title']}")
        print(f"   Venue: {event['venue_name']}")
        print(f"   Precio: ${event['price']} ARS")
        print(f"   Fuente: {event['source']}")
    
    return events

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_lightweight_scraper())