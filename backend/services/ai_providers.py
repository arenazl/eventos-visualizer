"""
🤖 AI PROVIDERS - Sistema Multi-Provider con Fallback Automático
Soporta múltiples servicios de IA: Groq, Gemini, Perplexity, OpenRouter
"""

import os
import logging
import aiohttp
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Tipos de providers disponibles"""
    GROK = "grok"          # xAI Grok (Elon Musk)
    GROQ = "groq"          # Groq (inferencia rápida)
    GEMINI = "gemini"      # Google Gemini
    PERPLEXITY = "perplexity"  # Perplexity AI
    OPENROUTER = "openrouter"  # OpenRouter


class AIProvider(ABC):
    """
    🧠 CLASE BASE ABSTRACTA PARA PROVIDERS DE IA

    Todos los providers deben implementar estos métodos
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.name = self.__class__.__name__

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea sesión HTTP reutilizable con timeout de 15s"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            # ⏱️ TIMEOUT CRÍTICO: 15 segundos máximo para evitar freezes
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            logger.debug(f"🔗 Nueva sesión HTTP para {self.name} (timeout: 15s)")
        return self.session

    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug(f"🔌 Sesión cerrada para {self.name}")

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """
        Genera respuesta usando el provider de IA

        Args:
            prompt: Texto del prompt
            temperature: Nivel de creatividad (0.0-1.0)

        Returns:
            Respuesta del modelo o None si falla
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Verifica si el provider está configurado con API key"""
        pass

    def __str__(self):
        return self.name


class GrokProvider(AIProvider):
    """
    🚀 GROK PROVIDER - xAI de Elon Musk

    Características:
    - Modelo Grok-4-latest (muy potente)
    - API compatible con OpenAI
    - Buen razonamiento y contexto
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('GROK_API_KEY'))
        self.base_url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-3"  # Modelo actual (grok-beta fue deprecado 2025-09-15)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Genera respuesta usando Grok (xAI)"""
        try:
            if not self.api_key:
                logger.warning("⚠️ GROK_API_KEY no configurada")
                return None

            session = await self._get_session()

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        text = data['choices'][0]['message']['content']
                        logger.info(f"✅ Grok respondió exitosamente")
                        return text.strip()
                    else:
                        logger.warning(f"⚠️ Grok response sin contenido: {data}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Grok API error: HTTP {response.status} - {error_text}")
                    return None

        except Exception as e:
            import traceback
            logger.error(f"❌ Error en Grok provider: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None


class GroqProvider(AIProvider):
    """
    ⚡ GROQ PROVIDER - Ultra Rápido

    Características:
    - 14,400 requests/día gratis
    - 500+ tokens/segundo
    - Modelos: Llama 3, Mixtral, Gemma
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('GROQ_API_KEY'))
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"  # Modelo actualizado

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Genera respuesta usando Groq"""
        try:
            if not self.api_key:
                logger.warning("⚠️ GROQ_API_KEY no configurada")
                return None

            session = await self._get_session()

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 8192
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        text = data['choices'][0]['message']['content']
                        logger.info(f"✅ Groq respondió exitosamente")
                        return text.strip()
                    else:
                        logger.warning(f"⚠️ Groq response sin contenido: {data}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Groq API error: HTTP {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error en Groq provider: {e}")
            return None


class GeminiProvider(AIProvider):
    """
    🔷 GEMINI PROVIDER - Google AI

    Características:
    - 250 requests/día gratis
    - Buen análisis de contexto
    - Integración con Google
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('GEMINI_API_KEY'))
        self.model = "gemini-2.5-flash"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Genera respuesta usando Gemini"""
        try:
            if not self.api_key:
                logger.warning("⚠️ GEMINI_API_KEY no configurada")
                return None

            session = await self._get_session()

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 8192
                }
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            if len(candidate['content']['parts']) > 0:
                                text = candidate['content']['parts'][0]['text']
                                logger.info(f"✅ Gemini respondió exitosamente")
                                return text.strip()

                    logger.warning(f"⚠️ Gemini response sin contenido válido")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Gemini API error: HTTP {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error en Gemini provider: {e}")
            return None


class PerplexityProvider(AIProvider):
    """
    🔍 PERPLEXITY PROVIDER - Búsqueda en Tiempo Real

    Características:
    - Acceso a web en tiempo real
    - Información actualizada
    - 5 requests/hora gratis
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('PERPLEXITY_API_KEY'))
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "pplx-7b-online"  # Modelo con búsqueda web

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Genera respuesta usando Perplexity con búsqueda web"""
        try:
            if not self.api_key:
                logger.warning("⚠️ PERPLEXITY_API_KEY no configurada")
                return None

            session = await self._get_session()

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        text = data['choices'][0]['message']['content']
                        logger.info(f"✅ Perplexity respondió exitosamente")
                        return text.strip()
                    else:
                        logger.warning(f"⚠️ Perplexity response sin contenido")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Perplexity API error: HTTP {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error en Perplexity provider: {e}")
            return None


class OpenRouterProvider(AIProvider):
    """
    🔄 OPENROUTER PROVIDER - Múltiples Modelos

    Características:
    - Acceso a GPT-4, Claude, Gemini, Llama
    - Pricing transparente
    - Fallback automático entre modelos
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('OPENROUTER_API_KEY'))
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        # Modelos ordenados por precio (más barato primero)
        self.models = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3-70b",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o-mini"
        ]
        self.current_model = self.models[0]

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Genera respuesta usando OpenRouter con fallback"""
        try:
            if not self.api_key:
                logger.warning("⚠️ OPENROUTER_API_KEY no configurada")
                return None

            session = await self._get_session()

            # Intentar con cada modelo hasta que uno funcione
            for model in self.models:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature
                    }

                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://eventos-visualizer.com",
                        "X-Title": "Eventos Visualizer"
                    }

                    async with session.post(self.base_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'choices' in data and len(data['choices']) > 0:
                                text = data['choices'][0]['message']['content']
                                logger.info(f"✅ OpenRouter ({model}) respondió exitosamente")
                                self.current_model = model
                                return text.strip()
                        else:
                            logger.warning(f"⚠️ OpenRouter modelo {model} falló: HTTP {response.status}")
                            continue

                except Exception as model_error:
                    logger.warning(f"⚠️ Error con modelo {model}: {model_error}")
                    continue

            logger.error("❌ Todos los modelos de OpenRouter fallaron")
            return None

        except Exception as e:
            logger.error(f"❌ Error en OpenRouter provider: {e}")
            return None
