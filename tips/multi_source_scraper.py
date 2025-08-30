#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MULTI-SOURCE EVENT SCRAPER - PALERMO BUENOS AIRES
Scraper completo para eventos de Facebook + Eventbrite + Instagram
Incluye agregador de múltiples fuentes
"""

from playwright.sync_api import sync_playwright
import json
import re
from datetime import datetime, timedelta
import time
import random
import sys
import os
import requests
from bs4 import BeautifulSoup

class MultiSourceEventScraper:
    def __init__(self):
        self.events = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def scrape_all_sources(self, location="palermo buenos aires", max_per_source=15):
        """
        Scraper principal que combina todas las fuentes
        
        Args:
            location (str): Ubicación a buscar
            max_per_source (int): Máximo eventos por fuente
            
        Returns:
            dict: Eventos agrupados por fuente
        """
        
        print(f"🚀 INICIANDO SCRAPING MULTI-FUENTE")
        print(f"📍 Ubicación: {location}")
        print(f"🎯 Máximo por fuente: {max_per_source}")
        print("="*80)
        
        all_events = {}
        
        # 1. Facebook Events
        print("\n📘 SCRAPEANDO FACEBOOK...")
        facebook_events = self.scrape_facebook_events(location, max_per_source)
        all_events['facebook'] = facebook_events
        print(f"✅ Facebook: {len(facebook_events)} eventos")
        
        # 2. Eventbrite  
        print("\n🎫 SCRAPEANDO EVENTBRITE...")
        eventbrite_events = self.scrape_eventbrite_events(location, max_per_source)
        all_events['eventbrite'] = eventbrite_events
        print(f"✅ Eventbrite: {len(eventbrite_events)} eventos")
        
        # 3. Instagram hashtags públicos
        print("\n📸 SCRAPEANDO INSTAGRAM...")
        instagram_events = self.scrape_instagram_events(location, max_per_source)
        all_events['instagram'] = instagram_events
        print(f"✅ Instagram: {len(instagram_events)} eventos")
        
        # 4. Fuentes argentinas específicas
        print("\n🇦🇷 SCRAPEANDO FUENTES ARGENTINAS...")
        argentina_events = self.scrape_argentina_sources(location, max_per_source)
        all_events['argentina'] = argentina_events
        print(f"✅ Fuentes Argentinas: {len(argentina_events)} eventos")
        
        # Resumen
        total_events = sum(len(events) for events in all_events.values())
        print(f"\n🎉 TOTAL COMBINADO: {total_events} eventos de {len(all_events)} fuentes")
        
        return all_events
    
    def scrape_facebook_events(self, location, max_events):
        """Scraper de Facebook Events (método ya probado)"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.headers['User-Agent'],
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires'
            )
            
            page = context.new_page()
            
            try:
                page.set_extra_http_headers(self.headers)
                
                search_query = location.replace(' ', '%20')
                url = f"https://www.facebook.com/events/search/?q={search_query}"
                
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(3)
                
                # Scroll para cargar más
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                content = page.text_content('body')
                events = self._parse_facebook_content(content, max_events)
                
                return events
                
            except Exception as e:
                print(f"⚠️ Error Facebook: {e}")
                return []
            finally:
                browser.close()
    
    def scrape_eventbrite_events(self, location, max_events):
        """Scraper de Eventbrite (método requests)"""
        
        events = []
        
        try:
            # URLs de Eventbrite Argentina
            urls = [
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/palermo/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/agosto/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_events = self._parse_eventbrite_page(soup)
                        events.extend(page_events)
                        
                        if len(events) >= max_events:
                            break
                            
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"⚠️ Error en URL {url}: {e}")
                    continue
            
            return events[:max_events]
            
        except Exception as e:
            print(f"⚠️ Error general Eventbrite: {e}")
            return []
    
    def scrape_instagram_events(self, location, max_events):
        """Scraper de Instagram vía hashtags públicos"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=self.headers['User-Agent'])
            page = context.new_page()
            
            events = []
            
            try:
                # Hashtags relevantes para Palermo
                hashtags = ['palermo', 'palermosoho', 'palermohollywood', 'eventospalermo', 'buenosaires']
                
                for hashtag in hashtags[:2]:  # Limitar para evitar bloqueos
                    try:
                        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
                        page.goto(url, timeout=20000)
                        time.sleep(2)
                        
                        # Buscar posts que mencionen eventos
                        content = page.text_content('body')
                        hashtag_events = self._parse_instagram_content(content, hashtag)
                        events.extend(hashtag_events)
                        
                        if len(events) >= max_events:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Error hashtag {hashtag}: {e}")
                        continue
                
                return events[:max_events]
                
            except Exception as e:
                print(f"⚠️ Error Instagram: {e}")
                return []
            finally:
                browser.close()
    
    def scrape_argentina_sources(self, location, max_events):
        """Scraper de fuentes argentinas específicas"""
        
        events = []
        
        try:
            # Fuentes argentinas confiables
            sources = [
                {
                    'name': 'Buenos Aires Turismo',
                    'url': 'https://turismo.buenosaires.gob.ar/es/eventos2025',
                    'parser': self._parse_buenosaires_gov
                },
                {
                    'name': 'TimeOut Buenos Aires', 
                    'url': 'https://www.timeout.com/buenos-aires/events',
                    'parser': self._parse_timeout_ba
                },
                {
                    'name': 'La Rural Buenos Aires',
                    'url': 'https://larural.com.ar/calendario/',
                    'parser': self._parse_larural
                }
            ]
            
            for source in sources:
                try:
                    print(f"   📡 Scrapeando {source['name']}...")
                    response = requests.get(source['url'], headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        source_events = source['parser'](soup, source['name'])
                        events.extend(source_events)
                        print(f"      ✅ {len(source_events)} eventos de {source['name']}")
                    
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"   ⚠️ Error {source['name']}: {e}")
                    continue
            
            return events[:max_events]
            
        except Exception as e:
            print(f"⚠️ Error fuentes argentinas: {e}")
            return []
    
    def _parse_facebook_content(self, content, max_events):
        """Parser para contenido de Facebook"""
        events = []
        lines = content.split('\n')
        
        date_patterns = [
            r'[A-Z][a-z]{2,3}, \d{1,2} de [a-z]{3,4}\.? a las \d{1,2}:\d{2}',
            r'[A-Z][a-z]{2,3}, \d{1,2} de [a-z]{3,4}\.?',
        ]
        
        i = 0
        while i < len(lines) and len(events) < max_events:
            line = lines[i].strip()
            
            for pattern in date_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    event = self._extract_facebook_event(lines, i)
                    if event:
                        events.append(event)
                        i += 5
                        break
            else:
                i += 1
        
        return events
    
    def _extract_facebook_event(self, lines, start_idx):
        """Extraer evento individual de Facebook"""
        try:
            max_idx = min(start_idx + 8, len(lines))
            event_lines = [lines[i].strip() for i in range(start_idx, max_idx)]
            
            date_line = event_lines[0] if event_lines else ""
            title = ""
            location = "Palermo, Buenos Aires"
            attendance = ""
            
            # Buscar título
            for line in event_lines[1:]:
                if line and len(line) > 10 and not self._is_facebook_metadata(line):
                    title = line
                    break
            
            # Buscar ubicación y asistencia
            for line in event_lines:
                if any(loc in line.lower() for loc in ['palermo', 'buenos aires', 'cabrera', 'avenida']):
                    location = line
                elif re.search(r'\d+\s*(interesados|asistirán)', line):
                    attendance = line
            
            if not title or len(title) < 10:
                return None
            
            return {
                'title': title[:150],
                'date': date_line[:100],
                'location': location[:100],
                'attendance': attendance or "Sin datos",
                'source': 'Facebook',
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception:
            return None
    
    def _is_facebook_metadata(self, line):
        """Detectar metadata de Facebook"""
        meta_words = ['facebook', 'iniciar sesión', 'contraseña', 'eventos', 'buscar']
        return any(word in line.lower() for word in meta_words)
    
    def _parse_eventbrite_page(self, soup):
        """Parser para páginas de Eventbrite"""
        events = []
        
        try:
            # Buscar contenedores de eventos
            event_containers = soup.find_all(['div', 'article'], class_=lambda x: x and 'event' in str(x).lower() if x else False)
            
            for container in event_containers:
                try:
                    title_elem = container.find(['h1', 'h2', 'h3', 'a'])
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    if len(title) > 10:
                        events.append({
                            'title': title[:150],
                            'date': "Verificar en Eventbrite",
                            'location': "Palermo, Buenos Aires",
                            'attendance': "Ver en plataforma",
                            'source': 'Eventbrite',
                            'extracted_at': datetime.now().isoformat()
                        })
                
                except Exception:
                    continue
            
            return events
            
        except Exception:
            return []
    
    def _parse_instagram_content(self, content, hashtag):
        """Parser para contenido de Instagram"""
        events = []
        
        try:
            # Buscar menciones de eventos en el contenido
            event_keywords = ['evento', 'show', 'concierto', 'festival', 'expo', 'feria']
            
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in event_keywords):
                    if len(line.strip()) > 20 and 'agosto' in line.lower():
                        events.append({
                            'title': f"Evento vía #{hashtag}: {line.strip()[:100]}",
                            'date': "Verificar en Instagram",
                            'location': "Palermo, Buenos Aires", 
                            'attendance': "Ver en Instagram",
                            'source': 'Instagram',
                            'hashtag': hashtag,
                            'extracted_at': datetime.now().isoformat()
                        })
                        
                        if len(events) >= 5:  # Limitar por hashtag
                            break
            
            return events
            
        except Exception:
            return []
    
    def _parse_buenosaires_gov(self, soup, source_name):
        """Parser para sitio del gobierno de Buenos Aires"""
        events = []
        
        try:
            # Buscar eventos mencionando Palermo
            text_content = soup.get_text()
            
            if 'palermo' in text_content.lower():
                # Buscar patrones de eventos
                lines = text_content.split('\n')
                for line in lines:
                    if 'palermo' in line.lower() and any(word in line.lower() for word in ['agosto', 'evento', 'festival']):
                        if len(line.strip()) > 20:
                            events.append({
                                'title': line.strip()[:150],
                                'date': "Agosto 2025",
                                'location': "Palermo, Buenos Aires",
                                'attendance': "Evento oficial",
                                'source': source_name,
                                'extracted_at': datetime.now().isoformat()
                            })
                            
                            if len(events) >= 3:
                                break
            
            return events
            
        except Exception:
            return []
    
    def _parse_timeout_ba(self, soup, source_name):
        """Parser para TimeOut Buenos Aires"""
        return []  # Implementar según estructura real
    
    def _parse_larural(self, soup, source_name):
        """Parser para La Rural"""
        return []  # Implementar según estructura real
    
    def combine_and_deduplicate(self, all_events):
        """Combinar y deduplificar eventos de todas las fuentes"""
        
        print("\n🔄 COMBINANDO Y DEDUPLICANDO...")
        
        combined = []
        seen_titles = set()
        
        for source, events in all_events.items():
            for event in events:
                title_clean = re.sub(r'\W+', '', event['title'].lower())
                
                if title_clean not in seen_titles and len(title_clean) > 10:
                    seen_titles.add(title_clean)
                    combined.append(event)
        
        # Ordenar por fuente (Facebook primero)
        source_priority = {'Facebook': 1, 'Eventbrite': 2, 'Instagram': 3, 'Argentina': 4}
        combined.sort(key=lambda x: source_priority.get(x['source'], 5))
        
        print(f"✅ {len(combined)} eventos únicos después de deduplicar")
        
        return combined
    
    def save_combined_results(self, all_events, combined_events):
        """Guardar todos los resultados"""
        
        # Archivo por fuente
        for source, events in all_events.items():
            if events:
                filename = f"eventos_{source}_palermo.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(events, f, ensure_ascii=False, indent=2)
                print(f"💾 {source}: {filename}")
        
        # Archivo combinado
        combined_file = "eventos_palermo_todas_fuentes.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'total_events': len(combined_events),
                    'sources': list(all_events.keys()),
                    'extracted_at': datetime.now().isoformat(),
                    'location': 'Palermo, Buenos Aires'
                },
                'events': combined_events
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Combinado: {combined_file}")
        
        return combined_file
    
    def display_summary(self, all_events, combined_events):
        """Mostrar resumen completo"""
        
        print("\n" + "="*80)
        print("🎭 RESUMEN COMPLETO - EVENTOS PALERMO AGOSTO 2025")
        print("="*80)
        
        total_by_source = {}
        for source, events in all_events.items():
            total_by_source[source] = len(events)
        
        print(f"\n📊 EVENTOS POR FUENTE:")
        for source, count in total_by_source.items():
            print(f"   📘 {source.upper()}: {count} eventos")
        
        print(f"\n🎯 RESUMEN:")
        print(f"   📈 Total extraído: {sum(total_by_source.values())} eventos")
        print(f"   🔄 Únicos después de dedup: {len(combined_events)}")
        print(f"   📍 Ubicación: Palermo, Buenos Aires")
        print(f"   🕐 Extraído: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n🎉 PRIMEROS 5 EVENTOS COMBINADOS:")
        for i, event in enumerate(combined_events[:5], 1):
            print(f"\n   📅 #{i} - {event['title'][:60]}...")
            print(f"      📅 {event['date']}")
            print(f"      📍 {event['location']}")
            print(f"      📘 Fuente: {event['source']}")

def main():
    """Función principal del multi-scraper"""
    
    print("🚀 MULTI-SOURCE EVENT SCRAPER - PALERMO BUENOS AIRES")
    print("="*80)
    print("📘 Facebook + 🎫 Eventbrite + 📸 Instagram + 🇦🇷 Fuentes Argentinas")
    print("="*80)
    
    scraper = MultiSourceEventScraper()
    
    # Ejecutar scraping de todas las fuentes
    all_events = scraper.scrape_all_sources("palermo buenos aires", max_per_source=10)
    
    # Combinar y deduplificar
    combined_events = scraper.combine_and_deduplicate(all_events)
    
    # Guardar resultados
    combined_file = scraper.save_combined_results(all_events, combined_events)
    
    # Mostrar resumen
    scraper.display_summary(all_events, combined_events)
    
    print(f"\n🏁 SCRAPING COMPLETO - ARCHIVO PRINCIPAL: {combined_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Scraping interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        sys.exit(1)
