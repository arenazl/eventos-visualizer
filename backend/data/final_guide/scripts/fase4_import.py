#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FASE 3: Importación a MySQL desde JSONs parseados

Importa eventos desde scrapper_results/parsed/ a MySQL con:
- Fuzzy duplicate detection (80% word similarity)
- UUID generation
- Soporte para neighborhood null (eventos sin barrio)
- Categorías ya definidas en FASE 2

Uso:
    python fase3_import.py                    # Importa todos los JSONs nuevos
    python fase3_import.py --reset            # Reinicia log y reprocesa todo
    python fase3_import.py --dry-run          # Preview sin importar
"""

import json
import pymysql
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Set
from datetime import datetime
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent.parent
ENV_FILE = BACKEND_DIR / '.env'

# Cargar .env
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configuración MySQL desde .env
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'events'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Archivo de log para tracking
LOG_FILE = SCRIPT_DIR / '.imported_files.log'

# Directorio de JSONs parseados
PARSED_DIR = SCRIPT_DIR.parent.parent / 'scrapper_results' / 'parsed'


# ========== FUNCIONES AUXILIARES ==========

def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def load_imported_files() -> Set[str]:
    """Carga lista de archivos ya importados"""
    if not LOG_FILE.exists():
        return set()

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def mark_as_imported(filepath: Path):
    """Marca un archivo como importado"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{filepath}\n")


def parse_fecha(fecha_str: str) -> str:
    """Convierte fecha a formato ISO 8601"""
    if not fecha_str:
        return datetime.now().isoformat()

    # Si ya está en formato ISO
    if 'T' in fecha_str or len(fecha_str) == 10:
        return fecha_str

    # Formatos posibles
    formatos = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(fecha_str.split('.')[0], formato)
            return dt.isoformat()
        except ValueError:
            continue

    # Si no matchea, usar fecha actual
    return datetime.now().isoformat()


def extract_price(precio_str) -> tuple:
    """Extrae precio numérico y si es gratis"""
    if not precio_str:
        return 0.0, True

    precio_lower = str(precio_str).lower()

    # Detectar eventos gratuitos
    if any(word in precio_lower for word in ['gratis', 'free', 'libre', 'gratuito']):
        return 0.0, True

    # Intentar extraer número
    try:
        # Eliminar símbolos de moneda y espacios
        precio_clean = precio_lower.replace('$', '').replace('€', '').replace('£', '').strip()
        precio_clean = precio_clean.replace(',', '.').split()[0]
        return float(precio_clean), False
    except (ValueError, IndexError):
        return 0.0, False


def process_evento(evento: Dict, source_file: Path) -> Optional[Dict]:
    """
    Procesa un evento individual del JSON parseado

    IMPORTANTE: Los eventos ya vienen con:
    - category y subcategory definidos en FASE 2
    - neighborhood puede ser null (es válido)
    - fecha en formato ISO
    """
    # Validar campos obligatorios
    title = evento.get('nombre', '').strip()
    if not title:
        print(f"    ⚠️  Evento sin nombre, saltando")
        return None

    # Descripción
    description = evento.get('descripcion', '')[:1000]

    # Fecha
    fecha_str = evento.get('fecha', '')
    start_datetime = parse_fecha(fecha_str)
    end_datetime = start_datetime  # Gemini no provee fecha fin

    # Ubicación
    venue_name = evento.get('lugar', 'Por definir')[:255]
    venue_address = evento.get('direccion', '')[:500]

    # Ciudad y país
    city = evento.get('ciudad', 'Buenos Aires')[:100]
    country = evento.get('pais', 'Argentina')[:100]

    # NEIGHBORHOOD: puede ser null, NO descartar el evento
    neighborhood = evento.get('neighborhood')  # Ya viene del parser
    if neighborhood:
        neighborhood = neighborhood[:100]

    # Categoría (YA viene del parser FASE 2)
    category = evento.get('category', 'other')
    subcategory = evento.get('subcategory', 'general')

    # Precio
    precio_str = evento.get('precio', '')
    es_gratis = evento.get('es_gratis', False)

    # Si es_gratis ya viene definido, usarlo
    if es_gratis:
        price = 0.0
        is_free = True
    else:
        price, is_free = extract_price(precio_str)

    # Moneda (default ARS para Argentina)
    currency = 'ARS'
    if 'EUR' in str(precio_str).upper() or 'EURO' in str(precio_str).upper():
        currency = 'EUR'
    elif 'USD' in str(precio_str).upper() or 'DÓLAR' in str(precio_str).upper():
        currency = 'USD'

    # Coordenadas (Gemini no las provee por ahora)
    latitude = evento.get('latitude')
    longitude = evento.get('longitude')

    # Imagen y URL
    image_url = evento.get('image_url')
    event_url = evento.get('event_url')

    # Source
    source = evento.get('source', 'gemini')

    return {
        'title': title[:255],
        'description': description,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'city': city,
        'neighborhood': neighborhood,  # Puede ser None
        'country': country,
        'latitude': latitude,
        'longitude': longitude,
        'category': category,
        'subcategory': subcategory,
        'price': price,
        'currency': currency,
        'is_free': is_free,
        'image_url': image_url,
        'event_url': event_url,
        'source_api': source
    }


