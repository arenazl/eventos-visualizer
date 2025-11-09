"""
🧠 AI SERVICE - Servicio de Inteligencia Artificial
Servicio singleton para interacciones con Gemini AI
"""

import os
import logging
import aiohttp
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GeminiAIService:
    """
    🧠 SERVICIO DE IA GEMINI
    
    Patrón Singleton para gestión centralizada de:
    - Detección de ubicaciones y provincias
    - Generación de URLs inteligentes
    - Análisis de contexto de eventos
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiAIService, cls).__new__(cls)
            logger.info("🧠 Singleton created: GeminiAIService")
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            logger.info("🧠 Gemini AI Service initialized as Singleton")
            self.session = None
            self.api_key = os.getenv('GEMINI_API_KEY')
            GeminiAIService._initialized = True
            logger.info("🧠 AI Service Singleton instance created globally")
    
    async def _get_session(self):
        """Obtiene o crea sesión HTTP reutilizable"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(connector=connector)
            logger.info("🔗 Nueva session HTTP creada con connection pooling")
        return self.session
    
    async def detect_location_info(self, location: str) -> Dict[str, Any]:
        """
        🌍 DETECCIÓN INTELIGENTE DE UBICACIÓN CON GEMINI API
        
        Usa Gemini API para analizar ubicación y extraer información estructurada
        """
        
        try:
            if not self.api_key:
                logger.error("❌ GEMINI_API_KEY no está configurada en las variables de entorno")
                raise Exception("ERROR: La API key de Gemini no está configurada. Por favor, configure GEMINI_API_KEY en el archivo .env del backend")
            
            # Prompt optimizado para Gemini API
            prompt = f"""Analiza la ubicación "{location}" y devuelve SOLO un JSON válido:
{{"city": "nombre_ciudad", "province": "nombre_provincia", "country": "nombre_pais", "confidence": 0.95}}

Reglas:
- Usa nombres en idioma local 
- Si no reconoces la ubicación, confidence: 0.30
- SOLO el JSON, sin explicaciones"""
            
            # Llamada real a Gemini API
            response = await self._call_gemini_api(prompt)
            
            if response:
                import json
                try:
                    # Limpiar respuesta y parsear JSON
                    clean_response = response.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                    
                    location_data = json.loads(clean_response)
                    
                    # Validar estructura
                    required_keys = ['city', 'province', 'country', 'confidence']
                    if all(key in location_data for key in required_keys):
                        logger.info(f"✅ Gemini detectó ubicación: {location_data['city']}, {location_data['country']}")
                        return location_data
                    else:
                        logger.warning(f"⚠️ Respuesta Gemini incompleta: {location_data}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Error parseando JSON de Gemini: {e}")
                    logger.warning(f"⚠️ Respuesta raw: {response[:100]}")
            
            # Fallback si Gemini no funciona
            logger.warning("⚠️ Gemini API no disponible, usando fallback básico")
            return {
                'city': location,
                'province': '',
                'country': '',
                'confidence': 0.30
            }
                
        except Exception as e:
            logger.error(f"❌ Error en detección de ubicación con Gemini: {e}")
            return {
                'city': location,
                'province': '',
                'country': '',
                'confidence': 0.10
            }
    
    async def generate_search_url(self, platform: str, location: str, category: Optional[str] = None) -> Optional[str]:
        """
        🔗 GENERACIÓN INTELIGENTE DE URLs CON GEMINI
        
        Usa Gemini AI para analizar patrones reales de plataformas y generar URLs
        """
        
        try:
            if not self.api_key:
                logger.warning("⚠️ GEMINI_API_KEY no configurado, usando fallback")
                return await self._generate_url_fallback(platform, location, category)
            
            location_info = await self.detect_location_info(location)
            
            # CASOS ESPECIALES: Plataformas que requieren formato específico
            if platform.lower() == 'meetup':
                # Para Meetup, usar SIEMPRE el formato real que funciona
                logger.info(f"🔄 Meetup detectado: usando formato real hardcodeado")
                return await self._generate_url_fallback(platform, location, category)
            
            # URLs base conocidas de plataformas populares
            platform_urls = {
                'eventbrite': 'eventbrite.com',
                'meetup': 'meetup.com', 
                'ticketmaster': 'ticketmaster.com',
                'bandsintown': 'bandsintown.com',
                'dice': 'dice.fm',
                'universe': 'universe.com',
                'facebook': 'facebook.com/events',
                'events': 'eventbrite.com',  # Events.com usa Eventbrite
                'ticombo': 'ticombo.com'  # Nueva plataforma de descubrimiento
            }
            
            platform_url = platform_urls.get(platform.lower())
            if not platform_url:
                logger.warning(f"⚠️ Plataforma no conocida: {platform}")
                return None
            
            # Prompt para que Gemini enseñe patrones reales de cada plataforma
            prompt = f"""Eres un experto en plataformas de eventos. Necesito que me enseñes cómo funciona la búsqueda por ubicación en {platform}.

Plataforma: {platform}
Ubicación ejemplo: {location_info['city']}, {location_info['country']}

PREGUNTA: ¿Cómo estructura {platform} sus URLs para buscar eventos por ciudad/ubicación?

Devuelve SOLO un JSON:
{{
  "platform": "{platform}",
  "url_structure": "patrón_real_que_usa_la_plataforma",
  "example_url": "url_completa_para_esta_ubicación",
  "domain_variations": ["dominio.com", "dominio.fr", "dominio.es"],
  "parameters": {{"city": "formato", "country": "formato", "state": "formato"}},
  "confidence": 0.95,
  "notes": "información_adicional_importante"
}}

IMPORTANTE: 
- Basa tu respuesta en el conocimiento real de cómo funciona {platform}
- Si no sabes exactamente, indica confidence: 0.3
- Si la plataforma cambió recientemente, menciona las variaciones conocidas

Ejemplos esperados por plataforma:

EVENTBRITE:
{{
  "platform": "eventbrite",
  "url_structure": "eventbrite.[domain]/d/[country]--[city]--events/",
  "example_url": "https://www.eventbrite.es/d/spain--barcelona--events/",
  "confidence": 0.95,
  "notes": "Usa guiones dobles -- como separador entre país y ciudad"
}}

MEETUP (FORMATO ESPECÍFICO):
{{
  "platform": "meetup", 
  "url_structure": "meetup.com/[locale]/find/?location=[country-code]--[city]&source=EVENTS",
  "example_url": "https://www.meetup.com/es-ES/find/?location=es--Barcelona&source=EVENTS",
  "confidence": 0.95,
  "notes": "Usa código de país (es, fr, us) seguido de -- y ciudad"
}}"""
            
            # Llamar a Gemini para analizar el patrón
            response = await self._call_gemini_api(prompt)
            
            if response:
                import json
                try:
                    # Limpiar respuesta y parsear JSON
                    clean_response = response.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                    
                    pattern_data = json.loads(clean_response)
                    
                    # Validar estructura
                    required_keys = ['platform', 'example_url', 'confidence']
                    if all(key in pattern_data for key in required_keys):
                        if pattern_data['confidence'] >= 0.5:
                            # Usar directamente la URL de ejemplo que Gemini generó
                            example_url = pattern_data.get('example_url', '')
                            if example_url and example_url.startswith('http'):
                                logger.info(f"✅ Gemini enseñó patrón para {platform}: {example_url}")
                                return example_url
                            else:
                                # Construir URL usando el patrón enseñado
                                url = await self._build_url_from_teaching(pattern_data, location_info, platform_url)
                                logger.info(f"✅ Gemini enseñó patrón, URL construida para {platform}: {url}")
                                return url
                        else:
                            logger.warning(f"⚠️ Gemini tiene baja confianza ({pattern_data['confidence']}) para {platform}")
                    else:
                        logger.warning(f"⚠️ Respuesta Gemini incompleta para {platform}: {pattern_data}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Error parseando JSON de Gemini para {platform}: {e}")
            
            # Fallback si Gemini no funciona
            logger.info(f"🔄 Usando fallback para {platform}")
            return await self._generate_url_fallback(platform, location, category)
                
        except Exception as e:
            logger.error(f"❌ Error generando URL para {platform}: {e}")
            return None
    
    async def _build_url_from_pattern(self, pattern_data: Dict, location_info: Dict, platform_url: str) -> str:
        """
        🔧 CONSTRUIR URL USANDO PATRÓN DE GEMINI
        
        Reemplaza variables en el patrón con datos reales de ubicación
        """
        
        try:
            url_pattern = pattern_data.get('url_pattern', '')
            
            # Variables de reemplazo
            variables = {
                '{city}': (location_info.get('city') or '').lower().replace(' ', pattern_data.get('separator', '-')),
                '{province}': (location_info.get('province') or '').lower().replace(' ', pattern_data.get('separator', '-')),
                '{country}': (location_info.get('country') or '').lower().replace(' ', pattern_data.get('separator', '-')),
                '{state}': (location_info.get('province') or '').lower().replace(' ', pattern_data.get('separator', '-'))
            }
            
            # Reemplazar variables en el patrón
            final_url = url_pattern
            for var, value in variables.items():
                if value:  # Solo reemplazar si hay valor
                    final_url = final_url.replace(var, value)
            
            # Si no tiene protocolo, agregarlo
            if not final_url.startswith(('http://', 'https://')):
                if final_url.startswith(platform_url):
                    final_url = f"https://{final_url}"
                else:
                    final_url = f"https://{platform_url}/{final_url.lstrip('/')}"
            
            logger.info(f"🔧 Patrón construido: {pattern_data.get('url_pattern')} → {final_url}")
            return final_url
            
        except Exception as e:
            logger.error(f"❌ Error construyendo URL desde patrón: {e}")
            return f"https://{platform_url}"
    
    async def _build_url_from_teaching(self, teaching_data: Dict, location_info: Dict, platform_url: str) -> str:
        """
        🎓 CONSTRUIR URL USANDO ENSEÑANZA DE GEMINI
        
        Usa la estructura enseñada por Gemini para construir URLs
        """
        
        try:
            url_structure = teaching_data.get('url_structure', '')
            parameters = teaching_data.get('parameters', {})
            domain_variations = teaching_data.get('domain_variations', [platform_url])
            
            # Seleccionar dominio apropiado por país
            country = location_info.get('country', '').lower()
            domain = platform_url  # fallback
            
            for domain_var in domain_variations:
                if country == 'france' and '.fr' in domain_var:
                    domain = domain_var
                elif country == 'españa' and '.es' in domain_var:
                    domain = domain_var
                elif country == 'argentina' and '.com.ar' in domain_var:
                    domain = domain_var
                elif '.com' in domain_var and domain == platform_url:
                    domain = domain_var  # fallback a .com
            
            # Construir URL siguiendo la estructura enseñada
            city = location_info.get('city', '').lower().replace(' ', '-')
            country_name = location_info.get('country', '').lower().replace(' ', '-')
            state = location_info.get('province', '').lower().replace(' ', '-')
            
            # Reemplazar patrones en la estructura
            final_structure = url_structure.replace('[domain]', domain)
            final_structure = final_structure.replace('[city]', city)
            final_structure = final_structure.replace('[country]', country_name)
            final_structure = final_structure.replace('[state]', state)
            
            # Si no empieza con http, agregarlo
            if not final_structure.startswith('http'):
                final_structure = f"https://{final_structure}"
            
            logger.info(f"🎓 Estructura enseñada: {url_structure} → {final_structure}")
            return final_structure
            
        except Exception as e:
            logger.error(f"❌ Error construyendo URL desde enseñanza: {e}")
            return f"https://{platform_url}"
    
    async def _generate_url_fallback(self, platform: str, location: str, category: Optional[str]) -> Optional[str]:
        """
        🔄 FALLBACK PARA GENERACIÓN DE URLs
        
        Sistema de respaldo cuando Gemini no funciona
        """
        
        location_info = await self.detect_location_info(location)
        
        # URLs base por plataforma (fallback seguro con patrones REALES)
        url_patterns = {
            'eventbrite': self._generate_eventbrite_url,
            'meetup': self._generate_meetup_url_real,  # Nuevo método con formato real
            'ticketmaster': self._generate_ticketmaster_url,
            'bandsintown': self._generate_bandsintown_url,
            'dice': self._generate_dice_url,
            'universe': self._generate_universe_url,
            'facebook': self._generate_facebook_url,
            'events': self._generate_events_url,
            'ticombo': self._generate_ticombo_url
        }
        
        generator = url_patterns.get(platform.lower())
        if generator:
            return generator(location_info, category)
        else:
            logger.warning(f"⚠️ No hay fallback para plataforma: {platform}")
            return None
    
    def _generate_eventbrite_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Eventbrite"""
        city = (location_info.get('city') or '').lower().replace(' ', '-')
        country = (location_info.get('country') or '').lower().replace(' ', '-')
        
        if country:
            return f"https://www.eventbrite.com/d/{country}--{city}--events/"
        else:
            return f"https://www.eventbrite.com/d/{city}--events/"
    
    def _generate_meetup_url_real(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Meetup CON FORMATO REAL QUE FUNCIONA"""
        country_code = self._get_country_code(location_info.get('country'))
        city = location_info.get('city', '').replace(' ', '')
        
        # Locale específico por país
        locale = 'es-ES' if country_code == 'ES' else 'en-US'
        
        # Formato REAL que funciona: /es-ES/find/?location=es--Barcelona&source=EVENTS
        return f"https://www.meetup.com/{locale}/find/?location={country_code.lower()}--{city}&source=EVENTS"
    
    def _generate_meetup_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Meetup (método original de respaldo)"""
        country_code = self._get_country_code(location_info.get('country'))
        province = location_info.get('province', '').replace(' ', '%20')
        city = location_info['city'].replace(' ', '%20')
        
        return f"https://www.meetup.com/find/?location={country_code}--{province}--{city}&source=EVENTS"
    
    def _generate_ticketmaster_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Ticketmaster"""
        city = location_info['city'].lower().replace(' ', '-')
        country = location_info.get('country', '').lower()
        
        if country == 'españa':
            return f"https://www.ticketmaster.es/city/{city}"
        elif country == 'argentina':
            return f"https://www.ticketmaster.com.ar/city/{city}"
        else:
            return f"https://www.ticketmaster.com/city/{city}"
    
    def _generate_bandsintown_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Bandsintown"""
        city = location_info['city'].lower().replace(' ', '-')
        return f"https://www.bandsintown.com/{city}/concerts"
    
    def _generate_dice_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Dice"""
        city = location_info['city'].lower().replace(' ', '-')
        return f"https://www.dice.fm/{city}/music"
    
    def _generate_universe_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Universe"""
        city = location_info['city'].lower().replace(' ', '-')
        return f"https://www.universe.com/{city}-events"
    
    def _generate_facebook_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Facebook"""
        return "https://www.facebook.com/events/search/?q=events"
    
    def _generate_events_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Events.com (via Eventbrite)"""
        return self._generate_eventbrite_url(location_info, category)
    
    def _generate_ticombo_url(self, location_info: Dict, category: Optional[str]) -> str:
        """Genera URL específica para Ticombo"""
        city = location_info['city'].lower().replace(' ', '+')
        return f"https://www.ticombo.com/en/discover/search?q={city}"
    
    def _get_country_code(self, country: Optional[str]) -> str:
        """Convierte país a código ISO"""
        if not country:
            return "US"
            
        country_lower = country.lower()
        codes = {
            'españa': 'ES',
            'spain': 'ES', 
            'argentina': 'AR',
            'france': 'FR',
            'francia': 'FR',
            'united states': 'US',
            'usa': 'US'
        }
        return codes.get(country_lower, 'US')
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """
        🤖 LLAMADA REAL A GEMINI API
        
        Args:
            prompt: Prompt para Gemini
            
        Returns:
            Respuesta de Gemini o None si falla
        """
        
        try:
            if not self.api_key:
                logger.warning("⚠️ GEMINI_API_KEY no disponible")
                return None
            
            session = await self._get_session()
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192
                }
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"🔍 Gemini full response: {data}")

                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]

                        # Verificar estructura del candidate
                        if 'content' not in candidate:
                            logger.error(f"❌ Gemini response missing 'content'. Response: {data}")
                            return None

                        content = candidate['content']

                        if 'parts' not in content:
                            logger.error(f"❌ Gemini response missing 'parts' in content. Content: {content}")
                            return None

                        if len(content['parts']) == 0:
                            logger.error(f"❌ Gemini response has empty 'parts' array")
                            return None

                        text = content['parts'][0]['text']
                        logger.info(f"✅ Gemini API responded successfully")
                        return text.strip()
                    else:
                        logger.warning(f"⚠️ Gemini API response sin contenido. Response: {data}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Gemini API error: HTTP {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error llamando Gemini API: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


# 🌍 Cache for nearby cities to avoid repeated AI calls
_nearby_cities_cache = {}

# 🌍 Helper function for nearby cities
async def get_nearby_cities_with_ai(location: str, limit: int = 10) -> list:
    """
    Get nearby cities using Gemini AI (with caching)

    Args:
        location: City name to find nearby cities for
        limit: Maximum number of cities to return

    Returns:
        List of dictionaries with city information
    """
    try:
        # Check cache first
        cache_key = f"{location.lower()}:{limit}"
        if cache_key in _nearby_cities_cache:
            logger.info(f"✅ Returning cached nearby cities for {location}")
            return _nearby_cities_cache[cache_key]

        prompt = f"""
