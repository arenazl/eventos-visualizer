#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper automatizado para TODA EUROPA usando BrightData + Gemini AI
Procesa 21 países y 63 ciudades con scraping multi-técnica

Uso:
    python scrape_europa_brightdata.py
    python scrape_europa_brightdata.py --cities 10  # Solo primeras 10 ciudades
    python scrape_europa_brightdata.py --country "Francia"  # Solo un país
"""

import sys
import os
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any, Optional

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
model = genai.GenerativeModel('gemini-1.5-flash')

# BrightData config (opcional)
BRIGHTDATA_CONFIG = None
if os.getenv('BRIGHTDATA_USERNAME') and os.getenv('BRIGHTDATA_PASSWORD'):
    BRIGHTDATA_CONFIG = {
        'username': os.getenv('BRIGHTDATA_USERNAME'),
        'password': os.getenv('BRIGHTDATA_PASSWORD'),
        'endpoint': os.getenv('BRIGHTDATA_ENDPOINT', 'rotating-residential.brightdata.com:22225')
    }
    print('✅ BrightData configurado')
else:
    print('⚠️  BrightData NO configurado - usando solo Gemini AI')


def load_european_cities() -> List[Dict]:
    """
    Carga todas las ciudades europeas de los archivos JSON
    Retorna lista de ciudades con país, código, región, coordenadas
    """
    all_cities = []

    # Regiones de Europa
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
            print(f'⚠️  Región no encontrada: {region}')
            continue

        # Leer todos los JSON de la región
        for json_file in region_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                country = data.get('country')
                country_code = data.get('country_code')
                region_name = data.get('region')
                cities = data.get('cities', [])

                # Agregar metadata a cada ciudad
                for city in cities:
                    city['country'] = country
                    city['country_code'] = country_code
                    city['region'] = region_name
                    city['source_file'] = json_file.stem
                    all_cities.append(city)

            except Exception as e:
                print(f'❌ Error leyendo {json_file}: {e}')
                continue

    return all_cities


async def scrape_city_with_gemini(city: Dict, max_retries: int = 2) -> Optional[List[Dict]]:
    """
    Scrapea eventos de una ciudad usando Gemini AI
    """
    city_name = city['name']
    country = city['country']

    print(f'\n🤖 Scrapeando {city_name}, {country} con Gemini AI...')

    # URLs comunes de eventos por país
    search_queries = {
        'ES': f'eventos {city_name} españa',
        'FR': f'événements {city_name} france',
        'GB': f'events {city_name} uk',
        'DE': f'veranstaltungen {city_name} deutschland',
        'IT': f'eventi {city_name} italia',
        'PT': f'eventos {city_name} portugal',
        'NL': f'evenementen {city_name} nederland',
        'BE': f'événements {city_name} belgique',
        'AT': f'veranstaltungen {city_name} österreich',
        'CH': f'événements {city_name} suisse',
        'SE': f'evenemang {city_name} sverige',
        'NO': f'arrangementer {city_name} norge',
        'DK': f'begivenheder {city_name} danmark',
        'FI': f'tapahtumat {city_name} suomi',
        'PL': f'wydarzenia {city_name} polska',
        'CZ': f'události {city_name} česko',
        'HU': f'események {city_name} magyarország',
        'RO': f'evenimente {city_name} românia',
        'GR': f'εκδηλώσεις {city_name} ελλάδα',
        'IE': f'events {city_name} ireland',
        'RU': f'события {city_name} россия'
    }

    country_code = city.get('country_code', 'ES')
    search_query = search_queries.get(country_code, f'events {city_name}')

    # Prompt para Gemini
    prompt = f"""
Busca en internet eventos actuales y próximos en {city_name}, {country}.

Busca eventos de TODAS las categorías:
- Conciertos y música (rock, pop, electrónica, jazz, clásica)
- Teatro y espectáculos
- Deportes (fútbol, básquet, etc.)
- Festivales y ferias
- Arte y exposiciones
- Gastronomía
- Tecnología y conferencias
- Eventos culturales

