#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Identifica y marca eventos de felo.ai específicamente
"""

import pymysql
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Cargar .env
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
ENV_FILE = BACKEND_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'events'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def main():
    print("=" * 80)
    print("🔍 IDENTIFICACIÓN DE EVENTOS FELO.AI")
    print("=" * 80)

    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Conectado a MySQL\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    barrios_felo = [
        'Palermo', 'Puerto Madero', 'Recoleta', 'Retiro',
        'San Telmo', 'Villa Crespo', 'Almagro', 'Belgrano',
        'Caballito', 'Núñez', 'Nuñez'
    ]

    try:
        # Query: Eventos de Buenos Aires insertados desde 2025-11-12 20:00
        query = '''
            SELECT
                id,
                title,
                city,
                DATE(start_datetime) as fecha_evento,
                created_at,
                source
            FROM events
            WHERE created_at >= '2025-11-12 20:00:00'
            AND (
                city LIKE '%Buenos%Aires%' OR
                city LIKE '%Palermo%' OR
                city LIKE '%Recoleta%' OR
                city LIKE '%Retiro%' OR
                city LIKE '%Puerto%Madero%' OR
                city LIKE '%San%Telmo%' OR
                city LIKE '%Villa%Crespo%' OR
                city LIKE '%Almagro%' OR
                city LIKE '%Belgrano%' OR
                city LIKE '%Caballito%' OR
                city LIKE '%Núñez%' OR
                city LIKE '%Nuñez%' OR
                city LIKE '%Felo%'
            )
            ORDER BY created_at DESC
        '''

        cursor.execute(query)
        eventos = cursor.fetchall()

        print(f"📊 TOTAL EVENTOS IDENTIFICADOS: {len(eventos)}\n")
        print("=" * 80)
        print("DESGLOSE POR BARRIO Y FECHA:\n")

        # Agrupar por ciudad
        por_ciudad = {}
        for evento in eventos:
            ciudad = evento['city']
            if ciudad not in por_ciudad:
                por_ciudad[ciudad] = []
            por_ciudad[ciudad].append(evento)

        for ciudad, evs in sorted(por_ciudad.items()):
            print(f"\n📍 {ciudad}: {len(evs)} eventos")
            print(f"   Rango inserción: {evs[-1]['created_at']} → {evs[0]['created_at']}")

        # Verificar si todos tienen source='gemini_scraper'
        print("\n" + "=" * 80)
        print("VERIFICACIÓN DE SOURCE:\n")

        sources = {}
        for evento in eventos:
            src = evento['source']
            if src not in sources:
                sources[src] = 0
            sources[src] += 1

        for src, count in sources.items():
            print(f"  {src}: {count} eventos")

        print("\n" + "=" * 80)
        print("PRIMEROS 10 EVENTOS (para verificar):\n")

        for i, evento in enumerate(eventos[:10], 1):
            print(f"{i}. [{evento['city']}] {evento['title'][:50]}")
            print(f"   ID: {evento['id']}")
            print(f"   Insertado: {evento['created_at']}")
            print()

        print("=" * 80)
        print(f"\n✅ Estos {len(eventos)} eventos pueden identificarse como felo.ai")
        print("   por el criterio: created_at >= '2025-11-12 20:00' + ciudad Buenos Aires\n")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
