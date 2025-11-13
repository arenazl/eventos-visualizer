#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para extraer neighborhoods de external_id y source
Patrones:
  - padron_{barrio}_noviembre_{num}
  - source contiene nombre del barrio
"""

import pymysql
import sys
import os
import re
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

# Lista de barrios porteños (para normalizar nombres)
BARRIOS_BSAS = {
    'palermo': 'Palermo',
    'recoleta': 'Recoleta',
    'san-telmo': 'San Telmo',
    'san telmo': 'San Telmo',
    'puerto-madero': 'Puerto Madero',
    'puerto madero': 'Puerto Madero',
    'retiro': 'Retiro',
    'belgrano': 'Belgrano',
    'villa-crespo': 'Villa Crespo',
    'villa crespo': 'Villa Crespo',
    'almagro': 'Almagro',
    'caballito': 'Caballito',
    'nunez': 'Núñez',
    'nuñez': 'Núñez',
    'colegiales': 'Colegiales',
    'chacarita': 'Chacarita',
    'flores': 'Flores',
    'boedo': 'Boedo',
    'barracas': 'Barracas',
    'la-boca': 'La Boca',
    'la boca': 'La Boca',
    'constitucion': 'Constitución',
    'constitución': 'Constitución',
    'monserrat': 'Monserrat',
    'montserrat': 'Monserrat',
    'san-nicolas': 'San Nicolás',
    'san nicolas': 'San Nicolás',
    'balvanera': 'Balvanera',
    'villa-urquiza': 'Villa Urquiza',
    'villa urquiza': 'Villa Urquiza',
    'villa-devoto': 'Villa Devoto',
    'villa devoto': 'Villa Devoto',
    'saavedra': 'Saavedra',
    'coghlan': 'Coghlan',
    'agronomia': 'Agronomía',
    'agronoma': 'Agronomía',
    'liniers': 'Liniers',
    'mataderos': 'Mataderos',
    'monte-castro': 'Monte Castro',
    'monte castro': 'Monte Castro',
    'parque-chas': 'Parque Chas',
    'parque chas': 'Parque Chas',
    'villa-ortuzar': 'Villa Ortúzar',
    'villa ortuzar': 'Villa Ortúzar',
    'villa-del-parque': 'Villa del Parque',
    'villa del parque': 'Villa del Parque',
    'villa-pueyrredon': 'Villa Pueyrredón',
    'villa pueyrredon': 'Villa Pueyrredón',
    'parque-patricios': 'Parque Patricios',
    'parque patricios': 'Parque Patricios',
}


def extract_barrio_from_external_id(external_id):
    """
    Extrae barrio de external_id con patrón: padron_{barrio}_noviembre_{num}
    """
    if not external_id:
        return None

    # Patrón: padron_{barrio}_noviembre_{num}
    match = re.match(r'padron_([a-z\-]+)_noviembre_\d+', external_id)
    if match:
        barrio_raw = match.group(1)
        # Normalizar nombre del barrio
        return BARRIOS_BSAS.get(barrio_raw.lower(), barrio_raw.replace('-', ' ').title())

    return None


def extract_barrio_from_source(source):
    """
    Extrae barrio del campo source si es un barrio conocido
    """
    if not source:
        return None

    source_lower = source.lower()

    # Normalizar y buscar en diccionario
    if source_lower in BARRIOS_BSAS:
        return BARRIOS_BSAS[source_lower]

    return None


def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def main():
    print("=" * 80)
    print("🔍 EXTRAER NEIGHBORHOODS DE EXTERNAL_ID Y SOURCE")
    print("=" * 80)

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("\n✅ Conectado a MySQL")
    except Exception as e:
        print(f"\n❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    # 1. Encontrar eventos de Buenos Aires sin neighborhood
    print("\n📊 Buscando eventos de Buenos Aires sin neighborhood...")

    query = '''
        SELECT id, external_id, source, neighborhood
        FROM events
        WHERE city = %s
        AND (neighborhood IS NULL OR neighborhood = '')
        LIMIT 2000
    '''

    cursor.execute(query, ('Buenos Aires',))
    eventos = cursor.fetchall()

    print(f"   Encontrados: {len(eventos)} eventos sin neighborhood")

    if len(eventos) == 0:
        print("\n✅ No hay eventos para actualizar")
        cursor.close()
        connection.close()
        return

    # 2. Procesar cada evento
    actualizados = 0
    errores = 0
    sin_barrio = 0

    for evento in eventos:
        try:
            event_id = evento['id']
            external_id = evento['external_id']
            source = evento['source']

            # Intentar extraer barrio
            barrio = None

            # Primero intentar desde external_id
            if external_id:
                barrio = extract_barrio_from_external_id(external_id)

            # Si no, intentar desde source
            if not barrio and source:
                barrio = extract_barrio_from_source(source)

            if barrio:
                # Actualizar evento
                update_sql = '''
                    UPDATE events
                    SET neighborhood = %s
                    WHERE id = %s
                '''

                cursor.execute(update_sql, (barrio, event_id))
                actualizados += 1

                if actualizados <= 10:
                    print(f"   ✅ {event_id[:20]}... → {barrio}")
                elif actualizados == 11:
                    print(f"   ... (continuando)")

                if actualizados % 50 == 0:
                    print(f"   Procesados: {actualizados}/{len(eventos)}")
                    connection.commit()
            else:
                sin_barrio += 1

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
    print("✨ EXTRACCIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n✅ Eventos actualizados: {actualizados}")
    print(f"⚠️  Sin barrio identificable: {sin_barrio}")
    print(f"❌ Errores: {errores}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
