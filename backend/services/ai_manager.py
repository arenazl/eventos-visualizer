"""
🎯 AI SERVICE MANAGER - Gestor Inteligente de Providers
Sistema con fallback automático y cambio dinámico de providers
"""

import os
import logging
from typing import Optional, Dict, Any, List
from .ai_providers import (
    AIProvider,
    ProviderType,
    GrokProvider,
    GroqProvider,
    GeminiProvider,
    PerplexityProvider,
    OpenRouterProvider
)

logger = logging.getLogger(__name__)


class AIServiceManager:
    """
    🎯 GESTOR INTELIGENTE DE PROVIDERS DE IA

    Características:
    - Fallback automático entre providers
    - Cambio dinámico de provider preferido
    - Singleton pattern para eficiencia
    - Cache de providers configurados
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIServiceManager, cls).__new__(cls)
            logger.info("🎯 Singleton AIServiceManager created")
        return cls._instance

    def __init__(self):
        if not self._initialized:
            logger.info("🎯 Inicializando AI Service Manager")

            # Providers disponibles
            self.providers: Dict[ProviderType, AIProvider] = {
                ProviderType.GROK: GrokProvider(),
                ProviderType.GROQ: GroqProvider(),
                ProviderType.GEMINI: GeminiProvider(),
                ProviderType.PERPLEXITY: PerplexityProvider(),
                ProviderType.OPENROUTER: OpenRouterProvider()
            }

            # Provider preferido (configurable vía env o endpoint)
            preferred = os.getenv('PREFERRED_AI_PROVIDER', 'grok').lower()
            try:
                self.preferred_provider = ProviderType(preferred)
            except ValueError:
                logger.warning(f"⚠️ Provider '{preferred}' no válido, usando Grok")
                self.preferred_provider = ProviderType.GROK

            # Orden de fallback: Gemini (gratis) -> Grok (backup)
            self.fallback_order = [
                ProviderType.GEMINI,      # 🥇 Primary - Gratis, 60 req/min
                ProviderType.GROK,        # 🥈 Fallback - Potente backup
                ProviderType.GROQ,        # Extra fallback si se configura
                ProviderType.OPENROUTER,
                ProviderType.PERPLEXITY
            ]

            AIServiceManager._initialized = True
            self._log_configured_providers()

    def _log_configured_providers(self):
        """Log de providers configurados"""
        configured = []
        for ptype, provider in self.providers.items():
            if provider.is_configured():
                configured.append(f"✅ {ptype.value}")
            else:
                configured.append(f"❌ {ptype.value}")

        logger.info(f"🎯 Providers: {' | '.join(configured)}")
        logger.info(f"🎯 Provider preferido: {self.preferred_provider.value}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        use_fallback: bool = True
    ) -> Optional[str]:
        """
        Genera respuesta usando el provider preferido con fallback automático

        Args:
            prompt: Texto del prompt
            temperature: Nivel de creatividad (0.0-1.0)
            use_fallback: Si debe intentar otros providers si el preferido falla

        Returns:
            Respuesta del modelo o None si todos fallan
        """
        # Intentar con provider preferido primero
        preferred = self.providers[self.preferred_provider]

        if preferred.is_configured():
            logger.info(f"🎯 Usando provider preferido: {self.preferred_provider.value}")
            response = await preferred.generate(prompt, temperature)

            if response:
                return response
            else:
                logger.warning(f"⚠️ Provider preferido {self.preferred_provider.value} falló")

        # Si falló y fallback está habilitado, intentar otros
        if use_fallback:
            logger.info("🔄 Iniciando fallback automático...")

            for provider_type in self.fallback_order:
                # Saltar el que ya intentamos
                if provider_type == self.preferred_provider:
                    continue

                provider = self.providers[provider_type]

                if not provider.is_configured():
                    logger.debug(f"⏭️ Saltando {provider_type.value} (no configurado)")
                    continue

                logger.info(f"🔄 Intentando fallback con: {provider_type.value}")
                response = await provider.generate(prompt, temperature)

                if response:
                    logger.info(f"✅ Fallback exitoso con {provider_type.value}")
                    return response
                else:
                    logger.warning(f"⚠️ Fallback con {provider_type.value} falló")

        logger.error("❌ Todos los providers fallaron")
        return None

    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.3,
        use_fallback: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Genera respuesta en formato JSON

        Args:
            prompt: Texto del prompt (debe pedir JSON en respuesta)
            temperature: Nivel de creatividad
            use_fallback: Si debe usar fallback

        Returns:
            Diccionario parseado o None si falla
        """
        response = await self.generate(prompt, temperature, use_fallback)

        if not response:
            return None

        # Limpiar y parsear JSON
        import json
        import re

        try:
            # Remover markdown si existe
            clean_response = re.sub(r'```json\n?|\n?```', '', response.strip())

            # Parsear JSON
            data = json.loads(clean_response)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            logger.error(f"Respuesta raw: {response[:200]}")
            return None

    def set_preferred_provider(self, provider_type: str) -> bool:
        """
        Cambia el provider preferido

        Args:
            provider_type: Tipo de provider ('groq', 'gemini', etc.)

        Returns:
            True si se cambió exitosamente
        """
        try:
            new_provider = ProviderType(provider_type.lower())

            if not self.providers[new_provider].is_configured():
                logger.warning(f"⚠️ Provider {provider_type} no está configurado")
                return False

            self.preferred_provider = new_provider
            logger.info(f"✅ Provider preferido cambiado a: {provider_type}")
            return True

        except ValueError:
            logger.error(f"❌ Provider inválido: {provider_type}")
            return False

    def get_provider_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de todos los providers

        Returns:
            Diccionario con info de cada provider
        """
        status = {
            "preferred": self.preferred_provider.value,
            "providers": {}
        }

        for ptype, provider in self.providers.items():
            status["providers"][ptype.value] = {
                "configured": provider.is_configured(),
                "name": provider.name
            }

        return status

    async def close_all(self):
        """Cierra todas las sesiones HTTP de los providers"""
        for provider in self.providers.values():
            await provider.close()
        logger.info("🔌 Todas las sesiones de providers cerradas")


# 🌍 FUNCIONES DE UTILIDAD PARA COMPATIBILIDAD CON CÓDIGO EXISTENTE

async def detect_location_info(location: str) -> Dict[str, Any]:
    """
    🌍 Detecta información de ubicación usando IA

    Args:
        location: Nombre de la ubicación

    Returns:
        Dict con city, province, country, confidence
    """
    manager = AIServiceManager()

    prompt = f"""Analiza la ubicación "{location}" y devuelve SOLO un JSON válido:
{{"city": "nombre_ciudad", "province": "nombre_provincia", "country": "nombre_pais", "confidence": 0.95}}