IMPORTANTE:
1. Solo eventos REALES que existan actualmente
2. Con fecha específica (día, mes, año)
3. Con ubicación específica en {city_name}
4. Incluir URL del evento si está disponible

Responde SOLO con JSON válido:
{{
  "eventos": [
    {{
      "title": "Nombre del evento",
      "date": "YYYY-MM-DD",
      "venue": "Lugar específico",
      "city": "{city_name}",
      "country": "{country}",
      "description": "Descripción breve",
      "category": "música|teatro|deportes|cultural|gastronomía|tech|arte",
      "url": "URL del evento",
      "source": "Fuente de la información"
    }}
  ]
}}

Si NO encuentras eventos reales, responde: {{"eventos": []}}
NO inventes eventos. Solo eventos REALES con fuente verificable.
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Limpiar markdown
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        # Parsear JSON
        data = json.loads(response_text)
        eventos = data.get('eventos', [])

        # Agregar metadata de la ciudad
        for evento in eventos:
            evento['latitude'] = city.get('latitude')
            evento['longitude'] = city.get('longitude')
            evento['country_code'] = country_code
            evento['scraping_method'] = 'gemini_ai_search'
            evento['scraped_at'] = datetime.now().isoformat()

        print(f'  ✅ {len(eventos)} eventos encontrados')

        return eventos if eventos else None

    except json.JSONDecodeError as e:
        print(f'  ❌ Error JSON: {str(e)[:100]}')
        return None
    except Exception as e:
        print(f'  ❌ Error: {str(e)[:100]}')
        return None


async def scrape_city_with_brightdata(city: Dict) -> Optional[List[Dict]]:
    """
    Scrapea eventos usando BrightData (si está configurado)
    """
    if not BRIGHTDATA_CONFIG:
        return None

    city_name = city['name']
    country = city['country']

    print(f'\n🌐 Scrapeando {city_name}, {country} con BrightData...')

    # Importar el scraper de BrightData
    try:
        sys.path.append(str(BACKEND_DIR / 'legacy'))
        from facebook_bright_data_scraper import FacebookBrightDataScraper

        scraper = FacebookBrightDataScraper(BRIGHTDATA_CONFIG)

        # Búsqueda específica por ciudad
        query = f"eventos {city_name} {country}"
        events = await scraper.method_3_facebook_search(query)

        if events:
            # Agregar metadata
            for event in events:
                event['city'] = city_name
                event['country'] = country
                event['latitude'] = city.get('latitude')
                event['longitude'] = city.get('longitude')
                event['scraping_method'] = 'brightdata_facebook'
                event['scraped_at'] = datetime.now().isoformat()

            print(f'  ✅ {len(events)} eventos encontrados con BrightData')
            return events

    except Exception as e:
        print(f'  ⚠️  BrightData error: {str(e)[:100]}')

    return None


async def scrape_single_city(city: Dict, use_brightdata: bool = True) -> Dict:
    """
    Scrapea una ciudad usando todos los métodos disponibles
    """
    city_name = city['name']
    country = city['country']

    print(f'\n{"="*70}')
    print(f'🌍 Procesando: {city_name}, {country}')
    print(f'📍 Coords: {city["latitude"]}, {city["longitude"]}')
    print(f'{"="*70}')

    all_events = []

    # Método 1: BrightData (si está disponible)
    if use_brightdata and BRIGHTDATA_CONFIG:
        brightdata_events = await scrape_city_with_brightdata(city)
        if brightdata_events:
            all_events.extend(brightdata_events)

    # Método 2: Gemini AI (siempre)
    gemini_events = await scrape_city_with_gemini(city)
    if gemini_events:
        all_events.extend(gemini_events)

    # Deduplicar eventos
    unique_events = []
    seen_titles = set()

    for event in all_events:
        title = event.get('title', '').lower().strip()
        if title and title not in seen_titles and len(title) > 5:
            seen_titles.add(title)
            unique_events.append(event)

    return {
        'city': city_name,
        'country': country,
        'country_code': city.get('country_code'),
        'region': city.get('region'),
        'latitude': city.get('latitude'),
        'longitude': city.get('longitude'),
        'total_events': len(unique_events),
        'events': unique_events,
        'scraped_at': datetime.now().isoformat(),
        'methods_used': ['brightdata' if BRIGHTDATA_CONFIG else None, 'gemini_ai']
    }


