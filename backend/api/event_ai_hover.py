"""
Endpoint de IA para análisis rápido de eventos con hover
ACTUALIZADO: Usa sistema multi-provider (Grok/Groq/Gemini) con fallback automático
CON SISTEMA DE PRIORIDADES Y STREAMING
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import os
import logging
import json
import asyncio

router = APIRouter(prefix="/api/ai", tags=["ai-hover"])
logger = logging.getLogger(__name__)

# 💾 Caché en memoria para insights (evitar llamadas repetidas a IA)
_insights_cache = {}

@router.post("/event-insight")
async def get_event_insight(event_data: Dict[str, Any]):
    """
    Obtiene insights rápidos de IA para un evento al hacer hover
    ACTUALIZADO: Usa Grok/Groq/Gemini con fallback automático
    """
    try:
        from services.ai_manager import AIServiceManager

        title = event_data.get("title", "")
        venue = event_data.get("venue_name", "")
        category = event_data.get("category", "")
        location = event_data.get("location", "Buenos Aires")

        # 💾 Crear cache key
        cache_key = f"{title}:{venue}:{category}"

        # ✅ Revisar caché primero
        if cache_key in _insights_cache:
            logger.info(f"✅ Insight CACHEADO para: {title[:40]}...")
            return _insights_cache[cache_key]

        logger.info(f"🎭 Generando insight NUEVO con IA para: {title[:40]}...")

        # 🎯 Prompt COMPLETO con toda la información rica
        prompt = f"""Evento: {title}
Lugar: {venue}
Categoría: {category}
Ciudad: {location}

Dame información SUPER CONCISA y ÚTIL sobre este evento.

FORMATO de respuesta (JSON):
{{
    "quick_insight": "1 línea sobre qué esperar del evento",
    "venue_tip": "1 tip sobre el lugar",
    "transport": "Colectivos/transporte que llegan ahí",
    "nearby": "1 lugar copado para ir antes/después",
    "vibe": "En 3 palabras el ambiente",
    "pro_tip": "1 consejo que solo un local sabría",
    "best_for": "Para quién es ideal este evento"
}}

Respondé SOLO el JSON, sin explicaciones adicionales."""

        # Usar AIServiceManager con Grok/Groq (ultra rápido)
        manager = AIServiceManager()
        response_text = await manager.generate(
            prompt=prompt,
            temperature=0.7,
            use_fallback=True
        )

        if not response_text:
            logger.warning("⚠️ No AI response, usando fallback")
            fallback = generate_fallback_insight(event_data)
            return {
                "success": True,
                "insight": fallback,
                "powered_by": "Fallback"
            }

        # Parsear JSON
        try:
            json_str = response_text.strip()
            # Limpiar markdown si viene
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            insight_data = json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parse error, usando fallback: {e}")
            # Si falla el parseo, usar fallback
            insight_data = generate_fallback_insight(event_data)

        result = {
            "success": True,
            "event_id": event_data.get("id", "unknown"),
            "insight": insight_data,
            "powered_by": "Grok AI"
        }

        # 💾 Guardar en caché
        _insights_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"Error getting AI insight: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback": generate_fallback_insight(event_data)
        }

def generate_fallback_insight(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights básicos sin IA cuando no está disponible
    """
    category = event.get("category", "general")
    venue = event.get("venue_name", "")

    # Insights predefinidos por categoría
    insights = {
        "music": {
            "quick_insight": "Show en vivo con buena acústica",
            "venue_tip": "Llegá temprano para estar cerca del escenario",
            "transport": "60, 152, 29, Subte Línea B",
            "nearby": "Hay bares copados en la zona para el after",
            "vibe": "Energético, social, vibrante",
            "pro_tip": "El sonido es mejor en el medio del lugar",
            "best_for": "Amantes de la música en vivo"
        },
        "theater": {
            "quick_insight": "Obra para disfrutar del arte escénico",
            "venue_tip": "Las mejores butacas están en el medio",
            "transport": "39, 68, 194, Subte Línea A",
            "nearby": "Cafés históricos para charlar post función",
            "vibe": "Cultural, elegante, íntimo",
            "pro_tip": "Llegá 15 min antes para ubicarte tranquilo",
            "best_for": "Quienes buscan propuestas culturales"
        },
        "sports": {
            "quick_insight": "Evento deportivo con mucha pasión",
            "venue_tip": "Las populares tienen más ambiente",
            "transport": "33, 53, 109",
            "nearby": "Parrillas típicas para comer antes",
            "vibe": "Pasional, familiar, emocionante",
            "pro_tip": "Comprá comida afuera, adentro es caro",
            "best_for": "Familias y fanáticos del deporte"
        },
        "cultural": {
            "quick_insight": "Experiencia cultural enriquecedora",
            "venue_tip": "Tomate tiempo para recorrer todo",
            "transport": "10, 17, 59, 67",
            "nearby": "Librerías y galerías en la zona",
            "vibe": "Tranquilo, inspirador, educativo",
            "pro_tip": "Los miércoles suele haber descuentos",
            "best_for": "Curiosos y amantes del arte"
        },
        "festival": {
            "quick_insight": "Experiencia festiva con mucha energía",
            "venue_tip": "Llevá efectivo para puestos de comida",
            "transport": "Varias líneas según ubicación",
            "nearby": "Food trucks y stands",
            "vibe": "Alegre, festivo, multitudinario",
            "pro_tip": "Llegá temprano para recorrer tranquilo",
            "best_for": "Familias y grupos de amigos"
        }
    }

    # Obtener insight según categoría o usar default
    insight = insights.get(category, insights["cultural"])

    # Personalizar según el venue si es conocido
    if "Luna Park" in venue:
        insight["transport"] = "2, 105, 126, 195"
        insight["nearby"] = "Puerto Madero para cenar"
    elif "Teatro Colón" in venue:
        insight["transport"] = "Subte Línea D, 29, 39, 152"
        insight["nearby"] = "Av. Corrientes llena de teatros y bares"
    elif "Quality" in venue or "Córdoba" in venue:
        insight["transport"] = "Líneas A, B, C del trolley"
        insight["nearby"] = "Nueva Córdoba tiene muchos bares"

    return insight

