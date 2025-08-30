"""
Cultural Context Engine - Interface + City Implementations
Smart culturally-aware recommendations for global travelers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, time
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TransportType(Enum):
    METRO = "metro"
    BUS = "bus"
    BICYCLE = "bicycle"
    TAXI = "taxi"
    WALKING = "walking"
    TRAM = "tram"
    TRAIN = "train"

class EventType(Enum):
    NIGHTLIFE = "nightlife"
    CULTURAL = "cultural"
    SPORTS = "sports"
    MUSIC = "music"
    DINING = "dining"
    BUSINESS = "business"

# 🌍 INTERFACE BASE
class CulturalContext(ABC):
    """
    Interface base para contexto cultural de cada ciudad
    Cada ciudad implementa sus propias reglas culturales
    """
    
    def __init__(self, city_name: str, country: str):
        self.city_name = city_name
        self.country = country
    
    @abstractmethod
    def get_transport_advice(self, venue_address: str, current_time: datetime) -> Dict[str, Any]:
        """Advice específico de transporte para esta ciudad"""
        pass
    
    @abstractmethod
    def get_timing_advice(self, event_type: EventType, start_time: datetime) -> Dict[str, Any]:
        """Advice sobre horarios culturales (cuándo llegar, cuándo comer, etc.)"""
        pass
    
    @abstractmethod
    def get_social_context(self, event_type: EventType, group_size: int) -> Dict[str, str]:
        """Normas sociales y expectativas culturales"""
        pass
    
    @abstractmethod
    def get_practical_tips(self, event_type: EventType) -> List[str]:
        """Tips prácticos específicos de la cultura local"""
        pass
    
    @abstractmethod
    def get_local_customs(self) -> Dict[str, str]:
        """Costumbres locales importantes"""
        pass

# 🇦🇷 ARGENTINA IMPLEMENTATION
class BuenosAiresContext(CulturalContext):
    """Contexto cultural específico de Buenos Aires"""
    
    def __init__(self):
        super().__init__("Buenos Aires", "Argentina")
        
        # Datos específicos de Buenos Aires
        self.colectivo_lines = {
            "Centro": ["29", "152", "60", "45"],
            "Palermo": ["93", "130", "41"], 
            "San Telmo": ["29", "152", "126"],
            "Puerto Madero": ["4", "20", "126"]
        }
        
        self.subte_lines = {
            "A": "Plaza de Mayo - San Pedrito",
            "B": "Juan Manuel de Rosas - Leandro N. Alem", 
            "C": "Retiro - Constitución",
            "D": "Catedral - Congreso de Tucumán",
            "E": "Retiro - Plaza de los Virreyes",
            "H": "Hospitales - Facultad de Derecho"
        }
    
    def get_transport_advice(self, venue_address: str, current_time: datetime) -> Dict[str, Any]:
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        advice = {
            "primary_transport": "colectivo",
            "secondary_transport": "subte",
            "payment_method": "Tarjeta SUBE obligatoria",
            "apps_recommended": ["Cómo llego", "Moovit Buenos Aires", "BA Subte"],
        }
        
        # Consejos específicos por horario
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            advice["timing_warning"] = "⚠️ Hora pico - subte MUY lleno, colectivo más cómodo"
            advice["extra_time"] = "Agregá 20min extra por tráfico"
        
        if hour >= 23:
            advice["night_transport"] = "🌙 Colectivos nocturnos funcionan toda la noche"
            advice["safety_tip"] = "Uber/taxi más seguro después 1am"
        
        if is_weekend:
            advice["weekend_note"] = "Menos frecuencia de colectivos domingos"
        
        # Líneas específicas (esto se puede hacer más inteligente con geocoding)
        if "centro" in venue_address.lower():
            advice["suggested_lines"] = self.colectivo_lines["Centro"]
        elif "palermo" in venue_address.lower():
            advice["suggested_lines"] = self.colectivo_lines["Palermo"]
        
        return advice
    
    def get_timing_advice(self, event_type: EventType, start_time: datetime) -> Dict[str, Any]:
        advice = {"cultural_timing": {}}
        
        if event_type == EventType.DINING:
            advice["cultural_timing"] = {
                "arrival": "🇦🇷 En Argentina se cena tarde - 21:00 es normal",
                "duration": "Las cenas argentinas son MUY largas - planeá 2-3 horas", 
                "tip": "Si es parrilla, preguntá tiempos de cocción antes"
            }
        
        elif event_type == EventType.NIGHTLIFE:
            if start_time.hour < 23:
                advice["cultural_timing"]["early_warning"] = "🕘 ¿Seguro es 20:00? La noche porteña empieza 00:00"
            advice["cultural_timing"]["peak_time"] = "La movida fuerte es 1-4am"
            advice["cultural_timing"]["previa"] = "Hacé previa antes - es tradición argentina"
        
        elif event_type == EventType.CULTURAL:
            advice["cultural_timing"] = {
                "punctuality": "Llegá puntual - eventos culturales son estrictos",
                "dress_code": "Buenos Aires se viste elegante, no muy casual"
            }
        
        # Horario general argentino
        advice["hora_argentina"] = "⏰ 'Hora Argentina' = llegá 15-30min tarde a eventos sociales"
        
        return advice
    
    def get_social_context(self, event_type: EventType, group_size: int) -> Dict[str, str]:
        context = {}
        
        if event_type == EventType.DINING:
            context["sharing"] = "🍖 En Argentina se comparte - pedí para el grupo"
            context["payment"] = "💳 Se puede dividir la cuenta, normal"
            context["wine"] = "🍷 Vino argentino obligatorio - pedí Malbec"
        
        if group_size == 1:
            context["solo_travel"] = "👤 Porteños son amigables - normal ir solo"
        elif group_size > 4:
            context["large_group"] = "👥 Grupos grandes - reservá antes, avisar al venue"
        
        context["conversation"] = "🗣️ Argentinos hablan FUERTE - es normal, no es agresión"
        context["personal_space"] = "🤝 Más cercanía física que otros países - besos al saludar"
        
        return context
    
    def get_practical_tips(self, event_type: EventType) -> List[str]:
        tips = [
            "💰 Llevá efectivo - no todos toman tarjeta",
            "📱 Datos móviles funcionan bien en toda CABA", 
            "🧉 Si te ofrecen mate, aceptar es cortés",
            "⚽ Nunca menciones Boca vs River si no sabés del tema"
        ]
        
        if event_type == EventType.NIGHTLIFE:
            tips.extend([
                "🍺 Fernet con coca es LA bebida nacional",
                "💃 Si hay milonga, animate a bailar - te van a enseñar",
                "🚫 No tomes agua de la canilla en bares - pedí mineral"
            ])
        
        elif event_type == EventType.CULTURAL:
            tips.extend([
                "🎭 Teatro en Buenos Aires es clase mundial - vestite bien",
                "📚 Argentinos aman hablar de literatura y política"
            ])
        
        return tips
    
    def get_local_customs(self) -> Dict[str, str]:
        return {
            "greeting": "Beso en la mejilla - una sola vez, derecha",
            "dining": "Cena 21:00-23:00, almuerzo 12:00-15:00",
            "tipping": "10% en restaurantes, redondear en taxis",
            "shopping": "Siesta 13:00-17:00 - muchos comercios cerrados",
            "weekend": "Domingo familiar - menos movida nocturna",
            "language": "Porteño Spanish - 'vos' en lugar de 'tú'",
            "politics": "Tema sensible - evitá si no conocés la historia"
        }

# 🇪🇸 SPAIN IMPLEMENTATION  
class BarcelonaContext(CulturalContext):
    """Contexto cultural específico de Barcelona"""
    
    def __init__(self):
        super().__init__("Barcelona", "España")
    
    def get_transport_advice(self, venue_address: str, current_time: datetime) -> Dict[str, Any]:
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        advice = {
            "primary_transport": "metro",
            "secondary_transport": "bus",
            "payment_method": "T-10 (10 viajes) súper conveniente",
            "apps_recommended": ["TMB App", "Citymapper Barcelona"],
        }
        
        # Horarios específicos Barcelona
        if hour >= 24 or hour <= 5:
            if is_weekend:
                advice["night_transport"] = "🌙 Metro hasta 2:00am viernes/sábado"
            else:
                advice["night_transport"] = "🚌 Bus nocturno - Nitbus cada 30min"
        
        # Zonas de Barcelona
        if "eixample" in venue_address.lower():
            advice["zone_tip"] = "Eixample bien conectado - cualquier línea metro"
        elif "gràcia" in venue_address.lower():
            advice["zone_tip"] = "Gràcia = Línea 3 (verde) - ambiente bohemio"
        elif "barceloneta" in venue_address.lower():
            advice["zone_tip"] = "Barceloneta = L4 (amarilla) hasta playa"
        
        return advice
    
    def get_timing_advice(self, event_type: EventType, start_time: datetime) -> Dict[str, Any]:
        advice = {"cultural_timing": {}}
        
        if event_type == EventType.DINING:
            advice["cultural_timing"] = {
                "lunch": "🇪🇸 Almuerzo español 14:00-16:00 - restaurantes cerrados antes",
                "dinner": "Cena 21:30-23:30 - antes de eso solo turistas",
                "siesta": "14:00-17:00 muchos lugares cerrados - planeá accordingly"
            }
        
        elif event_type == EventType.NIGHTLIFE:
            advice["cultural_timing"] = {
                "spanish_night": "🌃 Noche española empieza 23:00-00:00",
                "peak_time": "1:00-3:00am es el peak en Barcelona", 
                "tapas_first": "Tapas + vermut antes de cenar - tradición"
            }
        
        return advice
    
    def get_social_context(self, event_type: EventType, group_size: int) -> Dict[str, str]:
        return {
            "language": "Catalán + Español - ambos OK, inglés en zonas turísticas",
            "volume": "🗣️ Españoles hablan alto - es cultural, no rudeza",
            "personal_space": "Dos besos al saludar - izquierda primero",
            "meal_sharing": "Tapas = compartir - nunca pidas solo para vos"
        }
    
    def get_practical_tips(self, event_type: EventType) -> List[str]:
        return [
            "💳 Tarjeta funciona en casi todos lados",
            "🏖️ Barcelona = playa + cultura - llevá ropa para ambos",
            "🚫 No camines por bike lanes - multa €200",
            "⚽ Barça es religión - respetá si no sos fan",
            "🍷 Cava es el champagne catalán - pedilo en celebraciones"
        ]
    
    def get_local_customs(self) -> Dict[str, str]:
        return {
            "greeting": "Dos besos - izquierda primero, derecha segundo",
            "dining": "Almuerzo 14:00, cena 21:30 - horarios sagrados",
            "siesta": "14:00-17:00 muchos negocios cerrados",
            "sunday": "Domingo = familia y descanso",
            "language": "Catalán es oficial - aprende 'hola' = 'hola', 'gracias' = 'gràcies'",
            "tipping": "5-10% en restaurantes, redondear resto"
        }

# 🇳🇱 NETHERLANDS IMPLEMENTATION
class AmsterdamContext(CulturalContext):
    """Contexto cultural de Amsterdam"""
    
    def __init__(self):
        super().__init__("Amsterdam", "Netherlands")
    
    def get_transport_advice(self, venue_address: str, current_time: datetime) -> Dict[str, Any]:
        return {
            "primary_transport": "bicycle",
            "secondary_transport": "tram",
            "payment_method": "OV-chipkaart - una para todo",
            "apps_recommended": ["9292", "Citymapper"],
            "bike_culture": "🚴 Bici es MÁS rápido que transporte público",
            "bike_parking": "Parking de bicis gratis en la mayoría de venues",
            "rain_backup": "🌧️ Si llueve mucho, holandeses también usan tram"
        }
    
    def get_timing_advice(self, event_type: EventType, start_time: datetime) -> Dict[str, Any]:
        return {
            "cultural_timing": {
                "punctuality": "⏰ SÚPER puntuales - llegá exacto a la hora",
                "early_dinner": "Cena 17:30-19:00 - mucho más temprano que España",
                "efficiency": "Eventos empiezan y terminan puntual"
            }
        }
    
    def get_social_context(self, event_type: EventType, group_size: int) -> Dict[str, str]:
        return {
            "directness": "🗣️ Holandeses son SÚPER directos - no es rudeza",
            "english": "Inglés perfecto - no te preocupes por idioma",
            "cycling": "🚴 Si no andás en bici, sos turista obvio",
            "liberalism": "Mente abierta a todo - sociedad muy liberal"
        }
    
    def get_practical_tips(self, event_type: EventType) -> List[str]:
        return [
            "💳 Cashless society - tarjeta/contactless everywhere",
            "🚴 Bike lanes son SOLO bicis - pedestrian = muerte",
            "☔ Siempre llevá campera - puede llover cualquier momento",
            "🌷 Holandeses valoran eficiencia y puntualidad sobre todo"
        ]
    
    def get_local_customs(self) -> Dict[str, str]:
        return {
            "greeting": "Handshake formal, abrazo si hay confianza",
            "cycling": "Bici tiene prioridad TOTAL - cuidado peatones",
            "weather": "Weather small talk es OBLIGATORIO",
            "directness": "Feedback directo es normal - no offense",
            "drugs": "Weed legal pero respetá las reglas"
        }

# 🏭 FACTORY PATTERN
class CulturalContextFactory:
    """Factory para crear contextos culturales específicos"""
    
    _contexts = {
        "Buenos Aires": BuenosAiresContext,
        "Barcelona": BarcelonaContext,
        "Amsterdam": AmsterdamContext,
        # Fácil expandir
        # "Paris": ParisContext,
        # "Mexico City": MexicoCityContext,
    }
    
    @classmethod
    def create_context(cls, city: str) -> Optional[CulturalContext]:
        """Crea contexto cultural para una ciudad"""
        context_class = cls._contexts.get(city)
        if context_class:
            return context_class()
        else:
            logger.warning(f"No cultural context available for {city}")
            return None
    
    @classmethod
    def get_supported_cities(cls) -> List[str]:
        """Lista de ciudades soportadas"""
        return list(cls._contexts.keys())

# 🧠 MAIN ENGINE
class CulturalContextEngine:
    """Motor principal que combina todos los contextos culturales"""
    
    def __init__(self):
        self.factory = CulturalContextFactory()
    
    def get_smart_recommendations(self, city: str, event_type: EventType, 
                                venue_address: str, start_time: datetime,
                                group_size: int = 2) -> Dict[str, Any]:
        """
        Genera recomendaciones culturalmente inteligentes
        """
        context = self.factory.create_context(city)
        
        if not context:
            return {"error": f"City {city} not supported yet"}
        
        recommendations = {
            "city": city,
            "cultural_context": {
                "transport": context.get_transport_advice(venue_address, start_time),
                "timing": context.get_timing_advice(event_type, start_time),
                "social": context.get_social_context(event_type, group_size),
                "practical_tips": context.get_practical_tips(event_type),
                "local_customs": context.get_local_customs()
            },
            "personalized_message": self._generate_personalized_message(context, event_type, start_time)
        }
        
        return recommendations
    
    def _generate_personalized_message(self, context: CulturalContext, 
                                     event_type: EventType, start_time: datetime) -> str:
        """Genera mensaje personalizado basado en contexto cultural"""
        
        if context.city_name == "Buenos Aires":
            if event_type == EventType.NIGHTLIFE:
                return f"🇦🇷 ¡Perfecto! En Buenos Aires la noche empieza tarde. Tu evento a las {start_time.strftime('%H:%M')} está genial - hacé una previa antes y llevá SUBE para el colectivo de vuelta."
            elif event_type == EventType.DINING:
                return f"🥩 Excelente elección porteña. Cenás a las {start_time.strftime('%H:%M')} - hora perfecta argentina. Probá el Malbec y no te olvides que las porciones son ENORMES."
        
        elif context.city_name == "Barcelona":
            if event_type == EventType.NIGHTLIFE:
                return f"🇪🇸 ¡Genial! En Barcelona la movida nocturna es increíble. A las {start_time.strftime('%H:%M')} podés empezar con tapas, la noche fuerte empieza después de medianoche."
            elif event_type == EventType.CULTURAL:
                return f"🎨 Barcelona es culturalmente riquísima. Tu evento a las {start_time.strftime('%H:%M')} - llevá el metro, T-10 te conviene. ¡Y cuidado con las bike lanes!"
        
        return f"¡Disfrutá {context.city_name}! 🌍"


# 🧪 TESTING
def test_cultural_engine():
    """Test del motor cultural"""
    engine = CulturalContextEngine()
    
    # Test Buenos Aires
    recommendations = engine.get_smart_recommendations(
        city="Buenos Aires",
        event_type=EventType.NIGHTLIFE,
        venue_address="Palermo Hollywood",
        start_time=datetime.now().replace(hour=22, minute=0),
        group_size=3
    )
    
    print("🇦🇷 Buenos Aires Recommendations:")
    print(f"Transport: {recommendations['cultural_context']['transport']}")
    print(f"Message: {recommendations['personalized_message']}")
    print()
    
    # Test Barcelona
    recommendations = engine.get_smart_recommendations(
        city="Barcelona", 
        event_type=EventType.CULTURAL,
        venue_address="Gràcia",
        start_time=datetime.now().replace(hour=19, minute=30),
        group_size=2
    )
    
    print("🇪🇸 Barcelona Recommendations:")
    print(f"Transport: {recommendations['cultural_context']['transport']}")
    print(f"Message: {recommendations['personalized_message']}")

if __name__ == "__main__":
    test_cultural_engine()