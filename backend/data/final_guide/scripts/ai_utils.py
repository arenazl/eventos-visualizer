#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Utils - Módulo de inteligencia artificial para el pipeline de eventos

Soporta múltiples proveedores:
- Ollama (local, gratis) - DEFAULT
- Grok (X.ai)
- OpenAI

Funciones principales:
- extract_location_from_text(): Extrae ciudad/país de texto libre
- validate_location(): Valida si una ubicación existe en region_utils
- categorize_event_ai(): Categorización inteligente de eventos
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

# Cargar .env
from dotenv import load_dotenv
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent.parent
ENV_FILE = BACKEND_DIR / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


@dataclass
class AIConfig:
    """Configuración de AI providers"""
    # Provider activo: ollama, grok, openai
    provider: str = os.getenv('AI_PROVIDER', 'ollama')

    # Ollama (local)
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    ollama_model: str = os.getenv('OLLAMA_MODEL', 'llama3.2')

    # Grok (X.ai)
    grok_api_key: str = os.getenv('GROK_API_KEY', '')
    grok_model: str = os.getenv('GROK_MODEL', 'grok-beta')

    # OpenAI
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')


# Config global
AI_CONFIG = AIConfig()


def _call_ollama(prompt: str, system: str = None) -> Optional[str]:
    """Llama a Ollama local"""
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{AI_CONFIG.ollama_url}/api/chat",
            json={
                "model": AI_CONFIG.ollama_model,
                "messages": messages,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get('message', {}).get('content', '')
        else:
            print(f"    ⚠️ Ollama error: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"    ⚠️ Ollama no disponible en {AI_CONFIG.ollama_url}")
        return None
    except Exception as e:
        print(f"    ⚠️ Ollama error: {e}")
        return None


def _call_grok(prompt: str, system: str = None) -> Optional[str]:
    """Llama a Grok (X.ai)"""
    if not AI_CONFIG.grok_api_key:
        print("    ⚠️ GROK_API_KEY no configurada")
        return None

    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_CONFIG.grok_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": AI_CONFIG.grok_model,
                "messages": messages,
                "temperature": 0.3
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"    ⚠️ Grok error: {response.status_code}")
            return None

    except Exception as e:
        print(f"    ⚠️ Grok error: {e}")
        return None


def _call_openai(prompt: str, system: str = None) -> Optional[str]:
    """Llama a OpenAI"""
    if not AI_CONFIG.openai_api_key:
        print("    ⚠️ OPENAI_API_KEY no configurada")
        return None

    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_CONFIG.openai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": AI_CONFIG.openai_model,
                "messages": messages,
                "temperature": 0.3
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"    ⚠️ OpenAI error: {response.status_code}")
            return None

    except Exception as e:
        print(f"    ⚠️ OpenAI error: {e}")
        return None


def call_ai(prompt: str, system: str = None) -> Optional[str]:
    """
    Llama al provider de AI configurado.
    Fallback: Ollama → Grok → OpenAI
    """
    provider = AI_CONFIG.provider.lower()

    if provider == 'ollama':
        result = _call_ollama(prompt, system)
        if result:
            return result
        # Fallback a Grok
        result = _call_grok(prompt, system)
        if result:
            return result
        # Fallback a OpenAI
        return _call_openai(prompt, system)

    elif provider == 'grok':
        result = _call_grok(prompt, system)
        if result:
            return result
        return _call_ollama(prompt, system)

    elif provider == 'openai':
        result = _call_openai(prompt, system)
        if result:
            return result
        return _call_ollama(prompt, system)

    # Default: Ollama
    return _call_ollama(prompt, system)


def extract_location_from_text(text: str, filename_hint: str = None) -> Dict[str, Optional[str]]:
    """
    Usa IA para extraer ciudad y país de un texto.

    Args:
        text: Texto del evento o archivo RAW
        filename_hint: Pista del filename (ej: "miami_2025-11-23.txt")

    Returns:
        {
            'ciudad': 'Miami',
            'pais': 'USA',
            'provincia': 'Florida',
            'confidence': 0.95
        }
    """
    system = """Eres un experto en geografía. Tu tarea es extraer la ubicación (ciudad, país, provincia/estado) de un texto.

REGLAS CRÍTICAS:
1. SOLO responde en formato JSON válido
2. Si el texto menciona múltiples ciudades, identifica la ciudad PRINCIPAL donde ocurren los eventos
3. Si no puedes determinar la ubicación con certeza, usa confidence < 0.5
4. Los barrios de una ciudad NO son ciudades separadas (ej: Palermo es un barrio de Buenos Aires, no una ciudad)

Ejemplos:
- "eventos en Miami, FL" → {"ciudad": "Miami", "pais": "USA", "provincia": "Florida", "confidence": 0.95}
- "fiestas en Palermo, Buenos Aires" → {"ciudad": "Buenos Aires", "pais": "Argentina", "provincia": "Buenos Aires", "confidence": 0.9}
- "conciertos en Barcelona" → {"ciudad": "Barcelona", "pais": "España", "provincia": "Cataluña", "confidence": 0.9}
"""

    # Tomar solo los primeros 500 caracteres del texto para no saturar
    text_sample = text[:500] if len(text) > 500 else text

    prompt = f"""Extrae la ubicación principal de este texto de eventos.

Pista del archivo: {filename_hint or 'sin pista'}

Texto:
{text_sample}

Responde SOLO con JSON válido:
{{"ciudad": "...", "pais": "...", "provincia": "...", "confidence": 0.0-1.0}}"""

    response = call_ai(prompt, system)

    if not response:
        return {'ciudad': None, 'pais': None, 'provincia': None, 'confidence': 0.0}

    # Parsear JSON de la respuesta
    try:
        # Limpiar respuesta (a veces viene con texto extra)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    return {'ciudad': None, 'pais': None, 'provincia': None, 'confidence': 0.0}


