"""
Servicio para buscar imágenes en Google Images
Adaptado de buscar-primera-imagen.js
"""

import httpx
import re
import logging

logger = logging.getLogger(__name__)


async def _try_search_with_query(search_query: str, headers: dict) -> str | None:
    """
    Intenta buscar imagen con un query específico

    Args:
        search_query: Query de búsqueda
        headers: Headers HTTP

    Returns:
        URL de imagen o None
    """
    try:
        url = f"https://www.google.com/search?q={search_query}&tbm=isch"

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            html = response.text

            # Buscar URLs de imágenes en el HTML
            # Patrón que excluye URLs de Wikipedia y páginas web
            # Solo captura URLs directas de imágenes

            # Lista de dominios/patrones a excluir
            excluded_patterns = [
                'wikipedia.org/wiki/',
                'wikimedia.org/wiki/',
                'gstatic.com',
                'googleusercontent.com/youtube',
                'instagram.com',
                'cdninstagram.com',
            ]

            def is_valid_image_url(url: str) -> bool:
                """Verifica si la URL es una imagen válida"""
                url_lower = url.lower()
                for pattern in excluded_patterns:
                    if pattern in url_lower:
                        return False
                return True

            # Recolectar todas las URLs de imágenes
            all_image_urls = []

            # JPG
            jpg_matches = re.findall(r'(https://[^\s"\'<>)]+\.jpg)', html, re.IGNORECASE)
            all_image_urls.extend(jpg_matches)

            # PNG
            png_matches = re.findall(r'(https://[^\s"\'<>)]+\.png)', html, re.IGNORECASE)
            all_image_urls.extend(png_matches)

            # JPEG
            jpeg_matches = re.findall(r'(https://[^\s"\'<>)]+\.jpeg)', html, re.IGNORECASE)
            all_image_urls.extend(jpeg_matches)

            # Filtrar y retornar la primera URL válida
            valid_urls = [url for url in all_image_urls if is_valid_image_url(url)]

            if valid_urls:
                # Retornar la segunda si existe, sino la primera
                if len(valid_urls) >= 2:
                    logger.debug(f"🔄 Usando segunda imagen válida (total: {len(valid_urls)})")
                    return valid_urls[1]
                else:
                    logger.debug(f"✅ Usando primera imagen válida (total: {len(valid_urls)})")
                    return valid_urls[0]

            return None

    except Exception as e:
        logger.debug(f"Error en búsqueda: {e}")
        return None


def extract_keywords(description: str, max_keywords: int = 3) -> str:
    """
    Extrae palabras clave de la descripción

    Args:
        description: Descripción del evento
        max_keywords: Número máximo de keywords a extraer

    Returns:
        String con keywords separadas por espacio
    """
    if not description or not description.strip():
        return ""

    # Palabras a ignorar (stop words en español)
    stop_words = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'de', 'del', 'en', 'con', 'por', 'para', 'y', 'o', 'que',
        'es', 'su', 'sus', 'al', 'lo', 'le', 'se', 'a', 'e', 'i'
    }

    # Limpiar y dividir en palabras
    words = re.findall(r'\b[a-záéíóúñ]{4,}\b', description.lower())

    # Filtrar stop words
    keywords = [w for w in words if w not in stop_words]

    # Retornar primeras N keywords
    return ' '.join(keywords[:max_keywords])


async def search_google_image(query: str, venue: str = '', city: str = '', description: str = '') -> str | None:
    """
    Buscar imagen en Google Images con 3 etapas:
    1. Solo título
    2. Keywords de descripción
    3. Solo venue

    Args:
        query: Título del evento
        venue: Nombre del lugar/venue
        city: Ciudad (no usado en las 3 etapas)
        description: Descripción del evento

    Returns:
        URL de la imagen encontrada o None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Limpiar título
        cleaned_title = query
        if '/' in query:
            cleaned_title = query.split('/')[0].strip()
        elif ':' in query:
            cleaned_title = query.split(':')[0].strip()

        # ETAPA 1: Solo título
        logger.info(f"🔍 Etapa 1/3 - Solo título: '{cleaned_title}'")
        image_url = await _try_search_with_query(cleaned_title, headers)
        if image_url:
            logger.info(f"✅ Imagen encontrada en etapa 1: {image_url[:60]}...")
            return image_url

        # ETAPA 2: Keywords de descripción
        if description and description.strip():
            keywords = extract_keywords(description)
            if keywords:
                logger.info(f"🔍 Etapa 2/3 - Keywords de descripción: '{keywords}'")
                image_url = await _try_search_with_query(keywords, headers)
                if image_url:
                    logger.info(f"✅ Imagen encontrada en etapa 2: {image_url[:60]}...")
                    return image_url

        # ETAPA 3: Solo venue
        if venue and venue.strip():
            logger.info(f"🔍 Etapa 3/3 - Solo venue: '{venue.strip()}'")
            image_url = await _try_search_with_query(venue.strip(), headers)
            if image_url:
                logger.info(f"✅ Imagen encontrada en etapa 3: {image_url[:60]}...")
                return image_url

        # ETAPA 4 (FALLBACK): Imagen genérica de picsum
        fallback_url = "https://picsum.photos/800/600"
        logger.warning(f"⚠️ No se encontraron imágenes después de 3 etapas para: {cleaned_title}")
        logger.info(f"🎲 Usando imagen genérica de fallback: {fallback_url}")
        return fallback_url

    except Exception as e:
        logger.error(f"❌ Error buscando imagen para '{query}': {e}")
        # Incluso en error, devolver fallback
        return "https://picsum.photos/800/600"
