"""
Smart Recommendations API - Sistema de recomendaciones inteligentes
Usa Gemini para generar sugerencias cuando no hay resultados exactos
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import google.generativeai as genai
import json
import os
import aiomysql
from datetime import datetime, timedelta
import asyncio

# Import cultural context
from ai.cultural_context import detect_user_type, get_cultural_prompt, localize_event_description

router = APIRouter()

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SmartRecommendationRequest(BaseModel):
    original_query: str
    found_events: List[Dict[str, Any]]
    user_context: Optional[Dict[str, Any]] = {}
    no_results: bool = False

class SmartRecommendationResponse(BaseModel):
    original_query: str
    analysis: str
    recommendations: List[Dict[str, Any]]
    alternative_suggestions: List[str]
    follow_up_questions: List[str]
    personalized_message: str

async def get_similar_events_from_db(category: str = None, keywords: List[str] = None) -> List[Dict]:
    """Obtener eventos similares de la base de datos"""
    from main_mysql import pool
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Query base
                base_query = """
                    SELECT 
                        id, title, description, start_datetime, end_datetime,
                        venue_name, venue_address, category, subcategory,
                        price, currency, is_free, image_url, event_url, source_api
                    FROM events 
                    WHERE start_datetime >= NOW()
                """
                
                params = []
                conditions = []
                
                if category:
                    conditions.append("category = %s")
                    params.append(category)
                
                if keywords:
                    keyword_conditions = []
                    for keyword in keywords:
                        keyword_conditions.append("(title LIKE %s OR description LIKE %s)")
                        params.extend([f"%{keyword}%", f"%{keyword}%"])
                    
                    if keyword_conditions:
                        conditions.append(f"({' OR '.join(keyword_conditions)})")
                
                if conditions:
                    base_query += " AND " + " AND ".join(conditions)
                
                base_query += " ORDER BY start_datetime ASC LIMIT 20"
                
                await cursor.execute(base_query, params)
                events = await cursor.fetchall()
                return [dict(event) for event in events]
                
    except Exception as e:
        print(f"Error getting similar events: {e}")
        return []

def create_smart_recommendation_prompt(
    original_query: str, 
    found_events: List[Dict], 
    similar_events: List[Dict],
    user_context: Dict = None
) -> str:
    """Crear prompt culturalmente apropiado para recomendaciones inteligentes"""
    
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    user_location = user_context.get('location', 'Buenos Aires') if user_context else 'Buenos Aires'
    
    # 🧠 DETECCIÓN CULTURAL INTELIGENTE
    cultural_context = detect_user_type(
        query=original_query,
        location_context=user_context or {}
    )
    
    # 🎯 PROMPT CULTURALMENTE APROPIADO
    cultural_prompt = get_cultural_prompt(cultural_context, original_query)
    
    # 🌎 EVENTOS LOCALIZADOS
    localized_found_events = [
        localize_event_description(event, cultural_context) 
        for event in found_events[:10]
    ]
    localized_similar_events = [
        localize_event_description(event, cultural_context) 
        for event in similar_events[:10]  
    ]
    
    # 🚀 PROMPT FINAL INTEGRADO
    prompt = f"""
{cultural_prompt}

DATOS PARA PROCESAR:
EVENTOS ENCONTRADOS ({len(found_events)}):
{json.dumps(localized_found_events, indent=2, default=str, ensure_ascii=False)}

EVENTOS SIMILARES DISPONIBLES ({len(similar_events)}):
{json.dumps(localized_similar_events, indent=2, default=str, ensure_ascii=False)}

CONTEXTO DETECTADO:
- Tipo de usuario: {cultural_context.user_type.value}
- Nivel cultural: {cultural_context.cultural_level.value}  
- Idioma: {cultural_context.detected_language}
- Confianza: {cultural_context.confidence:.2f}

TAREA ESPECÍFICA:
1. **Analizar qué busca** según su perfil cultural
2. **Recomendar eventos** en su estilo de comunicación
3. **Dar contexto cultural** apropiado para su nivel
4. **Sugerir plan completo** considerando horarios/costumbres locales

RESPONDE EN FORMATO JSON:
{{
    "analysis": "Análisis de qué busca (en su estilo de comunicación)",
    "main_recommendations": [
        {{
            "event_id": "id del evento",
            "title": "título localizado",
            "reason": "por qué lo recomiendas (estilo apropiado)",
            "match_score": "1-10", 
            "perfect_for": "tipo de persona/momento",
            "cultural_context": "explicación cultural si es turista"
        }}
    ],
    "alternative_suggestions": [
        "Sugerencias en el estilo de comunicación detectado",
        "Con jerga local si es local, con explicaciones si es turista"
    ],
    "follow_up_questions": [
        "Preguntas en el estilo apropiado"
    ],
    "personalized_message": "Mensaje personal en el tono/estilo correcto",
    "local_insights": [
        "Tips culturales apropiados para el nivel del usuario"
    ]
}}

