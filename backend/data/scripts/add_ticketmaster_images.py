#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agrega imágenes de Ticketmaster API a eventos de Europa
Busca cada evento en Ticketmaster y extrae su imagen oficial
"""

import sys
import json
from pathlib import Path
import requests
import time

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

EUROPA_DIR = Path(__file__).parent.parent / 'scrapper_results' / 'europa'
TICKETMASTER_KEY = 'BnAVSbJZ7dVvPwFh91UVOmwX4CU1Ft5g'

def get_ticketmaster_image(event_title, city, country_code):
    """Busca imagen del evento en Ticketmaster"""
    url = 'https://app.ticketmaster.com/discovery/v2/events.json'

    params = {
        'apikey': TICKETMASTER_KEY,
        'keyword': event_title.split(' ')[0],  # Primera palabra del título
        'city': city,
        'countryCode': country_code,
        'size': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            events = data.get('_embedded', {}).get('events', [])

            if events:
                # Obtener imágenes del evento
                images = events[0].get('images', [])

                if images:
                    # Buscar la imagen más grande
                    best_image = max(images, key=lambda x: x.get('width', 0) * x.get('height', 0))
                    return best_image.get('url')

        return None

    except Exception as e:
        return None


def process_json_file(file_path):
    """Procesa un archivo JSON y agrega imágenes"""
    print(f"\n📄 {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'eventos' not in data or not data['eventos']:
        print('  ⚠️  Sin eventos')
        return 0

    city = data.get('city', '')
    country = data.get('country', '')

    # Mapeo de países a códigos
    country_codes = {
        'España': 'ES', 'Alemania': 'DE', 'Francia': 'FR',
        'Italia': 'IT', 'Países Bajos': 'NL', 'Suiza': 'CH',
        'Reino Unido': 'GB', 'Irlanda': 'IE', 'Noruega': 'NO',
        'Finlandia': 'FI', 'Polonia': 'PL', 'Chequia': 'CZ',
        'Austria': 'AT', 'Grecia': 'GR'
    }

    country_code = country_codes.get(country, 'ES')

    added = 0

    for i, evento in enumerate(data['eventos']):
        # Si ya tiene imagen, skip
        if evento.get('image_url'):
            continue

        # Solo para eventos de Ticketmaster
        if evento.get('source') != 'ticketmaster':
            continue

        print(f"  [{i+1}/{len(data['eventos'])}] {evento.get('title', '')[:40]}...", end=' ')

        image_url = get_ticketmaster_image(
            evento.get('title', ''),
            city,
            country_code
        )

        if image_url:
            evento['image_url'] = image_url
            added += 1
            print('✅')
        else:
            print('⚠️')

        # Rate limit: 5 requests por segundo max
        time.sleep(0.2)

    # Guardar JSON actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  💾 {added} imágenes agregadas")

    return added


def main():
    print('='*70)
    print('🖼️  AGREGANDO IMÁGENES DE TICKETMASTER')
    print('='*70)

    total_added = 0
    total_files = 0

    # Recorrer todas las carpetas de países
    for country_dir in EUROPA_DIR.iterdir():
        if not country_dir.is_dir():
            continue

        print(f'\n🌍 {country_dir.name.upper()}')
        print('-'*70)

        for json_file in country_dir.glob('*.json'):
            added = process_json_file(json_file)
            total_added += added
            total_files += 1

    print('\n' + '='*70)
    print('🎉 PROCESO COMPLETADO')
    print('='*70)
    print(f'📊 Archivos procesados: {total_files}')
    print(f'🖼️  Total imágenes agregadas: {total_added}')
    print('='*70 + '\n')


if __name__ == "__main__":
    main()
