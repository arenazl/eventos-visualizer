#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consulta todos los eventos de felo.ai insertados en MySQL
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

# Cargar .env desde backend/
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
ENV_FILE = BACKEND_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configuración de MySQL desde .env
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
    """Query felo events from MySQL"""

    print("=" * 80)
    print("🔍 CONSULTA DE EVENTOS FELO.AI EN MYSQL")
    print("=" * 80)

    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Conectado a MySQL\n")
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    # Lista de barrios de Buenos Aires que se scrapearon con felo
    barrios_felo = [
        'Palermo', 'Puerto Madero', 'Recoleta', 'Retiro',
        'San Telmo', 'Villa Crespo', 'Almagro', 'Belgrano',
        'Caballito', 'Núñez', 'Nuñez'
    ]

    try:
        # Query 1: Contar eventos por barrio desde 2025-11-12
        print("📊 EVENTOS POR BARRIO (desde 2025-11-12):\n")

        for barrio in barrios_felo:
            count_sql = '''
                SELECT COUNT(*) as total
                FROM events
                WHERE city LIKE %s
                AND created_at >= '2025-11-12'
            '''
            cursor.execute(count_sql, (f'%{barrio}%',))
            result = cursor.fetchone()

            if result and result['total'] > 0:
                print(f"  {barrio}: {result['total']} eventos")

        # Query 2: Total de eventos de Buenos Aires desde 2025-11-12
        print("\n" + "=" * 80)
        print("📍 TOTAL BUENOS AIRES (desde 2025-11-12):\n")

        total_sql = '''
            SELECT COUNT(*) as total
            FROM events
            WHERE (city LIKE '%Buenos%Aires%' OR city LIKE '%Palermo%' OR city LIKE '%Recoleta%'
                   OR city LIKE '%Retiro%' OR city LIKE '%Puerto%Madero%')
            AND created_at >= '2025-11-12'
        '''
        cursor.execute(total_sql)
        result = cursor.fetchone()
        print(f"  Total eventos Buenos Aires: {result['total']}\n")

        # Query 3: Listar últimos 50 eventos con detalles
        print("=" * 80)
        print("📋 ÚLTIMOS 50 EVENTOS DE BUENOS AIRES:\n")

        list_sql = '''
            SELECT title, city, DATE(start_datetime) as fecha, created_at
            FROM events
            WHERE (city LIKE '%Buenos%Aires%' OR city LIKE '%Palermo%' OR city LIKE '%Recoleta%'
                   OR city LIKE '%Retiro%' OR city LIKE '%Puerto%Madero%' OR city LIKE '%San%Telmo%'
                   OR city LIKE '%Villa%Crespo%' OR city LIKE '%Almagro%' OR city LIKE '%Belgrano%'
                   OR city LIKE '%Caballito%' OR city LIKE '%Núñez%' OR city LIKE '%Nuñez%')
            AND created_at >= '2025-11-12'
            ORDER BY created_at DESC
            LIMIT 50
        '''
        cursor.execute(list_sql)
        eventos = cursor.fetchall()

        if eventos:
            for i, evento in enumerate(eventos, 1):
                print(f"{i:2}. [{evento['city']}] {evento['title'][:60]}")
                print(f"    Fecha evento: {evento['fecha']} | Insertado: {evento['created_at']}")
                print()
        else:
            print("  ❌ No se encontraron eventos\n")

        # Query 4: Eventos insertados HOY
        print("=" * 80)
        print("🆕 EVENTOS INSERTADOS HOY:\n")

        today_sql = '''
            SELECT COUNT(*) as total
            FROM events
            WHERE DATE(created_at) = CURDATE()
        '''
        cursor.execute(today_sql)
        result = cursor.fetchone()
        print(f"  Total eventos hoy: {result['total']}\n")

    except Exception as e:
        print(f"❌ Error en query: {e}")
    finally:
        cursor.close()
        connection.close()
        print("=" * 80)

if __name__ == "__main__":
    main()
