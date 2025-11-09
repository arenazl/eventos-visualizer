"""
🏭 INDUSTRIAL FACTORY - Ejecutor Masivo de Scrapers
Sistema de producción industrial para ejecutar múltiples scrapers en paralelo
"""

import asyncio
import logging
import time
import os
import json
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

        # Inicializar caché persistente de ubicaciones enriquecidas
        self._location_cache = {}
        self._cache_file = os.path.join(os.path.dirname(__file__), '../data/location_enrichments_cache.json')
        self._load_location_cache()
        
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

    async def execute_streaming(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        🚀 STREAMING ASÍNCRONO - Devuelve resultados apenas estén listos

        Usa async generator para yield de resultados en tiempo real
        NO espera a que terminen todos los scrapers

        Yields:
            Dict con: {
                'scraper': nombre,
                'events': lista_eventos,
                'execution_time': tiempo,
                'success': bool,
                'error': str opcional
            }
        """

        logger.info(f"🌊 STREAMING MODE: Iniciando para '{location}'")

        # 🌍 ENRIQUECIMIENTO INTELIGENTE DE UBICACIÓN (UNA SOLA VEZ)
        enriched_location = await self._enrich_location_once(location, detected_country)

        # Auto-descubrir scrapers
        scrapers_map = self.discovery_engine.discover_all_scrapers()
        global_scrapers = scrapers_map.get('global', {})

        if not global_scrapers:
            logger.warning("⚠️ No se encontraron scrapers globales")
            return

        logger.info(f"🚀 Streaming: {len(global_scrapers)} scrapers en modo asíncrono")

        # Crear tareas con nombres
        tasks_map = {}

        # 📦 Preparar contexto enriquecido para TODOS los scrapers
        enriched_context = {
            'enriched_location': enriched_location,
            'detected_country': detected_country
        }
        if context_data:
            enriched_context.update(context_data)

        for scraper_name, scraper_instance in global_scrapers.items():
            task = asyncio.create_task(
                self._execute_single_scraper_with_details(
                    scraper_instance,
                    scraper_name,
                    location,
                    category,
                    limit,
                    detected_country,
                    enriched_context  # ← Contexto enriquecido
                )
            )
            tasks_map[task] = scraper_name

        # 🔥 CLAVE: Procesar tareas apenas terminan usando asyncio.wait
        pending = set(tasks_map.keys())

        while pending:
            # Esperar a que complete la primera tarea disponible
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            # Procesar cada tarea completada
            for task in done:
                scraper_name = tasks_map.get(task, 'unknown')

                try:
                    result = task.result()

                    # Extraer datos del resultado
                    events = result.get('events', [])
                    execution_time = result.get('execution_time', '0.0s')
                    status = result.get('status', 'unknown')
                    error = result.get('error')

                    # Yield inmediato - NO espera a otros scrapers
                    yield {
                        'scraper': scraper_name,
                        'events': events,
                        'execution_time': execution_time,
                        'success': status == 'success',
                        'error': error,
                        'count': len(events)
                    }

                    logger.info(f"📡 STREAMED: {scraper_name.title()} - {len(events)} eventos en {execution_time}")

                except Exception as e:
                    logger.error(f"❌ Error streaming {scraper_name}: {e}")

                    yield {
                        'scraper': scraper_name,
                        'events': [],
                        'execution_time': '0.0s',
                        'success': False,
                        'error': str(e),
                        'count': 0
                    }

        logger.info("🏁 Streaming completado - Todos los scrapers procesados")

    async def _enrich_location_once(
        self,
        location: str,
        detected_country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🌍 ENRIQUECIMIENTO INTELIGENTE DE UBICACIÓN

        Llama a Gemini UNA SOLA VEZ para enriquecer ubicación (ciudad chica → ciudad grande)
        Cachea resultados para evitar llamadas repetidas

        Args:
            location: Ubicación original del usuario
            detected_country: País detectado previamente

        Returns:
            Dict con ubicación enriquecida: {
                'original': str,
                'city': str,
                'state': str,
                'country': str,
                'nearby_major_city': str,
                'needs_expansion': bool
            }
        """

        cache_key = f"{location}_{detected_country or 'unknown'}"

        # Verificar caché (persistente)
        if cache_key in self._location_cache:
            cached_data = self._location_cache[cache_key]
            logger.info(f"✅ CACHE HIT: '{location}' → {cached_data.get('city')}, {cached_data.get('state')}")
            return cached_data

        try:
            # 🧠 Llamar a Gemini UNA SOLA VEZ para analizar ubicación
            from services.ai_service import GeminiAIService

            ai_service = GeminiAIService()

            # 🌍 EXTRAER PAÍS y UBICACIÓN BASE del input del usuario
            # Ejemplos:
            #   "Moreno, Buenos Aires, Argentina" → base: "Moreno, Buenos Aires", país: "Argentina"
            #   "Paris, Francia" → base: "Paris", país: "Francia"
            #   "Salta" → base: "Salta", país: "Argentina" (fallback)
            parts = [p.strip() for p in location.split(',')]

            if len(parts) >= 3:
                # 3 partes: localidad, provincia, país
                extracted_country = parts[-1]
                location_base = ', '.join(parts[:-1])  # "Moreno, Buenos Aires"
            elif len(parts) == 2:
                # 2 partes: ciudad, país
                extracted_country = parts[-1]
                location_base = parts[0]  # "Paris"
            else:
                # 1 parte: solo nombre
                extracted_country = detected_country or 'Argentina'
                location_base = location

            logger.info(f"🌍 Ubicación base: '{location_base}' | País: '{extracted_country}'")

            prompt = f"""Buscame 3 ciudades cercanas a {location_base}.

IMPORTANTE:
- Las ciudades DEBEN estar en el mismo país: {extracted_country}
- Formato OBLIGATORIO para cada ciudad: "Ciudad, Provincia/Estado, {extracted_country}"
- Todas las ciudades deben incluir el país completo al final

Devuelve SOLO JSON válido con este formato EXACTO:

{{
    "city": "nombre_ciudad_original",
    "state": "provincia_o_estado",
    "country": "{extracted_country}",
    "nearby_cities": ["Ciudad1, Estado1, {extracted_country}", "Ciudad2, Estado2, {extracted_country}", "Ciudad3, Estado3, {extracted_country}"],
    "needs_expansion": true
}}

Return ONLY valid JSON, sin explicaciones adicionales.
"""

            response = await ai_service._call_gemini_api(prompt)

            # DEBUG: Ver respuesta de Gemini
            print(f"\n🤖 GEMINI RESPONSE for '{location}':\n{response}\n")

            # Parsear respuesta JSON
            import json
            import re

            # Limpiar respuesta (quitar markdown)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                enriched_data = json.loads(json_match.group())

                # POST-PROCESAR nearby_cities para asegurar formato completo
                raw_nearby = enriched_data.get('nearby_cities', [])
                state = enriched_data.get('state', '')
                country = enriched_data.get('country', extracted_country)

                formatted_nearby = []
                for city in raw_nearby:
                    comma_count = city.count(',')

                    if comma_count == 0:
                        # Solo nombre: "Pinamar" → "Pinamar, Buenos Aires, Argentina"
                        if state and country:
                            formatted_nearby.append(f"{city}, {state}, {country}")
                        elif country:
                            formatted_nearby.append(f"{city}, {country}")
                        else:
                            formatted_nearby.append(city)
                    elif comma_count == 1:
                        # Nombre + algo: "Pinamar, Buenos Aires" → "Pinamar, Buenos Aires, Argentina"
                        if country and country not in city:
                            formatted_nearby.append(f"{city}, {country}")
                        else:
                            formatted_nearby.append(city)
                    else:
                        # Formato completo o más: dejar como está
                        formatted_nearby.append(city)

                logger.info(f"✅ Formatted nearby_cities: {formatted_nearby}")

                enriched_location = {
                    'original': location,
                    'city': enriched_data.get('city', location),
                    'state': state,
                    'country': country,
                    'nearby_cities': formatted_nearby,
                    'needs_expansion': enriched_data.get('needs_expansion', False)
                }

                # Guardar en caché (memoria + disco)
                self._location_cache[cache_key] = enriched_location
                self._save_location_cache()  # ← Persistir a disco

                logger.info(f"🌍 ENRIQUECIDO: {location} → {enriched_location['city']}, {enriched_location['state']}, {enriched_location['country']}")
                logger.info(f"📍 Ciudades cercanas: {enriched_location['nearby_cities']} (expandir: {enriched_location['needs_expansion']})")
                logger.info(f"💾 Caché guardado en: {self._cache_file}")

                return enriched_location
            else:
                raise ValueError("No se pudo parsear respuesta de Gemini")

        except Exception as e:
            logger.warning(f"⚠️ Error enriqueciendo ubicación: {e}, usando original")
            # Fallback: retornar ubicación original
            fallback = {
                'original': location,
                'city': location,
                'state': '',
                'country': detected_country or 'Argentina',
                'nearby_cities': [],
                'needs_expansion': False
            }
            self._location_cache[cache_key] = fallback
            self._save_location_cache()  # ← Persistir fallback también
            return fallback

    def _load_location_cache(self):
        """💾 Carga caché de enriquecimientos desde JSON"""
        import json
        import os

        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self._location_cache = cache_data.get('enrichments', {})
                    logger.info(f"✅ Caché de ubicaciones cargado: {len(self._location_cache)} ubicaciones")
            else:
                logger.info("📝 Caché de ubicaciones vacío, se creará automáticamente")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando caché de ubicaciones: {e}")
            self._location_cache = {}

    def _save_location_cache(self):
        """💾 Guarda caché de enriquecimientos en JSON"""
        import json
        import os

        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)

            cache_data = {
                'version': '1.0',
                'last_updated': str(time.time()),
                'enrichments': self._location_cache,
                'metadata': {
                    'total_enrichments': len(self._location_cache),
                    'cache_file': self._cache_file
                }
            }

            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Caché de ubicaciones guardado: {len(self._location_cache)} ubicaciones")
        except Exception as e:
            logger.error(f"❌ Error guardando caché de ubicaciones: {e}")