"""
🗄️ EVENTS DB SERVICE - Consultas rápidas a MySQL Aiven
Busca eventos en la base de datos por ubicación (incluye barrios)
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


async def get_db_connection():
    """
    DEPRECATED: Esta función se mantiene solo para compatibilidad con código legacy.
    Retorna None porque ahora usamos SQLAlchemy SessionLocal() en su lugar.

    TODO: Refactorizar gemini_factory.py para usar SessionLocal() directamente.
    """
    logger.warning("⚠️ get_db_connection() está deprecated, usar SessionLocal() en su lugar")
    return None


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

        # Rango de fechas
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        # Query SQL simplificada - buscar solo en: country, city, external_id
        query = """
        SELECT
            id, title, description, event_url, image_url,
            venue_name, venue_address, city, category,
            start_datetime, end_datetime, price, source
        FROM events
        WHERE
            (
                country LIKE :location_pattern
                OR city LIKE :location_pattern
                OR external_id LIKE :location_pattern
        """

        params = {
            'location_pattern': f'%{search_location}%',
            'now': now,
            'end_date': end_date
        }

        # Agregar búsqueda por ciudad principal si existe
        if parent_city:
            query += """
                OR country LIKE :parent_pattern
                OR city LIKE :parent_pattern
                OR external_id LIKE :parent_pattern
            """
            params['parent_pattern'] = f'%{parent_city}%'
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

        # Ordenar por fecha
        query += """
            ORDER BY start_datetime ASC
            LIMIT :limit
        """
        params['limit'] = limit

        # Ejecutar query
        result = session.execute(text(query), params)
        rows = result.fetchall()

        # Convertir a diccionarios
        events = []
        detected_city = None  # Para extraer ciudad de eventos con barrio

        for row in rows:
            # Convertir precio a float, si falla usar 0.0
            try:
                price = float(row[11]) if row[11] else 0.0
            except (ValueError, TypeError):
                price = 0.0

            event_source = row[12] or ''
            event_city = row[7] or ''

            # Si el evento tiene source (barrio) y coincide con la búsqueda, extraer la ciudad
            if event_source and not parent_city and not detected_city:
                if search_location.lower() in event_source.lower():
                    detected_city = event_city
                    logger.info(f"🏙️ Detectado que '{search_location}' es un barrio de '{detected_city}'")

            event = {
                'id': str(row[0]),
                'title': row[1],
                'description': row[2] or '',
                'url': row[3] or '',
                'image_url': row[4] or '',
                'venue_name': row[5] or '',
                'venue_address': row[6] or '',
                'city': event_city,
                'category': row[8] or 'General',
                'start_datetime': row[9].isoformat() if row[9] else None,
                'end_datetime': row[10].isoformat() if row[10] else None,
                'price': price,
                'source': event_source or 'database',  # Ahora source viene de la DB (barrio)
                'barrio': event_source or ''  # Alias para claridad
            }
            events.append(event)

        # Usar ciudad detectada si no hay parent_city de Gemini
        final_parent_city = parent_city or detected_city

        if final_parent_city:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}' (ciudad padre: {final_parent_city})")
        else:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}'")

        # Retornar metadata de búsqueda expandida junto con eventos
        return {
            'events': events,
            'parent_city_detected': final_parent_city if final_parent_city else None,
            'original_location': search_location,
            'expanded_search': bool(final_parent_city)
        }

    except Exception as e:
        logger.error(f"ERROR Error consultando MySQL: {e}")
        return {
            'events': [],
            'parent_city_detected': None,
            'original_location': location,
            'expanded_search': False
        }

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

        # Query simplificada - buscar en country, city, source (barrios)
        query = """
        SELECT
            city,
            country,
            source,
            COUNT(*) as event_count
        FROM events
        WHERE
            start_datetime >= :now
            AND (
                country LIKE :search_pattern
                OR city LIKE :search_pattern
                OR source LIKE :search_pattern
            )
        GROUP BY city, country, source
        ORDER BY event_count DESC
        """

        params = {
            'now': datetime.utcnow(),
            'search_pattern': f'%{search_query}%'
        }

        result = session.execute(text(query), params)
        rows = result.fetchall()

        # Procesar resultados - city, country, source (barrios)
        locations_map = {}  # key: location_name, value: {type, count, city, country}

        for row in rows:
            city = row[0] or ''
            country = row[1] or ''
            source = row[2] or ''
            count = row[3]

            # Agregar barrio si coincide (PRIORIDAD 1)
            if source and search_query.lower() in source.lower():
                if source not in locations_map:
                    locations_map[source] = {'type': 'barrio', 'count': 0, 'city': city, 'country': country}
                locations_map[source]['count'] += count

            # Agregar ciudad si coincide
            if city and search_query.lower() in city.lower():
                if city not in locations_map:
                    locations_map[city] = {'type': 'city', 'count': 0, 'city': '', 'country': country}
                locations_map[city]['count'] += count

            # Agregar país si coincide
            if country and search_query.lower() in country.lower():
                if country not in locations_map:
                    locations_map[country] = {'type': 'country', 'count': 0, 'city': '', 'country': ''}
                locations_map[country]['count'] += count

        # Convertir a lista y ordenar
        locations = []
        for location_name, data in locations_map.items():
            location_type = data['type']
            event_count = data['count']
            parent_city = data.get('city', '')
            parent_country = data.get('country', '')

            # Formato displayName con ciudad padre si es barrio
            if location_type == 'barrio' and parent_city:
                display_text = f"{location_name}, {parent_city} ({event_count} eventos)"
            else:
                display_text = f"{location_name} ({event_count} eventos)"

            locations.append({
                'location': location_name,
                'location_type': location_type,
                'event_count': event_count,
                'city': parent_city,
                'country': parent_country,
                'displayName': display_text
            })

        # Ordenar por tipo (barrio > ciudad > país) y luego por cantidad
        priority = {'barrio': 0, 'city': 1, 'country': 2}
        locations.sort(key=lambda x: (priority.get(x['location_type'], 999), -x['event_count']))


        # Limitar resultados
        locations = locations[:limit]

        logger.info(f"OK Encontradas {len(locations)} ubicaciones con eventos")

        return locations

    except Exception as e:
        logger.error(f"ERROR Error buscando ubicaciones: {e}")
        return []

    finally:
        session.close()