Eres un experto en geografía. Dame una lista de {limit} ciudades cercanas a "{location}", Argentina.

Para cada ciudad, proporciona:
1. Nombre de la ciudad
2. Provincia
3. Distancia aproximada en km desde {location}
4. Si tiene eventos culturales/deportivos importantes

Responde SOLO en formato JSON válido, sin markdown ni explicaciones adicionales:
{{
  "cities": [
    {{
      "name": "Nombre Ciudad",
      "displayName": "Ciudad (50 km)",
      "province": "Provincia",
      "country": "Argentina",
      "countryCode": "AR",
      "distance": "50 km",
      "hasEvents": true,
      "lat": -34.0,
      "lon": -64.0
    }}
  ]
}}
"""

        # Create AI service instance
        ai_service = GeminiAIService()

        # Call Gemini API
        response_text = await ai_service._call_gemini_api(prompt)

        if not response_text:
            logger.warning(f"⚠️ No response from Gemini for nearby cities")
            return []

        # Parse JSON response
        import json
        import re

        # Clean response (remove markdown if present)
        json_text = re.sub(r'```json\n?|\n?```', '', response_text.strip())

        try:
            data = json.loads(json_text)
            cities = data.get("cities", [])[:limit]

            # Store in cache for future requests
            cache_key = f"{location.lower()}:{limit}"
            _nearby_cities_cache[cache_key] = cities

            logger.info(f"✅ Got {len(cities)} nearby cities for {location} (cached for future use)")
            return cities

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON from Gemini: {e}")
            logger.error(f"Response was: {response_text[:200]}")
            return []

    except Exception as e:
        logger.error(f"❌ Error getting nearby cities: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []