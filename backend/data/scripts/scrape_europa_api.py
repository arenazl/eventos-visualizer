#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper 100% automático de Europa usando API de Gemini
Sin Playwright, sin intervención manual

Uso:
    python scrape_europa_api.py
    python scrape_europa_api.py --limit 10
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
REGIONS_DIR = BACKEND_DIR / 'data' / 'regions' / 'europa'
RESULTS_DIR = BACKEND_DIR / 'data' / 'scrapper_results' / 'europa'
ENV_FILE = BACKEND_DIR / '.env'

# Cargar .env
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configurar Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print('❌ Error: GEMINI_API_KEY no encontrado en .env')
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Usar modelo correcto
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
    print('✅ Usando gemini-1.5-pro')
except:
    try:
        model = genai.GenerativeModel('gemini-pro')
        print('✅ Usando gemini-pro')
    except:
        print('❌ Error: No se pudo inicializar modelo Gemini')
        sys.exit(1)


def load_european_cities():
    """Carga todas las ciudades europeas"""
    all_cities = []

    regions = [
        'europa-occidental',
        'europa-meridional',
        'europa-septentrional',
        'europa-oriental',
        'europa-nororiental'
    ]

    for region in regions:
        region_path = REGIONS_DIR / region
        if not region_path.exists():
            continue

        for json_file in region_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                country = data.get('country')
                country_code = data.get('country_code')
                region_name = data.get('region')
                cities = data.get('cities', [])

                for city in cities:
                    city['country'] = country
                    city['country_code'] = country_code
                    city['region'] = region_name
                    all_cities.append(city)

            except Exception as e:
                print(f'❌ Error leyendo {json_file}: {e}')
                continue

    return all_cities


def get_prompt(location, country):
    """Prompt simple para Gemini"""
    return f"que hay para hacer, eventos, fiestas en {location}, {country} desde hoy a fin de mes, que se sepa la fecha, lugar, etc"


def scrape_city(city, region_name):
    """Scrapea una ciudad usando Gemini API"""
    location = city['name']
    country = city['country']

    print(f'\n{"="*70}')
    print(f'🌍 [{location}, {country}]')
    print(f'{"="*70}')

    try:
        # Llamar a Gemini API
        prompt = get_prompt(location, country)
        print(f'  🤖 Consultando Gemini API...')

        response = model.generate_content(prompt)
        response_text = response.text

        print(f'  ✅ Respuesta recibida ({len(response_text)} caracteres)')

        # Preparar datos para guardar
        country_slug = country.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        location_slug = location.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

        # Determinar región
        region_map = {
            'alemania': 'europa-occidental',
            'francia': 'europa-occidental',
            'bélgica': 'europa-occidental',
            'países bajos': 'europa-occidental',
            'suiza': 'europa-occidental',
            'austria': 'europa-occidental',
            'españa': 'europa-meridional',
            'italia': 'europa-meridional',
            'grecia': 'europa-meridional',
            'portugal': 'europa-meridional',
            'reino unido': 'europa-septentrional',
            'irlanda': 'europa-septentrional',
            'suecia': 'europa-septentrional',
            'noruega': 'europa-septentrional',
            'dinamarca': 'europa-septentrional',
            'finlandia': 'europa-septentrional',
            'polonia': 'europa-oriental',
            'chequia': 'europa-oriental',
            'hungría': 'europa-oriental',
            'rumania': 'europa-oriental',
            'rusia': 'europa-nororiental'
        }

        region_dir = region_map.get(country_slug, 'europa-occidental')
        output_dir = RESULTS_DIR / region_dir / country_slug
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{location_slug}_dia_gemini.json"
        output_path = output_dir / filename

        # Guardar
        output_data = {
            "location": location,
            "country": country,
            "country_code": city.get('country_code'),
            "region": region_name,
            "latitude": city.get('latitude'),
            "longitude": city.get('longitude'),
            "query": prompt,
            "response_text": response_text,
            "scraped_at": datetime.now().isoformat(),
            "method": "gemini_api_direct"
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f'  💾 Guardado: {output_path.relative_to(RESULTS_DIR)}')

        return True

    except Exception as e:
        print(f'  ❌ Error: {str(e)[:100]}')
        return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scraper automático Europa con Gemini API')
    parser.add_argument('--limit', type=int, help='Número máximo de ciudades')
    args = parser.parse_args()

    print('\n' + '='*70)
    print('🌍 SCRAPER EUROPA - 100% AUTOMÁTICO CON GEMINI API')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    all_cities = load_european_cities()

    if args.limit:
        all_cities = all_cities[:args.limit]

    print(f'✅ {len(all_cities)} ciudades a procesar\n')

    # Estadísticas
    success = 0
    errors = 0

    # Procesar cada ciudad
    for i, city in enumerate(all_cities, 1):
        print(f'\n[{i}/{len(all_cities)}]', end=' ')

        try:
            # Verificar si ya existe
            location_slug = city['name'].lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            country_slug = city['country'].lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

            region_map = {
                'alemania': 'europa-occidental',
                'francia': 'europa-occidental',
                'bélgica': 'europa-occidental',
                'países bajos': 'europa-occidental',
                'suiza': 'europa-occidental',
                'austria': 'europa-occidental',
                'españa': 'europa-meridional',
                'italia': 'europa-meridional',
                'grecia': 'europa-meridional',
                'portugal': 'europa-meridional',
                'reino unido': 'europa-septentrional',
                'irlanda': 'europa-septentrional',
                'suecia': 'europa-septentrional',
                'noruega': 'europa-septentrional',
                'dinamarca': 'europa-septentrional',
                'finlandia': 'europa-septentrional',
                'polonia': 'europa-oriental',
                'chequia': 'europa-oriental',
                'hungría': 'europa-oriental',
                'rumania': 'europa-oriental',
                'rusia': 'europa-nororiental'
            }

            region_dir = region_map.get(country_slug, 'europa-occidental')
            check_path = RESULTS_DIR / region_dir / country_slug / f"{location_slug}_dia_gemini.json"

            if check_path.exists():
                print(f'⏭️  {city["name"]}, {city["country"]} - Ya existe, saltando...')
                continue

            # Scrapear
            result = scrape_city(city, city.get('region'))

            if result:
                success += 1
            else:
                errors += 1

            # Pausa para no saturar API
            time.sleep(3)

        except Exception as e:
            print(f'❌ Error procesando {city["name"]}: {str(e)[:100]}')
            errors += 1
            continue

    # Resumen
    print('\n' + '='*70)
    print('🎉 SCRAPING COMPLETADO')
    print('='*70)
    print(f'✅ Exitosos: {success}')
    print(f'❌ Errores: {errors}')
    print(f'📊 Total procesado: {success + errors}/{len(all_cities)}')
    print(f'💾 Resultados en: {RESULTS_DIR}')
    print('\n🖼️  Próximo paso: Agregar imágenes')
    print(f'   node add_images_generic.js "{RESULTS_DIR.relative_to(BACKEND_DIR)}"')
    print('\n📥 Siguiente: Importar a MySQL')
    print(f'   python import_generic.py "{RESULTS_DIR.relative_to(BACKEND_DIR)}"')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
