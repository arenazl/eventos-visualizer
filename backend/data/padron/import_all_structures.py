"""
Script universal para importar eventos de TODOS los barrios a MySQL
Maneja las 38+ estructuras diferentes de JSON
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple, List
import hashlib
import random
import uuid

# Configurar codificación para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Import pymysql for MySQL
try:
    import pymysql
except ImportError:
    print("ERROR pymysql no instalado")
    sys.exit(1)

# Coordenadas de barrios
BARRIO_COORDS = {
    "agronomia": (-34.5996, -58.4866), "almagro": (-34.6092, -58.4195),
    "balvanera": (-34.6098, -58.3968), "barracas": (-34.6432, -58.3736),
    "belgrano": (-34.5628, -58.4573), "boedo": (-34.6332, -58.4173),
    "caballito": (-34.6176, -58.4368), "chacarita": (-34.5891, -58.4510),
    "coghlan": (-34.5588, -58.4778), "colegiales": (-34.5749, -58.4467),
    "constitucion": (-34.6274, -58.3817), "flores": (-34.6281, -58.4657),
    "floresta": (-34.6286, -58.4838), "la-boca": (-34.6345, -58.3632),
    "laboca": (-34.6345, -58.3632), "la-paternal": (-34.5995, -58.4716),
    "lapaternal": (-34.5995, -58.4716), "liniers": (-34.6432, -58.5218),
    "mataderos": (-34.6592, -58.5018), "monte-castro": (-34.6181, -58.5036),
    "montecastro": (-34.6181, -58.5036), "montserrat": (-34.6102, -58.3745),
    "nueva-pompeya": (-34.6596, -58.4194), "nuevapompeya": (-34.6596, -58.4194),
    "nunez": (-34.5442, -58.4632), "palermo": (-34.5888, -58.4199),
    "parque-avellaneda": (-34.6462, -58.4815), "parqueavellaneda": (-34.6462, -58.4815),
    "parque-chacabuco": (-34.6389, -58.4415), "parquechacabuco": (-34.6389, -58.4415),
    "parque-chas": (-34.5767, -58.4817), "parque-patricios": (-34.6382, -58.3996),
    "puerto-madero": (-34.6118, -58.3636), "recoleta": (-34.5889, -58.3937),
    "retiro": (-34.5925, -58.3747), "saavedra": (-34.5487, -58.4848),
    "san-cristobal": (-34.6228, -58.3992), "san-nicolas": (-34.6032, -58.3748),
    "san-telmo": (-34.6214, -58.3724), "velez-sarsfield": (-34.6338, -58.4997),
    "versalles": (-34.6257, -58.5247), "villa-crespo": (-34.5999, -58.4386),
    "villa-del-parque": (-34.6047, -58.4912), "villa-devoto": (-34.6014, -58.5153),
    "villa-general-mitre": (-34.5921, -58.4744), "villa-lugano": (-34.6880, -58.4702),
    "villa-luro": (-34.6388, -58.5018), "villa-ortuzar": (-34.5784, -58.4663),
    "villa-pueyrredon": (-34.5869, -58.5019), "villa-real": (-34.6181, -58.5128),
    "villa-riachuelo": (-34.6964, -58.4547), "villa-santa-rita": (-34.6147, -58.4814),
    "villa-soldati": (-34.6647, -58.4489), "villa-urquiza": (-34.5722, -58.4843),
}

CATEGORY_MAPPING = {
    "gastronomia": "food", "gastronomia-cultural": "food",
    "tecnologia": "tech", "tech": "tech",
    "cine": "film", "teatro": "theater", "teatro-show": "theater",
    "rock": "music", "musica": "music", "electronica": "music",
    "cultural": "cultural", "cultural-religioso": "cultural",
    "deportes": "sports", "deportes-cultura": "sports",
    "festival": "festival", "arte": "art", "fiesta": "party",
    "feria": "festival", "artesanias": "art",
}

# Keys a ignorar (no son eventos)
SKIP_KEYS = {
    'notas', 'notas_importantes', 'sugerencias', 'sugerencias_adicionales',
    'lugares_interes', 'lugares_destacados', 'lugares_permanentes',
    'iconos_turisticos', 'caracteristicas'
}


def normalize_barrio_name(nombre: str) -> str:
    """Normaliza nombre de barrio"""
    return nombre.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def get_barrio_coordinates(barrio: str) -> Tuple[float, float]:
    """Obtiene coordenadas del barrio"""
    normalized = normalize_barrio_name(barrio)
    coords = BARRIO_COORDS.get(normalized, (-34.6037, -58.3816))
    lat, lng = coords
    lat += random.uniform(-0.005, 0.005)
    lng += random.uniform(-0.005, 0.005)
    return (round(lat, 6), round(lng, 6))


def normalize_category(categoria: str) -> str:
    """Normaliza categoría"""
    if not categoria:
        return "other"
    return CATEGORY_MAPPING.get(categoria.lower().strip(), "other")


def parse_fecha_text(fecha_text: str, year: int = 2025, month: int = 11) -> Optional[datetime]:
    """Parsea texto de fecha a datetime"""
    if not fecha_text:
        return None

    fecha_text = str(fecha_text).strip()

    # Formato YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_text):
        try:
            return datetime.strptime(fecha_text, '%Y-%m-%d')
        except:
            return None

    # Extraer día
    match = re.search(r'\b(\d{1,2})\b', fecha_text)
    if match:
        day = int(match.group(1))
        if 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    return None


def normalize_precio(precio_text: str) -> Tuple[str, bool]:
    """Normaliza precio a (texto, is_free)"""
    if not precio_text:
        return ("gratuito", True)

    precio_lower = str(precio_text).lower().strip()

    if precio_lower in ["gratuito", "gratis", "free", "libre"]:
        return ("gratuito", True)

    if precio_lower in ["pago", "variable", "consultar"]:
        return ("a consultar", False)

    match = re.search(r'\$?\s*(\d+(?:\.\d+)?)', precio_text)
    if match:
        try:
            valor = float(match.group(1))
            if valor == 0:
                return ("gratuito", True)
            else:
                return (f"${int(valor)}", False)
        except:
            pass

    return ("a consultar", False)


def generate_picsum_image(event_id: str) -> str:
    """Genera URL de imagen"""
    hash_num = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
    img_id = (hash_num % 1000) + 1
    return f"https://picsum.photos/id/{img_id}/800/600"


def clean_venue_name(venue: str) -> str:
    """Limpia nombre del venue"""
    if not venue:
        return "Lugar a confirmar"
    venue = venue.strip()
    if "(" in venue:
        parts = venue.split("(")
        return parts[0].strip()
    return venue[:255]


def extract_all_event_arrays(data: dict, parent_key: str = "") -> List[Tuple[str, List]]:
    """
    Extrae recursivamente todos los arrays que podrían ser eventos
    Ignora arrays de notas, lugares de interés, etc.

    Returns: [(key_path, array), ...]
    """
    result = []

    for key, value in data.items():
        # Saltar keys que no son eventos
        if key in SKIP_KEYS:
            continue

        current_path = f"{parent_key}.{key}" if parent_key else key

        if isinstance(value, list) and len(value) > 0:
            # Verificar si parece un array de eventos
            first_item = value[0]
            if isinstance(first_item, dict):
                # Tiene campos típicos de eventos?
                event_fields = {'nombre', 'titulo', 'title', 'fecha', 'date', 'lugar', 'place'}
                if any(field in first_item for field in event_fields):
                    result.append((current_path, value))

        elif isinstance(value, dict):
            # Recursivamente buscar en objetos anidados
            nested = extract_all_event_arrays(value, current_path)
            result.extend(nested)

    return result


def normalize_event_dict(evento: dict, barrio: str) -> Optional[dict]:
    """
    Normaliza un diccionario de evento independientemente de su estructura original

    Retorna dict con campos estandarizados o None si no es válido
    """
    # Intentar extraer título
    titulo = (
        evento.get('nombre') or
        evento.get('titulo') or
        evento.get('title') or
        evento.get('event_name') or
        'Evento sin título'
    )[:255]

    # Extraer descripción
    descripcion = (
        evento.get('descripcion') or
        evento.get('description') or
        evento.get('desc') or
        ''
    )

    # Extraer fecha
    fecha_text = (
        evento.get('fecha') or
        evento.get('date') or
        evento.get('fecha_inicio') or
        ''
    )

    start_datetime = parse_fecha_text(fecha_text)
    if not start_datetime:
        return None  # Sin fecha válida, skip

    # Agregar hora si existe
    hora = (
        evento.get('hora_inicio') or
        evento.get('hora') or
        evento.get('horario') or
        evento.get('time') or
        '00:00'
    )

    if hora and ':' in str(hora):
        try:
            parts = str(hora).replace('hs', '').replace('h', '').strip().split(':')[:2]
            if len(parts) >= 2:
                hora_num, minuto_num = int(parts[0]), int(parts[1])
                start_datetime = start_datetime.replace(hour=hora_num, minute=minuto_num)
        except:
            pass

    # End datetime
    end_datetime = None
    hora_fin = evento.get('hora_fin')
    if hora_fin and ':' in str(hora_fin):
        try:
            parts = str(hora_fin).split(':')[:2]
            if len(parts) >= 2:
                end_datetime = start_datetime.replace(hour=int(parts[0]), minute=int(parts[1]))
        except:
            pass

    # Lugar
    lugar = (
        evento.get('lugar') or
        evento.get('venue') or
        evento.get('venue_name') or
        evento.get('direccion') or
        barrio
    )

    venue_name = clean_venue_name(lugar)
    venue_address = lugar

    # Categoría
    categoria_raw = (
        evento.get('categoria') or
        evento.get('category') or
        evento.get('tipo') or
        'other'
    )
    category = normalize_category(categoria_raw)
    subcategory = categoria_raw if category != categoria_raw else None

    # Precio
    precio_raw = evento.get('precio') or evento.get('price') or 'a consultar'
    price, is_free = normalize_precio(precio_raw)

    return {
        'title': titulo,
        'description': descripcion[:5000] if descripcion else None,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'category': category,
        'subcategory': subcategory,
        'price': price,
        'is_free': is_free
    }


def insert_event(cursor, evento_data: Dict) -> bool:
    """Inserta evento en MySQL"""
    try:
        event_id = str(uuid.uuid4())

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
            event_id, evento_data['title'], evento_data['description'],
            evento_data['start_datetime'], evento_data['end_datetime'],
            evento_data['venue_name'], evento_data['venue_address'],
            evento_data['latitude'], evento_data['longitude'],
            evento_data['category'], evento_data['subcategory'],
            evento_data['price'], evento_data['is_free'],
            evento_data['external_id'], evento_data['source'],
            evento_data['image_url'], evento_data['event_url'],
            evento_data['city'], evento_data['country'],
            datetime.now(), datetime.now(), datetime.now()
        ))
        return True
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:  # Duplicate
            return False
        return False
    except Exception as e:
        return False


def process_json_file(filepath: Path, connection) -> Tuple[int, int]:
    """Procesa un archivo JSON con cualquier estructura"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    barrio = data.get('barrio', 'Unknown')
    mes = data.get('mes', 'noviembre')
    año = data.get('año', 2025)

    lat_base, lng_base = get_barrio_coordinates(barrio)

    eventos_procesados = 0
    eventos_insertados = 0

    cursor = connection.cursor()

    # Extraer todos los arrays de eventos
    event_arrays = extract_all_event_arrays(data)

    for array_path, eventos in event_arrays:
        for evento in eventos:
            eventos_procesados += 1

            # Normalizar evento
            normalized = normalize_event_dict(evento, barrio)
            if not normalized:
                continue

            # Coordenadas
            latitude = lat_base + random.uniform(-0.003, 0.003)
            longitude = lng_base + random.uniform(-0.003, 0.003)

            # External ID
            external_id = f"padron_{normalize_barrio_name(barrio)}_{mes}_{eventos_procesados}"

            # Preparar datos finales
            # Convertir barrio a formato bonito: "palermo" -> "Palermo", "san-telmo" -> "San Telmo"
            barrio_source = barrio.replace('-', ' ').title()

            evento_data = {
                **normalized,
                'latitude': round(latitude, 8),
                'longitude': round(longitude, 8),
                'external_id': external_id,
                'source': barrio_source,
                'image_url': generate_picsum_image(external_id),
                'event_url': None,
                'city': 'Buenos Aires',
                'country': 'Argentina'
            }

            # Insertar
            if insert_event(cursor, evento_data):
                eventos_insertados += 1

    connection.commit()
    cursor.close()

    return (eventos_procesados, eventos_insertados)


