import React from 'react'
import { useEvents } from '../stores/EventsStore'

const ScrapersDetailPanel: React.FC = () => {
  const { 
    sourceTiming, 
    performanceStats, 
    isStreaming,
    streamingSource,
    streamingProgress,
    streamingMessage,
    events
  } = useEvents()

  // Calcular estadísticas detalladas
  const getDetailedStats = () => {
    return sourceTiming.map(timing => {
      const eventCount = timing.eventTimes.length
      const avgTimePerEvent = eventCount > 0 ? timing.totalTime! / eventCount : 0
      const isActive = isStreaming && timing.endTime === undefined
      const status = isActive ? 'activo' : timing.totalTime ? 'completado' : 'pendiente'
      
      return {
        ...timing,
        eventCount,
        avgTimePerEvent,
        isActive,
        status
      }
    })
  }

  const detailedStats = getDetailedStats()
  const totalEvents = events.length
  const activeScrapers = detailedStats.filter(s => s.isActive).length
  const completedScrapers = detailedStats.filter(s => s.status === 'completado').length

  // Siempre mostrar el panel, incluso sin datos
  // if (!isStreaming && sourceTiming.length === 0) {
  //   return null
  // }

  return (
    <div className="fixed top-20 right-4 z-50 max-w-md">
      {/* Header siempre visible */}
      <div className={`w-full flex items-center justify-between px-4 py-2 backdrop-blur-xl border transition-all duration-200 rounded-t-lg ${
          isStreaming 
            ? 'bg-green-500/20 border-green-400/30 text-green-300' 
            : 'bg-white/10 border-white/20 text-white/80'
        }`}
      >
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className="font-medium text-sm">
            {isStreaming ? 'Scrapers En Vivo' : 'Análisis Detallado'}
          </span>
        </div>
        
        <div className="flex items-center space-x-3 text-xs">
          {isStreaming && streamingSource && (
            <span className="text-green-300">
              🔄 {streamingSource}
            </span>
          )}
          <span className="font-bold">{totalEvents} eventos</span>
          {detailedStats.length > 0 && (
            <span className="text-white/60">
              {detailedStats.length} APIs
            </span>
          )}
        </div>
      </div>

      {/* Panel detallado SIEMPRE visible */}
      <div className="backdrop-blur-xl bg-black/40 border-l border-r border-b border-white/20 rounded-b-lg p-4 shadow-2xl">
        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
          <div className="text-center p-2 bg-white/10 rounded">
            <div className="font-bold text-green-400">{activeScrapers}</div>
            <div className="text-white/70">Activos</div>
          </div>
          <div className="text-center p-2 bg-white/10 rounded">
            <div className="font-bold text-blue-400">{completedScrapers}</div>
            <div className="text-white/70">Completados</div>
          </div>
          <div className="text-center p-2 bg-white/10 rounded">
            <div className="font-bold text-purple-400">{totalEvents}</div>
            <div className="text-white/70">Total Eventos</div>
          </div>
        </div>

        {/* Current streaming status */}
        {isStreaming && streamingSource && (
          <div className="mb-4 p-3 bg-green-500/20 border border-green-400/30 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-green-300 font-medium">🔄 {streamingSource}</span>
              <span className="text-green-400 text-xs">{streamingProgress}%</span>
            </div>
            <div className="text-green-200 text-xs">{streamingMessage}</div>
            <div className="mt-2 bg-green-900/50 rounded-full h-1">
              <div 
                className="bg-green-400 h-1 rounded-full transition-all duration-300"
                style={{ width: `${streamingProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Detailed scraper stats */}
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {detailedStats.length === 0 ? (
            // Mostrar cuando no hay datos de scrapers
            <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
              <div className="text-white/60 text-sm mb-2">🔍 Panel de Monitoreo Técnico</div>
              <div className="text-white/80 text-xs">
                Haz una búsqueda para ver:
                <div className="mt-2 text-left">
                  • Tiempos de respuesta por API<br/>
                  • Cantidad de eventos por fuente<br/>
                  • Llamadas individuales y variaciones<br/>
                  • Estados en tiempo real
                </div>
              </div>
            </div>
          ) : (
            detailedStats.map((scraper) => {
            const emoji = scraper.source === 'eventbrite' ? '🎫' : 
                         scraper.source === 'facebook' ? '🔥' : 
                         scraper.source === 'instagram' ? '📸' : 
                         scraper.source === 'argentina_venues' ? '🏛️' : 
                         scraper.source === 'meetup' ? '👥' : '🔍'
            
            const statusColor = scraper.isActive ? 'text-green-400' : 
                               scraper.status === 'completado' ? 'text-blue-400' : 
                               'text-gray-400'

            return (
              <div key={scraper.source} className="p-3 bg-white/5 rounded-lg border border-white/10">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{emoji}</span>
                    <span className="text-white/90 font-medium capitalize">{scraper.source}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${statusColor} bg-current/20`}>
                    {scraper.status}
                  </span>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-white/60">Eventos:</span>
                    <span className="text-white/90 font-bold ml-1">{scraper.eventCount}</span>
                  </div>
                  <div>
                    <span className="text-white/60">Tiempo total:</span>
                    <span className="text-white/90 font-bold ml-1">
                      {scraper.totalTime ? Math.round(scraper.totalTime) : '⏳'}ms
                    </span>
                  </div>
                  {scraper.eventCount > 0 && (
                    <>
                      <div>
                        <span className="text-white/60">Avg/evento:</span>
                        <span className="text-white/90 font-bold ml-1">
                          {Math.round(scraper.avgTimePerEvent)}ms
                        </span>
                      </div>
                      <div>
                        <span className="text-white/60">Primer evento:</span>
                        <span className="text-white/90 font-bold ml-1">
                          {Math.round(scraper.firstEventTime || 0)}ms
                        </span>
                      </div>
                    </>
                  )}
                </div>

                {/* Event timing details - Información precisa que pediste */}
                {scraper.eventTimes.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/10">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-white/60 text-xs">Lotes recibidos:</span>
                      <span className="text-white/80 text-xs font-bold">{scraper.eventTimes.length} llamadas</span>
                    </div>
                    
                    {/* Mostrar todos los timings de las llamadas */}
                    <div className="flex flex-wrap gap-1 mt-1">
                      {scraper.eventTimes.map((time, idx) => (
                        <span 
                          key={idx} 
                          className={`text-xs px-2 py-0.5 rounded ${
                            idx === scraper.eventTimes.length - 1 
                              ? 'bg-green-500/30 text-green-300 border border-green-400/50' 
                              : 'bg-white/10 text-white/80'
                          }`}
                          title={`Llamada #${idx + 1}: ${Math.round(time)}ms`}
                        >
                          #{idx + 1}: {Math.round(time)}ms
                        </span>
                      ))}
                    </div>
                    
                    {/* Variación entre llamadas */}
                    {scraper.eventTimes.length > 1 && (
                      <div className="mt-2 text-xs">
                        <span className="text-white/60">Variación:</span>
                        <span className="text-white/90 ml-1">
                          {Math.round(Math.min(...scraper.eventTimes))}ms - {Math.round(Math.max(...scraper.eventTimes))}ms
                        </span>
                        <span className="text-white/60 ml-2">
                          (±{Math.round(Math.max(...scraper.eventTimes) - Math.min(...scraper.eventTimes))}ms)
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })
          )}
        </div>

        {/* Performance comparison */}
        {performanceStats.fastestSource && performanceStats.slowestSource && !isStreaming && (
          <div className="mt-4 pt-4 border-t border-white/20 text-xs">
            <div className="flex justify-between text-white/80">
              <span>🏆 Más rápido: {performanceStats.fastestSource} ({Math.round(performanceStats.fastestTime || 0)}ms)</span>
            </div>
            <div className="flex justify-between text-white/60 mt-1">
              <span>🐌 Más lento: {performanceStats.slowestSource} ({Math.round(performanceStats.slowestTime || 0)}ms)</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScrapersDetailPanel