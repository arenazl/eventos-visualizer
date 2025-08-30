"""
API endpoints para geolocalización y detección de ubicación
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.geolocation import geolocation_service

router = APIRouter()

class LocationRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    text: Optional[str] = None

class SaveLocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    neighborhood: str
    city: str
    consent: bool = True

@router.get("/detect")
async def detect_location_by_ip(request: Request):
    """
    Detecta la ubicación del usuario por su IP
    """
    try:
        # Obtener IP del cliente
        client_ip = request.client.host
        
        # Si es una IP local, intentar obtener la IP real desde headers
        if client_ip in ['127.0.0.1', 'localhost', '172.29.228.80']:
            # Intentar obtener desde headers de proxy
            forwarded_for = request.headers.get('X-Forwarded-For')
            real_ip = request.headers.get('X-Real-IP')
            
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
            elif real_ip:
                client_ip = real_ip
        
        # Obtener ubicación por IP
        location_data = await geolocation_service.get_location_by_ip(client_ip)
        
        return {
            "status": "success",
            "location": location_data,
            "message": f"📍 Detectamos que estás en {location_data['neighborhood']}, {location_data['city']}"
        }
        
    except Exception as e:
        # En caso de error, devolver ubicación por defecto
        return {
            "status": "fallback",
            "location": {
                "neighborhood": "Palermo",
                "city": "Buenos Aires",
                "country": "Argentina",
                "latitude": -34.5880,
                "longitude": -58.4306
            },
            "message": "📍 Ubicación aproximada: Palermo, Buenos Aires"
        }

@router.post("/nearest")
async def get_nearest_neighborhood(location: LocationRequest):
    """
    Encuentra el barrio más cercano a las coordenadas dadas
    """
    try:
        if location.latitude and location.longitude:
            neighborhood, distance = geolocation_service.get_nearest_neighborhood(
                location.latitude, 
                location.longitude
            )
            
            return {
                "status": "success",
                "neighborhood": neighborhood,
                "distance_km": distance,
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                },
                "message": f"📍 Estás en {neighborhood}" if distance < 2 else f"📍 Estás a {distance:.1f} km de {neighborhood}"
            }
        else:
            raise ValueError("Coordenadas no proporcionadas")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/parse-text")
async def parse_location_from_text(request: LocationRequest):
    """
    Detecta ubicaciones mencionadas en el texto
    Ej: "eventos en Caballito", "fiestas cerca de Palermo"
    """
    try:
        if not request.text:
            raise ValueError("No se proporcionó texto para analizar")
        
        result = geolocation_service.parse_location_from_text(request.text)
        
        # Construir mensaje de respuesta
        if result['locations']:
            location_names = [loc['name'] for loc in result['locations']]
            message = f"🔍 Buscando en: {', '.join(location_names)}"
        else:
            message = "🔍 Buscando en toda la ciudad"
        
        if result['radius_km']:
            message += f" (radio de {result['radius_km']} km)"
        
        return {
            "status": "success",
            "parsed": result,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save-user-location")
async def save_user_location(location: SaveLocationRequest):
    """
    Guarda la ubicación del usuario con su consentimiento
    """
    try:
        if not location.consent:
            return {
                "status": "rejected",
                "message": "Ubicación no guardada - Sin consentimiento del usuario"
            }
        
        # Aquí guardaríamos en la base de datos
        # Por ahora solo devolvemos success
        
        return {
            "status": "success",
            "message": f"✅ Ubicación guardada: {location.neighborhood}, {location.city}",
            "data": {
                "user_id": location.user_id,
                "neighborhood": location.neighborhood,
                "city": location.city,
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neighborhoods")
async def get_all_neighborhoods():
    """
    Obtiene la lista de todos los barrios y ciudades disponibles
    """
    from services.geolocation import BARRIOS_BUENOS_AIRES, CIUDADES_GBA
    
    return {
        "status": "success",
        "barrios_caba": list(BARRIOS_BUENOS_AIRES.keys()),
        "ciudades_gba": list(CIUDADES_GBA.keys()),
        "total": len(BARRIOS_BUENOS_AIRES) + len(CIUDADES_GBA)
    }

@router.get("/distance")
async def calculate_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
):
    """
    Calcula la distancia entre dos puntos
    """
    try:
        distance = geolocation_service.calculate_distance(lat1, lon1, lat2, lon2)
        
        return {
            "status": "success",
            "distance_km": distance,
            "message": f"📏 Distancia: {distance} km"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))