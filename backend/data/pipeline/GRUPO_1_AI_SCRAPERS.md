# GRUPO 1: AI-Based Scrapers

**Sitios**: Felo.ai, Gemini.ai, Grok.com

**Última actualización**: 2025-11-14

---

## 📋 Descripción

Scrapers que usan AIs conversacionales para obtener eventos. Todos comparten el mismo procedimiento y formato de output.

---

## 🎯 Input

**Fuente**: `backend/data/regions/latinamerica/sudamerica/argentina.json`

**Datos a usar**:
- `cities[].name` → Ejemplo: "Buenos Aires", "Córdoba", "Rosario"

**Ejemplo de lectura**:
```python
import json
from pathlib import Path

# Leer archivo de región
with open('backend/data/regions/latinamerica/sudamerica/argentina.json', 'r') as f:
    data = json.load(f)

# Iterar ciudades
for city in data['cities']:
    ciudad = city['name']
    # Buenos Aires, Córdoba, Rosario
```

---

## 💬 Prompt Template (INFORMAL) - PROBADO Y FUNCIONAL

```
me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!
```

**Variables**:
- `{lugar}`: Ciudad desde `argentina.json` → `cities[].name`
  - Ejemplos: "Palermo, Buenos Aires", "Córdoba", "Rosario"

**Notas Críticas**:
- ✅ **Probado manualmente** - No triggerea anti-spam
- ✅ **Tono natural** - No levanta sospechas de bot
- ✅ **Pide mínimo 20 eventos** - Asegura cantidad suficiente
- ✅ **Campos completos** - nombre, descripción, fecha, lugar, dirección, precio
- ⚠️ **NO especifica formato JSON** - La AI responde en formato natural
- ⚠️ **Requiere post-procesamiento** - Parsear respuesta a JSON válido

**Post-procesamiento requerido**:
1. Extraer texto de respuesta de AI
2. Parsear a formato estructurado (regex o AI parsing)
3. Convertir a JSON array válido
4. Validar campos obligatorios
5. Normalizar fechas a formato YYYY-MM-DD

---

## 🔧 Parsing de Respuesta AI

Como el prompt NO especifica formato JSON, las AIs responden en formato natural/lista. Necesitamos parsear esto a JSON.

### Opción 1: Usar Gemini mismo para parsear
```python
def parse_ai_response(raw_text: str) -> list:
    """Usa Gemini para convertir respuesta natural a JSON"""

    parse_prompt = f"""
    Convierte esta lista de eventos a JSON válido.

    Texto:
    {raw_text}

    Formato esperado (JSON array):
    [
      {{
        "nombre": "string",
        "descripcion": "string",
        "fecha": "YYYY-MM-DD",
        "lugar": "string",
        "direccion": "string",
        "precio": "string o número"
      }}
    ]

    IMPORTANTE: Responde SOLO con el JSON, sin texto adicional.
    """

    # Llamar a Gemini nuevamente para parsear
    response = gemini.generate_content(parse_prompt)

    # Limpiar y parsear
    json_text = response.text.strip()
    json_text = json_text.replace('```json', '').replace('```', '')

    return json.loads(json_text)
```

### Opción 2: Regex pattern matching
```python
import re
from datetime import datetime

def parse_ai_response_regex(raw_text: str) -> list:
    """Parsea respuesta usando regex"""

    eventos = []

    # Pattern para detectar bloques de eventos
    # Ejemplo: "1. Nombre del evento\nFecha: ...\nLugar: ..."
    pattern = r'(\d+)\.\s*([^\n]+)\n(?:.*?Fecha:\s*([^\n]+))?(?:.*?Lugar:\s*([^\n]+))?(?:.*?Dirección:\s*([^\n]+))?(?:.*?Precio:\s*([^\n]+))?'

    matches = re.finditer(pattern, raw_text, re.DOTALL)

    for match in matches:
        evento = {
            'nombre': match.group(2).strip(),
            'fecha': normalize_fecha(match.group(3)),
            'lugar': match.group(4).strip() if match.group(4) else '',
            'direccion': match.group(5).strip() if match.group(5) else '',
            'precio': match.group(6).strip() if match.group(6) else 'gratis'
        }
        eventos.append(evento)

    return eventos

def normalize_fecha(fecha_str: str) -> str:
    """Normaliza fecha a YYYY-MM-DD"""
    # Parsear formatos comunes: "15 de noviembre", "2025-11-15", "15/11/2025"
    # ... lógica de parsing ...
    return "2025-11-15"  # Ejemplo
```

