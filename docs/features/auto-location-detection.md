<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-01-13 14:30
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-01-13 14:30: Implementación inicial de detección automática multi-ciudad
📋 TAGS: #location #auto-detection #multi-city #geolocation #feature
-->

# Detección Automática de Ubicación Multi-Ciudad

## 📋 Resumen

Implementación de detección automática de ubicación al iniciar la aplicación, con búsqueda de eventos en múltiples ciudades cercanas simultáneamente.

## 🎯 Funcionalidad

### Al cargar HomePageModern.tsx:

1. **Detección Automática de Ubicación**
   - Intenta usar geolocalización del navegador (GPS)
   - Fallback a detección por IP (usando ipapi.co)
   - Reverse geocoding con Nominatim para obtener nombre de ciudad

2. **Enriquecimiento de Ubicación**
   - Llama a `/api/location/enrichment` para obtener ciudades cercanas
   - Obtiene hasta 5 ciudades (la principal + 4 cercanas)

3. **Búsqueda Multi-Ciudad**
   - Busca eventos en cada ciudad de forma secuencial
   - Combina todos los eventos encontrados
   - Muestra progreso visual durante la búsqueda

## 🔧 Archivos Modificados

### 1. **frontend/src/stores/EventsStore.tsx**

#### Nuevo método: `searchMultipleNearbyCities`

```typescript
searchMultipleNearbyCities: async (location: Location) => {
  // 1. Enriquecer ubicación para obtener ciudades cercanas
  const enrichResponse = await fetch(
    `${config.API_BASE_URL}/api/location/enrichment?location=${encodeURIComponent(location.name)}`
  )

  // 2. Buscar eventos en la ciudad principal + hasta 4 ciudades cercanas
  const citiesToSearch = [
    location.name,
    ...locationInfo.nearby_cities.slice(0, 4)
  ]

  // 3. Buscar eventos en cada ciudad
  for (const cityName of citiesToSearch) {
    const cityResponse = await fetch(
      `${config.API_BASE_URL}/api/events?location=${encodeURIComponent(cityName)}&limit=20`
    )
    // Agregar eventos con metadata de ciudad
  }

  // 4. Actualizar estado con todos los eventos combinados
  set({
    events: allEvents,
    nearbyCities: locationInfo.nearby_cities
  })
}
```

**Características:**
- ✅ Usa endpoints existentes (`/api/location/enrichment` y `/api/events`)
- ✅ Muestra progreso en tiempo real
- ✅ Fallback a búsqueda simple si falla
- ✅ Agrega metadata `source_city` a cada evento

### 2. **frontend/src/pages/HomePageModern.tsx**

#### Cambios en el useEffect de auto-detección:

```typescript
// ANTES: Solo streaming en ciudad detectada
await startStreamingSearch(detectedLocation)

// AHORA: Búsqueda multi-ciudad
await searchMultipleNearbyCities(detectedLocation)
```

#### Nuevo estado para loading:

```typescript
const [isDetectingLocation, setIsDetectingLocation] = useState(false)
```

#### Componente de loading visual:

```tsx
{isDetectingLocation && (
  <div className="mb-6 bg-gradient-to-r from-purple-500/20 ...">
    <div className="flex items-center justify-center gap-3">
      <div className="w-6 h-6 border-4 ... animate-spin"></div>
      <div className="text-white">
        <p className="font-semibold">Detectando tu ubicación...</p>
        <p className="text-sm">{streamingMessage || 'Buscando ciudades cercanas'}</p>
      </div>
    </div>
    {/* Barra de progreso */}
  </div>
)}
```

#### Indicador de ciudades buscadas:

```tsx
{nearbyCities.length > 0 && events.length > 0 && (
  <div className="bg-white/5 ...">
    <span>📍 Buscando en:</span>
    <div className="flex gap-2">
      <span>{currentLocation?.name}</span>
      {nearbyCities.slice(0, 4).map(city => (
        <span>• {city}</span>
      ))}
    </div>
  </div>
)}
```

## 🌊 Flujo de Ejecución

