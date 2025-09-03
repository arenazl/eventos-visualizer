import React, { useState } from 'react'
import { useEvents } from '../stores/EventsStore'

const ScrapersDetailPanel: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const { 
    sourceTiming, 
    isStreaming,
    streamingSource,
    events
  } = useEvents()

  // Calcular datos simples por servicio
  const getServiceRows = () => {
    return sourceTiming.map(timing => ({
      source: timing.source,
      eventCount: timing.eventTimes?.length || 0,
      totalTime: Math.round(timing.totalTime || 0),
      isActive: isStreaming && timing.endTime === undefined,
      status: isStreaming && timing.endTime === undefined ? 'activo' : 
             timing.totalTime ? 'completado' : 'fallido'
    }))
  }

  const serviceRows = getServiceRows()

  // Si no hay datos, no mostrar el panel
  if (serviceRows.length === 0 && !isStreaming) {
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
      case 'activo': return 'text-green-600 bg-green-100'
      case 'completado': return 'text-blue-600 bg-blue-100'
      case 'fallido': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      {/* Header colapsable con colores de la app */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 backdrop-blur-xl bg-black/40 border border-white/30 rounded-xl hover:bg-black/50 transition-all duration-200 shadow-2xl group"
      >
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-400 animate-pulse' : 'bg-purple-400'}`}></div>
          <span className="font-medium text-sm text-white/90">
            {isStreaming ? '⚡ APIs Ejecutándose' : '📊 Servicios Ejecutados'}
          </span>
        </div>
        
        <div className="flex items-center space-x-3 text-xs">
          {isStreaming && streamingSource && (
            <span className="text-green-300 bg-green-500/20 border border-green-400/30 px-2 py-1 rounded-full font-medium">
              🔄 {streamingSource}
            </span>
          )}
          <span className="font-bold text-white/90">{events.length} eventos</span>
          <span className="text-white/60">
            {serviceRows.length} servicios
          </span>
          <svg
            className={`w-4 h-4 text-white/60 transition-transform duration-200 ${
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

      {/* Panel expandible con colores de la app */}
      {isExpanded && (
        <div className="backdrop-blur-xl bg-black/40 border-l border-r border-b border-white/20 rounded-b-xl shadow-2xl">
          {serviceRows.map((service) => (
            <div key={service.source} className="px-4 py-3 flex items-center justify-between hover:bg-white/10 transition-colors border-b border-white/10 last:border-b-0">
              <div className="flex items-center space-x-3">
                <span className="text-lg">{getServiceEmoji(service.source)}</span>
                <span className="font-medium text-white/90 capitalize">{service.source}</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  service.status === 'activo' ? 'text-green-300 bg-green-500/20 border border-green-400/30' :
                  service.status === 'completado' ? 'text-blue-300 bg-blue-500/20 border border-blue-400/30' :
                  'text-red-300 bg-red-500/20 border border-red-400/30'
                }`}>
                  {service.status}
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-right">
                  <span className="font-bold text-white">{service.eventCount}</span>
                  <span className="text-white/60 ml-1">eventos</span>
                </div>
                <div className="text-right font-mono">
                  <span className="font-bold text-white">{service.totalTime}ms</span>
                </div>
              </div>
            </div>
          ))}

          {/* Mostrar servicio en ejecución si está streaming */}
          {isStreaming && streamingSource && !serviceRows.find(s => s.source === streamingSource) && (
            <div className="px-4 py-3 flex items-center justify-between bg-green-500/20 border border-green-400/30 animate-pulse">
              <div className="flex items-center space-x-3">
                <span className="text-lg">{getServiceEmoji(streamingSource)}</span>
                <span className="font-medium text-white/90 capitalize">{streamingSource}</span>
                <span className="text-xs px-2 py-1 rounded-full text-green-300 bg-green-500/30 border border-green-400/50">
                  ejecutando
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-right">
                  <span className="font-bold text-white">0</span>
                  <span className="text-white/60 ml-1">eventos</span>
                </div>
                <div className="text-right font-mono">
                  <div className="w-4 h-4 border-2 border-green-300/50 border-t-green-400 rounded-full animate-spin"></div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ScrapersDetailPanel