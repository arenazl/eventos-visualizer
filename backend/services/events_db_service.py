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


def normalize_category(category: str) -> str:
    """
    Normaliza categorías a formato estándar (inglés, minúsculas)

    Args:
        category: Categoría en cualquier formato

    Returns:
        Categoría normalizada
    """
    if not category:
        return 'other'

    # Convertir a minúsculas y quitar espacios
    cat_lower = category.lower().strip()

    # Mapeo de categorías
    CATEGORY_MAP = {
        # Música
        'musica': 'music',
        'música': 'music',
        'music': 'music',

        # Deportes
        'deportes': 'sports',
        'sports': 'sports',

        # Tecnología
        'tech': 'tech',
        'tecnología': 'tech',
        'tecnologia': 'tech',
        'negocios': 'tech',

        # Cultural
        'cultural': 'cultural',
        'turismo': 'cultural',

        # Comida
        'food': 'food',
        'gastronomía': 'food',
        'gastronomia': 'food',
        'feria': 'food',

        # Nightlife
        'nightlife': 'nightlife',
        'fiestas': 'nightlife',
        'party': 'nightlife',

        # Festival
        'festival': 'festival',

        # Film
        'film': 'film',
        'cine': 'film',

        # Theater
        'theater': 'theater',
        'theatre': 'theater',
        'teatro': 'theater',

        # Art
        'art': 'art',
        'arte': 'art',

        # Otros
        'other': 'other',
        'general': 'other',
        'entretenimiento': 'other',
        'hobbies': 'other',
        'ciencia': 'other',
        'civico': 'other',
        'cívico': 'other',
        'comedy': 'other',
    }

    # Buscar mapeo exacto
    if cat_lower in CATEGORY_MAP:
        return CATEGORY_MAP[cat_lower]

    # Si tiene múltiples categorías separadas por /, tomar la primera
    if '/' in cat_lower:
        first_cat = cat_lower.split('/')[0].strip()
        if first_cat in CATEGORY_MAP:
            return CATEGORY_MAP[first_cat]

    # Default: other
    return 'other'


