import React, { useState, useEffect, useRef } from 'react'
import EventCardModern from './EventCardModern'

interface StreamingEvent {
  id?: string
  title: string
  description?: string
  start_datetime: string
  end_datetime: string
  venue_name: string
  venue_address?: string
  category: string
  price: number
  currency: string
  is_free: boolean
  source: string
  event_url?: string
  image_url?: string
  created_at: string
  updated_at: string
}

interface ScraperResult {
  name: string
  status: 'success' | 'error' | 'timeout' | 'empty'
  events_count: number
  execution_time: string
}

interface StreamingMessage {
  type: 'connection' | 'scraper_completed' | 'scraper_empty' | 'scraper_error' 
       | 'search_completed' | 'search_error' | 'recommend_started' 
       | 'recommend_cities_detected' | 'recommend_location_started'
  message: string
  progress?: number
  timestamp: string
  location?: string
  scraper?: string
  events?: StreamingEvent[]
  count?: number
  execution_time?: string
  error?: string
  total_events?: number
  nearby_cities?: string[]
  status?: string
}

interface StreamingProgressLoaderProps {
  location: string
  onEventsReceived?: (events: StreamingEvent[]) => void
  onComplete?: (results: any) => void
  onError?: (error: string) => void
  mode?: 'search' | 'recommend'
}

