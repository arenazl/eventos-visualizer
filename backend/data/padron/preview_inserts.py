"""
Script para PREVIEW de INSERT statements sin ejecutarlos
Muestra cómo se verían los datos antes de insertarlos en la BD
"""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Configuración
BARRIOS_DIR = Path(__file__).parent
IMAGE_BASE_URL = "https://picsum.photos/800/600"
CURRENT_YEAR = 2025

def normalize_date(fecha_str: str, mes: str = "noviembre", año: int = CURRENT_YEAR) -> Optional[str]:
    """
    Normaliza fechas en diferentes formatos a YYYY-MM-DD

    Ejemplos:
    - "2025-11-09" → "2025-11-09"
    - "Jueves 13 de Noviembre" → "2025-11-13"
    - "Sábado 15 y Domingo 16" → "2025-11-15" (toma el primero)
    - "Todos los Domingos" → None (evento recurrente)
    - "Hasta el Sábado 15" → "2025-11-15"
    """
    if not fecha_str:
        return None

    # Ya está en formato ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
        return fecha_str

    # "Todos los X" → recurrente, retornamos None
    if "Todos los" in fecha_str or "Diario" in fecha_str:
        return None

    # Mapeo de meses en español
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }

    # Extraer números del 1-31 (días del mes)
    dias = re.findall(r'\b([1-9]|[12]\d|3[01])\b', fecha_str)
    if dias:
        dia = int(dias[0])  # Tomar el primer día encontrado
        mes_num = meses_map.get(mes.lower(), 11)  # Default noviembre
        return f"{año}-{mes_num:02d}-{dia:02d}"

    return None

def normalize_time(hora_str: Optional[str]) -> Optional[str]:
    """
    Normaliza horas a formato HH:MM
    """
    if not hora_str:
        return None

    # Ya está en formato HH:MM
    if re.match(r'^\d{1,2}:\d{2}$', hora_str):
        return hora_str

    # Extraer HH:MM
    match = re.search(r'(\d{1,2}):(\d{2})', hora_str)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"

    return None

def normalize_category(categoria: Optional[str]) -> str:
    """
    Normaliza categorías a valores estándar
    """
    if not categoria:
        return "otros"

    categoria = categoria.lower()

    mapping = {
        "gastronomia": "gastronomia",
        "cultural": "cultural",
        "musica": "musica",
        "rock": "musica",
        "cine": "cine",
        "deportes": "deportes",
        "tecnologia": "tecnologia",
        "feria": "ferias",
        "artesanias": "ferias",
        "teatro": "teatro"
    }

    for key, value in mapping.items():
        if key in categoria:
            return value

    return "otros"

def extract_price(precio_str: Optional[str]) -> tuple[Optional[float], bool]:
    """
    Extrae precio numérico y determina si es gratis
    Retorna: (precio, is_free)
    """
    if not precio_str:
        return (None, False)

    precio_str = precio_str.lower()

    if "gratis" in precio_str or "gratuito" in precio_str:
        return (0.0, True)

    # Buscar números
    match = re.search(r'(\d+(?:\.\d+)?)', precio_str)
    if match:
        return (float(match.group(1)), False)

    if "pago" in precio_str or "variable" in precio_str:
        return (None, False)

    return (None, False)

def get_random_image(event_id: int, category: str) -> str:
    """
    Genera URL de imagen de Picsum basada en evento y categoría
    """
    # Usar seed para tener imágenes consistentes
    seed = abs(hash(f"{event_id}_{category}")) % 1000
    return f"{IMAGE_BASE_URL}?random={seed}"

