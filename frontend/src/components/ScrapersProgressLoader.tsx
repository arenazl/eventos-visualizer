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

interface LocationData {
  original: string
  detected: string
  city: string
  province: string
  country: string
}

interface ScraperResult {
  name: string
  status: 'success' | 'error' | 'timeout'
  events_count: number
  execution_time: string
}

interface ScrapersMessage {
  type: 'connection' | 'scraping_started' | 'location_analyzed' | 'scrapers_discovery' 
       | 'scrapers_discovered' | 'scraper_started' | 'scraper_completed' 
       | 'scraper_timeout' | 'scraper_error' | 'scraping_completed' | 'scraping_error'
  message: string
  progress?: number
  timestamp: string
  location?: string
  location_data?: LocationData
  analysis_time?: string
  scrapers?: string[]
  scraper_name?: string
  events_count?: number
  execution_time?: string
  events?: StreamingEvent[]
  error?: string
  total_events?: number
  scrapers_summary?: ScraperResult[]
  successful_scrapers?: number
  total_scrapers?: number
}

interface ScrapersProgressLoaderProps {
  location: string
  category?: string
  limit?: number
  onEventsReceived?: (events: StreamingEvent[]) => void
  onComplete?: (results: any) => void
  onError?: (error: string) => void
}

export const ScrapersProgressLoader: React.FC<ScrapersProgressLoaderProps> = ({
  location,
  category,
  limit = 30,
  onEventsReceived,
  onComplete,
  onError
}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [currentMessage, setCurrentMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const [locationData, setLocationData] = useState<LocationData | null>(null)
  const [analysisTime, setAnalysisTime] = useState('')
  const [availableScrapers, setAvailableScrapers] = useState<string[]>([])
  const [currentScraper, setCurrentScraper] = useState('')
  const [scraperResults, setScraperResults] = useState<ScraperResult[]>([])
  const [events, setEvents] = useState<StreamingEvent[]>([])
  const [error, setError] = useState<string | null>(null)

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
  }, [])

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://172.29.228.80:8001/ws/scrapers-progress')

      ws.onopen = () => {
        console.log('🔄 ScrapersProgress WebSocket conectado')
        setIsConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const data: ScrapersMessage = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }

      ws.onclose = () => {
        console.log('ScrapersProgress WebSocket desconectado')
        setIsConnected(false)
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('ScrapersProgress WebSocket error:', error)
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

  const handleWebSocketMessage = (data: ScrapersMessage) => {
    console.log('📨 ScrapersProgress message:', data.type, data.message)

    switch (data.type) {
      case 'connection':
        setCurrentMessage(data.message)
        break

      case 'scraping_started':
        setIsRunning(true)
        setCurrentMessage(data.message)
        setProgress(0)
        setEvents([])
        setScraperResults([])
        setLocationData(null)
        break

      case 'location_analyzed':
        setLocationData(data.location_data || null)
        setAnalysisTime(data.analysis_time || '')
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scrapers_discovery':
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scrapers_discovered':
        setAvailableScrapers(data.scrapers || [])
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraper_started':
        setCurrentScraper(data.scraper_name || '')
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
          name: data.scraper_name || '',
          status: 'success',
          events_count: data.events_count || 0,
          execution_time: data.execution_time || '0s'
        }])
        
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraper_timeout':
        setScraperResults(prev => [...prev, {
          name: data.scraper_name || '',
          status: 'timeout',
          events_count: 0,
          execution_time: data.execution_time || '0s'
        }])
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraper_error':
        setScraperResults(prev => [...prev, {
          name: data.scraper_name || '',
          status: 'error',
          events_count: 0,
          execution_time: data.execution_time || '0s'
        }])
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'scraping_completed':
        setIsRunning(false)
        setCurrentMessage(data.message)
        setProgress(100)
        
        if (data.events) {
          setEvents(data.events)
          onEventsReceived?.(data.events)
        }
        
        onComplete?.({
          total_events: data.total_events,
          scrapers_summary: data.scrapers_summary,
          successful_scrapers: data.successful_scrapers,
          total_scrapers: data.total_scrapers,
          events: data.events || []
        })
        break

      case 'scraping_error':
        setIsRunning(false)
        setError(data.message)
        onError?.(data.message)
        break
    }
  }

  const startScraping = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'start_scraping',
        location,
        category,
        limit
      }))
    }
  }

  const getScraperEmoji = (scraperName: string) => {
    switch (scraperName.toLowerCase()) {
      case 'eventbrite': return '🎫'
      case 'meetup': return '🤝'
      case 'facebook': return '🎯'
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
      case 'timeout': return 'text-yellow-400 bg-yellow-500/20'
      case 'error': return 'text-red-400 bg-red-500/20'
      default: return 'text-white/60 bg-white/10'
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
          Conectando...
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
                🔄 Scrapers en Tiempo Real
              </h3>
              <p className="text-white/60">
                Monitoreo detallado de cada scraper
              </p>
            </div>
            {!isRunning && (
              <button
                onClick={startScraping}
                disabled={!isConnected}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                Iniciar Scraping
              </button>
            )}
          </div>

          {/* Location Analysis */}
          {locationData && (
            <div className="mb-4 p-4 bg-white/5 rounded-lg">
              <h4 className="text-white font-medium mb-2">
                📍 Análisis de Ubicación ({analysisTime})
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-white/60">Original:</span>
                  <p className="text-white">{locationData.original}</p>
                </div>
                <div>
                  <span className="text-white/60">Ciudad:</span>
                  <p className="text-white">{locationData.city}</p>
                </div>
                <div>
                  <span className="text-white/60">Provincia:</span>
                  <p className="text-white">{locationData.province}</p>
                </div>
                <div>
                  <span className="text-white/60">País:</span>
                  <p className="text-white">{locationData.country}</p>
                </div>
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
                  className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              {currentScraper && (
                <div className="flex items-center gap-2 text-white">
                  <span className="text-lg">{getScraperEmoji(currentScraper)}</span>
                  <span className="font-medium">Ejecutando: {currentScraper}</span>
                </div>
              )}
            </div>
          )}

          {/* Available Scrapers */}
          {availableScrapers.length > 0 && (
            <div className="mt-4">
              <h4 className="text-white font-medium mb-2">
                🌍 Scrapers Disponibles ({availableScrapers.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {availableScrapers.map(scraper => (
                  <div
                    key={scraper}
                    className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                      currentScraper === scraper
                        ? 'bg-blue-500/20 text-blue-300 scale-110'
                        : 'bg-white/10 text-white/60'
                    } transition-all`}
                  >
                    <span>{getScraperEmoji(scraper)}</span>
                    <span>{scraper}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scrapers Results */}
          {scraperResults.length > 0 && (
            <div className="mt-4">
              <h4 className="text-white font-medium mb-2">
                📊 Resultados por Scraper
              </h4>
              <div className="space-y-2">
                {scraperResults.map((result, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
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
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(result.status)}`}>
                        {result.status}
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
          <h3 className="text-white font-bold text-lg">
            🎉 Eventos Encontrados ({events.length})
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
                Y {events.length - 6} eventos más...
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ScrapersProgressLoader