def validate_event_location(evento: Dict, expected_city: str, expected_country: str) -> Tuple[bool, str]:
    """
    Usa IA para validar si un evento pertenece a la ciudad/país esperados.

    Detecta casos como:
    - Evento de "Paris" cuando se esperaba "Buenos Aires"
    - Evento con ciudad = "Noviembre" (error de parsing)

    Args:
        evento: Dict con datos del evento
        expected_city: Ciudad esperada (del filename)
        expected_country: País esperado

    Returns:
        (is_valid, reason)
    """
    nombre = evento.get('nombre', '')
    lugar = evento.get('lugar', '')
    direccion = evento.get('direccion', '')

    system = """Eres un validador de datos de eventos. Tu tarea es determinar si un evento pertenece a una ciudad específica.

RESPONDE SOLO con JSON: {"valid": true/false, "reason": "explicación corta"}

Casos de INVALIDEZ:
- El lugar menciona otra ciudad/país diferente al esperado
- El nombre del evento es claramente de otra ciudad
- La dirección indica otra ubicación geográfica
- La "ciudad" parece ser un error de parsing (ej: "Noviembre", "Felo", números)
"""

    prompt = f"""¿Este evento pertenece a {expected_city}, {expected_country}?

Evento:
- Nombre: {nombre}
- Lugar: {lugar}
- Dirección: {direccion}

Responde SOLO con JSON: {{"valid": true/false, "reason": "..."}}"""

    response = call_ai(prompt, system)

    if not response:
        # Si no hay IA, asumir válido pero con warning
        return (True, "IA no disponible - no validado")

    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            return (result.get('valid', True), result.get('reason', ''))
    except:
        pass

    return (True, "parse error - asumido válido")


def categorize_event_ai(nombre: str, descripcion: str = '') -> Tuple[str, str]:
    """
    Usa IA para categorizar un evento de forma inteligente.

    Returns:
        (category, subcategory)
    """
    system = """Categoriza eventos en estas categorías:
- Música: conciertos, festivales, DJ sets
- Fiestas: clubes, nightlife, after parties
- Cultural: teatro, arte, exposiciones, museos
- Deportes: partidos, torneos, maratones
- Tech: conferencias, meetups, hackathons
- Gastronomía: food trucks, catas, restaurantes
- Familiar: eventos para niños, parques
- Negocios: networking, ferias comerciales

Responde SOLO con JSON: {"category": "...", "subcategory": "..."}"""

    prompt = f"""Categoriza este evento:
Nombre: {nombre}
Descripción: {descripcion[:200] if descripcion else 'sin descripción'}

JSON: {{"category": "...", "subcategory": "..."}}"""

    response = call_ai(prompt, system)

    if not response:
        return ('General', 'Evento')

    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            return (result.get('category', 'General'), result.get('subcategory', 'Evento'))
    except:
        pass

    return ('General', 'Evento')


def is_ai_available() -> Tuple[bool, str]:
    """
    Verifica si hay algún provider de IA disponible.

    Returns:
        (available, provider_name)
    """
    # Probar Ollama
    try:
        response = requests.get(f"{AI_CONFIG.ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return (True, f"Ollama ({AI_CONFIG.ollama_model})")
    except:
        pass

    # Probar Grok
    if AI_CONFIG.grok_api_key:
        return (True, f"Grok ({AI_CONFIG.grok_model})")

    # Probar OpenAI
    if AI_CONFIG.openai_api_key:
        return (True, f"OpenAI ({AI_CONFIG.openai_model})")

    return (False, "Ninguno")


# ============================================================================
# TEST
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI UTILS - Test de conectividad")
    print("=" * 60)

    available, provider = is_ai_available()

    if available:
        print(f"\n✅ IA disponible: {provider}")

        # Test de extracción de ubicación
        print("\n🧪 Test: extract_location_from_text")
        test_text = "Aquí tienes eventos en Miami, Florida para las próximas semanas..."
        result = extract_location_from_text(test_text, "miami_2025-11-23.txt")
        print(f"   Input: '{test_text[:50]}...'")
        print(f"   Output: {result}")

        # Test de categorización
        print("\n🧪 Test: categorize_event_ai")
        result = categorize_event_ai("Ultra Music Festival", "Festival de música electrónica con DJs internacionales")
        print(f"   Input: 'Ultra Music Festival'")
        print(f"   Output: {result}")

    else:
        print(f"\n❌ IA NO disponible")
        print("\nPara habilitar IA:")
        print("  1. Ollama (recomendado): ollama serve")
        print("  2. Grok: Agregar GROK_API_KEY en .env")
        print("  3. OpenAI: Agregar OPENAI_API_KEY en .env")

    print("\n" + "=" * 60)
