"""
🏗️ INTEGRATED EVENTS SERVICE
Servicio que integra Intent Recognition + Gemini + Factory + Scrapers
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntegratedEventsService:
    """
    🏗️ SERVICIO INTEGRADO DE EVENTOS
    
    FLUJO COMPLETO:
    1. User Query → Intent Recognition (con Gemini)
    2. Jerarquía Geográfica → Smart URL Factory  
    3. URLs generadas → Scrapers específicos (Playwright/API)
    4. Eventos extraídos → Resultado unificado
    """
    
    def __init__(self):
        """Inicializar el servicio integrado"""
        self.intent_service = None
        self.smart_factory = None
        self.ticketmaster_scraper = None
        self.ticombo_scraper = None
        self.allevents_scraper = None
        self.stubhub_scraper = None
        self.ticketleap_scraper = None
        self.showpass_scraper = None
        logger.info("🏗️ Integrated Events Service inicializado")
    
    async def search_events_from_query(self, query: str, max_events: int = 20) -> Dict[str, Any]:
        """
        🔍 BUSCAR EVENTOS DESDE QUERY DE USUARIO
        
        FLUJO COMPLETO:
        User: "conciertos en Barcelona" 
        → Gemini: Barcelona, Cataluña, España
        → Factory: URLs de eventbrite.es, ticketmaster.es, meetup.com
        → Scrapers: Eventos reales extraídos
        
        Args:
            query: Query del usuario (ej: "eventos en Rosario")
            max_events: Máximo eventos por servicio
            
        Returns:
            Resultado completo con eventos y metadata
        """
        
        try:
            logger.info(f"🔍 Procesando query completo: '{query}'")
            
            # 1. ANÁLISIS DE INTENCIÓN CON GEMINI
            intent_result = await self._analyze_intent(query)
            if not intent_result['success']:
                return self._create_error_response("Error en análisis de intención", query)
            
            intent = intent_result['intent']
            hierarchy = intent.get('geographic_hierarchy', {})
            
            category = intent.get('categories', ['general'])[0] if intent.get('categories') else 'general'
            logger.info(f"🧠 Intent: {category} en {hierarchy.get('full_location', query)}")
            
            # 2. GENERACIÓN DE URLs CON FACTORY
            urls_data = await self._generate_urls_from_hierarchy(intent_result)
            
            # 3. EXTRACCIÓN DE EVENTOS CON SCRAPERS
            events_by_service = await self._extract_events_from_urls(urls_data, intent, max_events)
            
            # 4. RESULTADO UNIFICADO
            result = self._create_unified_result(query, intent_result, urls_data, events_by_service)
            
            logger.info(f"✅ Búsqueda completada: {result['metadata']['total_events']} eventos")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda integrada: {e}")
            return self._create_error_response(str(e), query)
    
    async def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        🧠 ANÁLIZAR INTENCIÓN CON ENDPOINT GLOBAL
        
        Usa el endpoint global /api/ai/analyze-intent que YA funciona
        y es el ÚNICO que debe obtener los 3 datos (ciudad, provincia, país)
        
        Args:
            query: Query del usuario
            
        Returns:
            Resultado del análisis de intención
        """
        
        try:
            import aiohttp
            
            # Llamar al endpoint global que YA funciona
            url = "http://172.29.228.80:8001/api/ai/analyze-intent"
            data = {"query": query}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Intent analizado via endpoint global")
                        return result
                    else:
                        error_msg = f"Error {response.status} en endpoint global"
                        logger.error(f"❌ {error_msg}")
                        return {"success": False, "error": error_msg}
            
        except Exception as e:
            logger.error(f"❌ Error llamando endpoint global: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_urls_from_hierarchy(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🏭 GENERAR URLs CON SMART FACTORY
        
        Args:
            intent_result: Resultado del análisis de intención
            
        Returns:
            URLs generadas por servicio
        """
        
        try:
            if not self.smart_factory:
                from services.smart_url_factory import smart_factory
                self.smart_factory = smart_factory
            
            return await self.smart_factory.generate_urls_for_location(intent_result)
            
        except Exception as e:
            logger.error(f"❌ Error generando URLs: {e}")
            return {"global_urls": [], "regional_urls": [], "metadata": {"error": str(e)}}
    
    async def _extract_events_from_urls(self, urls_data: Dict[str, Any], intent: Dict[str, Any], max_events: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        🤖 EXTRAER EVENTOS CON SCRAPERS
        
        Args:
            urls_data: URLs generadas por el factory
            intent: Datos de intención
            max_events: Máximo eventos por servicio
            
        Returns:
            Eventos extraídos por servicio
        """
        
        events_by_service = {}
        
        # Extraer eventos de servicios globales
        for service_data in urls_data.get('global_urls', []):
            service_name = service_data['service']
            urls = service_data.get('urls', [])
            
            if service_name == 'ticketmaster':
                # Usar Playwright scraper para Ticketmaster (integrado en método genérico)
                events = await self._extract_playwright_events(service_name, urls, intent, max_events)
                events_by_service[service_name] = events
            elif service_name == 'eventbrite':
                # Usar HTTP scraper para Eventbrite (más rápido)
                events = await self._extract_eventbrite_events(urls, intent, max_events)
                events_by_service[service_name] = events
            elif service_name in ['ticombo', 'allevents', 'stubhub', 'ticketleap', 'showpass']:
                # Usar Playwright scrapers para servicios avanzados
                events = await self._extract_playwright_events(service_name, urls, intent, max_events)
                events_by_service[service_name] = events
            elif service_name in ['meetup', 'bandsintown', 'dice', 'universe']:
                # Placeholder para otros scrapers
                events = await self._extract_generic_events(service_name, urls, intent, max_events)
                events_by_service[service_name] = events
        
        # Extraer eventos de servicios regionales
        for service_data in urls_data.get('regional_urls', []):
            service_name = service_data['service']
            urls = service_data.get('urls', [])
            events = await self._extract_generic_events(service_name, urls, intent, max_events)
            events_by_service[f"{service_name}_regional"] = events
        
        return events_by_service
    
    async def _extract_ticketmaster_events(self, urls: List[str], intent: Dict[str, Any], max_events: int) -> List[Dict[str, Any]]:
        """
        🎪 EXTRAER EVENTOS DE TICKETMASTER CON PLAYWRIGHT
        
        Args:
            urls: URLs de Ticketmaster (fallback jerárquico)
            intent: Datos de intención
            max_events: Máximo eventos
            
        Returns:
            Lista de eventos de Ticketmaster
        """
        
        try:
            if not self.ticketmaster_scraper:
                from services.ticketmaster_playwright_scraper import TicketmasterPlaywrightScraper
                self.ticketmaster_scraper = TicketmasterPlaywrightScraper()
            
            hierarchy = intent.get('geographic_hierarchy', {})
            country = hierarchy.get('country', '').lower()
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')
            
            # FALLBACK JERÁRQUICO: Ciudad → Provincia → País
            events = []
            
            # 1. Intentar con ciudad específica
            if city:
                logger.info(f"🎪 Ticketmaster: Probando ciudad '{city}'")
                events = await self.ticketmaster_scraper.search_by_location(city, country)
                if events:
                    logger.info(f"✅ Ticketmaster ciudad: {len(events)} eventos")
                    return events[:max_events]
            
            # 2. Fallback a provincia/región
            if not events and region and region != city:
                logger.info(f"🎪 Ticketmaster: Probando provincia '{region}'")
                events = await self.ticketmaster_scraper.search_by_location(region, country)
                if events:
                    logger.info(f"✅ Ticketmaster provincia: {len(events)} eventos")
                    return events[:max_events]
            
            # 3. Fallback a país completo
            if not events and country:
                logger.info(f"🎪 Ticketmaster: Probando país '{country}'")
                events = await self.ticketmaster_scraper.search_events(country, country, max_events)
                if events:
                    logger.info(f"✅ Ticketmaster país: {len(events)} eventos")
                    return events[:max_events]
            
            logger.warning("⚠️ Ticketmaster: No se encontraron eventos en ningún nivel")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de Ticketmaster: {e}")
            return []
    
    async def _extract_eventbrite_events(self, urls: List[str], intent: Dict[str, Any], max_events: int) -> List[Dict[str, Any]]:
        """
        🎫 EXTRAER EVENTOS DE EVENTBRITE (HTTP SCRAPER)
        
        Args:
            urls: URLs de Eventbrite con fallback jerárquico
            intent: Datos de intención
            max_events: Máximo eventos
            
        Returns:
            Lista de eventos de Eventbrite
        """
        
        try:
            # Placeholder: implementar scraper HTTP para Eventbrite
            logger.info(f"🎫 Eventbrite: Procesando {len(urls)} URLs")
            
            # Por ahora retornar eventos simulados para testing
            sample_events = [
                {
                    "title": f"Evento Eventbrite en {intent.get('geographic_hierarchy', {}).get('city', 'Ciudad')}",
                    "date": "2025-10-15 20:00",
                    "venue": "Venue Local",
                    "price": "$25.00",
                    "url": urls[0] if urls else "",
                    "source": "eventbrite",
                    "scraped_at": datetime.utcnow().isoformat()
                }
            ]
            
            logger.info(f"✅ Eventbrite: {len(sample_events)} eventos (simulados)")
            return sample_events[:max_events]
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de Eventbrite: {e}")
            return []
    
    async def _extract_playwright_events(self, service_name: str, urls: List[str], intent: Dict[str, Any], max_events: int) -> List[Dict[str, Any]]:
        """
        🎭 EXTRAER EVENTOS CON SCRAPERS PLAYWRIGHT (GENÉRICO)
        
        Maneja todos los scrapers que usan Playwright:
        - ticombo, allevents, stubhub, ticketleap, showpass
        
        Args:
            service_name: Nombre del servicio
            urls: URLs (fallback jerárquico)
            intent: Datos de intención
            max_events: Máximo eventos
            
        Returns:
            Lista de eventos del servicio
        """
        
        try:
            # Mapeo de servicios a scrapers
            scraper_mapping = {
                'ticketmaster': ('services.global_scrapers.ticketmaster_scraper', 'TicketmasterPlaywrightScraper', 'ticketmaster_scraper'),
                'ticombo': ('services.global_scrapers.ticombo_scraper', 'TicomboPlaywrightScraper', 'ticombo_scraper'),
                'allevents': ('services.global_scrapers.allevents_scraper', 'AllEventsPlaywrightScraper', 'allevents_scraper'),
                'stubhub': ('services.global_scrapers.stubhub_scraper', 'StubHubScraper', 'stubhub_scraper'),
                'ticketleap': ('services.global_scrapers.ticketleap_scraper', 'TicketLeapScraper', 'ticketleap_scraper'),
                'showpass': ('services.global_scrapers.showpass_scraper', 'ShowpassScraper', 'showpass_scraper')
            }
            
            if service_name not in scraper_mapping:
                logger.warning(f"⚠️ Servicio Playwright no configurado: {service_name}")
                return []
            
            module_path, class_name, attr_name = scraper_mapping[service_name]
            
            # Obtener o crear el scraper
            scraper = getattr(self, attr_name, None)
            if not scraper:
                module = __import__(module_path, fromlist=[class_name])
                scraper_class = getattr(module, class_name)
                scraper = scraper_class()
                setattr(self, attr_name, scraper)
            
            hierarchy = intent.get('geographic_hierarchy', {})
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')
            country = hierarchy.get('country', '')
            
            # FALLBACK JERÁRQUICO: Ciudad → Provincia → País
            events = []
            
            # 1. Intentar con ciudad específica
            if city:
                logger.info(f"🎭 {service_name}: Probando ciudad '{city}'")
                events = await scraper.search_events(city, max_events=max_events)
                if events:
                    logger.info(f"✅ {service_name} ciudad: {len(events)} eventos")
                    return events[:max_events]
            
            # 2. Fallback a provincia/región
            if not events and region and region != city:
                logger.info(f"🎭 {service_name}: Probando provincia '{region}'")
                events = await scraper.search_events(region, max_events=max_events)
                if events:
                    logger.info(f"✅ {service_name} provincia: {len(events)} eventos")
                    return events[:max_events]
            
            # 3. Fallback a país completo
            if not events and country:
                logger.info(f"🎭 {service_name}: Probando país '{country}'")
                events = await scraper.search_events(country, max_events=max_events)
                if events:
                    logger.info(f"✅ {service_name} país: {len(events)} eventos")
                    return events[:max_events]
            
            logger.warning(f"⚠️ {service_name}: No se encontraron eventos en ningún nivel")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de {service_name}: {e}")
            return []
    
    async def _extract_generic_events(self, service_name: str, urls: List[str], intent: Dict[str, Any], max_events: int) -> List[Dict[str, Any]]:
        """
        🔧 EXTRACTOR GENÉRICO PARA OTROS SERVICIOS
        
        Args:
            service_name: Nombre del servicio
            urls: URLs del servicio
            intent: Datos de intención
            max_events: Máximo eventos
            
        Returns:
            Lista de eventos del servicio
        """
        
        try:
            logger.info(f"🔧 {service_name}: Extractor genérico")
            
            # Placeholder para implementar scrapers específicos
            return []
            
        except Exception as e:
            logger.error(f"❌ Error en extractor genérico {service_name}: {e}")
            return []
    
    def _create_unified_result(self, query: str, intent_result: Dict[str, Any], urls_data: Dict[str, Any], events_by_service: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        📊 CREAR RESULTADO UNIFICADO
        
        Args:
            query: Query original
            intent_result: Resultado de análisis de intención
            urls_data: URLs generadas
            events_by_service: Eventos extraídos por servicio
            
        Returns:
            Resultado completo y estructurado
        """
        
        # Consolidar todos los eventos
        all_events = []
        service_stats = {}
        
        for service, events in events_by_service.items():
            all_events.extend(events)
            service_stats[service] = len(events)
        
        return {
            "success": True,
            "query": query,
            "intent": intent_result['intent'],
            "events": all_events,
            "events_by_service": events_by_service,
            "metadata": {
                "total_events": len(all_events),
                "services_used": list(service_stats.keys()),
                "service_stats": service_stats,
                "geographic_hierarchy": intent_result['intent'].get('geographic_hierarchy', {}),
                "urls_generated": len(urls_data.get('global_urls', [])) + len(urls_data.get('regional_urls', [])),
                "processed_at": datetime.utcnow().isoformat()
            }
        }
    
    def _create_error_response(self, error_message: str, query: str) -> Dict[str, Any]:
        """
        ❌ CREAR RESPUESTA DE ERROR
        
        Args:
            error_message: Mensaje de error
            query: Query original
            
        Returns:
            Respuesta de error estructurada
        """
        
        return {
            "success": False,
            "query": query,
            "error": error_message,
            "events": [],
            "events_by_service": {},
            "metadata": {
                "total_events": 0,
                "services_used": [],
                "service_stats": {},
                "processed_at": datetime.utcnow().isoformat()
            }
        }

# Instancia singleton global
integrated_service = IntegratedEventsService()