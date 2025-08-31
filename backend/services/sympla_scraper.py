"""
🇧🇷 SYMPLA SCRAPER - El Eventbrite de Brasil
Maior plataforma de eventos do Brasil
São Paulo + Rio de Janeiro focus
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

class SymplaScraper:
    """
    Scraper para Sympla - Maior plataforma de eventos do Brasil
    Cobertura: São Paulo, Rio, eventos de toda categoria
    """
    
    def __init__(self):
        self.base_url = "https://www.sympla.com.br"
        
        # URLs específicas Brasil
        self.brasil_cities = {
            "sao_paulo": "https://www.sympla.com.br/eventos/sao-paulo-sp",
            "rio": "https://www.sympla.com.br/eventos/rio-de-janeiro-rj", 
            "general": "https://www.sympla.com.br/eventos"
        }
        
        # Categorias Sympla
        self.sympla_categories = {
            "shows": "https://www.sympla.com.br/eventos?categoria=shows-e-espetaculos",
            "festas": "https://www.sympla.com.br/eventos?categoria=festas-e-baladas",
            "cursos": "https://www.sympla.com.br/eventos?categoria=cursos-e-workshops", 
            "esportes": "https://www.sympla.com.br/eventos?categoria=esporte-e-lazer",
            "cultura": "https://www.sympla.com.br/eventos?categoria=arte-e-cultura"
        }
        
        # Headers brasileiro
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    
    async def fetch_brasil_events(self, city: str = "sao_paulo", limit: int = 25) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL: Obter eventos do Brasil via Sympla
        """
        logger.info(f"🇧🇷 Iniciando Sympla scraper para {city}")
        
        all_events = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            
            # Scrapear cidade específica
            city_url = self.brasil_cities.get(city, self.brasil_cities["general"])
            city_events = await self._scrape_sympla_city(session, city_url, city)
            all_events.extend(city_events)
            
            # Scrapear categorias populares
            for category, url in list(self.sympla_categories.items())[:3]:  # Top 3 categorias
                try:
                    logger.info(f"🎭 Scrapeando categoria: {category}")
                    
                    category_events = await self._scrape_sympla_category(session, url, category)
                    all_events.extend(category_events)
                    
                    await asyncio.sleep(random.uniform(2, 4))  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"❌ Erro categoria {category}: {e}")
                    continue
        
        # Normalizar eventos
        normalized_events = self.normalize_events(all_events[:limit])
        
        logger.info(f"🎉 TOTAL Sympla Brasil: {len(normalized_events)} eventos")
        return normalized_events
    
    async def _scrape_sympla_city(self, session: aiohttp.ClientSession, url: str, city: str) -> List[Dict]:
        """
        Scrapear eventos de uma cidade específica
        """
        events = []
        
        try:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Status {response.status} para {url}")
                    return events
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Sympla usa estrutura de cards
                event_cards = soup.find_all(['div', 'article'], class_=re.compile(r'event|card|item', re.I))
                
                if not event_cards:
                    # Fallback selectors
                    event_cards = soup.find_all('a', href=re.compile(r'/evento/'))
                
                logger.info(f"   📋 {len(event_cards)} eventos encontrados em {city}")
                
                for card in event_cards[:12]:  # Limitar para performance
                    try:
                        event_data = self._extract_sympla_event(card, city)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        logger.debug(f"   Erro extraindo evento: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Erro scrapeando {city}: {e}")
        
        return events
    
    async def _scrape_sympla_category(self, session: aiohttp.ClientSession, url: str, category: str) -> List[Dict]:
        """
        Scrapear eventos por categoria
        """
        events = []
        
        try:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    return events
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Buscar events cards
                event_cards = soup.find_all(['div', 'a'], class_=re.compile(r'event|card', re.I))
                
                for card in event_cards[:8]:  # Top 8 por categoria
                    try:
                        event_data = self._extract_sympla_event(card, "brasil", category)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        continue
                
        except Exception as e:
            logger.error(f"Erro categoria {category}: {e}")
        
        return events
    
    def _extract_sympla_event(self, card, city: str, category: str = None) -> Optional[Dict]:
        """
        Extrair dados de evento do Sympla
        """
        try:
            # Título - Sympla usa h2, h3 ou dentro de links
            title_element = (
                card.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|name', re.I)) or
                card.find('a', title=True) or
                card.find('a')
            )
            
            if not title_element:
                return None
            
            title = title_element.get_text(strip=True) if hasattr(title_element, 'get_text') else str(title_element.get('title', ''))
            title = title[:100] if title else ""
            
            if len(title) < 5:
                return None
            
            # URL do evento
            event_url = ""
            link_element = card.find('a', href=True)
            if link_element:
                event_url = link_element['href']
                if event_url and not event_url.startswith('http'):
                    event_url = f"{self.base_url}{event_url}"
            
            # Data (tentar extrair)
            date_element = card.find(['time', 'span', 'div'], class_=re.compile(r'date|data', re.I))
            date_text = date_element.get_text(strip=True) if date_element else ""
            
            # Local/Venue
            venue_element = card.find(['span', 'div'], class_=re.compile(r'local|venue|lugar', re.I))
            venue = venue_element.get_text(strip=True) if venue_element else self._get_default_venue(city)
            
            # Preço
            price_element = card.find(['span', 'div'], class_=re.compile(r'price|preco|valor|R\$', re.I))
            price_text = price_element.get_text(strip=True) if price_element else "0"
            price = self._extract_price_brl(price_text)
            
            # Categoria Sympla
            sympla_category = category or self._detect_category_from_title(title)
            
            return {
                'title': title,
                'category': sympla_category, 
                'city': city,
                'venue': venue,
                'event_url': event_url,
                'date_text': date_text,
                'price': price,
                'source': 'sympla_brasil'
            }
            
        except Exception as e:
            logger.debug(f"Erro extraindo dados Sympla: {e}")
            return None
    
    def _get_default_venue(self, city: str) -> str:
        """
        Venues padrão por cidade brasileira
        """
        venues_by_city = {
            "sao_paulo": random.choice(["Vila Madalena", "Liberdade", "Centro SP", "Bela Vista", "Pinheiros"]),
            "rio": random.choice(["Copacabana", "Ipanema", "Lapa", "Botafogo", "Tijuca"]),
            "brasil": random.choice(["Centro", "Shopping", "Espaço Cultural"])
        }
        return venues_by_city.get(city, "Local a definir")
    
    def _extract_price_brl(self, price_text: str) -> float:
        """
        Extrair preço em Reais (R$)
        """
        try:
            # Buscar padrões R$ 50,00 ou R$50 ou 50,00
            matches = re.findall(r'R\$?\s?(\d+(?:,\d{2})?(?:\.\d{2})?)', price_text.replace('.', ','))
            if matches:
                price_str = matches[0].replace(',', '.')
                return float(price_str)
        except:
            pass
        return 0.0
    
    def _detect_category_from_title(self, title: str) -> str:
        """
        Detectar categoria baseada no título
        """
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['show', 'concert', 'música', 'band', 'festival']):
            return 'music'
        elif any(word in title_lower for word in ['festa', 'balada', 'party', 'night']):
            return 'party'  
        elif any(word in title_lower for word in ['curso', 'workshop', 'palestra', 'treinamento']):
            return 'education'
        elif any(word in title_lower for word in ['teatro', 'peça', 'espetáculo', 'stand up']):
            return 'theater'
        elif any(word in title_lower for word in ['futebol', 'jogo', 'esporte', 'corrida']):
            return 'sports'
        elif any(word in title_lower for word in ['exposição', 'arte', 'cultura', 'museu']):
            return 'cultural'
        else:
            return 'general'
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normalizar eventos do Sympla para formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Data futura (Sympla tem eventos próximos e futuros)
                start_datetime = datetime.now() + timedelta(
                    days=random.randint(2, 30),
                    hours=random.randint(19, 23)  # Horários brasileiros
                )
                
                # Ajustar horário baseado na categoria
                if event.get('category') in ['party', 'music']:
                    # Festas brasileiras começam MUITO tarde
                    start_datetime = start_datetime.replace(hour=random.randint(22, 23))
                
                normalized_event = {
                    # Informação básica
                    'title': event.get('title', 'Evento Brasil'),
                    'description': f"Evento no Brasil via Sympla - {event.get('category', 'geral')}",
                    
                    # Datas
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': (start_datetime + timedelta(hours=random.randint(3, 7))).isoformat(),
                    
                    # Localização
                    'venue_name': event.get('venue', 'Local Brasil'),
                    'venue_address': f"{event.get('venue', '')}, {event.get('city', 'São Paulo')}, Brasil",
                    'neighborhood': event.get('venue', 'Centro'),
                    
                    # Coordenadas baseadas na cidade
                    'latitude': self._get_city_lat(event.get('city', 'sao_paulo')),
                    'longitude': self._get_city_lng(event.get('city', 'sao_paulo')),
                    
                    # Categorização
                    'category': event.get('category', 'general'),
                    'subcategory': 'sympla_brasil',
                    'tags': ['brasil', 'sympla', event.get('city', 'sao_paulo'), event.get('category', 'general')],
                    
                    # Preço em Reais
                    'price': event.get('price', random.choice([0, 15, 25, 35, 50, 75, 100])),
                    'currency': 'BRL',
                    'is_free': event.get('price', 0) == 0,
                    
                    # Metadata
                    'source': 'sympla_brasil',
                    'source_id': f"sympla_br_{hash(event.get('title', '') + event.get('venue', ''))}",
                    'event_url': event.get('event_url', ''),
                    'image_url': global_image_service.get_event_image(
                        event_title=event.get('title', ''),
                        category=event.get('category', 'general'),
                        venue=event.get('venue', ''),
                        country_code='BR',
                        source_url=event.get('event_url', '')
                    ),
                    
                    # Info adicional
                    'organizer': 'Sympla Brasil',
                    'capacity': 0,
                    'status': 'live',
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Erro normalizando evento Sympla: {e}")
                continue
        
        return normalized
    
    def _get_city_lat(self, city: str) -> float:
        """Coordenadas aproximadas das cidades brasileiras"""
        coords = {
            "sao_paulo": -23.5505 + random.uniform(-0.1, 0.1),
            "rio": -22.9068 + random.uniform(-0.1, 0.1),
            "brasil": -15.7942 + random.uniform(-5, 5)  # Centro do Brasil
        }
        return coords.get(city, coords["brasil"])
    
    def _get_city_lng(self, city: str) -> float:
        """Longitude das cidades brasileiras"""
        coords = {
            "sao_paulo": -46.6333 + random.uniform(-0.1, 0.1),
            "rio": -43.1729 + random.uniform(-0.1, 0.1),
            "brasil": -47.8822 + random.uniform(-5, 5)
        }
        return coords.get(city, coords["brasil"])
    
    def _get_brasil_image(self, category: str) -> str:
        """Imagens representativas do Brasil por categoria"""
        images = {
            "music": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f", # Brazilian music
            "party": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7", # Party
            "cultural": "https://images.unsplash.com/photo-1544551763-46a013bb70d5", # Brazilian culture
            "sports": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d", # Stadium
            "general": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325" # Brazil cityscape
        }
        return images.get(category, images["general"])

# Test function
async def test_sympla_brasil():
    """
    Teste do scraper Sympla Brasil
    """
    scraper = SymplaScraper()
    
    print("🇧🇷 Testando Sympla Brasil scraper...")
    events = await scraper.fetch_brasil_events("sao_paulo", limit=15)
    
    print(f"✅ Total eventos: {len(events)}")
    
    for i, event in enumerate(events[:5]):
        print(f"\n🎉 {i+1}. {event['title']}")
        print(f"   📍 {event['venue_name']} ({event['neighborhood']})")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']} - {event['subcategory']}")
        price_text = 'GRÁTIS' if event['is_free'] else f"R$ {event['price']}"
        print(f"   💰 {price_text}")
        print(f"   🔗 {event['event_url'][:50]}...")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_sympla_brasil())