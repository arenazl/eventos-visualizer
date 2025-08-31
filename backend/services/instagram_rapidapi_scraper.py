"""
📸 Instagram RapidAPI Events Scraper
Instagram events discovery using RapidAPI Instagram API
"""

import aiohttp
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
try:
    from .city_scraper_factory import BaseGlobalScraper
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.city_scraper_factory import BaseGlobalScraper

logger = logging.getLogger(__name__)

class InstagramRapidApiScraper(BaseGlobalScraper):
    """
    Global scraper para Instagram usando RapidAPI
    Busca eventos en cuentas públicas relacionadas con eventos
    """
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY") or os.getenv("RAPIDAPI_INSTAGRAM_KEY")
        self.base_url = "https://instagram120.p.rapidapi.com/api/instagram"
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "instagram120.p.rapidapi.com"
        }
        
        # Palabras clave para identificar eventos
        self.event_keywords = [
            'evento', 'event', 'concierto', 'concert', 'festival',
            'conferencia', 'conference', 'exposición', 'exhibition',
            'show', 'presentación', 'meetup', 'workshop', 'taller',
            'seminario', 'webinar', 'charla', 'talk', 'feria',
            'inauguración', 'opening', 'lanzamiento', 'launch',
            'entrada gratis', 'free entry', 'boletos', 'tickets',
            'registro', 'registration', 'cupos limitados', 'limited seats',
            'próximo', 'coming', 'soon', 'save the date', 'reserva'
        ]
        
        # Patrones para detectar fechas y horarios
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # DD/MM/YYYY
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # DD-MM-YYYY
            r'\d{1,2}\s+de\s+\w+',       # 15 de marzo
            r'(lunes|martes|miércoles|jueves|viernes|sábado|domingo)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'\d{1,2}:\d{2}\s*(am|pm|AM|PM)?',  # Horarios
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        ]
        
        # Cuentas de eventos por ubicación
        self.location_accounts = {
            "Buenos Aires": [
                "timeoutbuenosaires", "buenosairesciudad", "ccrecoleta", 
                "usina_del_arte", "teatrocolon", "lunaparkoficial",
                "estadiolunaPark", "hipodromopalermo"
            ],
            "Madrid": [
                "timeoutmadrid", "madrid", "teatroreal", "circuitomadrid",
                "madridcultura", "ifema_madrid", "palaciovistalegre"
            ],
            "Barcelona": [
                "timeoutbarcelona", "barcelona_cat", "palausantjordi",
                "liceuopera", "auditori_bcn", "musicafestival"
            ],
            "Miami": [
                "timeoutmiami", "miamibeach", "americanairlines_arena",
                "adriennearsht", "miamibeachconvention", "sobemiami"
            ],
            "New York": [
                "timeout", "nyc", "madisonsquaregarden", "metmuseum",
                "lincolncenter", "brooklyn_museum", "centralpark"
            ],
            "London": [
                "timeoutlondon", "london", "royaloperahouse", "o2arena",
                "southbankcentre", "barbican", "tatemuseum"
            ]
        }
        
        # Cuentas globales de eventos
        self.global_event_accounts = [
            "eventbrite", "timeout", "sofarsounds", "tedx",
            "lollapalooza", "coachella", "tomorrowland",
            "burning_man", "sxsw", "cannes"
        ]

    async def fetch_events(self, location: str, country: str = None) -> Dict[str, Any]:
        """
        Fetch events from Instagram using location-specific accounts
        """
        if not self.api_key:
            logger.warning("⚠️ Instagram RapidAPI key not found in .env")
            return {"source": "Instagram RapidAPI", "events": [], "total": 0, "status": "no_api_key"}
        
        try:
            # Determinar cuentas basadas en ubicación
            accounts = self._get_accounts_for_location(location)
            
            # Buscar eventos en las cuentas
            events = await self._search_events_from_accounts(accounts, location)
            
            logger.info(f"✅ Instagram: {len(events)} eventos para {location}")
            
            return {
                "source": "Instagram RapidAPI",
                "location": location,
                "events": events,
                "total": len(events),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Instagram RapidAPI error for {location}: {e}")
            return {"source": "Instagram RapidAPI", "events": [], "total": 0, "status": "error", "error": str(e)}

    def _get_accounts_for_location(self, location: str) -> List[str]:
        """
        Obtiene cuentas de Instagram relevantes para una ubicación
        """
        location_lower = location.lower()
        accounts = []
        
        # Buscar cuentas específicas de la ubicación
        for city, city_accounts in self.location_accounts.items():
            if city.lower() in location_lower:
                accounts.extend(city_accounts)
                break
        
        # Agregar algunas cuentas globales
        accounts.extend(self.global_event_accounts[:3])  # Top 3 global accounts
        
        # Si no se encontraron cuentas específicas, usar solo globales
        if len(accounts) <= 3:
            accounts = self.global_event_accounts[:6]
        
        return list(set(accounts))  # Remover duplicados

    async def _search_events_from_accounts(self, accounts: List[str], location: str) -> List[Dict[str, Any]]:
        """
        Busca eventos en múltiples cuentas de Instagram
        """
        all_events = []
        max_posts_per_account = 10  # Limitar para performance
        
        # Limitar a 5 cuentas por request para evitar timeouts
        accounts = accounts[:5]
        
        tasks = []
        for account in accounts:
            task = self._get_posts_from_account(account, max_posts_per_account, location)
            tasks.append(task)
        
        # Ejecutar en paralelo con timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            account = accounts[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Instagram error for @{account}: {result}")
            elif isinstance(result, list):
                all_events.extend(result)
                logger.debug(f"✅ Instagram @{account}: {len(result)} eventos")
        
        return all_events

    async def _get_posts_from_account(self, username: str, max_posts: int, location: str) -> List[Dict[str, Any]]:
        """
        Obtiene posts de una cuenta específica y extrae eventos
        """
        events = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)  # Timeout corto
            async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
                
                url = f"{self.base_url}/posts"
                payload = {
                    "username": username,
                    "count": min(max_posts, 12)  # Instagram API limit
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'data' in data and 'posts' in data['data']:
                            posts = data['data']['posts']
                            
                            for post in posts:
                                if self._is_event_post(post):
                                    event = self._extract_event_info(post, username, location)
                                    if event:
                                        events.append(event)
                    
                    elif response.status == 429:
                        logger.warning(f"⚠️ Instagram API rate limit for @{username}")
                    elif response.status == 401:
                        logger.error("❌ Instagram API: Invalid RapidAPI key")
                    else:
                        logger.warning(f"⚠️ Instagram API HTTP {response.status} for @{username}")
        
        except Exception as e:
            logger.error(f"❌ Instagram request failed for @{username}: {e}")
        
        return events

    def _is_event_post(self, post: Dict) -> bool:
        """
        Determina si un post es sobre un evento
        """
        # Obtener el texto del post (caption)
        caption_obj = post.get('caption', {})
        if isinstance(caption_obj, dict):
            caption = caption_obj.get('text', '').lower()
        else:
            caption = str(caption_obj).lower()
        
        if not caption:
            return False
        
        # Verificar si contiene palabras clave de eventos
        has_event_keyword = any(keyword in caption for keyword in self.event_keywords)
        
        # Verificar si contiene fechas o horarios
        has_date = any(re.search(pattern, caption, re.IGNORECASE) for pattern in self.date_patterns)
        
        # Un post es considerado evento si tiene palabras clave Y/O fechas/horarios
        return has_event_keyword or has_date

    def _extract_event_info(self, post: Dict, account: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información relevante del evento de Instagram
        """
        try:
            # Obtener caption
            caption_obj = post.get('caption', {})
            if isinstance(caption_obj, dict):
                caption = caption_obj.get('text', '')
            else:
                caption = str(caption_obj)
            
            if not caption:
                return None
            
            # Información básica
            title = self._extract_title_from_caption(caption)
            if not title:
                title = f"Evento en @{account}"
            
            # Fecha estimada (usar timestamp del post + algunos días para eventos futuros)
            timestamp = post.get('taken_at_timestamp', int(datetime.now().timestamp()))
            post_date = datetime.fromtimestamp(timestamp)
            
            # Si encontramos fechas en el caption, usarlas como referencia
            dates_found = []
            for pattern in self.date_patterns:
                matches = re.findall(pattern, caption, re.IGNORECASE)
                dates_found.extend(matches[:2])  # Max 2 fechas
            
            # Fecha del evento (estimada como 1-30 días después del post)
            event_date = post_date + timedelta(days=7)  # Default: 1 semana después
            
            # Imagen
            image_url = post.get('display_url', '') or post.get('thumbnail_src', '')
            
            # Engagement metrics
            likes = 0
            comments = 0
            
            if isinstance(post.get('edge_liked_by'), dict):
                likes = post['edge_liked_by'].get('count', 0)
            if isinstance(post.get('edge_media_to_comment'), dict):
                comments = post['edge_media_to_comment'].get('count', 0)
            
            # Verificar que el evento tenga engagement mínimo
            if likes < 5:  # Filtrar posts con muy poco engagement
                return None
            
            return {
                "title": title[:200],
                "description": caption[:300],
                "start_datetime": event_date.isoformat(),
                "venue_name": f"Venue en {location}",
                "venue_address": location,
                "category": self._categorize_from_caption(caption),
                "price": 0,  # Instagram no suele tener precios
                "currency": "USD",
                "is_free": True,  # Asumir gratis por defecto
                "image_url": image_url,
                "event_url": f"https://www.instagram.com/p/{post.get('shortcode', '')}/",
                "latitude": None,
                "longitude": None,
                "external_id": post.get('id', ''),
                "source": "instagram_rapidapi",
                "status": "active",
                "engagement": {
                    "likes": likes,
                    "comments": comments,
                    "account": account
                },
                "dates_mentioned": dates_found
            }
            
        except Exception as e:
            logger.error(f"Error processing Instagram post: {e}")
            return None

    def _extract_title_from_caption(self, caption: str) -> str:
        """
        Extrae un título del caption de Instagram
        """
        # Tomar las primeras líneas o hasta el primer hashtag
        lines = caption.split('\n')
        title_parts = []
        
        for line in lines[:3]:  # Máximo 3 líneas
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('@'):
                title_parts.append(line)
            elif line.startswith('#'):
                break
        
        title = ' '.join(title_parts)
        
        # Limpiar y limitar
        title = re.sub(r'[^\w\s\-.,!?áéíóúñü]', '', title)
        return title[:100] if title else ""

    def _categorize_from_caption(self, caption: str) -> str:
        """
        Categoriza el evento basado en el contenido del caption
        """
        caption_lower = caption.lower()
        
        # Música
        if any(word in caption_lower for word in ['concierto', 'concert', 'música', 'music', 'festival', 'dj', 'band']):
            return 'music'
        
        # Cultural
        elif any(word in caption_lower for word in ['arte', 'art', 'museo', 'museum', 'exhibition', 'exposición']):
            return 'cultural'
        
        # Tech
        elif any(word in caption_lower for word in ['tech', 'startup', 'conference', 'webinar', 'workshop']):
            return 'tech'
        
        # Deportes
        elif any(word in caption_lower for word in ['deporte', 'sport', 'game', 'match', 'tournament']):
            return 'sports'
        
        return 'general'

# Función de testing
async def test_instagram_rapidapi_scraper():
    """
    Test function para Instagram RapidAPI scraper
    """
    scraper = InstagramRapidApiScraper()
    
    test_locations = ["Miami", "Buenos Aires", "New York", "Madrid"]
    
    for location in test_locations:
        print(f"\n📸 Testing Instagram RapidAPI for: {location}")
        result = await scraper.fetch_events(location)
        
        print(f"   Status: {result['status']}")
        print(f"   Events: {result['total']}")
        
        if result['events']:
            for event in result['events'][:3]:  # Mostrar primeros 3
                print(f"   🎉 {event['title']} - @{event['engagement']['account']} ({event['category']})")
                print(f"       ❤️ {event['engagement']['likes']} likes")

async def test_with_barcelona():
    """
    Test específico con Barcelona
    """
    scraper = InstagramRapidApiScraper()
    
    print("📸 INICIANDO Instagram RapidAPI Scraper con BARCELONA...")
    print(f"🏙️ Ciudad: Barcelona")
    print(f"🗝️ API Key configurado: {'✅' if scraper.api_key else '❌'}")
    
    if not scraper.api_key:
        print("⚠️ RAPIDAPI_KEY no configurado")
        print("📋 Para usar este scraper:")
        print("   1. Conseguir API key en RapidAPI")
        print("   2. Agregar a .env: RAPIDAPI_KEY=tu_key_aqui")
        print("   3. Reiniciar servidor")
        return []
    
    # Test scraping con Barcelona
    result = await scraper.fetch_events("Barcelona")
    
    print(f"\n🎯 RESULTADOS Barcelona Instagram:")
    print(f"   📊 Status: {result['status']}")
    print(f"   📊 Total eventos: {result['total']}")
    print(f"   📊 Source: {result['source']}")
    print(f"   📊 Location: {result['location']}")
    
    if result['events']:
        print(f"\n📸 Eventos de Barcelona:")
        for i, event in enumerate(result['events'][:10]):
            print(f"\n{i+1:2d}. 📸 {event['title'][:60]}...")
            print(f"     👤 @{event['engagement']['account']}")
            print(f"     🎪 {event.get('category', 'general')}")
            print(f"     ❤️ {event['engagement']['likes']} likes")
    else:
        print("⚠️ No se encontraron eventos en Barcelona")
    
    return result['events']

if __name__ == "__main__":
    asyncio.run(test_with_barcelona())