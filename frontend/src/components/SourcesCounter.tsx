import React from 'react'
import { useEvents } from '../stores/EventsStore'

const SourcesCounter: React.FC = () => {
  const { sourceTiming, performanceStats, isStreaming, events } = useEvents()

  // Fallback: Contar eventos por source_api cuando no hay streaming data
  const getEventCountsBySource = () => {
    if (events.length === 0) return {}
    
    const counts: Record<string, number> = {}
    events.forEach(event => {
      const source = event.source_api || 'unknown'
      counts[source] = (counts[source] || 0) + 1
    })
    return counts
  }

  const eventCounts = getEventCountsBySource()
  const hasEventData = Object.keys(eventCounts).length > 0
  const hasStreamingData = sourceTiming.length > 0

  // Modo offline/sin datos - mostrar indicador útil para la calle
  if (!isStreaming && !hasStreamingData && !hasEventData) {
    return (
      <div className="flex items-center space-x-2 text-xs">
        <div className="flex items-center space-x-1 px-2 py-1 rounded-full bg-yellow-500/20 border border-yellow-400/30">
          <span className="text-yellow-400">📡</span>
          <span className="text-yellow-300">Tocá buscar</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center space-x-3 text-xs">
      {/* Indicador de búsqueda activa */}
      {isStreaming && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-white/70">Buscando...</span>
        </div>
      )}

      {/* Contadores por fuente - Priorizar streaming data, fallback a conteo estático */}
      {(hasStreamingData || hasEventData) && (
        <div className="flex items-center space-x-2">
          {hasStreamingData ? (
            // Usar datos de streaming cuando están disponibles
            sourceTiming.map((timing) => {
              const eventCount = timing.eventTimes.length
              if (eventCount === 0 && !isStreaming) return null
              
              const emoji = timing.source === 'eventbrite' ? '🎫' : 
                           timing.source === 'facebook' ? '🔥' : 
                           timing.source === 'instagram' ? '📸' : 
                           timing.source === 'argentina_venues' ? '🏛️' : '🔍'
              
              const isActive = isStreaming && timing.endTime === undefined
              
              return (
                <div 
                  key={timing.source} 
                  className={`flex items-center space-x-1 px-2 py-1 rounded-full transition-all duration-200 ${
                    isActive 
                      ? 'bg-green-500/20 border border-green-400/30' 
                      : 'bg-white/10'
                  }`}
                >
                  <span>{emoji}</span>
                  <span className="text-white/90 font-medium">{eventCount}</span>
                  {isActive && (
                    <div className="w-1 h-1 bg-green-400 rounded-full animate-ping"></div>
                  )}
                </div>
              )
            })
          ) : (
            // Fallback: Usar conteo directo de eventos cuando no hay streaming
            Object.entries(eventCounts).map(([source, count]) => {
              const emoji = source === 'eventbrite' ? '🎫' : 
                           source === 'facebook' ? '🔥' : 
                           source === 'instagram' ? '📸' : 
                           source === 'argentina_venues' ? '🏛️' : 
                           source === 'meetup' ? '👥' :
                           source === 'ticketmaster' ? '🎭' : '🔍'
              
              return (
                <div 
                  key={source} 
                  className="flex items-center space-x-1 px-2 py-1 rounded-full bg-white/10 transition-all duration-200"
                >
                  <span>{emoji}</span>
                  <span className="text-white/90 font-medium">{count}</span>
                  <span className="text-white/50 text-xs">•</span>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* Stats de performance (más rápido) */}
      {performanceStats.fastestSource && !isStreaming && (
        <div className="text-white/50 hidden md:block">
          🏆 {performanceStats.fastestSource} ({Math.round(performanceStats.fastestTime || 0)}ms)
        </div>
      )}
    </div>
  )
}

export default SourcesCounter