### Opción 3: Híbrido (RECOMENDADO)
```python
def parse_ai_response_hybrid(raw_text: str, ai_service: str) -> list:
    """
    1. Intenta parsear con regex
    2. Si falla, usa AI para parsear
    3. Valida campos obligatorios
    """

    try:
        # Intento 1: Regex
        eventos = parse_ai_response_regex(raw_text)
        if len(eventos) > 0:
            return eventos
    except Exception as e:
        print(f"⚠️ Regex parsing falló: {e}")

    try:
        # Intento 2: AI parsing
        eventos = parse_ai_response(raw_text)
        return eventos
    except Exception as e:
        print(f"❌ AI parsing falló: {e}")
        return []
```

---

## 📝 Formatos de Respuesta por AI

Cada AI responde con formato ligeramente diferente, pero todos son parseables.

### Felo.ai
```
1. Nombre del Evento
   - Fecha: 15 de noviembre de 2025
   - Lugar: Venue Name
   - Dirección: Calle 123
   - Precio: $1500

2. Otro Evento
   ...
```

### Gemini.ai
```
## 1. Nombre del Evento

**Fecha:** 2025-11-15
**Lugar:** Venue Name
**Dirección:** Calle 123
**Precio:** $1500
**Descripción:** Texto descriptivo...

## 2. Otro Evento
...
```

### Grok.com
```
Evento 1: Nombre del Evento
Fecha: 15/11/2025
Lugar: Venue Name
Dirección: Calle 123
Precio: 1500 pesos

Evento 2: Otro Evento
...
```

