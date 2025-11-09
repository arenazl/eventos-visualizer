<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-01-12 23:00
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-01-12 23:00: Creación inicial - Estrategia de Gemini como scraper universal
📋 TAGS: #gemini #scraping #ai #estrategia #arma-secreta
-->

# 🔮 GEMINI COMO SCRAPER UNIVERSAL - LA ARMA SECRETA

## 💡 EL CONCEPTO

**En lugar de crear 50 scrapers específicos con BeautifulSoup:**

❌ **Enfoque tradicional** (lo que teníamos):
```python
# eventbrite_scraper.py - 400 líneas
soup = BeautifulSoup(html)
events = soup.find_all("div", class="event-card")
for event in events:
    title = event.find("h2", class="title").text
    date = event.find("time")["datetime"]
    # ... 50 líneas más de parsing frágil
```

✅ **Enfoque Gemini** (el futuro):
```python
# gemini_universal_scraper.py - 100 líneas totales
html = fetch_page(url)
prompt = f"""
Extrae eventos de este HTML y devuelve JSON:
{{
  "events": [
    {{"title": "...", "date": "...", "location": "...", "price": "..."}}
  ]
}}

HTML:
{html[:8000]}  # Primeros 8K tokens
"""
events = await gemini.call(prompt)
```

---

## 🎯 VENTAJAS DE GEMINI SCRAPER

### ✅ **1. UNIVERSAL - Funciona con CUALQUIER sitio**
- No necesitas parsear HTML manualmente
- No te rompe cuando cambian el diseño del sitio
- Gemini "entiende" el contenido semánticamente

### ✅ **2. BARATO/GRATIS**
- Gemini Flash 2.0: **GRATIS hasta 1,500 requests/día**
- Después: $0.00001875 por 1K tokens (casi gratis)
- Ejemplo: 1 millón de requests = ~$20

### ✅ **3. RÁPIDO**
- Gemini Flash 2.0: Optimizado para speed
- Respuesta en <1 segundo típicamente
- Paralelizable fácilmente

### ✅ **4. MANTENIMIENTO MÍNIMO**
- Un solo scraper para todos los sitios
- Solo ajustar prompt si la calidad baja
- No rompe con cambios de HTML

### ✅ **5. DATOS ESTRUCTURADOS**
- Retorna JSON directamente
- No necesitas regex ni parsers complejos
- Maneja edge cases automáticamente

---

## 🏗️ ARQUITECTURA PROPUESTA

### **GEMINI UNIVERSAL SCRAPER**

```python
# services/gemini_universal_scraper.py

class GeminiUniversalScraper(BaseGlobalScraper):
    """
    🔮 SCRAPER UNIVERSAL CON GEMINI

    Funciona con CUALQUIER sitio web de eventos:
    - Eventbrite
    - Resident Advisor
    - TimeOut
    - Cualquier blog de eventos
    - Páginas de venues locales
    - etc.
    """

    def __init__(self, ai_service: GeminiAIService):
        self.ai = ai_service

    async def scrape_events(
        self,
        url: str,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        1. Fetch HTML del sitio
        2. Enviar a Gemini con prompt estructurado
        3. Recibir JSON de eventos
        4. Validar y retornar
        """

        # 1. Fetch HTML
        html = await self._fetch_html(url)

        # 2. Preparar prompt optimizado
        prompt = self._build_extraction_prompt(html, location, category)

        # 3. Llamar a Gemini
        response = await self.ai._call_gemini_api(prompt)

        # 4. Parsear JSON
        events = self._parse_gemini_response(response)

        return events[:limit]
```

---

## 📝 PROMPT TEMPLATE OPTIMIZADO

### **Versión 1 - Básica**

```python
def _build_extraction_prompt(self, html: str, location: str, category: str) -> str:
    return f"""
Eres un experto extractor de información de eventos.

TAREA:
Extrae TODOS los eventos de este HTML y devuelve JSON válido.

UBICACIÓN: {location}
CATEGORÍA: {category or "todas"}

FORMATO DE SALIDA (JSON):
{{
  "events": [
    {{
      "title": "Nombre del evento",
      "date": "YYYY-MM-DD",
      "time": "HH:MM" o null,
      "location": "Venue o dirección",
      "description": "Breve descripción",
      "price": "Precio o 'Gratis'",
      "image_url": "URL de imagen" o null,
      "event_url": "URL del evento"
    }}
  ]
}}

REGLAS IMPORTANTES:
1. Solo eventos futuros (desde hoy {datetime.now().strftime("%Y-%m-%d")})
2. SIEMPRE incluir title, date, location
3. Si falta info, usar null (no inventar)
4. Fechas en formato ISO (YYYY-MM-DD)
5. Precios en formato: "$100", "€50", "Gratis", etc.

HTML A ANALIZAR:
{html[:8000]}

RESPONDE SOLO CON JSON VÁLIDO, SIN EXPLICACIONES.
"""
```