```
Usuario abre la app
      ↓
¿Ya hay eventos en memoria?
  ├─ Sí → Usar cache (navegación back)
  └─ No → Continuar
      ↓
Intentar GPS del navegador
  ├─ Éxito → Reverse geocoding (Nominatim)
  │           ├─ Corrección Villa Gesell (coordenadas especiales)
  │           └─ Location detectada
  └─ Fallo → Detección por IP (ipapi.co)
      ↓
setLocation(detectedLocation)
      ↓
searchMultipleNearbyCities(detectedLocation)
      ↓
Llamar /api/location/enrichment
      ↓
¿Hay ciudades cercanas?
  ├─ No → startStreamingSearch(location)
  └─ Sí → Continuar
      ↓
Buscar eventos en cada ciudad (1-5 ciudades)
  │   ├─ Ciudad 1: /api/events?location=...
  │   ├─ Ciudad 2: /api/events?location=...
  │   ├─ Ciudad 3: /api/events?location=...
  │   └─ ...
  └─ Combinar todos los eventos
      ↓
Actualizar UI con eventos + indicador de ciudades
      ↓
setLocationDetected(true)
setIsDetectingLocation(false)
```

## 📊 Ventajas

1. **Más eventos disponibles**: Busca en múltiples ciudades automáticamente
2. **Mejor experiencia inicial**: Usuario ve eventos inmediatamente
3. **Transparencia**: Muestra claramente en qué ciudades se buscó
4. **Progreso visible**: Loading states y barras de progreso
5. **Fallback robusto**: Si falla GPS, usa IP; si fallan ciudades cercanas, busca solo en la principal

## ⚙️ Configuración

### Límites por ciudad:
- Máximo **20 eventos por ciudad** (configurable en el código)
- Hasta **5 ciudades totales** (1 principal + 4 cercanas)
- Total máximo teórico: **100 eventos** en la carga inicial

### Timeouts y tiempos:
- GPS: 10 segundos de timeout
- Cache de geolocalización: 5 minutos
- Debounce de búsquedas: 500ms

## 🔄 Comportamiento de Cache

```typescript
// 🔒 NO ejecutar si ya hay eventos cargados (volviendo desde detalle)
if (events.length > 0) {
  console.log('✅ Eventos ya cargados en memoria - usando cache')
  setLocationDetected(true)
  hasAutoLoaded.current = true
  return
}
```

## 🛡️ Protecciones Implementadas

1. **Prevención de doble ejecución**: `hasAutoLoaded.current` ref
2. **Detección de navegación back**: Chequea `events.length > 0`
3. **Prevención de búsquedas en ciudades específicas**: No ejecuta si `selectedCity` está activo
4. **Debounce**: Evita llamadas repetidas < 500ms
5. **Locks robustos**: `isStreaming` lock en el store

## 🎨 UI/UX

### Estados visuales:

1. **Detectando ubicación** (inicial)
   ```
   [Spinner] Detectando tu ubicación...
             Buscando ciudades cercanas
   [Barra de progreso: 0-20%]
   ```

2. **Buscando en ciudades** (progreso)
   ```
   [Spinner] Buscando en Barcelona... (1/5)
   [Barra de progreso: 20-90%]
   ```

3. **Completado** (final)
   ```
   [Stats] 87 eventos encontrados
   [Indicador] 📍 Buscando en: Barcelona • Badalona • Hospitalet • Sabadell
   ```

## 🧪 Testing

### Casos de prueba:

1. ✅ GPS habilitado → Detecta ubicación precisa
2. ✅ GPS deshabilitado → Fallback a IP
3. ✅ Sin ciudades cercanas → Busca solo en ciudad principal
4. ✅ Navegación back → Usa cache de eventos
5. ✅ Error en enrichment → Fallback a streaming simple

## 📝 Notas Importantes

- **NO modifica endpoints existentes**: Solo usa `/api/location/enrichment` y `/api/events`
- **Compatible con búsquedas manuales**: No interfiere con el flujo existente
- **Respeta lógica de ciudades específicas**: No ejecuta si usuario está viendo eventos de una ciudad concreta
- **Metadata preservada**: Cada evento mantiene su `source_city` para futura referencia

## 🔮 Mejoras Futuras

1. Permitir al usuario seleccionar cuántas ciudades cercanas incluir
2. Filtrado por ciudad en la UI (botones para ver solo eventos de una ciudad)
3. Caché de resultados de enriquecimiento de ubicación
4. Búsqueda paralela en lugar de secuencial (Promise.all)
5. Mostrar mapa con las ciudades donde se buscó

## 🔗 Referencias

- Endpoint de enriquecimiento: `backend/main.py:1163` (@app.get("/api/location/enrichment"))
- Servicio Gemini Factory: `backend/services/gemini_factory.py`
- Store de eventos: `frontend/src/stores/EventsStore.tsx`
- Página principal: `frontend/src/pages/HomePageModern.tsx`
