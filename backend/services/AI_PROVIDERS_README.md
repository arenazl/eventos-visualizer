# 🤖 Sistema Multi-Provider de IA

Sistema flexible con fallback automático que soporta múltiples servicios de IA.

## 📋 Providers Disponibles

| Provider | Velocidad | Límites Gratis | Características | Registro |
|----------|-----------|----------------|-----------------|----------|
| **Grok** 🚀 | ⚡⚡⚡⚡ | Según plan | Grok-4, muy potente | https://x.ai |
| **Groq** ⚡ | ⚡⚡⚡⚡⚡ | 14,400/día | Ultra rápido, Llama 3 | https://console.groq.com |
| **Gemini** 🔷 | ⚡⚡⚡ | 250/día | Buen análisis | https://makersuite.google.com |
| **Perplexity** 🔍 | ⚡⚡⚡⚡ | 5/hora | Búsqueda web en tiempo real | https://www.perplexity.ai/settings/api |
| **OpenRouter** 🔄 | ⚡⚡⚡⚡ | Variables | Acceso a GPT-4, Claude, etc. | https://openrouter.ai |

## 🚀 Configuración Rápida

### 1. Obtener API Keys

#### Grok (xAI - Recomendado para este proyecto)
```bash
# Conseguir tu key en https://x.ai y agregarla al .env
GROK_API_KEY=xai-your-api-key-here
```

#### Groq (Opcional - Ultra rápido, gratis)
1. Ir a https://console.groq.com
2. Registrarse con Google/GitHub
3. Crear API Key en la sección "API Keys"
```bash
GROQ_API_KEY=gsk_tu_clave_aqui
```

#### Gemini (Ya configurado)
```bash
# Ya tenés esta configurada
GEMINI_API_KEY=tu_clave_existente
```

#### Perplexity (Opcional - Para búsqueda web)
1. Ir a https://www.perplexity.ai/settings/api
2. Crear cuenta y generar API key
```bash
PERPLEXITY_API_KEY=pplx-tu_clave_aqui
```

#### OpenRouter (Opcional - Acceso a múltiples modelos)
1. Ir a https://openrouter.ai
2. Registrarse y crear API key
```bash
OPENROUTER_API_KEY=sk-or-tu_clave_aqui
```

### 2. Configurar `.env`

```bash
# backend/.env

# Provider preferido (grok, groq, gemini, perplexity, openrouter)
PREFERRED_AI_PROVIDER=grok

# API Keys (solo las que tengas)
GROK_API_KEY=xai-your-api-key-here
GROQ_API_KEY=gsk_tu_clave_aqui  # Opcional
GEMINI_API_KEY=tu_clave_existente
PERPLEXITY_API_KEY=pplx_tu_clave_aqui  # Opcional
OPENROUTER_API_KEY=sk-or-tu_clave_aqui  # Opcional
```

### 3. Reiniciar Backend

```bash
# Detener servidor actual
lsof -ti:8001 | xargs kill -9

# En Windows:
taskkill /F /PID <pid>

# Reiniciar
cd backend
python main.py
```

## 📊 Verificar Estado

### Desde el backend:

```bash
# Ver qué providers están configurados
curl http://localhost:8001/api/ai/provider/status
```

Respuesta:
```json
{
  "preferred": "grok",
  "providers": {
    "grok": {
      "configured": true,
      "name": "GrokProvider"
    },
    "groq": {
      "configured": false,
      "name": "GroqProvider"
    },
    "gemini": {
      "configured": true,
      "name": "GeminiProvider"
    },
    "perplexity": {
      "configured": false,
      "name": "PerplexityProvider"
    },
    "openrouter": {
      "configured": false,
      "name": "OpenRouterProvider"
    }
  }
}
```

## 🔄 Cambiar Provider

### Desde API:

```bash
# Cambiar a Grok
curl -X POST http://localhost:8001/api/ai/provider/set \
  -H "Content-Type: application/json" \
  -d '{"provider": "grok"}'

# Cambiar a Gemini
curl -X POST http://localhost:8001/api/ai/provider/set \
  -H "Content-Type: application/json" \
  -d '{"provider": "gemini"}'
```

### Desde Python (backend):

```python
from services.ai_manager import AIServiceManager

manager = AIServiceManager()

# Cambiar provider
manager.set_preferred_provider("grok")

# Ver estado
status = manager.get_provider_status()
print(status)
```

## 🎨 Uso en el Código

### Generar Respuesta Simple

```python
from services.ai_manager import AIServiceManager

manager = AIServiceManager()

# Generar respuesta usando provider preferido con fallback automático
response = await manager.generate(
    prompt="¿Qué eventos hay en Buenos Aires?",
    temperature=0.7
)

print(response)
```

### Generar Respuesta JSON

```python
from services.ai_manager import AIServiceManager

manager = AIServiceManager()

# Generar y parsear JSON automáticamente
data = await manager.generate_json(
    prompt="""Lista 3 ciudades cercanas a Buenos Aires en JSON:
    {"cities": [{"name": "...", "distance": "..."}]}""",
    temperature=0.3
)

print(data["cities"])
```

### Generar Contexto de Evento

```python
from services.ai_manager import generate_event_context

event_data = {
    "title": "Lollapalooza Argentina",
    "category": "music",
    "venue_name": "Hipódromo de San Isidro",
    "city": "Buenos Aires",
    "start_datetime": "2025-03-21"
}

context = await generate_event_context(event_data)

print(context)
# {
#   "curiosidades": ["...", "...", "..."],
#   "que_llevar": ["...", "...", "..."],
#   "ambiente_esperado": "...",
#   "tip_local": "..."
# }
```

