"""
Script para procesar barrios faltantes de Buenos Aires con Gemini AI
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configurar codificación para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Variables de entorno cargadas desde {env_path}")
else:
    print(f"⚠️  Archivo .env no encontrado en {env_path}")

from services.ai_service import GeminiAIService

# Barrios pendientes de procesar
BARRIOS_PENDIENTES = [
    {"nombre": "Villa Luro", "comuna": 10, "zona": "Oeste"},
    {"nombre": "Villa Ortúzar", "comuna": 15, "zona": "Norte"},
    {"nombre": "Villa Pueyrredón", "comuna": 12, "zona": "Norte"},
    {"nombre": "Villa Real", "comuna": 10, "zona": "Oeste"},
    {"nombre": "Villa Riachuelo", "comuna": 8, "zona": "Sur"},
    {"nombre": "Villa Santa Rita", "comuna": 11, "zona": "Oeste"},
    {"nombre": "Villa Soldati", "comuna": 8, "zona": "Sur"},
    {"nombre": "Villa Urquiza", "comuna": 12, "zona": "Norte"}
]

def normalize_barrio_name(nombre: str) -> str:
    """Normaliza nombre de barrio para nombre de archivo"""
    return nombre.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

def extract_json_from_response(response: str) -> dict:
    """Extrae y parsea JSON de la respuesta de Gemini"""
    try:
        # Limpiar código markdown si existe
        clean_response = response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
        elif clean_response.startswith('```'):
            clean_response = clean_response.replace('```', '').strip()

        # Intentar parsear JSON
        return json.loads(clean_response)
    except json.JSONDecodeError:
        # Si no es JSON válido, intentar extraer información manualmente
        return None

async def process_barrio(barrio: dict, ai_service: GeminiAIService) -> bool:
    """
    Procesa un barrio individual con Gemini AI

    Returns:
        True si se procesó exitosamente, False en caso contrario
    """
    nombre = barrio["nombre"]
    comuna = barrio["comuna"]

    print(f"\n{'='*60}")
    print(f"🏙️  Procesando: {nombre} (Comuna {comuna})")
    print(f"{'='*60}")

    # Crear prompt para Gemini
    prompt = f"""Eres un asistente que recopila información sobre eventos en Buenos Aires, Argentina.

Necesito que me des información sobre eventos, fiestas, actividades, recitales, shows y festivales que están ocurriendo o van a ocurrir en el barrio {nombre}, Buenos Aires, Argentina desde hoy ({datetime.now().strftime('%Y-%m-%d')}) hasta fin de mes (30 de noviembre de 2025).

IMPORTANTE:
- Busca eventos REALES que estén anunciados públicamente
- Incluye fecha, hora, lugar específico (dirección), descripción, categoría y precio
- Si no hay eventos confirmados, retorna arrays vacíos
- Dame la respuesta SOLO en formato JSON válido

Formato esperado:
{{
  "barrio": "{nombre}",
  "comuna": {comuna},
  "mes": "noviembre",
  "año": 2025,
  "fecha_consulta": "{datetime.now().strftime('%Y-%m-%d')}",
  "caracteristica": "breve descripción del barrio",
  "eventos_ferias_festivales": [
    {{
      "nombre": "nombre del evento",
      "fecha": "YYYY-MM-DD o descripción",
      "hora_inicio": "HH:MM",
      "hora_fin": "HH:MM o null",
      "lugar": "nombre del lugar (dirección)",
      "descripcion": "descripción del evento",
      "categoria": "categoría",
      "precio": "gratuito/pago/variable",
      "estado": "hoy/próximo/etc"
    }}
  ],
  "recitales_shows_fiestas": [
    {{
      "nombre": "nombre del evento",
      "fecha": "YYYY-MM-DD o descripción",
      "hora_inicio": "HH:MM o consultar",
      "hora_fin": "HH:MM o null",
      "lugar": "nombre del lugar (dirección)",
      "descripcion": "descripción",
      "categoria": "rock/electrónica/teatro/etc",
      "precio": "pago/gratuito"
    }}
  ],
  "notas": [
    "observaciones sobre el barrio y sus eventos"
  ],
  "total_eventos_festivales": 0,
  "total_recitales": 0,
  "fuente": "Gemini AI"
}}

Devuelve SOLO el JSON, sin explicaciones adicionales."""

    try:
        # Llamar a Gemini API
        response = await ai_service._call_gemini_api(prompt)

        if not response:
            print(f"❌ No se obtuvo respuesta de Gemini para {nombre}")
            return False

        print(f"✅ Respuesta recibida de Gemini ({len(response)} caracteres)")

        # Extraer JSON de la respuesta
        data = extract_json_from_response(response)

        if not data:
            print(f"⚠️  No se pudo parsear JSON, creando estructura básica")
            # Crear estructura básica si no se puede parsear
            data = {
                "barrio": nombre,
                "comuna": comuna,
                "mes": "noviembre",
                "año": 2025,
                "fecha_consulta": datetime.now().strftime('%Y-%m-%d'),
                "caracteristica": f"Barrio de Buenos Aires en la zona {barrio['zona']}",
                "eventos_ferias_festivales": [],
                "recitales_shows_fiestas": [],
                "notas": [
                    f"No se encontraron eventos confirmados para {nombre} en este período",
                    "La información puede actualizarse a medida que se anuncien nuevos eventos",
                    "Respuesta raw de Gemini guardada para revisión manual"
                ],
                "total_eventos_festivales": 0,
                "total_recitales": 0,
                "fuente": "Gemini AI",
                "raw_response": response[:500]  # Guardar inicio de respuesta para debug
            }

        # Normalizar nombre para archivo
        filename = normalize_barrio_name(nombre) + "_noviembre.json"
        filepath = Path(__file__).parent / filename

        # Guardar JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Guardado: {filename}")
        print(f"📊 Eventos: {data.get('total_eventos_festivales', 0)}, Recitales: {data.get('total_recitales', 0)}")

        return True

    except Exception as e:
        print(f"❌ Error procesando {nombre}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    print("🚀 Iniciando procesamiento de barrios pendientes...")
    print(f"📝 Total a procesar: {len(BARRIOS_PENDIENTES)} barrios\n")

    # Verificar GEMINI_API_KEY
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ ERROR: GEMINI_API_KEY no está configurada en las variables de entorno")
        print("Por favor, configure la variable en el archivo .env")
        return

    # Inicializar servicio de IA
    ai_service = GeminiAIService()

    exitosos = 0
    fallidos = 0

    # Procesar cada barrio
    for i, barrio in enumerate(BARRIOS_PENDIENTES, 1):
        print(f"\n[{i}/{len(BARRIOS_PENDIENTES)}]")

        success = await process_barrio(barrio, ai_service)

        if success:
            exitosos += 1
        else:
            fallidos += 1

        # Esperar un poco entre requests para no sobrecargar la API
        if i < len(BARRIOS_PENDIENTES):
            print(f"\n⏳ Esperando 3 segundos antes del siguiente...")
            await asyncio.sleep(3)

    # Cerrar sesión HTTP
    if ai_service.session and not ai_service.session.closed:
        await ai_service.session.close()

    # Resumen final
    print(f"\n{'='*60}")
    print(f"✅ PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"✅ Exitosos: {exitosos}")
    print(f"❌ Fallidos: {fallidos}")
    print(f"📊 Total: {len(BARRIOS_PENDIENTES)}")
    print(f"\n💡 Próximo paso: Actualizar progreso.md")

if __name__ == "__main__":
    asyncio.run(main())