### **Versión 2 - Con ejemplos (Few-shot)**

```python
def _build_extraction_prompt_advanced(self, html: str, location: str) -> str:
    return f"""
Extrae eventos del HTML como en estos ejemplos:

EJEMPLO 1 - Evento completo:
{{
  "title": "Concierto de Coldplay",
  "date": "2025-03-15",
  "time": "21:00",
  "location": "Estadio River Plate, Buenos Aires",
  "description": "World Tour 2025",
  "price": "$15000",
  "image_url": "https://...",
  "event_url": "https://..."
}}

EJEMPLO 2 - Evento mínimo (info parcial):
{{
  "title": "Stand-up Comedy Night",
  "date": "2025-02-10",
  "time": null,
  "location": "Teatro Gran Rex",
  "description": null,
  "price": "Gratis",
  "image_url": null,
  "event_url": "https://..."
}}

AHORA EXTRAE EVENTOS DE ESTE HTML:
{html[:8000]}

Ubicación actual: {location}
Solo eventos en esta ubicación o cercanos.

RETORNA JSON:
{{
  "events": [...]
}}
"""
```

### **Versión 3 - Con validación estricta**

```python
STRICT_SCHEMA = """
{
  "events": [
    {
      "title": string (requerido, max 200 chars),
      "date": string (requerido, formato YYYY-MM-DD),
      "time": string | null (formato HH:MM),
      "location": string (requerido, max 150 chars),
      "description": string | null (max 500 chars),
      "price": string | null,
      "image_url": string | null (URL válida),
      "event_url": string (requerido, URL válida)
    }
  ]
}
"""
```

---

## 🎛️ CASOS DE USO

### **Caso 1: Scrapear sitios sin API**

```python
# Resident Advisor (no tiene API)
url = "https://ra.co/events/ar/buenosaires"
events = await gemini_scraper.scrape_events(
    url=url,
    location="Buenos Aires, Argentina",
    category="electrónica"
)
# ✅ Gemini extrae eventos aunque la estructura HTML cambie
```

### **Caso 2: Venues locales**

```python
# Cualquier bar/club que publique eventos
url = "https://www.niceltoclub.com/agenda"
events = await gemini_scraper.scrape_events(
    url=url,
    location="Buenos Aires, Argentina"
)
# ✅ Funciona sin configuración específica
```

### **Caso 3: Descubrir fuentes nuevas**

```python
# Gemini puede descubrir URLs de eventos también
discover_prompt = f"""
Dame 5 URLs de sitios web con eventos en {location}.
Pueden ser:
- Sitios de ticketing
- Agendas de venues
- Blogs de eventos
- Calendarios culturales

Devuelve JSON:
{{
  "sources": [
    {{"name": "...", "url": "...", "type": "..."}}
  ]
}}
"""
sources = await gemini.call(discover_prompt)
```

---

## 💰 COSTO ESTIMADO

### **Gemini Flash 2.0 Pricing:**

| Volumen | Costo Input | Costo Output | Total |
|---------|-------------|--------------|-------|
| 0-1,500 req/día | **GRATIS** | **GRATIS** | **$0** |
| 1,501-10K req/día | $0.00001875/1K tokens | $0.000075/1K tokens | ~$1-5/día |
| 10K-100K req/día | (mismo) | (mismo) | ~$10-50/día |

**Ejemplo real:**
- 1 request = ~10K tokens (8K input HTML + 2K output JSON)
- 1,000 requests = ~$0.10
- **100,000 eventos scrapeados = ~$10**

**VS scrapers tradicionales:**
- Proxies: $50-500/mes
- Mantenimiento: horas/semana
- Infraestructura: $20-100/mes

---

## ⚡ IMPLEMENTACIÓN RÁPIDA

### **Paso 1: Crear scraper básico**

```bash
# Archivo: backend/services/gemini_universal_scraper.py
```

