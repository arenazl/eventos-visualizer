"""
Smart Scraper Selector - Sistema híbrido inteligente
Combina detección rápida + IA contextual para elegir scrapers óptimos
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class Intent(Enum):
    GENERAL = "general"
    NIGHTLIFE = "nightlife"
    MUSIC = "music"
    SPORTS = "sports"
    CULTURAL = "cultural"
    FOOD = "food"
    BUSINESS = "business"
    ROMANTIC = "romantic"
    FAMILY = "family"

class ScraperSelector:
    """
    Sistema híbrido para seleccionar scrapers inteligentemente
    """
    
    def __init__(self):
        # 🗺️ SCRAPERS POR CIUDAD (O(1) lookup)
        self.SCRAPERS_BY_CITY = {
            # España
            "Barcelona": {
                "primary": ["barcelona_scraper"],
                "secondary": ["ticketmaster_global", "timeout_barcelona"],
                "specialties": {
                    Intent.NIGHTLIFE: ["barcelona_nightlife"],
                    Intent.MUSIC: ["primavera_sound", "razzmatazz"],
                    Intent.SPORTS: ["camp_nou_scraper"],
                    Intent.CULTURAL: ["palau_musica", "cccb_scraper"]
                }
            },
            "Madrid": {
                "primary": ["madrid_scraper"],
                "secondary": ["ticketmaster_global", "timeout_madrid"],
                "specialties": {
                    Intent.SPORTS: ["bernabeu_scraper", "wanda_scraper"],
                    Intent.MUSIC: ["wizink_center"],
                    Intent.CULTURAL: ["reina_sofia", "prado_scraper"]
                }
            },
            
            # Francia  
            "Paris": {
                "primary": ["paris_scraper"],
                "secondary": ["ticketmaster_global", "sortir_paris"],
                "specialties": {
                    Intent.CULTURAL: ["louvre_scraper", "orsay_scraper"],
                    Intent.MUSIC: ["olympia_scraper", "zenith_paris"],
                    Intent.SPORTS: ["parc_princes"]
                }
            },
            
            # Argentina
            "Buenos Aires": {
                "primary": ["argentina_venues_scraper", "oficial_venues_scraper"],
                "secondary": ["eventbrite_massive", "timeout_baires"],
                "specialties": {
                    Intent.SPORTS: ["luna_park", "estadio_obras"],
                    Intent.CULTURAL: ["teatro_colon", "ccr_scraper"],
                    Intent.MUSIC: ["niceto_club", "groove_scraper"]
                }
            },
            "Mendoza": {
                "primary": ["mendoza_scraper"],
                "secondary": ["provincial_scrapers"],
                "specialties": {
                    Intent.FOOD: ["bodegas_scraper", "wine_tours"]
                }
            },
            "Córdoba": {
                "primary": ["cordoba_scraper"],
                "secondary": ["provincial_scrapers"],
                "specialties": {
                    Intent.MUSIC: ["quality_espacio", "plaza_musica"]
                }
            },
            
            # México
            "Mexico City": {
                "primary": ["cdmx_scraper"],
                "secondary": ["ticketmaster_mexico", "timeout_cdmx"],
                "specialties": {
                    Intent.CULTURAL: ["palacio_bellas_artes", "antropologia"],
                    Intent.SPORTS: ["azteca_scraper", "foro_sol"]
                }
            }
        }
        
        # 🎯 INTENT DETECTION KEYWORDS
        self.INTENT_KEYWORDS = {
            Intent.NIGHTLIFE: ["bar", "club", "fiesta", "party", "discoteca", "night", "drinks", "copas"],
            Intent.MUSIC: ["concierto", "música", "concert", "band", "dj", "festival", "show"],
            Intent.SPORTS: ["fútbol", "football", "partido", "match", "deporte", "sport", "estadio"],
            Intent.CULTURAL: ["museo", "arte", "exposición", "culture", "gallery", "theater", "teatro"],
            Intent.FOOD: ["restaurante", "comida", "food", "wine", "vino", "gastronomy", "chef"],
            Intent.BUSINESS: ["networking", "conference", "business", "trabajo", "professional"],
            Intent.ROMANTIC: ["romántico", "romantic", "pareja", "date", "íntimo", "couple"],
            Intent.FAMILY: ["familia", "family", "kids", "niños", "children", "infantil"]
        }
        
        # 🌍 CITY ALIASES (más completo que antes)
        self.CITY_ALIASES = {
            # España
            "barcelona": "Barcelona", "bcn": "Barcelona", "barna": "Barcelona",
            "madrid": "Madrid", "capital españa": "Madrid",
            "valencia": "Valencia", "sevilla": "Sevilla",
            
            # Francia
            "paris": "Paris", "parís": "Paris", "ville lumière": "Paris",
            "lyon": "Lyon", "marseille": "Marseille",
            
            # Argentina
            "buenos aires": "Buenos Aires", "baires": "Buenos Aires", "caba": "Buenos Aires",
            "capital": "Buenos Aires", "ciudad autónoma": "Buenos Aires",
            "mendoza": "Mendoza", "mza": "Mendoza",
            "córdoba": "Córdoba", "cordoba": "Córdoba", "la docta": "Córdoba",
            
            # México
            "cdmx": "Mexico City", "ciudad de méxico": "Mexico City", "df": "Mexico City",
            "guadalajara": "Guadalajara", "gdl": "Guadalajara"
        }

    def analyze_query(self, query: str) -> Tuple[Optional[str], Intent, Dict[str, Any]]:
        """
        Analiza query y retorna: (ciudad, intent, contexto)
        """
        query_lower = query.lower().strip()
        
        # 1. 🏙️ DETECCIÓN DE CIUDAD (rápido)
        detected_city = self._detect_city(query_lower)
        
        # 2. 🎯 DETECCIÓN DE INTENT (keywords)  
        detected_intent = self._detect_intent(query_lower)
        
        # 3. 📊 CONTEXTO ADICIONAL
        context = self._extract_context(query_lower)
        
        logger.info(f"🧠 Query analysis: city='{detected_city}', intent='{detected_intent.value}', context={context}")
        
        return detected_city, detected_intent, context

    def select_scrapers(self, city: str, intent: Intent, context: Dict[str, Any] = None) -> List[str]:
        """
        Selecciona scrapers óptimos basado en ciudad + intent + contexto
        """
        if city not in self.SCRAPERS_BY_CITY:
            logger.warning(f"⚠️ Ciudad '{city}' no soportada, usando scrapers por defecto")
            return ["multi_source_scraper"]
        
        city_config = self.SCRAPERS_BY_CITY[city]
        selected_scrapers = []
        
        # 1. Scrapers primarios (siempre)
        selected_scrapers.extend(city_config["primary"])
        
        # 2. Scrapers especializados según intent
        if intent in city_config.get("specialties", {}):
            specialty_scrapers = city_config["specialties"][intent]
            selected_scrapers.extend(specialty_scrapers)
            logger.info(f"✨ Agregando scrapers especializados para {intent.value}: {specialty_scrapers}")
        
        # 3. Scrapers secundarios (si necesitamos más cobertura)
        context = context or {}
        if context.get("need_comprehensive", False) or len(selected_scrapers) < 2:
            selected_scrapers.extend(city_config.get("secondary", []))
        
        # 4. Eliminar duplicados y validar
        unique_scrapers = list(dict.fromkeys(selected_scrapers))  # Preserva orden
        
        logger.info(f"🎯 Selected scrapers for {city} ({intent.value}): {unique_scrapers}")
        
        return unique_scrapers

    def _detect_city(self, query_lower: str) -> Optional[str]:
        """
        Detección rápida de ciudad usando aliases
        """
        for alias, city in self.CITY_ALIASES.items():
            if alias in query_lower:
                logger.info(f"🏙️ Ciudad detectada: '{alias}' → {city}")
                return city
        return None

    def _detect_intent(self, query_lower: str) -> Intent:
        """
        Detección de intent usando keywords
        """
        intent_scores = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"🎯 Intent detectado: {best_intent.value} (score: {intent_scores[best_intent]})")
            return best_intent
        
        return Intent.GENERAL

    def _extract_context(self, query_lower: str) -> Dict[str, Any]:
        """
        Extrae contexto adicional del query
        """
        context = {}
        
        # Tiempo
        if any(word in query_lower for word in ["hoy", "today", "tonight", "esta noche"]):
            context["timeframe"] = "today"
        elif any(word in query_lower for word in ["mañana", "tomorrow"]):
            context["timeframe"] = "tomorrow"  
        elif any(word in query_lower for word in ["fin de semana", "weekend", "sábado", "domingo"]):
            context["timeframe"] = "weekend"
        
        # Presupuesto
        if any(word in query_lower for word in ["barato", "cheap", "gratis", "free", "sin plata"]):
            context["budget"] = "low"
        elif any(word in query_lower for word in ["premium", "caro", "luxury", "expensive"]):
            context["budget"] = "high"
        
        # Social context
        if any(word in query_lower for word in ["solo", "alone", "individual"]):
            context["social"] = "solo"
        elif any(word in query_lower for word in ["amigos", "friends", "grupo"]):
            context["social"] = "group"
        elif any(word in query_lower for word in ["pareja", "couple", "novia", "novio"]):
            context["social"] = "couple"
        
        # Comprehensiveness
        if any(word in query_lower for word in ["todo", "all", "completo", "comprehensive"]):
            context["need_comprehensive"] = True
        
        return context

    def get_available_cities(self) -> List[str]:
        """
        Retorna lista de ciudades soportadas
        """
        return list(self.SCRAPERS_BY_CITY.keys())

    def get_city_specialties(self, city: str) -> Dict[str, List[str]]:
        """
        Retorna especialidades disponibles para una ciudad
        """
        if city not in self.SCRAPERS_BY_CITY:
            return {}
        
        specialties = {}
        city_specialties = self.SCRAPERS_BY_CITY[city].get("specialties", {})
        
        for intent, scrapers in city_specialties.items():
            specialties[intent.value] = scrapers
        
        return specialties


# 🧪 Testing functions
def test_scraper_selector():
    """
    Prueba el selector de scrapers
    """
    selector = ScraperSelector()
    
    test_queries = [
        "eventos en barcelona",
        "conciertos en madrid este fin de semana", 
        "bares copados en barna para ir con amigos",
        "museos en paris para una cita romántica",
        "partidos de fútbol en buenos aires",
        "algo barato en mendoza para hacer solo",
        "eventos premium en cdmx"
    ]
    
    print("🧠 Testing Smart Scraper Selector...")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        city, intent, context = selector.analyze_query(query)
        scrapers = selector.select_scrapers(city or "Buenos Aires", intent, context)
        
        print(f"   🏙️ City: {city or 'None (default: Buenos Aires)'}")
        print(f"   🎯 Intent: {intent.value}")
        print(f"   📊 Context: {context}")
        print(f"   🔧 Scrapers: {scrapers}")

if __name__ == "__main__":
    test_scraper_selector()