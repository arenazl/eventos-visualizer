"""
Servicio de Geolocalización y detección de barrios
"""
import httpx
import asyncio
from typing import Dict, Tuple, Optional
import json

# Barrios de Buenos Aires con coordenadas aproximadas
BARRIOS_BUENOS_AIRES = {
    "Palermo": (-34.5880, -58.4306),
    "Recoleta": (-34.5873, -58.3934),
    "San Telmo": (-34.6212, -58.3731),
    "La Boca": (-34.6345, -58.3631),
    "Puerto Madero": (-34.6037, -58.3616),
    "Belgrano": (-34.5628, -58.4565),
    "Caballito": (-34.6183, -58.4400),
    "Flores": (-34.6282, -58.4636),
    "Almagro": (-34.6036, -58.4201),
    "Villa Crespo": (-34.5990, -58.4400),
    "Colegiales": (-34.5739, -58.4493),
    "Núñez": (-34.5436, -58.4584),
    "Mataderos": (-34.6545, -58.5028),
    "Liniers": (-34.6418, -58.5225),
    "Villa Urquiza": (-34.5730, -58.4877),
    "Villa Devoto": (-34.6006, -58.5108),
    "Boedo": (-34.6301, -58.4163),
    "Barracas": (-34.6497, -58.3833),
    "Constitución": (-34.6270, -58.3814),
    "Retiro": (-34.5927, -58.3749),
    "Microcentro": (-34.6037, -58.3816),
    "San Nicolás": (-34.6033, -58.3816),
    "Monserrat": (-34.6100, -58.3800),
    "San Cristóbal": (-34.6227, -58.3964),
    "Parque Patricios": (-34.6380, -58.4053),
    "Nueva Pompeya": (-34.6519, -58.4163),
    "Villa Lugano": (-34.6793, -58.4728),
    "Villa Soldati": (-34.6619, -58.4397),
    "Versalles": (-34.6313, -58.5227),
    "Monte Castro": (-34.6190, -58.5050),
    "Parque Avellaneda": (-34.6451, -58.4783),
    "Villa Real": (-34.6151, -58.5320),
    "Vélez Sársfield": (-34.6318, -58.4931),
    "Villa Luro": (-34.6383, -58.5003),
    "Floresta": (-34.6276, -58.4838),
    "Villa General Mitre": (-34.6128, -58.4652),
    "Villa del Parque": (-34.6067, -58.4897),
    "Villa Santa Rita": (-34.6110, -58.4823),
    "Saavedra": (-34.5508, -58.4806),
    "Coghlan": (-34.5601, -58.4739),
    "Villa Pueyrredón": (-34.5872, -58.5036),
    "Agronomía": (-34.5990, -58.4889),
    "Parque Chas": (-34.5826, -58.4794),
    "Villa Ortúzar": (-34.5769, -58.4669),
    "Chacarita": (-34.5872, -58.4546),
    "Paternal": (-34.5990, -58.4669),
    "Balvanera": (-34.6090, -58.4000),
    "Abasto": (-34.6033, -58.4100),
    "Once": (-34.6090, -58.4070),
    "Congreso": (-34.6090, -58.3926)
}

# Ciudades del Gran Buenos Aires
CIUDADES_GBA = {
    "Avellaneda": (-34.6611, -58.3659),
    "Lanús": (-34.7000, -58.3933),
    "Quilmes": (-34.7203, -58.2547),
    "Lomas de Zamora": (-34.7570, -58.4065),
    "Banfield": (-34.7438, -58.3965),
    "Temperley": (-34.7750, -58.3975),
    "Adrogué": (-34.7984, -58.3813),
    "San Isidro": (-34.4708, -58.5286),
    "Vicente López": (-34.5272, -58.4798),
    "Olivos": (-34.5078, -58.4999),
    "Martinez": (-34.4889, -58.5039),
    "Tigre": (-34.4260, -58.5796),
    "San Fernando": (-34.4423, -58.5585),
    "Ramos Mejía": (-34.6407, -58.5631),
    "Morón": (-34.6534, -58.6197),
    "Haedo": (-34.6439, -58.5939),
    "Ciudadela": (-34.6383, -58.5433),
    "Caseros": (-34.6094, -58.5628),
    "San Martín": (-34.5769, -58.5350),
    "Villa Ballester": (-34.5550, -58.5569),
    "San Andrés": (-34.5550, -58.5297),
    "Hurlingham": (-34.5889, -58.6323),
    "Ituzaingó": (-34.6597, -58.6669),
    "Castelar": (-34.6521, -58.6294),
    "Merlo": (-34.6653, -58.7293),
    "Moreno": (-34.6343, -58.7915),
    "Marcos Paz": (-34.7806, -58.8378),
    "General Rodríguez": (-34.6090, -58.9506),
    "Luján": (-34.5633, -59.1180),
    "Pilar": (-34.4587, -58.9142),
    "Escobar": (-34.3511, -58.7956),
    "Zárate": (-34.0983, -59.0245),
    "Campana": (-34.1639, -58.9614),
    "Berazategui": (-34.7632, -58.2126),
    "Florencio Varela": (-34.8050, -58.2756),
    "La Plata": (-34.9215, -57.9545),
    "Berisso": (-34.8714, -57.8867),
    "Ensenada": (-34.8633, -57.9078),
    "Ezeiza": (-34.8541, -58.5231),
    "Cañuelas": (-35.0522, -58.7625),
    "San Vicente": (-35.0244, -58.4222),
    "Alejandro Korn": (-34.9833, -58.3833)
}

