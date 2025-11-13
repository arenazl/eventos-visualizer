import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { create } from 'zustand'
import { config } from '../config'
import { API_BASE_URL } from '../config/api'

interface Event {
  title: string
  description?: string
  start_datetime?: string | null
  end_datetime?: string | null
  venue_name: string
  venue_address?: string
  latitude?: number
  longitude?: number
  category: string
  price?: number | null
  currency?: string
  is_free?: boolean
  source?: string
  image_url?: string | null
  status?: string
}

interface Location {
  name: string
  coordinates?: { lat: number; lng: number }
  country?: string
  detected: 'gps' | 'manual' | 'prompt' | 'fallback'
}

interface AIRecommendation {
  analysis: string
  recommendations: any[]
  alternative_suggestions: string[]
  follow_up_questions: string[]
  personalized_message: string
}

interface SourceTiming {
  source: string
  startTime: number
  endTime?: number
  totalTime?: number
  eventTimes: number[] // Tiempo de cada batch de eventos
  firstEventTime?: number // Tiempo del primer evento
}

interface ScraperInfo {
  name: string
  status: 'success' | 'failed' | 'timeout'
  events_count: number
  response_time: string
  message: string
}

interface ScrapersExecution {
  scrapers_called: string[]
  total_scrapers: number
  scrapers_info: ScraperInfo[]
  summary: string
}

interface EventsState {
  events: Event[]
  loading: boolean
  error: string | null
  favoriteEvents: string[]
  currentLocation: Location | null
  aiRecommendations: AIRecommendation | null
  lastQuery: string
  
  // WebSocket Streaming State
  isStreaming: boolean
  streamingProgress: number
  streamingMessage: string
  streamingSource: string
  
  // Performance Metrics
  searchStartTime: number
  sourceTiming: SourceTiming[]
  performanceStats: {
    fastestSource?: string
    fastestTime?: number
    slowestSource?: string
    slowestTime?: number
    firstEventSource?: string
    firstEventTime?: number
  }
  
  // ✨ NUEVA INFO DE SCRAPERS
  scrapersExecution: ScrapersExecution | null

  // 🔌 SSE CONNECTION CLEANUP
  sseCleanup: (() => void) | null

  // 🎭 CALLBACK PARA ASISTENTES
  onNoEventsCallback?: (cityName: string, searchingNearby: boolean) => void
  setOnNoEventsCallback: (callback: (cityName: string, searchingNearby: boolean) => void) => void

  // AI-First Methods
  aiSearch: (query: string, location?: Location) => Promise<void>
  aiInitialSearch: (location: Location) => Promise<void>  // New function for initial page load
  // DISABLED: getSmartRecommendations removed
  // getSmartRecommendations: (query: string, foundEvents: Event[], detectedLocation?: string) => Promise<void>
  analyzeUserIntent: (query: string) => Promise<any>

  // WebSocket Streaming Methods
  startStreamingSearch: (location?: Location) => Promise<void>
  stopStreaming: () => void

  // 📍 EVENTOS CERCANOS Y PROVINCIA (Nuevo sistema multi-ciudad)
  fetchLocationEnrichment: () => Promise<void>
  searchSpecificCity: (cityName: string, isOriginal?: boolean) => Promise<void>
  fetchNearbyEvents: () => Promise<void>
  fetchProvinceEvents: () => Promise<void>
  autoLoadExpandedEvents: () => Promise<void>
  searchMultipleNearbyCities: (location: Location) => Promise<void>
  nearbyEventsAvailable: boolean
  nearbyCities: string[]  // Array de 3 ciudades cercanas
  nearbyCity: string | null  // Mantener por compatibilidad
  loadingNearby: boolean
  provinceEventsAvailable: boolean
  provinceName: string | null
  loadingProvince: boolean
  loadingEnrichment: boolean
  selectedCity: string | null  // Ciudad actualmente seleccionada
  originalSearchLocation: string | null  // Ubicación original buscada
  showReturnButton: boolean  // Mostrar botón de "volver"
  loadingCityName: string | null  // Nombre de la ciudad que está cargando eventos

  // 🏙️ BÚSQUEDA EXPANDIDA A CIUDAD PRINCIPAL
  parentCityDetected: string | null  // Ciudad principal detectada (ej: "Buenos Aires" para "Merlo")
  searchLocationQuery: string | null  // Ubicación original del query (ej: "Merlo")
  expandedSearch: boolean  // Si la búsqueda fue expandida automáticamente

  // Legacy methods (fallback)
  fetchEvents: (location?: Location) => Promise<void>
  toggleFavorite: (eventId: string) => void
  searchEvents: (query: string, location?: Location) => Promise<void>
  smartSearch: (query: string, location?: Location) => Promise<void>
  filterByCategory: (category: string) => void
  setLocation: (location: Location) => void
}

