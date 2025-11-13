#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SUPER SCRAPER - Lee archivos .md con URLs y hace scraping automático
Busca eventos en la primera línea (URL) de cada archivo .md
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup
import time

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SITES_DIR = Path(__file__).parent.parent / 'sites'
OUTPUT_DIR = Path(__file__).parent.parent / 'scrapper_results' / 'auto_scraped'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class SuperScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        }

    def extract_url_from_md(self, md_file):
        """Extrae URL de la primera línea del archivo .md"""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()

                # Si es una URL completa
                if first_line.startswith('http'):
                    return first_line

                # Si es un dominio sin http, agregar https
                if '.' in first_line and not first_line.startswith('#'):
                    return f'https://{first_line}'

                return None
        except Exception as e:
            print(f"  ❌ Error leyendo {md_file.name}: {e}")
            return None

    def scrape_page(self, url):
        """Hace scraping de una página"""
        try:
            print(f"  🌐 Descargando: {url}")
            response = self.scraper.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return response.text
            else:
                print(f"  ⚠️  Status {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ Error descargando: {str(e)[:100]}")
            return None

    def extract_events_generic(self, html, source_url):
        """Extrae eventos usando patrones genéricos"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []

        # Patrones comunes de contenedores de eventos
        event_containers = []

        # Buscar por clases comunes
        event_containers.extend(soup.find_all(class_=re.compile(r'event', re.I)))
        event_containers.extend(soup.find_all(class_=re.compile(r'card', re.I)))
        event_containers.extend(soup.find_all('article'))

        print(f"  📦 Encontrados {len(event_containers)} contenedores potenciales")

        for idx, container in enumerate(event_containers[:50]):  # Limitar a 50
            try:
                # Extraer título
                title_elem = (
                    container.find('h1') or
                    container.find('h2') or
                    container.find('h3') or
                    container.find(class_=re.compile(r'title|heading', re.I))
                )

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Extraer fecha (opcional)
                date_elem = container.find(class_=re.compile(r'date|time|when', re.I))
                date = date_elem.get_text(strip=True) if date_elem else None

                # Extraer lugar (opcional)
                venue_elem = container.find(class_=re.compile(r'venue|location|where|place', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else None

                # Extraer descripción (opcional)
                desc_elem = container.find(class_=re.compile(r'description|summary|excerpt', re.I))
                description = desc_elem.get_text(strip=True) if desc_elem else None

                # Extraer imagen (opcional)
                img_elem = container.find('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

                # Extraer link (opcional)
                link_elem = container.find('a', href=True)
                event_url = link_elem['href'] if link_elem else None

                # Hacer URLs absolutas
                if event_url and not event_url.startswith('http'):
                    from urllib.parse import urljoin
                    event_url = urljoin(source_url, event_url)

                if image_url and not image_url.startswith('http'):
                    from urllib.parse import urljoin
                    image_url = urljoin(source_url, image_url)

                event = {
                    'title': title,
                    'date': date,
                    'venue': venue,
                    'description': description,
                    'image_url': image_url,
                    'url': event_url,
                    'source': source_url,
                    'scraped_at': datetime.now().isoformat()
                }

                # Solo agregar si tiene al menos título
                if title and len(title) > 5:
                    events.append(event)

            except Exception as e:
                continue

        return events

    def save_events(self, events, source_name):
        """Guarda eventos en JSON"""
        if not events:
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{source_name}_{timestamp}.json"
        output_file = OUTPUT_DIR / filename

        data = {
            'source': source_name,
            'total': len(events),
            'scraped_at': datetime.now().isoformat(),
            'eventos': events
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_file

    def process_md_file(self, md_file):
        """Procesa un archivo .md completo"""
        print(f"\n{'='*70}")
        print(f"📄 Procesando: {md_file.name}")
        print('='*70)

        # Extraer URL
        url = self.extract_url_from_md(md_file)
        if not url:
            print("  ⚠️  No se encontró URL válida")
            return None

        print(f"  🔗 URL: {url}")

        # Scraping
        html = self.scrape_page(url)
        if not html:
            return None

        # Extraer eventos
        print("  🔍 Extrayendo eventos...")
        events = self.extract_events_generic(html, url)

        if not events:
            print("  ⚠️  No se encontraron eventos")
            return None

        print(f"  ✅ {len(events)} eventos encontrados")

        # Guardar
        source_name = md_file.stem
        output_file = self.save_events(events, source_name)

        if output_file:
            print(f"  💾 Guardado en: {output_file.name}")
            return output_file

        return None


def main():
    print('='*70)
    print('🚀 SUPER SCRAPER - Scraping Automático desde .md')
    print('='*70)
    print(f'📂 Carpeta sites: {SITES_DIR}')
    print(f'📂 Carpeta output: {OUTPUT_DIR}\n')

    scraper = SuperScraper()

    # Buscar todos los .md en la carpeta sites
    md_files = list(SITES_DIR.glob('*.md'))

    if not md_files:
        print('⚠️  No se encontraron archivos .md')
        return

    print(f'📊 {len(md_files)} archivos .md encontrados\n')

    results = {
        'success': 0,
        'failed': 0,
        'total_events': 0
    }

    for md_file in md_files:
        try:
            output = scraper.process_md_file(md_file)

            if output:
                results['success'] += 1
                # Contar eventos del archivo guardado
                with open(output, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results['total_events'] += data.get('total', 0)
            else:
                results['failed'] += 1

            # Rate limit entre archivos
            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error procesando {md_file.name}: {e}")
            results['failed'] += 1

    print('\n' + '='*70)
    print('🎉 PROCESO COMPLETADO')
    print('='*70)
    print(f"✅ Éxitos: {results['success']}")
    print(f"❌ Fallos: {results['failed']}")
    print(f"🎫 Total eventos: {results['total_events']}")
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
