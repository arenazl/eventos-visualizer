# 🧠 Gemini Brain - Configuración IA-First

## 🚀 Setup Rápido

### 1. Agregar tu API Key de Gemini

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env y agregar tu key
GEMINI_API_KEY=tu_api_key_aqui
```

### 2. Probar el Sistema IA

#### Chat Inteligente para Indecisos
```bash
# Usuario indeciso típico
curl -X POST http://172.29.228.80:8001/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "no se que hacer este finde, ayuda",
    "context": {"user_id": "usuario123"}
  }'
```

#### Respuestas Esperadas:
- Si detecta indecisión → 3 opciones súper claras
- Si detecta mood específico → Recomendación personalizada
- Aprende con cada interacción

## 🎯 Features del Gemini Brain

### 1. **Detección de Indecisos**
Frases que activan el modo indeciso:
- "no sé qué hacer"
- "estoy aburrido"
- "ayudame a decidir"
- "dame opciones"
- "sugerime algo"

### 2. **Perfiles de Personalidad**
El sistema detecta automáticamente:
- **Mood**: energético, relajado, romántico, cultural, social, aventurero
- **Presupuesto**: bajo, medio, alto
- **Estilo de decisión**: indeciso, decisivo, conservador, experimental
- **Con quién**: solo, pareja, amigos, familia

### 3. **Memoria y Aprendizaje**
```bash
# Enviar feedback sobre eventos
curl -X POST http://172.29.228.80:8001/api/ai/gemini/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usuario123",
    "event_id": "evento456",
    "feedback": "liked"
  }'

# Ver perfil aprendido del usuario
curl http://172.29.228.80:8001/api/ai/gemini/profile/usuario123
```

## 🔥 Ejemplos de Uso Real

### Conversación Típica:

**Usuario indeciso:**
> "no se que hacer, estoy aburrido"

**Gemini Brain responde:**
> "🎯 ¡Perfecto! Te voy a hacer súper fácil la decisión. Te doy 3 opciones GENIALES:
> 
> 1. 🎉 **Fiesta Rooftop en Palermo** - Música increíble, vista de la ciudad (Match: 92%)
> 2. 🍷 **Noche de Jazz y Vinos** - Relajado pero interesante (Match: 88%)  
> 3. 🎮 **Arcade Bar Retro** - Nostalgia y tragos temáticos (Match: 85%)
>
> ¿Cuál te llamó más la atención? ¿O querés que elija yo por vos? 😊"

### Después de varias interacciones:

**Sistema aprende que el usuario:**
- Prefiere eventos nocturnos
- Le gusta la música en vivo
- Presupuesto medio-alto
- Generalmente va con amigos

**Próximas recomendaciones serán aún más precisas!**

## 📊 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/ai/chat` | POST | Chat principal con Gemini Brain |
| `/api/ai/recommendations` | POST | Recomendaciones personalizadas |
| `/api/ai/plan-weekend` | POST | Planificar fin de semana completo |
| `/api/ai/gemini/feedback` | POST | Enviar feedback sobre eventos |
| `/api/ai/gemini/profile/{user_id}` | GET | Ver perfil de personalidad aprendido |
| `/api/ai/trending-now` | GET | Eventos trending con IA |

## 🛠️ Modo Fallback

Si no hay API Key de Gemini configurada, el sistema usa lógica inteligente local:
- Detección de keywords para mood
- Recomendaciones basadas en categorías
- Respuestas pre-configuradas pero contextuales

## 🚦 Testing sin API Key

El sistema funciona sin Gemini API Key usando fallback inteligente:

```bash
# Funciona incluso sin API Key
curl -X POST http://172.29.228.80:8001/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "busco algo para hacer con amigos"}'
```

## 📈 Métricas de Éxito

- **Match Score**: 0-100% de qué tan bien matchea con el usuario
- **Personality Profile**: Se construye con el tiempo
- **Decision Style**: Detecta si sos indeciso o decisivo
- **Preference Learning**: Mejora con cada interacción

---

**🎉 El sistema está listo! Solo agregá tu GEMINI_API_KEY en .env para activar la IA completa**