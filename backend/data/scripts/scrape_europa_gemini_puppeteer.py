#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper de Europa usando gemini.com via Puppeteer MCP
NO USA API - USA gemini.com directamente

Uso:
    python scrape_europa_gemini_puppeteer.py --limit 5
    python scrape_europa_gemini_puppeteer.py  # todas las 63 ciudades
"""

import sys
import json
from pathlib import Path
import time

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
    """Carga todas las 63 ciudades europeas"""
    cities = []

    # Buscar todos los JSONs de Europa
    for subregion in REGIONS_DIR.iterdir():
        if not subregion.is_dir():
            continue

        for json_file in subregion.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                country = data.get('country', '')
                country_code = data.get('country_code', '')

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


def get_gemini_prompt(city_name, country):
    """Genera el prompt para gemini.com"""
    return f"""Busca eventos de música electrónica, conciertos, clubes y fiestas en {city_name}, {country} para las próximas 4 semanas.

Extrae la información en formato JSON con esta estructura exacta:

{{
  "eventos": [
    {{
      "title": "Nombre del evento",
      "date": "YYYY-MM-DD",
      "venue": "Lugar/club",
      "address": "Dirección completa",
      "lineup": ["Artista 1", "Artista 2"],
      "time": "HH:MM o descripción",
      "category": "música electrónica/techno/house/etc",
      "city": "{city_name}",
      "country": "{country}"
    }}
  ]
}}

IMPORTANTE:
- Responde SOLO con JSON válido
- Si no encuentras eventos, responde: {{"eventos": []}}
- NO agregues explicaciones, SOLO el JSON
- Incluye lineup si está disponible
- Fecha en formato ISO (YYYY-MM-DD)"""


def save_results(city_name, country, eventos):
    """Guarda resultados en JSON"""
    # Crear estructura de carpetas
    country_folder = RESULTS_DIR / country.lower().replace(' ', '_')
    country_folder.mkdir(parents=True, exist_ok=True)

    output_file = country_folder / f"{city_name.lower().replace(' ', '_')}.json"

    output_data = {
        'source': 'gemini.com',
        'method': 'puppeteer_mcp',
        'city': city_name,
        'country': country,
        'total_events': len(eventos),
        'eventos': eventos
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_file


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper Europa con gemini.com')
    parser.add_argument('--limit', type=int, help='Número de ciudades a procesar')
    args = parser.parse_args()

    print('='*70)
    print('🌍 SCRAPER EUROPA - GEMINI.COM + PUPPETEER MCP')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    cities = load_europa_cities()

    if args.limit:
        cities = cities[:args.limit]

    print(f'✅ {len(cities)} ciudades a procesar\n')

    # Instrucciones para el usuario
    print('🎯 INSTRUCCIONES:')
    print('   1. Abre gemini.com en Puppeteer')
    print('   2. Para cada ciudad, copia y pega el prompt')
    print('   3. Extrae el JSON de la respuesta')
    print('   4. Guarda el resultado\n')

    print('📝 PROMPTS GENERADOS:\n')

    # Generar prompts para todas las ciudades
    for i, city in enumerate(cities, 1):
        city_name = city['name']
        country = city['country']

        print(f'\n[{i}/{len(cities)}] {city_name}, {country}')
        print('-' * 70)

        prompt = get_gemini_prompt(city_name, country)
        print(prompt)
        print('-' * 70)

        # Esperar input del usuario con el JSON
        print('\n📥 Pega aquí el JSON que te devolvió Gemini (o "skip" para saltar):')

        # En modo real, aquí esperaríamos input del usuario
        # Por ahora, solo guardamos un placeholder vacío
        save_results(city_name, country, [])
        print(f'💾 Guardado: europa/{country.lower().replace(" ", "_")}/{city_name.lower().replace(" ", "_")}.json')

    print('\n' + '='*70)
    print('🎉 GENERACIÓN DE PROMPTS COMPLETADA')
    print('='*70)
    print(f'📊 Total ciudades: {len(cities)}')
    print(f'💾 Resultados en: {RESULTS_DIR}')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