@router.get("/quick-hover/{event_id}")
async def quick_hover_info(event_id: str):
    """
    Endpoint simplificado para hover rápido
    """
    # Para demo, generamos info básica
    return {
        "event_id": event_id,
        "hover_text": "🎯 Evento popular • 🚌 Líneas 60, 152 • 📍 Zona segura",
        "mini_tips": [
            "Llegá 30 min antes",
            "Zona con buenos bares",
            "Fácil acceso en transporte"
        ]
    }


@router.post("/event-insight-stream")
async def get_event_insight_stream(event_data: Dict[str, Any]):
    """
    🌊 STREAMING VERSION - Insights aparecen progresivamente
    ACTUALIZADO: Usa Grok/Groq/Gemini con fallback automático
    """
    async def event_stream():
        try:
            from services.ai_manager import AIServiceManager

            title = event_data.get("title", "")
            venue = event_data.get("venue_name", "")
            category = event_data.get("category", "")
            location = event_data.get("location", "Buenos Aires")

            # Enviar evento de inicio
            yield f"data: {json.dumps({'type': 'start', 'message': 'Analizando evento...'})}\n\n"
            await asyncio.sleep(0.1)

            # Prompt específico
            prompt = f"""
            Evento: {title}
            Lugar: {venue}
            Categoría: {category}
            Ciudad: {location}

            Dame información SUPER CONCISA y ÚTIL sobre este evento.

            FORMATO de respuesta (JSON):
            {{
                "quick_insight": "1 línea sobre qué esperar del evento",
                "venue_tip": "1 tip sobre el lugar",
                "transport": "Colectivos que llegan ahí",
                "nearby": "1 lugar copado para ir antes/después",
                "vibe": "En 3 palabras el ambiente",
                "pro_tip": "1 consejo que solo un local sabría",
                "best_for": "Para quién es ideal este evento"
            }}

            Respondé SOLO el JSON, sin explicaciones adicionales.
            """

            # Generar con AIServiceManager
            manager = AIServiceManager()
            response_text = await manager.generate(
                prompt=prompt,
                temperature=0.7,
                use_fallback=True
            )

            if not response_text:
                fallback = generate_fallback_insight(event_data)
                yield f"data: {json.dumps({'type': 'complete', 'insight': fallback})}\n\n"
                return

            # Parsear JSON final
            try:
                json_str = response_text.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]

                insight_data = json.loads(json_str.strip())
            except json.JSONDecodeError:
                insight_data = {
                    "quick_insight": response_text[:100] if response_text else "Evento interesante",
                    "transport": "Varias líneas de colectivo",
                    "vibe": "Copado y divertido",
                    "best_for": "Todos los públicos"
                }

            # Enviar resultado final
            yield f"data: {json.dumps({'type': 'complete', 'insight': insight_data})}\n\n"

        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            fallback = generate_fallback_insight(event_data)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'fallback': fallback})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
