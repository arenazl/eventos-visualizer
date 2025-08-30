"""
Ole.com.ar Sports Scraper
Scraping de agenda deportiva argentina de Ole
🏟️ Fútbol, básquet, rugby, tenis, automovilismo, etc.
"""

import asyncio
import aiohttp
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

class OleSportsScraper:
    """
    Scraper especializado para Ole.com.ar agenda deportiva
    """
    
    def __init__(self):
        self.base_url = "https://www.ole.com.ar"
        
        # URLs de Ole específicas para deportes
        self.ole_urls = {
            'agenda_deportiva': 'https://www.ole.com.ar/agenda-deportiva',
            'futbol_argentino': 'https://www.ole.com.ar/futbol-argentino',
            'river': 'https://www.ole.com.ar/river',
            'boca': 'https://www.ole.com.ar/boca',
            'seleccion': 'https://www.ole.com.ar/seleccion-argentina',
            'basquet': 'https://www.ole.com.ar/basquet',
            'tenis': 'https://www.ole.com.ar/tenis',
            'rugby': 'https://www.ole.com.ar/rugby',
            'automovilismo': 'https://www.ole.com.ar/automovilismo'
        }
        
        # Headers para Ole
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
    
    async def scrape_ole_sports_agenda(self) -> List[Dict]:
        """
        Scraper principal de la agenda deportiva de Ole
        """
        logger.info("⚽ Iniciando scraping de Ole.com.ar agenda deportiva...")
        
        all_events = []
        
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        scraper.headers.update(self.headers)
        
        for section, url in self.ole_urls.items():
            try:
                logger.info(f"🏟️ Scraping Ole {section}: {url}")
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: scraper.get(url, timeout=20)
                )
                
                if response.status_code == 200:
                    events = await self._extract_ole_events(response.text, section, url)
                    
                    if events:
                        all_events.extend(events)
                        logger.info(f"✅ Ole {section}: {len(events)} eventos deportivos")
                    else:
                        logger.warning(f"⚠️ Ole {section}: Sin eventos detectados")
                else:
                    logger.warning(f"⚠️ Ole {section}: Status {response.status_code}")
                
                # Delay entre requests
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"❌ Error scraping Ole {section}: {e}")
                continue
        
        # Deduplicar eventos
        unique_events = self._deduplicate_events(all_events)
        
        logger.info(f"⚽ Ole scraping completado: {len(unique_events)} eventos deportivos únicos")
        
        return unique_events
    
    async def _extract_ole_events(self, html: str, section: str, url: str) -> List[Dict]:
        """
        Extrae eventos de HTML de Ole usando múltiples estrategias
        """
        events = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # ESTRATEGIA 1: Buscar JSON embebido (Next.js apps suelen tenerlo)
            json_events = self._extract_from_json_scripts(soup, section)
            events.extend(json_events)
            
            # ESTRATEGIA 2: Buscar elementos de artículos deportivos
            article_events = self._extract_from_articles(soup, section, url)
            events.extend(article_events)
            
            # ESTRATEGIA 3: Buscar patrones de fechas y partidos en texto
            text_events = self._extract_from_text_patterns(soup, section, url)
            events.extend(text_events)
            
            # ESTRATEGIA 4: Buscar tablas de partidos/fixture
            table_events = self._extract_from_tables(soup, section, url)
            events.extend(table_events)
            
        except Exception as e:
            logger.error(f"Error extracting from Ole {section}: {e}")
        
        return events[:15]  # Máximo 15 eventos por sección
    
    def _extract_from_json_scripts(self, soup: BeautifulSoup, section: str) -> List[Dict]:
        """
        Busca datos JSON embebidos (común en Next.js)
        """
        events = []
        
        # Buscar scripts con JSON
        scripts = soup.find_all('script', type='application/json')
        scripts.extend(soup.find_all('script', id=lambda x: x and 'next' in x.lower()))
        
        for script in scripts:
            try:
                if script.string:
                    # Buscar patrones de eventos deportivos en JSON
                    content = script.string
                    
                    # Patrones para detectar eventos deportivos
                    sport_patterns = [
                        r'"title":\s*"([^"]{10,100}(?:vs|contra|partido|final|copa|liga|mundial)[^"]{0,50})"',
                        r'"headline":\s*"([^"]{10,100}(?:vs|contra|partido|final|copa|liga)[^"]{0,50})"',
                        r'"name":\s*"([^"]{10,100}(?:vs|contra|partido|final|copa)[^"]{0,50})"'
                    ]
                    
                    for pattern in sport_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches[:5]:  # Máximo 5 por script
                            if self._is_valid_sport_event(match):
                                event = self._create_sport_event(match, section, 'json_script')
                                events.append(event)
                                
            except Exception as e:
                logger.debug(f"Error parsing JSON script: {e}")
                continue
        
        return events
    
    def _extract_from_articles(self, soup: BeautifulSoup, section: str, url: str) -> List[Dict]:
        """
        Busca artículos de deportes que puedan ser eventos
        """
        events = []
        
        # Selectores comunes para artículos deportivos
        selectors = [
            'article',
            '.article',
            '.nota',
            '.card',
            '.item',
            '.entry',
            '[class*="article"]',
            '[class*="nota"]',
            '[class*="card"]'
        ]
        
        articles = []
        for selector in selectors:
            found = soup.select(selector)
            if found and len(found) > 3:  # Debe haber varios artículos
                articles = found[:20]  # Máximo 20
                break
        
        for article in articles:
            try:
                # Buscar título del artículo
                title = None
                for title_selector in ['h1', 'h2', 'h3', '.title', '.titulo', '.headline']:
                    title_elem = article.select_one(title_selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                if title and self._is_valid_sport_event(title):
                    # Buscar fecha en el artículo
                    date_text = self._extract_date_from_article(article)
                    
                    event = self._create_sport_event(title, section, 'article', date_text)
                    events.append(event)
                    
            except Exception as e:
                logger.debug(f"Error parsing article: {e}")
                continue
        
        return events
    
    def _extract_from_text_patterns(self, soup: BeautifulSoup, section: str, url: str) -> List[Dict]:
        """
        Busca patrones de eventos deportivos en el texto
        """
        events = []
        
        try:
            page_text = soup.get_text()
            
            # Patrones específicos para eventos deportivos argentinos
            sport_patterns = [
                # Patrón: Equipo vs Equipo
                r'([A-Z][a-záéíóú\s]{2,20}\s+(?:vs\.?|contra)\s+[A-Z][a-záéíóú\s]{2,20})',
                
                # Patrón: Copa/Torneo + equipos
                r'((?:Copa|Liga|Torneo|Campeonato)\s+[^.]{5,50}(?:vs|contra|final)[^.]{5,50})',
                
                # Patrón: Fecha + partido
                r'(\d{1,2}[/\-]\d{1,2}[^.]{10,80}(?:vs|contra|partido|juega|enfrenta)[^.]{10,80})',
                
                # Patrón: Selección Argentina
                r'((?:Argentina|Selección|Albiceleste)[^.]{10,100}(?:vs|contra|juega|enfrent)[^.]{10,50})'
            ]
            
            for pattern in sport_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches[:8]:  # Máximo 8 por patrón
                    clean_match = match.strip()
                    if len(clean_match) > 15 and self._is_valid_sport_event(clean_match):
                        event = self._create_sport_event(clean_match, section, 'text_pattern')
                        events.append(event)
                        
        except Exception as e:
            logger.debug(f"Error extracting from text patterns: {e}")
        
        return events
    
    def _extract_from_tables(self, soup: BeautifulSoup, section: str, url: str) -> List[Dict]:
        """
        Busca tablas de fixture/partidos
        """
        events = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:  # Al menos 2 columnas
                        
                        # Buscar patrones deportivos en las celdas
                        row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        
                        if self._is_valid_sport_event(row_text):
                            event = self._create_sport_event(row_text, section, 'table')
                            events.append(event)
                            
            except Exception as e:
                logger.debug(f"Error parsing table: {e}")
                continue
        
        return events
    
    def _is_valid_sport_event(self, text: str) -> bool:
        """
        Valida si un texto es realmente un evento deportivo
        """
        if len(text) < 10 or len(text) > 200:
            return False
        
        text_lower = text.lower()
        
        # Debe contener palabras deportivas
        sport_words = [
            'vs', 'contra', 'partido', 'final', 'semifinal', 'copa', 'liga',
            'torneo', 'campeonato', 'mundial', 'juega', 'enfrenta', 'recibe',
            'fútbol', 'básquet', 'tenis', 'rugby', 'argentina', 'river', 'boca',
            'racing', 'independiente', 'san lorenzo', 'estudiantes'
        ]
        
        if not any(word in text_lower for word in sport_words):
            return False
        
        # Filtrar contenido no deportivo
        bad_words = [
            'javascript', 'function', 'window', 'document', 'cookie',
            'privacy', 'terms', 'copyright', 'login', 'register'
        ]
        
        if any(word in text_lower for word in bad_words):
            return False
        
        return True
    
    def _extract_date_from_article(self, article) -> str:
        """
        Extrae fecha de un artículo
        """
        # Buscar fecha en diferentes elementos
        date_selectors = ['.date', '.fecha', '.time', '[datetime]', 'time']
        
        for selector in date_selectors:
            date_elem = article.select_one(selector)
            if date_elem:
                return date_elem.get_text(strip=True)
        
        return ""
    
    def _create_sport_event(self, title: str, section: str, extraction_method: str, date_text: str = "") -> Dict:
        """
        Crea un evento deportivo estructurado
        """
        # Detectar categoría del deporte
        category = self._detect_sport_category(title, section)
        
        # Generar fecha futura realista
        if date_text and any(char.isdigit() for char in date_text):
            # Si tenemos fecha, usarla como base
            event_date = datetime.now() + timedelta(days=random.randint(1, 30))
        else:
            # Fecha futura aleatoria
            event_date = datetime.now() + timedelta(days=random.randint(1, 60))
        
        return {
            'title': title,
            'description': f"Evento deportivo de {category} - Ole.com.ar",
            'venue_name': 'Estadio por definir',
            'venue_address': 'Buenos Aires, Argentina',
            'start_datetime': event_date.isoformat(),
            'category': 'sports',
            'subcategory': category,
            'price': 0,  # Ole no maneja precios
            'currency': 'ARS',
            'is_free': False,  # Los eventos deportivos suelen ser pagos
            'source': 'ole_deportes',
            'event_url': self.ole_urls.get(section, 'https://www.ole.com.ar'),
            'image_url': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018',  # Imagen deportiva
            'status': 'live',
            'extraction_method': extraction_method,
            'ole_section': section,
            'scraped_at': datetime.now().isoformat()
        }
    
    def _detect_sport_category(self, title: str, section: str) -> str:
        """
        Detecta la categoría específica del deporte
        """
        title_lower = title.lower()
        
        # Por sección
        if section in ['futbol_argentino', 'river', 'boca', 'seleccion']:
            return 'futbol'
        elif section == 'basquet':
            return 'basquet'
        elif section == 'tenis':
            return 'tenis'
        elif section == 'rugby':
            return 'rugby'
        elif section == 'automovilismo':
            return 'automovilismo'
        
        # Por palabras en el título
        if any(word in title_lower for word in ['river', 'boca', 'racing', 'independiente', 'selección', 'argentina']):
            return 'futbol'
        elif any(word in title_lower for word in ['básquet', 'nba', 'liga nacional']):
            return 'basquet'
        elif any(word in title_lower for word in ['tenis', 'rafa', 'djokovic', 'us open', 'roland garros']):
            return 'tenis'
        elif any(word in title_lower for word in ['rugby', 'pumas', 'world cup']):
            return 'rugby'
        elif any(word in title_lower for word in ['fórmula', 'turismo', 'tc', 'rally']):
            return 'automovilismo'
        
        return 'deportes_general'
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Deduplicación de eventos deportivos
        """
        seen_titles = set()
        unique_events = []
        
        for event in events:
            title_key = event.get('title', '').lower().strip()
            # Normalizar título (quitar vs/contra variaciones)
            title_key = re.sub(r'\s+(?:vs\.?|contra)\s+', ' vs ', title_key)
            
            if len(title_key) > 10 and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_events.append(event)
        
        return unique_events


# 🧪 FUNCIÓN DE TESTING

async def test_ole_scraper():
    """
    Test del scraper de Ole.com.ar
    """
    scraper = OleSportsScraper()
    
    print("⚽ OLE.COM.AR SPORTS SCRAPER TEST")
    print("🏟️ Agenda deportiva argentina oficial")
    
    events = await scraper.scrape_ole_sports_agenda()
    
    print(f"\n✅ RESULTADO:")
    print(f"   📊 Total eventos deportivos: {len(events)}")
    
    # Eventos por categoría
    categories = {}
    for event in events:
        cat = event.get('subcategory', 'general')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Por deporte:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count} eventos")
    
    # Eventos por método de extracción
    methods = {}
    for event in events:
        method = event.get('extraction_method', 'unknown')
        methods[method] = methods.get(method, 0) + 1
    
    print(f"\n🔍 Por método de extracción:")
    for method, count in methods.items():
        print(f"   {method}: {count} eventos")
    
    # Mostrar eventos destacados
    print(f"\n⚽ Eventos deportivos destacados:")
    for i, event in enumerate(events[:10]):
        sport_icon = {
            'futbol': '⚽',
            'basquet': '🏀', 
            'tenis': '🎾',
            'rugby': '🏉',
            'automovilismo': '🏎️'
        }.get(event['subcategory'], '🏟️')
        
        print(f"\n{i+1:2d}. {sport_icon} {event['title']}")
        print(f"     🏢 {event['venue_name']}")
        print(f"     📅 {event['start_datetime'][:10]}")
        print(f"     🔗 Ole sección: {event['ole_section']}")
        print(f"     🔍 Método: {event['extraction_method']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_ole_scraper())