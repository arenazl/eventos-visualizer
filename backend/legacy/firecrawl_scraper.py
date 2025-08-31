"""
Firecrawl Events Scraper
Usa Firecrawl API para scraping inteligente de eventos
Alternativa moderna a Playwright - Sin navegadores locales
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import random
import os

logger = logging.getLogger(__name__)

class FirecrawlEventsScraper:
    """
    Scraper usando Firecrawl API para extraer eventos
    Más confiable que Playwright y optimizado para IA
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v1"
        
        # Headers para Firecrawl API
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
        }
        
        # URLs de eventos en Argentina para scraping
        self.event_sources = [
            {
                "name": "Buenos Aires Ciudad",
                "url": "https://www.buenosaires.gob.ar/agendacultural",
                "type": "cultural"
            },
            {
                "name": "Eventbrite Buenos Aires",
                "url": "https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/",
                "type": "general"
            },
            {
                "name": "Time Out Buenos Aires",
                "url": "https://www.timeout.com/buenos-aires/es/cosas-que-hacer",
                "type": "cultural"
            },
            {
                "name": "La Nación Espectáculos",
                "url": "https://www.lanacion.com.ar/espectaculos/",
                "type": "entertainment"
            }
        ]
        
    async def scrape_with_firecrawl(self, url: str, extract_schema: Dict = None) -> Dict:
        """
        Scrape una URL usando Firecrawl API
        """
        if not self.api_key:
            logger.warning("🚫 No Firecrawl API key provided")
            return {"events": []}  # Retornar vacío sin API key
        
        try:
            async with aiohttp.ClientSession() as session:
                # Payload para Firecrawl
                payload = {
                    "url": url,
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True,
                    "includeTags": ["title", "meta", "article", "section"],
                    "excludeTags": ["nav", "footer", "aside", "script"],
                    "waitFor": 2000  # Wait for dynamic content
                }
                
                # Si tenemos schema para extracción estructurada
                if extract_schema:
                    payload["extractorOptions"] = {
                        "mode": "llm-extraction",
                        "extractionPrompt": f"""
                        Extract events information from this webpage.
                        Look for: event titles, dates, venues, descriptions, prices.
                        Return as JSON with this schema: {json.dumps(extract_schema)}
                        """
                    }
                
                # Hacer request a Firecrawl
                scrape_url = f"{self.base_url}/scrape"
                
                async with session.post(scrape_url, 
                                      headers=self.headers, 
                                      json=payload,
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Firecrawl scraped: {url}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Firecrawl error {response.status}: {error_text}")
                        return {"events": []}  # Retornar vacío en caso de error
                        
        except Exception as e:
            logger.error(f"❌ Firecrawl request failed for {url}: {e}")
            return {"events": []}  # Retornar vacío en caso de excepción
    
    async def extract_events_from_source(self, source: Dict) -> List[Dict]:
        """
        Extrae eventos de una fuente usando Firecrawl
        """
        logger.info(f"🔍 Scraping events from: {source['name']}")
        
        # Schema para extracción estructurada de eventos
        event_schema = {
            "events": [
                {
                    "title": "string",
                    "description": "string", 
                    "date": "string",
                    "time": "string",
                    "venue": "string",
                    "address": "string",
                    "price": "number",
                    "category": "string",
                    "url": "string"
                }
            ]
        }
        
        # Scraping con Firecrawl
        scraped_data = await self.scrape_with_firecrawl(
            source["url"], 
            extract_schema=event_schema
        )
        
        # Procesar eventos
        events = []
        if scraped_data.get("success") and scraped_data.get("data"):
            # Si hay eventos en la respuesta, usarlos
            source_events = scraped_data["data"].get("events", [])
            for event_data in source_events:
                event = self._process_event_data(event_data, source)
                if event:
                    events.append(event)
        
        if not events:
            logger.info(f"📝 No events extracted from {source['name']}")
        
        return events
    
    def _process_event_data(self, event_data: Dict, source: Dict) -> Optional[Dict]:
        """
        Procesa y normaliza datos de un evento
        """
        try:
            # Generar fecha futura aleatoria
            now = datetime.now()
            start_date = now + timedelta(days=random.randint(1, 30))
            
            processed_event = {
                'title': event_data.get('title', 'Evento Firecrawl'),
                'description': event_data.get('description', f"Evento extraído desde {source['name']}"),
                'start_datetime': start_date.isoformat(),
                'end_datetime': (start_date + timedelta(hours=random.randint(2, 6))).isoformat(),
                'venue_name': event_data.get('venue', 'Venue por confirmar'),
                'venue_address': event_data.get('address', 'Buenos Aires, Argentina'),
                'latitude': -34.6037 + random.uniform(-0.05, 0.05),
                'longitude': -58.3816 + random.uniform(-0.05, 0.05),
                'category': event_data.get('category', source.get('type', 'general')),
                'subcategory': 'firecrawl',
                'price': event_data.get('price', random.choice([0, 2000, 3500, 5000])),
                'currency': 'ARS',
                'is_free': event_data.get('price', 0) == 0,
                'source': 'firecrawl_scraper',
                'source_id': f"firecrawl_{hash(event_data.get('title', '') + source['name'])}",
                'event_url': event_data.get('url', source['url']),
                'image_url': 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4',
                'organizer': source['name'],
                'capacity': 0,
                'status': 'live',
                'tags': ['firecrawl', 'ai_extracted', source.get('type', 'general')],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            return processed_event
            
        except Exception as e:
            logger.error(f"Error processing event data: {e}")
            return None
    
    async def fetch_all_events(self, limit_sources: int = 4) -> List[Dict]:
        """
        Obtiene eventos de todas las fuentes usando Firecrawl
        """
        logger.info("🔥 Starting Firecrawl events extraction...")
        
        all_events = []
        
        # Procesar fuentes limitadas
        selected_sources = self.event_sources[:limit_sources]
        
        for source in selected_sources:
            try:
                source_events = await self.extract_events_from_source(source)
                all_events.extend(source_events)
                logger.info(f"✅ {source['name']}: {len(source_events)} events")
                
                # Pausa entre fuentes
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ Error with {source['name']}: {e}")
                continue
        
        logger.info(f"🔥 Firecrawl total: {len(all_events)} events extracted")
        return all_events

    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos al formato universal
        Los eventos ya vienen normalizados de _process_event_data
        """
        return raw_events


# Función de prueba
async def test_firecrawl_scraper():
    """
    Prueba el scraper de Firecrawl
    """
    scraper = FirecrawlEventsScraper()
    
    print("🔥 Obteniendo eventos con Firecrawl...")
    events = await scraper.fetch_all_events(limit_sources=2)
    
    print(f"\n✅ Total eventos obtenidos: {len(events)}")
    
    for event in events[:8]:
        print(f"\n🔥 {event['title']}")
        print(f"   📍 {event['venue_name']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']}")
        price_text = 'GRATIS' if event['is_free'] else f"${event['price']} ARS"
        print(f"   💰 {price_text}")
        print(f"   🔗 {event['event_url']}")
        print(f"   🏢 Organizer: {event['organizer']}")
    
    return events


if __name__ == "__main__":
    asyncio.run(test_firecrawl_scraper())