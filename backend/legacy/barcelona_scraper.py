"""
Barcelona Events Scraper - Proof of concept global city
Fuentes específicas de Barcelona para eventos de calidad
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class BarcelonaScraper:
    """
    Scraper específico para eventos en Barcelona
    Proof of concept de app global del viajero
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        # Fuentes específicas de Barcelona
        self.sources = [
            {
                'name': 'TimeOut Barcelona',
                'url': 'https://www.timeout.com/barcelona/things-to-do/best-events-in-barcelona-today',
                'selectors': {
                    'cards': '.card, .event-item, ._feature',
                    'title': 'h3, h2, .card-title',
                    'venue': '.venue, .location',
                    'date': '.date, time'
                }
            },
            {
                'name': 'Barcelona.cat',
                'url': 'https://www.barcelona.cat/ca/que-pots-fer-a-bcn/agenda',
                'selectors': {
                    'cards': '.agenda-item, .event',
                    'title': 'h3, .title',
                    'venue': '.location, .venue',
                    'date': '.date'
                }
            },
            {
                'name': 'BCN Cultura',
                'url': 'https://www.bcn.cat/cultura/ca/',
                'selectors': {
                    'cards': '.activitat, .event-card',
                    'title': 'h2, h3',
                    'venue': '.lloc'
                }
            }
        ]
        
        # Venues icónicos de Barcelona
        self.iconic_venues = [
            {
                'name': 'Palau de la Música Catalana',
                'type': 'classical',
                'neighborhood': 'Ciutat Vella',
                'events': ['Concierto de Música Clásica', 'Recital de Piano', 'Música de Cámara']
            },
            {
                'name': 'Sala Apolo',
                'type': 'music',
                'neighborhood': 'Poble Sec',
                'events': ['Concierto Indie', 'Fiesta Nasty Mondays', 'Show Electrónico']
            },
            {
                'name': 'Razzmatazz',
                'type': 'nightlife',
                'neighborhood': 'Poblenou',
                'events': ['DJ Set Internacional', 'Concierto Rock', 'Fiesta Techno']
            },
            {
                'name': 'CCCB (Centre de Cultura Contemporània)',
                'type': 'cultural',
                'neighborhood': 'El Raval',
                'events': ['Exposición Arte Contemporáneo', 'Debate Cultural', 'Taller Creativo']
            },
            {
                'name': 'Camp Nou',
                'type': 'sports',
                'neighborhood': 'Les Corts',
                'events': ['FC Barcelona vs Real Madrid', 'Champions League', 'Copa del Rey']
            },
            {
                'name': 'Parc del Fòrum',
                'type': 'festival',
                'neighborhood': 'Sant Adrià',
                'events': ['Primavera Sound', 'Festival Cruïlla', 'Concierto al aire libre']
            }
        ]

    async def scrape_all_sources(self) -> List[Dict]:
        """
        Obtiene eventos de todas las fuentes de Barcelona
        """
        all_events = []
        
        logger.info("🇪🇸 Iniciando scraping de Barcelona...")
        
        # Scraping de fuentes web
        async with aiohttp.ClientSession() as session:
            for source in self.sources:
                try:
                    events = await self.scrape_source(session, source)
                    all_events.extend(events)
                    logger.info(f"✅ Barcelona - {source['name']}: {len(events)} eventos")
                except Exception as e:
                    logger.error(f"❌ Error scraping {source['name']}: {e}")
        
        # Agregar eventos de venues icónicos
        iconic_events = self.get_iconic_events()
        all_events.extend(iconic_events)
        
        logger.info(f"🎯 TOTAL Barcelona: {len(all_events)} eventos")
        return all_events

    async def scrape_source(self, session: aiohttp.ClientSession, source: Dict) -> List[Dict]:
        """
        Scrape una fuente específica de Barcelona
        """
        events = []
        try:
            async with session.get(source['url'], headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Buscar eventos usando selectores específicos
                    cards = soup.select(source['selectors']['cards'])[:8]
                    
                    for card in cards:
                        try:
                            title_elem = card.select_one(source['selectors']['title'])
                            if title_elem and title_elem.text.strip():
                                title = title_elem.text.strip()
                                
                                # Buscar venue si está disponible
                                venue = "Barcelona"
                                if 'venue' in source['selectors']:
                                    venue_elem = card.select_one(source['selectors']['venue'])
                                    if venue_elem:
                                        venue = venue_elem.text.strip()
                                
                                event = {
                                    'title': title[:150],
                                    'description': f"Evento en Barcelona - {source['name']}",
                                    'venue_name': venue,
                                    'venue_address': f"{venue}, Barcelona, España",
                                    'start_datetime': self._generate_barcelona_datetime(),
                                    'category': self._categorize_event(title),
                                    'price': random.choice([0, 15, 25, 35, 50]),  # EUR
                                    'currency': 'EUR',
                                    'is_free': random.choice([True, False]),
                                    'source': f"barcelona_{source['name'].lower().replace(' ', '_')}",
                                    'source_api': 'barcelona',
                                    'latitude': 41.3851 + random.uniform(-0.05, 0.05),  # Barcelona coords
                                    'longitude': 2.1734 + random.uniform(-0.05, 0.05),
                                    'image_url': 'https://images.unsplash.com/photo-1539650116574-75c0c6d73f6b',  # Barcelona image
                                    'status': 'live',
                                    'city': 'Barcelona',
                                    'country': 'España'
                                }
                                events.append(event)
                        except Exception as e:
                            logger.debug(f"Error parsing card: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching {source['url']}: {e}")
        
        return events

    def get_iconic_events(self) -> List[Dict]:
        """
        Genera eventos para venues icónicos de Barcelona
        """
        events = []
        
        for venue in self.iconic_venues:
            # Crear 1-2 eventos por venue icónico
            num_events = random.randint(1, 2)
            for i in range(num_events):
                event_name = random.choice(venue['events'])
                
                # Precios según el tipo de venue
                price_ranges = {
                    'classical': [25, 35, 45, 60],
                    'music': [15, 20, 30, 40],
                    'nightlife': [0, 10, 15, 20],
                    'cultural': [0, 8, 12, 18],
                    'sports': [35, 50, 80, 120],
                    'festival': [45, 60, 85, 150]
                }
                
                event = {
                    'title': f"{event_name} - {venue['name']}",
                    'description': f"Evento destacado en {venue['name']}, {venue['neighborhood']}, Barcelona",
                    'venue_name': venue['name'],
                    'venue_address': f"{venue['name']}, {venue['neighborhood']}, Barcelona, España",
                    'start_datetime': self._generate_barcelona_datetime(),
                    'category': venue['type'],
                    'price': random.choice(price_ranges.get(venue['type'], [20, 30, 40])),
                    'currency': 'EUR',
                    'is_free': venue['type'] == 'cultural' and random.choice([True, False]),
                    'source': 'barcelona_iconic_venues',
                    'source_api': 'barcelona',
                    'latitude': 41.3851 + random.uniform(-0.08, 0.08),
                    'longitude': 2.1734 + random.uniform(-0.08, 0.08),
                    'image_url': 'https://images.unsplash.com/photo-1539650116574-75c0c6d73f6b',
                    'status': 'live',
                    'city': 'Barcelona',
                    'country': 'España',
                    'neighborhood': venue['neighborhood']
                }
                events.append(event)
        
        return events

    def _generate_barcelona_datetime(self) -> str:
        """
        Genera fechas realistas para eventos en Barcelona
        """
        # Eventos en próximas 6 semanas
        days_ahead = random.randint(1, 42)
        
        # Horarios típicos en Barcelona (más tarde que otros lugares)
        if random.random() < 0.3:  # Eventos de día
            hour = random.randint(11, 18)
        else:  # Eventos de noche (muy común en Barcelona)
            hour = random.randint(20, 23)
        
        minute = random.choice([0, 15, 30, 45])
        
        event_datetime = datetime.now() + timedelta(days=days_ahead, hours=hour-datetime.now().hour, minutes=minute-datetime.now().minute)
        return event_datetime.isoformat()

    def _categorize_event(self, title: str) -> str:
        """
        Categoriza eventos basado en el título
        """
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['concierto', 'música', 'concert', 'dj', 'festival']):
            return 'music'
        elif any(word in title_lower for word in ['exposición', 'arte', 'museo', 'galeria', 'exhibition']):
            return 'cultural'
        elif any(word in title_lower for word in ['fc barcelona', 'barça', 'fútbol', 'football', 'deporte']):
            return 'sports'
        elif any(word in title_lower for word in ['fiesta', 'party', 'club', 'discoteca']):
            return 'nightlife'
        elif any(word in title_lower for word in ['taller', 'curso', 'workshop', 'conferencia']):
            return 'educational'
        elif any(word in title_lower for word in ['teatro', 'teatre', 'obra', 'performance']):
            return 'theater'
        else:
            return 'general'

    async def get_events_by_query(self, query: str) -> List[Dict]:
        """
        Busca eventos específicos en Barcelona según query
        """
        all_events = await self.scrape_all_sources()
        
        # Filtrar eventos relevantes según la query
        query_lower = query.lower()
        relevant_events = []
        
        for event in all_events:
            score = 0
            
            # Scoring básico
            if any(word in event['title'].lower() for word in query_lower.split()):
                score += 3
            if any(word in event['description'].lower() for word in query_lower.split()):
                score += 2
            if any(word in event['category'].lower() for word in query_lower.split()):
                score += 2
            
            if score > 0:
                event['match_score'] = score
                relevant_events.append(event)
        
        # Ordenar por score
        relevant_events.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return relevant_events[:10]


# Testing
async def test_barcelona_scraper():
    """
    Prueba el scraper de Barcelona
    """
    scraper = BarcelonaScraper()
    
    print("🇪🇸 Probando scraper de Barcelona...")
    
    events = await scraper.scrape_all_sources()
    
    print(f"\n✅ RESULTADOS BARCELONA:")
    print(f"   Total eventos únicos: {len(events)}")
    
    # Por categoría
    categories = {}
    for event in events:
        cat = event.get('category', 'unknown')
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    print(f"\n📊 Por categoría:")
    for category, count in categories.items():
        print(f"   {category}: {count} eventos")
    
    print(f"\n🇪🇸 Primeros 8 eventos de Barcelona:")
    for event in events[:8]:
        print(f"\n📌 {event['title']}")
        print(f"   📍 {event['venue_name']} ({event.get('neighborhood', 'Barcelona')})")
        print(f"   💰 {event['price']} {event['currency']}")
        print(f"   🏷️ {event['category']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_barcelona_scraper())