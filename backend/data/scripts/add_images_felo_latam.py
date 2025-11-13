#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agrega imágenes a eventos de Latinoamérica usando Felo.ai
Busca cada evento en Felo y extrae URLs de imágenes
"""

import sys
import json
from pathlib import Path
import requests
import time
import re

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

LATAM_DIR = Path(__file__).parent.parent / 'scrapper_results' / 'latinamerica'

def get_felo_image(event_title, venue='', city=''):
    """Busca imagen del evento en Felo.ai"""

    # Construir query de búsqueda
    search_query = f"{event_title} {venue} {city} event image"

    url = 'https://api.felo.ai/search'

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    payload = {
        'query': search_query,
        'search_type': 'image',
        'num_results': 1
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()

            # Extraer primera imagen de los resultados
            if 'results' in data and len(data['results']) > 0:
                first_result = data['results'][0]

                # Felo puede retornar la imagen en diferentes campos
                image_url = (first_result.get('image_url') or
                           first_result.get('thumbnail') or
                           first_result.get('url'))

                if image_url:
                    return image_url

        return None

    except Exception as e:
        print(f"    Error Felo: {str(e)[:50]}")
        return None


def process_json_file(file_path):
    """Procesa un archivo JSON y agrega imágenes"""
    print(f"\n📄 {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Detectar estructura
    eventos = []
    if isinstance(data, dict):
        if 'eventos' in data:
            eventos = data['eventos']
        elif 'events' in data:
            eventos = data['events']
    elif isinstance(data, list):
        eventos = data

    if not eventos:
        print('  ⚠️  Sin eventos')
        return 0

    city = data.get('city', data.get('ciudad', ''))

    added = 0

    for i, evento in enumerate(eventos):
        # Si ya tiene imagen, skip
        if evento.get('image_url'):
            continue

        title = evento.get('title', evento.get('nombre', evento.get('titulo', '')))
        venue = evento.get('venue', evento.get('lugar', ''))

        if not title:
            continue

        print(f"  [{i+1}/{len(eventos)}] {title[:40]}...", end=' ')

        image_url = get_felo_image(title, venue, city)

        if image_url:
            evento['image_url'] = image_url
            added += 1
            print('✅')
        else:
            print('⚠️')

        # Rate limit: 2 requests por segundo
        time.sleep(0.5)

    # Guardar JSON actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  💾 {added} imágenes agregadas")

    return added


def main():
    print('='*70)
    print('🖼️  AGREGANDO IMÁGENES CON FELO.AI - LATINOAMÉRICA')
    print('='*70)

    total_added = 0
    total_files = 0

    # Recorrer todas las subcarpetas
    for json_file in LATAM_DIR.rglob('*.json'):
        # Filtrar configs y archivos no relevantes
        if any(x in json_file.name.lower() for x in ['config', 'package', 'readme']):
            continue

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
