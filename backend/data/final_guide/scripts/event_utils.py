#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UTILIDAD: Funciones compartidas para procesamiento de eventos

- categorize_event(): Categoriza eventos basándose en nombre/descripción
- normalize_fecha(): Normaliza fechas a formato YYYY-MM-DD

Usado por: parse_felo.py, parse_gemini.py, auto_import.py, etc.
"""

import sys
import re
from typing import Tuple, Optional

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def categorize_event(nombre: str, descripcion: str = '') -> Tuple[str, str]:
    """
    Categoriza evento basado en nombre y descripción.

    IMPORTANTE: El orden importa! Categorías más específicas primero.

    Args:
        nombre: Nombre del evento
        descripcion: Descripción del evento (opcional)

    Returns:
        Tuple[category, subcategory]

    Categorías disponibles:
        - music: rock, pop, jazz, electronic, folk, classical, other
        - sports: football, basketball, tennis, running, other
        - cultural: theater, museum, exhibition, literature, other
        - nightlife: party, club, bar, other
        - entertainment: comedy, circus, magic, other
        - food: restaurant, festival, market, other
        - tech: conference, hackathon, meetup, other
        - other: general
    """
    nombre_lower = nombre.lower() if nombre else ''
    desc_lower = descripcion.lower() if descripcion else ''
    texto = nombre_lower + ' ' + desc_lower

    # =========================================================================
    # CATEGORÍAS ESPECÍFICAS PRIMERO (más restrictivas)
    # =========================================================================

    # Museos (ANTES de música, porque pueden tener "conciertos")
    if any(word in texto for word in ['museo', 'museos', 'museum']):
        return 'cultural', 'museum'

    # Literatura / Libros (ANTES de nightlife/noche)
    if any(word in texto for word in ['literatura', 'libro', 'librería', 'librerías', 'lectura', 'festival infantil', 'filbita', 'feria del libro']):
        return 'cultural', 'literature'

    # Cine
    if any(word in texto for word in ['cine', 'film', 'película', 'documental', 'proyección', 'festival de cine', 'cinema']):
        return 'cultural', 'cinema'

    # Teatro
    if any(word in texto for word in ['teatro', 'theater', 'theatre', 'obra teatral', 'musical']):
        return 'cultural', 'theater'

    # Deportes
    if any(word in texto for word in ['deporte', 'sport', 'fútbol', 'football', 'futbol', 'futbolera', 'soccer',
                                       'basketball', 'basquet', 'polo', 'tennis', 'tenis', 'running', 'maratón',
                                       'marathon', 'carrera', '5k', '10k', '21k', 'media maratón', 'triatlón']):
        if any(word in texto for word in ['fútbol', 'football', 'futbol', 'soccer']):
            return 'sports', 'football'
        elif any(word in texto for word in ['basketball', 'basquet']):
            return 'sports', 'basketball'
        elif any(word in texto for word in ['tennis', 'tenis']):
            return 'sports', 'tennis'
        elif any(word in texto for word in ['running', 'maratón', 'marathon', 'carrera', '5k', '10k', '21k']):
            return 'sports', 'running'
        else:
            return 'sports', 'other'

    # Nightlife / Bares / Fiestas
    if any(word in texto for word in ['barcrawl', 'recorrido de bares', 'boliche', 'nightclub', 'disco',
                                       'rave', 'afterparty', 'after party']):
        return 'nightlife', 'party'

    # Fiestas temáticas (excluye conciertos y eventos culturales)
    if any(word in texto for word in ['fiesta', 'party', 'noche de']) and not any(word in texto for word in ['concierto', 'banda', 'museo', 'librería']):
        return 'nightlife', 'party'

    # Stand Up / Comedia
    if any(word in texto for word in ['stand up', 'standup', 'comedia', 'comedy', 'humor', 'cómico', 'comico', 'humorista']):
        return 'entertainment', 'comedy'

    # Circo / Magia
    if any(word in texto for word in ['circo', 'circus', 'magia', 'magic', 'ilusionismo']):
        return 'entertainment', 'circus'

    # Gastronomía
    if any(word in texto for word in ['gastronomía', 'gastronomy', 'food', 'gastronómico', 'gastronomico',
                                       'comida', 'restaurante', 'cocina', 'chef', 'degustación',
                                       'food truck', 'feria gastronómica', 'festival gastronómico',
                                       'vino', 'wine', 'cerveza', 'beer', 'cata']):
        return 'food', 'other'

    # Tech / Negocios / Conferencias
    if any(word in texto for word in ['tech', 'tecnología', 'technology', 'hackathon', 'conferencia',
                                       'conference', 'summit', 'pymes', 'negocios', 'networking',
                                       'startup', 'innovación', 'developer', 'programación',
                                       'software', 'ai', 'inteligencia artificial', 'meetup']):
        return 'tech', 'conference'

    # =========================================================================
    # MÚSICA (después de las específicas)
    # =========================================================================
    if any(word in texto for word in ['música', 'music', 'concierto', 'concert', 'dj', 'banda',
                                       'show musical', 'fado', 'peña', 'recital', 'sinfónica',
                                       'orquesta', 'ópera', 'opera', 'festival de música']):
        # Subgéneros de música
        if any(word in texto for word in ['rock', 'punk', 'metal', 'hardcore']):
            return 'music', 'rock'
        elif any(word in texto for word in ['pop', 'k-pop', 'kpop']):
            return 'music', 'pop'
        elif any(word in texto for word in ['jazz', 'blues', 'soul']):
            return 'music', 'jazz'
        elif any(word in texto for word in ['electrónica', 'electronica', 'electronic', 'dj', 'techno',
                                            'house', 'trance', 'edm', 'rave']):
            return 'music', 'electronic'
        elif any(word in texto for word in ['fado', 'folclore', 'folklore', 'peña', 'tango',
                                            'flamenco', 'cumbia', 'salsa', 'reggaeton']):
            return 'music', 'folk'
        elif any(word in texto for word in ['clásica', 'clasica', 'classical', 'sinfónica', 'sinfonica',
                                            'orquesta', 'ópera', 'opera', 'piano', 'orquestal']):
            return 'music', 'classical'
        elif any(word in texto for word in ['hip hop', 'hiphop', 'rap', 'trap', 'reggae']):
            return 'music', 'hiphop'
        else:
            return 'music', 'other'

    # =========================================================================
    # CULTURAL / ARTE (DESPUÉS de específicos)
    # =========================================================================
    if any(word in texto for word in ['cultural', 'cultura', 'arte', 'art', 'exposición', 'exhibition',
                                       'galería', 'gallery', 'feria', 'visita guiada', 'tour',
                                       'orgullo', 'diversidad', 'lgbt', 'pride', 'patrimonio',
                                       'artesanía', 'artesanal', 'mercado navideño', 'navidad']):
        return 'cultural', 'other'

    # =========================================================================
    # DEFAULT
    # =========================================================================
    return 'other', 'general'


def normalize_fecha(fecha_str: str) -> Optional[str]:
    """
    Normaliza fechas a YYYY-MM-DD

    Formatos soportados:
    - "8 noviembre 2025"
    - "8 de noviembre 2025"
    - "8 de noviembre de 2025"
    - "Sábado 8 de noviembre"
    - "Del 7 al 9 de noviembre"
    - "29 octubre - 2 noviembre 2025"
    - "13-16 noviembre 2025"
    - "2025-11-08" (ya normalizado)

    Args:
        fecha_str: String con la fecha en cualquier formato

    Returns:
        Fecha en formato YYYY-MM-DD o None si no se puede parsear
    """
    if not fecha_str:
        return None

    fecha_str = str(fecha_str).strip()

    # Si ya está en formato ISO, retornar
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
        return fecha_str

    fecha_lower = fecha_str.lower()

    # Mapeo de meses en español
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }

    # Buscar año (si está presente)
    year_match = re.search(r'(\d{4})', fecha_str)
    year = year_match.group(1) if year_match else '2025'

    # Formato: "8 noviembre 2025" o "8 noviembre" (sin "de")
    match_directo = re.search(r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', fecha_lower)
    if match_directo:
        dia = match_directo.group(1).zfill(2)
        mes_nombre = match_directo.group(2)
        mes_num = meses.get(mes_nombre, '11')
        return f"{year}-{mes_num}-{dia}"

    # Formato: "Del X al Y de mes" o "X-Y de mes"
    match_rango = re.search(r'(?:del\s+)?(\d+)(?:\s*[-–]\s*|\s+al\s+)(\d+)\s+(?:de\s+)?(\w+)', fecha_lower)
    if match_rango:
        dia_inicio = match_rango.group(1).zfill(2)
        mes_nombre = match_rango.group(3)
        mes_num = meses.get(mes_nombre, '11')
        return f"{year}-{mes_num}-{dia_inicio}"

    # Formato: "8 de noviembre" o "8 de noviembre de 2025"
    match_con_de = re.search(r'(\d{1,2})\s+de\s+(\w+)', fecha_lower)
    if match_con_de:
        dia = match_con_de.group(1).zfill(2)
        mes_nombre = match_con_de.group(2)
        mes_num = meses.get(mes_nombre, '11')
        return f"{year}-{mes_num}-{dia}"

    # Si solo tiene mes (ej: "Hasta diciembre 2025")
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in fecha_lower:
            return f"{year}-{mes_num}-01"

    # No se pudo parsear
    return None


# =============================================================================
# TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("TEST: event_utils.py - Categorización de eventos")
    print("=" * 70)

    test_events = [
        ("The Offspring", "Concierto de la banda de punk rock californiana"),
        ("Lady Gaga", "Conciertos de la estrella del pop"),
        ("Mumford & Sons", "Presentación de su nuevo álbum"),
        ("Hans Zimmer", "Concierto orquestal con sus bandas sonoras"),
        ("HAVASI", "Espectáculo de piano y composición contemporánea"),
        ("SC21K", "Media maratón que incluye distancias de 5 km, 10 km, y 21 km"),
        ("Agora É Que São Elas!", "Comedia dirigida por Fábio Porchat"),
        ("TUM Festival 2025", "Festival de música y conferencias"),
        ("Mystara Festival", "Festival de música electrónica y arte"),
        ("Torresmofest", "Festival gastronómico con música"),
        ("Organïk XXL Techno Rave", "Noche de música techno"),
        ("Navidad en Disneyland", "Inicio de las celebraciones navideñas"),
        ("Salon du Chocolat", "Feria dedicada al chocolate"),
        ("Paris Photo", "Feria de fotografía contemporánea"),
    ]

    print("\nResultados de categorización:")
    print("-" * 70)
    for nombre, desc in test_events:
        cat, subcat = categorize_event(nombre, desc)
        print(f"  {nombre[:30]:30} | {cat:12} | {subcat}")

    print("\n" + "=" * 70)
    print("TEST: Normalización de fechas")
    print("=" * 70)

    test_fechas = [
        "8 noviembre 2025",
        "8 de noviembre de 2025",
        "Del 7 al 9 de noviembre",
        "20-22 de noviembre de 2025",
        "Sábado 15 de noviembre",
        "2025-11-23",
        "Hasta diciembre 2025",
    ]

    print("\nResultados:")
    for fecha in test_fechas:
        norm = normalize_fecha(fecha)
        print(f"  {fecha:35} -> {norm}")
