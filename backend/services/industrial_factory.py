"""
🏭 INDUSTRIAL FACTORY - Ejecutor Masivo de Scrapers
Sistema de producción industrial para ejecutar múltiples scrapers en paralelo
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from services.auto_discovery import AutoDiscoveryEngine
from services.interfaces.discovery_interface import DiscoveryEngineInterface

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
    
    def __init__(self, discovery_engine: DiscoveryEngineInterface = None):
        """
        🔌 DEPENDENCY INJECTION PATTERN
        
        Inicializa la factory con discovery engine inyectado
        
        Args:
            discovery_engine: Interface para descubrir scrapers (inyectada)
                            Si es None, usa AutoDiscoveryEngine por defecto (compatibility)
        """
        logger.info("🏭 Industrial Factory inicializado con Dependency Injection")
        
        # 🔌 Dependency Injection - recibe dependencia desde el exterior
        if discovery_engine is None:
            # Fallback para compatibilidad con código existente
            logger.info("📦 DI: Usando AutoDiscoveryEngine por defecto (compatibility mode)")
            self.discovery_engine = AutoDiscoveryEngine()
        else:
            # Patrón DI correcto - recibe dependencia inyectada
            logger.info(f"🔌 DI: Usando discovery engine inyectado: {type(discovery_engine).__name__}")
            self.discovery_engine = discovery_engine
            
        logger.info("📋 Factory usa scrapers habilitados automáticamente por enabled_by_default")
        
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
        
        # AutoDiscovery ya entrega solo los scrapers habilitados (enabled_by_default=True)
        global_scrapers = scrapers_map.get('global', {})
        
        # Sort scrapers by priority (fastest first)
        sorted_scrapers = sorted(
            global_scrapers.items(), 
            key=lambda x: getattr(x[1], 'priority', 99)
        )
        logger.info(f"🌍 Scrapers ordenados por prioridad: {[name for name, _ in sorted_scrapers]}")
        
        if not global_scrapers:
            logger.warning("⚠️ No se encontraron scrapers habilitados (Eventbrite/Meetup)")
            return []
        
        # Ejecutar scrapers en paralelo (ordenados por prioridad)
        logger.info(f"🚀 Ejecutando {len(sorted_scrapers)} scrapers en paralelo para '{location}'")
        
        tasks = []
        scraper_names = []
        
        for scraper_name, scraper_instance in sorted_scrapers:
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
        
        # AutoDiscovery ya entrega solo los scrapers habilitados (enabled_by_default=True)
        global_scrapers = scrapers_map.get('global', {})
        logger.info(f"🌍 Global scrapers instanciados: {len(global_scrapers)}")
        
        # Sort scrapers by priority (fastest first) - CRITICAL: Add this missing line
        sorted_scrapers = sorted(
            global_scrapers.items(), 
            key=lambda x: getattr(x[1], 'priority', 99)
        )
        logger.info(f"🌍 Scrapers ordenados por prioridad: {[name for name, _ in sorted_scrapers]}")
        
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
        
        # Ejecutar scrapers en paralelo (ordenados por prioridad)
        logger.info(f"🚀 Ejecutando {len(sorted_scrapers)} scrapers en paralelo para '{location}'")
        
        tasks = []
        scraper_names = []
        
        for scraper_name, scraper_instance in sorted_scrapers:
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
    
    async def execute_recommend(
        self,
        location: str,
        nearby_cities: List[str],
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🌍 EJECUCIÓN PARA RECOMENDACIONES CON CIUDADES CERCANAS
        
        Ejecuta scrapers que soportan nearby_cities para recomendaciones inteligentes
        
        Args:
            location: Ubicación principal
            nearby_cities: Lista de ciudades cercanas
            category: Categoría opcional
            limit: Límite por scraper y ciudad
            detected_country: País detectado
            context_data: Contexto adicional
            
        Returns:
            Dict con eventos y botones de ciudades
        """
        
        logger.info(f"🌍 Ejecutando recommend para {location} con ciudades cercanas: {nearby_cities}")
        
        # Auto-descubrir scrapers disponibles
        scrapers_map = self.discovery_engine.discover_all_scrapers()
        global_scrapers = scrapers_map.get('global', {})
        
        # Filtrar solo scrapers que soportan nearby_cities
        recommend_scrapers = {
            name: scraper for name, scraper in global_scrapers.items()
            if hasattr(scraper, 'nearby_cities') and scraper.nearby_cities
        }
        
        logger.info(f"🎯 Scrapers habilitados para recommend: {list(recommend_scrapers.keys())}")
        
        if not recommend_scrapers:
            logger.warning("⚠️ No hay scrapers habilitados para recommend")
            return {
                'nearby_events': [],
                'city_buttons': [],
                'city_stats': {}
            }
        
        # Ejecutar scrapers en paralelo para cada ciudad
        all_tasks = []
        city_scraper_mapping = []
        
        for city in nearby_cities:
            for scraper_name, scraper_instance in recommend_scrapers.items():
                task = self._execute_single_scraper(
                    scraper_instance,
                    scraper_name,
                    city,
                    category,
                    limit,
                    detected_country,
                    context_data
                )
                all_tasks.append(task)
                city_scraper_mapping.append((city, scraper_name))
        
        logger.info(f"🚀 Ejecutando {len(all_tasks)} tareas en paralelo ({len(nearby_cities)} ciudades × {len(recommend_scrapers)} scrapers)")
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Procesar resultados por ciudad
        city_events = {city: [] for city in nearby_cities}
        city_stats = {city: 0 for city in nearby_cities}
        
        for i, result in enumerate(results):
            city, scraper_name = city_scraper_mapping[i]
            
            if isinstance(result, list) and result:
                city_events[city].extend(result)
                logger.info(f"✅ {city} - {scraper_name}: {len(result)} eventos")
            elif isinstance(result, Exception):
                logger.warning(f"⚠️ {city} - {scraper_name}: {str(result)}")
        
        # Calcular estadísticas por ciudad
        for city in nearby_cities:
            city_stats[city] = len(city_events[city])
        
        # Crear botones de ciudades
        city_buttons = [
            {
                "city": city,
                "label": f"Eventos en {city}",
                "count": city_stats[city]
            }
            for city in nearby_cities if city_stats[city] > 0
        ]
        
        # Combinar todos los eventos
        all_nearby_events = []
        for events in city_events.values():
            all_nearby_events.extend(events)
        
        total_events = len(all_nearby_events)
        logger.info(f"🎯 RESUMEN RECOMMEND: {total_events} eventos de {len(nearby_cities)} ciudades con {len(recommend_scrapers)} scrapers")
        
        return {
            'nearby_events': all_nearby_events,
            'city_buttons': city_buttons,
            'city_stats': city_stats,
            'total_events': total_events,
            'scrapers_used': list(recommend_scrapers.keys()),
            'cities_processed': nearby_cities
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
                timeout=5.0  # Reduced from 10s to 5s for faster responses
            )
            
            execution_time = time.time() - start_time
            self._record_scraper_time(scraper_name, execution_time)
            
            return events if isinstance(events, list) else []
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ {scraper_name.title()}Scraper: Timeout después de 5s")
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
    
    async def execute_with_fallback(
        self,
        city: str,
        province: Optional[str] = None,
        country: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 30,
        min_events_threshold: int = 3,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🎯 EJECUCIÓN CON FALLBACK JERÁRQUICO DE 3 NIVELES
        
        Intenta obtener eventos en este orden:
        1. Ciudad específica
        2. Provincia/Estado (si hay menos de min_events_threshold)
        3. País (si aún hay pocos eventos)
        
        Args:
            city: Ciudad para buscar
            province: Provincia/Estado para fallback
            country: País para fallback final
            category: Categoría opcional
            limit: Límite de eventos por nivel
            min_events_threshold: Mínimo de eventos para considerar suficiente
            context_data: Contexto adicional
            
        Returns:
            Dict con eventos y nivel de búsqueda usado
        """
        
        logger.info(f"🎯 FALLBACK SEARCH iniciando con: {city} → {province} → {country}")
        
        # Nivel 1: Buscar en ciudad específica
        logger.info(f"🏙️ NIVEL 1: Buscando en ciudad '{city}'...")
        city_result = await self.execute_global_scrapers_with_details(
            location=city,
            category=category,
            limit=limit,
            detected_country=country,
            context_data=context_data
        )
        
        city_events = city_result.get('events', [])
        city_count = len(city_events)
        
        if city_count >= min_events_threshold:
            logger.info(f"✅ NIVEL 1 exitoso: {city_count} eventos en {city}")
            return {
                **city_result,
                'search_level': 'city',
                'search_location': city,
                'fallback_used': False,
                'search_hierarchy': {
                    'city': city,
                    'province': province,
                    'country': country
                }
            }
        
        logger.warning(f"⚠️ NIVEL 1 insuficiente: solo {city_count} eventos en {city}")
        
        # Nivel 2: Fallback a provincia si está disponible
        if province and province != city:
            logger.info(f"🏛️ NIVEL 2: Fallback a provincia '{province}'...")
            province_result = await self.execute_global_scrapers_with_details(
                location=province,
                category=category,
                limit=limit,
                detected_country=country,
                context_data=context_data
            )
            
            province_events = province_result.get('events', [])
            combined_events = city_events + province_events
            
            # Eliminar duplicados por título
            unique_events = {}
            for event in combined_events:
                title = event.get('title', '')
                if title and title not in unique_events:
                    unique_events[title] = event
            
            combined_events = list(unique_events.values())
            combined_count = len(combined_events)
            
            if combined_count >= min_events_threshold:
                logger.info(f"✅ NIVEL 2 exitoso: {combined_count} eventos combinados de {city} + {province}")
                return {
                    'events': combined_events[:limit],
                    'scrapers_execution': province_result.get('scrapers_execution', {}),
                    'search_level': 'province',
                    'search_location': province,
                    'fallback_used': True,
                    'search_hierarchy': {
                        'city': city,
                        'province': province,
                        'country': country
                    },
                    'events_by_level': {
                        'city': city_count,
                        'province': len(province_events),
                        'combined': combined_count
                    }
                }
            
            logger.warning(f"⚠️ NIVEL 2 insuficiente: {combined_count} eventos en {province}")
        
        # Nivel 3: Fallback a país si está disponible
        if country and country not in [city, province]:
            logger.info(f"🌍 NIVEL 3: Fallback a país '{country}'...")
            country_result = await self.execute_global_scrapers_with_details(
                location=country,
                category=category,
                limit=limit * 2,  # Más eventos para país
                detected_country=country,
                context_data=context_data
            )
            
            country_events = country_result.get('events', [])
            
            # Combinar todos los eventos (ciudad + provincia + país)
            all_events = city_events
            if province:
                all_events += province_events
            all_events += country_events
            
            # Eliminar duplicados
            unique_events = {}
            for event in all_events:
                title = event.get('title', '')
                if title and title not in unique_events:
                    unique_events[title] = event
            
            all_events = list(unique_events.values())
            total_count = len(all_events)
            
            logger.info(f"✅ NIVEL 3 completado: {total_count} eventos totales desde país {country}")
            
            return {
                'events': all_events[:limit],
                'scrapers_execution': country_result.get('scrapers_execution', {}),
                'search_level': 'country',
                'search_location': country,
                'fallback_used': True,
                'search_hierarchy': {
                    'city': city,
                    'province': province,
                    'country': country
                },
                'events_by_level': {
                    'city': city_count,
                    'province': len(province_events) if province else 0,
                    'country': len(country_events),
                    'total': total_count
                },
                'fallback_message': f"Mostrando eventos de {country} (no se encontraron suficientes en {city})"
            }
        
        # Si no hay país para fallback, devolver lo que tengamos
        logger.warning(f"⚠️ Sin más niveles de fallback. Devolviendo {city_count} eventos de {city}")
        return {
            **city_result,
            'search_level': 'city',
            'search_location': city,
            'fallback_used': False,
            'search_hierarchy': {
                'city': city,
                'province': province,
                'country': country
            },
            'warning': f"Solo se encontraron {city_count} eventos en {city}"
        }
    
    async def execute_with_websocket_streaming(
        self,
        websocket,
        location: str,
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        🚀 STREAMING REAL-TIME VIA WEBSOCKET
        
        Ejecuta scrapers en paralelo y envía eventos inmediatamente 
        cuando cada scraper completa, sin esperar a que todos terminen
        
        Args:
            websocket: WebSocket connection para streaming
            location: Ubicación de búsqueda
            category: Categoría opcional
            limit: Límite por scraper
            detected_country: País detectado
            context_data: Contexto adicional
        """
        
        logger.info(f"🚀 STREAMING: Iniciando búsqueda paralela con streaming para '{location}'")
        
        # Auto-descubrir scrapers disponibles
        scrapers_map = self.discovery_engine.discover_all_scrapers()
        global_scrapers = scrapers_map.get('global', {})
        
        # Sort scrapers by priority (fastest first)
        sorted_scrapers = sorted(
            global_scrapers.items(), 
            key=lambda x: getattr(x[1], 'priority', 99)
        )
        
        if not global_scrapers:
            await websocket.send_json({
                "type": "no_scrapers",
                "message": "⚠️ No se encontraron scrapers habilitados",
                "timestamp": time.time()
            })
            return
        
        # Crear tasks para todos los scrapers en paralelo
        # Using asyncio.create_task to properly create coroutines
        task_to_scraper = {}
        tasks_list = []
        
        for scraper_name, scraper_instance in sorted_scrapers:
            # Create the coroutine
            coro = self._execute_single_scraper_with_websocket(
                scraper_instance, 
                scraper_name, 
                location, 
                category, 
                limit,
                detected_country,
                context_data,
                websocket
            )
            # Create task from coroutine
            task = asyncio.create_task(coro)
            task_to_scraper[task] = scraper_name
            tasks_list.append(task)
        
        # Enviar mensaje de inicio
        await websocket.send_json({
            "type": "streaming_started",
            "message": f"🚀 Ejecutando {len(tasks_list)} scrapers en paralelo",
            "scrapers": list(task_to_scraper.values()),
            "timestamp": time.time()
        })
        
        # Usar asyncio.as_completed para obtener resultados tan pronto como cada scraper termine
        completed_scrapers = 0
        total_events = 0
        
        for completed_task in asyncio.as_completed(tasks_list):
            try:
                result = await completed_task
                # Find which scraper this was
                scraper_name = None
                for task, name in task_to_scraper.items():
                    if task == completed_task or task.done():
                        scraper_name = name
                        break
                
                if not scraper_name:
                    # Fallback - extract from result if possible
                    scraper_name = result.get('scraper_name', 'unknown') if isinstance(result, dict) else 'unknown'
                
                # Extract events from result
                events = result if isinstance(result, list) else []
                completed_scrapers += 1
                event_count = len(events) if isinstance(events, list) else 0
                total_events += event_count
                
                # Enviar eventos inmediatamente cuando el scraper completa
                await websocket.send_json({
                    "type": "scraper_completed",
                    "scraper_name": scraper_name,
                    "events": events,
                    "events_count": event_count,
                    "completed_scrapers": completed_scrapers,
                    "total_scrapers": len(tasks_list),
                    "total_events": total_events,
                    "message": f"✅ {scraper_name.title()}: {event_count} eventos",
                    "timestamp": time.time()
                })
                
                logger.info(f"📡 STREAMING: {scraper_name} completado - {event_count} eventos enviados inmediatamente")
                
            except Exception as e:
                completed_scrapers += 1
                
                # Enviar error inmediatamente
                await websocket.send_json({
                    "type": "scraper_failed",
                    "scraper_name": scraper_name,
                    "error": str(e),
                    "completed_scrapers": completed_scrapers,
                    "total_scrapers": len(tasks_list),
                    "message": f"❌ {scraper_name.title()}: Error",
                    "timestamp": time.time()
                })
                
                logger.warning(f"⚠️ STREAMING: {scraper_name} falló - {str(e)}")
        
        # Enviar mensaje final cuando todos completaron
        await websocket.send_json({
            "type": "streaming_completed",
            "message": f"🎯 Streaming completado: {total_events} eventos de {len(tasks)} scrapers",
            "total_events": total_events,
            "completed_scrapers": completed_scrapers,
            "total_scrapers": len(tasks),
            "timestamp": time.time()
        })
        
        logger.info(f"🎯 STREAMING COMPLETED: {total_events} eventos totales de {completed_scrapers} scrapers")
    
    async def _execute_single_scraper_with_websocket(
        self,
        scraper_instance,
        scraper_name: str,
        location: str,
        category: Optional[str],
        limit: int,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        websocket = None
    ) -> List[Dict[str, Any]]:
        """
        🔧 EJECUTOR INDIVIDUAL PARA WEBSOCKET STREAMING
        
        Similar a _execute_single_scraper pero optimizado para streaming
        """
        
        start_time = time.time()
        
        # Enviar mensaje de inicio del scraper
        if websocket:
            await websocket.send_json({
                "type": "scraper_started",
                "scraper_name": scraper_name,
                "message": f"🚀 Iniciando {scraper_name.title()}Scraper...",
                "timestamp": time.time()
            })
        
        try:
            # Configurar contexto si el scraper lo soporta
            if hasattr(scraper_instance, 'set_context'):
                full_context = {'detected_country': detected_country}
                if context_data:
                    full_context.update(context_data)
                scraper_instance.set_context(full_context)
            
            # Ejecutar scraper con timeout
            events = await asyncio.wait_for(
                scraper_instance.scrape_events(location, category, limit),
                timeout=5.0  # 5 segundos timeout
            )
            
            execution_time = time.time() - start_time
            events_list = events if isinstance(events, list) else []
            
            logger.info(f"✅ STREAM: {scraper_name} completado en {execution_time:.2f}s - {len(events_list)} eventos")
            
            return events_list
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"⏰ STREAM: {scraper_name} timeout después de 5s")
            return []
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ STREAM: {scraper_name} error: {str(e)}")
            return []