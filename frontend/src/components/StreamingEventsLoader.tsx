import React, { useState, useEffect, useRef } from 'react'
import EventCardModern from './EventCardModern'
import { EventsGridSkeleton } from './LoadingStates'

interface StreamingEvent {
  id?: string
  title: string
  description?: string
  start_datetime: string
  end_datetime: string
  venue_name: string
  venue_address?: string
  neighborhood?: string
  latitude?: number
  longitude?: number
  category: string
  subcategory?: string
  tags?: string[]
  price: number
  currency: string
  is_free: boolean
  source: string
  source_id?: string
  event_url?: string
  image_url?: string
  organizer?: string
  capacity?: number
  status?: string
  scraping_method?: string
  created_at: string
  updated_at: string
}

interface StreamingMessage {
  type: 'connection' | 'search_started' | 'source_started' | 'events_batch' | 'search_completed' | 'search_error'
  status?: string
  message: string
  progress?: number
  source?: string
  events?: StreamingEvent[]
  batch_count?: number
  total_so_far?: number
  total_events?: number
  sources_completed?: number
}

interface StreamingEventsLoaderProps {
  location: string
  onEventsReceived?: (events: StreamingEvent[]) => void
  onSearchComplete?: (totalEvents: number) => void
  onError?: (error: string) => void
}

export const StreamingEventsLoader: React.FC<StreamingEventsLoaderProps> = ({
  location,
  onEventsReceived,
  onSearchComplete,
  onError
}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [events, setEvents] = useState<StreamingEvent[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const [currentSource, setCurrentSource] = useState('')
  const [totalEvents, setTotalEvents] = useState(0)
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

  useEffect(() => {
    if (isConnected && location) {
      startSearch()
    }
  }, [isConnected, location])

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://172.29.228.80:8001/ws/search-events')

      ws.onopen = () => {
        console.log('🔥 WebSocket conectado')
        setIsConnected(true)
        setError(null)
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
        console.log('WebSocket desconectado')
        setIsConnected(false)
        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
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
    console.log('📨 WebSocket message:', data.type)

    switch (data.type) {
      case 'connection':
        setCurrentMessage(data.message)
        break

      case 'search_started':
        setIsSearching(true)
        setCurrentMessage(data.message)
        setProgress(0)
        setEvents([])
        setTotalEvents(0)
        break

      case 'source_started':
        setCurrentSource(data.source || '')
        setCurrentMessage(data.message)
        setProgress(data.progress || 0)
        break

      case 'events_batch':
        if (data.events) {
          setEvents(prev => {
            const newEvents = [...prev, ...data.events!]
            onEventsReceived?.(newEvents)
            return newEvents
          })
          setTotalEvents(data.total_so_far || 0)
        }
        setProgress(data.progress || 0)
        break

      case 'search_completed':
        setIsSearching(false)
        setCurrentMessage(data.message)
        setProgress(100)
        onSearchComplete?.(data.total_events || 0)
        break

      case 'search_error':
        setIsSearching(false)
        setError(data.message)
        onError?.(data.message)
        break
    }
  }

  const startSearch = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'search',
        location: location
      }))
    }
  }

  // Get source emoji and name
  const getSourceDisplay = (source: string) => {
    switch (source) {
      case 'eventbrite': return { emoji: '🎫', name: 'Eventbrite' }
      case 'facebook': return { emoji: '🔥', name: 'Facebook' }
      case 'instagram': return { emoji: '📸', name: 'Instagram' }
      default: return { emoji: '🔍', name: source }
    }
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
        <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mb-6">
          <svg className="w-10 h-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-white/90 mb-3">Error de conexión</h3>
        <p className="text-white/60 mb-4">{error}</p>
        <button
          onClick={connectWebSocket}
          className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
        >
          Reconectar
        </button>
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-white/20 rounded-full animate-spin"></div>
          <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-blue-500 rounded-full animate-spin"></div>
        </div>
        <p className="mt-6 text-white/80 text-lg font-medium animate-pulse">
          Conectando al servidor...
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar & Status */}
      {isSearching && (
        <div className="relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-cyan-600/20 rounded-2xl blur opacity-30"></div>
          <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {currentSource && (
                  <span className="text-2xl">
                    {getSourceDisplay(currentSource).emoji}
                  </span>
                )}
                <div>
                  <h3 className="text-white font-semibold">
                    {currentMessage}
                  </h3>
                  <p className="text-white/60 text-sm">
                    {totalEvents} eventos encontrados hasta ahora
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">
                  {Math.round(progress)}%
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500 transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            {/* Sources Status */}
            <div className="flex justify-center gap-4 mt-4">
              {['eventbrite', 'facebook', 'instagram'].map((source) => {
                const { emoji, name } = getSourceDisplay(source)
                const isActive = currentSource === source
                const isCompleted = progress > (source === 'eventbrite' ? 50 : source === 'facebook' ? 75 : 100)

                return (
                  <div
                    key={source}
                    className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm transition-all ${isActive
                        ? 'bg-white/20 text-white scale-110'
                        : isCompleted
                          ? 'bg-green-500/20 text-green-300'
                          : 'bg-white/5 text-white/40'
                      }`}
                  >
                    <span>{emoji}</span>
                    <span className="font-medium">{name}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Events Grid */}
      {events.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">
              Eventos encontrados ({totalEvents})
            </h2>
            {isSearching && (
              <div className="flex items-center gap-2 text-white/60">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">Buscando más...</span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event, index) => (
              <div
                key={`${event.source_id || index}`}
                className="opacity-0 animate-fade-in-up"
                style={{
                  animationDelay: `${(index % 3) * 0.1}s`,
                  animationFillMode: 'forwards'
                }}
              >
                <EventCardModern event={event} />
              </div>
            ))}

            {/* Show skeleton cards while searching */}
            {isSearching && (
              <>
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={`skeleton-${index}`} className="animate-pulse">
                    <div className="relative group">
                      <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-cyan-600/20 rounded-2xl blur opacity-30"></div>
                      <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
                        <div className="w-full h-48 bg-white/10 rounded-xl mb-4"></div>
                        <div className="h-6 bg-white/15 rounded-lg mb-3"></div>
                        <div className="h-4 bg-white/10 rounded-lg w-3/4 mb-4"></div>
                        <div className="flex justify-between items-center">
                          <div className="h-6 bg-white/15 rounded-lg w-20"></div>
                          <div className="w-8 h-8 bg-white/10 rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      ) : isSearching ? (
        <EventsGridSkeleton />
      ) : null}
    </div>
  )
}

export default StreamingEventsLoader