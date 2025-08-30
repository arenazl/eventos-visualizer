"""
🧩 Hybrid Event Enricher - La Magia del API + Scraping
Combina datos estructurados de APIs con contexto cultural de scraping
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json

@dataclass
class EventEnrichment:
    cultural_context: str
    local_tips: List[str] 
    vibe_description: str
    critic_reviews: List[str]
    neighborhood_info: str
    insider_knowledge: str
    confidence_score: float  # Qué tan confiable es el enrichment

class HybridEventEnricher:
    def __init__(self):
        # Mapping de venues a fuentes de contexto
        self.context_sources = {
            # TEATRO
            "teatro_san_martin": ["alternativa_teatral", "lanacion_espectaculos"],
            "teatro_colon": ["teatro_colon_oficial", "timeout_cultura"],
            "complejo_teatral": ["alternativa_teatral", "clarin_espectaculos"],
            
            # MÚSICA  
            "luna_park": ["resident_advisor", "timeout_musica", "rolling_stone"],
            "niceto": ["resident_advisor", "palermo_magazine"],
            "grosse_point": ["under_cultura", "indie_hoy"],
            
            # CULTURA
            "centro_cultural_recoleta": ["timeout_arte", "lanacion_cultura"], 
            "usina_del_arte": ["usina_oficial", "buenosaires_cultura"],
            "malba": ["malba_oficial", "arte_ba"],
            
            # DEPORTES
            "estadio_monumental": ["river_oficial", "ole_deportes", "tyc_sports"],
            "la_bombonera": ["boca_oficial", "ole_deportes"],
            
            # GASTRONOMÍA
            "aramburu": ["lanacion_gourmet", "timeout_food"],
            "pujol": ["palermo_magazine", "food_wine"],
            "chila": ["michelin_guide", "gourmet_ba"]
        }
        
        # Scrapers específicos por fuente
        self.scrapers = {
            "timeout": self._scrape_timeout,
            "lanacion": self._scrape_lanacion,  
            "palermo_magazine": self._scrape_palermo_mag,
            "resident_advisor": self._scrape_resident_advisor,
            "alternativa_teatral": self._scrape_alternativa_teatral
        }

    async def enrich_event(self, base_event: Dict, country_code: str = "AR") -> Dict:
        """
        Enriquecer evento con contexto cultural híbrido
        """
        # 1. IDENTIFICAR FUENTES RELEVANTES
        venue_sources = self._identify_context_sources(base_event)
        
        # 2. SCRAPER CONTEXTO EN PARALELO
        enrichments = await self._gather_enrichments(base_event, venue_sources)
        
        # 3. COMBINAR API + CONTEXTO
        enriched_event = await self._merge_api_and_context(base_event, enrichments)
        
        return enriched_event

    def _identify_context_sources(self, event: Dict) -> List[str]:
        """
        Identificar qué fuentes usar para contexto según el evento
        """
        venue = event.get('venue_name', '').lower()
        category = event.get('category', '').lower()
        
        sources = []
        
        # Por venue específico
        for venue_key, venue_sources in self.context_sources.items():
            if venue_key.replace('_', ' ') in venue:
                sources.extend(venue_sources)
                
        # Por categoría general
        if category == 'music':
            sources.extend(["resident_advisor", "timeout_musica"])
        elif category == 'theater':
            sources.extend(["alternativa_teatral", "timeout_cultura"])
        elif category == 'sports': 
            sources.extend(["ole_deportes", "tyc_sports"])
        elif category == 'cultural':
            sources.extend(["timeout_arte", "lanacion_cultura"])
            
        return list(set(sources))  # Remove duplicates

    async def _gather_enrichments(self, event: Dict, sources: List[str]) -> List[EventEnrichment]:
        """
        Obtener enrichments de múltiples fuentes en paralelo
        """
        tasks = []
        
        for source in sources[:3]:  # Máximo 3 fuentes para performance
            task = self._scrape_single_source(event, source)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados exitosos
        enrichments = [r for r in results if isinstance(r, EventEnrichment)]
        
        return enrichments

    async def _scrape_single_source(self, event: Dict, source: str) -> Optional[EventEnrichment]:
        """
        Scraper individual para una fuente específica
        """
        try:
            # Determinar scraper apropiado
            scraper = None
            for key, scraper_func in self.scrapers.items():
                if key in source:
                    scraper = scraper_func
                    break
                    
            if not scraper:
                return None
                
            # Ejecutar scraping
            enrichment = await scraper(event, source)
            return enrichment
            
        except Exception as e:
            print(f"Error scraping {source}: {e}")
            return None

    async def _scrape_timeout(self, event: Dict, source: str) -> Optional[EventEnrichment]:
        """
        Scraper específico para Time Out Buenos Aires
        """
        # Búsqueda inteligente en Time Out
        search_terms = [
            event.get('title', ''),
            event.get('venue_name', ''),
            event.get('category', '')
        ]
        
        # Simulated scraping (implementar real después)
        timeout_context = {
            "cultural_context": f"Time Out recomienda: {event.get('title')} como imperdible",
            "local_tips": [
                "Llegá 30 min antes para buen lugar",
                "La zona tiene varios bares para after"
            ],
            "vibe_description": "Ambiente trendy, público joven y local",
            "neighborhood_info": f"Zona segura con buena conectividad de subte"
        }
        
        return EventEnrichment(
            cultural_context=timeout_context["cultural_context"],
            local_tips=timeout_context["local_tips"],
            vibe_description=timeout_context["vibe_description"], 
            critic_reviews=[],
            neighborhood_info=timeout_context["neighborhood_info"],
            insider_knowledge="Time Out insider tips disponibles",
            confidence_score=0.85
        )

    async def _scrape_lanacion(self, event: Dict, source: str) -> Optional[EventEnrichment]:
        """
        Scraper para La Nación espectáculos
        """
        # Simulated context from La Nación
        return EventEnrichment(
            cultural_context=f"La Nación destaca la relevancia cultural del evento",
            local_tips=["Evento recomendado por críticos especializados"],
            vibe_description="Público conocedor y exigente",
            critic_reviews=[f"★★★★☆ Crítica especializada"],
            neighborhood_info="Ubicación central con fácil acceso",
            insider_knowledge="Cobertura periodística completa disponible",
            confidence_score=0.90
        )

    async def _scrape_resident_advisor(self, event: Dict, source: str) -> Optional[EventEnrichment]:
        """
        Scraper para Resident Advisor (música electrónica)
        """
        if event.get('category') != 'music':
            return None
            
        return EventEnrichment(
            cultural_context="Resident Advisor: Evento destacado en la escena electrónica porteña",
            local_tips=[
                "Sound system de alta calidad",
                "Crowd conocedor de música electrónica", 
                "After-party hasta late"
            ],
            vibe_description="Underground, ambiente internacional",
            critic_reviews=["Rating RA: 4.2/5"],
            neighborhood_info="Hub de vida nocturna electrónica",
            insider_knowledge="Recomendado por DJs locales",
            confidence_score=0.92
        )

    async def _merge_api_and_context(self, base_event: Dict, enrichments: List[EventEnrichment]) -> Dict:
        """
        Combinar datos API con contexto cultural
        """
        if not enrichments:
            return base_event
            
        # Combinar todos los enrichments
        all_tips = []
        all_reviews = []
        contexts = []
        
        for enrichment in enrichments:
            all_tips.extend(enrichment.local_tips)
            all_reviews.extend(enrichment.critic_reviews)
            contexts.append(enrichment.cultural_context)
            
        # Crear evento enriquecido
        enriched = base_event.copy()
        enriched.update({
            # CONTEXTO CULTURAL HÍBRIDO
            "cultural_context": " | ".join(contexts),
            "local_insider_tips": list(set(all_tips)),  # Remove duplicates
            "critic_reviews": all_reviews,
            "vibe_description": enrichments[0].vibe_description if enrichments else "",
            "neighborhood_context": enrichments[0].neighborhood_info if enrichments else "",
            
            # METADATA HÍBRIDO  
            "enrichment_sources": len(enrichments),
            "enrichment_confidence": round(sum(e.confidence_score for e in enrichments) / len(enrichments), 2),
            "hybrid_score": self._calculate_hybrid_score(base_event, enrichments),
            
            # TAGS INTELIGENTES
            "smart_tags": self._generate_smart_tags(base_event, enrichments)
        })
        
        return enriched

    def _calculate_hybrid_score(self, base_event: Dict, enrichments: List[EventEnrichment]) -> float:
        """
        Calcular score de calidad híbrida (API + Context)
        """
        api_completeness = len([k for k in ['title', 'venue_name', 'start_datetime', 'price'] 
                               if base_event.get(k)])
        context_richness = len(enrichments)
        
        return min((api_completeness / 4) + (context_richness / 3), 1.0)

    def _generate_smart_tags(self, event: Dict, enrichments: List[EventEnrichment]) -> List[str]:
        """
        Generar tags inteligentes basados en API + contexto
        """
        tags = []
        
        # Tags de API
        if event.get('is_free'):
            tags.append("gratis")
        if event.get('price', 0) > 20000:
            tags.append("premium")
            
        # Tags de contexto
        for enrichment in enrichments:
            if "underground" in enrichment.vibe_description.lower():
                tags.append("underground")
            if "trendy" in enrichment.vibe_description.lower():
                tags.append("trendy")
            if "cultural" in enrichment.cultural_context.lower():
                tags.append("cultural")
                
        return list(set(tags))

# 🎯 FUNCIÓN PRINCIPAL DE ENRICHMENT
async def enrich_events_hybrid(events: List[Dict], country_code: str = "AR") -> List[Dict]:
    """
    Enriquecer lista de eventos con contexto híbrido
    """
    enricher = HybridEventEnricher()
    
    # Procesar en paralelo (máximo 5 a la vez para no sobrecargar)
    semaphore = asyncio.Semaphore(5)
    
    async def enrich_single(event):
        async with semaphore:
            return await enricher.enrich_event(event, country_code)
    
    tasks = [enrich_single(event) for event in events]
    enriched_events = await asyncio.gather(*tasks)
    
    return enriched_events