def insert_event(cursor, evento_data: Dict) -> tuple:
    """
    Inserta evento en MySQL con fuzzy duplicate detection

    Returns:
        tuple: (inserted: bool, reason: str)
        - (True, 'inserted') si se insertó
        - (False, 'duplicate_exact') si título exacto existe
        - (False, 'duplicate_fuzzy') si título similar >=80%
    """
    try:
        title = evento_data['title']
        city = evento_data['city']
        fecha = evento_data['start_datetime']

        # PASO 1: Verificar duplicado EXACTO
        check_exact_sql = '''
            SELECT id, title FROM events
            WHERE title = %s
            AND city = %s
            AND DATE(start_datetime) = DATE(%s)
            LIMIT 1
        '''
        cursor.execute(check_exact_sql, (title, city, fecha))

        if cursor.fetchone():
            return (False, 'duplicate_exact')

        # PASO 2: Fuzzy duplicate detection (80% similitud)
        check_fuzzy_sql = '''
            SELECT id, title FROM events
            WHERE city = %s
            AND DATE(start_datetime) = DATE(%s)
        '''
        cursor.execute(check_fuzzy_sql, (city, fecha))

        existing_events = cursor.fetchall()

        for existing in existing_events:
            existing_title = existing['title'].lower()
            new_title = title.lower()

            # Comparación por palabras en común
            existing_words = set(existing_title.split())
            new_words = set(new_title.split())

            if len(new_words) == 0:
                continue

            common_words = existing_words & new_words
            similarity = len(common_words) / len(new_words)

            # 80% threshold
            if similarity >= 0.8:
                return (False, f'duplicate_fuzzy:{existing["title"][:40]}')

        # PASO 3: No hay duplicados, insertar
        import uuid
        event_id = str(uuid.uuid4())

        insert_sql = '''
            INSERT INTO events (
                id,
                title, description, start_datetime, end_datetime,
                venue_name, venue_address, city, neighborhood, country,
                latitude, longitude,
                category, subcategory,
                price, is_free,
                image_url, event_url, source,
                created_at, updated_at
            ) VALUES (
                %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                NOW(), NOW()
            )
        '''

        cursor.execute(insert_sql, (
            event_id,
            evento_data['title'],
            evento_data['description'],
            evento_data['start_datetime'],
            evento_data['end_datetime'],
            evento_data['venue_name'],
            evento_data['venue_address'],
            evento_data['city'],
            evento_data['neighborhood'],  # Puede ser None
            evento_data['country'],
            evento_data['latitude'],
            evento_data['longitude'],
            evento_data['category'],
            evento_data['subcategory'],
            str(evento_data['price']),
            evento_data['is_free'],
            evento_data['image_url'],
            evento_data['event_url'],
            evento_data['source_api']
        ))

        return (True, 'inserted')

    except Exception as e:
        error_msg = str(e)[:80]
        return (False, f'error:{error_msg}')


def find_parsed_json_files() -> List[Path]:
    """Encuentra todos los JSONs parseados en scrapper_results/parsed/"""
    if not PARSED_DIR.exists():
        print(f"❌ Directorio {PARSED_DIR} no existe")
        return []

    # Buscar recursivamente en parsed/
    all_jsons = list(PARSED_DIR.rglob('*.json'))

    # Filtrar archivos válidos
    valid_jsons = [
        f for f in all_jsons
        if f.stat().st_size > 100  # Al menos 100 bytes
        and 'config' not in f.name.lower()
    ]

    return valid_jsons