class GeolocationService:
    """
    Servicio para detectar ubicación del usuario
    """
    
    @staticmethod
    def get_nearest_neighborhood(lat: float, lon: float) -> Tuple[str, float]:
        """
        Encuentra el barrio más cercano a las coordenadas dadas
        """
        min_distance = float('inf')
        nearest_place = "Buenos Aires"
        
        # Combinar todos los lugares
        all_places = {**BARRIOS_BUENOS_AIRES, **CIUDADES_GBA}
        
        for place, coords in all_places.items():
            place_lat, place_lon = coords
            # Calcular distancia euclidiana simple
            distance = ((lat - place_lat) ** 2 + (lon - place_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_place = place
        
        # Convertir distancia aproximada a km (muy aproximado)
        distance_km = min_distance * 111  # 1 grado ≈ 111 km
        
        return nearest_place, distance_km
    
    @staticmethod
    async def get_location_by_ip(ip_address: str = None) -> Dict:
        """
        Obtiene la ubicación aproximada por IP
        Usa servicios gratuitos de geolocalización
        """
        try:
            # Si no hay IP, usar servicio que detecta la IP automáticamente
            if not ip_address or ip_address in ['127.0.0.1', 'localhost', '172.29.228.80']:
                url = "http://ip-api.com/json/"
            else:
                url = f"http://ip-api.com/json/{ip_address}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                
                if data.get('status') == 'success':
                    lat = data.get('lat', -34.6037)  # Default: Buenos Aires
                    lon = data.get('lon', -58.3816)
                    
                    # Encontrar el barrio más cercano
                    neighborhood, distance = GeolocationService.get_nearest_neighborhood(lat, lon)
                    
                    return {
                        'status': 'success',
                        'country': data.get('country', 'Argentina'),
                        'city': data.get('city', 'Buenos Aires'),
                        'neighborhood': neighborhood,
                        'distance_km': round(distance, 1),
                        'latitude': lat,
                        'longitude': lon,
                        'ip': data.get('query', ip_address),
                        'region': data.get('regionName', ''),
                        'zip': data.get('zip', ''),
                        'timezone': data.get('timezone', 'America/Argentina/Buenos_Aires'),
                        'isp': data.get('isp', '')
                    }
                else:
                    # Fallback a Buenos Aires centro
                    return {
                        'status': 'fallback',
                        'country': 'Argentina',
                        'city': 'Buenos Aires',
                        'neighborhood': 'Microcentro',
                        'distance_km': 0,
                        'latitude': -34.6037,
                        'longitude': -58.3816,
                        'ip': ip_address,
                        'timezone': 'America/Argentina/Buenos_Aires'
                    }
                    
        except Exception as e:
            # Si falla, devolver ubicación por defecto
            return {
                'status': 'error',
                'error': str(e),
                'country': 'Argentina',
                'city': 'Buenos Aires', 
                'neighborhood': 'Palermo',
                'distance_km': 0,
                'latitude': -34.5880,
                'longitude': -58.4306,
                'timezone': 'America/Argentina/Buenos_Aires'
            }
    
    @staticmethod
    def parse_location_from_text(text: str) -> Optional[Dict]:
        """
        Detecta barrios o ciudades mencionados en el texto
        Ej: "eventos en Caballito", "fiestas en Palermo"
        """
        text_lower = text.lower()
        found_locations = []
        
        # Buscar en barrios
        for barrio, coords in BARRIOS_BUENOS_AIRES.items():
            if barrio.lower() in text_lower:
                found_locations.append({
                    'type': 'barrio',
                    'name': barrio,
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'city': 'Buenos Aires'
                })
        
        # Buscar en ciudades del GBA
        for ciudad, coords in CIUDADES_GBA.items():
            if ciudad.lower() in text_lower:
                found_locations.append({
                    'type': 'ciudad',
                    'name': ciudad,
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'region': 'Gran Buenos Aires'
                })
        
        # Detectar palabras clave de ubicación
        location_keywords = {
            'cerca': 5,  # 5km radio
            'cerca de mi': 3,
            'cerca mio': 3,
            'cercano': 5,
            'por acá': 2,
            'por aca': 2,
            'zona norte': 20,
            'zona sur': 20,
            'zona oeste': 20,
            'capital': 15,
            'provincia': 30,
            'gba': 25,
            'gran buenos aires': 25,
            'caba': 15,
            'microcentro': 2,
            'centro': 3,
            'conurbano': 30
        }
        
        detected_radius = None
        for keyword, radius in location_keywords.items():
            if keyword in text_lower:
                detected_radius = radius
                break
        
        return {
            'locations': found_locations,
            'radius_km': detected_radius,
            'original_text': text
        }
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia en km entre dos puntos (aproximada)
        """
        import math
        
        # Radio de la Tierra en km
        R = 6371
        
        # Convertir a radianes
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Fórmula de Haversine
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return round(distance, 2)

# Instancia global
geolocation_service = GeolocationService()