import React from 'react'
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

interface SimpleServicesPanelProps {
  scrapersExecution?: ScrapersExecution | null
}

const SimpleServicesPanel: React.FC<SimpleServicesPanelProps> = ({
  scrapersExecution
}) => {
  // Datos del store de eventos (datos reales de timing)
  const { 
    sourceTiming, 
    isStreaming,
    streamingSource,
    events
  } = useEvents()

  // Combinar datos reales de ambas fuentes
  const getServiceRows = () => {
    const services: Array<{
      name: string
      time: number
      eventCount: number
      status: 'activo' | 'completado' | 'fallido' | 'timeout'
    }> = []

    // Datos del store de eventos (timing real)
    sourceTiming.forEach(timing => {
      const eventCount = timing.eventTimes?.length || 0
      services.push({
        name: timing.source,
        time: Math.round(timing.totalTime || 0),
        eventCount,
        status: isStreaming && timing.endTime === undefined ? 'activo' : 
               timing.totalTime ? 'completado' : 'fallido'
      })
    })

    // Datos de scrapers execution (si existen)
    scrapersExecution?.scrapers_info?.forEach(scraper => {
      const existingIndex = services.findIndex(s => s.name === scraper.name.toLowerCase())
      const time = parseFloat(scraper.response_time.replace(/[^0-9.]/g, '')) || 0
      
      if (existingIndex >= 0) {
        // Actualizar datos existentes
        services[existingIndex] = {
          ...services[existingIndex],
          time: Math.round(time),
          eventCount: scraper.events_count,
          status: scraper.status === 'success' ? 'completado' :
                 scraper.status === 'failed' ? 'fallido' : 'timeout'
        }
      } else {
        // Agregar nuevo servicio
        services.push({
          name: scraper.name,
          time: Math.round(time),
          eventCount: scraper.events_count,
          status: scraper.status === 'success' ? 'completado' :
                 scraper.status === 'failed' ? 'fallido' : 'timeout'
        })
      }
    })

    return services
  }

  const serviceRows = getServiceRows()

  // Si no hay datos, no mostrar el panel
  if (serviceRows.length === 0 && !isStreaming) {
    return null
  }

  const getServiceEmoji = (name: string) => {
    switch (name.toLowerCase()) {
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
      case 'timeout': return 'text-yellow-600 bg-yellow-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="w-full mb-4">
      <div className="bg-white/90 backdrop-blur-sm border border-gray-200/70 rounded-lg shadow-sm">
        {/* Header simple */}
        <div className="px-4 py-2 border-b border-gray-200/50 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-500 animate-pulse' : 'bg-blue-500'}`}></div>
              <span className="text-sm font-medium text-gray-700">
                Servicios Ejecutados
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {serviceRows.length} fuentes • {events.length} eventos
            </span>
          </div>
        </div>

        {/* Lista simple de servicios */}
        <div className="divide-y divide-gray-100">
          {serviceRows.map((service) => (
            <div key={service.name} className="px-4 py-3 flex items-center justify-between hover:bg-gray-50/50 transition-colors">
              <div className="flex items-center space-x-3">
                <span className="text-lg">{getServiceEmoji(service.name)}</span>
                <span className="font-medium text-gray-700 capitalize">{service.name}</span>
                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(service.status)}`}>
                  {service.status}
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-right">
                  <span className="font-medium text-gray-900">{service.eventCount}</span>
                  <span className="text-gray-500 ml-1">eventos</span>
                </div>
                <div className="text-right font-mono">
                  <span className="font-medium text-gray-900">{service.time}ms</span>
                </div>
              </div>
            </div>
          ))}

          {/* Mostrar servicio en ejecución si está streaming */}
          {isStreaming && streamingSource && !serviceRows.find(s => s.name === streamingSource) && (
            <div className="px-4 py-3 flex items-center justify-between bg-green-50/50 animate-pulse">
              <div className="flex items-center space-x-3">
                <span className="text-lg">{getServiceEmoji(streamingSource)}</span>
                <span className="font-medium text-gray-700 capitalize">{streamingSource}</span>
                <span className="text-xs px-2 py-1 rounded-full text-green-600 bg-green-100">
                  ejecutando
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-right">
                  <span className="font-medium text-gray-900">0</span>
                  <span className="text-gray-500 ml-1">eventos</span>
                </div>
                <div className="text-right font-mono">
                  <div className="w-4 h-4 border-2 border-green-300 border-t-green-600 rounded-full animate-spin"></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SimpleServicesPanel