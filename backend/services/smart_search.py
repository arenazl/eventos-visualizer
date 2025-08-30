"""
Servicio de búsqueda inteligente con procesamiento de lenguaje natural
Entiende queries como: "bares en Mendoza", "restaurantes en Palermo", "conciertos mañana"
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SmartSearchService:
    def __init__(self):
        # Mapeo de categorías y sinónimos
        self.category_mappings = {
            'bares': ['bar', 'bares', 'cervecería', 'pub', 'brewery', 'cerveceria'],
            'restaurantes': ['restaurante', 'restaurantes', 'comida', 'restaurant', 'resto', 'parrilla', 'pizzería'],
            'música': ['música', 'musica', 'concierto', 'recital', 'show', 'banda', 'rock', 'jazz', 'cumbia'],
            'deportes': ['deporte', 'deportes', 'fútbol', 'futbol', 'partido', 'básquet', 'tenis', 'rugby'],
            'teatro': ['teatro', 'obra', 'musical', 'comedia', 'drama'],
            'fiesta': ['fiesta', 'party', 'boliche', 'club', 'after', 'bailar'],
            'cultural': ['museo', 'exposición', 'arte', 'cultura', 'muestra', 'galería'],
            'tech': ['tech', 'tecnología', 'hackathon', 'meetup', 'conferencia', 'workshop']
        }
        
        # Ciudades y barrios de Argentina
        self.locations = {
            # Ciudades principales
            'buenos aires': ['buenos aires', 'bsas', 'caba', 'capital federal'],
            'mendoza': ['mendoza', 'godoy cruz', 'guaymallen', 'maipu'],
            'córdoba': ['córdoba', 'cordoba', 'villa carlos paz'],
            'rosario': ['rosario', 'funes'],
            'mar del plata': ['mar del plata', 'mardel', 'mdq'],
            'bariloche': ['bariloche', 'san carlos de bariloche'],
            'salta': ['salta'],
            'tucumán': ['tucumán', 'tucuman', 'san miguel de tucuman'],
            
            # Barrios de Buenos Aires
            'palermo': ['palermo', 'palermo soho', 'palermo hollywood'],
            'recoleta': ['recoleta'],
            'belgrano': ['belgrano'],
            'san telmo': ['san telmo'],
            'puerto madero': ['puerto madero'],
            'microcentro': ['microcentro', 'centro'],
            'villa crespo': ['villa crespo'],
            'colegiales': ['colegiales'],
            'nuñez': ['nuñez', 'nunez'],
            'caballito': ['caballito'],
            'almagro': ['almagro'],
            'boedo': ['boedo']
        }
        
        # Palabras temporales
        self.time_keywords = {
            'hoy': 0,
            'mañana': 1,
            'pasado mañana': 2,
            'esta semana': 7,
            'este fin de semana': 'weekend',
            'finde': 'weekend',
            'próxima semana': 14,
            'este mes': 30
        }
        
    def parse_query(self, query: str) -> Dict:
        """
        Parsea una búsqueda en lenguaje natural y extrae:
        - Categoría/tipo de evento
        - Ubicación
        - Fecha/tiempo
        - Keywords adicionales
        """
        query_lower = query.lower().strip()
        
        result = {
            'original_query': query,
            'category': None,
            'location': None,
            'location_type': None,  # 'city' o 'neighborhood'
            'time_filter': None,
            'keywords': [],
            'is_free': None
        }
        
        # Detectar categoría
        for category, keywords in self.category_mappings.items():
            for keyword in keywords:
                if keyword in query_lower:
                    result['category'] = category
                    break
            if result['category']:
                break
        
        # Detectar ubicación
        location_found = False
        for location, variations in self.locations.items():
            for variation in variations:
                if variation in query_lower:
                    result['location'] = location
                    # Determinar si es ciudad o barrio
                    if location in ['palermo', 'recoleta', 'belgrano', 'san telmo', 'puerto madero', 
                                   'microcentro', 'villa crespo', 'colegiales', 'nuñez', 
                                   'caballito', 'almagro', 'boedo']:
                        result['location_type'] = 'neighborhood'
                    else:
                        result['location_type'] = 'city'
                    location_found = True
                    break
            if location_found:
                break
        
        # Detectar tiempo
        for time_keyword, days in self.time_keywords.items():
            if time_keyword in query_lower:
                if days == 'weekend':
                    # Calcular próximo fin de semana
                    today = datetime.now()
                    days_until_saturday = (5 - today.weekday()) % 7
                    if days_until_saturday == 0:
                        days_until_saturday = 0  # Ya es sábado
                    result['time_filter'] = {
                        'type': 'weekend',
                        'days_ahead': days_until_saturday
                    }
                else:
                    result['time_filter'] = {
                        'type': 'days',
                        'days_ahead': days
                    }
                break
        
        # Detectar si busca eventos gratuitos
        if any(word in query_lower for word in ['gratis', 'gratuito', 'libre', 'free']):
            result['is_free'] = True
        
        # Extraer keywords adicionales
        # Remover stopwords comunes en español
        stopwords = ['en', 'el', 'la', 'de', 'del', 'para', 'con', 'por', 'y', 'o', 'un', 'una']
        words = query_lower.split()
        keywords = []
        for word in words:
            if (word not in stopwords and 
                len(word) > 2 and
                not any(word in variations for variations in self.locations.values()) and
                not any(word in keywords for keywords in self.category_mappings.values())):
                keywords.append(word)
        
        result['keywords'] = keywords
        
        return result
    
    def build_search_params(self, parsed_query: Dict) -> Dict:
        """
        Convierte el query parseado en parámetros para la API
        """
        params = {}
        
        # Categoría
        if parsed_query['category']:
            params['category'] = parsed_query['category']
        
        # Ubicación
        if parsed_query['location']:
            if parsed_query['location_type'] == 'neighborhood':
                # Si es un barrio, agregarlo a Buenos Aires
                params['location'] = f"{parsed_query['location']}, Buenos Aires, Argentina"
            else:
                params['location'] = f"{parsed_query['location']}, Argentina"
        
        # Tiempo
        if parsed_query['time_filter']:
            today = datetime.now()
            if parsed_query['time_filter']['type'] == 'days':
                days = parsed_query['time_filter']['days_ahead']
                params['date_from'] = today
                params['date_to'] = today + timedelta(days=days)
            elif parsed_query['time_filter']['type'] == 'weekend':
                days = parsed_query['time_filter']['days_ahead']
                params['date_from'] = today + timedelta(days=days)
                params['date_to'] = today + timedelta(days=days + 2)
        
        # Eventos gratuitos
        if parsed_query['is_free']:
            params['is_free'] = True
        
        # Keywords para búsqueda de texto
        if parsed_query['keywords']:
            params['search_text'] = ' '.join(parsed_query['keywords'])
        
        return params
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Genera sugerencias de búsqueda basadas en el query actual
        """
        suggestions = []
        parsed = self.parse_query(query)
        
        # Si no hay ubicación, sugerir agregar una
        if not parsed['location']:
            base_query = query.strip()
            suggestions.extend([
                f"{base_query} en Buenos Aires",
                f"{base_query} en Palermo",
                f"{base_query} en Mendoza"
            ])
        
        # Si no hay tiempo, sugerir agregar uno
        if not parsed['time_filter']:
            base_query = query.strip()
            suggestions.extend([
                f"{base_query} hoy",
                f"{base_query} este fin de semana",
                f"{base_query} mañana"
            ])
        
        # Sugerencias relacionadas por categoría
        if parsed['category'] == 'bares':
            suggestions.extend([
                "happy hour en Palermo",
                "cervecerías artesanales",
                "bares con música en vivo"
            ])
        elif parsed['category'] == 'restaurantes':
            suggestions.extend([
                "parrillas en Puerto Madero",
                "restaurantes románticos",
                "comida vegetariana"
            ])
        elif parsed['category'] == 'música':
            suggestions.extend([
                "conciertos de rock",
                "jazz en San Telmo",
                "música en vivo hoy"
            ])
        
        return suggestions[:5]  # Limitar a 5 sugerencias