```python
from services.ai_service import GeminiAIService
import aiohttp
import json
import re

class GeminiUniversalScraper:
    def __init__(self):
        self.ai = GeminiAIService()

    async def scrape_url(self, url: str, location: str) -> List[Dict]:
        # 1. Fetch HTML
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.text()

        # 2. Prompt Gemini
        prompt = f"""Extrae eventos de este HTML.

Ubicación: {location}

Devuelve JSON:
{{
  "events": [
    {{"title": "...", "date": "YYYY-MM-DD", "location": "..."}}
  ]
}}

HTML:
{html[:8000]}

SOLO JSON, sin explicaciones.
"""

        # 3. Llamar Gemini
        response = await self.ai._call_gemini_api(prompt)

        # 4. Extraer JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get('events', [])

        return []
```

### **Paso 2: Testear**

```python
# test_gemini_scraper.py
scraper = GeminiUniversalScraper()

# Probar con Resident Advisor
events = await scraper.scrape_url(
    "https://ra.co/events/ar/buenosaires",
    "Buenos Aires, Argentina"
)

print(f"✅ Extraídos {len(events)} eventos")
for event in events[:3]:
    print(f"  - {event['title']} ({event['date']})")
```

---

## 🎯 ESTRATEGIA DE IMPLEMENTACIÓN

### **FASE 1: Prueba de concepto (1-2 días)**
1. Crear gemini_universal_scraper.py básico
2. Testear con 3-4 sitios diferentes:
   - Resident Advisor
   - TimeOut Buenos Aires
   - Un venue local
3. Iterar en el prompt hasta 80% accuracy

### **FASE 2: Integración (2-3 días)**
4. Integrar con IndustrialFactory
5. Agregar a auto_discovery como scraper más
6. Configurar caching de resultados

### **FASE 3: Escalado (1 semana)**
7. Crear lista de 50+ fuentes de eventos
8. Ejecutar Gemini scraper en paralelo
9. Agregar validación y deduplicación

---

## 🚨 CONSIDERACIONES IMPORTANTES

### ✅ **Ventajas sobre APIs oficiales:**
- No necesitas API keys
- No hay rate limits (excepto Gemini: 1,500/día gratis)
- Funciona con sitios pequeños sin API

### ⚠️ **Limitaciones:**
- Gemini tiene límite de tokens (8K-32K según modelo)
  - Solución: Scrapear página por página
- Puede alucinar datos si HTML confuso
  - Solución: Validar campos requeridos
- Necesita HTML limpio
  - Solución: Usar BeautifulSoup para limpiar primero

### 🔑 **Key Success Factors:**
1. **Prompt bien diseñado** - Iterar hasta 80%+ accuracy
2. **Validación de output** - No confiar ciegamente en Gemini
3. **Caching inteligente** - No re-scrapear mismo sitio cada 5 minutos
4. **Fallbacks** - Si Gemini falla, intentar scraper tradicional

---

## 📊 COMPARACIÓN: GEMINI vs SCRAPERS TRADICIONALES

| Aspecto | Scrapers Tradicionales | Gemini Universal |
|---------|------------------------|------------------|
| **Desarrollo** | 5-10 horas/scraper | 30 min setup inicial |
| **Mantenimiento** | Alto (rompe con cambios HTML) | Bajo (Gemini se adapta) |
| **Cobertura** | 1 sitio por scraper | TODOS los sitios |
| **Costo** | Proxies $50-500/mes | $0-10/mes |
| **Precisión** | 95%+ (si no rompe) | 80-90% |
| **Escalabilidad** | Lineal (N scrapers) | Constante (1 scraper) |
| **Flexibilidad** | Baja (hardcodeado) | Alta (prompt adaptable) |

---

## 🎯 RECOMENDACIÓN FINAL

**ESTRATEGIA ÓPTIMA (Lo mejor de ambos mundos):**

1. **APIs oficiales** para sitios grandes:
   - Ticketmaster API
   - Eventbrite API
   - SeatGeek API

2. **Gemini Universal Scraper** para todo lo demás:
   - Resident Advisor
   - TimeOut
   - Venues locales
   - Blogs de eventos
   - Agendas culturales

3. **Mantener scrapers específicos** solo si:
   - Gemini no alcanza 80% accuracy
   - Sitio tiene anti-bot muy fuerte
   - Necesitas precisión 99%+

---

## 💡 PRÓXIMO PASO

¿Querés que implementemos un prototipo de Gemini Universal Scraper ahora?

Puedo crear:
1. `gemini_universal_scraper.py` básico
2. Script de prueba con 3-4 sitios
3. Documento de mejores prompts

**Tiempo estimado:** 30-60 minutos para prototipo funcional.