def save_results(result: Dict, region: str):
    """
    Guarda resultados en el directorio apropiado
    """
    city_name = result['city']
    country = result['country']
    total = result['total_events']

    if total == 0:
        print(f'⚠️  {city_name}: Sin eventos - no se guarda archivo')
        return

    # Normalizar nombres para archivos
    city_slug = city_name.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    country_slug = country.lower().replace(' ', '_')

    # Directorio por región
    output_dir = RESULTS_DIR / region / country_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Nombre de archivo
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f'{city_slug}_{timestamp}_brightdata.json'
    output_file = output_dir / filename

    # Guardar
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f'\n💾 Guardado: {output_file}')
    print(f'📊 {total} eventos de {city_name}, {country}')


async def main():
    """Main scraping function"""
    parser = argparse.ArgumentParser(
        description='Scraper automatizado de toda Europa con BrightData + Gemini AI'
    )
    parser.add_argument('--cities', type=int, help='Número máximo de ciudades a procesar')
    parser.add_argument('--country', type=str, help='Procesar solo un país específico')
    parser.add_argument('--no-brightdata', action='store_true', help='No usar BrightData')

    args = parser.parse_args()

    print('\n' + '='*70)
    print('🌍 SCRAPER EUROPA - BRIGHTDATA + GEMINI AI')
    print('='*70)

    # Cargar ciudades
    print('\n📋 Cargando ciudades europeas...')
    all_cities = load_european_cities()

    # Filtrar por país si se especifica
    if args.country:
        all_cities = [c for c in all_cities if c['country'].lower() == args.country.lower()]
        print(f'🔍 Filtrando solo: {args.country}')

    # Limitar cantidad
    if args.cities:
        all_cities = all_cities[:args.cities]

    print(f'✅ {len(all_cities)} ciudades a procesar\n')

    # Estadísticas
    total_processed = 0
    total_events = 0
    total_errors = 0

    # Procesar cada ciudad
    for i, city in enumerate(all_cities, 1):
        try:
            print(f'\n[{i}/{len(all_cities)}] Procesando {city["name"]}, {city["country"]}...')

            result = await scrape_single_city(city, use_brightdata=not args.no_brightdata)

            # Guardar si hay eventos
            if result['total_events'] > 0:
                # Determinar región para organizar archivos
                region_map = {
                    'Europa Occidental': 'europa-occidental',
                    'Europa Meridional': 'europa-meridional',
                    'Europa Septentrional': 'europa-septentrional',
                    'Europa Oriental': 'europa-oriental',
                    'Europa Nororiental': 'europa-nororiental'
                }
                region_dir = region_map.get(city.get('region'), 'europa-occidental')

                save_results(result, region_dir)
                total_events += result['total_events']

            total_processed += 1

            # Pequeña pausa entre ciudades para no saturar APIs
            await asyncio.sleep(2)

        except Exception as e:
            print(f'❌ Error procesando {city["name"]}: {str(e)[:100]}')
            total_errors += 1
            continue

    # Resumen final
    print('\n' + '='*70)
    print('🎉 SCRAPING COMPLETADO')
    print('='*70)
    print(f'✅ Ciudades procesadas: {total_processed}/{len(all_cities)}')
    print(f'📊 Total eventos encontrados: {total_events}')
    print(f'❌ Errores: {total_errors}')
    print(f'💾 Resultados guardados en: {RESULTS_DIR}')
    print('='*70 + '\n')


if __name__ == "__main__":
    asyncio.run(main())