def main():
    """Función principal"""
    print("Importacion universal de eventos a MySQL")
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
    print("OK Conexion a MySQL\n")

    # Procesar archivos
    padron_path = Path(__file__).parent
    json_files = sorted(padron_path.glob('*_noviembre.json'))

    print(f"Procesando {len(json_files)} archivos...\n")

    total_procesados = 0
    total_insertados = 0
    archivos_exitosos = 0

    for i, json_file in enumerate(json_files, 1):
        barrio_name = json_file.stem.replace('_noviembre', '').replace('-', ' ').title()
        print(f"[{i}/{len(json_files)}] {barrio_name:<25}", end=" ")

        try:
            procesados, insertados = process_json_file(json_file, connection)
            total_procesados += procesados
            total_insertados += insertados

            if insertados > 0:
                archivos_exitosos += 1
                print(f"OK {insertados}/{procesados} eventos")
            else:
                print(f"SKIP 0/{procesados}")

        except Exception as e:
            print(f"ERROR: {e}")

    connection.close()

    # Resumen
    print("\n" + "="*70)
    print("COMPLETADO")
    print("="*70)
    print(f"Archivos: {len(json_files)}")
    print(f"Con eventos: {archivos_exitosos}")
    print(f"Procesados: {total_procesados}")
    print(f"Insertados: {total_insertados}")

    if total_procesados > 0:
        print(f"Tasa exito: {(total_insertados / total_procesados) * 100:.1f}%")


if __name__ == "__main__":
    main()
