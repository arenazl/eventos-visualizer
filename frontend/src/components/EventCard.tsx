import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface Event {
  title: string
  description?: string
  start_datetime: string
  venue_name: string
  venue_address?: string
  category: string
  price: number | null | undefined
  currency: string
  is_free: boolean
  image_url: string
  latitude?: number
  longitude?: number
  source?: string
  status?: string
}

interface EventCardProps {
  event: Event
  isFavorite?: boolean
  onToggleFavorite?: (eventId: string) => void
}

const EventCard: React.FC<EventCardProps> = ({
  event,
  isFavorite = false,
  onToggleFavorite
}) => {
  const navigate = useNavigate()
  const [imageError, setImageError] = useState(false)

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Fecha por confirmar'
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Fecha por confirmar'
    
    return date.toLocaleDateString('es-AR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatPrice = (price: number | null | undefined, currency: string, isFree: boolean) => {
    if (isFree) return 'Gratis'
    if (!price || price === 0) return 'Consultar'
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
      'international': 'from-cyan-500 via-blue-500 to-indigo-500',
      'festival': 'from-orange-600 via-amber-500 to-yellow-500',
      'theater': 'from-red-600 via-rose-500 to-pink-500',
      'comedy': 'from-yellow-600 via-amber-500 to-orange-500'
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
      'international': '🌍',
      'festival': '🎪',
      'theater': '🎬',
      'comedy': '😂'
    }
    return icons[category] || '📅'
  }

  const handleCardClick = () => {
    // Usar la misma lógica de generación de ID que EventCardModern
    const eventId = event.title
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // Remover acentos
      .replace(/[^a-z0-9]+/g, '-') // Reemplazar todo lo que no sea letra o número con -
      .replace(/^-+|-+$/g, '') // Remover - al inicio o final
    
    console.log('🔄 EventCard - Clicking event:', event.title)
    console.log('🔄 EventCard - Generated ID:', eventId)
    console.log('🔄 EventCard - SessionStorage key:', `event-${eventId}`)
    
    // Guardar el evento en sessionStorage para que persista
    const storageKey = `event-${eventId}`
    sessionStorage.setItem(storageKey, JSON.stringify(event))
    
    // Verificar que se guardó correctamente
    const saved = sessionStorage.getItem(storageKey)
    console.log('🔄 EventCard - Verified storage:', saved ? 'Saved successfully' : 'Failed to save!')
    
    // NAVEGACIÓN DESHABILITADA - Mantener en la misma página para que Sofia y Juan sigan disponibles
    // navigate(`/evento/${eventId}`, { 
    //   state: { event: event } 
    // })
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    // Usar la misma lógica de generación de ID
    const eventId = event.title
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    onToggleFavorite?.(eventId)
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 max-w-sm">
      {/* Image Section - EXACTO del template */}
      <div className="relative aspect-video">
        {!imageError && event.image_url && event.image_url.trim() !== "" ? (
          <img
            src={event.image_url}
            alt={event.title}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className={`w-full h-full bg-gradient-to-br ${getCategoryGradient(event.category)} flex items-center justify-center`}>
            <span className="text-6xl">{getCategoryIcon(event.category)}</span>
          </div>
        )}
        {/* Category Badge */}
        <div className="absolute top-2 right-2">
          <span className="bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-medium">
            {event.category}
          </span>
        </div>
        {/* Price Badge */}
        <div className="absolute bottom-2 left-2">
          <span className="bg-green-600 text-white px-2 py-1 rounded-lg text-sm font-bold">
            {formatPrice(event.price, event.currency, event.is_free)}
          </span>
        </div>
      </div>
      
      {/* Content Section - EXACTO del template */}
      <div className="p-4">
        {/* Title */}
        <h3 className="font-bold text-lg text-gray-900 mb-2 line-clamp-2">
          {event.title}
        </h3>
        
        {/* Description */}
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {event.description}
        </p>
        
        {/* Date & Location */}
        <div className="flex items-center text-sm text-gray-500 mb-3">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{formatDate(event.start_datetime)}</span>
          <span className="mx-2">•</span>
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
          <span>{event.venue_name}</span>
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-2">
          <button 
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors"
            onClick={handleCardClick}
          >
            Ver Detalles
          </button>
          <button 
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            onClick={handleFavoriteClick}
          >
            <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export default EventCard