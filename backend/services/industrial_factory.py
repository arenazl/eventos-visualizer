"""
🏭 INDUSTRIAL FACTORY - Ejecutor Masivo de Scrapers
Sistema de producción industrial para ejecutar múltiples scrapers en paralelo
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from services.auto_discovery import AutoDiscoveryEngine

logger = logging.getLogger(__name__)

class IndustrialFactory:
    """
    🏭 FÁBRICA INDUSTRIAL DE SCRAPERS
    
    CARACTERÍSTICAS:
    - Ejecuta scrapers en paralelo masivo
    - Auto-descubrimiento de scrapers disponibles
    - Manejo de timeouts y errores robusto
    - Estadísticas de rendimiento en tiempo real
    - Patrón factory para instanciación dinámica
    """
    
    def __init__(self):
        """Inicializa la factory con auto-discovery"""
        logger.info("🏭 Industrial Factory inicializado")
        self.discovery_engine = AutoDiscoveryEngine()
        logger.info("📋 Funcionando con auto-discovery puro (sin JSON)")
        
    async def execute_global_scrapers(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        🚀 EJECUCIÓN PARALELA DE SCRAPERS GLOBALES
        
        Args:
            location: Ubicación de búsqueda
            category: Categoría opcional
            limit: Límite por scraper
            
        Returns:
            Lista consolidada de eventos de todos los scrapers
        """
        
        logger.info("🔍 Ejecutando auto-discovery de scrapers...")
        
        # Auto-descubrir scrapers disponibles
        scrapers_map = self.discovery_engine.discover_all_scrapers()
        
        global_scrapers = scrapers_map.get('global', {})
        logger.info(f"🌍 Global scrapers instanciados: {len(global_scrapers)}")
        
        if not global_scrapers:
            logger.warning("⚠️ No se encontraron scrapers globales")
            return []
        
        # Ejecutar scrapers en paralelo
        logger.info(f"🚀 Ejecutando {len(global_scrapers)} scrapers en paralelo para '{location}'")
        
        tasks = []
        scraper_names = []
        
        for scraper_name, scraper_instance in global_scrapers.items():
            task = self._execute_single_scraper(
                scraper_instance, 
                scraper_name, 
                location, 
                category, 
                limit,
                detected_country,
                context_data
            )
            tasks.append(task)
            scraper_names.append(scraper_name)
        
        # Ejecutar todos en paralelo con timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        all_events = []
        successful_scrapers = 0
        
        for i, result in enumerate(results):
            scraper_name = scraper_names[i]
            
            if isinstance(result, Exception):
                logger.warning(f"⚠️ {scraper_name.title()}Scraper: {str(result)}")
            elif isinstance(result, list):
                event_count = len(result)
                all_events.extend(result)
                successful_scrapers += 1
                logger.info(f"✅ {scraper_name.title()}Scraper: {event_count} eventos en {self._get_scraper_time(scraper_name)}")
            else:
                logger.warning(f"⚠️ {scraper_name.title()}Scraper: Resultado inesperado")
        
        logger.info(f"🎯 RESUMEN: {successful_scrapers}/{len(global_scrapers)} scrapers exitosos, {len(all_events)} eventos totales")
        
        return all_events
    
    async def execute_global_scrapers_with_details(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🚀 EJECUCIÓN PARALELA CON DETALLES COMPLETOS
        
        Returns:
            Dict con eventos y detalles completos de cada scraper
        """
        
        start_time = time.time()
        logger.info("🔍 Ejecutando auto-discovery de scrapers...")
        
        # Auto-descubrir scrapers disponibles
        scrapers_map = self.discovery_engine.discover_all_scrapers()
        
        global_scrapers = scrapers_map.get('global', {})
        logger.info(f"🌍 Global scrapers instanciados: {len(global_scrapers)}")
        
        if not global_scrapers:
            logger.warning("⚠️ No se encontraron scrapers globales")
            return {
                'events': [],
                'scrapers_execution': {
                    'scrapers_called': [],
                    'total_scrapers': 0,
                    'scrapers_info': [],
                    'summary': 'No scrapers disponibles'
                }
            }
        
        # Ejecutar scrapers en paralelo
        logger.info(f"🚀 Ejecutando {len(global_scrapers)} scrapers en paralelo para '{location}'")
        
        tasks = []
        scraper_names = []
        
        for scraper_name, scraper_instance in global_scrapers.items():
            task = self._execute_single_scraper_with_details(
                scraper_instance, 
                scraper_name, 
                location, 
                category, 
                limit,
                detected_country,
                context_data
            )
            tasks.append(task)
            scraper_names.append(scraper_name)
        
        # Ejecutar todos en paralelo con timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        all_events = []
        scrapers_info = []
        successful_scrapers = 0
        
        for i, result in enumerate(results):
            scraper_name = scraper_names[i]
            
            if isinstance(result, Exception):
                scrapers_info.append({
                    'name': scraper_name.title(),
                    'status': 'failed',
                    'events_count': 0,
                    'response_time': '0.0s',
                    'message': str(result)
                })
                logger.warning(f"⚠️ {scraper_name.title()}Scraper: {str(result)}")
            elif isinstance(result, dict) and 'events' in result:
                events = result['events']
                event_count = len(events)
                all_events.extend(events)
                
                scrapers_info.append({
                    'name': scraper_name.title(),
                    'status': 'success',
                    'events_count': event_count,
                    'response_time': result.get('execution_time', '0.0s'),
                    'message': f'{event_count} eventos obtenidos exitosamente'
                })
                
                if event_count > 0:
                    successful_scrapers += 1
                    
                logger.info(f"✅ {scraper_name.title()}Scraper: {event_count} eventos en {result.get('execution_time', '0.0s')}")
            else:
                scrapers_info.append({
                    'name': scraper_name.title(),
                    'status': 'timeout',
                    'events_count': 0,
                    'response_time': '10.0s',
                    'message': 'Timeout después de 10 segundos'
                })
                logger.warning(f"⚠️ {scraper_name.title()}Scraper: Resultado inesperado")
        
        total_time = time.time() - start_time
        
        scrapers_execution = {
            'scrapers_called': scraper_names,
            'total_scrapers': len(global_scrapers),
            'scrapers_info': scrapers_info,
            'summary': f'{successful_scrapers}/{len(global_scrapers)} scrapers exitosos en {total_time:.2f}s - {len(all_events)} eventos totales'
        }
        
        logger.info(f"🎯 RESUMEN: {successful_scrapers}/{len(global_scrapers)} scrapers exitosos, {len(all_events)} eventos totales en {total_time:.2f}s")
        
        return {
            'events': all_events,
            'scrapers_execution': scrapers_execution
        }
    
    async def _execute_single_scraper(
        self,
        scraper_instance,
        scraper_name: str,
        location: str,
        category: Optional[str],
        limit: int,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        🔧 EJECUTOR INDIVIDUAL DE SCRAPER
        
        Ejecuta un scraper individual con manejo de errores y timeout
        """
        
        start_time = time.time()
        
        try:
            # Timeout de 10 segundos por scraper
            # Intentar pasar contexto completo si el scraper lo soporta
            if hasattr(scraper_instance, 'set_context'):
                full_context = {'detected_country': detected_country}
                if context_data:
                    full_context.update(context_data)
                scraper_instance.set_context(full_context)
            
            events = await asyncio.wait_for(
                scraper_instance.scrape_events(location, category, limit),
                timeout=10.0
            )
            
            execution_time = time.time() - start_time
            self._record_scraper_time(scraper_name, execution_time)
            
            return events if isinstance(events, list) else []
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ {scraper_name.title()}Scraper: Timeout después de 10s")
            return []
        except Exception as e:
            logger.error(f"❌ {scraper_name.title()}Scraper: {str(e)}")
            return []
    
    async def _execute_single_scraper_with_details(
        self,
        scraper_instance,
        scraper_name: str,
        location: str,
        category: Optional[str],
        limit: int,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🔧 EJECUTOR INDIVIDUAL CON DETALLES
        
        Ejecuta un scraper individual con manejo de errores y timeout
        Retorna detalles completos de la ejecución
        """
        
        start_time = time.time()
        
        try:
            # Timeout de 5 segundos por scraper para mayor velocidad
            # Intentar pasar contexto completo si el scraper lo soporta
            if hasattr(scraper_instance, 'set_context'):
                full_context = {'detected_country': detected_country}
                if context_data:
                    full_context.update(context_data)
                scraper_instance.set_context(full_context)
                
            events = await asyncio.wait_for(
                scraper_instance.scrape_events(location, category, limit),
                timeout=5.0
            )
            
            execution_time = time.time() - start_time
            events_list = events if isinstance(events, list) else []
            
            return {
                'events': events_list,
                'execution_time': f"{execution_time:.2f}s",
                'status': 'success',
                'events_count': len(events_list)
            }
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"⏰ {scraper_name.title()}Scraper: Timeout después de 5s")
            return {
                'events': [],
                'execution_time': f"{execution_time:.2f}s",
                'status': 'timeout',
                'events_count': 0,
                'error': 'Timeout después de 5 segundos'
            }
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {scraper_name.title()}Scraper: {str(e)}")
            return {
                'events': [],
                'execution_time': f"{execution_time:.2f}s",
                'status': 'failed',
                'events_count': 0,
                'error': str(e)
            }
    
    def _record_scraper_time(self, scraper_name: str, execution_time: float):
        """Registra tiempo de ejecución del scraper"""
        if not hasattr(self, '_scraper_times'):
            self._scraper_times = {}
        self._scraper_times[scraper_name] = execution_time
    
    def _get_scraper_time(self, scraper_name: str) -> str:
        """Obtiene tiempo formateado del scraper"""
        if hasattr(self, '_scraper_times') and scraper_name in self._scraper_times:
            return f"{self._scraper_times[scraper_name]:.2f}s"
        return "0.0s"