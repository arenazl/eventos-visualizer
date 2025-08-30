"""
API de Geolocalización - Detecta ubicación del usuario automáticamente
Prioridad: IP -> GPS del navegador -> Fallback Buenos Aires
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Optional
import httpx
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# Servicio gratuito de geolocalización por IP
IP_API_URL = "http://ip-api.com/json/"

# Mapeo de países a ciudades principales
COUNTRY_TO_CITY = {
    "Argentina": "Buenos Aires",
    "México": "Ciudad de México", 
    "Mexico": "Ciudad de México",
    "Colombia": "Bogotá",
    "Chile": "Santiago",
    "Brasil": "São Paulo",
    "Brazil": "São Paulo",
    "Perú": "Lima",
    "Peru": "Lima",
    "Uruguay": "Montevideo",
    "Venezuela": "Caracas",
    "Ecuador": "Quito",
    "Bolivia": "La Paz",
    "Paraguay": "Asunción"
}

# Ciudades con coordenadas conocidas
CITY_COORDINATES = {
    "Buenos Aires": {"lat": -34.6037, "lng": -58.3816, "country": "Argentina"},
    "Mendoza": {"lat": -32.8908, "lng": -68.8272, "country": "Argentina"},
    "Córdoba": {"lat": -31.4201, "lng": -64.1888, "country": "Argentina"},
    "Rosario": {"lat": -32.9442, "lng": -60.6505, "country": "Argentina"},
    "Mar del Plata": {"lat": -38.0023, "lng": -57.5575, "country": "Argentina"},
    "Salta": {"lat": -24.7859, "lng": -65.4117, "country": "Argentina"},
    "Tucumán": {"lat": -26.8241, "lng": -65.2226, "country": "Argentina"},
    "Ciudad de México": {"lat": 19.4326, "lng": -99.1332, "country": "México"},
    "Bogotá": {"lat": 4.7110, "lng": -74.0721, "country": "Colombia"},
    "Santiago": {"lat": -33.4489, "lng": -70.6693, "country": "Chile"},
    "São Paulo": {"lat": -23.5505, "lng": -46.6333, "country": "Brasil"},
    "Lima": {"lat": -12.0464, "lng": -77.0428, "country": "Perú"},
    "Montevideo": {"lat": -34.9011, "lng": -56.1645, "country": "Uruguay"}
}

@router.get("/detect")
async def detect_location(request: Request):
    """
    Detecta automáticamente la ubicación del usuario
    Prioridad: IP -> Fallback a Buenos Aires
    """
    try:
        # Obtener IP del cliente
        client_ip = request.client.host
        
        # Si es localhost o IP privada, usar IP pública
        if client_ip in ["127.0.0.1", "localhost"] or client_ip.startswith("172."):
            # Obtener IP pública
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("https://api.ipify.org?format=json")
                    if response.status_code == 200:
                        client_ip = response.json().get("ip", client_ip)
                except:
                    pass
        
        # Consultar servicio de geolocalización
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{IP_API_URL}{client_ip}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    city = data.get("city", "")
                    country = data.get("country", "")
                    lat = data.get("lat", 0)
                    lon = data.get("lon", 0)
                    
                    # Si no hay ciudad pero sí país, usar ciudad principal
                    if not city and country:
                        city = COUNTRY_TO_CITY.get(country, "Buenos Aires")
                    
                    # Si la ciudad no está en nuestro mapa, usar la más cercana
                    if city not in CITY_COORDINATES and country in COUNTRY_TO_CITY:
                        city = COUNTRY_TO_CITY[country]
                    
                    return {
                        "status": "success",
                        "method": "ip",
                        "location": {
                            "city": city or "Buenos Aires",
                            "country": country or "Argentina",
                            "latitude": lat if lat else CITY_COORDINATES.get(city, CITY_COORDINATES["Buenos Aires"])["lat"],
                            "longitude": lon if lon else CITY_COORDINATES.get(city, CITY_COORDINATES["Buenos Aires"])["lng"],
                            "display_name": f"{city}, {country}" if city and country else "Buenos Aires, Argentina"
                        },
                        "ip": client_ip,
                        "timestamp": datetime.utcnow().isoformat()
                    }
    
    except Exception as e:
        logger.error(f"Error detecting location: {e}")
    
    # Fallback a Buenos Aires
    return {
        "status": "fallback",
        "method": "default",
        "location": {
            "city": "Buenos Aires",
            "country": "Argentina",
            "latitude": -34.6037,
            "longitude": -58.3816,
            "display_name": "Buenos Aires, Argentina"
        },
        "message": "No se pudo detectar tu ubicación, usando Buenos Aires por defecto",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/set")
async def set_location(location_data: Dict):
    """
    Permite al usuario establecer manualmente su ubicación
    o recibir coordenadas GPS del navegador
    """
    try:
        lat = location_data.get("latitude")
        lng = location_data.get("longitude")
        city = location_data.get("city")
        
        # Si vienen coordenadas GPS, hacer geocoding inverso
        if lat and lng:
            # Por ahora, buscar la ciudad más cercana
            min_distance = float('inf')
            closest_city = "Buenos Aires"
            
            for city_name, coords in CITY_COORDINATES.items():
                # Calcular distancia simple (no es precisa pero sirve)
                distance = ((coords["lat"] - lat) ** 2 + (coords["lng"] - lng) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_city = city_name
            
            city_data = CITY_COORDINATES[closest_city]
            return {
                "status": "success",
                "method": "gps",
                "location": {
                    "city": closest_city,
                    "country": city_data["country"],
                    "latitude": lat,
                    "longitude": lng,
                    "display_name": f"{closest_city}, {city_data['country']}"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Si viene el nombre de la ciudad
        elif city:
            if city in CITY_COORDINATES:
                city_data = CITY_COORDINATES[city]
                return {
                    "status": "success",
                    "method": "manual",
                    "location": {
                        "city": city,
                        "country": city_data["country"],
                        "latitude": city_data["lat"],
                        "longitude": city_data["lng"],
                        "display_name": f"{city}, {city_data['country']}"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(status_code=400, detail=f"Ciudad '{city}' no encontrada")
        
        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar coordenadas o nombre de ciudad")
    
    except Exception as e:
        logger.error(f"Error setting location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cities")
async def get_available_cities():
    """
    Devuelve lista de ciudades disponibles para selección manual
    """
    cities = []
    for city, data in CITY_COORDINATES.items():
        cities.append({
            "city": city,
            "country": data["country"],
            "display_name": f"{city}, {data['country']}",
            "latitude": data["lat"],
            "longitude": data["lng"]
        })
    
    # Ordenar por país y luego por ciudad
    cities.sort(key=lambda x: (x["country"], x["city"]))
    
    return {
        "status": "success",
        "cities": cities,
        "total": len(cities)
    }