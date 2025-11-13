#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper Europa usando CloudScraper para bypasear protecciones
Resident Advisor + Eventbrite

Uso:
    python scrape_europa_cloudscraper.py --limit 5
"""

import sys
import json
from pathlib import Path
import re
from datetime import datetime
import cloudscraper

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
REGIONS_DIR = SCRIPT_DIR.parent / 'regions' / 'europa'
RESULTS_DIR = SCRIPT_DIR.parent / 'scrapper_results' / 'europa'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_europa_cities():
    """Carga todas las ciudades europeas"""
    cities = []
    for subregion in REGIONS_DIR.iterdir():
        if not subregion.is_dir():
            continue
        for json_file in subregion.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                country = data.get('country', '')
                country_code = data.get('country_code', '').lower()
                for city in data.get('cities', []):
                    cities.append({
                        'name': city['name'],
                        'country': country,
                        'country_code': country_code,
                        'latitude': city.get('latitude'),
                        'longitude': city.get('longitude')
                    })
            except Exception as e:
                print(f'⚠️  Error en {json_file}: {e}')
    return cities


def scrape_resident_advisor(city_name, country_code, scraper):
    """Scrapea Resident Advisor con CloudScraper"""
    city_slug = city_name.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    url = f'https://www.residentadvisor.net/events/{country_code}/{city_slug}'

    try:
        print(f'  📡 Scrapeando: {url}')
        response = scraper.get(url, timeout=15)

        if response.status_code == 200:
            html = response.text

            # Buscar eventos en el HTML
            # Resident Advisor usa structure: <li class="event-item">
            events_found = re.findall(r'<li class="event-item".*?</li>', html, re.DOTALL)

            print(f'  ✅ HTML descargado: {len(html)} chars')
            print(f'  📊 Eventos encontrados: {len(events_found)}')

            return html
        else:
            print(f'  ❌ Error {response.status_code}')
            return None

    except Exception as e:
        print(f'  ❌ Error: {str(e)[:100]}')
        return None


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper Europa con CloudScraper')
    parser.add_argument('--limit', type=int, help='Número de ciudades a procesar')
    args = parser.parse_args()

    print('='*70)
    print('🌍 SCRAPER EUROPA - CLOUDSCRAPER (ANTI-CAPTCHA)')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    cities = load_europa_cities()

    if args.limit:
        cities = cities[:args.limit]

    print(f'✅ {len(cities)} ciudades a procesar\n')

    # Crear scraper con CloudScraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    total_success = 0
    total_failed = 0

    for i, city in enumerate(cities, 1):
        city_name = city['name']
        country = city['country']
        country_code = city['country_code']

        print(f'\n[{i}/{len(cities)}] {city_name}, {country}')
        print('-' * 70)

        # Scrapear Resident Advisor
        html = scrape_resident_advisor(city_name, country_code, scraper)

        if html:
            total_success += 1

            # Guardar HTML para procesamiento posterior
            country_folder = RESULTS_DIR / country.lower().replace(' ', '_')
            country_folder.mkdir(parents=True, exist_ok=True)

            html_file = country_folder / f"{city_name.lower().replace(' ', '_')}_ra.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f'  💾 HTML guardado: {html_file.name}')
        else:
            total_failed += 1

    # Resumen
    print('\n' + '='*70)
    print('🎉 SCRAPING COMPLETADO')
    print('='*70)
    print(f'✅ Exitosos: {total_success}/{len(cities)}')
    print(f'❌ Fallidos: {total_failed}/{len(cities)}')
    print(f'💾 HTMLs guardados en: {RESULTS_DIR}')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