async def search_events_by_location(
    location: str,
    category: Optional[str] = None,
    limit: int = 100,
    days_ahead: int = 90,
    include_parent_city: bool = True,
    parent_city: Optional[str] = None  # ✨ NUEVO: Ciudad padre desde metadata del frontend
) -> List[Dict[str, Any]]:
    """
     BUSCAR EVENTOS POR UBICACIÓN EN MYSQL

    Args:
        location: Ciudad, provincia o país (ej: "Buenos Aires", "Argentina", "Buenos Aires, Argentina")
        category: Categoría opcional (Musica, Cultural, etc.)
        limit: Límite de eventos (default: 100)
        days_ahead: Días hacia adelante (default: 90)
        include_parent_city: Si es True, detecta ciudad principal y busca también allí (default: True)
        parent_city: Ciudad padre desde metadata del frontend (sin necesidad de IA)

    Returns:
        Lista de eventos desde MySQL Aiven
    """

    session = SessionLocal()

    try:
        # Extraer ubicación (puede venir como "Buenos Aires, Argentina" o solo "Brasil")
        search_location = location.split(',')[0].strip()

        # ✨ Si parent_city ya viene del frontend, usarlo directamente (sin AI, sin DB lookup extra)
        if parent_city:
            logger.info(f"🏙️ Usando parent_city del frontend: '{parent_city}' para '{search_location}'")
        else:
            # Solo hacer lookup si NO viene parent_city del frontend
            # PRIMERO: Verificar en DB si la ubicación es un barrio
            try:
                neighborhood_check = session.execute(text('''
                    SELECT DISTINCT city FROM events
                    WHERE neighborhood LIKE :pattern
                    AND city IS NOT NULL AND city != ''
                    LIMIT 1
                '''), {'pattern': f'%%{search_location}%%'})
                row = neighborhood_check.fetchone()
                if row and row[0]:
                    parent_city = row[0]
                    logger.info(f"🏙️ '{search_location}' detectado como barrio de '{parent_city}' (DB lookup)")
            except Exception as e:
                logger.warning(f"⚠️ Error verificando barrio en DB: {e}")

            # SI no se encontró en DB Y include_parent_city está habilitado, usar IA
            if not parent_city and include_parent_city:
                try:
                    from services.gemini_factory import gemini_factory
                    parent_city = await gemini_factory.get_parent_location(search_location)
                    if parent_city:
                        logger.info(f"🏙️ Detectada ciudad principal para '{search_location}': {parent_city} (IA)")
                except TimeoutError:
                    logger.warning(f"⏱️ Timeout detectando ciudad principal (15s) - continuando sin detección")
                except Exception as e:
                    logger.warning(f"⚠️ Error detectando ciudad principal: {e}")

        logger.info(f" Buscando eventos en MySQL para ubicación: '{search_location}'")

        # Rango de fechas
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        # Query SQL simplificada - buscar en: country, city, neighborhood, external_id
        query = """
        SELECT
            id, title, description, event_url, image_url,
            venue_name, venue_address, city, category,
            start_datetime, end_datetime, price, source, neighborhood
        FROM events
        WHERE
            (
                country LIKE :location_pattern
                OR city LIKE :location_pattern
                OR neighborhood LIKE :location_pattern
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
                OR neighborhood LIKE :parent_pattern
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

        # Ordenar: primero eventos del barrio exacto, luego por fecha
        query += """
            ORDER BY
                CASE WHEN neighborhood LIKE :location_pattern THEN 0 ELSE 1 END,
                start_datetime ASC
            LIMIT :limit
        """
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

            event_source = row[12] or ''
            event_neighborhood = row[13] or ''  # Nuevo campo neighborhood
            event_city = row[7] or ''

            # Normalizar categoría (depurar idiomas y variantes)
            raw_category = row[8] or 'other'
            normalized_category = normalize_category(raw_category)

            event = {
                'id': str(row[0]),
                'title': row[1],
                'description': row[2] or '',
                'url': row[3] or '',
                'image_url': row[4] or '',
                'venue_name': row[5] or '',
                'venue_address': row[6] or '',
                'city': event_city,
                'category': normalized_category,  # ✨ Categoría normalizada
                'start_datetime': row[9].isoformat() if row[9] else None,
                'end_datetime': row[10].isoformat() if row[10] else None,
                'price': price,
                'source': event_source or 'database',
                'neighborhood': event_neighborhood,  # ✨ Barrio real de la DB
                'barrio': event_neighborhood or event_source or ''  # Alias para compatibilidad
            }
            events.append(event)

        # parent_city ya fue detectado antes de la query (DB lookup o IA)
        final_parent_city = parent_city

        # 🔍 DEBUG: Mostrar sources únicos de eventos encontrados
        sources_count = {}
        for evt in events:
            src = evt.get('source', 'unknown')
            sources_count[src] = sources_count.get(src, 0) + 1

        sources_summary = ', '.join([f'{src}:{count}' for src, count in sorted(sources_count.items())])

        if final_parent_city:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}' (ciudad padre: {final_parent_city})")
        else:
            logger.info(f"OK Encontrados {len(events)} eventos en MySQL para '{search_location}'")

        logger.info(f"📊 DEBUG Sources: {sources_summary}")

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

        # Query simplificada - buscar en country, city, neighborhood (barrios)
        query = """
        SELECT
            city,
            country,
            neighborhood,
            COUNT(*) as event_count
        FROM events
        WHERE
            start_datetime >= :now
            AND (
                country LIKE :search_pattern
                OR city LIKE :search_pattern
                OR neighborhood LIKE :search_pattern
            )
        GROUP BY city, country, neighborhood
        ORDER BY event_count DESC
        """

        params = {
            'now': datetime.utcnow(),
            'search_pattern': f'%{search_query}%'
        }

        result = session.execute(text(query), params)
        rows = result.fetchall()

        # Función para normalizar nombres de ciudades
        def normalize_city_name(city_name: str) -> str:
            """Normaliza variantes de nombres de ciudades"""
            city_lower = city_name.lower().strip()

            # Buenos Aires y variantes
            if city_lower in ['caba', 'ciudad de buenos aires', 'ciudad autonoma de buenos aires', 'c.a.b.a.']:
                return 'Buenos Aires'

            return city_name.strip()

        # Procesar resultados - city, country, neighborhood (barrios)
        locations_map = {}  # key: location_name, value: {type, count, city, country}

        for row in rows:
            city_raw = row[0] or ''
            country = row[1] or ''
            neighborhood = row[2] or ''
            count = row[3]

            # Normalizar nombre de ciudad
            city = normalize_city_name(city_raw) if city_raw else ''

            # Agregar barrio si coincide (PRIORIDAD 1)
            if neighborhood and search_query.lower() in neighborhood.lower():
                if neighborhood not in locations_map:
                    locations_map[neighborhood] = {'type': 'barrio', 'count': 0, 'city': city, 'country': country}
                locations_map[neighborhood]['count'] += count

            # Agregar ciudad si coincide (buscar en nombre normalizado)
            if city and search_query.lower() in city.lower():
                # Usar nombre normalizado como key
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
