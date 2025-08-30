import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { create } from 'zustand'

interface Event {
  title: string
  description: string
  start_datetime: string
  end_datetime?: string
  venue_name: string
  venue_address?: string
  latitude?: number
  longitude?: number
  category: string
  price: number
  currency: string
  is_free: boolean
  source?: string
  image_url: string
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

  // AI-First Methods
  aiSearch: (query: string, location?: Location) => Promise<void>
  getSmartRecommendations: (query: string, foundEvents: Event[]) => Promise<void>
  analyzeUserIntent: (query: string) => Promise<any>
  
  // WebSocket Streaming Methods
  startStreamingSearch: (location?: Location) => Promise<void>
  stopStreaming: () => void

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
      const intentResponse = await fetch('http://172.29.228.80:8001/api/ai/analyze-intent', {
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

      // 2. PASO 2: Búsqueda inteligente con contexto
      const searchResponse = await fetch('http://172.29.228.80:8001/api/smart/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          user_context: {
            location: searchLocation?.name,
            coordinates: searchLocation?.coordinates,
            intent_analysis: intent
          }
        })
      })

      if (!searchResponse.ok) throw new Error('Error en búsqueda AI')

      const searchData = await searchResponse.json()
      const foundEvents = searchData.recommended_events || []

      // 3. PASO 3: Generar recomendaciones inteligentes
      await get().getSmartRecommendations(query, foundEvents)

      set({ events: foundEvents, loading: false })

    } catch (error) {
      console.warn('AI search failed, falling back to traditional search:', error)
      // Fallback a búsqueda tradicional
      await get().smartSearch(query, location)
    }
  },

  // 🎯 Recomendaciones inteligentes (complementa cualquier búsqueda)
  getSmartRecommendations: async (query: string, foundEvents: Event[]) => {
    try {
      const { currentLocation } = get()
      const query = get()

      const response = await fetch('http://172.29.228.80:8001/api/ai/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_query: query,
          found_events: foundEvents,
          no_results: foundEvents.length === 0,
          user_context: {
            location: currentLocation?.name,
            coordinates: currentLocation?.coordinates
          }
        })
      })

      if (response.ok) {
        const recommendations = await response.json()
        set({ aiRecommendations: recommendations })
      }
    } catch (error) {
      console.warn('Failed to get AI recommendations:', error)
    }
  },

  // 🧠 Análisis de intención
  analyzeUserIntent: async (query: string) => {
    try {
      const response = await fetch('http://172.29.228.80:8001/api/ai/analyze-intent', {
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
    set({ loading: true, error: null })
    try {
      const { currentLocation } = get()
      const searchLocation = location || currentLocation

      // Usar el nuevo endpoint progressive
      let apiUrl = 'http://172.29.228.80:8001/api/multi/fetch-all'
      if (searchLocation) {
        apiUrl += `?location=${encodeURIComponent(searchLocation.name || "Buenos Aires")}`
      }

      const response = await fetch(apiUrl)
      if (!response.ok) throw new Error('Error al cargar eventos')

      const data = await response.json()
      set({ events: data.events || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
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
    set({ loading: true, error: null })
    try {
      const { currentLocation } = get()
      const searchLocation = location || currentLocation

      let apiUrl = `http://172.29.228.80:8001/api/events/search?q=${encodeURIComponent(query)}`
      if (searchLocation) {
        apiUrl += `&location=${encodeURIComponent(searchLocation.name || "Buenos Aires")}`
      }

      const response = await fetch(apiUrl)
      if (!response.ok) throw new Error('Error en la búsqueda')

      const data = await response.json()
      set({ events: data.events || data || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  smartSearch: async (query: string, location?: Location) => {
    set({ loading: true, error: null })
    try {
      const { currentLocation } = get()
      const searchLocation = location || currentLocation

      // Usar Gemini Smart Search
      const response = await fetch('http://172.29.228.80:8001/api/smart/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          user_context: {
            location: searchLocation?.name,
            coordinates: searchLocation?.coordinates
          }
        })
      })

      if (!response.ok) throw new Error('Error en búsqueda inteligente')

      const data = await response.json()
      set({ events: data.recommended_events || [], loading: false })
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
    const { currentLocation } = get()
    const searchLocation = location || currentLocation
    
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
      performanceStats: {}
    })

    try {
      const ws = new WebSocket('ws://172.29.228.80:8001/ws/search-events')
      
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
  },

  stopStreaming: () => {
    set({ 
      isStreaming: false, 
      loading: false,
      streamingProgress: 0,
      streamingMessage: '',
      streamingSource: ''
    })
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