Reglas:
- Usa nombres en idioma local
- Si no reconoces la ubicación, confidence: 0.30
- SOLO el JSON, sin explicaciones"""

    try:
        data = await manager.generate_json(prompt, temperature=0.1)

        if data and all(key in data for key in ['city', 'province', 'country', 'confidence']):
            logger.info(f"✅ Ubicación detectada: {data['city']}, {data['country']}")
            return data
        else:
            logger.warning("⚠️ Respuesta de IA incompleta, usando fallback")

    except Exception as e:
        logger.error(f"❌ Error detectando ubicación: {e}")

    # Fallback
    return {
        'city': location,
        'province': '',
        'country': '',
        'confidence': 0.30
    }


async def get_nearby_cities_with_ai(location: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    🌍 Obtiene ciudades cercanas usando IA

    Args:
        location: Ciudad base
        limit: Número máximo de ciudades

    Returns:
        Lista de ciudades con información
    """
    manager = AIServiceManager()

    prompt = f"""
Eres un experto en geografía. Dame una lista de {limit} ciudades cercanas a "{location}".

Para cada ciudad, proporciona:
1. Nombre de la ciudad
2. Provincia/Estado
3. Distancia aproximada en km desde {location}
4. Si tiene eventos culturales/deportivos importantes

Responde SOLO en formato JSON válido, sin markdown ni explicaciones adicionales:
{{
  "cities": [
    {{
      "name": "Nombre Ciudad",
      "displayName": "Ciudad (50 km)",
      "province": "Provincia",
      "country": "País",
      "countryCode": "XX",
      "distance": "50 km",
      "hasEvents": true,
      "lat": -34.0,
      "lon": -64.0
    }}
  ]
}}
"""

    try:
        data = await manager.generate_json(prompt, temperature=0.3)

        if data and "cities" in data:
            cities = data["cities"][:limit]
            logger.info(f"✅ {len(cities)} ciudades cercanas encontradas")
            return cities

    except Exception as e:
        logger.error(f"❌ Error obteniendo ciudades cercanas: {e}")

    return []


async def generate_event_context(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    🎨 Genera contexto adicional para un evento usando IA

    Args:
        event_data: Datos del evento (title, category, venue_name, city, start_datetime)

    Returns:
        Dict con curiosidades, que_llevar, ambiente_esperado, tip_local
    """
    manager = AIServiceManager()

    prompt = f"""
Genera información adicional interesante sobre este evento:
- Título: {event_data.get('title')}
- Categoría: {event_data.get('category')}
- Ubicación: {event_data.get('venue_name')}, {event_data.get('city')}
- Fecha: {event_data.get('start_datetime')}

Responde en JSON con:
{{
  "curiosidades": ["dato 1", "dato 2", "dato 3"],
  "que_llevar": ["item 1", "item 2", "item 3"],
  "ambiente_esperado": "descripción breve del ambiente",
  "tip_local": "consejo útil sobre la zona o evento"
}}

IMPORTANTE: Responde SOLO el JSON, sin markdown ni explicaciones.
"""

    try:
        data = await manager.generate_json(prompt, temperature=0.7)
        return data

    except Exception as e:
        logger.error(f"❌ Error generando contexto del evento: {e}")
        return None
