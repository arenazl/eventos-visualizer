"""
🗄️ EVENTS DB SERVICE - Consultas rápidas a MySQL Aiven
Busca eventos en la base de datos por ubicación
"""
import logging
import os
import unicodedata
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Conexión a MySQL Aiven
DB_URL = os.getenv('DATABASE_URL')
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def remove_accents(text: str) -> str:
    """
    Elimina acentos y normaliza texto para búsquedas insensibles a acentos
    Bogotá -> Bogota, São Paulo -> Sao Paulo, etc.
    """
    if not text:
        return text

    # Normalizar usando NFD (Canonical Decomposition)
    # Esto separa caracteres acentuados en base + acento
    nfd = unicodedata.normalize('NFD', text)

    # Filtrar solo caracteres que NO sean diacríticos (acentos)
    without_accents = ''.join(
        char for char in nfd
        if unicodedata.category(char) != 'Mn'  # Mn = Nonspacing Mark (acentos)
    )

    return without_accents


async def search_events_by_location(
    location: str,
    category: Optional[str] = None,
    limit: int = 100,
    days_ahead: int = 90,
    include_parent_city: bool = True
) -> List[Dict[str, Any]]:
    """
     BUSCAR EVENTOS POR UBICACIÓN EN MYSQL

    Args:
        location: Ciudad, provincia o país (ej: "Buenos Aires", "Argentina", "Buenos Aires, Argentina")
        category: Categoría opcional (Musica, Cultural, etc.)
        limit: Límite de eventos (default: 100)
        days_ahead: Días hacia adelante (default: 90)
        include_parent_city: Si es True, detecta ciudad principal y busca también allí (default: True)

    Returns:
        Lista de eventos desde MySQL Aiven
    """

    session = SessionLocal()

    try:
        # Extraer ubicación (puede venir como "Buenos Aires, Argentina" o solo "Brasil")
        search_location = location.split(',')[0].strip()

        # 🏙️ Detectar ciudad principal si está habilitado
        parent_city = None
        if include_parent_city:
            try:
                from services.gemini_factory import gemini_factory
                parent_city = await gemini_factory.get_parent_location(search_location)
                if parent_city:
                    logger.info(f"🏙️ Detectada ciudad principal para '{search_location}': {parent_city}")
            except Exception as e:
                logger.warning(f"⚠️ Error detectando ciudad principal: {e}")

        logger.info(f" Buscando eventos en MySQL para ubicación: '{search_location}'")

        # Normalizar búsqueda (eliminar acentos para búsqueda insensible)
        search_normalized = remove_accents(search_location)
        logger.info(f"🔄 Búsqueda normalizada (sin acentos): '{search_normalized}'")

        # Normalizar ciudad principal si existe
        parent_normalized = remove_accents(parent_city) if parent_city else None

        # Rango de fechas
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        # Query SQL con filtros - buscar en city, venue_address Y country
        # Usa REPLACE para eliminar acentos comunes en SQL también
        # Si hay ciudad principal, buscar TAMBIÉN en esa ciudad
        query = """
        SELECT
            id, title, description, event_url, image_url,
            venue_name, venue_address, city, category,
            start_datetime, end_datetime, price
        FROM events
        WHERE
            (
                city LIKE :location_pattern
                OR venue_address LIKE :location_pattern
                OR country LIKE :location_pattern
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(city, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :location_normalized
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(venue_address, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :location_normalized
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(country, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :location_normalized
        """

        params = {
            'location_pattern': f'%{search_location}%',
            'location_normalized': f'%{search_normalized}%',
            'now': now,
            'end_date': end_date
        }

        # Agregar búsqueda por ciudad principal si existe
        if parent_city and parent_normalized:
            query += """
                OR city LIKE :parent_pattern
                OR venue_address LIKE :parent_pattern
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(city, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :parent_normalized
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(venue_address, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :parent_normalized
            """
            params['parent_pattern'] = f'%{parent_city}%'
            params['parent_normalized'] = f'%{parent_normalized}%'
            logger.info(f"🔍 También buscando eventos en ciudad principal: {parent_city}")

        # Cerrar el WHERE
        query += """
            )
            AND start_datetime >= :now
            AND start_datetime <= :end_date
        """

        # Agregar filtro de categoría si existe
        if category and category.lower() != 'todas':
            query += " AND category LIKE :category"
            params['category'] = f'%{category}%'

        # Ordenar por fecha y limitar
        query += " ORDER BY start_datetime ASC LIMIT :limit"
        params['limit'] = limit

        # Ejecutar query
        result = session.execute(text(query), params)
        rows = result.fetchall()

        # Convertir a diccionarios
        events = []
        for row in rows:
            # Convertir precio a float, si falla usar 0.0
            try:
                price = float(row[11]) if row[11] else 0.0
            except (ValueError, TypeError):
                price = 0.0

            event = {
                'id': str(row[0]),
                'title': row[1],
                'description': row[2] or '',
                'url': row[3] or '',
                'image_url': row[4] or '',
                'venue_name': row[5] or '',
                'venue_address': row[6] or '',
                'city': row[7] or '',
                'category': row[8] or 'General',
                'start_datetime': row[9].isoformat() if row[9] else None,
                'end_datetime': row[10].isoformat() if row[10] else None,
                'price': price,
                'source': 'database'
            }
            events.append(event)

        if parent_city:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}' y '{parent_city}'")
        else:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}'")

        return events

    except Exception as e:
        logger.error(f"ERROR Error consultando MySQL: {e}")
        return []

    finally:
        session.close()


