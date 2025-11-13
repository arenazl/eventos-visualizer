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


async def search_google_image(query: str, venue: str = '', city: str = '') -> str | None:
    """
    Buscar la primera imagen relevante en Google Images con múltiples estrategias

    Args:
        query: Query de búsqueda (ej: "Festival Rock Buenos Aires")
        venue: Nombre del lugar/venue (ej: "Luna Park")
        city: Nombre de la ciudad (ej: "Buenos Aires")

    Returns:
        URL de la imagen encontrada o None si no se encuentra
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Limpiar query: si tiene / o :, usar solo la primera parte
        cleaned_query = query
        if '/' in query:
            cleaned_query = query.split('/')[0].strip()
            logger.info(f"🧹 Query limpiado (/) '{query}' → '{cleaned_query}'")
        elif ':' in query:
            cleaned_query = query.split(':')[0].strip()
            logger.info(f"🧹 Query limpiado (:) '{query}' → '{cleaned_query}'")

        # Estrategia 1: Solo título
        logger.info(f"🔍 Intento 1 (solo título): '{cleaned_query}'")
        image_url = await _try_search_with_query(cleaned_query, headers)
        if image_url:
            logger.info(f"✅ Imagen encontrada (intento 1): {image_url[:60]}...")
            return image_url

        # Estrategia 2: Título + venue (si existe)
        if venue and venue.strip():
            search_query_2 = f"{cleaned_query} {venue.strip()}"
            logger.info(f"🔍 Intento 2 (título + venue): '{search_query_2}'")

            image_url = await _try_search_with_query(search_query_2, headers)
            if image_url:
                logger.info(f"✅ Imagen encontrada (intento 2): {image_url[:60]}...")
                return image_url

        # Estrategia 3: Solo venue (si existe)
        if venue and venue.strip():
            logger.info(f"🔍 Intento 3 (solo venue): '{venue.strip()}'")

            image_url = await _try_search_with_query(venue.strip(), headers)
            if image_url:
                logger.info(f"✅ Imagen encontrada (intento 3): {image_url[:60]}...")
                return image_url

        # Estrategia 4: Primeras 3 palabras del título
        first_words = ' '.join(cleaned_query.split()[:3])
        logger.info(f"🔍 Intento 4 (primeras 3 palabras): '{first_words}'")

        image_url = await _try_search_with_query(first_words, headers)
        if image_url:
            logger.info(f"✅ Imagen encontrada (intento 4): {image_url[:60]}...")
            return image_url

        # Estrategia 5: Solo ciudad (si existe)
        if city and city.strip():
            logger.info(f"🔍 Intento 5 (solo ciudad): '{city.strip()}'")

            image_url = await _try_search_with_query(city.strip(), headers)
            if image_url:
                logger.info(f"✅ Imagen encontrada (intento 5): {image_url[:60]}...")
                return image_url

        logger.warning(f"⚠️ No se encontraron imágenes después de 5 intentos para: {cleaned_query}")
        return None

    except Exception as e:
        logger.error(f"❌ Error buscando imagen para '{query}': {e}")
        return None
