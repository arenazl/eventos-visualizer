import React, { useState } from 'react'
import { useEvents } from '../stores/EventsStore'

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

interface UnifiedScrapersPanelProps {
  scrapersExecution?: ScrapersExecution | null
}

const UnifiedScrapersPanel: React.FC<UnifiedScrapersPanelProps> = ({
  scrapersExecution
}) => {
  // Estado para colapsar/expandir
  const [isExpanded, setIsExpanded] = useState(false)
  // Datos del store de eventos (datos reales de timing)
  const { 
    sourceTiming, 
    performanceStats, 
    isStreaming,
    streamingSource,
    streamingProgress,
    streamingMessage,
    events
  } = useEvents()

  // Combinar datos reales de ambas fuentes
  const getCombinedStats = () => {
    const realTimeStats = sourceTiming.map(timing => ({
      source: timing.source,
      eventCount: timing.eventTimes?.length || 0,
      totalTime: timing.totalTime || 0,
      avgTimePerEvent: timing.eventTimes?.length > 0 ? (timing.totalTime! / timing.eventTimes.length) : 0,
      isActive: isStreaming && timing.endTime === undefined,
      status: isStreaming && timing.endTime === undefined ? 'activo' : 
             timing.totalTime ? 'completado' : 'pendiente',
      eventTimes: timing.eventTimes || [],
      firstEventTime: timing.firstEventTime || 0
    }))

    // Si también tenemos datos de scrapersExecution, los combinamos
    const executionStats = scrapersExecution?.scrapers_info?.map(scraper => ({
      source: scraper.name.toLowerCase(),
      eventCount: scraper.events_count,
      totalTime: parseFloat(scraper.response_time.replace(/[^0-9.]/g, '')) || 0,
      avgTimePerEvent: scraper.events_count > 0 ? (parseFloat(scraper.response_time.replace(/[^0-9.]/g, '')) || 0) / scraper.events_count : 0,
      isActive: scraper.status !== 'success' && scraper.status !== 'failed',
      status: scraper.status === 'success' ? 'completado' : 
             scraper.status === 'failed' ? 'fallido' : 'timeout',
      message: scraper.message,
      responseTime: scraper.response_time
    })) || []

    // Combinar y deduplicar por source
    const combined = [...realTimeStats]
    executionStats.forEach(execStat => {
      const existingIndex = combined.findIndex(stat => stat.source === execStat.source)
      if (existingIndex >= 0) {
        // Merge data - usar datos más recientes
        combined[existingIndex] = { ...combined[existingIndex], ...execStat }
      } else {
        combined.push(execStat)
      }
    })

    return combined
  }

  const combinedStats = getCombinedStats()
  const totalEvents = events.length
  const activeScrapers = combinedStats.filter(s => s.isActive).length
  const completedScrapers = combinedStats.filter(s => s.status === 'completado').length
  const totalExecutionTime = combinedStats.reduce((sum, s) => sum + s.totalTime, 0)
  const avgExecutionTime = combinedStats.length > 0 ? totalExecutionTime / combinedStats.length : 0

  // Si no hay datos reales, no mostrar el panel
  if (combinedStats.length === 0 && !isStreaming) {
    return null
  }

  const getServiceEmoji = (source: string) => {
    switch (source.toLowerCase()) {
      case 'eventbrite': return '🎫'
      case 'facebook': return '🔥'
      case 'instagram': return '📸'
      case 'argentina_venues': return '🏛️'
      case 'meetup': return '👥'
      case 'ticketmaster': return '🎤'
      default: return '🔍'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'activo': return 'text-green-400'
      case 'completado': return 'text-blue-400'
      case 'fallido': return 'text-red-400'
      case 'timeout': return 'text-yellow-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="w-full mb-4">
      {/* Header clickable con colores del sistema */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white/90 backdrop-blur-sm border border-gray-200/70 rounded-lg hover:bg-white/95 transition-all duration-200 shadow-sm"
      >
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-500 animate-pulse' : 'bg-blue-500'}`}></div>
          <span className="font-medium text-sm text-gray-800">
            {isStreaming ? '⚡ APIs Ejecutándose' : '📊 Métricas de APIs'}
          </span>
        </div>
        
        <div className="flex items-center space-x-3 text-xs">
          {isStreaming && streamingSource && (
            <span className="text-green-600 bg-green-100/70 px-2 py-1 rounded-full font-medium">
              🔄 {streamingSource}
            </span>
          )}
          <span className="font-bold text-gray-700">{totalEvents} eventos</span>
          <span className="text-gray-500">
            {combinedStats.length} fuentes
          </span>
          <span className="text-gray-500 font-mono">
            ~{Math.round(avgExecutionTime)}ms
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Panel principal expandible con colores del sistema */}
      {isExpanded && (
        <div className="border-t border-gray-200/70 bg-white/80 backdrop-blur-sm rounded-b-lg p-4 shadow-sm">
          {/* Stats resumen - Solo datos reales */}
          <div className="grid grid-cols-4 gap-2 mb-4 text-xs">
            <div className="text-center p-2 bg-green-50 border border-green-200/50 rounded">
              <div className="font-bold text-green-600">{activeScrapers}</div>
              <div className="text-green-500/70">Activos</div>
            </div>
            <div className="text-center p-2 bg-blue-50 border border-blue-200/50 rounded">
              <div className="font-bold text-blue-600">{completedScrapers}</div>
              <div className="text-blue-500/70">Completados</div>
            </div>
            <div className="text-center p-2 bg-purple-50 border border-purple-200/50 rounded">
              <div className="font-bold text-purple-600">{totalEvents}</div>
              <div className="text-purple-500/70">Eventos</div>
            </div>
            <div className="text-center p-2 bg-orange-50 border border-orange-200/50 rounded">
              <div className="font-bold text-orange-600">{Math.round(totalExecutionTime)}ms</div>
              <div className="text-orange-500/70">Tiempo Total</div>
            </div>
          </div>

          {/* Status de streaming actual */}
          {isStreaming && streamingSource && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-green-700 font-medium">🔄 {streamingSource}</span>
                <span className="text-green-600 text-xs">{streamingProgress}%</span>
              </div>
              <div className="text-green-600 text-xs">{streamingMessage}</div>
              <div className="mt-2 bg-green-200 rounded-full h-1">
                <div 
                  className="bg-green-500 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${streamingProgress}%` }}
                ></div>
              </div>
            </div>
          )}

        {/* Lista detallada de servicios - Solo datos reales */}
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {combinedStats.map((service) => {
            const emoji = getServiceEmoji(service.source)
            const statusColor = getStatusColor(service.status)

            return (
              <div key={service.source} className="p-3 bg-gray-50/80 rounded-lg border border-gray-200/50 hover:bg-gray-100/80 transition-colors duration-200">
                {/* Header del servicio */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{emoji}</span>
                    <span className="text-gray-700 font-medium capitalize">{service.source}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${statusColor} ${
                    service.status === 'activo' ? 'bg-green-100' :
                    service.status === 'completado' ? 'bg-blue-100' :
                    service.status === 'fallido' ? 'bg-red-100' :
                    'bg-gray-100'
                  }`}>
                    {service.status}
                  </span>
                </div>

                {/* Métricas reales */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Eventos:</span>
                    <span className="text-gray-700 font-bold ml-1">{service.eventCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Tiempo total:</span>
                    <span className="text-gray-700 font-bold ml-1">
                      {service.totalTime > 0 ? Math.round(service.totalTime) : '0'}ms
                    </span>
                  </div>
                  {service.eventCount > 0 && (
                    <>
                      <div>
                        <span className="text-gray-500">Avg/evento:</span>
                        <span className="text-gray-700 font-bold ml-1">
                          {Math.round(service.avgTimePerEvent)}ms
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Primer evento:</span>
                        <span className="text-gray-700 font-bold ml-1">
                          {Math.round(service.firstEventTime || 0)}ms
                        </span>
                      </div>
                    </>
                  )}
                </div>

                {/* Detalles de timing real (si existen) */}
                {service.eventTimes && service.eventTimes.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200/50">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-500 text-xs">Llamadas ejecutadas:</span>
                      <span className="text-gray-700 text-xs font-bold">{service.eventTimes.length} reales</span>
                    </div>
                    
                    <div className="flex flex-wrap gap-1 mt-1">
                      {service.eventTimes.map((time: number, idx: number) => (
                        <span 
                          key={idx} 
                          className={`text-xs px-2 py-0.5 rounded ${
                            idx === service.eventTimes!.length - 1 
                              ? 'bg-green-100 text-green-700 border border-green-300' 
                              : 'bg-gray-100 text-gray-600'
                          }`}
                          title={`Llamada real #${idx + 1}: ${Math.round(time)}ms`}
                        >
                          #{idx + 1}: {Math.round(time)}ms
                        </span>
                      ))}
                    </div>
                    
                    {service.eventTimes.length > 1 && (
                      <div className="mt-2 text-xs">
                        <span className="text-gray-500">Variación real:</span>
                        <span className="text-gray-700 ml-1">
                          {Math.round(Math.min(...service.eventTimes))}ms - {Math.round(Math.max(...service.eventTimes))}ms
                        </span>
                        <span className="text-gray-500 ml-2">
                          (±{Math.round(Math.max(...service.eventTimes) - Math.min(...service.eventTimes))}ms)
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Mensaje adicional si existe */}
                {('message' in service) && service.message && (
                  <div className="mt-2 text-xs text-gray-500 italic">
                    {service.message}
                  </div>
                )}
              </div>
            )
          })}
        </div>

          {/* Comparación de performance real */}
          {performanceStats.fastestSource && performanceStats.slowestSource && !isStreaming && (
            <div className="mt-4 pt-4 border-t border-gray-200/50 text-xs">
              <div className="flex justify-between text-gray-700">
                <span>🏆 Más rápido: {performanceStats.fastestSource} ({Math.round(performanceStats.fastestTime || 0)}ms)</span>
              </div>
              <div className="flex justify-between text-gray-500 mt-1">
                <span>🐌 Más lento: {performanceStats.slowestSource} ({Math.round(performanceStats.slowestTime || 0)}ms)</span>
              </div>
            </div>
          )}

          {/* Summary real si existe */}
          {scrapersExecution?.summary && (
            <div className="mt-4 pt-4 border-t border-gray-200/50 text-xs text-gray-600">
              <span className="text-purple-600 font-medium">📋 Resumen:</span> {scrapersExecution.summary}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default UnifiedScrapersPanel