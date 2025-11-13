#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agrega categorías específicas a eventos de Europa
Analiza título y venue para detectar género musical
"""

import sys
import json
from pathlib import Path
import re

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

EUROPA_DIR = Path(__file__).parent.parent / 'scrapper_results' / 'europa'

# Palabras clave por categoría
CATEGORIES = {
    'techno': ['techno', 'berghain', 'tresor', 'drumcode'],
    'house': ['house', 'deep house', 'tech house'],
    'electronic': ['electronic', 'edm', 'electro', 'dj', 'rave'],
    'rock': ['rock', 'punk', 'metal', 'hardcore'],
    'pop': ['pop', 'mainstream'],
    'hip hop': ['hip hop', 'rap', 'trap'],
    'jazz': ['jazz', 'blues'],
    'classical': ['classical', 'orchestra', 'symphony'],
    'indie': ['indie', 'alternative'],
    'reggae': ['reggae', 'ska', 'dub'],
    'country': ['country', 'folk'],
    'latin': ['latin', 'salsa', 'bachata', 'reggaeton']
}

def detect_category(title, venue=''):
    """Detecta categoría basándose en título y venue"""
    text = f"{title} {venue}".lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    # Default
    return 'música'

def process_json_file(file_path):
    """Procesa un archivo JSON y agrega categorías"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'eventos' not in data or not data['eventos']:
        return 0

    updated = 0

    for evento in data['eventos']:
        # Solo actualizar si es categoría genérica
        if evento.get('category') == 'música':
            new_category = detect_category(
                evento.get('title', ''),
                evento.get('venue', '')
            )

            if new_category != 'música':
                evento['category'] = new_category
                updated += 1

    # Guardar
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return updated

def main():
    print('='*70)
    print('🏷️  AGREGANDO CATEGORÍAS A EVENTOS DE EUROPA')
    print('='*70)

    total_updated = 0
    total_files = 0

    # Recorrer todas las carpetas de países
    for country_dir in EUROPA_DIR.iterdir():
        if not country_dir.is_dir():
            continue

        print(f'\n🌍 {country_dir.name.upper()}')
        print('-'*70)

        for json_file in country_dir.glob('*.json'):
            print(f'  📄 {json_file.name}', end=' ')

            updated = process_json_file(json_file)

            if updated > 0:
                print(f'✅ {updated} categorizados')
                total_updated += updated
            else:
                print('⚠️  Sin cambios')

            total_files += 1

    print('\n' + '='*70)
    print('🎉 PROCESO COMPLETADO')
    print('='*70)
    print(f'📊 Archivos procesados: {total_files}')
    print(f'🏷️  Total eventos categorizados: {total_updated}')
    print('='*70 + '\n')

if __name__ == "__main__":
    main()