async def get_available_cities(limit: int = 10) -> List[Dict[str, Any]]:
    """
     OBTENER CIUDADES DISPONIBLES CON EVENTOS

    Returns:
        Lista de ciudades con cantidad de eventos
    """
    session = SessionLocal()

    try:
        logger.info(f" Obteniendo ciudades disponibles en MySQL")

        # Query para contar eventos por ciudad
        query = """
        SELECT
            city,
            COUNT(*) as event_count
        FROM events
        WHERE start_datetime >= :now
        GROUP BY city
        ORDER BY event_count DESC
        LIMIT :limit
        """

        from datetime import datetime
        params = {
            'now': datetime.utcnow(),
            'limit': limit
        }

        result = session.execute(text(query), params)
        rows = result.fetchall()

        cities = []
        for row in rows:
            cities.append({
                'city': row[0],
                'event_count': row[1]
            })

        logger.info(f"OK Encontradas {len(cities)} ciudades con eventos en MySQL")

        return cities

    except Exception as e:
        logger.error(f"ERROR Error obteniendo ciudades: {e}")
        return []

    finally:
        session.close()


async def get_available_cities_with_events(search_query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
     BUSCAR UBICACIONES CON EVENTOS (Ciudades, Provincias, Países)

    Retorna ubicaciones que coincidan con la búsqueda y tengan eventos activos.
    Busca en múltiples niveles geográficos: ciudades, provincias, países.
    Optimizado para autocomplete.

    Args:
        search_query: Texto de búsqueda (mínimo 2 caracteres)
        limit: Límite de resultados (default: 10)

    Returns:
        Lista de ubicaciones con:
        - location: Nombre de la ubicación
        - location_type: 'city', 'province', 'country'
        - event_count: Cantidad de eventos
        - displayName: Nombre formateado para mostrar
    """
    session = SessionLocal()

    try:
        logger.info(f" Buscando ubicaciones con eventos que contengan: '{search_query}'")

        # Normalizar búsqueda (eliminar acentos)
        search_normalized = remove_accents(search_query)
        logger.info(f"🔄 Búsqueda normalizada (sin acentos): '{search_normalized}'")

        # Query para buscar en city y venue_address (insensible a acentos)
        query = """
        SELECT
            city,
            venue_address,
            COUNT(*) as event_count
        FROM events
        WHERE
            start_datetime >= :now
            AND (
                city LIKE :search_pattern
                OR venue_address LIKE :search_pattern
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(city, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :search_normalized
                OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(venue_address, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') LIKE :search_normalized
            )
        GROUP BY city, venue_address
        ORDER BY event_count DESC
        """

        params = {
            'now': datetime.utcnow(),
            'search_pattern': f'%{search_query}%',
            'search_normalized': f'%{search_normalized}%'
        }

        result = session.execute(text(query), params)
        rows = result.fetchall()

        # Procesar resultados para extraer diferentes niveles geográficos
        locations_map = {}  # key: location_name, value: {type, count}

        for row in rows:
            city = row[0] or ''
            venue_address = row[1] or ''
            count = row[2]

            # 1. Agregar ciudad si coincide (insensible a acentos)
            if remove_accents(search_query.lower()) in remove_accents(city.lower()):
                if city not in locations_map:
                    locations_map[city] = {'type': 'city', 'count': 0}
                locations_map[city]['count'] += count

            # 2. Parsear venue_address para provincia y país
            # Formato típico: "Ciudad, Provincia, País" o "Ciudad, País"
            if venue_address:
                parts = [p.strip() for p in venue_address.split(',')]

                # Si hay 3 partes: Ciudad, Provincia, País
                if len(parts) >= 3:
                    province = parts[1]
                    country = parts[2]

                    if remove_accents(search_query.lower()) in remove_accents(province.lower()):
                        key = f"{province}, {country}"
                        if key not in locations_map:
                            locations_map[key] = {'type': 'province', 'count': 0}
                        locations_map[key]['count'] += count

                    if remove_accents(search_query.lower()) in remove_accents(country.lower()):
                        if country not in locations_map:
                            locations_map[country] = {'type': 'country', 'count': 0}
                        locations_map[country]['count'] += count

                # Si hay 2 partes: Ciudad, País
                elif len(parts) >= 2:
                    country = parts[1]

                    if remove_accents(search_query.lower()) in remove_accents(country.lower()):
                        if country not in locations_map:
                            locations_map[country] = {'type': 'country', 'count': 0}
                        locations_map[country]['count'] += count

        # Convertir a lista y ordenar
        locations = []
        for location_name, data in locations_map.items():
            location_type = data['type']
            event_count = data['count']

            # Iconos según tipo
            # Icons removed for Windows compatibility
            type_label = 'ciudad' if location_type == 'city' else 'provincia' if location_type == 'province' else 'país'

            locations.append({
                'location': location_name,
                'location_type': location_type,
                'event_count': event_count,
                'displayName': f"{location_name} ({event_count} eventos)"
            })

        # Ordenar por tipo (ciudad > provincia > país) y luego por cantidad
        priority = {'city': 1, 'province': 2, 'country': 3}
        locations.sort(key=lambda x: (priority[x['location_type']], -x['event_count']))

        # Limitar resultados
        locations = locations[:limit]

        logger.info(f"OK Encontradas {len(locations)} ubicaciones con eventos")

        return locations

    except Exception as e:
        logger.error(f"ERROR Error buscando ubicaciones: {e}")
        return []

    finally:
        session.close()
