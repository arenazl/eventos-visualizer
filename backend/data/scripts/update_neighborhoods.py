#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para actualizar el campo neighborhood en eventos existentes
que tienen barrios de Buenos Aires registrados
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

# Lista de barrios porteños
BARRIOS_BSAS = [
    'Palermo', 'Recoleta', 'San Telmo', 'Puerto Madero', 'Retiro',
    'Belgrano', 'Villa Crespo', 'Almagro', 'Caballito', 'Nunez', 'Núñez',
    'Colegiales', 'Chacarita', 'Flores', 'Boedo', 'Barracas',
    'La Boca', 'Constitución', 'Monserrat', 'San Nicolás', 'Balvanera',
    'Villa Urquiza', 'Villa Devoto', 'Saavedra', 'Coghlan'
]


def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def main():
    print("=" * 80)
    print("🔧 ACTUALIZAR NEIGHBORHOODS EN EVENTOS EXISTENTES")
    print("=" * 80)

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("\n✅ Conectado a MySQL")
    except Exception as e:
        print(f"\n❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    # 1. Encontrar eventos donde city está en la lista de barrios
    print("\n📊 Buscando eventos con barrios en el campo 'city'...")

    placeholders = ', '.join(['%s'] * len(BARRIOS_BSAS))
    query = f'''
        SELECT id, title, city, neighborhood
        FROM events
        WHERE city IN ({placeholders})
        AND (neighborhood IS NULL OR neighborhood = '')
        LIMIT 1000
    '''

    cursor.execute(query, BARRIOS_BSAS)
    eventos_por_actualizar = cursor.fetchall()

    print(f"   Encontrados: {len(eventos_por_actualizar)} eventos")

    if len(eventos_por_actualizar) == 0:
        print("\n✅ No hay eventos para actualizar")
        cursor.close()
        connection.close()
        return

    # 2. Actualizar cada evento
    actualizados = 0
    errores = 0

    for evento in eventos_por_actualizar:
        try:
            barrio = evento['city']

            update_sql = '''
                UPDATE events
                SET neighborhood = %s, city = 'Buenos Aires'
                WHERE id = %s
            '''

            cursor.execute(update_sql, (barrio, evento['id']))
            actualizados += 1

            if actualizados % 50 == 0:
                print(f"   Procesados: {actualizados}/{len(eventos_por_actualizar)}")
                connection.commit()

        except Exception as e:
            print(f"   ❌ Error en evento {evento['id']}: {e}")
            errores += 1

    # Commit final
    connection.commit()

    # Cerrar conexión
    cursor.close()
    connection.close()

    # Resumen
    print("\n" + "=" * 80)
    print("✨ ACTUALIZACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n✅ Eventos actualizados: {actualizados}")
    print(f"❌ Errores: {errores}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
