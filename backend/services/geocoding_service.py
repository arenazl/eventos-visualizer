"""
Servicio de Geolocalización y Búsqueda por Radio
Asigna coordenadas a eventos y permite búsqueda por distancia
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import hashlib
import re
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)

@dataclass
class GeoLocation:
    """Representa una ubicación geográfica"""
    latitude: float
    longitude: float
    name: str
    type: str  # barrio, ciudad, venue, etc
    confidence: float = 1.0  # 0-1 confianza en la precisión

class GeocodingService:
    """
    Servicio de geocoding para asignar coordenadas a eventos
    Funciona offline con base de datos precargada
    """
    
    def __init__(self):
        # Base de datos de ubicaciones en Latinoamérica
        self.locations_db = {
            # ARGENTINA - Buenos Aires
            "barrios_buenos_aires": {
                "palermo": GeoLocation(-34.5873, -58.4308, "Palermo", "barrio"),
                "recoleta": GeoLocation(-34.5873, -58.3916, "Recoleta", "barrio"),
                "belgrano": GeoLocation(-34.5627, -58.4563, "Belgrano", "barrio"),
                "san telmo": GeoLocation(-34.6212, -58.3719, "San Telmo", "barrio"),
                "puerto madero": GeoLocation(-34.6111, -58.3625, "Puerto Madero", "barrio"),
                "microcentro": GeoLocation(-34.6037, -58.3816, "Microcentro", "barrio"),
                "caballito": GeoLocation(-34.6194, -58.4310, "Caballito", "barrio"),
                "flores": GeoLocation(-34.6283, -58.4637, "Flores", "barrio"),
                "villa crespo": GeoLocation(-34.5986, -58.4400, "Villa Crespo", "barrio"),
                "colegiales": GeoLocation(-34.5736, -58.4476, "Colegiales", "barrio"),
                "nuñez": GeoLocation(-34.5438, -58.4555, "Núñez", "barrio"),
                "almagro": GeoLocation(-34.6084, -58.4209, "Almagro", "barrio"),
                "boedo": GeoLocation(-34.6295, -58.4141, "Boedo", "barrio"),
                "la boca": GeoLocation(-34.6368, -58.3630, "La Boca", "barrio"),
                "barracas": GeoLocation(-34.6475, -58.3820, "Barracas", "barrio"),
                "constitucion": GeoLocation(-34.6278, -58.3818, "Constitución", "barrio"),
                "once": GeoLocation(-34.6092, -58.4104, "Once", "barrio"),
                "villa urquiza": GeoLocation(-34.5721, -58.4871, "Villa Urquiza", "barrio"),
                "coghlan": GeoLocation(-34.5591, -58.4738, "Coghlan", "barrio"),
                "saavedra": GeoLocation(-34.5508, -58.4807, "Saavedra", "barrio"),
                "abasto": GeoLocation(-34.6033, -58.4104, "Abasto", "barrio"),
                "retiro": GeoLocation(-34.5925, -58.3745, "Retiro", "barrio"),
            },
            
            "venues_buenos_aires": {
                # Teatros
                "teatro colon": GeoLocation(-34.6010, -58.3831, "Teatro Colón", "venue", 1.0),
                "teatro gran rex": GeoLocation(-34.6034, -58.3796, "Teatro Gran Rex", "venue", 1.0),
                "teatro opera": GeoLocation(-34.6094, -58.3802, "Teatro Opera", "venue", 1.0),
                "teatro maipo": GeoLocation(-34.6088, -58.3794, "Teatro Maipo", "venue", 1.0),
                
                # Estadios y venues grandes
                "luna park": GeoLocation(-34.6022, -58.3686, "Luna Park", "venue", 1.0),
                "estadio obras": GeoLocation(-34.5430, -58.4503, "Estadio Obras", "venue", 1.0),
                "la bombonera": GeoLocation(-34.6357, -58.3647, "La Bombonera", "venue", 1.0),
                "monumental": GeoLocation(-34.5452, -58.4498, "Estadio Monumental", "venue", 1.0),
                "movistar arena": GeoLocation(-34.6438, -58.4453, "Movistar Arena", "venue", 1.0),
                
                # Clubs y música
                "niceto club": GeoLocation(-34.5859, -58.4386, "Niceto Club", "venue", 1.0),
                "la trastienda": GeoLocation(-34.6212, -58.3728, "La Trastienda", "venue", 1.0),
                "konex": GeoLocation(-34.5982, -58.4111, "Ciudad Cultural Konex", "venue", 1.0),
                "teatro vorterix": GeoLocation(-34.5771, -58.4456, "Teatro Vorterix", "venue", 1.0),
                "quality espacio": GeoLocation(-34.5899, -58.4238, "Quality Espacio", "venue", 1.0),
                
                # Centros culturales
                "centro cultural recoleta": GeoLocation(-34.5847, -58.3928, "Centro Cultural Recoleta", "venue", 1.0),
                "usina del arte": GeoLocation(-34.6425, -58.3537, "Usina del Arte", "venue", 1.0),
                "cck": GeoLocation(-34.6030, -58.3696, "Centro Cultural Kirchner", "venue", 1.0),
                "malba": GeoLocation(-34.5775, -58.4015, "MALBA", "venue", 1.0),
                
                # Parques
                "parque centenario": GeoLocation(-34.6064, -58.4357, "Parque Centenario", "venue", 0.9),
                "bosques de palermo": GeoLocation(-34.5694, -58.4177, "Bosques de Palermo", "venue", 0.9),
                "parque lezama": GeoLocation(-34.6288, -58.3694, "Parque Lezama", "venue", 0.9),
                "costanera sur": GeoLocation(-34.6111, -58.3528, "Costanera Sur", "venue", 0.9),
            },
            
            "ciudades_argentina": {
                "buenos aires": GeoLocation(-34.6037, -58.3816, "Buenos Aires", "ciudad"),
                "cordoba": GeoLocation(-31.4201, -64.1888, "Córdoba", "ciudad"),
                "rosario": GeoLocation(-32.9468, -60.6393, "Rosario", "ciudad"),
                "mendoza": GeoLocation(-32.8895, -68.8458, "Mendoza", "ciudad"),
                "la plata": GeoLocation(-34.9214, -57.9544, "La Plata", "ciudad"),
                "mar del plata": GeoLocation(-38.0055, -57.5426, "Mar del Plata", "ciudad"),
                "salta": GeoLocation(-24.7859, -65.4117, "Salta", "ciudad"),
                "tucuman": GeoLocation(-26.8083, -65.2176, "Tucumán", "ciudad"),
                "santa fe": GeoLocation(-31.6333, -60.7000, "Santa Fe", "ciudad"),
                "neuquen": GeoLocation(-38.9516, -68.0591, "Neuquén", "ciudad"),
                "bariloche": GeoLocation(-41.1335, -71.3103, "Bariloche", "ciudad"),
            },
            
            # MÉXICO
            "ciudades_mexico": {
                "ciudad de mexico": GeoLocation(19.4326, -99.1332, "Ciudad de México", "ciudad"),
                "cdmx": GeoLocation(19.4326, -99.1332, "CDMX", "ciudad"),
                "guadalajara": GeoLocation(20.6597, -103.3496, "Guadalajara", "ciudad"),
                "monterrey": GeoLocation(25.6866, -100.3161, "Monterrey", "ciudad"),
                "puebla": GeoLocation(19.0414, -98.2063, "Puebla", "ciudad"),
                "cancun": GeoLocation(21.1619, -86.8515, "Cancún", "ciudad"),
                "tijuana": GeoLocation(32.5149, -117.0382, "Tijuana", "ciudad"),
                "leon": GeoLocation(21.1221, -101.6827, "León", "ciudad"),
                "merida": GeoLocation(20.9674, -89.5926, "Mérida", "ciudad"),
                "queretaro": GeoLocation(20.5888, -100.3899, "Querétaro", "ciudad"),
            },
            
            "venues_mexico": {
                "palacio de los deportes": GeoLocation(19.4028, -99.0907, "Palacio de los Deportes", "venue"),
                "foro sol": GeoLocation(19.4028, -99.0858, "Foro Sol", "venue"),
                "auditorio nacional": GeoLocation(19.4253, -99.1945, "Auditorio Nacional", "venue"),
                "arena ciudad de mexico": GeoLocation(19.3955, -99.2847, "Arena Ciudad de México", "venue"),
                "teatro metropolitan": GeoLocation(19.4335, -99.1418, "Teatro Metropolitan", "venue"),
            },
            
            # COLOMBIA
            "ciudades_colombia": {
                "bogota": GeoLocation(4.7110, -74.0721, "Bogotá", "ciudad"),
                "medellin": GeoLocation(6.2476, -75.5658, "Medellín", "ciudad"),
                "cali": GeoLocation(3.4516, -76.5320, "Cali", "ciudad"),
                "barranquilla": GeoLocation(10.9685, -74.7813, "Barranquilla", "ciudad"),
                "cartagena": GeoLocation(10.3910, -75.4794, "Cartagena", "ciudad"),
                "bucaramanga": GeoLocation(7.1193, -73.1227, "Bucaramanga", "ciudad"),
            },
            
            "venues_colombia": {
                "movistar arena bogota": GeoLocation(4.6486, -74.0766, "Movistar Arena Bogotá", "venue"),
                "teatro colon bogota": GeoLocation(4.5968, -74.0756, "Teatro Colón Bogotá", "venue"),
                "estadio el campin": GeoLocation(4.6473, -74.0779, "Estadio El Campín", "venue"),
            },
            
            # CHILE
            "ciudades_chile": {
                "santiago": GeoLocation(-33.4489, -70.6693, "Santiago", "ciudad"),
                "valparaiso": GeoLocation(-33.0458, -71.6197, "Valparaíso", "ciudad"),
                "concepcion": GeoLocation(-36.8261, -73.0498, "Concepción", "ciudad"),
                "la serena": GeoLocation(-29.9027, -71.2520, "La Serena", "ciudad"),
                "antofagasta": GeoLocation(-23.6500, -70.4000, "Antofagasta", "ciudad"),
                "temuco": GeoLocation(-38.7484, -72.6194, "Temuco", "ciudad"),
                "viña del mar": GeoLocation(-33.0153, -71.5501, "Viña del Mar", "ciudad"),
            },
            
            "venues_chile": {
                "movistar arena santiago": GeoLocation(-33.4635, -70.6614, "Movistar Arena Santiago", "venue"),
                "teatro municipal santiago": GeoLocation(-33.4418, -70.6506, "Teatro Municipal de Santiago", "venue"),
                "teatro caupolican": GeoLocation(-33.4647, -70.6463, "Teatro Caupolicán", "venue"),
                "estadio nacional": GeoLocation(-33.4648, -70.6107, "Estadio Nacional", "venue"),
            },
            
            # BRASIL
            "ciudades_brasil": {
                "sao paulo": GeoLocation(-23.5505, -46.6333, "São Paulo", "ciudad"),
                "rio de janeiro": GeoLocation(-22.9068, -43.1729, "Rio de Janeiro", "ciudad"),
                "belo horizonte": GeoLocation(-19.9167, -43.9345, "Belo Horizonte", "ciudad"),
                "porto alegre": GeoLocation(-30.0346, -51.2177, "Porto Alegre", "ciudad"),
                "brasilia": GeoLocation(-15.7975, -47.8919, "Brasília", "ciudad"),
                "salvador": GeoLocation(-12.9714, -38.5014, "Salvador", "ciudad"),
                "fortaleza": GeoLocation(-3.7319, -38.5267, "Fortaleza", "ciudad"),
                "curitiba": GeoLocation(-25.4244, -49.2654, "Curitiba", "ciudad"),
                "recife": GeoLocation(-8.0476, -34.8770, "Recife", "ciudad"),
                "manaus": GeoLocation(-3.1019, -60.0250, "Manaus", "ciudad"),
            },
            
            "venues_brasil": {
                "allianz parque": GeoLocation(-23.5273, -46.6785, "Allianz Parque", "venue"),
                "maracana": GeoLocation(-22.9121, -43.2302, "Maracanã", "venue"),
                "jeunesse arena": GeoLocation(-22.9790, -43.2173, "Jeunesse Arena", "venue"),
                "teatro municipal sp": GeoLocation(-23.5453, -46.6389, "Teatro Municipal de São Paulo", "venue"),
            },
            
            # PERÚ
            "ciudades_peru": {
                "lima": GeoLocation(-12.0464, -77.0428, "Lima", "ciudad"),
                "arequipa": GeoLocation(-16.4090, -71.5375, "Arequipa", "ciudad"),
                "cusco": GeoLocation(-13.5319, -71.9675, "Cusco", "ciudad"),
                "trujillo": GeoLocation(-8.1116, -79.0288, "Trujillo", "ciudad"),
                "chiclayo": GeoLocation(-6.7714, -79.8409, "Chiclayo", "ciudad"),
            },
            
            # URUGUAY
            "ciudades_uruguay": {
                "montevideo": GeoLocation(-34.9011, -56.1645, "Montevideo", "ciudad"),
                "punta del este": GeoLocation(-34.9475, -54.9338, "Punta del Este", "ciudad"),
                "colonia": GeoLocation(-34.4626, -57.8396, "Colonia del Sacramento", "ciudad"),
            }
        }
        
        # Cache de geocoding
        self.geocoding_cache = {}
    
    def get_coordinates(self, location_text: str, 
                        city: str = "Buenos Aires", 
                        country: str = "Argentina") -> Optional[GeoLocation]:
        """
        Obtiene coordenadas para un texto de ubicación
        Intenta múltiples estrategias de matching
        """
        # Normalizar texto
        location_lower = self._normalize_text(location_text)
        city_lower = self._normalize_text(city)
        
        # Check cache
        cache_key = f"{location_lower}_{city_lower}_{country}"
        if cache_key in self.geocoding_cache:
            return self.geocoding_cache[cache_key]
        
        # Estrategia 1: Buscar venue exacto
        result = self._search_venue(location_lower, city_lower)
        if result:
            self.geocoding_cache[cache_key] = result
            return result
        
        # Estrategia 2: Buscar barrio
        result = self._search_neighborhood(location_lower, city_lower)
        if result:
            self.geocoding_cache[cache_key] = result
            return result
        
        # Estrategia 3: Extraer barrio del texto
        result = self._extract_neighborhood_from_text(location_text, city_lower)
        if result:
            self.geocoding_cache[cache_key] = result
            return result
        
        # Estrategia 4: Devolver coordenadas de la ciudad
        result = self._get_city_coordinates(city, country)
        if result:
            result.confidence = 0.5  # Baja confianza
            self.geocoding_cache[cache_key] = result
            return result
        
        # Fallback: Buenos Aires centro
        default = GeoLocation(-34.6037, -58.3816, "Buenos Aires", "ciudad", 0.3)
        self.geocoding_cache[cache_key] = default
        return default
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para búsqueda"""
        if not text:
            return ""
        
        text = text.lower().strip()
        # Remover acentos comunes
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _search_venue(self, venue_text: str, city: str) -> Optional[GeoLocation]:
        """Busca un venue específico"""
        # Determinar qué base de datos usar según la ciudad
        if "buenos aires" in city or "argentina" in city:
            venues = self.locations_db.get("venues_buenos_aires", {})
        elif "mexico" in city or "cdmx" in city or "ciudad de mexico" in city:
            venues = self.locations_db.get("venues_mexico", {})
        elif "bogota" in city or "colombia" in city:
            venues = self.locations_db.get("venues_colombia", {})
        elif "santiago" in city or "chile" in city:
            venues = self.locations_db.get("venues_chile", {})
        elif "sao paulo" in city or "brasil" in city or "brazil" in city:
            venues = self.locations_db.get("venues_brasil", {})
        else:
            venues = {}
        
        # Buscar match exacto o parcial
        for venue_key, location in venues.items():
            if venue_key in venue_text or venue_text in venue_key:
                return location
        
        # Buscar en todos los venues si no encontramos en la ciudad específica
        for db_key in self.locations_db:
            if "venues_" in db_key:
                for venue_key, location in self.locations_db[db_key].items():
                    if venue_key in venue_text or venue_text in venue_key:
                        location.confidence = 0.8  # Menor confianza si es de otra ciudad
                        return location
        
        return None
    
    def _search_neighborhood(self, text: str, city: str) -> Optional[GeoLocation]:
        """Busca un barrio"""
        if "buenos aires" in city:
            barrios = self.locations_db.get("barrios_buenos_aires", {})
            
            for barrio_key, location in barrios.items():
                if barrio_key in text:
                    return location
        
        return None
    
    def _extract_neighborhood_from_text(self, text: str, city: str) -> Optional[GeoLocation]:
        """Extrae barrio del texto usando patterns"""
        text_lower = text.lower()
        
        # Patterns para extraer barrio
        patterns = [
            r'barrio\s+(\w+)',
            r'en\s+(\w+)',
            r',\s*(\w+)$',
            r'zona\s+(\w+)',
        ]
        
        if "buenos aires" in city:
            barrios = self.locations_db.get("barrios_buenos_aires", {})
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    potential_barrio = self._normalize_text(match.group(1))
                    if potential_barrio in barrios:
                        return barrios[potential_barrio]
        
        return None
    
    def _get_city_coordinates(self, city: str, country: str) -> Optional[GeoLocation]:
        """Obtiene coordenadas de una ciudad"""
        city_lower = self._normalize_text(city)
        
        # Buscar en todas las ciudades
        for db_key in self.locations_db:
            if "ciudades_" in db_key:
                cities = self.locations_db[db_key]
                if city_lower in cities:
                    return cities[city_lower]
        
        # Buscar match parcial
        for db_key in self.locations_db:
            if "ciudades_" in db_key:
                for city_key, location in self.locations_db[db_key].items():
                    if city_key in city_lower or city_lower in city_key:
                        return location
        
        return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia entre dos puntos en kilómetros
        Usa la fórmula de Haversine para mayor precisión
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    
    def filter_events_by_radius(self, 
                               events: List[Dict[str, Any]], 
                               user_lat: float, 
                               user_lon: float, 
                               radius_km: float) -> List[Dict[str, Any]]:
        """
        Filtra eventos dentro de un radio específico
        """
        filtered_events = []
        
        for event in events:
            # Obtener coordenadas del evento
            event_lat = event.get("latitude")
            event_lon = event.get("longitude")
            
            # Si no tiene coordenadas, intentar geocoding
            if not event_lat or not event_lon:
                location_text = event.get("venue_name", "") + " " + event.get("venue_address", "")
                city = event.get("city", "Buenos Aires")
                
                geo_location = self.get_coordinates(location_text, city)
                if geo_location:
                    event_lat = geo_location.latitude
                    event_lon = geo_location.longitude
                    # Actualizar el evento con las coordenadas
                    event["latitude"] = event_lat
                    event["longitude"] = event_lon
                    event["location_confidence"] = geo_location.confidence
            
            # Calcular distancia
            if event_lat and event_lon:
                distance = self.calculate_distance(user_lat, user_lon, event_lat, event_lon)
                event["distance_km"] = round(distance, 2)
                
                # Incluir si está dentro del radio
                if distance <= radius_km:
                    filtered_events.append(event)
        
        # Ordenar por distancia
        filtered_events.sort(key=lambda x: x.get("distance_km", float('inf')))
        
        return filtered_events
    
    def get_nearby_areas(self, lat: float, lon: float, radius_km: float = 10) -> List[Dict[str, Any]]:
        """
        Obtiene áreas cercanas (barrios, venues) dentro de un radio
        """
        nearby = []
        
        # Buscar en todos los locations
        for category in self.locations_db.values():
            for location in category.values():
                distance = self.calculate_distance(lat, lon, location.latitude, location.longitude)
                
                if distance <= radius_km:
                    nearby.append({
                        "name": location.name,
                        "type": location.type,
                        "distance_km": round(distance, 2),
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    })
        
        # Ordenar por distancia
        nearby.sort(key=lambda x: x["distance_km"])
        
        return nearby
    
    def suggest_search_radius(self, city: str) -> Dict[str, int]:
        """
        Sugiere radios de búsqueda basados en la ciudad
        """
        # Ciudades grandes necesitan radios más pequeños
        large_cities = ["buenos aires", "sao paulo", "ciudad de mexico", "santiago", "bogota"]
        medium_cities = ["cordoba", "rosario", "montevideo", "guadalajara", "medellin"]
        
        city_lower = self._normalize_text(city)
        
        if any(lc in city_lower for lc in large_cities):
            return {
                "walking": 2,      # A pie
                "nearby": 5,       # Cerca
                "local": 10,       # Local
                "city": 25,        # Ciudad
                "metro": 50,       # Área metropolitana
                "region": 100      # Regional
            }
        elif any(mc in city_lower for mc in medium_cities):
            return {
                "walking": 3,
                "nearby": 8,
                "local": 15,
                "city": 30,
                "metro": 60,
                "region": 120
            }
        else:
            # Ciudades pequeñas
            return {
                "walking": 5,
                "nearby": 10,
                "local": 20,
                "city": 40,
                "metro": 80,
                "region": 150
            }
    
    def enrich_event_with_location(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece un evento con información de geolocalización
        """
        # Si ya tiene coordenadas precisas, solo validar
        if event.get("latitude") and event.get("longitude"):
            event["location_source"] = "original"
            event["location_confidence"] = 1.0
            return event
        
        # Intentar geocoding
        location_text = " ".join(filter(None, [
            event.get("venue_name", ""),
            event.get("venue_address", ""),
            event.get("neighborhood", ""),
        ]))
        
        city = event.get("city", "Buenos Aires")
        country = event.get("country", "Argentina")
        
        geo_location = self.get_coordinates(location_text, city, country)
        
        if geo_location:
            event["latitude"] = geo_location.latitude
            event["longitude"] = geo_location.longitude
            event["location_confidence"] = geo_location.confidence
            event["location_source"] = "geocoded"
            event["location_type"] = geo_location.type
            
            # Agregar información adicional si es un venue conocido
            if geo_location.type == "venue":
                event["venue_verified"] = True
            
            # Agregar barrio si no lo tiene
            if not event.get("neighborhood") and geo_location.type == "barrio":
                event["neighborhood"] = geo_location.name
        else:
            # Fallback: coordenadas de la ciudad
            logger.warning(f"No se pudo geocodificar: {location_text} en {city}")
            city_coords = self._get_city_coordinates(city, country)
            if city_coords:
                event["latitude"] = city_coords.latitude
                event["longitude"] = city_coords.longitude
                event["location_confidence"] = 0.3
                event["location_source"] = "city_center"
        
        return event


# Singleton
geocoding_service = GeocodingService()


# Funciones de utilidad
def get_user_location_from_ip(ip_address: str = None) -> Tuple[float, float]:
    """
    Obtiene ubicación aproximada del usuario por IP
    Por ahora devuelve Buenos Aires como default
    """
    # TODO: Implementar geolocalización por IP real
    return -34.6037, -58.3816  # Buenos Aires


def calculate_relevance_by_distance(distance_km: float) -> float:
    """
    Calcula un score de relevancia basado en distancia
    """
    if distance_km <= 1:
        return 1.0
    elif distance_km <= 5:
        return 0.9
    elif distance_km <= 10:
        return 0.8
    elif distance_km <= 20:
        return 0.7
    elif distance_km <= 30:
        return 0.6
    elif distance_km <= 50:
        return 0.5
    elif distance_km <= 100:
        return 0.3
    else:
        return 0.1


# Ejemplo de uso
def example_usage():
    """Ejemplo de uso del servicio de geocoding"""
    
    service = geocoding_service
    
    # Test 1: Geocodificar venues conocidos
    print("🗺️ Test de geocoding de venues:")
    venues_test = [
        "Teatro Colón",
        "Luna Park",
        "Niceto Club",
        "Parque Centenario",
        "Centro Cultural Recoleta"
    ]
    
    for venue in venues_test:
        location = service.get_coordinates(venue, "Buenos Aires")
        if location:
            print(f"✅ {venue}: {location.latitude}, {location.longitude} (confianza: {location.confidence})")
    
    # Test 2: Filtrar eventos por radio
    print("\n📍 Test de filtrado por radio:")
    
    # Eventos de prueba
    events = [
        {"title": "Concierto en Teatro Colón", "venue_name": "Teatro Colón"},
        {"title": "Festival en Parque Centenario", "venue_name": "Parque Centenario"},
        {"title": "Show en Luna Park", "venue_name": "Luna Park"},
        {"title": "Fiesta en Niceto", "venue_name": "Niceto Club"},
        {"title": "Evento en Rosario", "city": "Rosario", "venue_name": "Centro"},
    ]
    
    # Enriquecer con coordenadas
    for event in events:
        service.enrich_event_with_location(event)
    
    # Filtrar desde Palermo con radio de 10km
    user_lat, user_lon = -34.5873, -58.4308  # Palermo
    
    nearby_events = service.filter_events_by_radius(events, user_lat, user_lon, radius_km=10)
    
    print(f"\nEventos a menos de 10km de Palermo:")
    for event in nearby_events:
        print(f"  - {event['title']}: {event['distance_km']}km")
    
    # Test 3: Áreas cercanas
    print("\n🏘️ Áreas cercanas a Palermo:")
    nearby_areas = service.get_nearby_areas(user_lat, user_lon, radius_km=5)
    for area in nearby_areas[:5]:
        print(f"  - {area['name']} ({area['type']}): {area['distance_km']}km")


if __name__ == "__main__":
    example_usage()