const useEventsStore = create<EventsState>((set, get) => ({
  events: [],
  loading: false,

  // 📍 Estado de eventos cercanos y provincia
  nearbyEventsAvailable: false,
  nearbyCities: [],
  nearbyCity: null,
  loadingNearby: false,
  provinceEventsAvailable: false,
  provinceName: null,
  loadingProvince: false,
  loadingEnrichment: false,
  selectedCity: null,
  originalSearchLocation: null,
  showReturnButton: false,
  loadingCityName: null,

  // 🏙️ Búsqueda expandida a ciudad principal
  parentCityDetected: null,
  searchLocationQuery: null,
  expandedSearch: false,
  error: null,
  favoriteEvents: JSON.parse(localStorage.getItem('favoriteEvents') || '[]'),
  currentLocation: null,
  aiRecommendations: null,
  lastQuery: '',
  
  // WebSocket Streaming State
  isStreaming: false,
  streamingProgress: 0,
  streamingMessage: '',
  streamingSource: '',
  
  // Performance Metrics
  searchStartTime: 0,
  sourceTiming: [],
  performanceStats: {},
  
  // ✨ SCRAPERS EXECUTION INFO
  scrapersExecution: null,

  // 🔌 SSE CONNECTION CLEANUP
  sseCleanup: null as (() => void) | null,

  // 🎭 CALLBACK PARA ASISTENTES
  onNoEventsCallback: undefined,
  setOnNoEventsCallback: (callback) => {
    set({ onNoEventsCallback: callback })
  },

  setLocation: (location: Location) => {
    set({ currentLocation: location })
  },

  // 🧠 AI-FIRST SEARCH - La nueva forma principal de buscar
  aiSearch: async (query: string, location?: Location) => {
    set({ loading: true, error: null, lastQuery: query })

    try {
      const { currentLocation } = get()
      const searchLocation = location || currentLocation

      // 1. PASO 1: Analizar intención del usuario
      const intentResponse = await fetch(`${config.API_BASE_URL}/api/ai/analyze-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          context: {
            location: searchLocation?.name,
            time: new Date().toISOString()
          }
        })
      })

      const intent = intentResponse.ok ? await intentResponse.json() : null

      // 🧠 USAR UBICACIÓN DETECTADA POR IA SI ESTÁ DISPONIBLE
      const detectedCity = intent?.intent?.detected_city || intent?.intent?.query
      const detectedProvince = intent?.intent?.detected_province
      const detectedCountry = intent?.intent?.detected_country || 'Argentina'

      // Build full location string: "City, Province, Country"
      const locationParts = [detectedCity, detectedProvince, detectedCountry].filter(Boolean)
      const finalLocation = locationParts.length > 0 ? locationParts.join(', ') : searchLocation?.name

      // 2. PASO 2: Búsqueda inteligente con contexto
      const searchResponse = await fetch(`${config.API_BASE_URL}/api/smart/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          location: finalLocation,  // ✅ Ahora usa ubicación IA o fallback
          user_context: {
            location: finalLocation,
            coordinates: searchLocation?.coordinates,
            intent_analysis: intent
          }
        })
      })

      if (!searchResponse.ok) throw new Error('Error en búsqueda AI')

      const searchData = await searchResponse.json()
      const foundEvents = searchData.recommended_events || []

      // 3. PASO 3: Generar recomendaciones inteligentes
      // DISABLED: getSmartRecommendations removed - endpoint no longer exists
      // await get().getSmartRecommendations(query, foundEvents, finalLocation)

      set({ 
        events: foundEvents, 
        loading: false,
        // ✨ CAPTURAR SCRAPERS EXECUTION DATA
        scrapersExecution: searchData.scrapers_execution || null
      })

    } catch (error) {
      console.warn('AI search failed, falling back to traditional search:', error)
      // Fallback a búsqueda tradicional
      await get().smartSearch(query, location)
    }
  },

  // 🌍 AI INITIAL SEARCH - Para carga inicial con geolocalización
  aiInitialSearch: async (location: Location) => {
    set({ loading: true, error: null, lastQuery: `Eventos en ${location.name}` })

    try {
      // Use location name as the query for initial search
      const initialQuery = location.name
      
      // SOLO UN LLAMADO: Analizar intención de la ubicación detectada con Gemini
      const intentResponse = await fetch(`${config.API_BASE_URL}/api/ai/analyze-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: initialQuery,
          current_location: location.name
        })
      })

      if (!intentResponse.ok) {
        throw new Error('Error analizando ubicación')
      }

      const data = await intentResponse.json()
      
      // Actualizar la ubicación con los datos correctos de Gemini
      if (data.success && data.intent) {
        const detectedLocation = data.intent.geographic_hierarchy?.full_location || location.name
        const newLocation: Location = {
          name: detectedLocation,
          coordinates: location.coordinates,
          country: data.intent.detected_country,
          detected: 'prompt'
        }
        
        set({ 
          currentLocation: newLocation,
          loading: false,
          events: [], // Por ahora no cargamos eventos, solo analizamos ubicación
          error: null
        })
        
        console.log('📍 Ubicación detectada por Gemini:', detectedLocation)
      } else {
        // Si algo falla, mantener la ubicación original
        set({ 
          currentLocation: location,
          loading: false,
          error: null
        })
      }

    } catch (error) {
      console.error('Error al analizar ubicación con Gemini:', error)
      set({ 
        loading: false,
        error: 'Error al detectar ubicación',
        currentLocation: location
      })
    }
  },

  // DISABLED: getSmartRecommendations - endpoint removed, use client-side scoring instead
  // 🎯 Recomendaciones inteligentes (complementa cualquier búsqueda)
  // getSmartRecommendations: async (query: string, foundEvents: Event[], detectedLocation?: string) => {
  //   // Moved to client-side scoring logic
  // },

  // 🧠 Análisis de intención
  analyzeUserIntent: async (query: string) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/ai/analyze-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          context: { location: get().currentLocation?.name }
        })
      })

      return response.ok ? await response.json() : null
    } catch (error) {
      console.warn('Intent analysis failed:', error)
      return null
    }
  },

  fetchEvents: async (location?: Location) => {
    set({ loading: true, error: null, events: [] })

    const searchLocation = location || get().currentLocation
    const locationString = searchLocation?.name || 'Buenos Aires'

    try {
      console.log('🔍 Fetching events for:', locationString)

      const response = await fetch(`${config.API_BASE_URL}/api/events?location=${encodeURIComponent(locationString)}&limit=30`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('✅ Events received:', data)

      if (data.status === 'success' && data.events) {
        set({ events: data.events, loading: false, error: null })
      } else {
        set({ events: [], loading: false, error: 'No events found' })
      }
    } catch (error: any) {
      console.error('❌ Error fetching events:', error)
      set({ error: error.message || 'Failed to fetch events', loading: false, events: [] })
    }
  },

  toggleFavorite: (eventId: string) => {
    const { favoriteEvents } = get()
    const newFavorites = favoriteEvents.includes(eventId)
      ? favoriteEvents.filter(id => id !== eventId)
      : [...favoriteEvents, eventId]

    localStorage.setItem('favoriteEvents', JSON.stringify(newFavorites))
    set({ favoriteEvents: newFavorites })
  },

  searchEvents: async (query: string, location?: Location) => {
    set({ loading: true, error: null, events: [] })
    
    const { currentLocation } = get()
    const searchLocation = location || currentLocation
    const locationString = searchLocation?.name || "Buenos Aires"
    
    // First, detect intent using API V1
    try {
      const intentResponse = await fetch(`${config.API_BASE_URL}/api/ai/analyze-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: `${query} en ${locationString}` })
      })
      
      if (intentResponse.ok) {
        const intent = await intentResponse.json()
        // Use detected location if available
        const detectedLocation = [
          intent.location?.city,
          intent.location?.state,
          intent.location?.country
        ].filter(Boolean).join(', ') || locationString

        // SSE streaming disabled - using fallback API instead
        // Use regular API search
        let apiUrl = `${config.API_BASE_URL}/api/events/search?q=${encodeURIComponent(query)}`
        apiUrl += `&location=${encodeURIComponent(detectedLocation)}`

        const response = await fetch(apiUrl)
        if (!response.ok) throw new Error('Error en la búsqueda')

        const data = await response.json()
        set({ events: data.events || data || [], loading: false })

      } else {
        // Fallback to old API if V1 fails
        let apiUrl = `${config.API_BASE_URL}/api/events/search?q=${encodeURIComponent(query)}`
        if (searchLocation) {
          apiUrl += `&location=${encodeURIComponent(locationString)}`
        }

        const response = await fetch(apiUrl)
        if (!response.ok) throw new Error('Error en la búsqueda')

        const data = await response.json()
        set({ events: data.events || data || [], loading: false })
      }
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  smartSearch: async (query: string, location?: Location) => {
    set({ loading: true, error: null })
    try {
      const { currentLocation } = get()
      const searchLocation = location || currentLocation

      // 🧠 PASO 1: Analizar intención para detectar ubicación
      const intentResponse = await fetch(`${config.API_BASE_URL}/api/ai/analyze-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          current_location: searchLocation?.name
        })
      })

      const intent = intentResponse.ok ? await intentResponse.json() : null

      // 🧠 USAR UBICACIÓN DETECTADA POR IA SI ESTÁ DISPONIBLE
      const finalLocation = intent?.user_context?.location || searchLocation?.name

      // Usar Gemini Smart Search
      const response = await fetch(`${config.API_BASE_URL}/api/smart/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          location: finalLocation,  // ✅ Ahora usa ubicación IA o fallback
          user_context: {
            location: finalLocation,
            coordinates: searchLocation?.coordinates,
            intent_analysis: intent
          }
        })
      })

      if (!response.ok) throw new Error('Error en búsqueda inteligente')

      const data = await response.json()
      set({ 
        events: data.recommended_events || [], 
        loading: false,
        // ✨ CAPTURAR SCRAPERS EXECUTION DATA  
        scrapersExecution: data.scrapers_execution || null
      })
    } catch (error) {
      // Fallback to regular search if Gemini fails
      console.warn('Smart search failed, falling back to regular search:', error)
      await get().searchEvents(query, location)
    }
  },

  filterByCategory: (category: string) => {
    const { events } = get()
    if (category === 'all') {
      get().fetchEvents()
    } else {
      const filtered = events.filter(event => event.category === category)
      set({ events: filtered })
    }
  },

  // 🔥 WEBSOCKET STREAMING - Nueva funcionalidad principal
  startStreamingSearch: async (location?: Location) => {
    const state = get()
    const { currentLocation, isStreaming } = state

    console.log('🎬 [STREAM] startStreamingSearch llamado con location:', location?.name || 'undefined')
    console.log('🎬 [STREAM] currentLocation en store:', currentLocation?.name || 'null')
    console.log('🎬 [STREAM] isStreaming:', isStreaming)

    // 🔒 LOCK ROBUSTO: Prevenir llamadas duplicadas
    if (isStreaming) {
      console.warn('⏸️ [LOCK] Búsqueda en progreso - ignorando llamada duplicada')
      return
    }

    const searchLocation = location || currentLocation

    console.log('🎬 [STREAM] searchLocation final:', searchLocation?.name || 'undefined')

    if (!searchLocation) {
      console.error('❌ [STREAM] No hay ubicación para buscar - abortando')
      return
    }

    // 🔒 DEBOUNCE: Prevenir llamadas rápidas sucesivas (< 500ms)
    const now = Date.now()
    const lastSearch = (window as any).__lastSearchTime || 0
    const timeSinceLastSearch = now - lastSearch
    if (timeSinceLastSearch < 500) {
      console.warn(`⏸️ [DEBOUNCE] Ignorando búsqueda repetida (${timeSinceLastSearch}ms < 500ms)`)
      return
    }
    (window as any).__lastSearchTime = now

    console.log('✅ [STREAM] Locks pasados - iniciando streaming...')

    const startTime = Date.now()
    set({
      isStreaming: true,
      events: [],
      loading: true,
      error: null,
      streamingProgress: 0,
      streamingMessage: 'Conectando...',
      streamingSource: '',
      searchStartTime: startTime,
      sourceTiming: [],
      performanceStats: {},
      nearbyCities: [],  // Limpiar ciudades cercanas al iniciar nueva búsqueda

      // 🏙️ Limpiar metadata de búsqueda expandida
      parentCityDetected: null,
      searchLocationQuery: null,
      expandedSearch: false
    })

    // DISABLED - No WebSocket, use SSE search instead
    console.log('WebSocket disabled - using SSE search instead')

    // Inicializar estructura de scrapers
    const scrapersData: any = {
      scrapers_called: [],
      total_scrapers: 0,
      scrapers_info: [],
      summary: ''
    }

    // Call the SSE search method instead
    const sseService = (await import('../services/sse-events')).sseEventsService

    // Construir ubicación completa para el backend
    const fullLocationString = searchLocation?.name
      ? `${searchLocation.name}${searchLocation.country ? ', ' + searchLocation.country : ''}`
      : 'Villa Gesell'

    console.log('🔍 SSE Streaming con ubicación:', fullLocationString)

    // 🛑 CERRAR CONEXIÓN ANTERIOR SI EXISTE
    const { sseCleanup: previousCleanup } = get()
    if (previousCleanup) {
      console.log('🔌 Cerrando conexión SSE anterior...')
      previousCleanup()
    }

    const cleanup = sseService.searchEventsStream(
      fullLocationString,
      (event) => {
        // Handle SSE events
        console.log('SSE Event:', event)

        const { events, scrapersExecution } = get()

        // Eventos de un scraper
        if (event.type === 'events' && event.events && event.scraper) {
          // Agregar eventos
          set({ events: [...events, ...event.events] })

          // 🏙️ Capturar metadata de ciudad principal si existe
          if (event.parent_city && event.original_location && event.expanded_search) {
            set({
              parentCityDetected: event.parent_city,
              searchLocationQuery: event.original_location,
              expandedSearch: event.expanded_search
            })
            console.log(`📍 Búsqueda expandida detectada: ${event.original_location} → ${event.parent_city}`)
          }

          // Mensaje personalizado para ciudades cercanas
          let scraperMessage = `${event.count || event.events.length} eventos obtenidos`
          if (event.scraper === 'nearby_cities' && event.message) {
            scraperMessage = event.message
          }

          // Agregar info del scraper
          const scraperInfo = {
            name: event.scraper === 'nearby_cities' ? 'Zonas Cercanas' : event.scraper.charAt(0).toUpperCase() + event.scraper.slice(1),
            status: 'success',
            events_count: event.count || event.events.length,
            response_time: event.execution_time || '0.0s',
            message: scraperMessage
          }

          scrapersData.scrapers_called.push(event.scraper)
          scrapersData.scrapers_info.push(scraperInfo)
          scrapersData.total_scrapers = scrapersData.scrapers_called.length

          set({ scrapersExecution: { ...scrapersData } })
        }

        // Scraper sin eventos
        if (event.type === 'no_events' && event.scraper) {
          // 🏙️ Capturar metadata de ciudad principal incluso sin eventos
          if (event.parent_city && event.original_location && event.expanded_search) {
            set({
              parentCityDetected: event.parent_city,
              searchLocationQuery: event.original_location,
              expandedSearch: event.expanded_search
            })
            console.log(`📍 Búsqueda expandida sin eventos: ${event.original_location} → ${event.parent_city}`)
          }

          const scraperInfo = {
            name: event.scraper.charAt(0).toUpperCase() + event.scraper.slice(1),
            status: 'success',
            events_count: 0,
            response_time: event.execution_time || '0.0s',
            message: 'Sin eventos encontrados'
          }

          scrapersData.scrapers_called.push(event.scraper)
          scrapersData.scrapers_info.push(scraperInfo)
          scrapersData.total_scrapers = scrapersData.scrapers_called.length

          set({ scrapersExecution: { ...scrapersData } })
        }

        // Scraper con error
        if (event.type === 'scraper_error' && event.scraper) {
          const scraperInfo = {
            name: event.scraper.charAt(0).toUpperCase() + event.scraper.slice(1),
            status: 'failed',
            events_count: 0,
            response_time: event.execution_time || '0.0s',
            message: event.error || 'Error desconocido'
          }

          scrapersData.scrapers_called.push(event.scraper)
          scrapersData.scrapers_info.push(scraperInfo)
          scrapersData.total_scrapers = scrapersData.scrapers_called.length

          set({ scrapersExecution: { ...scrapersData } })
        }

        // Mensaje informativo (buscando en ciudades cercanas, etc.)
        if (event.type === 'info' && event.message) {
          console.log('ℹ️ Info:', event.message)
          // NO disparar búsqueda automática en ciudades cercanas
          // El usuario verá el mensaje pero no se hará otra búsqueda
        }

        // Búsqueda completa
        if (event.type === 'complete') {
          const totalEvents = get().events.length
          scrapersData.summary = `${scrapersData.scrapers_info.filter((s: any) => s.events_count > 0).length}/${scrapersData.total_scrapers} scrapers exitosos - ${totalEvents} eventos totales`

          console.log(`✅ [STREAM] Streaming completado - ${totalEvents} eventos encontrados`)
          console.log('🔓 [STREAM] Liberando lock (isStreaming = false)')

          set({
            isStreaming: false,
            loading: false,
            scrapersExecution: { ...scrapersData }
          })
        }

        // Enriquecimiento de ubicación (ciudades cercanas + provincia)
        if (event.type === 'enrichment') {
          console.log('🌍 Evento enrichment recibido:', event)
          console.log('🌍 nearby_cities:', event.nearby_cities)
          console.log('🌍 nearby_cities length:', event.nearby_cities?.length)

          if (event.nearby_cities) {
            console.log('✅ Actualizando nearbyCities en store:', event.nearby_cities)
            set({
              nearbyCities: event.nearby_cities,
              provinceName: event.state || null,
              loadingEnrichment: false
            })
          } else {
            console.warn('⚠️ Evento enrichment sin nearby_cities')
          }
        }
      }
    )

    // ✅ GUARDAR CLEANUP EN STATE PARA CERRAR DESPUÉS
    set({ sseCleanup: cleanup })
    console.log('✅ Nueva conexión SSE creada y cleanup guardado')
    
    /* DISABLED WEBSOCKET CODE
    try {
      // Convertir HTTP(S) URL a WS(S) URL
      const wsUrl = API_BASE_URL.replace(/^https?/, (match) => match === 'https' ? 'wss' : 'ws')
      const ws = new WebSocket(`${wsUrl}/ws/search-events`)
      
      ws.onopen = () => {
        console.log('🔥 WebSocket conectado para búsqueda streaming')
        // Iniciar búsqueda automáticamente
        ws.send(JSON.stringify({
          action: 'search',
          location: searchLocation?.name || 'Buenos Aires'
        }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📨 Streaming message:', data.type)
          
          switch (data.type) {
            case 'connection':
              set({ streamingMessage: data.message })
              break
              
            case 'search_started':
              // Mensaje como en Linux: "🚀 Iniciando búsqueda en Buenos Aires..."
              const startMessage = `🚀 ${data.message}`
              set({ 
                streamingMessage: startMessage,
                streamingProgress: 0
              })
              break
              
            case 'source_started':
              const source = data.source || ''
              const emoji = source === 'eventbrite' ? '🎫' : source === 'facebook' ? '🔥' : source === 'instagram' ? '📸' : source === 'argentina_venues' ? '🏛️' : '🔍'
              // Mensaje como en Linux: "🎫 Buscando en Eventbrite Argentina... (Progreso: 5%)"
              const sourceMessage = `${emoji} ${data.message} (Progreso: ${data.progress || 0}%)`
              
              // Iniciar timing para esta fuente
              const currentTime = Date.now()
              const { sourceTiming } = get()
              const newTiming: SourceTiming = {
                source: source,
                startTime: currentTime,
                eventTimes: []
              }
              
              set({ 
                streamingSource: source,
                streamingMessage: sourceMessage,
                streamingProgress: data.progress || 0,
                sourceTiming: [...sourceTiming, newTiming]
              })
              break
              
            case 'events_batch':
              if (data.events) {
                const { events, sourceTiming, searchStartTime, performanceStats } = get()
                const newEvents = [...events, ...data.events]
                const totalEvents = newEvents.length
                const source = data.source || 'unknown'
                const progress = data.progress || 0
                const currentTime = Date.now()
                
                // Mensaje igual al de Linux: "📦 3 eventos de eventbrite - Total: 6 (Progreso: 5.8%)"
                const linuxMessage = `📦 ${data.events.length} eventos de ${source} - Total: ${totalEvents} (Progreso: ${progress.toFixed(1)}%)`
                
                // Actualizar timing para esta fuente
                const updatedTiming = sourceTiming.map(timing => {
                  if (timing.source === source) {
                    const eventTime = currentTime - timing.startTime
                    const firstEventTime = timing.eventTimes.length === 0 ? eventTime : timing.firstEventTime
                    
                    return {
                      ...timing,
                      eventTimes: [...timing.eventTimes, eventTime],
                      firstEventTime
                    }
                  }
                  return timing
                })
                
                // Actualizar stats de performance
                const newStats = { ...performanceStats }
                if (events.length === 0) { // Primer evento de cualquier fuente
                  const timeFromStart = currentTime - searchStartTime
                  newStats.firstEventSource = source
                  newStats.firstEventTime = timeFromStart
                }
                
                set({ 
                  events: newEvents,
                  streamingProgress: progress,
                  streamingMessage: linuxMessage,
                  streamingSource: source,
                  sourceTiming: updatedTiming,
                  performanceStats: newStats
                })
              }
              break
              
            case 'search_completed':
              const { sourceTiming: finalTiming, performanceStats: finalStats } = get()
              const endTime = Date.now()
              
              // Completar timing de todas las fuentes
              const completedTiming = finalTiming.map(timing => ({
                ...timing,
                endTime,
                totalTime: endTime - timing.startTime
              }))
              
              // Calcular estadísticas finales
              const newStats = { ...finalStats }
              if (completedTiming.length > 0) {
                // Fuente más rápida (primera en entregar eventos)
                const sourcesWithEvents = completedTiming.filter(t => t.eventTimes.length > 0)
                if (sourcesWithEvents.length > 0) {
                  const fastestSource = sourcesWithEvents.reduce((prev, curr) => 
                    (curr.firstEventTime || 0) < (prev.firstEventTime || 0) ? curr : prev
                  )
                  newStats.fastestSource = fastestSource.source
                  newStats.fastestTime = fastestSource.firstEventTime
                  
                  // Fuente más lenta (última en entregar eventos)
                  const slowestSource = sourcesWithEvents.reduce((prev, curr) => 
                    (curr.totalTime || 0) > (prev.totalTime || 0) ? curr : prev
                  )
                  newStats.slowestSource = slowestSource.source
                  newStats.slowestTime = slowestSource.totalTime
                }
              }
              
              // Mensaje como en Linux: "🎉 Búsqueda completada - Total final: 36 eventos"
              const completedMessage = `🎉 ${data.message} - Total final: ${data.total_events || get().events.length} eventos`
              
              set({ 
                isStreaming: false,
                loading: false,
                streamingMessage: completedMessage,
                streamingProgress: 100,
                sourceTiming: completedTiming,
                performanceStats: newStats
              })
              ws.close()
              break
              
            case 'search_error':
              set({ 
                isStreaming: false,
                loading: false,
                error: data.message
              })
              ws.close()
              break
          }
        } catch (e) {
          console.error('Error parsing streaming message:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket cerrado')
        set({ isStreaming: false, loading: false })
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        set({ 
          isStreaming: false, 
          loading: false,
          error: 'Error de conexión WebSocket'
        })
      }

    } catch (error) {
      console.error('Error iniciando streaming search:', error)
      set({ 
        isStreaming: false, 
        loading: false,
        error: 'No se pudo conectar al servidor'
      })
    }
    */ // END OF DISABLED WEBSOCKET CODE
  },

  stopStreaming: () => {
    // 🛑 CERRAR CONEXIÓN SSE SI EXISTE
    const { sseCleanup } = get()
    if (sseCleanup) {
      console.log('🔌 Cerrando conexión SSE desde stopStreaming...')
      sseCleanup()
    }

    set({
      isStreaming: false,
      loading: false,
      streamingProgress: 0,
      streamingMessage: '',
      streamingSource: '',
      sseCleanup: null
    })
  },

  // 🌍 ENRIQUECIMIENTO DE UBICACIÓN - Obtener ciudades cercanas y provincia
  fetchLocationEnrichment: async () => {
    const { currentLocation } = get()

    if (!currentLocation) {
      console.warn('No hay ubicación actual para enriquecer')
      return
    }

    set({ loadingEnrichment: true })

    try {
      // Construir ubicación completa con país si está disponible
      const fullLocation = currentLocation.country
        ? `${currentLocation.name}, ${currentLocation.country}`
        : currentLocation.name

      console.log(`🌍 Enriqueciendo ubicación: "${fullLocation}"`)

      const response = await fetch(
        `${config.API_BASE_URL}/api/location/enrichment?location=${encodeURIComponent(fullLocation)}`
      )

      if (!response.ok) {
        throw new Error('Error al obtener enriquecimiento de ubicación')
      }

      const data = await response.json()

      if (data.success && data.location_info) {
        const enrichment = data.location_info

        set({
          nearbyCities: enrichment.nearby_cities || [],
          provinceName: enrichment.state || null,
          originalSearchLocation: enrichment.city || currentLocation.name,
          loadingEnrichment: false
        })

        console.log(`🌍 Ubicación enriquecida:`, {
          city: enrichment.city,
          nearbyCities: enrichment.nearby_cities,
          province: enrichment.state
        })
      } else {
        set({ loadingEnrichment: false })
      }
    } catch (error) {
      console.error('Error fetching location enrichment:', error)
      set({ loadingEnrichment: false })
    }
  },

  // 🏙️ BUSCAR EN CIUDAD ESPECÍFICA - Buscar eventos en una ciudad cercana específica
  searchSpecificCity: async (cityName: string, isOriginal: boolean = false) => {
    const { currentLocation, originalSearchLocation } = get()

    if (!currentLocation) {
      console.warn('No hay ubicación actual')
      return
    }

    // Establecer loading y selected ANTES del fetch para mostrar spinner
    if (isOriginal) {
      set({
        loadingNearby: true,
        loadingCityName: cityName
      })
    } else {
      set({
        loadingNearby: true,
        loadingCityName: cityName,
        selectedCity: cityName,
        showReturnButton: true
      })
    }

    try {
      const originalLocation = originalSearchLocation || currentLocation.name

      const response = await fetch(
        `${config.API_BASE_URL}/api/events/city?city=${encodeURIComponent(cityName)}&original_location=${encodeURIComponent(originalLocation)}`
      )

      if (!response.ok) {
        throw new Error(`Error al buscar eventos en ${cityName}`)
      }

      const data = await response.json()

      console.log(`📦 Data recibida de ${cityName}:`, data)
      console.log(`📊 Eventos actuales ANTES de reemplazar:`, get().events.length)

      if (data.events && data.events.length > 0) {
        // SIEMPRE reemplazar eventos, no agregar
        if (isOriginal) {
          set({
            events: data.events,
            selectedCity: null,
            showReturnButton: false,
            loadingNearby: false,
            loadingCityName: null
          })
          console.log(`🔄 Volviendo a ${cityName}: ${data.events.length} eventos`)
        } else {
          console.log(`🏙️ Reemplazando con ${data.events.length} eventos desde ${cityName}`)
          set({
            events: data.events,
            loadingNearby: false,
            loadingCityName: null
          })
          console.log(`✅ Mostrando solo eventos de ${cityName}`)
        }
      } else {
        set({
          loadingNearby: false,
          loadingCityName: null
        })
        console.log(`ℹ️ No se encontraron eventos en ${cityName}`)
      }
    } catch (error) {
      console.error(`Error buscando eventos en ${cityName}:`, error)
      set({
        loadingNearby: false,
        loadingCityName: null
      })
    }
  },

  // 📍 EVENTOS CERCANOS - Buscar en ciudad grande cercana
  fetchNearbyEvents: async () => {
    const { currentLocation } = get()

    if (!currentLocation) {
      console.warn('No hay ubicación actual para buscar eventos cercanos')
      return
    }

    set({ loadingNearby: true })

    try {
      const response = await fetch(
        `${config.API_BASE_URL}/api/events/nearby?location=${encodeURIComponent(currentLocation.name)}`
      )

      if (!response.ok) {
        throw new Error('Error al buscar eventos cercanos')
      }

      const data = await response.json()

      // Nuevo formato: backend retorna nearby_cities array
      if (data.success && data.nearby_cities && data.nearby_cities.length > 0) {
        set({
          nearbyCities: data.nearby_cities,
          nearbyEventsAvailable: true,
          loadingNearby: false
        })

        console.log(`📍 ${data.nearby_cities.length} ciudades cercanas detectadas:`, data.nearby_cities)
      } else {
        // No hay ciudades cercanas
        set({
          nearbyCities: [],
          nearbyEventsAvailable: false,
          loadingNearby: false
        })

        console.log(`ℹ️ ${data.message || 'No hay ciudades cercanas disponibles'}`)
      }
    } catch (error) {
      console.error('Error fetching nearby events:', error)
      set({
        loadingNearby: false,
        nearbyEventsAvailable: false,
        nearbyCities: []
      })
    }
  },

  // 🌍 EVENTOS DE LA PROVINCIA - Buscar en toda la provincia/estado
  fetchProvinceEvents: async () => {
    const { currentLocation } = get()

    if (!currentLocation) {
      console.warn('No hay ubicación actual para buscar eventos de provincia')
      return
    }

    set({ loadingProvince: true })

    try {
      const response = await fetch(
        `${config.API_BASE_URL}/api/events/province?location=${encodeURIComponent(currentLocation.name)}`
      )

      if (!response.ok) {
        throw new Error('Error al buscar eventos de provincia')
      }

      const data = await response.json()

      if (data.province && data.events && data.events.length > 0) {
        // Agregar eventos de provincia a los existentes
        const currentEvents = get().events
        set({
          events: [...currentEvents, ...data.events],
          provinceEventsAvailable: true,
          provinceName: data.province,
          loadingProvince: false
        })

        console.log(`🌍 ${data.events.length} eventos agregados desde ${data.province}`)
      } else {
        // No hay eventos de provincia
        set({
          provinceEventsAvailable: false,
          loadingProvince: false
        })

        console.log(`ℹ️ ${data.message || 'No hay eventos de provincia disponibles'}`)
      }
    } catch (error) {
      console.error('Error fetching province events:', error)
      set({
        loadingProvince: false,
        provinceEventsAvailable: false
      })
    }
  },

  // 🎯 AUTO-LOAD - Cargar automáticamente eventos expandidos si hay pocos resultados
  autoLoadExpandedEvents: async () => {
    const { events } = get()

    // Solo auto-cargar si hay menos de 5 eventos
    if (events.length >= 5) {
      console.log('✅ Suficientes eventos locales, no auto-loading')
      return
    }

    console.log(`⚡ Auto-loading eventos expandidos (solo ${events.length} eventos locales)`)

    // Cargar cercanos primero
    await get().fetchNearbyEvents()

    // Luego cargar provincia
    await get().fetchProvinceEvents()

    console.log(`✅ Auto-load completo: ${get().events.length} eventos totales`)
  },

  // 🌍 BUSCAR EVENTOS EN MÚLTIPLES CIUDADES CERCANAS - Auto-detección inicial
  searchMultipleNearbyCities: async (location: Location) => {
    console.log('🌍 [INIT] searchMultipleNearbyCities llamado con:', location.name)

    // 🚀 SIMPLIFICADO: Usar directamente el sistema SSE streaming que ya busca en ciudades cercanas
    // El backend SSE automáticamente detecta ciudades cercanas y busca en múltiples fuentes
    try {
      await get().startStreamingSearch(location)
      console.log('✅ [INIT] Búsqueda SSE completada desde searchMultipleNearbyCities')
    } catch (error) {
      console.error('❌ Error en búsqueda multi-ciudad:', error)
      set({
        loading: false,
        isStreaming: false,
        error: 'Error al buscar eventos'
      })
    }
  }
}))

const EventsContext = createContext<EventsState | null>(null)

export const EventsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const eventsStore = useEventsStore()

  useEffect(() => {
    // No auto-fetch - wait for location detection in components
    // eventsStore.fetchEvents()
  }, [])

  return (
    <EventsContext.Provider value={eventsStore}>
      {children}
    </EventsContext.Provider>
  )
}

export const useEvents = () => {
  const context = useContext(EventsContext)
  if (!context) {
    throw new Error('useEvents must be used within an EventsProvider')
  }
  return context
}