"""
🌍 GLOBAL ROUTER API - Endpoint para el sistema de routing inteligente
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import logging
from services.global_scraper_router import global_router
from services.gemini_brain import gemini_brain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/global", tags=["global_routing"])

@router.get("/route/analyze")
async def analyze_location_routing(
    location: str = Query(..., description="Ciudad o país para analizar"),
    intent: str = Query("general", description="Intención del usuario"),
    budget: Optional[str] = Query(None, description="Presupuesto estimado (low/medium/high)"),
    comprehensive: bool = Query(False, description="Si necesita cobertura comprehensiva"),
    use_ai: bool = Query(True, description="Si usar optimización con IA")
) -> Dict[str, Any]:
    """
    🎯 ENDPOINT PRINCIPAL: Analiza ubicación y devuelve routing de scrapers
    
    Ejemplos:
    - /api/global/route/analyze?location=Barcelona&intent=music
    - /api/global/route/analyze?location=Buenos Aires&intent=culture&budget=low
    - /api/global/route/analyze?location=Mexico City&comprehensive=true
    """
    
    try:
        logger.info(f"🌍 Analyzing routing for: {location}")
        
        # Construir contexto
        context = {}
        if budget:
            context["budget"] = budget
        if comprehensive:
            context["comprehensive"] = comprehensive
        
        # Obtener routing recommendation
        routing_result = await global_router.route_scrapers(
            location=location,
            intent=intent, 
            context=context,
            use_ai_suggestions=use_ai
        )
        
        # Agregar insights adicionales
        routing_result["insights"] = {
            "detected_country_confidence": routing_result["routing_metadata"]["confidence_score"],
            "optimal_scraper_count": len(routing_result["selected_scrapers"]),
            "fallback_available": len(routing_result["fallback_scrapers"]) > 0,
            "ai_enhanced": routing_result["routing_metadata"]["ai_enhanced"]
        }
        
        return {
            "status": "success",
            "routing": routing_result,
            "recommendations": await _get_routing_recommendations(routing_result)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in routing analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing routing: {str(e)}")

@router.get("/countries/supported")
async def get_supported_countries() -> Dict[str, Any]:
    """
    🌍 Lista países y ciudades soportados
    """
    stats = global_router.get_routing_stats()
    
    # Detalles por país
    country_details = {}
    for country_code, config in global_router.COUNTRIES.items():
        cities = [city for city, code in global_router.CITY_TO_COUNTRY.items() if code == country_code]
        country_details[country_code] = {
            "name": config.name,
            "currency": config.currency,
            "timezone": config.timezone,
            "supported_cities": cities,
            "primary_strategies": [s.value for s in config.primary_strategies],
            "cultural_specialties": list(config.cultural_context.get("event_types", []))
        }
    
    return {
        "status": "success",
        "summary": {
            "total_countries": stats["supported_countries"],
            "total_cities": stats["supported_cities"]
        },
        "countries": country_details
    }

@router.get("/performance/stats")
async def get_scraper_performance() -> Dict[str, Any]:
    """
    📊 Estadísticas de performance de scrapers
    """
    stats = global_router.get_routing_stats()
    
    # Ranking de scrapers por performance
    performance_ranking = []
    for scraper, metrics in stats["scraper_performance"].items():
        score = metrics["success_rate"] * (1 / max(metrics["avg_time"], 0.1))
        performance_ranking.append({
            "scraper": scraper,
            "success_rate": round(metrics["success_rate"], 3),
            "avg_time_seconds": round(metrics["avg_time"], 2),
            "total_runs": metrics["total_runs"],
            "performance_score": round(score, 3)
        })
    
    performance_ranking.sort(key=lambda x: x["performance_score"], reverse=True)
    
    return {
        "status": "success",
        "performance_ranking": performance_ranking,
        "system_stats": {
            "countries_supported": stats["supported_countries"],
            "total_scrapers_tracked": len(stats["scraper_performance"])
        }
    }

@router.post("/countries/add")
async def add_new_country(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌍 Agregar nuevo país al sistema (solo para admins)
    
    Ejemplo payload:
    {
        "iso_code": "BR",
        "name": "Brasil", 
        "main_language": "pt",
        "currency": "BRL",
        "timezone": "America/Sao_Paulo",
        "primary_strategies": ["native_sites", "global_apis"],
        "scrapers": {
            "native_sites": ["brasil_venues_scraper"]
        }
    }
    """
    try:
        # Aquí irían validaciones de admin, etc.
        
        # Por ahora, solo log de la request
        logger.info(f"📥 Request to add country: {country_data.get('name', 'Unknown')}")
        
        return {
            "status": "info",
            "message": "Country addition feature coming soon",
            "received_data": country_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid country data: {str(e)}")

@router.get("/test/routing/{location}")
async def test_routing(location: str) -> Dict[str, Any]:
    """
    🧪 Test endpoint rápido para probar routing
    """
    
    test_contexts = [
        {"intent": "general", "budget": "medium"},
        {"intent": "music", "budget": "low"}, 
        {"intent": "culture", "comprehensive": True},
        {"intent": "sports", "budget": "high"}
    ]
    
    results = []
    for context in test_contexts:
        try:
            routing = await global_router.route_scrapers(
                location=location,
                intent=context.get("intent", "general"),
                context=context,
                use_ai_suggestions=False  # Más rápido para test
            )
            
            results.append({
                "test_context": context,
                "selected_scrapers": routing["selected_scrapers"],
                "strategies": routing["strategies_used"],
                "confidence": routing["routing_metadata"]["confidence_score"]
            })
        except Exception as e:
            results.append({
                "test_context": context,
                "error": str(e)
            })
    
    return {
        "status": "success",
        "location_tested": location,
        "test_results": results
    }

@router.get("/madrid/events")
async def test_madrid_events() -> Dict[str, Any]:
    """
    🇪🇸 Test específico para Madrid - Primer scraper global
    """
    try:
        # Importar scrapers de Madrid
        from services.ticketmaster_spain_scraper import TicketmasterSpainScraper
        from services.timeout_madrid_scraper import TimeOutMadridScraper
        
        results = {}
        
        # Test Ticketmaster España
        try:
            tm_scraper = TicketmasterSpainScraper()
            tm_events = await tm_scraper.fetch_madrid_events(limit=8)
            results["ticketmaster_spain"] = {
                "status": "success",
                "events_count": len(tm_events),
                "sample_events": tm_events[:3]
            }
        except Exception as e:
            results["ticketmaster_spain"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test TimeOut Madrid
        try:
            timeout_scraper = TimeOutMadridScraper()
            timeout_events = await timeout_scraper.fetch_madrid_events(limit=8)
            results["timeout_madrid"] = {
                "status": "success", 
                "events_count": len(timeout_events),
                "sample_events": timeout_events[:3]
            }
        except Exception as e:
            results["timeout_madrid"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test Marca Madrid (Deportes)
        try:
            from services.marca_madrid_scraper import MarcaMadridScraper
            marca_scraper = MarcaMadridScraper()
            marca_events = await marca_scraper.fetch_madrid_sports_events(limit=8)
            results["marca_madrid"] = {
                "status": "success",
                "events_count": len(marca_events),
                "sample_events": marca_events[:3]
            }
        except Exception as e:
            results["marca_madrid"] = {
                "status": "error", 
                "error": str(e)
            }
        
        # Test routing para Madrid
        try:
            routing = await global_router.route_scrapers("Madrid", "music")
            results["routing_analysis"] = {
                "detected_country": routing["location"]["detected_country"],
                "selected_scrapers": routing["selected_scrapers"],
                "strategies": routing["strategies_used"],
                "cultural_context": routing["cultural_context"]
            }
        except Exception as e:
            results["routing_analysis"] = {"error": str(e)}
        
        return {
            "status": "success",
            "message": "🇪🇸 Madrid scrapers test completed",
            "results": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing Madrid scrapers: {str(e)}"
        }

async def _get_routing_recommendations(routing_result: Dict[str, Any]) -> List[str]:
    """
    💡 Generar recomendaciones basadas en el routing
    """
    recommendations = []
    
    # Confidence-based recommendations
    confidence = routing_result["routing_metadata"]["confidence_score"]
    if confidence < 0.7:
        recommendations.append("⚠️ Ubicación con baja confianza - considera usar términos más específicos")
    
    # Coverage-based recommendations  
    coverage = routing_result["estimated_coverage"]
    if coverage < 0.6:
        recommendations.append("📊 Cobertura limitada - habilita modo 'comprehensive' para más eventos")
    
    # Strategy-based recommendations
    strategies = routing_result["strategies_used"]
    if "social_media" not in strategies:
        recommendations.append("📱 Considera agregar redes sociales para eventos más informales")
    
    if len(routing_result["selected_scrapers"]) < 3:
        recommendations.append("🔧 Pocos scrapers seleccionados - revisa configuración de país")
    
    return recommendations if recommendations else ["✅ Routing óptimo configurado"]