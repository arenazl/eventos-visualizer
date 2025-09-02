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
        
    async def get_events_comprehensive(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        🚀 BÚSQUEDA COMPLETA DE EVENTOS
        
        Args:
            location: Ciudad o región de búsqueda
            category: Categoría opcional de eventos
            limit: Número máximo de eventos a retornar
            
        Returns:
            Diccionario con eventos, estadísticas y metadata
        """
        
        logger.info(f"🎯 EVENT ORCHESTRATOR: Iniciando búsqueda completa para '{location}'")
        
        start_time = time.time()
        all_events = []
        scraper_stats = []
        
        try:
            # 🌍 FASE 1: Scrapers Globales (prioritarios)
            logger.info("🌍 Ejecutando scrapers GLOBALES con Industrial Factory...")
            
            global_events = await self.factory.execute_global_scrapers(
                location=location,
                category=category,
                limit=limit,
                context_data={}
            )
            
            logger.info(f"🌍 Industrial Factory completado: {len(global_events)} eventos de 8 scrapers")
            all_events.extend(global_events)
            
            # 🇦🇷 FASE 1.5: Argentina Factory para eventos regionales
            if "argentina" in location.lower() or any(city in location.lower() for city in ["buenos aires", "córdoba", "rosario", "mendoza", "salta"]):
                try:
                    from services.regional_factory.argentina.argentina_factory import argentina_factory
                    
                    logger.info(f"🇦🇷 Ejecutando Argentina Factory para {location}...")
                    argentina_result = await argentina_factory.get_events(location, category, limit)
                    
                    argentina_events = argentina_result.get("events", [])
                    if argentina_events:
                        logger.info(f"🇦🇷 Argentina Factory: {len(argentina_events)} eventos regionales agregados")
                        all_events.extend(argentina_events)
                    else:
                        logger.info(f"🇦🇷 Argentina Factory: No se encontraron eventos regionales para {location}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en Argentina Factory: {e}")
            
            # 🔄 FASE 2: Eliminar duplicados
            unique_events = self._remove_duplicates(all_events)
            logger.info(f"🔄 Duplicados eliminados: {len(all_events)} → {len(unique_events)} eventos únicos")
            
            # 📊 Limitar resultados
            final_events = unique_events[:limit] if limit else unique_events
            
            execution_time = time.time() - start_time
            
            return {
                "events": final_events,
                "total_found": len(unique_events),
                "returned": len(final_events),
                "execution_time": f"{execution_time:.2f}s",
                "scrapers_used": "industrial_factory",
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