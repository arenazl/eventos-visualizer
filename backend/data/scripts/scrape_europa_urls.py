#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper de Europa usando URLs reales de sitios de eventos
Usa scrape_generic.py internamente

Uso:
    python scrape_europa_urls.py
    python scrape_europa_urls.py --limit 5
"""

import sys
import subprocess
from pathlib import Path
import json

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
SCRAPE_GENERIC = SCRIPT_DIR / 'scrape_generic.py'

# URLs de eventos por ciudad europea
CITY_URLS = {
    # Alemania
    'Berlin': [
        ('https://www.residentadvisor.net/events/de/berlin', 'Dame todos los eventos de música electrónica'),
        ('https://www.eventbrite.de/d/germany--berlin/events/', 'Extrae eventos de Berlin')
    ],
    'Munich': [
        ('https://www.residentadvisor.net/events/de/munich', 'Dame eventos de música electrónica'),
    ],

    # Francia
    'Paris': [
        ('https://www.residentadvisor.net/events/fr/paris', 'Eventos de música electrónica en Paris'),
        ('https://www.timeout.com/paris/en/music/clubs-in-paris', 'Eventos y clubs en Paris')
    ],
    'Lyon': [
        ('https://www.residentadvisor.net/events/fr/lyon', 'Eventos de música en Lyon'),
    ],
    'Marseille': [
        ('https://www.residentadvisor.net/events/fr/marseille', 'Eventos musicales en Marseille'),
    ],

    # Reino Unido
    'London': [
        ('https://www.residentadvisor.net/events/uk/london', 'Eventos de música electrónica en Londres'),
        ('https://www.timeout.com/london/clubs/best-clubs-in-london', 'Eventos y clubs en Londres')
    ],
    'Manchester': [
        ('https://www.residentadvisor.net/events/uk/manchester', 'Eventos de música en Manchester'),
    ],

    # España
    'Madrid': [
        ('https://www.residentadvisor.net/events/es/madrid', 'Eventos de música electrónica en Madrid'),
    ],
    'Barcelona': [
        ('https://www.residentadvisor.net/events/es/barcelona', 'Eventos de música en Barcelona'),
    ],
    'Valencia': [
        ('https://www.residentadvisor.net/events/es/valencia', 'Eventos en Valencia'),
    ],

    # Italia
    'Rome': [
        ('https://www.residentadvisor.net/events/it/rome', 'Eventi musicali a Roma'),
    ],
    'Milan': [
        ('https://www.residentadvisor.net/events/it/milan', 'Eventi a Milano'),
    ],

    # Holanda
    'Amsterdam': [
        ('https://www.residentadvisor.net/events/nl/amsterdam', 'Events in Amsterdam'),
    ],

    # Bélgica
    'Brussels': [
        ('https://www.residentadvisor.net/events/be/brussels', 'Events in Brussels'),
    ],

    # Portugal
    'Lisbon': [
        ('https://www.residentadvisor.net/events/pt/lisbon', 'Eventos em Lisboa'),
    ],

    # Grecia
    'Athens': [
        ('https://www.residentadvisor.net/events/gr/athens', 'Events in Athens'),
    ],
}


def scrape_city(city_name, urls):
    """
    Scrapea todas las URLs de una ciudad
    """
    print(f'\n{"="*70}')
    print(f'🌍 {city_name}')
    print(f'{"="*70}')

    success_count = 0

    for url, prompt in urls:
        print(f'\n📍 URL: {url}')
        print(f'💬 Prompt: {prompt[:50]}...')

        try:
            # Llamar a scrape_generic.py
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRAPE_GENERIC),
                    url,
                    prompt
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )

            if result.returncode == 0:
                print('  ✅ Scraping exitoso')
                success_count += 1
            else:
                print(f'  ❌ Error: {result.stderr[:100]}')

        except subprocess.TimeoutExpired:
            print('  ⏱️  Timeout (60s)')
        except Exception as e:
            print(f'  ❌ Error: {str(e)[:100]}')

    return success_count


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper Europa con URLs reales')
    parser.add_argument('--limit', type=int, help='Número de ciudades a procesar')
    args = parser.parse_args()

    print('='*70)
    print('🌍 SCRAPER EUROPA - URLs REALES DE EVENTOS')
    print('='*70)

    cities = list(CITY_URLS.items())

    if args.limit:
        cities = cities[:args.limit]

    print(f'\n📊 {len(cities)} ciudades a procesar')
    print(f'🌐 Fuentes: Resident Advisor, Time Out, Eventbrite\n')

    total_success = 0
    total_urls = 0

    for i, (city, urls) in enumerate(cities, 1):
        print(f'\n[{i}/{len(cities)}]', end=' ')
        success = scrape_city(city, urls)
        total_success += success
        total_urls += len(urls)

    # Resumen
    print('\n' + '='*70)
    print('🎉 SCRAPING COMPLETADO')
    print('='*70)
    print(f'✅ URLs exitosas: {total_success}/{total_urls}')
    print(f'📁 Resultados en: backend/data/scrapper_results/generic/')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
