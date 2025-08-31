import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EventAIHover from './EventAIHover'

interface Event {
  title: string
  description: string
  start_datetime: string
  venue_name: string
  venue_address?: string
  category: string
  price: number
  currency: string
  is_free: boolean
  image_url: string
  latitude?: number
  longitude?: number
  source?: string
  status?: string
}

interface EventCardModernProps {
  event: Event
  isFavorite?: boolean
  onToggleFavorite?: (eventId: string) => void
}

const EventCardModern: React.FC<EventCardModernProps> = ({ 
  event, 
  isFavorite = false, 
  onToggleFavorite 
}) => {
  const navigate = useNavigate()
  const [isHovered, setIsHovered] = useState(false)
  const [imageError, setImageError] = useState(false)

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const day = date.getDate()
    const month = date.toLocaleDateString('es-AR', { month: 'short' }).toUpperCase()
    const time = date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    return { day, month, time }
  }

  const formatPrice = (price: number, currency: string, isFree: boolean) => {
    if (isFree) return 'GRATIS'
    return `${currency} ${price.toLocaleString()}`
  }

  const getCategoryGradient = (category: string) => {
    const gradients: Record<string, string> = {
      'music': 'from-purple-600 via-pink-500 to-red-500',
      'sports': 'from-green-600 via-emerald-500 to-teal-500',
      'cultural': 'from-blue-600 via-indigo-500 to-purple-500',
      'tech': 'from-indigo-600 via-blue-500 to-cyan-500',
      'party': 'from-pink-600 via-rose-500 to-orange-500',
      'hobbies': 'from-yellow-500 via-orange-500 to-red-500',
      'international': 'from-cyan-500 via-blue-500 to-indigo-500'
    }
    return gradients[category] || 'from-gray-600 via-gray-500 to-gray-400'
  }

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      'music': '🎵',
      'sports': '⚽',
      'cultural': '🎭',
      'tech': '💻',
      'party': '🎉',
      'hobbies': '🎨',
      'international': '🌍'
    }
    return icons[category] || '📅'
  }

  const { day, month, time } = formatDate(event.start_datetime)

  const handleCardClick = () => {
    // Generar ID basado en título para navegación - mejorado para manejar caracteres especiales
    const eventId = event.title
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // Remover acentos
      .replace(/[^a-z0-9]+/g, '-') // Reemplazar todo lo que no sea letra o número con -
      .replace(/^-+|-+$/g, '') // Remover - al inicio o final
    
    console.log('🔄 EventCard - Clicking event:', event.title)
    console.log('🔄 EventCard - Generated ID:', eventId)
    console.log('🔄 EventCard - SessionStorage key:', `event-${eventId}`)
    console.log('🔄 EventCard - Full event data:', event)
    
    // Guardar el evento en sessionStorage para que persista
    const storageKey = `event-${eventId}`
    sessionStorage.setItem(storageKey, JSON.stringify(event))
    
    // Verificar que se guardó correctamente
    const saved = sessionStorage.getItem(storageKey)
    console.log('🔄 EventCard - Verified storage:', saved ? 'Saved successfully' : 'Failed to save!')
    
    // Pasar los datos del evento a través del state de navegación
    navigate(`/evento/${eventId}`, { 
      state: { event: event } 
    })
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    const eventId = event.title.toLowerCase().replace(/\s+/g, '-').replace(/[.,]/g, '')
    onToggleFavorite?.(eventId)
  }

  return (
    <div 
      className="relative group cursor-pointer transform transition-all duration-500 hover:scale-[1.02]"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
    >
      {/* Glow effect */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${getCategoryGradient(event.category)} rounded-2xl blur-xl opacity-60 group-hover:opacity-100 transition-opacity duration-500`} />
      
      {/* Card content */}
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl overflow-hidden shadow-2xl">
        {/* Image with overlay */}
        <div className="relative h-56 overflow-hidden">
          {!imageError ? (
            <img 
              src={event.image_url} 
              alt={event.title}
              className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${getCategoryGradient(event.category)} flex items-center justify-center`}>
              <span className="text-6xl">{getCategoryIcon(event.category)}</span>
            </div>
          )}
          
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
          
          {/* Date badge */}
          <div className="absolute top-4 left-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md rounded-xl px-3 py-2 shadow-lg">
            <div className="text-center">
              <div className="text-2xl font-black text-gray-900 dark:text-white">{day}</div>
              <div className="text-xs font-bold text-gray-600 dark:text-gray-400">{month}</div>
            </div>
          </div>
          
          {/* Category badge with gradient */}
          <div className="absolute top-4 right-4">
            <div className={`bg-gradient-to-r ${getCategoryGradient(event.category)} px-3 py-1 rounded-full shadow-lg`}>
              <span className="text-white text-xs font-bold uppercase tracking-wider flex items-center gap-1">
                <span>{getCategoryIcon(event.category)}</span>
                <span>{event.category}</span>
              </span>
            </div>
          </div>
          
          {/* Price badge */}
          <div className="absolute bottom-4 left-4">
            <div className={`${event.is_free ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-blue-600 to-indigo-600'} text-white px-4 py-2 rounded-xl font-bold text-sm shadow-lg backdrop-blur-md`}>
              {formatPrice(event.price, event.currency, event.is_free)}
            </div>
          </div>
          
        </div>
        
        {/* Content */}
        <div className="p-5">
          {/* Title with gradient on hover */}
          <h3 className="font-bold text-xl text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-purple-600 group-hover:to-pink-600 transition-all duration-300">
            {event.title}
          </h3>
          
          {/* Description */}
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
            {event.description}
          </p>
          
          {/* Location and time with icons */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <svg className="w-4 h-4 mr-2 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">{time}</span>
            </div>
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <svg className="w-4 h-4 mr-2 text-pink-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <span className="truncate">{event.venue_name}</span>
            </div>
          </div>
          
          {/* Action buttons with gradients */}
          <div className="flex gap-2">
            <button 
              className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white py-2.5 px-4 rounded-xl font-semibold text-sm hover:shadow-lg transform transition-all duration-300 hover:-translate-y-0.5"
              onClick={handleCardClick}
            >
              Ver más
            </button>
            
            <button 
              className={`p-2.5 rounded-xl transition-all duration-300 ${
                isFavorite 
                  ? 'bg-gradient-to-r from-red-500 to-pink-500 text-white shadow-lg' 
                  : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              onClick={handleFavoriteClick}
            >
              <svg className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} fill={isFavorite ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </button>
            
            {/* AI Button - Reemplaza el ícono anterior */}
            <EventAIHover event={{
              id: event.id || Math.random().toString(),
              title: event.title,
              description: event.description,
              location: event.venue_address || 'Buenos Aires'
            }} />
          </div>
        </div>
        
        {/* Hover effect overlay */}
        {isHovered && (
          <div className="absolute inset-0 bg-gradient-to-t from-purple-600/20 to-transparent pointer-events-none animate-pulse" />
        )}
      </div>
    </div>
  )
}

export default EventCardModern