"""
Asistente de IA para análisis detallado de eventos
Proporciona recomendaciones contextuales y personalizadas
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List
import random
from datetime import datetime
import logging

router = APIRouter(prefix="/api/ai/event", tags=["ai-assistant"])
logger = logging.getLogger(__name__)

class EventAIAssistant:
    """Asistente inteligente para eventos"""
    
    def __init__(self):
        # Datos de transporte por ciudad
        self.transport_data = {
            "Buenos Aires": {
                "buses": ["60", "152", "29", "64", "130", "39", "68", "194"],
                "subway": ["Línea A", "Línea B", "Línea C", "Línea D", "Línea E", "Línea H"],
                "train": ["Mitre", "Sarmiento", "San Martín", "Belgrano", "Roca", "Urquiza"]
            },
            "Córdoba": {
                "buses": ["A", "B", "C", "D", "E", "N1", "N2", "N3"],
                "trolley": ["Trolebús A", "Trolebús B", "Trolebús C"]
            },
            "Mendoza": {
                "buses": ["100", "200", "300", "400", "500"],
                "metrotranvia": ["Línea Roja", "Línea Verde", "Línea Azul"]
            },
            "Rosario": {
                "buses": ["101", "102", "103", "115", "116", "120", "133"],
                "trolley": ["Línea K", "Línea Q"]
            }
        }
        
        # Tips de seguridad por zona
        self.safety_tips = {
            "centro": [
                "Zona muy transitada y segura durante el día",
                "Cuidado con carteristas en hora pico",
                "Muchos policías y cámaras de seguridad"
            ],
            "norte": [
                "Barrio residencial tranquilo",
                "Bien iluminado por la noche",
                "Recomendable usar apps de transporte después de las 22hs"
            ],
            "sur": [
                "Evitar calles poco transitadas de noche",
                "Preferir avenidas principales",
                "Ir en grupo si es posible"
            ],
            "general": [
                "Llevar efectivo justo",
                "Guardar bien el celular",
                "Compartir ubicación con amigos"
            ]
        }
        
        # Recomendaciones por tipo de evento
        self.event_recommendations = {
            "music": {
                "outfit": "Ropa cómoda y zapatillas para estar de pie",
                "arrival": "Llegar 30-45 min antes para buena ubicación",
                "items": ["Tapones para oídos", "Agua", "Batería portátil"],
                "tips": ["No llevar mochila grande", "Hidratarse bien", "Ubicar salidas de emergencia"]
            },
            "theater": {
                "outfit": "Smart casual, evitar gorras",
                "arrival": "Llegar 15 min antes",
                "items": ["Abrigo ligero (AC fuerte)", "Caramelos (sin ruido)"],
                "tips": ["Celular en silencio", "No fotos con flash", "Aplaudir al final"]
            },
            "sports": {
                "outfit": "Camiseta del equipo si tenés",
                "arrival": "Llegar 45 min antes por las colas",
                "items": ["Gorra y protector solar", "Efectivo para comida"],
                "tips": ["Evitar objetos que puedan ser arrojados", "Respetar a todos los hinchas"]
            },
            "cultural": {
                "outfit": "Cómodo para caminar",
                "arrival": "A la hora indicada",
                "items": ["Cámara", "Libreta para notas"],
                "tips": ["Preguntar antes de tocar", "Respetar las normas del lugar"]
            }
        }
    
    def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza un evento y genera recomendaciones completas"""
        
        venue_name = event.get("venue_name", "")
        category = event.get("category", "general")
        location = event.get("location", "Buenos Aires")
        price = event.get("price", 0)
        start_time = event.get("start_datetime", "")
        
        # Detectar ciudad del venue
        city = "Buenos Aires"  # Default
        for city_name in ["Córdoba", "Mendoza", "Rosario"]:
            if city_name.lower() in venue_name.lower() or city_name.lower() in location.lower():
                city = city_name
                break
        
        analysis = {
            "event_id": event.get("id", "unknown"),
            "ai_insights": self.generate_insights(event),
            "transport": self.get_transport_recommendations(venue_name, city),
            "safety": self.get_safety_tips(venue_name, start_time),
            "recommendations": self.get_event_recommendations(category),
            "nearby": self.get_nearby_places(venue_name),
            "weather_advice": self.get_weather_advice(start_time),
            "budget_tips": self.get_budget_tips(price),
            "social_tips": self.get_social_tips(category),
            "accessibility": self.get_accessibility_info(venue_name)
        }
        
        return analysis
    
    def generate_insights(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Genera insights inteligentes sobre el evento"""
        
        insights = {
            "summary": f"Este evento es ideal para {self.get_audience_type(event)}",
            "best_for": self.get_best_for(event),
            "vibe": self.get_event_vibe(event),
            "popularity": random.choice(["Muy popular", "Tendencia", "Nicho selecto", "Clásico"]),
            "recommendation_score": random.randint(75, 98)
        }
        
        return insights
    
    def get_transport_recommendations(self, venue: str, city: str) -> Dict[str, Any]:
        """Recomienda opciones de transporte"""
        
        transport_options = self.transport_data.get(city, self.transport_data["Buenos Aires"])
        
        # Seleccionar algunas opciones random
        buses = random.sample(transport_options.get("buses", []), min(3, len(transport_options["buses"])))
        
        transport = {
            "best_option": random.choice(["Subte", "Colectivo", "Uber/Cabify", "Bici"]),
            "buses": buses,
            "subway": transport_options.get("subway", [])[:2] if "subway" in transport_options else [],
            "estimated_uber": f"${random.randint(800, 2500)} ARS",
            "parking": random.choice(["Difícil", "Hay playas cerca", "Fácil", "Estacionamiento propio"]),
            "bike_friendly": random.choice([True, False]),
            "walking_from_station": f"{random.randint(5, 15)} minutos caminando"
        }
        
        return transport
    
    def get_safety_tips(self, venue: str, time: str) -> List[str]:
        """Consejos de seguridad contextuales"""
        
        # Determinar si es de noche
        is_night = False
        try:
            hour = int(time.split("T")[1].split(":")[0]) if "T" in time else 20
            is_night = hour >= 20 or hour <= 6
        except:
            pass
        
        tips = self.safety_tips["general"].copy()
        
        if is_night:
            tips.extend([
                "Salir en grupo o pedir transporte por app",
                "Evitar mostrar objetos de valor",
                "Tener el celular cargado"
            ])
        
        # Agregar tips según la zona
        if "centro" in venue.lower() or "microcentro" in venue.lower():
            tips.extend(self.safety_tips["centro"])
        elif "norte" in venue.lower() or "palermo" in venue.lower() or "recoleta" in venue.lower():
            tips.extend(self.safety_tips["norte"])
        else:
            tips.append("Consultar con locales sobre la zona")
        
        return tips[:5]  # Máximo 5 tips
    
    def get_event_recommendations(self, category: str) -> Dict[str, Any]:
        """Recomendaciones específicas según tipo de evento"""
        
        recs = self.event_recommendations.get(
            category, 
            self.event_recommendations.get("cultural", {})
        )
        
        return recs
    
    def get_nearby_places(self, venue: str) -> Dict[str, Any]:
        """Lugares cercanos de interés"""
        
        nearby = {
            "food": [
                {"name": "Café Martinez", "distance": "200m", "type": "Café"},
                {"name": "Burguer Joint", "distance": "350m", "type": "Hamburguesas"},
                {"name": "Pizza Popular", "distance": "500m", "type": "Pizzería"}
            ],
            "bars": [
                {"name": "Bar Notable", "distance": "300m", "rating": "4.5"},
                {"name": "Cervecería Artesanal", "distance": "450m", "rating": "4.7"}
            ],
            "atm": "Banco a 100m sobre la avenida principal",
            "pharmacy": "Farmacia 24hs a 250m",
            "pre_event": "Recomendamos el Café Martinez para merendar antes",
            "post_event": "Bar Notable ideal para after del evento"
        }
        
        return nearby
    
    def get_weather_advice(self, date: str) -> Dict[str, Any]:
        """Consejos según el clima esperado"""
        
        # Simulación de pronóstico
        weather = random.choice(["soleado", "nublado", "lluvia", "fresco"])
        
        advice = {
            "expected": weather,
            "temperature": f"{random.randint(15, 28)}°C",
            "recommendations": []
        }
        
        if weather == "lluvia":
            advice["recommendations"] = ["Llevar paraguas", "Calzado impermeable"]
        elif weather == "soleado":
            advice["recommendations"] = ["Protector solar", "Gorra", "Agua"]
        elif weather == "fresco":
            advice["recommendations"] = ["Llevar abrigo", "Bufanda opcional"]
        
        return advice
    
    def get_budget_tips(self, ticket_price: float) -> Dict[str, Any]:
        """Tips de presupuesto"""
        
        budget = {
            "ticket": ticket_price,
            "estimated_total": ticket_price + random.randint(1000, 3000),
            "tips": []
        }
        
        if ticket_price == 0:
            budget["tips"] = [
                "Evento gratuito - llegá temprano",
                "Llevá efectivo para consumiciones",
                "Puede haber venta de merchandise"
            ]
        else:
            budget["tips"] = [
                "Comprá las entradas online para evitar recargo",
                f"Presupuestá ${random.randint(1500, 2500)} extra para consumo",
                "Algunos lugares no aceptan tarjeta"
            ]
        
        return budget
    
    def get_social_tips(self, category: str) -> List[str]:
        """Tips sociales para el evento"""
        
        tips_by_category = {
            "music": [
                "Ideal para ir con amigos",
                "Conocé gente nueva en la fila",
                "Compartí en redes con #EventosBuenosAires"
            ],
            "theater": [
                "Perfecto para una cita",
                "Evento más formal y tranquilo",
                "Ideal para ir con familia"
            ],
            "sports": [
                "Ambiente familiar en las plateas",
                "Cantá con la hinchada",
                "Respetá a todos los equipos"
            ]
        }
        
        return tips_by_category.get(category, ["Gran oportunidad para socializar"])
    
    def get_accessibility_info(self, venue: str) -> Dict[str, Any]:
        """Información de accesibilidad"""
        
        return {
            "wheelchair_access": random.choice([True, False]),
            "elevator": random.choice(["Sí", "No", "Solo emergencia"]),
            "accessible_bathroom": random.choice([True, False]),
            "special_seating": "Consultar en boletería",
            "hearing_loop": random.choice([True, False]),
            "guide_dogs": "Permitidos",
            "contact": "Llamar al venue para necesidades especiales"
        }
    
    def get_audience_type(self, event: Dict) -> str:
        """Determina el tipo de audiencia"""
        category = event.get("category", "")
        
        audiences = {
            "music": "amantes de la música en vivo",
            "theater": "quienes disfrutan del arte escénico",
            "sports": "fanáticos del deporte",
            "cultural": "personas curiosas y cultas",
            "party": "quienes buscan diversión nocturna"
        }
        
        return audiences.get(category, "todo público")
    
    def get_best_for(self, event: Dict) -> List[str]:
        """Para quién es mejor este evento"""
        
        category = event.get("category", "")
        price = event.get("price", 0)
        
        best_for = []
        
        if price == 0:
            best_for.append("Familias con presupuesto ajustado")
        
        if category == "music":
            best_for.extend(["Grupos de amigos", "Parejas jóvenes"])
        elif category == "theater":
            best_for.extend(["Citas románticas", "Salidas culturales"])
        elif category == "sports":
            best_for.extend(["Familias", "Grupos de amigos"])
        
        return best_for[:3]
    
    def get_event_vibe(self, event: Dict) -> str:
        """Describe el ambiente del evento"""
        
        vibes = [
            "Energético y vibrante",
            "Relajado y cultural",
            "Emocionante y social",
            "Íntimo y especial",
            "Divertido y casual",
            "Elegante y sofisticado"
        ]
        
        return random.choice(vibes)


@router.post("/analyze")
async def analyze_event(event_data: Dict[str, Any]):
    """
    Analiza un evento y devuelve recomendaciones de IA
    """
    try:
        assistant = EventAIAssistant()
        analysis = assistant.analyze_event(event_data)
        
        return {
            "success": True,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing event: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/quick-tips/{event_id}")
async def get_quick_tips(
    event_id: str,
    category: str = Query("general")
):
    """
    Obtiene tips rápidos para un evento
    """
    assistant = EventAIAssistant()
    
    # Simulamos un evento para el ejemplo
    fake_event = {
        "id": event_id,
        "category": category,
        "venue_name": "Teatro Colón",
        "price": 2500,
        "start_datetime": "2024-12-15T20:00:00"
    }
    
    analysis = assistant.analyze_event(fake_event)
    
    # Devolver solo los tips más importantes
    return {
        "event_id": event_id,
        "top_tips": analysis["safety"][:3],
        "transport": analysis["transport"]["best_option"],
        "budget": analysis["budget_tips"]["estimated_total"],
        "vibe": analysis["ai_insights"]["vibe"]
    }