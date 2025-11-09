"""
🌐 EXTERNAL EVENTS API
Endpoint para recibir eventos scrapeados externamente (BrightData, Puppeteer, etc.)
Y GUARDARLOS EN POSTGRESQL
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from batch.nightly_scraper import Event, Base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/external", tags=["External Events"])

# Database connection
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/eventos_db')
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)


class ExternalEvent(BaseModel):
    """Modelo para eventos externos (flexible)"""
    numero: Optional[int] = None
    nombre: str
    fecha: str  # Puede ser "Sábado 14 de diciembre de 2025" o "2025-12-14"
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    lugar: Optional[str] = None
    precio: Optional[str] = None
    hora: Optional[str] = None
    imagen: Optional[str] = None
    url: Optional[str] = None


class ExternalEventsPayload(BaseModel):
    """Payload completo de BrightData/Puppeteer"""
    consulta: str
    ubicacion: str
    fecha_consulta: str
    fuente: str
    nota_importante: Optional[str] = None
    contexto: Optional[str] = None
    eventos_confirmados_o_tradicionales: List[ExternalEvent]


def parse_date_spanish(fecha_str: str) -> Optional[str]:
    """
    🗓️ PARSEAR FECHAS EN ESPAÑOL

    Convierte fechas como "Sábado 14 de diciembre de 2025" a "2025-12-14"
    """
    try:
        # Si ya está en formato ISO
        if "-" in fecha_str and len(fecha_str) == 10:
            return fecha_str

        # Mapeo de meses en español
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        # Extraer partes: "Sábado 14 de diciembre de 2025"
        parts = fecha_str.lower().split()

        dia = None
        mes = None
        año = None

        for i, part in enumerate(parts):
            # Buscar día (número)
            if part.isdigit() and 1 <= int(part) <= 31 and dia is None:
                dia = int(part)

            # Buscar mes
            if part in meses:
                mes = meses[part]

            # Buscar año (4 dígitos)
            if part.isdigit() and len(part) == 4:
                año = int(part)

        if dia and mes and año:
            return f"{año:04d}-{mes:02d}-{dia:02d}"

        return None

    except Exception as e:
        logger.warning(f"⚠️ Error parseando fecha '{fecha_str}': {e}")
        return None


def standardize_external_event(event: ExternalEvent, ubicacion: str) -> Dict[str, Any]:
    """
    📋 ESTANDARIZAR EVENTO EXTERNO AL FORMATO DE LA APP

    Convierte eventos de BrightData al formato interno
    """

    # Parsear fecha
    fecha_iso = parse_date_spanish(event.fecha)

    if not fecha_iso:
        # Fallback: usar fecha actual + 7 días
        from datetime import timedelta
        fecha_iso = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    # Hora por defecto
    hora = event.hora or "20:00"

    # Combinar fecha y hora
    try:
        start_datetime = datetime.strptime(f"{fecha_iso} {hora}", '%Y-%m-%d %H:%M')
    except:
        start_datetime = datetime.strptime(f"{fecha_iso} 20:00", '%Y-%m-%d %H:%M')

    # Determinar categoría
    tipo = (event.tipo or "").lower()
    if "música" in tipo or "concierto" in tipo:
        category = "Música"
    elif "deporte" in tipo or "maratón" in tipo:
        category = "Deportes"
    elif "cultura" in tipo or "teatro" in tipo or "cine" in tipo:
        category = "Cultural"
    elif "fiesta" in tipo or "festival" in tipo:
        category = "Fiestas"
    else:
        category = "Eventos"

    # Precio
    precio = event.precio or "Consultar"
    is_free = precio.lower() in ['gratis', 'free', 'libre', 'gratuito']

    return {
        'title': event.nombre,
        'description': event.descripcion or f"Evento en {ubicacion}",
        'event_url': event.url or '',
        'image_url': event.imagen or '',
        'venue_name': event.lugar or ubicacion,
        'venue_address': '',
        'start_datetime': start_datetime.isoformat(),
        'end_datetime': None,
        'price': precio,
        'is_free': is_free,
        'source': 'brightdata',
        'category': category,
        'external_id': f"brightdata_{ubicacion}_{fecha_iso}_{event.nombre.replace(' ', '_')[:30]}"
    }


def save_events_to_db(events: List[Dict[str, Any]], city: str, country: str = "Argentina") -> Dict[str, int]:
    """
    💾 GUARDAR EVENTOS EN POSTGRESQL

    Guarda eventos en la base, evitando duplicados por external_id

    Returns:
        Dict con contadores de saved/updated
    """
    session = SessionLocal()

    try:
        saved_count = 0
        updated_count = 0

        for event_data in events:
            external_id = event_data.get('external_id')

            if not external_id:
                logger.warning(f"⚠️ Evento sin external_id: {event_data.get('title')}")
                continue

            # Verificar si ya existe
            existing = session.query(Event).filter_by(external_id=external_id).first()

            # Parsear start_datetime si es string
            if isinstance(event_data.get('start_datetime'), str):
                try:
                    from datetime import datetime
                    event_data['start_datetime'] = datetime.fromisoformat(
                        event_data['start_datetime'].replace('Z', '+00:00')
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Error parseando fecha: {e}")
                    continue

            if existing:
                # Actualizar evento existente
                for key, value in event_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                existing.scraped_at = datetime.utcnow()
                updated_count += 1
            else:
                # Crear nuevo evento
                event_data['city'] = city
                event_data['country'] = country
                event_data['scraped_at'] = datetime.utcnow()

                event = Event(**event_data)
                session.add(event)
                saved_count += 1

        session.commit()
        logger.info(f"💾 DB: {saved_count} nuevos, {updated_count} actualizados")

        return {"saved": saved_count, "updated": updated_count}

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error guardando eventos en DB: {e}")
        raise
    finally:
        session.close()


@router.post("/submit-events")
async def submit_external_events(payload: ExternalEventsPayload = Body(...)):
    """
    📥 RECIBIR EVENTOS SCRAPEADOS EXTERNAMENTE Y GUARDAR EN DB

    Endpoint para que BrightData/Puppeteer envíe eventos scrapeados.

    Example payload:
    ```json
    {
      "consulta": "10 eventos de música importantes en Villa Gesell para diciembre del 2025",
      "ubicacion": "Villa Gesell, Provincia de Buenos Aires, Argentina",
      "fecha_consulta": "2025-11-02",
      "fuente": "Gemini (Google)",
      "eventos_confirmados_o_tradicionales": [
        {
          "numero": 1,
          "nombre": "Aniversario de Villa Gesell",
          "fecha": "Sábado 14 de diciembre de 2025",
          "descripcion": "Celebración...",
          "tipo": "Celebración fundacional con música",
          "lugar": "Plaza Primera Junta"
        }
      ]
    }
    ```

    Returns:
        Dict con eventos estandarizados y guardados en DB
    """

    try:
        logger.info(f"📥 Recibiendo {len(payload.eventos_confirmados_o_tradicionales)} eventos externos de {payload.fuente}")

        # Estandarizar todos los eventos
        standardized_events = []

        for event in payload.eventos_confirmados_o_tradicionales:
            try:
                std_event = standardize_external_event(event, payload.ubicacion)
                standardized_events.append(std_event)
            except Exception as e:
                logger.warning(f"⚠️ Error estandarizando evento '{event.nombre}': {e}")
                continue

        logger.info(f"✅ {len(standardized_events)} eventos estandarizados exitosamente")

        # GUARDAR EN BASE DE DATOS
        # Extraer ciudad del campo ubicacion
        city = payload.ubicacion.split(',')[0].strip()

        db_stats = save_events_to_db(standardized_events, city)

        return {
            "success": True,
            "events_received": len(payload.eventos_confirmados_o_tradicionales),
            "events_standardized": len(standardized_events),
            "events_saved": db_stats["saved"],
            "events_updated": db_stats["updated"],
            "events": standardized_events,
            "metadata": {
                "query": payload.consulta,
                "location": payload.ubicacion,
                "source": payload.fuente,
                "scraped_at": payload.fecha_consulta
            }
        }

    except Exception as e:
        logger.error(f"❌ Error procesando eventos externos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-events/stream")
async def submit_external_events_stream(payload: ExternalEventsPayload = Body(...)):
    """
    📥 RECIBIR EVENTOS Y RETORNAR EN FORMATO STREAMING

    Endpoint compatible con el formato de streaming del frontend
    """

    try:
        result = await submit_external_events(payload)

        # Formato compatible con streaming
        return {
            "scraper": payload.fuente.lower().replace(" ", "_"),
            "events": result["events"],
            "execution_time": "0.5s",
            "success": True,
            "error": None,
            "count": len(result["events"])
        }

    except Exception as e:
        logger.error(f"❌ Error en streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))