**Estrategia de parsing**:
- Detectar patrón de numeración (1., ##, Evento 1:)
- Extraer campos con regex flexible
- Normalizar fechas a YYYY-MM-DD
- Si falla regex, usar AI para re-parsear

---

## 📊 Formato JSON Esperado

El script `auto_import.py` acepta múltiples nombres de campos (flexible):

```json
[
  {
    "nombre": "string",           // o "titulo" o "title"
    "descripcion": "string",      // o "description" (opcional)
    "fecha_inicio": "YYYY-MM-DD", // o "fecha" o "start_date"
    "fecha_fin": "YYYY-MM-DD",    // opcional
    "lugar": "string",            // o "venue" o "venue_name"
    "direccion": "string",        // o "address" (opcional)
    "categoria": "string",        // música/deportes/cultural/fiesta/tech
    "precio": "number o string",  // "$500", "gratis", "free", 0
    "imagen": "url",              // o "image_url" (opcional)
    "url": "url"                  // o "event_url" (opcional)
  }
]
```

**Campos obligatorios**:
- `nombre` (o `title`)
- `fecha` (o `fecha_inicio` o `start_date`)
- `lugar` (o `venue`)
- `categoria`

**Campos opcionales** (pueden ser null o vacíos):
- `descripcion`
- `direccion`
- `precio` (default: gratis)
- `imagen`
- `url`

---

## ⚠️ Rate Limiting (CRÍTICO)

**Para evitar bloqueos:**

1. **Delay entre requests**:
   - Mínimo: 5 segundos
   - Recomendado: 10 segundos
   - Entre ciudades: 15-20 segundos

2. **Máximo por sesión**:
   - 3-5 ciudades por corrida
   - NO procesar todas las ciudades de una vez

3. **Rotar AIs**:
   - Ciudad 1 → Felo.ai
   - Ciudad 2 → Gemini.ai
   - Ciudad 3 → Grok.com
   - Volver a empezar con Felo para ciudad 4

4. **Horarios recomendados**:
   - Evitar: 9-12am, 2-5pm (horario pico)
   - Preferir: 6-8am, 8-11pm

---

## 💾 Guardado de Resultados

**Estructura de carpetas**:
```
scrapper_results/
└── latinamerica/
    └── sudamerica/
        └── argentina/
            ├── buenos-aires/
            │   ├── ai_felo_2025-11-14.json
            │   ├── ai_gemini_2025-11-14.json
            │   └── ai_grok_2025-11-14.json
            ├── cordoba/
            │   ├── ai_felo_2025-11-14.json
            │   └── ai_gemini_2025-11-14.json
            └── rosario/
                └── ai_felo_2025-11-14.json
```

**Naming convention**:
```
ai_{servicio}_{YYYY-MM-DD}.json
```

Ejemplos:
- `ai_felo_2025-11-14.json`
- `ai_gemini_2025-11-14.json`
- `ai_grok_2025-11-14.json`

---

## 📝 Logging Requerido

### Inicio de scraping
```
🚀 [AI-SCRAPER] Iniciando scraping del GRUPO 1
📍 Ciudad: Buenos Aires
🤖 AI seleccionada: Felo.ai
⏰ Timestamp: 2025-11-14 18:30:45
```

### Durante el proceso
```
💬 [FELO] Enviando prompt para Buenos Aires...
⏱️ [FELO] Esperando respuesta (timeout: 30s)...
✅ [FELO] Respuesta recibida (2.3s)
📊 [FELO] Eventos parseados: 12
```

### Guardado
```
💾 [SAVE] Guardando en: scrapper_results/.../buenos-aires/ai_felo_2025-11-14.json
✅ [SAVE] Archivo guardado exitosamente (12 eventos)
```

### Rate limiting
```
⏸️ [RATE-LIMIT] Esperando 10 segundos antes de siguiente request...
⏸️ [RATE-LIMIT] Esperando 20 segundos antes de cambiar de ciudad...
```

### Errores
```
❌ [ERROR] Timeout esperando respuesta de Gemini.ai
⚠️ [RETRY] Reintentando en 30 segundos (intento 1/3)...
❌ [ERROR] JSON inválido en respuesta de Grok
📝 [SKIP] Saltando evento sin campo 'nombre'
```

### Resumen final
```
✅ [RESUMEN] Scraping completado
📊 Total ciudades procesadas: 3
📊 Total eventos obtenidos: 45
📊 Archivos generados: 9
⏱️ Tiempo total: 8m 32s
```

---

## 🔄 Flujo de Ejecución

```
1. Leer argentina.json
2. Obtener lista de ciudades
3. Para cada ciudad (max 3-5):
   a. Seleccionar AI (rotar: Felo → Gemini → Grok)
   b. Construir prompt informal con ciudad
   c. Enviar request a AI
   d. Esperar respuesta (timeout 30s)
   e. Parsear respuesta JSON
   f. Validar campos obligatorios
   g. Guardar en archivo JSON
   h. Log resultados
   i. Rate limiting delay (10-20s)
4. Resumen final
```

---

## 🚦 Script Base (Simplificado y Realista)

```python
# backend/data/scripts/ai_scraper_grupo1.py

import json
import time
from pathlib import Path
from datetime import datetime
import requests

# Configuración
AI_SERVICES = ['felo', 'gemini', 'grok']
DELAY_BETWEEN_REQUESTS = 10
DELAY_BETWEEN_CITIES = 20
MAX_CITIES_PER_RUN = 3

def call_felo(prompt: str) -> str:
    """Llamada a Felo.ai - IMPLEMENTAR según su API"""
    # TODO: Implementar request específico de Felo
    return raw_response_text

def call_gemini(prompt: str) -> str:
    """Llamada a Gemini.ai"""
    import google.generativeai as genai
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def call_grok(prompt: str) -> str:
    """Llamada a Grok.com - IMPLEMENTAR según su API"""
    # TODO: Implementar request específico de Grok
    return raw_response_text

def parse_felo_format(raw_text: str) -> list:
    """Parsea formato específico de Felo"""
    # Formato: "1. Nombre\n   - Fecha: ...\n   - Lugar: ..."
    import re
    eventos = []
    pattern = r'(\d+)\.\s*([^\n]+)\n\s*-\s*Fecha:\s*([^\n]+)\n\s*-\s*Lugar:\s*([^\n]+)'
    # ... parsing logic ...
    return eventos

def parse_gemini_format(raw_text: str) -> list:
    """Parsea formato específico de Gemini"""
    # Formato: "## 1. Nombre\n**Fecha:** ...\n**Lugar:** ..."
    import re
    eventos = []
    # ... parsing logic ...
    return eventos

def parse_grok_format(raw_text: str) -> list:
    """Parsea formato específico de Grok"""
    # Formato: "Evento 1: Nombre\nFecha: ...\nLugar: ..."
    import re
    eventos = []
    # ... parsing logic ...
    return eventos

def scrape_grupo1():
    # 1. Leer ciudades
    with open('regions/latinamerica/sudamerica/argentina.json') as f:
        data = json.load(f)

    ciudades = [city['name'] for city in data['cities']][:MAX_CITIES_PER_RUN]

    # 2. Iterar ciudades
    for idx, ciudad in enumerate(ciudades):
        ai_service = AI_SERVICES[idx % len(AI_SERVICES)]

        print(f"🤖 [{ai_service.upper()}] Procesando {ciudad}...")

        # 3. Construir prompt
        prompt = f"me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {ciudad} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!"

        # 4. Llamar a AI según servicio
        if ai_service == 'felo':
            raw_response = call_felo(prompt)
            eventos = parse_felo_format(raw_response)
        elif ai_service == 'gemini':
            raw_response = call_gemini(prompt)
            eventos = parse_gemini_format(raw_response)
        elif ai_service == 'grok':
            raw_response = call_grok(prompt)
            eventos = parse_grok_format(raw_response)

        print(f"✅ [{ai_service.upper()}] {len(eventos)} eventos parseados")

        # 5. Guardar resultados
        output_dir = Path(f"scrapper_results/latinamerica/sudamerica/argentina/{ciudad.lower().replace(' ', '-')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"ai_{ai_service}_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eventos, f, indent=2, ensure_ascii=False)

        print(f"💾 Guardado en: {output_file}")

        # 6. Rate limiting
        if idx < len(ciudades) - 1:
            print(f"⏸️ Esperando {DELAY_BETWEEN_CITIES}s...")
            time.sleep(DELAY_BETWEEN_CITIES)

if __name__ == "__main__":
    scrape_grupo1()
```

---

## ✅ Checklist Pre-Ejecución

Antes de correr el scraper, verificar:

- [ ] `.env` tiene las API keys de las 3 AIs
- [ ] Carpeta `scrapper_results/` existe
- [ ] `argentina.json` tiene las ciudades correctas
- [ ] Rate limiting configurado (min 10s)
- [ ] Máximo de ciudades configurado (max 5)
- [ ] Logging habilitado
- [ ] No es horario pico (evitar 9am-5pm)

---

## 🐛 Problemas Comunes

### 1. AI no responde JSON válido
**Solución**: Agregar en el prompt "IMPORTANTE: responde SOLO con JSON válido, sin texto adicional"

### 2. Rate limiting - IP bloqueada
**Solución**: Esperar 1 hora, reducir frecuencia de requests, usar VPN

### 3. Eventos sin fecha válida
**Solución**: `auto_import.py` maneja múltiples formatos de fecha automáticamente

### 4. Duplicados entre diferentes AIs
**Solución**: `clean_duplicates.py` elimina duplicados por título + fecha

---

## 📚 Próximos Pasos

1. ✅ Documentar GRUPO 1 (este archivo)
2. ⏳ Implementar script `ai_scraper_grupo1.py`
3. ⏳ Probar con 1 ciudad primero
4. ⏳ Escalar a 3 ciudades
5. ⏳ Documentar GRUPO 2 (HTML Scraping)
6. ⏳ Documentar GRUPO 3 (APIs oficiales)
7. ⏳ Documentar GRUPO 4 (Scraping avanzado)
8. ⏳ Crear script maestro que ejecute todos los grupos

---

**Mantenedor**: Sistema de scraping procedural
**Fecha creación**: 2025-11-14
