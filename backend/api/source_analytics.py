"""
📊 Source Analytics API - Detector de Gaps y Oportunidades
Endpoints para analizar qué fuentes faltan y priorizar nuevas integraciones
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

# Import our gap detector
from analytics.source_gap_detector import analyze_data_gaps, SourceGapDetector
from integrations.hybrid_enricher import enrich_events_hybrid

router = APIRouter()

class SourceGapAnalysisResponse(BaseModel):
    analysis_date: str
    gaps_detected: int
    implementation_plan: Dict
    top_missing_sources: List[Dict]
    recommendations: Dict

class HybridEnrichmentRequest(BaseModel):
    events: List[Dict]
    country_code: str = "AR"
    enable_scraping: bool = True

@router.get("/gaps/analyze", response_model=SourceGapAnalysisResponse)
async def analyze_source_gaps():
    """
    🔍 Analizar gaps de fuentes de datos
    
    Detecta automáticamente qué fuentes faltan basado en:
    - Búsquedas sin resultados
    - Categorías con pocos eventos  
    - Ubicaciones sin cobertura
    - Gaps de precios/tipos de eventos
    """
    try:
        analysis = await analyze_data_gaps()
        
        return SourceGapAnalysisResponse(
            analysis_date=analysis["analysis_date"],
            gaps_detected=analysis["gaps_detected"], 
            implementation_plan=analysis["implementation_plan"],
            top_missing_sources=analysis["top_missing_sources"],
            recommendations=analysis["recommendations"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing gaps: {str(e)}")

@router.get("/gaps/priorities")
async def get_source_priorities():
    """
    🎯 Obtener prioridades de implementación de fuentes
    """
    try:
        detector = SourceGapDetector()
        gaps = await detector.analyze_failed_searches(days_back=30)
        
        if not gaps:
            return {
                "message": "No gaps detected in the last 30 days",
                "recommendation": "Sistema funcionando bien o necesita más data de búsquedas"
            }
        
        plan = detector.generate_implementation_plan()
        top_sources = detector.get_top_missing_sources()
        
        # Calcular ROI por fuente
        source_roi = {}
        for source_data in top_sources:
            source = source_data["source"]
            impact = source_data["total_impact"]
            
            # Estimar esfuerzo (simplificado)
            effort_map = {
                "api": 2, "scraping": 4, "complex": 7, "manual": 10
            }
            effort = effort_map.get("scraping", 5)  # Default scraping
            
            roi = impact / effort
            source_roi[source] = {
                "impact": impact,
                "effort": effort,
                "roi": round(roi, 2),
                "queries": source_data["total_queries"]
            }
        
        return {
            "analysis_period": "30 days",
            "total_gaps": len(gaps),
            "next_sprint_items": len(plan.get("next_sprint", [])),
            "source_priorities": dict(sorted(source_roi.items(), 
                                           key=lambda x: x[1]["roi"], 
                                           reverse=True)[:10]),
            "quick_wins": [
                source for source, data in source_roi.items() 
                if data["roi"] > 2.0 and data["effort"] <= 3
            ][:5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting priorities: {str(e)}")

@router.post("/enrich/hybrid")
async def enrich_events_with_context(request: HybridEnrichmentRequest):
    """
    🧩 Enriquecer eventos con contexto híbrido (API + Scraping)
    
    Combina datos estructurados de APIs con contexto cultural de scraping
    para crear la experiencia más rica posible
    """
    try:
        if not request.events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        # Enriquecer eventos híbridamente
        enriched_events = await enrich_events_hybrid(
            events=request.events,
            country_code=request.country_code
        )
        
        # Calcular métricas de enrichment
        total_events = len(request.events)
        enriched_count = len([e for e in enriched_events if e.get("enrichment_sources", 0) > 0])
        avg_confidence = sum(e.get("enrichment_confidence", 0) for e in enriched_events) / total_events
        
        return {
            "enriched_events": enriched_events,
            "enrichment_stats": {
                "total_events": total_events,
                "enriched_events": enriched_count,
                "enrichment_rate": round(enriched_count / total_events, 2),
                "avg_confidence": round(avg_confidence, 2),
                "sources_used": list(set([
                    source for event in enriched_events 
                    for source in event.get("smart_tags", [])
                ]))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching events: {str(e)}")

@router.get("/sources/coverage")
async def get_source_coverage():
    """
    📊 Análisis de cobertura actual de fuentes
    """
    try:
        # Obtener eventos de los últimos 30 días por fuente
        from main_mysql import pool
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    SELECT 
                        source_api,
                        category,
                        COUNT(*) as event_count,
                        AVG(CASE WHEN is_free = 1 THEN 0 ELSE price END) as avg_price
                    FROM events 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY source_api, category
                    ORDER BY event_count DESC
                """
                
                await cursor.execute(query)
                results = await cursor.fetchall()
                
                # Procesar resultados
                coverage = {}
                total_events = 0
                
                for row in results:
                    source, category, count, avg_price = row
                    total_events += count
                    
                    if source not in coverage:
                        coverage[source] = {
                            "total_events": 0,
                            "categories": {},
                            "avg_price": 0
                        }
                    
                    coverage[source]["total_events"] += count
                    coverage[source]["categories"][category] = count
                    coverage[source]["avg_price"] = float(avg_price or 0)
                
                # Calcular porcentajes
                for source_data in coverage.values():
                    source_data["percentage"] = round(
                        (source_data["total_events"] / total_events) * 100, 1
                    ) if total_events > 0 else 0
                
                return {
                    "analysis_period": "Last 30 days",
                    "total_events": total_events,
                    "active_sources": len(coverage),
                    "source_coverage": coverage,
                    "insights": {
                        "dominant_source": max(coverage.items(), key=lambda x: x[1]["total_events"])[0] if coverage else None,
                        "most_diverse": max(coverage.items(), key=lambda x: len(x[1]["categories"]))[0] if coverage else None,
                        "coverage_gaps": [
                            category for category in ["music", "theater", "sports", "cultural", "tech", "party"]
                            if not any(category in source_data["categories"] for source_data in coverage.values())
                        ]
                    }
                }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing coverage: {str(e)}")