### Detectar Ubicación

```python
from services.ai_manager import detect_location_info

location_info = await detect_location_info("Palermo")

print(location_info)
# {
#   "city": "Palermo",
#   "province": "Buenos Aires",
#   "country": "Argentina",
#   "confidence": 0.95
# }
```

## 🔧 Sistema de Fallback Automático

El sistema intenta automáticamente con otros providers si el preferido falla:

```
Orden de fallback por defecto:
1. Grok (si configurado)
2. Groq (si configurado)
3. Gemini (si configurado)
4. OpenRouter (si configurado)
5. Perplexity (si configurado)
```

### Ejemplo de Fallback:

```python
manager = AIServiceManager()

# Aunque Grok sea el preferido, si falla automáticamente
# intentará con Groq, luego Gemini, etc.
response = await manager.generate(
    prompt="¿Qué eventos hay?",
    use_fallback=True  # True por defecto
)
```

### Deshabilitar Fallback:

```python
# Solo usar el provider preferido, no intentar otros
response = await manager.generate(
    prompt="¿Qué eventos hay?",
    use_fallback=False
)
```

## 📡 Endpoints API

### GET `/api/ai/provider/status`
Obtener estado de todos los providers

**Respuesta:**
```json
{
  "preferred": "grok",
  "providers": {
    "grok": {"configured": true, "name": "GrokProvider"},
    ...
  }
}
```

### POST `/api/ai/provider/set`
Cambiar provider preferido

**Body:**
```json
{
  "provider": "grok"
}
```

**Respuesta:**
```json
{
  "success": true,
  "provider": "grok",
  "message": "Provider cambiado a grok exitosamente"
}
```

### POST `/api/ai/generate-event-context`
Generar contexto adicional para un evento

**Body:**
```json
{
  "event_data": {
    "title": "Lollapalooza Argentina",
    "category": "music",
    "venue_name": "Hipódromo de San Isidro",
    "city": "Buenos Aires",
    "start_datetime": "2025-03-21"
  }
}
```

**Respuesta:**
```json
{
  "success": true,
  "curiosidades": [
    "El Hipódromo de San Isidro es uno de los más importantes de Sudamérica",
    "Lollapalooza comenzó en Chicago en 1991",
    "Esta edición contará con más de 100 artistas"
  ],
  "que_llevar": [
    "Protector solar",
    "Botella de agua reutilizable",
    "Efectivo para puestos de comida"
  ],
  "ambiente_esperado": "Festival masivo con múltiples escenarios, ambiente joven y energético",
  "tip_local": "Llegá temprano porque el tráfico en San Isidro se complica. Podés tomar el Tren Mitre hasta estación Hipódromo."
}
```

## 🎯 Casos de Uso por Provider

### Grok 🚀
**Mejor para:**
- Análisis general de eventos
- Detección de ubicaciones
- Respuestas rápidas y precisas
- **USO ACTUAL:** Provider por defecto del proyecto

### Groq ⚡
**Mejor para:**
- UI/UX donde se necesita respuesta instantánea
- Alto volumen de requests (14,400/día)
- Costo $0

### Gemini 🔷
**Mejor para:**
- Análisis de contexto largo
- Fallback cuando otros providers no disponibles
- Integración con Google Services

### Perplexity 🔍
**Mejor para:**
- Verificar si eventos siguen vigentes
- Obtener clima esperado para la fecha
- Buscar lugares cercanos al evento
- Info actualizada de artistas/venues

### OpenRouter 🔄
**Mejor para:**
- Necesitas modelo específico (GPT-4, Claude)
- Fallback multi-modelo
- Flexibilidad de pricing

## ⚠️ Troubleshooting

### Error: "GROK_API_KEY no configurada"
```bash
# Verificar que el .env tiene la key
cat backend/.env | grep GROK_API_KEY

# Si no está, agregarla
echo 'GROK_API_KEY=xai-tu_clave_aqui' >> backend/.env
```

### Error: "Provider no está configurado"
Significa que el provider que intentás usar no tiene API key en el `.env`. Configura otra o agrega la key faltante.

### Todos los providers fallan
```python
# Ver logs para diagnosticar
logger.error("❌ Todos los providers fallaron")

# Verificar conexión a internet
# Verificar que las API keys sean válidas
# Ver estado de providers
curl http://localhost:8001/api/ai/provider/status
```

## 📚 Arquitectura

```
backend/services/
├── ai_providers.py      # Clases de providers individuales
├── ai_manager.py        # Manager con fallback automático
├── ai_service.py        # Servicio legacy (usa ai_manager internamente)
└── AI_PROVIDERS_README.md  # Esta documentación
```

### Flujo de Llamada:

```
Usuario/Frontend
    ↓
Endpoint (/api/ai/...)
    ↓
AIServiceManager.generate()
    ↓
Intenta con provider preferido
    ↓ (si falla)
Fallback automático a otros providers
    ↓
Retorna respuesta o error
```

## 🔐 Seguridad

- **API Keys**: Nunca commitear al repo, solo en `.env` local
- **Rate Limiting**: Cada provider tiene sus propios límites
- **Fallback**: Asegura disponibilidad incluso si un servicio cae
- **Logs**: Todos los intentos y fallos se loguean para debugging

## 📈 Monitoreo

Ver logs en tiempo real:
```bash
# Backend logs mostrarán qué provider se usó
✅ Grok respondió exitosamente
⚠️ Gemini API error: HTTP 429
🔄 Iniciando fallback automático...
✅ Fallback exitoso con Groq
```

---

**🎉 Sistema configurado y listo para usar con Grok como provider principal!**
