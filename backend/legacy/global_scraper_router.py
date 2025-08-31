"""
🌍 GLOBAL SCRAPER ROUTER - Sistema Híbrido para Escalabilidad Mundial
Combina lógica determinística + IA contextual para routing inteligente de scrapers
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapingStrategy(Enum):
    """Estrategias de scraping disponibles"""
    NATIVE_SITES = "native_sites"          # Sitios locales nativos
    GLOBAL_APIS = "global_apis"           # APIs globales (Eventbrite, Ticketmaster)
    SOCIAL_MEDIA = "social_media"         # Facebook, Instagram, Twitter
    VENUE_DIRECT = "venue_direct"         # Scraping directo de venues
    AGGREGATORS = "aggregators"           # Agregadores locales
    CULTURAL_INST = "cultural_institutions"  # Instituciones culturales oficiales

@dataclass
class CountryConfig:
    """Configuración completa por país"""
    name: str
    iso_code: str  # AR, ES, FR, MX, etc.
    main_language: str
    currency: str
    timezone: str
    
    # Strategies disponibles por orden de prioridad
    primary_strategies: List[ScrapingStrategy]
    fallback_strategies: List[ScrapingStrategy]
    
    # Scrapers específicos por estrategia
    scrapers_by_strategy: Dict[ScrapingStrategy, List[str]]
    
    # City-specific overrides
    city_overrides: Dict[str, Dict[str, Any]] = None
    
    # Cultural context for IA decision-making
    cultural_context: Dict[str, Any] = None
    
    def __post_init__(self):
        self.city_overrides = self.city_overrides or {}
        self.cultural_context = self.cultural_context or {}

class GlobalScraperRouter:
    """
    🌍 Router Global Inteligente
    
    FILOSOFÍA:
    - Switch determinístico para decisiones rápidas O(1)
    - IA contextual para casos complejos y aprendizaje
    - Fallbacks automáticos por país/región
    - Optimización continua basada en performance
    """
    
    def __init__(self):
        # 🗺️ CONFIGURACIÓN POR PAÍSES (Expandible)
        self.COUNTRIES = {
            "AR": CountryConfig(
                name="Argentina",
                iso_code="AR", 
                main_language="es",
                currency="ARS",
                timezone="America/Argentina/Buenos_Aires",
                primary_strategies=[
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.VENUE_DIRECT,
                    ScrapingStrategy.CULTURAL_INST
                ],
                fallback_strategies=[
                    ScrapingStrategy.GLOBAL_APIS,
                    ScrapingStrategy.SOCIAL_MEDIA
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.NATIVE_SITES: [
                        "argentina_venues_scraper",
                        "timeout_baires_scraper", 
                        "alternativa_teatral_scraper"
                    ],
                    ScrapingStrategy.VENUE_DIRECT: [
                        "luna_park_scraper",
                        "teatro_colon_scraper",
                        "estadio_obras_scraper"
                    ],
                    ScrapingStrategy.CULTURAL_INST: [
                        "ccr_scraper",
                        "malba_scraper",
                        "usina_arte_scraper"
                    ],
                    ScrapingStrategy.GLOBAL_APIS: [
                        "eventbrite_argentina",
                        "ticketmaster_argentina"
                    ],
                    ScrapingStrategy.SOCIAL_MEDIA: [
                        "rapidapi_facebook_scraper"
                    ]
                },
                city_overrides={
                    "Buenos Aires": {
                        "add_scrapers": ["provincial_scrapers"],
                        "boost_strategy": ScrapingStrategy.VENUE_DIRECT
                    },
                    "Mendoza": {
                        "primary_scrapers": ["mendoza_wine_scraper", "provincial_scrapers"],
                        "specialty": "wine_tourism"
                    },
                    "Córdoba": {
                        "primary_scrapers": ["cordoba_universities_scraper", "provincial_scrapers"], 
                        "specialty": "student_life"
                    }
                },
                cultural_context={
                    "event_types": ["tango", "fútbol", "asado", "folklore", "rock_nacional"],
                    "peak_times": ["19:00-02:00"], 
                    "social_style": "group_oriented",
                    "budget_sensitivity": "high"
                }
            ),
            
            "ES": CountryConfig(
                name="España",
                iso_code="ES",
                main_language="es", 
                currency="EUR",
                timezone="Europe/Madrid",
                primary_strategies=[
                    ScrapingStrategy.GLOBAL_APIS,
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.CULTURAL_INST
                ],
                fallback_strategies=[
                    ScrapingStrategy.VENUE_DIRECT,
                    ScrapingStrategy.SOCIAL_MEDIA
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.GLOBAL_APIS: [
                        "ticketmaster_spain_scraper",
                        "eventbrite_spain_scraper"
                    ],
                    ScrapingStrategy.NATIVE_SITES: [
                        "timeout_madrid_scraper",
                        "atrapalo_madrid_scraper",
                        "madrid_oficial_scraper"
                    ],
                    ScrapingStrategy.CULTURAL_INST: [
                        "prado_museo_scraper",
                        "reina_sofia_scraper", 
                        "teatro_real_scraper"
                    ],
                    ScrapingStrategy.VENUE_DIRECT: [
                        "wizink_center_scraper",
                        "palacio_deportes_scraper"
                    ]
                },
                city_overrides={
                    "Barcelona": {
                        "specialty": "cosmopolitan_culture",
                        "boost_strategy": ScrapingStrategy.CULTURAL_INST,
                        "add_scrapers": ["timeout_barcelona_scraper", "palau_musica_scraper"]
                    },
                    "Madrid": {
                        "specialty": "capital_culture", 
                        "boost_strategy": ScrapingStrategy.GLOBAL_APIS,
                        "primary_scrapers": ["ticketmaster_spain_scraper", "timeout_madrid_scraper", "atrapalo_madrid_scraper"]
                    }
                },
                cultural_context={
                    "event_types": ["flamenco", "fútbol", "tapas_tours", "art_galleries", "teatro_musical", "conciertos_pop"],
                    "peak_times": ["21:00-03:00"],
                    "social_style": "late_night_culture",
                    "budget_sensitivity": "medium",
                    "local_habits": ["siesta_afternoon", "dinner_after_22", "nightlife_starts_midnight"],
                    "tourist_tips": ["museums_free_evenings", "metro_closes_2am", "cash_preferred_bars"]
                }
            ),
            
            "MX": CountryConfig(
                name="México",
                iso_code="MX",
                main_language="es",
                currency="MXN", 
                timezone="America/Mexico_City",
                primary_strategies=[
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.GLOBAL_APIS,
                    ScrapingStrategy.VENUE_DIRECT
                ],
                fallback_strategies=[
                    ScrapingStrategy.CULTURAL_INST,
                    ScrapingStrategy.SOCIAL_MEDIA
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.NATIVE_SITES: [
                        "timeout_cdmx_scraper",
                        "chilango_scraper"
                    ],
                    ScrapingStrategy.GLOBAL_APIS: [
                        "ticketmaster_mexico", 
                        "eventbrite_mexico"
                    ],
                    ScrapingStrategy.VENUE_DIRECT: [
                        "foro_sol_scraper",
                        "auditorio_nacional_scraper"
                    ]
                },
                cultural_context={
                    "event_types": ["mariachi", "lucha_libre", "día_muertos", "food_festivals"],
                    "peak_times": ["20:00-02:00"],
                    "social_style": "family_group_oriented", 
                    "budget_sensitivity": "high"
                }
            ),
            
            "FR": CountryConfig(
                name="Francia", 
                iso_code="FR",
                main_language="fr",
                currency="EUR",
                timezone="Europe/Paris",
                primary_strategies=[
                    ScrapingStrategy.CULTURAL_INST,
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.GLOBAL_APIS
                ],
                fallback_strategies=[
                    ScrapingStrategy.VENUE_DIRECT
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.CULTURAL_INST: [
                        "louvre_scraper",
                        "orsay_scraper",
                        "centre_pompidou_scraper"
                    ],
                    ScrapingStrategy.NATIVE_SITES: [
                        "timeout_paris_scraper",
                        "sortiraparis_scraper"
                    ],
                    ScrapingStrategy.GLOBAL_APIS: [
                        "eventbrite_france",
                        "ticketmaster_france"
                    ]
                },
                cultural_context={
                    "event_types": ["wine_tastings", "art_exhibitions", "classical_music", "fashion"],
                    "peak_times": ["19:00-00:00"],
                    "social_style": "sophisticated_culture",
                    "budget_sensitivity": "low"
                }
            ),
            
            "BR": CountryConfig(
                name="Brasil",
                iso_code="BR",
                main_language="pt", 
                currency="BRL",
                timezone="America/Sao_Paulo",
                primary_strategies=[
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.GLOBAL_APIS,
                    ScrapingStrategy.VENUE_DIRECT
                ],
                fallback_strategies=[
                    ScrapingStrategy.SOCIAL_MEDIA,
                    ScrapingStrategy.CULTURAL_INST
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.NATIVE_SITES: [
                        "sympla_scraper",
                        "ingresse_scraper",
                        "eventim_brasil_scraper"
                    ],
                    ScrapingStrategy.GLOBAL_APIS: [
                        "eventbrite_brasil_scraper",
                        "ticketmaster_brasil_scraper"
                    ],
                    ScrapingStrategy.VENUE_DIRECT: [
                        "allianz_parque_scraper",
                        "morumbi_stadium_scraper", 
                        "via_funchal_scraper"
                    ],
                    ScrapingStrategy.CULTURAL_INST: [
                        "pinacoteca_sp_scraper",
                        "masp_scraper",
                        "memorial_america_latina_scraper"
                    ]
                },
                city_overrides={
                    "São Paulo": {
                        "specialty": "megacity_nightlife",
                        "boost_strategy": ScrapingStrategy.NATIVE_SITES,
                        "primary_scrapers": ["sympla_scraper", "ingresse_scraper", "eventbrite_brasil_scraper"]
                    },
                    "Rio de Janeiro": {
                        "specialty": "carnival_culture",
                        "boost_strategy": ScrapingStrategy.VENUE_DIRECT,
                        "add_scrapers": ["rio_venues_scraper", "copacabana_events_scraper"]
                    }
                },
                cultural_context={
                    "event_types": ["samba", "forró", "futebol", "festa_junina", "capoeira", "pagode", "funk_carioca", "axé"],
                    "peak_times": ["22:00-05:00"],
                    "social_style": "carnival_energy",
                    "budget_sensitivity": "high",
                    "local_habits": ["festa_starts_late", "carnival_spirit", "beach_events", "churrasco_gatherings"],
                    "tourist_tips": ["cash_preferred", "uber_safer_nights", "events_run_very_late", "dress_casual_colorful"]
                }
            ),
            
            "US": CountryConfig(
                name="United States",
                iso_code="US",
                main_language="en",
                currency="USD",
                timezone="America/New_York",  # Eastern time (más común)
                primary_strategies=[
                    ScrapingStrategy.NATIVE_SITES,
                    ScrapingStrategy.GLOBAL_APIS,
                    ScrapingStrategy.VENUE_DIRECT
                ],
                fallback_strategies=[
                    ScrapingStrategy.CULTURAL_INST,
                    ScrapingStrategy.SOCIAL_MEDIA
                ],
                scrapers_by_strategy={
                    ScrapingStrategy.NATIVE_SITES: [
                        "timeout_miami_scraper",
                        "timeout_nyc_scraper",
                        "timeout_la_scraper"
                    ],
                    ScrapingStrategy.GLOBAL_APIS: [
                        "eventbrite_usa_scraper",
                        "ticketmaster_usa_scraper",
                        "stubhub_scraper"
                    ],
                    ScrapingStrategy.VENUE_DIRECT: [
                        "madison_square_garden_scraper",
                        "american_airlines_arena_scraper",
                        "staples_center_scraper"
                    ],
                    ScrapingStrategy.CULTURAL_INST: [
                        "met_museum_scraper",
                        "moma_scraper",
                        "kennedy_center_scraper"
                    ]
                },
                city_overrides={
                    "Miami": {
                        "specialty": "beach_nightlife_culture",
                        "boost_strategy": ScrapingStrategy.NATIVE_SITES,
                        "primary_scrapers": ["miami_scraper", "timeout_miami_scraper", "eventbrite_miami_scraper"],
                        "timezone": "America/New_York"  # Eastern time para Miami
                    },
                    "New York": {
                        "specialty": "world_class_entertainment",
                        "boost_strategy": ScrapingStrategy.VENUE_DIRECT,
                        "add_scrapers": ["broadway_scraper", "lincoln_center_scraper"]
                    },
                    "Los Angeles": {
                        "specialty": "entertainment_industry",
                        "boost_strategy": ScrapingStrategy.GLOBAL_APIS,
                        "add_scrapers": ["hollywood_bowl_scraper", "staples_center_scraper"]
                    }
                },
                cultural_context={
                    "event_types": ["concerts", "sports", "broadway", "festivals", "nightlife", "art_galleries", "food_festivals", "beach_parties"],
                    "peak_times": ["19:00-02:00"],
                    "social_style": "diverse_metropolitan",
                    "budget_sensitivity": "medium",
                    "local_habits": ["dinner_early_evening", "nightlife_varies_by_city", "tipping_culture"],
                    "tourist_tips": ["tickets_expensive", "uber_common", "events_start_on_time", "credit_cards_preferred"]
                }
            )
        }
        
        # 🏙️ MAPPING: CIUDAD → PAÍS
        self.CITY_TO_COUNTRY = {
            # Argentina
            "Buenos Aires": "AR", "CABA": "AR", "Capital Federal": "AR",
            "Mendoza": "AR", "Córdoba": "AR", "Rosario": "AR", "La Plata": "AR",
            
            # España  
            "Madrid": "ES", "Barcelona": "ES", "Valencia": "ES", "Sevilla": "ES",
            "Bilbao": "ES", "Zaragoza": "ES", "Málaga": "ES",
            
            # México
            "Mexico City": "MX", "CDMX": "MX", "Ciudad de México": "MX", 
            "Guadalajara": "MX", "Monterrey": "MX", "Cancún": "MX",
            
            # Francia
            "Paris": "FR", "Lyon": "FR", "Marseille": "FR", "Nice": "FR",
            
            # Brasil 🇧🇷
            "São Paulo": "BR", "Sao Paulo": "BR", "SP": "BR",
            "Rio de Janeiro": "BR", "Rio": "BR", "RJ": "BR", 
            "Brasília": "BR", "Salvador": "BR", "Belo Horizonte": "BR",
            
            # Estados Unidos 🇺🇸
            "Miami": "US", "Miami Beach": "US", "South Beach": "US",
            "New York": "US", "NYC": "US", "Los Angeles": "US", "LA": "US",
            "Chicago": "US", "Las Vegas": "US", "San Francisco": "US"
        }
        
        # 📊 Performance tracking
        self.scraper_performance = {}
        self.ai_suggestions_accepted = {}

    async def route_scrapers(self, 
                           location: str,
                           intent: str = "general",
                           context: Dict[str, Any] = None,
                           use_ai_suggestions: bool = True) -> Dict[str, Any]:
        """
        🎯 MÉTODO PRINCIPAL: Ruteo Inteligente de Scrapers
        
        Args:
            location: Ciudad/país solicitado
            intent: Intención del usuario (música, cultura, deportes, etc.)
            context: Contexto adicional (presupuesto, horario, etc.)
            use_ai_suggestions: Si usar IA para optimización contextual
        
        Returns:
            Dict con scrapers seleccionados, estrategias y metadata
        """
        
        logger.info(f"🌍 Routing scrapers for location='{location}', intent='{intent}'")
        
        # 1. 🗺️ DETECCIÓN DE PAÍS/CIUDAD (Determinístico - O(1))
        country_code, city_name = self._detect_country_city(location)
        
        if country_code not in self.COUNTRIES:
            logger.warning(f"⚠️ País no soportado: {country_code}, usando fallback global")
            return await self._global_fallback_routing(location, intent, context)
        
        country_config = self.COUNTRIES[country_code]
        logger.info(f"🎯 País detectado: {country_config.name}")
        
        # 2. 🎯 SELECCIÓN DETERMINÍSTICA DE ESTRATEGIAS
        base_strategies = self._select_base_strategies(
            country_config, city_name, intent, context
        )
        
        # 3. 🧠 OPTIMIZACIÓN CON IA (Si está habilitada)
        if use_ai_suggestions:
            base_strategies = await self._ai_optimize_strategies(
                base_strategies, country_config, city_name, intent, context
            )
        
        # 4. 🔧 MAPEO A SCRAPERS ESPECÍFICOS
        selected_scrapers = self._map_strategies_to_scrapers(
            base_strategies, country_config, city_name
        )
        
        # 5. 📊 RESULTADO FINAL
        routing_result = {
            "location": {
                "detected_country": country_config.name,
                "country_code": country_code,
                "city": city_name,
                "original_query": location
            },
            "selected_scrapers": selected_scrapers,
            "strategies_used": [s.value for s in base_strategies],
            "execution_order": self._optimize_execution_order(selected_scrapers),
            "fallback_scrapers": self._get_fallback_scrapers(country_config),
            "estimated_coverage": self._estimate_coverage(country_config, base_strategies),
            "cultural_context": country_config.cultural_context,
            "routing_metadata": {
                "routing_time": datetime.now().isoformat(),
                "ai_enhanced": use_ai_suggestions,
                "confidence_score": 0.95 if country_code in self.COUNTRIES else 0.7
            }
        }
        
        logger.info(f"✅ Routing completed: {len(selected_scrapers)} scrapers selected")
        return routing_result
    
    def _detect_country_city(self, location: str) -> Tuple[str, Optional[str]]:
        """
        🗺️ Detección rápida país/ciudad - O(1) lookup
        """
        location_clean = location.strip().title()
        
        # Direct city lookup
        if location_clean in self.CITY_TO_COUNTRY:
            country_code = self.CITY_TO_COUNTRY[location_clean]
            return country_code, location_clean
        
        # Fuzzy matching para ciudades
        for city, country in self.CITY_TO_COUNTRY.items():
            if city.lower() in location.lower() or location.lower() in city.lower():
                return country, city
        
        # Country-only detection
        for country_code, config in self.COUNTRIES.items():
            if config.name.lower() in location.lower():
                return country_code, None
        
        # Default fallback
        logger.warning(f"🚫 No se pudo detectar país para: {location}")
        return "AR", None  # Default to Argentina
    
    def _select_base_strategies(self, 
                               country_config: CountryConfig,
                               city_name: Optional[str], 
                               intent: str,
                               context: Dict[str, Any]) -> List[ScrapingStrategy]:
        """
        🎯 Selección determinística de estrategias base
        """
        strategies = country_config.primary_strategies.copy()
        
        # City-specific overrides
        if city_name and city_name in country_config.city_overrides:
            city_override = country_config.city_overrides[city_name]
            if "boost_strategy" in city_override:
                boost_strategy = city_override["boost_strategy"]
                if boost_strategy not in strategies:
                    strategies.insert(0, boost_strategy)
        
        # Intent-based modifications
        if intent in ["cultura", "art", "museums"]:
            if ScrapingStrategy.CULTURAL_INST not in strategies:
                strategies.insert(1, ScrapingStrategy.CULTURAL_INST)
        elif intent in ["sports", "fútbol", "deportes"]:
            if ScrapingStrategy.VENUE_DIRECT not in strategies:
                strategies.insert(1, ScrapingStrategy.VENUE_DIRECT)
        
        # Context-based modifications
        if context and context.get("comprehensive", False):
            strategies.extend(country_config.fallback_strategies)
        
        return strategies[:4]  # Limit to top 4 strategies
    
    async def _ai_optimize_strategies(self, 
                                    base_strategies: List[ScrapingStrategy],
                                    country_config: CountryConfig,
                                    city_name: Optional[str],
                                    intent: str, 
                                    context: Dict[str, Any]) -> List[ScrapingStrategy]:
        """
        🧠 IA contextual para optimizar estrategias
        (Placeholder - aquí integrarías con Gemini Brain)
        """
        
        # Por ahora, lógica heurística inteligente
        # En producción, llamarías a Gemini Brain
        
        logger.info("🧠 AI optimization triggered")
        
        # Ejemplo de optimización contextual:
        if context and context.get("budget") == "low":
            # Priorizar estrategias gratuitas
            free_strategies = [ScrapingStrategy.CULTURAL_INST, ScrapingStrategy.SOCIAL_MEDIA]
            optimized = [s for s in free_strategies if s in base_strategies]
            optimized.extend([s for s in base_strategies if s not in free_strategies])
            return optimized
        
        return base_strategies
    
    def _map_strategies_to_scrapers(self, 
                                  strategies: List[ScrapingStrategy],
                                  country_config: CountryConfig, 
                                  city_name: Optional[str]) -> List[str]:
        """
        🔧 Mapeo de estrategias a scrapers específicos
        """
        selected_scrapers = []
        
        for strategy in strategies:
            if strategy in country_config.scrapers_by_strategy:
                scrapers = country_config.scrapers_by_strategy[strategy]
                selected_scrapers.extend(scrapers)
        
        # City-specific additions
        if city_name and city_name in country_config.city_overrides:
            city_override = country_config.city_overrides[city_name]
            if "add_scrapers" in city_override:
                selected_scrapers.extend(city_override["add_scrapers"])
            if "primary_scrapers" in city_override:
                # Prepend city-specific scrapers
                selected_scrapers = city_override["primary_scrapers"] + selected_scrapers
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(selected_scrapers))
    
    def _optimize_execution_order(self, scrapers: List[str]) -> List[str]:
        """
        📊 Optimiza orden de ejecución basado en performance histórica
        """
        # Ordenar por performance (scrapers más rápidos/exitosos primero)
        def scraper_priority(scraper):
            performance = self.scraper_performance.get(scraper, {"avg_time": 5.0, "success_rate": 0.8})
            # Prioridad = velocidad * success rate
            return performance["success_rate"] / performance["avg_time"]
        
        return sorted(scrapers, key=scraper_priority, reverse=True)
    
    def _get_fallback_scrapers(self, country_config: CountryConfig) -> List[str]:
        """
        🛡️ Scrapers de fallback en caso de fallos
        """
        fallback_scrapers = []
        for strategy in country_config.fallback_strategies:
            if strategy in country_config.scrapers_by_strategy:
                fallback_scrapers.extend(country_config.scrapers_by_strategy[strategy])
        return list(dict.fromkeys(fallback_scrapers))
    
    def _estimate_coverage(self, 
                          country_config: CountryConfig, 
                          strategies: List[ScrapingStrategy]) -> float:
        """
        📊 Estima cobertura de eventos esperada
        """
        # Heurística simple: cada estrategia aporta coverage
        base_coverage = 0.4  # Coverage base
        strategy_bonus = len(strategies) * 0.15
        return min(base_coverage + strategy_bonus, 0.95)
    
    async def _global_fallback_routing(self, 
                                     location: str, 
                                     intent: str,
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🌐 Fallback global para países/ciudades no configurados
        """
        logger.info(f"🌐 Using global fallback for: {location}")
        
        return {
            "location": {
                "detected_country": "Unknown",
                "country_code": "XX", 
                "city": location,
                "original_query": location
            },
            "selected_scrapers": [
                "ticketmaster_global_scraper",
                "eventbrite_global_scraper",
                "rapidapi_facebook_scraper"
            ],
            "strategies_used": ["global_apis", "social_media"],
            "execution_order": [
                "ticketmaster_global_scraper", 
                "eventbrite_global_scraper",
                "rapidapi_facebook_scraper"
            ],
            "fallback_scrapers": [],
            "estimated_coverage": 0.6,
            "cultural_context": {"note": "Global fallback - limited local context"},
            "routing_metadata": {
                "routing_time": datetime.now().isoformat(),
                "ai_enhanced": False,
                "confidence_score": 0.5,
                "is_fallback": True
            }
        }
    
    def add_country(self, country_config: CountryConfig):
        """
        🌍 Agregar nuevo país dinámicamente
        """
        self.COUNTRIES[country_config.iso_code] = country_config
        logger.info(f"✅ País agregado: {country_config.name}")
    
    def update_performance_metrics(self, scraper_name: str, execution_time: float, success: bool):
        """
        📊 Actualizar métricas de performance
        """
        if scraper_name not in self.scraper_performance:
            self.scraper_performance[scraper_name] = {
                "avg_time": execution_time,
                "success_rate": 1.0 if success else 0.0,
                "total_runs": 1
            }
        else:
            metrics = self.scraper_performance[scraper_name]
            metrics["total_runs"] += 1
            
            # Running average
            metrics["avg_time"] = (metrics["avg_time"] + execution_time) / 2
            
            # Running success rate
            current_successes = metrics["success_rate"] * (metrics["total_runs"] - 1)
            new_successes = current_successes + (1 if success else 0)
            metrics["success_rate"] = new_successes / metrics["total_runs"]
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        📊 Estadísticas del sistema de routing
        """
        return {
            "supported_countries": len(self.COUNTRIES),
            "supported_cities": len(self.CITY_TO_COUNTRY), 
            "scraper_performance": self.scraper_performance,
            "countries": {code: config.name for code, config in self.COUNTRIES.items()}
        }

# Instancia global del router
global_router = GlobalScraperRouter()