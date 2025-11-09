"""
Smart Search API - Búsqueda inteligente con Gemini
El usuario pregunta en lenguaje natural y Gemini procesa todos los eventos
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import google.generativeai as genai
import json
import os
import aiomysql
from datetime import datetime, timedelta

router = APIRouter()

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SmartSearchRequest(BaseModel):
    query: str
    user_context: Optional[Dict[str, Any]] = {}

class SmartSearchResponse(BaseModel):
    query: str
    ai_analysis: str
    recommended_events: List[Dict[str, Any]]
    total_events_analyzed: int
    processing_time: float

async def get_all_events_from_db():
    """Obtener todos los eventos de la base de datos"""
    from main_mysql import pool  # Import pool from main
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Obtener eventos futuros
                await cursor.execute("""
                    SELECT 
                        id, title, description, start_datetime, end_datetime,
                        venue_name, venue_address, category, subcategory,
                        price, currency, is_free, image_url, event_url, source_api
                    FROM events 
                    WHERE start_datetime >= NOW()
                    ORDER BY start_datetime ASC
                    LIMIT 200
                """)
                
                events = await cursor.fetchall()
                return [dict(event) for event in events]
    except Exception as e:
        print(f"Error getting events: {e}")
        return []

def create_gemini_prompt(user_query: str, events: List[Dict], user_context: Dict = None) -> str:
    """Crear prompt inteligente para Gemini"""
    
    # Información del contexto
    current_date = datetime.now().strftime("%Y-%m-%d")
    weekend_start = datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
    weekend_end = weekend_start + timedelta(days=2)
    
    prompt = f"""
Eres un asistente experto en eventos de Buenos Aires. Analiza esta consulta del usuario y recomienda eventos relevantes.

CONSULTA DEL USUARIO: "{user_query}"

CONTEXTO TEMPORAL:
- Fecha actual: {current_date}
- Próximo fin de semana: {weekend_start.strftime('%Y-%m-%d')} a {weekend_end.strftime('%Y-%m-%d')}

EVENTOS DISPONIBLES ({len(events)} total):
{json.dumps(events[:50], indent=2, default=str, ensure_ascii=False)}

INSTRUCCIONES:
1. Analiza la consulta del usuario en español argentino
2. Identifica qué tipo de eventos busca (teatro, música, deportes, etc.)
3. Considera fechas, precios, ubicaciones relevantes
4. Selecciona los 5-8 eventos MÁS RELEVANTES
5. Explica por qué cada evento es una buena recomendación

RESPONDE EN FORMATO JSON:
{{
    "analysis": "Tu análisis de qué busca el usuario",
    "recommendations": [
        {{
            "event_id": "id del evento",
            "title": "título del evento", 
            "reason": "por qué lo recomiendas",
            "match_score": "del 1-10",
            "highlights": ["punto destacado 1", "punto destacado 2"]
        }}
    ],
    "summary": "resumen ejecutivo de las recomendaciones",
    "additional_suggestions": "sugerencias adicionales para el usuario"
}}

Responde SOLO en JSON válido, sin markdown ni texto adicional.
"""
    
    return prompt

@router.post("/search", response_model=SmartSearchResponse)
async def smart_search(request: SmartSearchRequest):
    """
    Búsqueda inteligente de eventos con Gemini
    
    Ejemplos de consultas:
    - "¿Qué obra hay para ver?"
    - "Eventos gratis este fin de semana"
    - "Algo romántico para una cita"
    - "Conciertos de rock en septiembre"
    - "Eventos familiares económicos"
    """
    
    start_time = datetime.now()
    
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Gemini AI no está configurado. Falta GEMINI_API_KEY"
        )
    
    try:
        # 1. Obtener todos los eventos de la BD
        all_events = await get_all_events_from_db()
        
        if not all_events:
            raise HTTPException(
                status_code=404, 
                detail="No hay eventos disponibles en la base de datos"
            )
        
        # 2. Crear prompt inteligente
        prompt = create_gemini_prompt(
            request.query, 
            all_events, 
            request.user_context
        )
        
        # 3. Consultar Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await asyncio.create_task(
            asyncio.to_thread(model.generate_content, prompt)
        )
        
        # 4. Procesar respuesta de Gemini
        try:
            ai_response = json.loads(response.text)
        except json.JSONDecodeError:
            # Si Gemini no devuelve JSON válido, crear respuesta de fallback
            ai_response = {
                "analysis": f"Búsqueda para: {request.query}",
                "recommendations": [],
                "summary": "Error procesando respuesta de Gemini",
                "additional_suggestions": "Intenta ser más específico en tu búsqueda"
            }
        
        # 5. Enriquecer recomendaciones con datos completos
        event_dict = {event['id']: event for event in all_events}
        enriched_recommendations = []
        
        for rec in ai_response.get('recommendations', [])[:10]:  # Limitar a 10
            event_id = rec.get('event_id')
            if event_id and event_id in event_dict:
                full_event = event_dict[event_id].copy()
                full_event.update({
                    'ai_reason': rec.get('reason', ''),
                    'ai_match_score': rec.get('match_score', 0),
                    'ai_highlights': rec.get('highlights', [])
                })
                enriched_recommendations.append(full_event)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SmartSearchResponse(
            query=request.query,
            ai_analysis=ai_response.get('analysis', ''),
            recommended_events=enriched_recommendations,
            total_events_analyzed=len(all_events),
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error en búsqueda inteligente: {str(e)}"
        )

@router.get("/suggestions")
async def get_smart_suggestions():
    """
    Sugerencias inteligentes basadas en eventos disponibles
    """
    try:
        all_events = await get_all_events_from_db()
        
        if not all_events:
            return {"suggestions": []}
        
        # Análisis rápido de categorías disponibles
        categories = {}
        for event in all_events:
            cat = event.get('category', 'general')
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        # Crear sugerencias basadas en categorías más populares
        suggestions = []
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:6]:
            category_names = {
                'music': 'Conciertos y música en vivo',
                'theater': 'Obras de teatro y espectáculos',
                'sports': 'Eventos deportivos',
                'cultural': 'Eventos culturales y arte',
                'party': 'Fiestas y vida nocturna',
                'food': 'Eventos gastronómicos',
                'general': 'Eventos generales'
            }
            
            suggestions.append({
                'category': category,
                'display_name': category_names.get(category, category.title()),
                'event_count': count,
                'suggested_query': f"Eventos de {category_names.get(category, category).lower()}"
            })
        
        return {
            "total_events": len(all_events),
            "suggestions": suggestions,
            "popular_queries": [
                "¿Qué obra hay para ver este fin de semana?",
                "Eventos gratis en Buenos Aires",
                "Conciertos este mes",
                "Algo romántico para una cita",
                "Eventos familiares",
                "Fiestas y vida nocturna"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

import asyncio