"""
🔍 Detector Automático de Fuentes Faltantes
Analiza búsquedas sin resultados para identificar oportunidades de nuevas fuentes de datos
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import json
import asyncio
import aiomysql
from collections import defaultdict, Counter

class GapType(Enum):
    CATEGORY_GAP = "category_gap"       # Falta una categoría completa
    LOCATION_GAP = "location_gap"       # Falta cobertura en una ciudad
    VENUE_GAP = "venue_gap"             # Venue específico no cubierto
    PRICE_GAP = "price_gap"             # Rango de precios sin cobertura
    DATE_GAP = "date_gap"               # Fechas específicas sin eventos
    LANGUAGE_GAP = "language_gap"       # Eventos en otro idioma
    SOURCE_GAP = "source_gap"           # Fuente específica identificada

class Priority(Enum):
    CRITICAL = "critical"    # 🔥 Implementar ASAP
    HIGH = "high"           # 📈 Próximo sprint
    MEDIUM = "medium"       # 📋 Backlog prioritario  
    LOW = "low"             # 💡 Futuro

@dataclass
class DataGap:
    gap_type: GapType
    description: str
    search_queries: List[str]           # Queries que no tuvieron resultados
    frequency: int                      # Cuántas veces se buscó
    last_searched: datetime
    suggested_sources: List[str]        # Fuentes recomendadas
    priority: Priority
    potential_impact: float             # 0.0 - 1.0 impacto estimado
    implementation_effort: int          # 1-10 dificultad
    roi_score: float = field(init=False) # Auto-calculado

    def __post_init__(self):
        # ROI = Impacto / Esfuerzo * Frecuencia
        self.roi_score = (self.potential_impact / max(self.implementation_effort, 1)) * min(self.frequency / 10, 2.0)

class SourceGapDetector:
    def __init__(self):
        self.detected_gaps: List[DataGap] = []
        self.query_patterns = {
            # CATEGORÍAS
            "teatro": ["alternativa_teatral", "teatroenweb", "complejoteatral"],
            "vinos": ["passline", "winelovers", "vinosdemaipú"], 
            "gastronomía": ["zomato_events", "opentable_events"],
            "arte": ["museos_argentina", "galerías_palermo"],
            "tango": ["milongas_ba", "tangocity", "2x4tango"],
            "fútbol": ["afa_oficial", "olé_agenda", "tycsports"],
            "teatro independiente": ["alternativa_teatral", "teatrix"],
            "música clásica": ["teatro_colon", "usina_del_arte"],
            "jazz": ["blue_note", "jazz_clubs_ba"],
            "electrónica": ["resident_advisor", "clubbing_argentina"],
            
            # UBICACIONES  
            "córdoba": ["córdoba_turismo", "via_cordoba"],
            "rosario": ["rosario_eventos", "la_capital"],
            "mendoza": ["mendoza_turismo", "diario_uno"],
            "bariloche": ["bariloche_eventos", "andina_turismo"],
            "mar del plata": ["mdp_eventos", "0223_agenda"],
            "salta": ["salta_eventos", "el_tribuno"],
            
            # VENUES ESPECÍFICOS
            "estadio river": ["river_oficial", "ticketek_river"],
            "estadio boca": ["boca_oficial", "ticketek_boca"], 
            "luna park": ["luna_park_oficial"],
            "teatro colón": ["teatro_colon_oficial"],
            "hipódromo": ["hipodromo_palermo", "jockey_club"],
            
            # TIPOS DE EVENTOS
            "eventos gratuitos": ["gobierno_caba", "universidades_ba"],
            "eventos premium": ["palermo_magazine", "exclusive_events"],
            "eventos familiares": ["pequeños_grandes", "family_events"],
            "workshops": ["meetup_ar", "eventbrite_workshops"],
            "conferencias": ["eventbrite_tech", "tech_meetups"]
        }
        
        # Fuentes conocidas en Argentina
        self.argentina_sources = {
            "ticketing": ["ticketek", "plateanet", "tuentrada", "passline"],
            "cultura": ["alternativa_teatral", "teatro_colon", "usina_del_arte"],
            "música": ["resident_advisor", "songkick", "bandsintown"],
            "deportes": ["afa_oficial", "tycsports", "olé"],
            "gastronomía": ["zomato", "opentable", "restorando"],
            "gobierno": ["buenosaires.gob.ar", "cultura.gov.ar"],
            "medios": ["lanacion", "clarin", "timeout", "whats_up"]
        }

    async def analyze_failed_searches(self, days_back: int = 7) -> List[DataGap]:
        """
        Analizar búsquedas fallidas de los últimos N días
        """
        from main_mysql import pool
        
        gaps = []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    
                    # Simulamos tabla de búsquedas (agregarla al schema después)
                    query = """
                        SELECT 
                            query, location, COUNT(*) as frequency,
                            MAX(searched_at) as last_searched
                        FROM failed_searches 
                        WHERE searched_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        AND results_count = 0
                        GROUP BY query, location
                        ORDER BY frequency DESC
                        LIMIT 50
                    """
                    
                    # Por ahora simulamos data para el ejemplo
                    simulated_failed_searches = [
                        ("teatro independiente palermo", "Buenos Aires", 15, datetime.now()),
                        ("vinos cata mendoza", "Mendoza", 12, datetime.now()),
                        ("conciertos jazz", "Buenos Aires", 8, datetime.now()),
                        ("eventos gratuitos familia", "Buenos Aires", 25, datetime.now()),
                        ("fútbol river boca", "Buenos Aires", 20, datetime.now()),
                        ("tango milonga principiantes", "Buenos Aires", 10, datetime.now()),
                        ("eventos córdoba", "Córdoba", 18, datetime.now()),
                        ("workshops tech", "Buenos Aires", 14, datetime.now())
                    ]
                    
                    for query, location, frequency, last_searched in simulated_failed_searches:
                        gap = await self._analyze_single_query_gap(query, location, frequency, last_searched)
                        if gap:
                            gaps.append(gap)
                    
        except Exception as e:
            print(f"Error analyzing failed searches: {e}")
        
        self.detected_gaps = gaps
        return gaps

    async def _analyze_single_query_gap(self, query: str, location: str, frequency: int, last_searched: datetime) -> Optional[DataGap]:
        """
        Analizar una query específica para detectar gaps
        """
        query_lower = query.lower()
        
        # 1. DETECTAR TIPO DE GAP
        gap_type, suggested_sources = self._identify_gap_type(query_lower)
        
        if not suggested_sources:
            return None
            
        # 2. CALCULAR PRIORIDAD
        priority = self._calculate_priority(frequency, gap_type)
        
        # 3. ESTIMAR IMPACTO Y ESFUERZO
        impact = self._estimate_impact(query_lower, frequency, location)
        effort = self._estimate_effort(suggested_sources)
        
        # 4. CREAR GAP
        return DataGap(
            gap_type=gap_type,
            description=f"Gap detectado: '{query}' en {location}",
            search_queries=[query],
            frequency=frequency,
            last_searched=last_searched,
            suggested_sources=suggested_sources,
            priority=priority,
            potential_impact=impact,
            implementation_effort=effort
        )

    def _identify_gap_type(self, query: str) -> Tuple[GapType, List[str]]:
        """
        Identificar tipo de gap y fuentes sugeridas
        """
        # Buscar coincidencias en patrones conocidos
        for category, sources in self.query_patterns.items():
            if category in query:
                return GapType.CATEGORY_GAP, sources
                
        # Detectar gaps de ubicación
        locations = ["córdoba", "rosario", "mendoza", "bariloche", "mar del plata", "salta"]
        for location in locations:
            if location in query:
                return GapType.LOCATION_GAP, self.query_patterns.get(location, [])
        
        # Detectar gaps de venues
        if any(venue in query for venue in ["estadio", "teatro", "club", "centro cultural"]):
            return GapType.VENUE_GAP, ["venue_specific_apis"]
            
        # Detectar gaps de precio
        if any(price in query for price in ["gratis", "barato", "premium", "exclusivo"]):
            return GapType.PRICE_GAP, ["specialized_pricing_sources"]
            
        return GapType.SOURCE_GAP, ["general_sources"]

    def _calculate_priority(self, frequency: int, gap_type: GapType) -> Priority:
        """
        Calcular prioridad basada en frecuencia y tipo
        """
        if frequency >= 20:
            return Priority.CRITICAL
        elif frequency >= 10:
            return Priority.HIGH
        elif frequency >= 5:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def _estimate_impact(self, query: str, frequency: int, location: str) -> float:
        """
        Estimar impacto potencial (0.0 - 1.0)
        """
        base_impact = min(frequency / 30, 0.8)  # Máximo 0.8 por frecuencia
        
        # Bonus por categorías populares
        if any(cat in query for cat in ["música", "teatro", "fútbol", "eventos gratuitos"]):
            base_impact += 0.2
            
        # Bonus por ubicaciones principales
        if location in ["Buenos Aires", "Córdoba", "Rosario"]:
            base_impact += 0.1
            
        return min(base_impact, 1.0)

    def _estimate_effort(self, sources: List[str]) -> int:
        """
        Estimar esfuerzo de implementación (1-10)
        """
        effort_map = {
            "api": 3,           # API oficial fácil
            "scraping": 5,      # Web scraping medio
            "complex": 8,       # Fuente compleja
            "manual": 10        # Proceso manual
        }
        
        # Por ahora estimación simple
        if len(sources) == 1:
            return 3
        elif len(sources) <= 3:
            return 5
        else:
            return 7

    def generate_implementation_plan(self) -> Dict:
        """
        Generar plan de implementación priorizado
        """
        if not self.detected_gaps:
            return {"message": "No gaps detected"}
            
        # Ordenar por ROI score
        sorted_gaps = sorted(self.detected_gaps, key=lambda x: x.roi_score, reverse=True)
        
        plan = {
            "summary": {
                "total_gaps": len(sorted_gaps),
                "critical": len([g for g in sorted_gaps if g.priority == Priority.CRITICAL]),
                "high": len([g for g in sorted_gaps if g.priority == Priority.HIGH]),
                "estimated_user_impact": sum(g.potential_impact * g.frequency for g in sorted_gaps)
            },
            "next_sprint": [],
            "backlog": [],
            "source_recommendations": defaultdict(list)
        }
        
        for gap in sorted_gaps[:5]:  # Top 5 por ROI
            gap_info = {
                "description": gap.description,
                "queries": gap.search_queries,
                "frequency": gap.frequency,
                "roi_score": round(gap.roi_score, 2),
                "suggested_sources": gap.suggested_sources,
                "priority": gap.priority.value,
                "estimated_effort": f"{gap.implementation_effort}/10"
            }
            
            if gap.priority in [Priority.CRITICAL, Priority.HIGH]:
                plan["next_sprint"].append(gap_info)
            else:
                plan["backlog"].append(gap_info)
                
            # Agrupar por fuente recomendada
            for source in gap.suggested_sources:
                plan["source_recommendations"][source].append({
                    "gap": gap.description,
                    "frequency": gap.frequency
                })
        
        return plan

    def get_top_missing_sources(self) -> List[Dict]:
        """
        Obtener las fuentes más necesarias
        """
        source_impact = defaultdict(float)
        source_frequency = defaultdict(int)
        
        for gap in self.detected_gaps:
            for source in gap.suggested_sources:
                source_impact[source] += gap.roi_score
                source_frequency[source] += gap.frequency
                
        top_sources = []
        for source, impact in sorted(source_impact.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_sources.append({
                "source": source,
                "total_impact": round(impact, 2),
                "total_queries": source_frequency[source],
                "avg_impact": round(impact / max(source_frequency[source], 1), 2)
            })
            
        return top_sources

# 🎯 ENDPOINT PARA ANÁLISIS
async def analyze_data_gaps() -> Dict:
    """
    Función principal para análizar gaps de datos
    """
    detector = SourceGapDetector()
    
    # Analizar búsquedas fallidas
    gaps = await detector.analyze_failed_searches(days_back=7)
    
    # Generar plan
    implementation_plan = detector.generate_implementation_plan()
    
    # Top fuentes faltantes
    missing_sources = detector.get_top_missing_sources()
    
    return {
        "analysis_date": datetime.now().isoformat(),
        "gaps_detected": len(gaps),
        "implementation_plan": implementation_plan,
        "top_missing_sources": missing_sources,
        "recommendations": {
            "immediate_action": "Implementar fuentes CRITICAL priority",
            "next_week": "Evaluar fuentes HIGH priority", 
            "next_month": "Planificar fuentes MEDIUM priority"
        }
    }