def process_json_file(json_path: Path) -> list[Dict[str, Any]]:
    """
    Procesa un archivo JSON y extrae eventos normalizados
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    barrio = data.get("barrio", "Desconocido")
    mes = data.get("mes", "noviembre")
    año = data.get("año", CURRENT_YEAR)

    eventos = []
    event_id = 0

    # Procesar eventos/ferias/festivales
    for evento in data.get("eventos_ferias_festivales", []):
        event_id += 1
        eventos.append(normalize_event(evento, barrio, mes, año, event_id))

    # Procesar recitales/shows
    for evento in data.get("recitales_shows_fiestas", []):
        event_id += 1
        eventos.append(normalize_event(evento, barrio, mes, año, event_id))

    # Procesar eventos del Centro Cultural Recoleta
    if "centro_cultural_recoleta" in data:
        for evento in data["centro_cultural_recoleta"].get("eventos", []):
            event_id += 1
            eventos.append(normalize_event(evento, barrio, mes, año, event_id, venue_default="Centro Cultural Recoleta"))

    # Procesar eventos generales
    for evento in data.get("eventos", []):
        event_id += 1
        eventos.append(normalize_event(evento, barrio, mes, año, event_id))

    return eventos

def normalize_event(evento: Dict[str, Any], barrio: str, mes: str, año: int, event_id: int, venue_default: str = None) -> Dict[str, Any]:
    """
    Normaliza un evento individual
    """
    # Extraer campos
    nombre = evento.get("nombre") or evento.get("titulo", "Sin título")
    nombre = nombre.replace("**", "").strip()  # Limpiar markdown

    fecha_str = evento.get("fecha")
    fecha = normalize_date(fecha_str, mes, año)

    hora_inicio = normalize_time(evento.get("hora_inicio") or evento.get("hora") or evento.get("horario"))
    hora_fin = normalize_time(evento.get("hora_fin"))

    lugar = evento.get("lugar") or venue_default or f"{barrio}, Buenos Aires"
    descripcion = evento.get("descripcion", "")
    categoria = normalize_category(evento.get("categoria") or evento.get("tipo"))

    precio_str = evento.get("precio")
    precio, is_free = extract_price(precio_str)

    # Generar imagen
    image_url = get_random_image(event_id, categoria)

    # Geocoding básico (placeholder - en producción usar Google Maps API)
    # Por ahora asumimos coordenadas de Buenos Aires por barrio
    lat, lng = -34.6037, -58.3816  # Centro de CABA por defecto

    return {
        "title": nombre,
        "description": descripcion,
        "start_date": fecha,
        "start_time": hora_inicio,
        "end_time": hora_fin,
        "venue_name": lugar,
        "venue_address": evento.get("direccion", lugar),
        "latitude": lat,
        "longitude": lng,
        "category": categoria,
        "price": precio,
        "is_free": is_free,
        "image_url": image_url,
        "source": f"Gemini AI - Padrón {barrio}",
        "barrio": barrio,
        "fecha_original": fecha_str  # Guardar original para debug
    }

def generate_insert_statement(evento: Dict[str, Any]) -> str:
    """
    Genera un INSERT statement SQL
    """
    # Escapar comillas simples
    def escape_sql(value):
        if value is None:
            return "NULL"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return f"'{str(value).replace(chr(39), chr(39)+chr(39))}'"  # Escapar comillas simples

    fields = [
        "title", "description", "start_date", "start_time", "end_time",
        "venue_name", "venue_address", "latitude", "longitude",
        "category", "price", "is_free", "image_url", "source"
    ]

    values = [escape_sql(evento.get(field)) for field in fields]

    sql = f"""INSERT INTO events ({', '.join(fields)})
VALUES ({', '.join(values)});"""

    return sql

def preview_barrio(json_path: Path, max_events: int = 5):
    """
    Preview de eventos de un barrio
    """
    print(f"\n{'='*80}")
    print(f"BARRIO: {json_path.stem.replace('_noviembre', '').replace('-', ' ').upper()}")
    print(f"{'='*80}\n")

    eventos = process_json_file(json_path)

    if not eventos:
        print("No se encontraron eventos validos en este archivo")
        return

    print(f"Eventos encontrados: {len(eventos)}")
    print(f"Mostrando primeros {min(max_events, len(eventos))} eventos:\n")

    for i, evento in enumerate(eventos[:max_events], 1):
        print(f"--- Evento {i} ---")
        print(f"Titulo: {evento['title']}")
        print(f"Fecha: {evento['start_date'] or 'RECURRENTE/SIN FECHA'}")
        print(f"Hora: {evento['start_time'] or 'No especificada'}")
        print(f"Lugar: {evento['venue_name']}")
        print(f"Categoria: {evento['category']}")
        print(f"Precio: {'GRATIS' if evento['is_free'] else (f'${evento["price"]}' if evento['price'] else 'Consultar')}")
        print(f"Imagen: {evento['image_url']}")
        print()

        # Mostrar INSERT SQL
        sql = generate_insert_statement(evento)
        print("SQL INSERT:")
        print(sql)
        print()

    if len(eventos) > max_events:
        print(f"... y {len(eventos) - max_events} eventos mas\n")

    # Resumen
    eventos_con_fecha = [e for e in eventos if e['start_date']]
    eventos_gratis = [e for e in eventos if e['is_free']]

    print(f"RESUMEN:")
    print(f"   Total eventos: {len(eventos)}")
    print(f"   Con fecha especifica: {len(eventos_con_fecha)}")
    print(f"   Eventos recurrentes/sin fecha: {len(eventos) - len(eventos_con_fecha)}")
    print(f"   Eventos gratuitos: {len(eventos_gratis)}")
    print(f"   Categorias: {', '.join(set(e['category'] for e in eventos))}")

def main():
    """
    Preview de INSERT statements de todos los barrios
    """
    print("\n" + "="*80)
    print("PREVIEW DE INSERT STATEMENTS - PADRON DE EVENTOS")
    print("="*80)

    # Buscar todos los JSON
    json_files = list(BARRIOS_DIR.glob("*_noviembre.json"))

    print(f"\nArchivos JSON encontrados: {len(json_files)}")

    # Preview de 3 barrios como ejemplo
    barrios_ejemplo = ["palermo", "recoleta", "san-telmo"]

    for barrio in barrios_ejemplo:
        json_file = next((f for f in json_files if barrio in f.stem), None)
        if json_file:
            preview_barrio(json_file, max_events=3)

    print("\n" + "="*80)
    print("PREVIEW COMPLETADO")
    print("="*80)
    print("\nPara ejecutar los INSERT reales, usa: python import_to_database.py")

if __name__ == "__main__":
    main()