@router.get("/sources/recommendations")
async def get_source_recommendations():
    """
    💡 Recomendaciones inteligentes de próximas fuentes a implementar
    """
    try:
        # Combinar análisis de gaps con coverage
        gaps_analysis = await analyze_data_gaps()
        
        # Fuentes disponibles por país/categoría
        available_sources = {
            "AR": {
                "music": [
                    {"name": "resident_advisor", "effort": 3, "coverage": "electronic music"},
                    {"name": "songkick", "effort": 2, "coverage": "concerts API"},
                    {"name": "bandsintown", "effort": 2, "coverage": "artist tours"}
                ],
                "theater": [
                    {"name": "alternativa_teatral", "effort": 4, "coverage": "independent theater"},
                    {"name": "teatro_colon_api", "effort": 3, "coverage": "classical events"}
                ],
                "sports": [
                    {"name": "afa_oficial", "effort": 5, "coverage": "football official"},
                    {"name": "tyc_sports", "effort": 4, "coverage": "sports news/events"}
                ],
                "food": [
                    {"name": "zomato_events", "effort": 2, "coverage": "restaurant events"},
                    {"name": "restorando", "effort": 4, "coverage": "dining experiences"}
                ]
            }
        }
        
        # Generar recomendaciones basadas en gaps
        recommendations = []
        
        for gap in gaps_analysis.get("implementation_plan", {}).get("next_sprint", [])[:5]:
            gap_desc = gap["description"].lower()
            
            # Matching simple con categorías
            if "teatro" in gap_desc or "theater" in gap_desc:
                for source in available_sources["AR"]["theater"]:
                    recommendations.append({
                        "source": source["name"],
                        "reason": f"Addresses theater gap: {gap['description']}",
                        "priority": gap["priority"],
                        "estimated_effort": source["effort"],
                        "potential_queries": gap["frequency"],
                        "implementation_score": gap["roi_score"]
                    })
            
            elif "música" in gap_desc or "music" in gap_desc:
                for source in available_sources["AR"]["music"]:
                    recommendations.append({
                        "source": source["name"], 
                        "reason": f"Addresses music gap: {gap['description']}",
                        "priority": gap["priority"],
                        "estimated_effort": source["effort"],
                        "potential_queries": gap["frequency"],
                        "implementation_score": gap["roi_score"]
                    })
        
        # Ordenar por score de implementación
        recommendations.sort(key=lambda x: x["implementation_score"], reverse=True)
        
        return {
            "total_recommendations": len(recommendations),
            "top_recommendations": recommendations[:8],
            "implementation_roadmap": {
                "week_1": [r for r in recommendations if r["estimated_effort"] <= 2][:3],
                "week_2": [r for r in recommendations if r["estimated_effort"] == 3][:2], 
                "month_1": [r for r in recommendations if r["estimated_effort"] >= 4][:3]
            },
            "estimated_impact": {
                "queries_addressed": sum(r["potential_queries"] for r in recommendations[:5]),
                "coverage_improvement": "15-25% estimated increase",
                "user_satisfaction": "High impact on search success rate"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")