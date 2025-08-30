"""
Conector para Buenos Aires Data API
API oficial del Gobierno de la Ciudad de Buenos Aires
Datos abiertos de eventos culturales gratuitos
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class BuenosAiresDataConnector:
    """
    Conector para la API de datos abiertos de Buenos Aires
    No requiere autenticación y no tiene límites de rate
    """
    
    def __init__(self):
        self.base_url = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets"
        self.endpoints = {
            "agenda_cultural": "/cultura/agenda-cultural/agenda-cultural.json",
            "actividades_culturales": "/cultura/actividades-culturales/actividades-culturales.json",
            "museos": "/cultura/museos/museos.json",
            "bibliotecas": "/cultura/bibliotecas/bibliotecas.json",
            "centros_culturales": "/cultura/centros-culturales/centros-culturales.json",
            "teatros": "/cultura/teatros/teatros.json"
        }
        
        # Cache para evitar requests innecesarios
        self.cache = {}
        self.cache_duration = timedelta(hours=1)  # Cache de 1 hora
        
    async def fetch_all_events(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los eventos de todas las fuentes disponibles
        """
        all_events = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Obtener agenda cultural principal
            tasks.append(self.fetch_agenda_cultural(session))
            
            # Obtener actividades culturales
            tasks.append(self.fetch_actividades_culturales(session))
            
            # Obtener eventos de museos
            tasks.append(self.fetch_museum_events(session))
            
            # Obtener eventos de centros culturales
            tasks.append(self.fetch_cultural_centers_events(session))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_events.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching events: {result}")
        
        return self.normalize_events(all_events)
    
    async def fetch_agenda_cultural(self, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Obtiene eventos de la agenda cultural oficial
        """
        try:
            url = self.base_url + self.endpoints["agenda_cultural"]
            
            # Verificar cache
            if self.is_cached("agenda_cultural"):
                return self.cache["agenda_cultural"]["data"]
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Guardar en cache
                    self.cache["agenda_cultural"] = {
                        "data": data,
                        "timestamp": datetime.now()
                    }
                    
                    logger.info(f"✅ Buenos Aires Agenda Cultural: {len(data)} eventos obtenidos")
                    return data
                else:
                    logger.error(f"Error fetching agenda cultural: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching agenda cultural: {e}")
            return []
    
    async def fetch_actividades_culturales(self, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Obtiene actividades culturales (talleres, cursos, etc)
        """
        try:
            url = self.base_url + self.endpoints["actividades_culturales"]
            
            if self.is_cached("actividades_culturales"):
                return self.cache["actividades_culturales"]["data"]
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    self.cache["actividades_culturales"] = {
                        "data": data,
                        "timestamp": datetime.now()
                    }
                    
                    logger.info(f"✅ Buenos Aires Actividades: {len(data)} actividades obtenidas")
                    return data
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching actividades: {e}")
            return []
    
    async def fetch_museum_events(self, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Obtiene eventos de museos
        """
        try:
            # Primero obtener lista de museos
            url = self.base_url + self.endpoints["museos"]
            
            async with session.get(url) as response:
                if response.status == 200:
                    museos = await response.json()
                    
                    # Crear eventos ficticios para museos (visitas guiadas, exposiciones)
                    events = []
                    for museo in museos:
                        if museo.get("nombre") and museo.get("direccion"):
                            event = {
                                "titulo": f"Visita al {museo['nombre']}",
                                "descripcion": f"Entrada libre y gratuita. {museo.get('info', '')}",
                                "lugar": museo["nombre"],
                                "direccion": museo["direccion"],
                                "barrio": museo.get("barrio", ""),
                                "precio": 0,
                                "es_gratis": True,
                                "categoria": "museo",
                                "fuente": "museos_ba"
                            }
                            
                            # Agregar coordenadas si están disponibles
                            if museo.get("lat") and museo.get("long"):
                                event["latitud"] = museo["lat"]
                                event["longitud"] = museo["long"]
                            
                            events.append(event)
                    
                    logger.info(f"✅ Buenos Aires Museos: {len(events)} museos con entrada libre")
                    return events
                    
        except Exception as e:
            logger.error(f"Error fetching museum events: {e}")
            return []
    
    async def fetch_cultural_centers_events(self, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Obtiene eventos de centros culturales
        """
        try:
            url = self.base_url + self.endpoints["centros_culturales"]
            
            async with session.get(url) as response:
                if response.status == 200:
                    centros = await response.json()
                    
                    events = []
                    for centro in centros:
                        if centro.get("nombre"):
                            event = {
                                "titulo": f"Actividades en {centro['nombre']}",
                                "descripcion": "Centro cultural con actividades gratuitas",
                                "lugar": centro["nombre"],
                                "direccion": centro.get("direccion", ""),
                                "barrio": centro.get("barrio", ""),
                                "precio": 0,
                                "es_gratis": True,
                                "categoria": "centro_cultural",
                                "fuente": "centros_culturales_ba"
                            }
                            
                            if centro.get("lat") and centro.get("long"):
                                event["latitud"] = centro["lat"]
                                event["longitud"] = centro["long"]
                            
                            events.append(event)
                    
                    logger.info(f"✅ Buenos Aires Centros Culturales: {len(events)} centros")
                    return events
                    
        except Exception as e:
            logger.error(f"Error fetching cultural centers: {e}")
            return []
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza los eventos al formato universal de la aplicación
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Intentar parsear diferentes formatos de fecha
                start_date = self.parse_date(
                    event.get("fecha") or 
                    event.get("fecha_inicio") or 
                    event.get("start_date")
                )
                
                end_date = self.parse_date(
                    event.get("fecha_fin") or 
                    event.get("end_date")
                ) or start_date
                
                normalized_event = {
                    # Información básica
                    "title": event.get("titulo") or event.get("nombre") or "Evento sin título",
                    "description": event.get("descripcion") or event.get("info") or "",
                    
                    # Fechas (convertir a string ISO si es datetime)
                    "start_datetime": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                    "end_datetime": end_date.isoformat() if isinstance(end_date, datetime) else end_date,
                    
                    # Ubicación
                    "venue_name": event.get("lugar") or event.get("espacio") or "",
                    "venue_address": event.get("direccion") or event.get("domicilio") or "",
                    "neighborhood": event.get("barrio") or "",
                    "latitude": self.safe_float(event.get("latitud") or event.get("lat")),
                    "longitude": self.safe_float(event.get("longitud") or event.get("long")),
                    
                    # Categorización
                    "category": self.map_category(event.get("categoria") or event.get("tipo")),
                    "subcategory": event.get("subcategoria") or "",
                    "tags": self.extract_tags(event),
                    
                    # Precio
                    "price": 0,  # Todos los eventos de BA Data son gratuitos
                    "currency": "ARS",
                    "is_free": True,
                    
                    # Metadata
                    "source": "buenos_aires_data",
                    "source_id": event.get("id") or f"ba_{hash(str(event))}",
                    "event_url": event.get("link") or event.get("url") or "",
                    "image_url": event.get("imagen") or event.get("foto") or "",
                    
                    # Información adicional
                    "organizer": event.get("organizador") or "Gobierno de la Ciudad de Buenos Aires",
                    "contact_info": event.get("contacto") or event.get("telefono") or "",
                    "accessibility": event.get("accesibilidad") or "",
                    
                    # Timestamps
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing event: {e}")
                continue
        
        return normalized
    
    def parse_date(self, date_str: Any) -> Optional[datetime]:
        """
        Parsea diferentes formatos de fecha
        """
        if not date_str:
            return None
            
        if isinstance(date_str, datetime):
            return date_str
            
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except:
                continue
        
        # Si no se puede parsear, devolver fecha actual
        return datetime.now()
    
    def safe_float(self, value: Any) -> Optional[float]:
        """
        Convierte de forma segura a float
        """
        try:
            return float(value) if value else None
        except:
            return None
    
    def map_category(self, category: Optional[str]) -> str:
        """
        Mapea categorías de BA Data a categorías universales
        """
        if not category:
            return "cultural"
            
        category = category.lower()
        
        category_map = {
            "música": "music",
            "musica": "music",
            "concierto": "music",
            "recital": "music",
            
            "teatro": "theater",
            "obra": "theater",
            
            "danza": "dance",
            "baile": "dance",
            
            "cine": "film",
            "película": "film",
            "pelicula": "film",
            
            "arte": "art",
            "exposición": "art",
            "exposicion": "art",
            "muestra": "art",
            
            "museo": "museum",
            "visita": "museum",
            
            "taller": "workshop",
            "curso": "workshop",
            "clase": "workshop",
            
            "literatura": "literature",
            "libro": "literature",
            "lectura": "literature",
            
            "festival": "festival",
            "feria": "festival",
            
            "deporte": "sports",
            "deportivo": "sports",
            
            "gastronomía": "food",
            "gastronomia": "food",
            "comida": "food",
            
            "conferencia": "conference",
            "charla": "conference",
            "seminario": "conference",
        }
        
        for key, value in category_map.items():
            if key in category:
                return value
        
        return "cultural"  # Default
    
    def extract_tags(self, event: Dict) -> List[str]:
        """
        Extrae tags del evento
        """
        tags = []
        
        # Agregar categoría como tag
        if event.get("categoria"):
            tags.append(event["categoria"])
        
        # Agregar tipo como tag
        if event.get("tipo"):
            tags.append(event["tipo"])
        
        # Agregar barrio como tag
        if event.get("barrio"):
            tags.append(event["barrio"])
        
        # Agregar "gratis" como tag
        tags.append("gratis")
        tags.append("entrada libre")
        
        # Agregar tags especiales
        if "niños" in str(event).lower() or "infantil" in str(event).lower():
            tags.append("familiar")
            tags.append("niños")
        
        if "aire libre" in str(event).lower():
            tags.append("aire libre")
            tags.append("outdoor")
        
        return list(set(tags))  # Eliminar duplicados
    
    def is_cached(self, key: str) -> bool:
        """
        Verifica si hay datos en cache y si son válidos
        """
        if key not in self.cache:
            return False
            
        cached_data = self.cache[key]
        age = datetime.now() - cached_data["timestamp"]
        
        return age < self.cache_duration
    
    async def search_events(self, 
                           query: Optional[str] = None,
                           category: Optional[str] = None,
                           neighborhood: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict]:
        """
        Busca eventos con filtros específicos
        """
        all_events = await self.fetch_all_events()
        filtered = all_events
        
        # Filtrar por query
        if query:
            query_lower = query.lower()
            filtered = [e for e in filtered 
                       if query_lower in e["title"].lower() 
                       or query_lower in e["description"].lower()]
        
        # Filtrar por categoría
        if category:
            filtered = [e for e in filtered if e["category"] == category]
        
        # Filtrar por barrio
        if neighborhood:
            neighborhood_lower = neighborhood.lower()
            filtered = [e for e in filtered 
                       if neighborhood_lower in e.get("neighborhood", "").lower()]
        
        # Filtrar por fecha
        if date_from:
            filtered = [e for e in filtered 
                       if e["start_datetime"] and e["start_datetime"] >= date_from]
        
        if date_to:
            filtered = [e for e in filtered 
                       if e["start_datetime"] and e["start_datetime"] <= date_to]
        
        return filtered


# Función de prueba
async def test_buenos_aires_api():
    """
    Prueba el conector de Buenos Aires Data
    """
    connector = BuenosAiresDataConnector()
    
    print("🔍 Obteniendo eventos de Buenos Aires Data...")
    events = await connector.fetch_all_events()
    
    print(f"\n✅ Total eventos obtenidos: {len(events)}")
    
    # Mostrar algunos ejemplos
    for event in events[:5]:
        print(f"\n📌 {event['title']}")
        print(f"   📍 {event['venue_name']} - {event['neighborhood']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']}")
        print(f"   💰 {'GRATIS' if event['is_free'] else f'${event["price"]}'}")
    
    # Buscar eventos específicos
    print("\n🔍 Buscando eventos de música...")
    music_events = await connector.search_events(category="music")
    print(f"   Encontrados: {len(music_events)} eventos de música")
    
    return events


if __name__ == "__main__":
    asyncio.run(test_buenos_aires_api())