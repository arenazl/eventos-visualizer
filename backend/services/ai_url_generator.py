"""
🧠 AI URL Generator - Generador inteligente de URLs sin hardcodeos
Pregunta a la IA el formato específico de cada sitio web
Usa Google Gemini (gratis) para generar URLs correctas
"""

import logging
from typing import Optional
import asyncio
import os
import aiohttp
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class AIUrlGenerator:
    """
    Generador inteligente de URLs usando IA
    Cada sitio web tiene su propio formato - la IA lo conoce
    """
    
    def __init__(self):
        self.cache = {}  # Cache de URLs generadas
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')  # API key desde .env
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    async def generate_url_for_site(self, sitio: str, ciudad: str) -> Optional[str]:
        """
        Genera URL correcta preguntando a la IA el formato específico del sitio
        
        Args:
            sitio: Nombre del sitio web (ej: "eventbrite.com", "meetup.com")
            ciudad: Ciudad para buscar eventos (ej: "Ramos Mejía", "Barcelona")
            
        Returns:
            URL completa generada por IA
        """
        try:
            # Cache key para evitar llamadas repetidas
            cache_key = f"{sitio}|{ciudad}"
            if cache_key in self.cache:
                logger.info(f"🧠 AI URL Cache hit: {sitio} + {ciudad}")
                return self.cache[cache_key]
            
            # Prompt específico para generar URL
            ai_prompt = f"""
            Por favor, ayúdame con dos tareas importantes:

            1️⃣ COMPLETAR NOMBRES: Por favor, completáme los nombres de ciudades/países ya que las URLs me exigen el nombre entero completo.
            
            2️⃣ CAMBIAR FORMATO: Por favor, cambia el formato para generar la URL correcta de este sitio web específico.

            Datos:
            - Sitio web: {sitio}
            - Ciudad (posiblemente incompleta): {ciudad}

            TAREA 1 - COMPLETAR NOMBRES INCOMPLETOS:
            Las URLs necesitan nombres completos. Si recibo nombres parciales, completálos:
            - "Ramos" → completar a "Ramos Mejía, Buenos Aires, Argentina"  
            - "Villa" → completar a "Villa [nombre completo], Argentina"
            - "San" → completar a "San [nombre completo]" según geografía
            - "Merlo" → completar a "Merlo, Buenos Aires, Argentina" 
            - "Mexico" → completar a "Mexico City, Mexico"
            - Usar tu conocimiento geográfico para identificar la ciudad completa exacta

            TAREA 2 - FORMATO ESPECÍFICO POR SITIO WEB:
            Cada sitio web tiene su formato único de URL. Usa el formato correcto:
            - eventbrite.com: /d/pais/ciudad/ (ej: /d/argentina/ramos-mejia/)
            - meetup.com: /find/?location=ciudad (ej: /find/?location=barcelona)  
            - facebook.com: /events/discovery/?city=ciudad
            - ticketmaster.com: /city/ciudad-CODE
            - timeout.com: /ciudad/events
            - turismo.buenosaires.gob.ar: /es/article/que-hacer-esta-semana (URL fija)
            - castelar-digital.com.ar: /agenda/ (URL fija)

            PROCESO:
            1. Primero completa el nombre de la ciudad/país
            2. Luego normaliza: espacios→guiones, sin acentos, minúsculas  
            3. Finalmente aplica el formato específico del sitio
            4. Genera URL completa con https://

            EJEMPLOS DEL PROCESO COMPLETO:
            - {sitio} + "Ramos" → completar "Ramos Mejía" → normalizar "ramos-mejia" → aplicar formato del sitio
            - {sitio} + "Villa Ball" → completar "Villa Ballester" → normalizar "villa-ballester" → aplicar formato
            - {sitio} + "Mexico" → completar "Mexico City" → normalizar "mexico-city" → aplicar formato

            Por favor, responde SOLO con la URL completa final:
            """
            
            # 🪄 LLAMADA GEMINI AI REAL 
            url = await self._call_gemini_ai(ai_prompt)
            
            # Fallback a simulación si Gemini falla
            if not url:
                logger.warning(f"Gemini AI failed, using fallback for {sitio} + {ciudad}")
                url = await self._simulate_ai_response(sitio, ciudad)
            
            # Guardar en cache
            self.cache[cache_key] = url
            
            logger.info(f"🧠 AI Generated URL: {sitio} + {ciudad} → {url}")
            return url
            
        except Exception as e:
            logger.error(f"❌ AI URL generation failed for {sitio} + {ciudad}: {e}")
            return None

    async def _simulate_ai_response(self, sitio: str, ciudad: str) -> str:
        """
        Simulación de respuesta IA - reemplazar con API real
        """
        sitio_lower = sitio.lower()
        ciudad_lower = ciudad.lower()
        
        # Normalizar ciudad
        def normalize_city(city_text: str) -> str:
            return (city_text
                   .replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
                   .replace(' ', '-')
                   .replace(',', '')
                   .strip('-'))
        
        ciudad_normalizada = normalize_city(ciudad_lower)
        
        # Lógica específica por sitio (conocimiento IA)
        if 'eventbrite' in sitio_lower:
            # Detectar país
            if any(term in ciudad_lower for term in ['argentina', 'buenos aires', 'ramos mejía', 'merlo']):
                return f"https://www.eventbrite.com/d/argentina/{ciudad_normalizada}/"
            elif any(term in ciudad_lower for term in ['españa', 'barcelona', 'madrid']):
                return f"https://www.eventbrite.com/d/spain/{ciudad_normalizada}/"
            elif any(term in ciudad_lower for term in ['méxico', 'mexico']):
                return f"https://www.eventbrite.com/d/mexico/{ciudad_normalizada}/"
            else:
                # Default a argentina
                return f"https://www.eventbrite.com/d/argentina/{ciudad_normalizada}/"
                
        elif 'meetup' in sitio_lower:
            return f"https://www.meetup.com/find/?location={ciudad_normalizada}"
            
        elif 'facebook' in sitio_lower:
            return f"https://www.facebook.com/events/discovery/?city={ciudad_normalizada}"
            
        elif 'ticketmaster' in sitio_lower:
            # Ticketmaster usa códigos específicos, la IA debería conocerlos
            city_code = ciudad_normalizada[:4].upper() + "AR"  # Ejemplo
            return f"https://www.ticketmaster.com.ar/city/{ciudad_normalizada}-{city_code}"
            
        elif 'turismo.buenosaires' in sitio_lower:
            # URL fija - ignora ciudad
            return "https://turismo.buenosaires.gob.ar/es/article/que-hacer-esta-semana"
            
        elif 'castelar-digital' in sitio_lower:
            # URL fija - ignora ciudad  
            return "https://www.castelar-digital.com.ar/agenda/"
            
        elif 'timeout' in sitio_lower:
            return f"https://www.timeout.com/{ciudad_normalizada}/events"
            
        else:
            # Formato genérico
            return f"https://www.{sitio}/{ciudad_normalizada}/events/"

    async def _call_gemini_ai(self, prompt: str) -> Optional[str]:
        """
        Llamada real a Google Gemini AI (GRATIS)
        """
        if not self.gemini_api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")
            return None
            
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            url_with_key = f"{self.gemini_url}?key={self.gemini_api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url_with_key, headers=headers, json=payload, timeout=10) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Gemini AI HTTP {response.status}: {error_text}")
                        return None
                    
                    data = await response.json()
                    
                    if 'candidates' in data and len(data['candidates']) > 0:
                        generated_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        logger.info(f"🧠 Gemini AI response: {generated_text}")
                        
                        # Extraer solo la URL si hay texto adicional
                        if 'http' in generated_text:
                            import re
                            url_match = re.search(r'https?://[^\s\n]+', generated_text)
                            if url_match:
                                return url_match.group(0)
                        
                        return generated_text
                    
                    logger.error("❌ Gemini AI: No candidates in response")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Gemini AI error: {e}")
            return None

    def get_url_sync(self, sitio: str, ciudad: str) -> Optional[str]:
        """
        Wrapper sincrónico para compatibilidad
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.generate_url_for_site(sitio, ciudad))
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.generate_url_for_site(sitio, ciudad))
            finally:
                loop.close()


# Instancia global
ai_url_generator = AIUrlGenerator()

async def get_url_with_ai(sitio: str, ciudad: str) -> Optional[str]:
    """
    Función de conveniencia para generar URLs con IA
    
    Ejemplos:
    - get_url_with_ai("eventbrite.com", "Ramos Mejía") 
      → https://www.eventbrite.com/d/argentina/ramos-mejia/
    - get_url_with_ai("meetup.com", "Barcelona")
      → https://www.meetup.com/find/?location=barcelona
    """
    return await ai_url_generator.generate_url_for_site(sitio, ciudad)

def get_url_with_ai_sync(sitio: str, ciudad: str) -> Optional[str]:
    """
    Versión sincrónica para uso en scrapers existentes
    """
    return ai_url_generator.get_url_sync(sitio, ciudad)


if __name__ == "__main__":
    # Tests
    async def test_ai_url_generator():
        generator = AIUrlGenerator()
        
        tests = [
            ("eventbrite.com", "Ramos Mejía"),
            ("eventbrite.com", "Barcelona"),  
            ("meetup.com", "Buenos Aires"),
            ("facebook.com", "Madrid"),
            ("turismo.buenosaires.gob.ar", "cualquier ciudad"),
            ("castelar-digital.com.ar", "Castelar"),
        ]
        
        print("🧠 Testing AI URL Generator:")
        for sitio, ciudad in tests:
            url = await generator.generate_url_for_site(sitio, ciudad)
            print(f"   {sitio} + {ciudad} → {url}")
    
    asyncio.run(test_ai_url_generator())