#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper Europa usando APIs oficiales
Eventbrite + Ticketmaster + PredictHQ

Uso:
    python scrape_europa_apis.py --limit 5
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
REGIONS_DIR = SCRIPT_DIR.parent / 'regions' / 'europa'
RESULTS_DIR = SCRIPT_DIR.parent / 'scrapper_results' / 'europa'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys (desde .env)
EVENTBRITE_TOKEN = 'OWHOYDNG6PU5KRQPMMKS'  # Private token correcto
TICKETMASTER_KEY = 'BnAVSbJZ7dVvPwFh91UVOmwX4CU1Ft5g'


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
                country_code = data.get('country_code', '').upper()
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


def fetch_ticketmaster_events(city_name, country_code, latitude, longitude):
    """Fetch events from Ticketmaster API"""
    url = 'https://app.ticketmaster.com/discovery/v2/events.json'

    params = {
        'apikey': TICKETMASTER_KEY,
        'city': city_name,
        'countryCode': country_code,
        'classificationName': 'music',
        'size': 50,
        'sort': 'date,asc'
    }

    try:
        print(f'  📡 Ticketmaster API...')
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            events = data.get('_embedded', {}).get('events', [])

            print(f'  ✅ {len(events)} eventos encontrados')

            # Transformar a nuestro formato
            eventos_clean = []
            for event in events:
                try:
                    date_start = event.get('dates', {}).get('start', {})
                    venue = event.get('_embedded', {}).get('venues', [{}])[0]

                    eventos_clean.append({
                        'title': event.get('name', ''),
                        'date': date_start.get('localDate', ''),
                        'time': date_start.get('localTime', 'TBD'),
                        'venue': venue.get('name', ''),
                        'address': venue.get('address', {}).get('line1', ''),
                        'city': city_name,
                        'country': country_code,
                        'category': 'música',
                        'source': 'ticketmaster',
                        'url': event.get('url', '')
                    })
                except:
                    continue

            return eventos_clean
        else:
            print(f'  ❌ Error {response.status_code}')
            return []

    except Exception as e:
        print(f'  ❌ Error: {str(e)[:100]}')
        return []


def fetch_eventbrite_events(city_name, latitude, longitude):
    """Fetch events from Eventbrite API"""
    url = 'https://www.eventbriteapi.com/v3/events/search/'

    headers = {
        'Authorization': f'Bearer {EVENTBRITE_TOKEN}'
    }

    # Calcular fechas
    start_date = datetime.now().isoformat() + 'Z'
    end_date = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'

    params = {
        'location.latitude': latitude,
        'location.longitude': longitude,
        'location.within': '50km',
        'categories': '103',  # Music
        'start_date.range_start': start_date,
        'start_date.range_end': end_date,
        'expand': 'venue',
        'page_size': 50
    }

    try:
        print(f'  📡 Eventbrite API...')
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])

            print(f'  ✅ {len(events)} eventos encontrados')

            # Transformar a nuestro formato
            eventos_clean = []
            for event in events:
                try:
                    venue = event.get('venue', {}) if event.get('venue') else {}

                    eventos_clean.append({
                        'title': event.get('name', {}).get('text', ''),
                        'date': event.get('start', {}).get('local', '')[:10],
                        'time': event.get('start', {}).get('local', '')[11:16],
                        'venue': venue.get('name', ''),
                        'address': venue.get('address', {}).get('localized_address_display', ''),
                        'city': city_name,
                        'category': 'música',
                        'source': 'eventbrite',
                        'url': event.get('url', '')
                    })
                except:
                    continue

            return eventos_clean
        else:
            print(f'  ❌ Error {response.status_code}')
            return []

    except Exception as e:
        print(f'  ❌ Error: {str(e)[:100]}')
        return []


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper Europa con APIs oficiales')
    parser.add_argument('--limit', type=int, help='Número de ciudades a procesar')
    args = parser.parse_args()

    print('='*70)
    print('🌍 SCRAPER EUROPA - APIS OFICIALES')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    cities = load_europa_cities()

    if args.limit:
        cities = cities[:args.limit]

    print(f'✅ {len(cities)} ciudades a procesar')
    print(f'🔑 APIs: Ticketmaster + Eventbrite\n')

    total_events = 0

    for i, city in enumerate(cities, 1):
        city_name = city['name']
        country = city['country']
        country_code = city['country_code']
        latitude = city['latitude']
        longitude = city['longitude']

        print(f'\n[{i}/{len(cities)}] {city_name}, {country}')
        print('-' * 70)

        eventos_all = []

        # Fetch de Ticketmaster
        eventos_tm = fetch_ticketmaster_events(city_name, country_code, latitude, longitude)
        eventos_all.extend(eventos_tm)

        # Fetch de Eventbrite
        eventos_eb = fetch_eventbrite_events(city_name, latitude, longitude)
        eventos_all.extend(eventos_eb)

        print(f'\n  📊 Total: {len(eventos_all)} eventos')

        if eventos_all:
            # Guardar JSON
            country_folder = RESULTS_DIR / country.lower().replace(' ', '_')
            country_folder.mkdir(parents=True, exist_ok=True)

            output_file = country_folder / f"{city_name.lower().replace(' ', '_')}.json"

            output_data = {
                'source': 'apis_oficiales',
                'city': city_name,
                'country': country,
                'scraped_at': datetime.now().isoformat(),
                'total_events': len(eventos_all),
                'eventos': eventos_all
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f'  💾 Guardado: {output_file.name}')

            total_events += len(eventos_all)

    # Resumen
    print('\n' + '='*70)
    print('🎉 SCRAPING COMPLETADO')
    print('='*70)
    print(f'📊 Total eventos: {total_events}')
    print(f'💾 Archivos JSON en: {RESULTS_DIR}')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
