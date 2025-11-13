#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper directo de Europa - Sin AI
Usa sitios web reales: Resident Advisor, Eventbrite, TimeOut

Uso:
    python scrape_europa_direct.py --limit 5
"""

import sys
import json
from pathlib import Path
import re
from datetime import datetime

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
REGIONS_DIR = SCRIPT_DIR.parent / 'regions' / 'europa'
RESULTS_DIR = SCRIPT_DIR.parent / 'scrapper_results' / 'europa'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# URLs base por tipo
SOURCES = {
    'residentadvisor': 'https://www.residentadvisor.net/events/{country_code}/{city_slug}',
    'eventbrite': 'https://www.eventbrite.com/d/{country}--{city}/events/',
    'timeout': 'https://www.timeout.com/{city}/music/clubs'
}

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


def get_urls_for_city(city_name, country, country_code):
    """Genera URLs de scraping para una ciudad"""
    city_slug = city_name.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

    urls = []

    # Resident Advisor
    ra_url = f'https://www.residentadvisor.net/events/{country_code}/{city_slug}'
    urls.append(('residentadvisor', ra_url))

    # Eventbrite
    eb_url = f'https://www.eventbrite.com/d/{country.lower()}--{city_slug}/music--events/'
    urls.append(('eventbrite', eb_url))

    return urls


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper directo Europa')
    parser.add_argument('--limit', type=int, help='Número de ciudades a procesar')
    args = parser.parse_args()

    print('='*70)
    print('🌍 SCRAPER EUROPA - DIRECTO (SIN AI)')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    cities = load_europa_cities()

    if args.limit:
        cities = cities[:args.limit]

    print(f'✅ {len(cities)} ciudades a procesar')
    print(f'📊 Fuentes: Resident Advisor, Eventbrite\n')

    # Generar URLs para scraping manual
    print('🔗 URLs GENERADAS PARA PUPPETEER:\n')

    for i, city in enumerate(cities, 1):
        city_name = city['name']
        country = city['country']
        country_code = city['country_code']

        print(f'\n[{i}/{len(cities)}] {city_name}, {country}')
        print('-' * 70)

        urls = get_urls_for_city(city_name, country, country_code)

        for source, url in urls:
            print(f'  📍 {source}: {url}')

        # Guardar placeholder vacío
        country_folder = RESULTS_DIR / country.lower().replace(' ', '_')
        country_folder.mkdir(parents=True, exist_ok=True)

        output_file = country_folder / f"{city_name.lower().replace(' ', '_')}.json"

        output_data = {
            'source': 'direct_scraping',
            'city': city_name,
            'country': country,
            'urls': [url for _, url in urls],
            'total_events': 0,
            'eventos': []
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

    print('\n' + '='*70)
    print('🎯 URLS GENERADAS')
    print('='*70)
    print(f'📊 Total ciudades: {len(cities)}')
    print(f'💾 Archivos JSON creados en: {RESULTS_DIR}')
    print('\n🔧 Siguiente paso: Usar Puppeteer para extraer eventos de cada URL')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
