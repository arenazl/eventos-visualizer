"""
Script para importar eventos de Puerto Rico a MySQL
"""
import json
import os
import sys
import uuid
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Configurar codificación
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

import pymysql

# Coordenadas por ciudad de Puerto Rico
CITY_COORDS = {
    "san juan": (18.4655, -66.1057),
    "bayamón": (18.3833, -66.1667),
    "bayamon": (18.3833, -66.1667),
    "carolina": (18.3809, -65.9571),
    "ponce": (18.0111, -66.6141),
    "caguas": (18.2342, -66.0356),
    "dorado": (18.4589, -66.2678),
    "isla verde": (18.4400, -66.0100),
}

CATEGORY_MAPPING = {
    "música": "music",
    "musica": "music",
    "music": "music",
    "concierto": "music",
    "show": "music",
    "cultural": "cultural",
    "festival": "festival",
    "feria": "festival",
    "fiesta": "party",
    "deportes": "sports",
    "sports": "sports",
    "teatro": "theater",
    "comedia": "comedy",
    "arte": "art",
    "electrónica": "music",
    "electronica": "music",
}


def get_city_coordinates(city: str) -> tuple:
    """Obtiene coordenadas de la ciudad"""
    normalized = city.lower().strip()
    coords = CITY_COORDS.get(normalized, (18.4655, -66.1057))  # Default San Juan
    lat, lng = coords
    # Agregar variación aleatoria
    lat += random.uniform(-0.01, 0.01)
    lng += random.uniform(-0.01, 0.01)
    return (round(lat, 6), round(lng, 6))


def normalize_category(categoria: str) -> str:
    """Normaliza categoría"""
    if not categoria:
        return "other"
    return CATEGORY_MAPPING.get(categoria.lower().strip(), "other")


def parse_fecha(fecha_str: str) -> Optional[datetime]:
    """Parsea fecha de diferentes formatos"""
    if not fecha_str or fecha_str == "Continuo":
        return None

    fecha_str = str(fecha_str).strip()

    # Formato YYYY-MM-DD
    if '-' in fecha_str and len(fecha_str) >= 10:
        try:
            return datetime.strptime(fecha_str[:10], '%Y-%m-%d')
        except:
            pass

    # Formato "Noviembre (varios juegos)" - usar día 15 por defecto
    if "noviembre" in fecha_str.lower() or "varios" in fecha_str.lower():
        return datetime(2025, 11, 15)

    # Extraer primer número como día
    import re
    match = re.search(r'\b(\d{1,2})\b', fecha_str)
    if match:
        day = int(match.group(1))
        if 1 <= day <= 30:
            return datetime(2025, 11, day)

    return None


def generate_picsum_image(event_title: str, event_id: str) -> str:
    """Genera URL de imagen Picsum acorde al título"""
    title_lower = event_title.lower()

    # IDs de Picsum categorizados por tema
    THEME_IMAGES = {
        'musica': [1, 48, 82, 133, 169, 174, 180, 201, 367, 452, 493, 659, 718, 790],
        'concierto': [1, 48, 82, 133, 169, 174, 180, 201, 367, 452, 493, 659, 718, 790],
        'festival': [292, 313, 329, 351, 395, 403, 429, 447, 496, 500, 544, 593, 616, 659],
        'playa': [152, 184, 206, 234, 274, 304, 332, 379, 405, 433, 473, 507, 532, 579],
        'deporte': [113, 143, 158, 205, 223, 244, 278, 299, 318, 358, 382, 407, 447, 496],
        'navidad': [21, 24, 61, 95, 123, 161, 193, 216, 247, 284, 311, 346, 387, 419],
        'teatro': [100, 128, 154, 177, 203, 231, 265, 289, 320, 353, 383, 412, 441, 478],
        'arte': [102, 129, 147, 178, 212, 239, 269, 295, 323, 349, 384, 417, 448, 485],
        'cultural': [102, 129, 147, 178, 212, 239, 269, 295, 323, 349, 384, 417, 448, 485],
        'comida': [162, 183, 213, 240, 276, 302, 334, 362, 390, 421, 455, 487, 514, 549],
        'feria': [292, 313, 329, 351, 395, 403, 429, 447, 496, 500, 544, 593, 616, 659],
        'mercado': [292, 313, 329, 351, 395, 403, 429, 447, 496, 500, 544, 593, 616, 659],
    }

    # Buscar tema en el título
    for keyword, image_ids in THEME_IMAGES.items():
        if keyword in title_lower:
            # Seleccionar imagen basada en hash para consistencia
            hash_num = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
            img_id = image_ids[hash_num % len(image_ids)]
            return f"https://picsum.photos/id/{img_id}/800/600"

    # Default: imagen basada en hash
    hash_num = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
    img_id = (hash_num % 500) + 1
    return f"https://picsum.photos/id/{img_id}/800/600"


def normalize_precio(precio_text: str) -> tuple:
    """Retorna (precio_str, is_free)"""
    if not precio_text:
        return ("a consultar", False)

    precio_lower = str(precio_text).lower().strip()

    if precio_lower in ["gratuito", "gratis", "free"]:
        return ("gratuito", True)

    if precio_lower in ["pago", "variable", "consultar"]:
        return ("a consultar", False)

    return (precio_text, False)


