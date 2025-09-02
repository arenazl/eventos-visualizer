import React from 'react'

interface Event {
  title: string
  description: string
  start_datetime?: string | null
  venue_name: string
  venue_address?: string
  category: string
  price?: number | null
  currency?: string
  is_free?: boolean
  image_url?: string | null
  latitude?: number
  longitude?: number
  source?: string
  status?: string
}

interface EventDetailOverlayProps {
  event: Event | null
  isOpen: boolean
  onClose: () => void
}

const EventDetailOverlay: React.FC<EventDetailOverlayProps> = ({ event, isOpen, onClose }) => {
  if (!isOpen || !event) return null

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Fecha por confirmar'
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Fecha por confirmar'
    
    return date.toLocaleDateString('es-AR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatPrice = () => {
    if (event.is_free) return 'Entrada libre'
    if (event.price && event.price > 0) {
      return `${event.currency || 'ARS'} ${event.price.toLocaleString()}`
    }
    return 'Precio por confirmar'
  }

  const getCategoryEmoji = (category: string) => {
    const icons: Record<string, string> = {
      'música': '🎵', 'music': '🎵',
      'deportes': '⚽', 'sports': '⚽',
      'cultural': '🎭', 'culture': '🎭',
      'tech': '💻', 'technology': '💻',
      'party': '🎉',
      'hobbies': '🎨',
      'international': '🌍'
    }
    return icons[category.toLowerCase()] || '📅'
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal - Hasta mitad de pantalla */}
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl w-full max-w-4xl mx-4 h-[50vh] overflow-hidden shadow-2xl flex flex-col">
        {/* Contenido superior - Info del evento */}
        <div className="flex-1 overflow-y-auto">
          {/* Header compacto */}
          <div className="relative h-32 overflow-hidden">
            {event.image_url ? (
              <img 
                src={event.image_url} 
                alt={event.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <span className="text-4xl">{getCategoryEmoji(event.category)}</span>
              </div>
            )}
            
            {/* Botón cerrar */}
            <button
              onClick={onClose}
              className="absolute top-2 right-2 w-8 h-8 bg-black/50 text-white rounded-full flex items-center justify-center hover:bg-black/70 transition-colors text-sm"
            >
              ✕
            </button>
          </div>

          {/* Info del evento */}
          <div className="p-4">
            {/* Título */}
            <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {event.title}
            </h1>

            {/* Categoría y fecha */}
            <div className="flex items-center gap-3 mb-3 text-sm">
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full font-medium text-xs">
                {getCategoryEmoji(event.category)} {event.category}
              </span>
              <span className="text-gray-600 dark:text-gray-400 text-xs">
                📅 {formatDate(event.start_datetime)}
              </span>
            </div>

            {/* Info compacta */}
            <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
              {/* Venue */}
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">📍 Ubicación</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  {event.venue_name}
                </p>
              </div>

              {/* Precio */}
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">💰 Precio</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  {formatPrice()}
                </p>
              </div>
            </div>

            {/* Recomendaciones MOVIDAS AQUÍ - Más arriba */}
            <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-xl mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                🎯 Eventos Similares Recomendados
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {/* Recomendaciones simuladas por ahora */}
                <div className="bg-white dark:bg-gray-700 rounded-lg p-2 text-center">
                  <div className="text-lg mb-1">🎭</div>
                  <div className="text-xs font-medium text-gray-800 dark:text-white">Teatro San Martín</div>
                  <div className="text-xs text-gray-500">Mañana 20:00</div>
                </div>
                <div className="bg-white dark:bg-gray-700 rounded-lg p-2 text-center">
                  <div className="text-lg mb-1">🎵</div>
                  <div className="text-xs font-medium text-gray-800 dark:text-white">Concierto Jazz</div>
                  <div className="text-xs text-gray-500">Sábado 21:00</div>
                </div>
                <div className="bg-white dark:bg-gray-700 rounded-lg p-2 text-center">
                  <div className="text-lg mb-1">🎨</div>
                  <div className="text-xs font-medium text-gray-800 dark:text-white">Expo MALBA</div>
                  <div className="text-xs text-gray-500">Todo el mes</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default EventDetailOverlay