export const StreamingProgressLoader: React.FC<StreamingProgressLoaderProps> = ({
  location,
  onEventsReceived,
  onComplete,
  onError,
  mode = 'search'
}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [currentMessage, setCurrentMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const [currentScraper, setCurrentScraper] = useState('')
  const [scraperResults, setScraperResults] = useState<ScraperResult[]>([])
  const [events, setEvents] = useState<StreamingEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [nearbyCities, setNearbyCities] = useState<string[]>([])
  const [totalEvents, setTotalEvents] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [mode])

  const connectWebSocket = () => {
    try {
      const endpoint = mode === 'recommend' ? '/ws/recommend' : '/ws/search-events'
      const ws = new WebSocket(`ws://172.29.228.80:8001${endpoint}`)

      ws.onopen = () => {
        console.log(`🔄 ${mode} WebSocket conectado`)
        setIsConnected(true)
        setError(null)
        
        // Iniciar búsqueda automáticamente
        startSearch()
      }

      ws.onmessage = (event) => {
        try {
          const data: StreamingMessage = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }

      ws.onclose = () => {
        console.log(`${mode} WebSocket desconectado`)
        setIsConnected(false)
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error(`${mode} WebSocket error:`, error)
        setError('Error de conexión WebSocket')
        onError?.('Error de conexión WebSocket')
      }

      wsRef.current = ws
    } catch (e) {
      console.error('Error creating WebSocket:', e)
      setError('No se pudo conectar al servidor')
      onError?.('No se pudo conectar al servidor')
    }
  }

  const handleWebSocketMessage = (data: StreamingMessage) => {
    console.log(`📨 ${mode} message:`, data.type, data.message)

    switch (data.type) {
      case 'connection':
        setCurrentMessage(data.message)
        setIsRunning(true)
        setProgress(0)
        setEvents([])
        setScraperResults([])
        setTotalEvents(0)
        break

      case 'recommend_started':
        setCurrentMessage(data.message)
        setIsRunning(true)
        setProgress(5)
        break

      case 'recommend_cities_detected':
        setNearbyCities(data.nearby_cities || [])
        setCurrentMessage(data.message)
        setProgress(10)
        break

      case 'recommend_location_started':
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraper_completed':
        if (data.events && data.events.length > 0) {
          setEvents(prev => {
            const newEvents = [...prev, ...data.events!]
            onEventsReceived?.(newEvents)
            return newEvents
          })
        }
        
        setScraperResults(prev => [...prev, {
          name: data.scraper || 'Unknown',
          status: 'success',
          events_count: data.count || 0,
          execution_time: data.execution_time || '0s'
        }])
        
        setCurrentScraper(data.scraper || '')
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        setTotalEvents(data.total_events || 0)
        break

      case 'scraper_empty':
        setScraperResults(prev => [...prev, {
          name: data.scraper || 'Unknown',
          status: 'empty',
          events_count: 0,
          execution_time: data.execution_time || '0s'
        }])
        setCurrentScraper(data.scraper || '')
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraper_error':
        setScraperResults(prev => [...prev, {
          name: data.scraper || 'Unknown',
          status: 'error',
          events_count: 0,
          execution_time: data.execution_time || '0s'
        }])
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'search_completed':
        setIsRunning(false)
        setCurrentMessage(data.message)
        setProgress(100)
        setTotalEvents(data.total_events || 0)
        
        onComplete?.({
          total_events: data.total_events,
          scrapers_summary: scraperResults,
          events: events
        })
        break

      case 'search_error':
        setIsRunning(false)
        setError(data.message)
        onError?.(data.message)
        break
    }
  }

  const startSearch = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = mode === 'recommend' 
        ? { location: location }
        : { action: 'search', location: location, message: '' }
      
      wsRef.current.send(JSON.stringify(message))
    }
  }

  const getScraperEmoji = (scraperName: string) => {
    switch (scraperName.toLowerCase()) {
      case 'eventbrite': return '🎫'
      case 'meetup': return '🤝'
      case 'facebook': return '🎯'
      case 'facebook_api': return '📘'
      case 'ticketmaster': return '🎵'
      case 'universe': return '🌌'
      case 'dice': return '🎲'
      case 'bandsintown': return '🎵'
      default: return '🔍'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400 bg-green-500/20'
      case 'empty': return 'text-yellow-400 bg-yellow-500/20'
      case 'error': return 'text-red-400 bg-red-500/20'
      default: return 'text-white/60 bg-white/10'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅'
      case 'empty': return '⚪'
      case 'error': return '❌'
      default: return '🔍'
    }
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-6 text-center">
        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-bold text-white/90 mb-2">Error de conexión</h3>
        <p className="text-white/60 mb-4">{error}</p>
        <button
          onClick={connectWebSocket}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          Reconectar
        </button>
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="relative">
          <div className="w-12 h-12 border-4 border-white/20 rounded-full animate-spin"></div>
          <div className="absolute top-0 left-0 w-12 h-12 border-4 border-transparent border-t-blue-500 rounded-full animate-spin"></div>
        </div>
        <p className="mt-4 text-white/80 font-medium animate-pulse">
          Conectando a {mode === 'recommend' ? 'recomendaciones' : 'búsqueda'}...
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 rounded-2xl blur opacity-30"></div>
        <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-white">
                {mode === 'recommend' ? '💡 Recomendaciones Streaming' : '🚀 Búsqueda Streaming'}
              </h3>
              <p className="text-white/60">
                {mode === 'recommend' 
                  ? 'Eventos en ciudades cercanas en tiempo real'
                  : 'Scrapers ejecutándose en tiempo real'}
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">
                {totalEvents}
              </div>
              <div className="text-xs text-white/60">
                eventos encontrados
              </div>
            </div>
          </div>

          {/* Nearby Cities for Recommend */}
          {mode === 'recommend' && nearbyCities.length > 0 && (
            <div className="mb-4 p-4 bg-white/5 rounded-lg">
              <h4 className="text-white font-medium mb-2">
                🏙️ Ciudades Aledañas
              </h4>
              <div className="flex flex-wrap gap-2">
                {nearbyCities.map(city => (
                  <div
                    key={city}
                    className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm"
                  >
                    {city}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress */}
          {isRunning && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-white">{currentMessage}</span>
                <span className="text-white font-bold">{Math.round(progress)}%</span>
              </div>
              
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    mode === 'recommend'
                      ? 'bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500'
                      : 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500'
                  }`}
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              {currentScraper && (
                <div className="flex items-center gap-2 text-white">
                  <span className="text-lg">{getScraperEmoji(currentScraper)}</span>
                  <span className="font-medium">Ejecutando: {currentScraper}</span>
                  <div className="ml-auto flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <span className="text-xs text-blue-300">activo</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Scrapers Results */}
          {scraperResults.length > 0 && (
            <div className="mt-4">
              <h4 className="text-white font-medium mb-2">
                📊 Resultados por Scraper ({scraperResults.length})
              </h4>
              <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {scraperResults.map((result, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg opacity-0 animate-fade-in-up"
                    style={{
                      animationDelay: `${index * 0.1}s`,
                      animationFillMode: 'forwards'
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{getScraperEmoji(result.name)}</span>
                      <div>
                        <span className="text-white font-medium">{result.name}</span>
                        <div className="text-xs text-white/60">
                          {result.execution_time}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-white font-bold">
                        {result.events_count} eventos
                      </div>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(result.status)}`}>
                        <span>{getStatusIcon(result.status)}</span>
                        <span>{result.status}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Events Preview */}
      {events.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-white font-bold text-lg flex items-center gap-2">
            🎉 Eventos Encontrados 
            <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text font-extrabold">
              ({events.length})
            </span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.slice(0, 6).map((event, index) => (
              <div
                key={index}
                className="opacity-0 animate-fade-in-up"
                style={{
                  animationDelay: `${(index % 3) * 0.1}s`,
                  animationFillMode: 'forwards'
                }}
              >
                <EventCardModern event={event} />
              </div>
            ))}
          </div>
          {events.length > 6 && (
            <div className="text-center">
              <p className="text-white/60">
                Y {events.length - 6} eventos más encontrados en tiempo real...
              </p>
            </div>
          )}
        </div>
      )}

      {/* No Events Message */}
      {!isRunning && events.length === 0 && scraperResults.length > 0 && (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mb-4 mx-auto">
            <span className="text-2xl">🔍</span>
          </div>
          <h3 className="text-lg font-bold text-white/90 mb-2">Sin eventos encontrados</h3>
          <p className="text-white/60">
            {mode === 'recommend' 
              ? 'No se encontraron eventos en las ciudades cercanas'
              : `No se encontraron eventos para "${location}"`}
          </p>
        </div>
      )}
    </div>
  )
}

export default StreamingProgressLoader