IMPORTANTE: Usá el estilo de comunicación detectado - jerga local para locales, explicativo para turistas.
Responde SOLO en JSON válido, sin markdown.
"""
    
    return prompt

@router.post("/recommend", response_model=SmartRecommendationResponse)
async def get_smart_recommendations(request: SmartRecommendationRequest):
    """
    Generar recomendaciones inteligentes basadas en búsqueda original
    
    Casos de uso:
    1. Usuario busca algo específico pero no hay resultados exactos
    2. Usuario encuentra algo pero queremos sugerir experiencias complementarias
    3. Usuario parece indeciso y necesita orientación
    """
    
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de recomendaciones no disponible"
        )
    
    try:
        # 1. Analizar la consulta para extraer categorías e intenciones
        analysis_keywords = []
        detected_category = None
        
        query_lower = request.original_query.lower()
        
        # Detectar categorías
        if any(word in query_lower for word in ['teatro', 'obra', 'comedia', 'drama']):
            detected_category = 'theater'
            analysis_keywords.extend(['teatro', 'comedia', 'drama', 'espectáculo'])
            
        elif any(word in query_lower for word in ['concierto', 'música', 'banda', 'recital']):
            detected_category = 'music'
            analysis_keywords.extend(['música', 'concierto', 'show', 'recital'])
            
        elif any(word in query_lower for word in ['fiesta', 'party', 'boliche', 'after']):
            detected_category = 'party'
            analysis_keywords.extend(['fiesta', 'party', 'diversión', 'noche'])
            
        elif any(word in query_lower for word in ['deporte', 'fútbol', 'partido', 'estadio']):
            detected_category = 'sports'
            analysis_keywords.extend(['deporte', 'fútbol', 'partido', 'estadio'])
        
        # 2. Buscar eventos similares si no hay resultados o para complementar
        similar_events = []
        if request.no_results or len(request.found_events) < 3:
            similar_events = await get_similar_events_from_db(
                category=detected_category,
                keywords=analysis_keywords[:3]  # Limitar keywords
            )
        
        # 3. Crear prompt para Gemini
        prompt = create_smart_recommendation_prompt(
            request.original_query,
            request.found_events,
            similar_events,
            request.user_context
        )
        
        # 4. Consultar Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await asyncio.create_task(
            asyncio.to_thread(model.generate_content, prompt)
        )
        
        # 5. Procesar respuesta
        try:
            ai_response = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback response si Gemini no devuelve JSON válido
            ai_response = {
                "analysis": f"Análisis de búsqueda: {request.original_query}",
                "main_recommendations": [],
                "alternative_suggestions": [
                    "Intentá buscar con palabras similares",
                    "Explorá otras categorías de eventos",
                    "Revisá eventos en fechas cercanas"
                ],
                "follow_up_questions": [
                    "¿Te interesaría algo similar?",
                    "¿Querés que te sugiera otras opciones?"
                ],
                "personalized_message": "No encontramos exactamente lo que buscás, pero hay muchas otras opciones interesantes.",
                "local_insights": []
            }
        
        # 6. Construir respuesta final
        return SmartRecommendationResponse(
            original_query=request.original_query,
            analysis=ai_response.get('analysis', ''),
            recommendations=ai_response.get('main_recommendations', []),
            alternative_suggestions=ai_response.get('alternative_suggestions', []),
            follow_up_questions=ai_response.get('follow_up_questions', []),
            personalized_message=ai_response.get('personalized_message', '')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generando recomendaciones: {str(e)}"
        )

@router.post("/analyze-intent")
async def analyze_user_intent(request: Dict[str, Any]):
    """
    Analizar la intención del usuario para optimizar búsquedas
    """
    
    query = request.get('query', '')
    context = request.get('context', {})
    
    if not GEMINI_API_KEY:
        return {"intent": "general_search", "confidence": 0.5}
    
    try:
        prompt = f"""
        Analiza esta consulta de usuario sobre eventos y detecta su intención:
        
        CONSULTA: "{query}"
        CONTEXTO: {json.dumps(context, default=str)}
        
        Responde en JSON con:
        {{
            "intent": "search_events|ask_recommendation|compare_options|plan_evening|find_venue",
            "confidence": 0.0-1.0,
            "extracted_filters": {{
                "category": "music|theater|sports|party|cultural|general",
                "date_preference": "today|tomorrow|weekend|next_week|flexible",
                "price_preference": "free|cheap|medium|expensive|any",
                "group_size": "solo|couple|friends|family|large_group",
                "mood": "energetic|relaxed|romantic|adventurous|cultural"
            }},
            "suggested_search_strategy": "exact_match|broad_search|alternative_suggestions|guided_discovery"
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await asyncio.create_task(
            asyncio.to_thread(model.generate_content, prompt)
        )
        
        try:
            result = json.loads(response.text)
            return result
        except:
            return {"intent": "general_search", "confidence": 0.5}
            
    except Exception as e:
        return {"intent": "general_search", "confidence": 0.1, "error": str(e)}