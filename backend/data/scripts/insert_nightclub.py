#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inserta eventos de nightclub.json a la base de datos
Convierte formato local al formato de la BD
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid

load_dotenv()

def parse_venue_city(lugar):
    """Extrae venue y ciudad del campo 'lugar'"""
    # Ej: "Native Beach Club, Cardales" -> venue: "Native Beach Club", city: "Cardales"
    if ',' in lugar:
        parts = lugar.split(',')
        venue = parts[0].strip()
        city = parts[-1].strip()
    else:
        venue = lugar
        city = "Buenos Aires"  # Default

    return venue, city

def convert_event(evento):
    """Convierte formato nightclub al formato BD"""
    venue, city = parse_venue_city(evento.get('lugar', ''))

    return {
        'id': str(uuid.uuid4()),
        'title': evento.get('nombre', ''),
        'description': evento.get('descripcion', ''),
        'start_datetime': evento.get('fecha_inicio', '') + ' 23:00:00',  # Asumimos 23hs
        'end_datetime': evento.get('fecha_fin', '') + ' 06:00:00' if evento.get('fecha_fin') else None,
        'venue_name': venue,
        'city': city,
        'country': 'Argentina',
        'category': 'Música',
        'subcategory': 'Electrónica',
        'source': 'nightclub',
        'is_free': 0,
        'price': None,
        'image_url': None,
        'event_url': None,
        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    print('='*70)
    print('🎧 INSERTANDO EVENTOS DE NIGHTCLUB')
    print('='*70)

    # Leer archivo
    nightclub_file = Path(__file__).parent.parent / 'regions' / 'nightclub.json'

    if not nightclub_file.exists():
        print(f"❌ No se encontró {nightclub_file}")
        return

    with open(nightclub_file, 'r', encoding='utf-8') as f:
        eventos_raw = json.load(f)

    print(f"📄 Archivo: {nightclub_file}")
    print(f"📊 {len(eventos_raw)} eventos encontrados\n")

    # Convertir eventos
    eventos = [convert_event(e) for e in eventos_raw]

    # Conectar a BD
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url, pool_pre_ping=True)
    conn = engine.connect()
    print("✅ Conectado a MySQL\n")

    # Insertar eventos
    inserted = 0
    duplicates = 0

    for evento in eventos:
        try:
            # Verificar si ya existe (por título + fecha + venue)
            result = conn.execute(text("""
                SELECT COUNT(*) FROM events
                WHERE title = :title
                AND DATE(start_datetime) = DATE(:start_datetime)
                AND venue_name = :venue_name
            """), {
                'title': evento['title'],
                'start_datetime': evento['start_datetime'],
                'venue_name': evento['venue_name']
            })

            if result.fetchone()[0] > 0:
                duplicates += 1
                continue

            # Insertar
            conn.execute(text("""
                INSERT INTO events (
                    id, title, description, start_datetime, end_datetime,
                    venue_name, city, country, category, subcategory,
                    source, is_free, price, image_url, event_url, scraped_at
                ) VALUES (
                    :id, :title, :description, :start_datetime, :end_datetime,
                    :venue_name, :city, :country, :category, :subcategory,
                    :source, :is_free, :price, :image_url, :event_url, :scraped_at
                )
            """), evento)

            conn.commit()
            inserted += 1
            print(f"✅ [{inserted}] {evento['title'][:50]}")

        except Exception as e:
            print(f"❌ Error: {evento['title'][:30]} - {str(e)[:50]}")

    conn.close()

    print('\n' + '='*70)
    print('🎉 PROCESO COMPLETADO')
    print('='*70)
    print(f"✅ Insertados: {inserted}")
    print(f"⚠️  Duplicados: {duplicates}")
    print(f"📊 Total procesados: {len(eventos)}")
    print('='*70)

if __name__ == "__main__":
    main()
