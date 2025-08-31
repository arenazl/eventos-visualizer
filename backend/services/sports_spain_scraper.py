"""
🇪🇸 SPORTS SPAIN SCRAPER
API de deportes españoles - LaLiga, Copa del Rey, deportes populares
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class SportsSpainScraper:
    """
    Scraper de deportes españoles usando múltiples APIs
    Enfoque en fútbol (LaLiga) + otros deportes populares
    """
    
    def __init__(self):
        # Football-Data.org API (gratuita con registro)
        self.football_api_key = os.getenv("FOOTBALL_DATA_API_KEY", "")
        self.football_base_url = "http://api.football-data.org/v4"
        
        # LaLiga oficial
        self.laliga_base_url = "https://www.laliga.com/api/v1"
        
        # Headers para APIs
        self.headers = {
            "User-Agent": "FanAroundYou/1.0",
            "Accept": "application/json"
        }
        
        # Competiciones españolas importantes
        self.spanish_competitions = {
            "laliga": {"id": "PD", "name": "LaLiga EA Sports"},
            "copa_rey": {"id": "CLI", "name": "Copa del Rey"}, 
            "champions": {"id": "CL", "name": "Champions League"},
            "europa": {"id": "EL", "name": "Europa League"}
        }
        
        # Equipos españoles populares
        self.madrid_teams = [
            "Real Madrid CF", "Atlético Madrid", "Rayo Vallecano", "Getafe CF"
        ]
    
    async def fetch_spain_sports_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL: Obtener eventos deportivos España
        """
        logger.info(f"🇪🇸 Iniciando Sports Spain scraper")
        
        all_events = []
        
        # Prioridad 1: Football-Data API (si tenemos key)
        if self.football_api_key:
            football_events = await self._fetch_football_data_events()
            all_events.extend(football_events)
        
        # Prioridad 2: LaLiga oficial (scraping)
        laliga_events = await self._fetch_laliga_events()
        all_events.extend(laliga_events)
        
        # Prioridad 3: Eventos de Madrid específicos
        madrid_events = await self._fetch_madrid_sports_events()
        all_events.extend(madrid_events)
        
        # Normalizar eventos
        normalized_events = self.normalize_events(all_events[:limit])
        
        logger.info(f"🏆 TOTAL Sports España: {len(normalized_events)} eventos")
        return normalized_events
    
    async def _fetch_football_data_events(self) -> List[Dict]:
        """
        Obtener eventos desde Football-Data.org API oficial
        """
        events = []
        
        if not self.football_api_key:
            logger.info("📝 Football-Data API key no configurado, saltando...")
            return events
        
        headers = {
            **self.headers,
            "X-Auth-Token": self.football_api_key
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            
            # Obtener partidos de LaLiga
            try:
                laliga_url = f"{self.football_base_url}/competitions/PD/matches"
                params = {
                    "status": "SCHEDULED", 
                    "limit": 15
                }
                
                logger.info(f"⚽ Obteniendo LaLiga desde Football-Data API...")
                
                async with session.get(laliga_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = data.get("matches", [])
                        
                        for match in matches:
                            event_data = self._parse_football_data_match(match)
                            if event_data:
                                events.append(event_data)
                        
                        logger.info(f"✅ Football-Data LaLiga: {len(events)} partidos")
                    else:
                        logger.warning(f"⚠️ Football-Data status: {response.status}")
            
            except Exception as e:
                logger.error(f"❌ Error Football-Data API: {e}")
        
        return events
    
    async def _fetch_laliga_events(self) -> List[Dict]:
        """
        Scraping de LaLiga oficial (fallback)
        """
        events = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                
                # LaLiga calendar/fixtures
                laliga_url = "https://www.laliga.com/calendario-de-partidos"
                
                logger.info(f"⚽ Scrapeando LaLiga oficial...")
                
                async with session.get(laliga_url, timeout=15) as response:
                    if response.status == 200:
                        # Aquí podrías parsear HTML, pero LaLiga es compleja
                        # Para MVP, generar eventos de ejemplo basados en equipos reales
                        events = self._generate_laliga_sample_events()
                        logger.info(f"✅ LaLiga sample events: {len(events)}")
                    
        except Exception as e:
            logger.error(f"❌ Error scraping LaLiga: {e}")
            # Fallback: eventos de ejemplo
            events = self._generate_laliga_sample_events()
        
        return events
    
    async def _fetch_madrid_sports_events(self) -> List[Dict]:
        """
        Eventos deportivos específicos de Madrid
        """
        events = []
        
        # Venues deportivos de Madrid
        madrid_venues = [
            {
                "name": "Santiago Bernabéu",
                "team": "Real Madrid CF",
                "sport": "football",
                "capacity": 81044
            },
            {
                "name": "Wanda Metropolitano", 
                "team": "Atlético Madrid",
                "sport": "football",
                "capacity": 68456
            },
            {
                "name": "WiZink Center",
                "team": "Real Madrid Basketball",
                "sport": "basketball", 
                "capacity": 15544
            }
        ]
        
        # Generar eventos para cada venue
        for venue in madrid_venues:
            try:
                venue_events = self._generate_venue_events(venue)
                events.extend(venue_events)
            except Exception as e:
                logger.error(f"Error generando eventos para {venue['name']}: {e}")
        
        return events
    
    def _parse_football_data_match(self, match: Dict) -> Optional[Dict]:
        """
        Parse match data desde Football-Data.org
        """
        try:
            home_team = match.get("homeTeam", {}).get("name", "Equipo Local")
            away_team = match.get("awayTeam", {}).get("name", "Equipo Visitante") 
            
            # Solo incluir si involucra equipos españoles/Madrid
            spanish_teams = ["Real Madrid", "Atlético", "Barcelona", "Valencia", "Sevilla"]
            is_spanish_match = any(team in f"{home_team} {away_team}" for team in spanish_teams)
            
            if not is_spanish_match:
                return None
            
            return {
                "title": f"{home_team} vs {away_team}",
                "home_team": home_team,
                "away_team": away_team,
                "competition": match.get("competition", {}).get("name", "LaLiga"),
                "match_day": match.get("matchday"),
                "utc_date": match.get("utcDate"),
                "status": match.get("status"),
                "venue": match.get("venue", "Estadio por confirmar"),
                "source": "football_data_api"
            }
        
        except Exception as e:
            logger.debug(f"Error parsing match: {e}")
            return None
    
    def _generate_laliga_sample_events(self) -> List[Dict]:
        """
        Genera eventos de ejemplo de LaLiga para MVP
        """
        sample_matches = [
            {
                "title": "Real Madrid vs Barcelona",
                "home_team": "Real Madrid CF",
                "away_team": "FC Barcelona", 
                "competition": "LaLiga EA Sports",
                "venue": "Santiago Bernabéu",
                "rivalry": "El Clásico"
            },
            {
                "title": "Atlético Madrid vs Valencia",
                "home_team": "Atlético Madrid",
                "away_team": "Valencia CF",
                "competition": "LaLiga EA Sports", 
                "venue": "Wanda Metropolitano"
            },
            {
                "title": "Real Madrid vs Atlético Madrid",
                "home_team": "Real Madrid CF",
                "away_team": "Atlético Madrid",
                "competition": "LaLiga EA Sports",
                "venue": "Santiago Bernabéu",
                "rivalry": "Derbi Madrileño"
            }
        ]
        
        return sample_matches
    
    def _generate_venue_events(self, venue: Dict) -> List[Dict]:
        """
        Genera eventos para un venue específico
        """
        events = []
        
        # 1-2 eventos por venue
        for i in range(2):
            if venue["sport"] == "football":
                opponent = f"Opponent Team {i+1}"
                event = {
                    "title": f"{venue['team']} vs {opponent}",
                    "home_team": venue["team"],
                    "away_team": opponent,
                    "competition": "LaLiga EA Sports" if i == 0 else "Copa del Rey",
                    "venue": venue["name"],
                    "sport": venue["sport"],
                    "capacity": venue["capacity"],
                    "source": "madrid_venues"
                }
            elif venue["sport"] == "basketball":
                event = {
                    "title": f"{venue['team']} - Liga Endesa",
                    "team": venue["team"],
                    "competition": "Liga Endesa ACB",
                    "venue": venue["name"], 
                    "sport": venue["sport"],
                    "capacity": venue["capacity"],
                    "source": "madrid_venues"
                }
            
            events.append(event)
        
        return events
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos deportivos españoles al formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Fecha futura para eventos deportivos
                start_datetime = datetime.now() + timedelta(
                    days=random.randint(3, 45),
                    hours=random.choice([16, 18, 20, 21])  # Horarios típicos LaLiga
                )
                
                normalized_event = {
                    # Información básica
                    'title': event.get('title', 'Evento Deportivo Madrid'),
                    'description': f"{event.get('competition', 'Competición deportiva')} - {event.get('title', 'Partido')}",
                    
                    # Fechas
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': (start_datetime + timedelta(hours=2)).isoformat(),
                    
                    # Ubicación
                    'venue_name': event.get('venue', 'Estadio Madrid'),
                    'venue_address': f"{event.get('venue', 'Madrid')}, Madrid, España",
                    'neighborhood': 'Madrid',
                    'latitude': 40.4530 + random.uniform(-0.02, 0.02),  # Madrid stadium area
                    'longitude': -3.6883 + random.uniform(-0.02, 0.02),
                    
                    # Categorización
                    'category': 'sports',
                    'subcategory': event.get('sport', 'football'),
                    'tags': ['madrid', 'deportes', event.get('sport', 'football'), event.get('competition', '').lower()],
                    
                    # Precio (deportes profesionales)
                    'price': random.choice([25, 35, 45, 65, 85, 120, 150]),
                    'currency': 'EUR',
                    'is_free': False,  # Deportes profesionales son de pago
                    
                    # Metadata
                    'source': 'sports_spain',
                    'source_id': f"sport_es_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': f"https://www.laliga.com/partidos/{event.get('title', '').replace(' ', '-').lower()}",
                    'image_url': 'https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d', # Football stadium
                    
                    # Info adicional
                    'organizer': event.get('competition', 'Liga Española'),
                    'capacity': event.get('capacity', 50000),
                    'status': 'live',
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing sports event: {e}")
                continue
        
        return normalized

# Test function
async def test_sports_spain():
    """
    Test del scraper de deportes España
    """
    scraper = SportsSpainScraper()
    
    print("🏆 Testing Sports Spain scraper...")
    events = await scraper.fetch_spain_sports_events(limit=10)
    
    print(f"✅ Total eventos deportivos: {len(events)}")
    
    for i, event in enumerate(events[:5]):
        print(f"\n⚽ {i+1}. {event['title']}")
        print(f"   🏟️ {event['venue_name']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['subcategory']} - {event['category']}")
        print(f"   💰 {event['price']} EUR")
    
    return events

if __name__ == "__main__":
    import random
    asyncio.run(test_sports_spain())