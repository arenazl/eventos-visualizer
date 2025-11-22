"""
Cloudinary Image Service
Sube imágenes de eventos a Cloudinary para evitar problemas de hotlinking
"""
import os
import httpx
import hashlib
from typing import Optional
from datetime import datetime

# Cloudinary config desde variables de entorno
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "di39tigkf")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "eventos_unsigned")  # Para uploads sin firma

# URL base de Cloudinary
CLOUDINARY_BASE_URL = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}"


async def upload_image_from_url(
    image_url: str,
    folder: str = "eventos",
    public_id: Optional[str] = None
) -> Optional[str]:
    """
    Descarga una imagen desde URL y la sube a Cloudinary

    Args:
        image_url: URL de la imagen original
        folder: Carpeta en Cloudinary (default: "eventos")
        public_id: ID público opcional (si no se provee, se genera uno)

    Returns:
        URL de Cloudinary o None si falla
    """
    if not image_url or not image_url.startswith("http"):
        return None

    # Dominios que sabemos que no funcionan
    blocked_domains = [
        "example.com",
        "placeholder.com",
        "via.placeholder.com"
    ]

    for domain in blocked_domains:
        if domain in image_url:
            print(f"⚠️ Skipping blocked domain: {domain}")
            return None

    try:
        # Generar public_id único si no se provee
        if not public_id:
            # Crear hash de la URL original para evitar duplicados
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
            timestamp = datetime.now().strftime("%Y%m%d")
            public_id = f"{folder}/{timestamp}_{url_hash}"

        # Método 1: Upload por URL (más simple, no requiere descargar)
        upload_url = f"{CLOUDINARY_BASE_URL}/image/upload"

        # Si tenemos API key y secret, usar upload firmado
        if CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            import time
            timestamp = int(time.time())

            # Crear firma
            params_to_sign = f"folder={folder}&public_id={public_id}&timestamp={timestamp}"
            signature = hashlib.sha1(
                f"{params_to_sign}{CLOUDINARY_API_SECRET}".encode()
            ).hexdigest()

            data = {
                "file": image_url,
                "folder": folder,
                "public_id": public_id,
                "timestamp": timestamp,
                "api_key": CLOUDINARY_API_KEY,
                "signature": signature
            }
        else:
            # Upload sin firma (requiere upload preset configurado en Cloudinary)
            data = {
                "file": image_url,
                "upload_preset": CLOUDINARY_UPLOAD_PRESET,
                "folder": folder
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, data=data)

            if response.status_code == 200:
                result = response.json()
                cloudinary_url = result.get("secure_url")
                print(f"✅ Uploaded to Cloudinary: {cloudinary_url}")
                return cloudinary_url
            else:
                print(f"❌ Cloudinary upload failed: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        print(f"❌ Error uploading to Cloudinary: {e}")
        return None


async def migrate_event_image(event_id: str, current_url: str, db_connection) -> Optional[str]:
    """
    Migra una imagen de evento a Cloudinary y actualiza la BD

    Args:
        event_id: ID del evento
        current_url: URL actual de la imagen
        db_connection: Conexión a la base de datos

    Returns:
        Nueva URL de Cloudinary o None si falla
    """
    # Verificar si ya está en Cloudinary
    if "cloudinary.com" in (current_url or ""):
        print(f"ℹ️ Image already in Cloudinary: {event_id}")
        return current_url

    # Subir a Cloudinary
    new_url = await upload_image_from_url(
        current_url,
        folder="eventos",
        public_id=f"event_{event_id}"
    )

    if new_url and db_connection:
        # Actualizar en la base de datos
        try:
            await db_connection.execute(
                "UPDATE events SET image_url = :new_url WHERE id = :event_id",
                {"new_url": new_url, "event_id": event_id}
            )
            print(f"✅ Updated DB for event {event_id}")
        except Exception as e:
            print(f"❌ DB update failed: {e}")

    return new_url


async def batch_migrate_images(events: list, db_connection, limit: int = 50) -> dict:
    """
    Migra imágenes de múltiples eventos a Cloudinary

    Args:
        events: Lista de eventos con id y image_url
        db_connection: Conexión a la base de datos
        limit: Máximo de imágenes a procesar

    Returns:
        Estadísticas de migración
    """
    stats = {
        "total": 0,
        "migrated": 0,
        "skipped": 0,
        "failed": 0,
        "already_cloudinary": 0
    }

    for event in events[:limit]:
        stats["total"] += 1
        event_id = event.get("id")
        current_url = event.get("image_url")

        if not current_url:
            stats["skipped"] += 1
            continue

        if "cloudinary.com" in current_url:
            stats["already_cloudinary"] += 1
            continue

        new_url = await migrate_event_image(event_id, current_url, db_connection)

        if new_url:
            stats["migrated"] += 1
        else:
            stats["failed"] += 1

    return stats


# Función de prueba
async def test_cloudinary_connection() -> dict:
    """Prueba la conexión a Cloudinary"""
    return {
        "cloud_name": CLOUDINARY_CLOUD_NAME,
        "api_key_configured": bool(CLOUDINARY_API_KEY),
        "api_secret_configured": bool(CLOUDINARY_API_SECRET),
        "upload_preset": CLOUDINARY_UPLOAD_PRESET,
        "status": "ready" if CLOUDINARY_API_KEY else "unsigned_only"
    }