def process_json_file(filepath: Path, cursor, dry_run: bool = False) -> dict:
    """Procesa un archivo JSON parseado"""
    relative_path = filepath.relative_to(PARSED_DIR)
    print(f"\n📄 {relative_path}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error leyendo JSON: {e}")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_fuzzy': 0,
            'errores': 1
        }

    # JSONs parseados son arrays de eventos
    if not isinstance(data, list):
        print(f"  ❌ Formato inesperado (esperaba array)")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_fuzzy': 0,
            'errores': 1
        }

    events = data
    print(f"  📊 {len(events)} eventos encontrados")

    if dry_run:
        print(f"  🔍 [DRY-RUN] Se procesarían {len(events)} eventos")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_fuzzy': 0,
            'errores': 0
        }

    # Contadores
    insertados = 0
    duplicate_exact = 0
    duplicate_fuzzy = 0
    errores = 0

    for evento in events:
        evento_data = process_evento(evento, filepath)
        if not evento_data:
            errores += 1
            continue

        # Insertar
        success, reason = insert_event(cursor, evento_data)

        if success:
            insertados += 1
        elif reason == 'duplicate_exact':
            duplicate_exact += 1
        elif reason.startswith('duplicate_fuzzy'):
            duplicate_fuzzy += 1
        else:
            errores += 1
            if reason.startswith('error'):
                error_msg = reason.split(':', 1)[1] if ':' in reason else reason
                print(f"    ❌ {evento_data['title'][:50]} → {error_msg}")

    # Resumen
    total_duplicados = duplicate_exact + duplicate_fuzzy
    print(f"  ✅ {insertados} nuevos | ⏭️  {total_duplicados} duplicados | ❌ {errores} errores")

    return {
        'insertados': insertados,
        'duplicate_exact': duplicate_exact,
        'duplicate_fuzzy': duplicate_fuzzy,
        'errores': errores
    }


def main():
    """Main function"""
    # Parsear argumentos
    reset_log = '--reset' in sys.argv
    dry_run = '--dry-run' in sys.argv

    print("=" * 80)
    print("🚀 FASE 3: IMPORTACIÓN A MYSQL")
    print("=" * 80)

    if dry_run:
        print("\n🔍 MODO DRY-RUN: Mostrará qué se importaría sin modificar la BD")

    if reset_log:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print("\n🔄 Log de archivos importados reiniciado")

    # Cargar archivos ya procesados
    imported_files = load_imported_files()
    print(f"\n📋 Archivos previamente importados: {len(imported_files)}")

    # Buscar JSONs parseados
    all_json_files = find_parsed_json_files()
    print(f"📂 Total JSONs parseados encontrados: {len(all_json_files)}")

    # Filtrar solo nuevos
    new_files = [f for f in all_json_files if str(f) not in imported_files]
    print(f"🆕 Archivos nuevos para importar: {len(new_files)}")

    if not new_files:
        print("\n✅ No hay archivos nuevos para importar")
        print("💡 Usa --reset para reprocesar todos los archivos")
        return

    # Preview
    print("\n📋 Archivos que se importarán:")
    for i, f in enumerate(new_files[:10], 1):
        rel_path = f.relative_to(PARSED_DIR)
        print(f"  {i}. {rel_path}")

    if len(new_files) > 10:
        print(f"  ... y {len(new_files) - 10} más")

    if dry_run:
        print("\n🔍 [DRY-RUN] No se importará nada")
        return

    # Conectar a MySQL
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("\n✅ Conectado a MySQL")
    except Exception as e:
        print(f"\n❌ Error conectando a MySQL: {e}")
        print(f"\n💡 Verifica tu .env en: {ENV_FILE}")
        sys.exit(1)

    # Procesar archivos
    total_insertados = 0
    total_duplicate_exact = 0
    total_duplicate_fuzzy = 0
    total_errores = 0
    archivos_procesados = 0

    for json_file in new_files:
        try:
            stats = process_json_file(json_file, cursor, dry_run=False)
            total_insertados += stats['insertados']
            total_duplicate_exact += stats['duplicate_exact']
            total_duplicate_fuzzy += stats['duplicate_fuzzy']
            total_errores += stats['errores']

            # Commit después de cada archivo
            connection.commit()

            # Marcar como importado
            mark_as_imported(json_file)
            archivos_procesados += 1

        except Exception as e:
            print(f"  ❌ Error procesando: {e}")
            connection.rollback()

    # Cerrar conexión
    cursor.close()
    connection.close()

    # Resumen final
    total_duplicados = total_duplicate_exact + total_duplicate_fuzzy
    print("\n" + "=" * 80)
    print("✨ IMPORTACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n📊 Archivos procesados: {archivos_procesados}")
    print(f"✅ Eventos insertados: {total_insertados}")
    print(f"⏭️  Eventos duplicados: {total_duplicados}")
    print(f"   • Duplicados exactos: {total_duplicate_exact}")
    print(f"   • Duplicados fuzzy (≥80% similares): {total_duplicate_fuzzy}")
    print(f"❌ Errores: {total_errores}")

    if total_insertados + total_errores > 0:
        tasa_exito = (total_insertados / (total_insertados + total_errores)) * 100
        print(f"\n📈 Tasa de éxito: {tasa_exito:.1f}%")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
