#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script genérico MUNDIAL para importar eventos de cualquier región a MySQL

🌍 DETECCIÓN AUTOMÁTICA:
- Ciudad y país desde estructura de carpetas
- Moneda por país (ARS, USD, EUR, GBP, etc.)
- Categorías multiidioma (español, inglés, francés)
- Formatos de fecha internacionales

📂 Estructura esperada:
scrapper_results/[continente]/[region]/[pais]/[mes]/[ciudad]_dia_gemini.json

Uso:
    python import_generic.py europa
    python import_generic.py latinamerica/sudamerica
    python import_generic.py scrapper_results/europa/europa-meridional/espana
    python import_generic.py scrapper_results/latinamerica/sudamerica/argentina/2025-11
"""

import json
import pymysql
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar path para importar desde final_guide/scripts/
SCRIPT_DIR = Path(__file__).parent
FINAL_GUIDE_SCRIPTS = SCRIPT_DIR.parent / 'final_guide' / 'scripts'
sys.path.insert(0, str(FINAL_GUIDE_SCRIPTS))

# Importar utilidades compartidas
from event_utils import categorize_event
from region_utils import get_pais_from_ciudad, get_provincia_from_ciudad

# Cargar .env desde backend/
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

def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def parse_fecha(fecha_str: str) -> str:
    """Convierte fecha a formato ISO 8601 con soporte internacional"""
    if not fecha_str:
        return datetime.now().isoformat()

    # Limpiar string (espacios extra, "todo el día", etc)
    fecha_str = str(fecha_str).strip()

    # Si es "todo el día" o similar, usar fecha actual
    if any(word in fecha_str.lower() for word in ['todo', 'all day', 'tbd']):
        return datetime.now().isoformat()

    # Detectar RANGOS DE FECHAS y tomar la fecha de inicio
    # Formatos: "2025-11-07/2025-11-16", "15/11/2025-20/11/2025", "Nov 15-20, 2025"
    if '/' in fecha_str and '-' in fecha_str:
        # Formato ISO: 2025-11-07/2025-11-16
        if fecha_str.count('-') >= 4:  # Al menos 2 fechas completas
            fecha_inicio = fecha_str.split('/')[0].strip()
            fecha_str = fecha_inicio
    elif ' - ' in fecha_str or ' al ' in fecha_str or ' to ' in fecha_str:
        # Formato: "15 de noviembre al 20 de noviembre" o "Nov 15 - Nov 20"
        separadores = [' - ', ' al ', ' to ', ' hasta ']
        for sep in separadores:
            if sep in fecha_str:
                fecha_inicio = fecha_str.split(sep)[0].strip()
                fecha_str = fecha_inicio
                break

    # Si contiene "A confirmar", usar fecha actual
    if 'a confirmar' in fecha_str.lower():
        return datetime.now().isoformat()

    # Formatos posibles (internacional)
    formatos = [
        '%Y-%m-%dT%H:%M:%S',  # ISO 8601 completo con segundos
        '%Y-%m-%dT%H:%M',     # ISO 8601 sin segundos (ej: 2025-11-29T21:00)
        '%Y-%m-%d',           # 2025-11-15 (ISO)
        '%d/%m/%Y',           # 15/11/2025 (Europa/América Latina)
        '%m/%d/%Y',           # 11/15/2025 (USA)
        '%d-%m-%Y',           # 15-11-2025
        '%Y/%m/%d',           # 2025/11/15
        '%Y-%m-%d %H:%M:%S',  # Datetime
        '%d/%m/%Y %H:%M',     # Con hora
        '%Y-%m-%d %H:%M',     # Con hora
        '%d de %B de %Y',     # 15 de noviembre de 2025 (español)
        '%B %d, %Y',          # November 15, 2025 (inglés)
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(fecha_str.split('.')[0], formato)
            return dt.isoformat()
        except (ValueError, AttributeError):
            continue

    # Si no matchea ningún formato, usar fecha actual
    print(f"  ⚠️  Formato de fecha no reconocido: {fecha_str}, usando fecha actual")
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


def extract_location_from_path(filepath: Path) -> tuple:
    """Extrae ciudad y país de la estructura de carpetas o nombre de archivo

    Estructura esperada:
    scrapper_results/[continente]/[region]/[pais]/[mes]/[ciudad]_dia_gemini.json

    Retorna: (ciudad, pais, moneda)
    """
    # Mapeo de países a monedas
    CURRENCY_MAP = {
        'argentina': 'ARS',
        'brasil': 'BRL', 'brazil': 'BRL',
        'chile': 'CLP',
        'colombia': 'COP',
        'mexico': 'MXN',
        'peru': 'PEN',
        'uruguay': 'UYU',
        'venezuela': 'VES',
        'espana': 'EUR', 'españa': 'EUR', 'spain': 'EUR',
        'francia': 'EUR', 'france': 'EUR',
        'italia': 'EUR', 'italy': 'EUR',
        'alemania': 'EUR', 'germany': 'EUR',
        'portugal': 'EUR',
        'reino unido': 'GBP', 'uk': 'GBP', 'united kingdom': 'GBP',
        'usa': 'USD', 'united states': 'USD', 'estados unidos': 'USD',
        'canada': 'CAD',
        'australia': 'AUD',
        'japon': 'JPY', 'japan': 'JPY',
        'china': 'CNY',
        'india': 'INR',
    }

    # Extraer ciudad del nombre del archivo
    filename = filepath.stem  # Sin extensión
    ciudad = None

    # Detectar patrones: "palermo_dia_gemini" o "buenos_aires_2025-11-03"
    if '_dia_gemini' in filename:
        ciudad = filename.replace('_dia_gemini', '').replace('_', ' ').title()
    elif '_' in filename:
        # Tomar la primera parte antes de números/fechas
        parts = filename.split('_')
        ciudad = ' '.join([p for p in parts if not p.isdigit() and not '-' in p]).title()

    # Extraer país de la estructura de carpetas
    pais = None
    parts = filepath.parts

    # Buscar en las últimas 5 carpetas
    for part in parts[-5:]:
        part_lower = part.lower()
        if part_lower in CURRENCY_MAP:
            pais = part.title()
            break

    # Detectar moneda por país
    currency = 'USD'  # Default internacional
    if pais:
        for country_key, curr in CURRENCY_MAP.items():
            if country_key in pais.lower():
                currency = curr
                break

    return (
        ciudad if ciudad else 'Unknown City',
        pais if pais else 'Unknown Country',
        currency
    )


def process_evento(evento: Dict, index: int, filepath: Path = None) -> Optional[Dict]:
    """Procesa un evento individual y retorna datos normalizados"""
    # Título (detectar campo: nombre, titulo, title)
    title = (evento.get('nombre') or evento.get('titulo') or evento.get('title') or 'Evento sin título')[:255]

    # Descripción
    description = (evento.get('descripcion') or evento.get('description') or '')[:1000]

    # Fechas
    fecha_inicio = evento.get('fecha_inicio') or evento.get('fecha') or evento.get('start_date') or ''
    fecha_fin = evento.get('fecha_fin') or evento.get('end_date') or ''

    start_datetime = parse_fecha(fecha_inicio)
    end_datetime = parse_fecha(fecha_fin) if fecha_fin else start_datetime

    # Ubicación
    venue_name = (evento.get('venue') or evento.get('lugar') or evento.get('location') or 'Por definir')[:255]
    venue_address = (evento.get('direccion') or evento.get('address') or '')[:500]

    # Extrae ciudad, país y moneda automáticamente desde estructura de carpetas
    auto_city, auto_country, auto_currency = extract_location_from_path(filepath) if filepath else (None, None, 'USD')

    # Ciudad y país (usar detección automática como fallback)
    city = (evento.get('ciudad') or evento.get('city') or auto_city)[:100]
    country = (evento.get('pais') or evento.get('country') or auto_country)[:100]

    # Coordenadas
    latitude = evento.get('latitud') or evento.get('latitude')
    longitude = evento.get('longitud') or evento.get('longitude')

    # Categoría
    categoria = evento.get('categoria') or evento.get('category') or ''
    category, subcategory = categorize_event(categoria, description)

    # Precio
    precio_str = evento.get('precio') or evento.get('price') or ''
    price, is_free = extract_price(precio_str)

    # Moneda (usar detección automática como fallback)
    currency = evento.get('moneda') or evento.get('currency') or auto_currency
    if 'eur' in currency.lower():
        currency = 'EUR'
    elif 'usd' in currency.lower() or 'dol' in currency.lower():
        currency = 'USD'
    elif 'gbp' in currency.lower() or 'pound' in currency.lower():
        currency = 'GBP'

    # Imagen - usar la de Google Images si existe
    image_url = evento.get('image_url')

    # URL del evento
    event_url = evento.get('url') or evento.get('event_url') or evento.get('link')

    return {
        'title': title,
        'description': description,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'city': city,
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
        'source_api': 'scraper'
    }


def insert_event(cursor, evento_data: Dict) -> bool:
    """Inserta evento en MySQL"""
    try:
        # Verificar si ya existe un evento con el mismo título, ciudad y fecha
        check_sql = '''
            SELECT id FROM events
            WHERE title = %s
            AND city = %s
            AND DATE(start_datetime) = DATE(%s)
            LIMIT 1
        '''
        cursor.execute(check_sql, (
            evento_data['title'],
            evento_data['city'],
            evento_data['start_datetime']
        ))

        if cursor.fetchone():
            return False  # Ya existe

        # Generar UUID para el id
        import uuid
        event_id = str(uuid.uuid4())

        # Insertar nuevo evento
        insert_sql = '''
            INSERT INTO events (
                id,
                title, description, start_datetime, end_datetime,
                venue_name, venue_address, city, country,
                latitude, longitude,
                category, subcategory,
                price, is_free,
                image_url, event_url, source,
                created_at, updated_at
            ) VALUES (
                %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
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
            evento_data['country'],
            evento_data['latitude'],
            evento_data['longitude'],
            evento_data['category'],
            evento_data['subcategory'],
            str(evento_data['price']),
            evento_data['is_free'],
            evento_data['image_url'],
            evento_data['event_url'],
            'gemini_scraper'
        ))

        return True

    except Exception as e:
        print(f"  ❌ Error insertando: {str(e)[:100]}")
        return False


def find_json_files(directory: Path) -> List[Path]:
    """Encuentra todos los JSONs recursivamente (cualquier mes/patrón)"""
    # Buscar archivos con patrones comunes: _dia_gemini, noviembre, o cualquier .json
    all_jsons = list(directory.rglob('*.json'))

    # Filtrar archivos que probablemente sean eventos (excluir configs, etc)
    event_jsons = [
        f for f in all_jsons
        if not any(exclude in f.name.lower() for exclude in ['config', 'settings', 'package'])
    ]

    return event_jsons


def process_json_file(filepath: Path, cursor) -> dict:
    """Procesa un archivo JSON"""
    print(f"\n📄 Procesando: {filepath.relative_to(filepath.parents[3])}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error leyendo JSON: {e}")
        return {'insertados': 0, 'duplicados': 0, 'errores': 1}

    # Detectar estructura del JSON
    events = []

    if isinstance(data, dict):
        if 'eventos' in data and isinstance(data['eventos'], list):
            # Estructura: {ciudad, pais, eventos: [...]}
            events = data['eventos']
        elif 'eventos_ferias_festivales' in data or 'recitales_shows_fiestas' in data:
            # Estructura Puerto Rico
            events = (data.get('eventos_ferias_festivales', []) +
                     data.get('recitales_shows_fiestas', []))
    elif isinstance(data, list):
        # Estructura: [...eventos...]
        events = data

    if not events:
        print("  ⚠️  No se encontraron eventos en el archivo")
        return {'insertados': 0, 'duplicados': 0, 'errores': 0}

    insertados = 0
    duplicados = 0
    errores = 0

    for i, evento in enumerate(events):
        evento_data = process_evento(evento, i, filepath)
        if not evento_data:
            errores += 1
            continue

        if insert_event(cursor, evento_data):
            insertados += 1
        else:
            duplicados += 1

    print(f"  ✅ {insertados} insertados, {duplicados} duplicados, {errores} errores")

    return {'insertados': insertados, 'duplicados': duplicados, 'errores': errores}


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ Uso: python import_generic.py <region|path>")
        print("\nEjemplos:")
        print("  python import_generic.py europa")
        print("  python import_generic.py latinamerica")
        print("  python import_generic.py scrapper_results/europa/europa-meridional")
        sys.exit(1)

    region = sys.argv[1]
    base_dir = Path(__file__).parent.parent
    scrapper_results = base_dir / 'scrapper_results'

    # Determinar directorio objetivo
    if '/' in region or '\\' in region:
        target_dir = base_dir / region
    else:
        target_dir = scrapper_results / region

    print("=" * 70)
    print("IMPORTADOR GENÉRICO DE EVENTOS")
    print("=" * 70)
    print(f"\n📍 Región/Ruta: {region}")
    print(f"📂 Directorio: {target_dir}")

    if not target_dir.exists():
        print(f"\n❌ Directorio no existe: {target_dir}")
        sys.exit(1)

    # Buscar JSONs
    json_files = find_json_files(target_dir)

    if not json_files:
        print("\n❌ No se encontraron archivos JSON de eventos en el directorio")
        print("💡 Asegúrate de que los archivos tengan extensión .json")
        sys.exit(1)

    print(f"\n📊 {len(json_files)} archivos encontrados")

    # Conectar a MySQL
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("✅ Conectado a MySQL")
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    # Procesar archivos
    total_insertados = 0
    total_duplicados = 0
    total_errores = 0

    for json_file in json_files:
        try:
            stats = process_json_file(json_file, cursor)
            total_insertados += stats['insertados']
            total_duplicados += stats['duplicados']
            total_errores += stats['errores']

            # Commit cada archivo
            connection.commit()

        except Exception as e:
            print(f"  ❌ Error procesando archivo: {e}")
            total_errores += 1
            connection.rollback()

    # Cerrar conexión
    cursor.close()
    connection.close()

    # Resumen final
    print("\n" + "=" * 70)
    print("IMPORTACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\n📊 Archivos procesados: {len(json_files)}")
    print(f"✅ Eventos insertados: {total_insertados}")
    print(f"⏭️  Eventos duplicados: {total_duplicados}")
    print(f"❌ Errores: {total_errores}")
    print(f"\n📈 Tasa de éxito: {(total_insertados/(total_insertados + total_errores)*100 if total_insertados + total_errores > 0 else 0):.1f}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