def process_evento(evento: Dict, location: str, country_code: str, index: int) -> Optional[Dict]:
    """Procesa un evento individual"""
    # Título
    title = evento.get('nombre', 'Evento sin título')[:255]

    # Fecha
    fecha_str = evento.get('fecha', '')
    start_datetime = parse_fecha(fecha_str)
    if not start_datetime:
        return None  # Sin fecha válida

    # Agregar hora
    hora_inicio = evento.get('hora_inicio', '19:00')
    if hora_inicio and ':' in str(hora_inicio):
        try:
            parts = str(hora_inicio).split(':')
            hour, minute = int(parts[0]), int(parts[1])
            start_datetime = start_datetime.replace(hour=hour, minute=minute)
        except:
            pass

    # Descripción
    description = evento.get('descripcion', '')[:5000] if evento.get('descripcion') else None

    # Lugar
    venue_name = evento.get('lugar', location)[:255]
    venue_address = evento.get('lugar', location)

    # Coordenadas
    lat, lng = get_city_coordinates(location)

    # Categoría
    categoria_raw = evento.get('categoria', 'other')
    category = normalize_category(categoria_raw)

    # Precio
    precio_raw = evento.get('precio', 'a consultar')
    price, is_free = normalize_precio(precio_raw)

    # IDs
    event_id = str(uuid.uuid4())
    external_id = f"padron_pr_{location.lower().replace(' ', '_')}_{index}"

    return {
        'id': event_id,
        'title': title,
        'description': description,
        'start_datetime': start_datetime,
        'end_datetime': None,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'latitude': lat,
        'longitude': lng,
        'category': category,
        'subcategory': categoria_raw if category != categoria_raw else None,
        'price': price,
        'is_free': is_free,
        'external_id': external_id,
        'source': location,
        'image_url': generate_picsum_image(title, external_id),
        'event_url': None,
        'city': location,
        'country': 'Puerto Rico',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'scraped_at': datetime.now()
    }


def insert_event(cursor, evento_data: Dict) -> bool:
    """Inserta evento en MySQL"""
    try:
        sql = '''
            INSERT INTO events (
                id, title, description, start_datetime, end_datetime,
                venue_name, venue_address, latitude, longitude,
                category, subcategory, price, is_free,
                external_id, source, image_url, event_url,
                city, country, created_at, updated_at, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        '''

        cursor.execute(sql, (
            evento_data['id'],
            evento_data['title'],
            evento_data['description'],
            evento_data['start_datetime'],
            evento_data['end_datetime'],
            evento_data['venue_name'],
            evento_data['venue_address'],
            evento_data['latitude'],
            evento_data['longitude'],
            evento_data['category'],
            evento_data['subcategory'],
            evento_data['price'],
            evento_data['is_free'],
            evento_data['external_id'],
            evento_data['source'],
            evento_data['image_url'],
            evento_data['event_url'],
            evento_data['city'],
            evento_data['country'],
            evento_data['created_at'],
            evento_data['updated_at'],
            evento_data['scraped_at']
        ))
        return True
    except pymysql.err.IntegrityError:
        return False
    except Exception as e:
        print(f"Error insertando: {e}")
        return False


def process_json_file(filepath: Path, connection) -> tuple:
    """Procesa un archivo JSON de Puerto Rico"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    location = data.get('location', data.get('ciudad', 'Puerto Rico'))
    country_code = data.get('country_code', 'PR')

    eventos_procesados = 0
    eventos_insertados = 0
    cursor = connection.cursor()

    # Procesar eventos_ferias_festivales
    for evento in data.get('eventos_ferias_festivales', []):
        eventos_procesados += 1
        evento_data = process_evento(evento, location, country_code, eventos_procesados)
        if evento_data and insert_event(cursor, evento_data):
            eventos_insertados += 1

    # Procesar recitales_shows_fiestas
    for evento in data.get('recitales_shows_fiestas', []):
        eventos_procesados += 1
        evento_data = process_evento(evento, location, country_code, eventos_procesados)
        if evento_data and insert_event(cursor, evento_data):
            eventos_insertados += 1

    # Procesar eventos (para puertorico_electronica.json)
    for evento in data.get('eventos', []):
        eventos_procesados += 1
        evento_data = process_evento(evento, location, country_code, eventos_procesados)
        if evento_data and insert_event(cursor, evento_data):
            eventos_insertados += 1

    connection.commit()
    cursor.close()

    return (eventos_procesados, eventos_insertados)


def main():
    """Función principal"""
    print("🇵🇷 Importando eventos de Puerto Rico a MySQL")
    print("="*70)

    # Conectar a MySQL
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        charset='utf8mb4'
    )
    print("✅ Conexión a MySQL establecida\n")

    # Obtener archivos JSON
    pr_path = Path(__file__).parent
    json_files = list(pr_path.glob('*.json'))

    print(f"📁 Encontrados {len(json_files)} archivos JSON\n")

    total_procesados = 0
    total_insertados = 0
    archivos_exitosos = 0

    for i, json_file in enumerate(json_files, 1):
        file_name = json_file.stem
        print(f"[{i}/{len(json_files)}] {file_name:<30}", end=" ")

        try:
            procesados, insertados = process_json_file(json_file, connection)
            total_procesados += procesados
            total_insertados += insertados

            if insertados > 0:
                archivos_exitosos += 1
                print(f"✅ {insertados}/{procesados} eventos")
            else:
                print(f"⚠️  0/{procesados}")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    connection.close()

    # Resumen
    print("\n" + "="*70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*70)
    print(f"📄 Archivos procesados: {len(json_files)}")
    print(f"✅ Con eventos: {archivos_exitosos}")
    print(f"📊 Eventos procesados: {total_procesados}")
    print(f"💾 Eventos insertados: {total_insertados}")

    if total_procesados > 0:
        print(f"📈 Tasa de éxito: {(total_insertados / total_procesados) * 100:.1f}%")


if __name__ == "__main__":
    main()
