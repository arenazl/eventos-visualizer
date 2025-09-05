"""
🎯 EVENT ORCHESTRATOR - Coordinador Principal de Scrapers
Sistema centralizado que orquesta todos los scrapers globales, regionales y locales
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from services.industrial_factory import IndustrialFactory
from services.auto_discovery import AutoDiscoveryEngine

logger = logging.getLogger(__name__)

class EventOrchestrator:
    """
    🎯 COORDINADOR PRINCIPAL DE EVENTOS
    
    RESPONSABILIDADES:
    - Coordinar scrapers globales, regionales y locales
    - Ejecutar búsquedas en paralelo optimizado
    - Eliminar duplicados inteligentemente
    - Gestionar timeouts y reintentos
    - Reportar estadísticas de ejecución
    """
    
    def __init__(self):
        """Inicializa el orchestrador con factory pattern"""
        self.factory = IndustrialFactory()
        logger.info("🔧 DEBUG: EventOrchestrator inicializado SIN Argentina Factory calls")
        
    async def get_events_comprehensive(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30,
        province: Optional[str] = None,
        country: Optional[str] = None,
        min_events_threshold: int = 3
    ) -> Dict[str, Any]:
        """
        🚀 BÚSQUEDA COMPLETA DE EVENTOS CON FALLBACK INTELIGENTE
        
        Args:
            location: Ciudad o región de búsqueda
            category: Categoría opcional de eventos
            limit: Número máximo de eventos a retornar
            province: Provincia/Estado para fallback
            country: País para fallback final
            min_events_threshold: Mínimo de eventos para considerar suficiente
            
        Returns:
            Diccionario con eventos, estadísticas y metadata
        """
        
        logger.info(f"🎯 EVENT ORCHESTRATOR: Búsqueda con fallback para '{location}'")
        
        start_time = time.time()
        
        try:
            # 🎯 Usar Factory con Fallback Inteligente
            logger.info("🔄 Ejecutando Factory con fallback jerárquico...")
            
            # Si no tenemos provincia/país, intentar detectarlos con IA
            if not province or not country:
                try:
                    from services.intent_recognition import IntentRecognitionService
                    intent_service = IntentRecognitionService()
                    
                    # Analizar ubicación para extraer jerarquía geográfica
                    intent_result = await intent_service.get_all_api_parameters(location)
                    
                    if intent_result.get('success'):
                        intent_data = intent_result.get('intent', {})
                        detected_city = intent_data.get('city', location)
                        detected_province = intent_data.get('province')
                        detected_country = intent_data.get('country')
                        
                        # Si la búsqueda es por ciudad pequeña, usar la ciudad detectada
                        if detected_city and detected_city != location:
                            location = detected_city
                            logger.info(f"🏙️ Ciudad refinada por IA: {location}")
                        
                        if not province and detected_province:
                            province = detected_province
                            logger.info(f"📍 Provincia detectada por IA: {province}")
                            
                        if not country and detected_country:
                            country = detected_country
                            logger.info(f"🌍 País detectado por IA: {country}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo detectar jerarquía geográfica: {e}")
            
            # Ejecutar búsqueda con fallback
            result = await self.factory.execute_with_fallback(
                city=location,
                province=province,
                country=country,
                category=category,
                limit=limit,
                min_events_threshold=min_events_threshold,
                context_data={'source': 'EventOrchestrator'}
            )
            
            # Obtener eventos y metadata del resultado
            final_events = result.get('events', [])
            search_level = result.get('search_level', 'unknown')
            search_location = result.get('search_location', location)
            fallback_used = result.get('fallback_used', False)
            events_by_level = result.get('events_by_level', {})
            
            # Log del resultado
            if fallback_used:
                logger.info(f"✅ FALLBACK usado: {search_level} → {search_location} con {len(final_events)} eventos")
            else:
                logger.info(f"✅ Búsqueda exitosa en {search_level}: {len(final_events)} eventos")
            
            execution_time = time.time() - start_time
            
            return {
                "events": final_events,
                "total_found": len(final_events),
                "returned": len(final_events),
                "execution_time": f"{execution_time:.2f}s",
                "scrapers_used": "industrial_factory_with_fallback",
                "scrapers_execution": result.get('scrapers_execution', {}),
                "search_level": search_level,
                "search_location": search_location,
                "fallback_used": fallback_used,
                "events_by_level": events_by_level,
                "search_hierarchy": result.get('search_hierarchy', {}),
                "fallback_message": result.get('fallback_message', None),
                "location_searched": location,
                "category_filter": category
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Event Orchestrator: {str(e)}")
            return {
                "events": [],
                "total_found": 0,
                "returned": 0,
                "execution_time": f"{time.time() - start_time:.2f}s",
                "error": str(e),
                "location_searched": location,
                "category_filter": category
            }
    
    def _remove_duplicates(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔄 ELIMINACIÓN CONSERVADORA DE DUPLICADOS
        
        SOLO elimina duplicados por URL exacta - preserva eventos con títulos genéricos
        """
        
        if not events:
            return []
            
        unique_events = []
        seen_urls = set()
        
        for event in events:
            event_url = event.get('event_url', '').strip()
            
            # Si tiene URL, solo eliminar si la URL ya existe
            if event_url:
                if event_url in seen_urls:
                    continue  # Skip - URL duplicada
                seen_urls.add(event_url)
            
            # Siempre agregar eventos sin URL o con URL nueva
            unique_events.append(event)
        
        return unique_events