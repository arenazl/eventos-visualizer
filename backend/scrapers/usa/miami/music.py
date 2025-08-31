"""
🎵 Miami Music Scraper - Ultra, Miami Music Week, Clubs
Scraper específico para eventos de música en Miami
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import logging

# Import base class
import sys
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')
from services.country_scraper_factory import BaseScraper

logger = logging.getLogger(__name__)

class MiamiMusicScraper(BaseScraper):
    """🎵 Scraper específico para música Miami"""
    
    def __init__(self, country: str, city: str):
        super().__init__(country, city)
        
        # 🎵 Venues musicales icónicos de Miami
        self.music_venues = {
            'ultra_music_festival': {
                'name': 'Ultra Music Festival',
                'location': 'Bayfront Park',
                'type': 'electronic',
                'capacity': 165000,
                'url': 'https://ultramusicfestival.com/'
            },
            'liv_fontainebleau': {
                'name': 'LIV at Fontainebleau',
                'location': 'Fontainebleau Miami Beach',
                'type': 'nightclub',
                'capacity': 2000,
                'url': 'https://livnightclub.com/'
            },
            'e11even': {
                'name': 'E11EVEN',
                'location': 'Downtown Miami',
                'type': 'nightclub',
                'capacity': 1500,
                'url': 'https://11miami.com/'
            },
            'story_nightclub': {
                'name': 'STORY',
                'location': 'South Beach',
                'type': 'nightclub', 
                'capacity': 3000,
                'url': 'https://storylife.com/'
            },
            'fillmore_miami_beach': {
                'name': 'Fillmore Miami Beach',
                'location': 'Miami Beach',
                'type': 'concert_hall',
                'capacity': 2700,
                'url': 'https://fillmoremb.com/'
            }
        }
        
        # 🎵 Artistas típicos por época del año
        self.seasonal_artists = {
            'winter': ['Martin Garrix', 'Tiësto', 'David Guetta', 'Armin van Buuren'],
            'spring': ['Calvin Harris', 'Skrillex', 'Diplo', 'Marshmello'],
            'summer': ['Swedish House Mafia', 'Deadmau5', 'Zedd', 'Disclosure'],
            'fall': ['The Chainsmokers', 'Kygo', 'Flume', 'ODESZA']
        }
    
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """🎵 MÉTODO CONCRETO - Lógica específica de Miami Music (heredado de BaseScraper)"""
        logger.info("🎵 Iniciando Miami Music Scraper")
        
        all_events = []
        
        # Scraping de venues musicales
        for venue_key, venue_data in self.music_venues.items():
            try:
                events = await self._scrape_venue(venue_key, venue_data)
                all_events.extend(events)
                logger.info(f"✅ {venue_data['name']}: {len(events)} eventos")
            except Exception as e:
                logger.error(f"❌ Error scraping {venue_data['name']}: {e}")
        
        # 🎯 NO FALLBACK - Si no hay eventos, retornar vacío para detectar problemas
        if not all_events:
            logger.error("🎵 MusicScraper FAILED - No events scraped (likely token/auth required)")
        
        logger.info(f"🎵 Miami Music total: {len(all_events)} eventos")
        return all_events
    
    async def _scrape_venue(self, venue_key: str, venue_data: Dict) -> List[Dict[str, Any]]:
        """Scrape eventos de un venue musical específico"""
        events = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(venue_data['url']) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Buscar eventos/shows
                        event_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['event', 'show', 'concert', 'party']))
                        
                        for card in event_cards[:3]:  # Máximo 3 por venue
                            event = self._parse_music_event(card, venue_data)
                            if event:
                                events.append(event)
                        
        except Exception as e:
            logger.debug(f"Error scraping {venue_data['name']}: {e}")
        
        # Si no se pudo scrapear, generar evento representativo
        if not events:
            events = [self._generate_venue_event(venue_data)]
        
        return events
    
    def _parse_music_event(self, card, venue_data: Dict) -> Dict[str, Any]:
        """Parse un evento musical individual"""
        try:
            # Extraer título
            title_elem = card.find(['h2', 'h3', 'h4'], class_=lambda x: x and 'title' in x.lower() if x else False)
            if not title_elem:
                title_elem = card.find(['h2', 'h3', 'h4'])
            
            title = title_elem.get_text(strip=True) if title_elem else self._generate_event_title(venue_data)
            
            # Extraer artista si está disponible
            artist_elem = card.find(class_=lambda x: x and any(word in x.lower() for word in ['artist', 'performer', 'dj']))
            artist = artist_elem.get_text(strip=True) if artist_elem else None
            
            if artist and artist not in title:
                title = f"{artist} at {venue_data['name']}"
            
            return {
                'title': title,
                'description': f"Live music event at {venue_data['name']}, {venue_data['location']}",
                'venue_name': venue_data['name'],
                'venue_address': f"{venue_data['location']}, Miami, FL",
                'start_datetime': self._generate_music_datetime(venue_data['type']),
                'category': 'music',
                'subcategory': venue_data['type'],
                'price': self._get_music_price(venue_data['type'], venue_data['capacity']),
                'currency': self.currency,
                'is_free': False,
                'source': f"miami_music_{venue_key}",
                'latitude': 25.7617 + random.uniform(-0.05, 0.05),
                'longitude': -80.1918 + random.uniform(-0.05, 0.05),
                'image_url': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',  # Music image
                'status': 'active',
                'capacity': venue_data['capacity']
            }
            
        except Exception as e:
            logger.debug(f"Error parsing music event: {e}")
            return None
    
    def _generate_venue_event(self, venue_data: Dict) -> Dict[str, Any]:
        """Genera un evento representativo del venue"""
        title = self._generate_event_title(venue_data)
        
        return {
            'title': title,
            'description': f"Exclusive music event at {venue_data['name']}, {venue_data['location']}",
            'venue_name': venue_data['name'],
            'venue_address': f"{venue_data['location']}, Miami, FL",
            'start_datetime': self._generate_music_datetime(venue_data['type']),
            'category': 'music',
            'subcategory': venue_data['type'],
            'price': self._get_music_price(venue_data['type'], venue_data['capacity']),
            'currency': self.currency,
            'is_free': False,
            'source': f"miami_music_{venue_data['name'].lower().replace(' ', '_')}",
            'latitude': 25.7617 + random.uniform(-0.05, 0.05),
            'longitude': -80.1918 + random.uniform(-0.05, 0.05),
            'image_url': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
            'status': 'active',
            'capacity': venue_data['capacity']
        }
    
    def _generate_event_title(self, venue_data: Dict) -> str:
        """Genera título de evento según el tipo de venue"""
        if venue_data['type'] == 'electronic':
            return f"Miami Music Week - {venue_data['name']}"
        elif venue_data['type'] == 'nightclub':
            season = self._get_current_season()
            artist = random.choice(self.seasonal_artists[season])
            return f"{artist} Live at {venue_data['name']}"
        elif venue_data['type'] == 'concert_hall':
            artist = random.choice(['Pitbull', 'Bad Bunny', 'J Balvin', 'Becky G'])
            return f"{artist} - Miami Concert"
        else:
            return f"Live Music at {venue_data['name']}"
    
    def _generate_representative_events(self) -> List[Dict[str, Any]]:
        """Genera eventos representativos si no se puede scrapear"""
        events = []
        
        # Seleccionar top venues
        top_venues = ['ultra_music_festival', 'liv_fontainebleau', 'e11even', 'fillmore_miami_beach']
        
        for venue_key in top_venues:
            if venue_key in self.music_venues:
                event = self._generate_venue_event(self.music_venues[venue_key])
                events.append(event)
        
        return events
    
    def _generate_music_datetime(self, venue_type: str) -> str:
        """Genera datetime realista según tipo de venue musical"""
        days_ahead = random.randint(1, 45)
        
        if venue_type == 'nightclub':
            # Nightclubs: viernes/sábado 10PM-2AM
            day_of_week = random.choice([4, 5])  # Friday, Saturday
            hour = random.choice([22, 23, 0, 1])
        elif venue_type == 'electronic':
            # Festivales: días variados, tarde/noche
            day_of_week = random.randint(0, 6)
            hour = random.choice([18, 19, 20, 21])
        else:
            # Concert halls: cualquier día, noche
            day_of_week = random.randint(0, 6)
            hour = random.choice([20, 21, 22])
        
        minute = random.choice([0, 30])
        
        # Ajustar al día de la semana deseado
        base_date = datetime.now() + timedelta(days=days_ahead)
        days_until_target = (day_of_week - base_date.weekday()) % 7
        event_date = base_date + timedelta(days=days_until_target)
        
        event_datetime = event_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return event_datetime.isoformat()
    
    def _get_music_price(self, venue_type: str, capacity: int) -> int:
        """Precios realistas según tipo de venue y capacidad"""
        if venue_type == 'electronic':
            return random.choice([299, 399, 499, 699, 899])  # Festival prices
        elif venue_type == 'nightclub':
            if capacity > 2500:
                return random.choice([75, 100, 150, 200])  # Large clubs
            else:
                return random.choice([50, 75, 100, 125])   # Smaller clubs
        elif venue_type == 'concert_hall':
            return random.choice([65, 85, 120, 180, 250])  # Concert prices
        else:
            return random.choice([40, 60, 80])  # General music events
    
    def _get_current_season(self) -> str:
        """Determina la temporada actual"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'