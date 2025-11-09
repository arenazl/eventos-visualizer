import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EventAIHover from './EventAIHover'
import EventDetailOverlay from './EventDetailOverlay'
import { useAssistants } from '../contexts/AssistantsContext'

interface Event {
  title: string
  description?: string
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
  const [defaultImageError, setDefaultImageError] = useState(false)
  const [isShaking, setIsShaking] = useState(false)
  const [showDetailOverlay, setShowDetailOverlay] = useState(false)
  const { triggerEventComment } = useAssistants()

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) {
      return { day: '?', month: 'TBD', time: 'Por confirmar' }
    }
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      return { day: '?', month: 'TBD', time: 'Por confirmar' }
    }
    
    const day = date.getDate()
    const month = date.toLocaleDateString('es-AR', { month: 'short' }).toUpperCase()
    const time = date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    return { day, month, time }
  }

  const formatPrice = (price?: number | null, currency?: string, isFree?: boolean) => {
    if (isFree) return 'GRATIS'
    if (!price || price === 0) return 'CONSULTAR'
    return `${currency || 'ARS'} ${price.toLocaleString()}`
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

  const getDefaultImage = (category: string) => {
    // Imágenes por defecto según categoría usando Unsplash
    const defaultImages: Record<string, string> = {
      'music': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&h=600&fit=crop',
      'sports': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&h=600&fit=crop',
      'cultural': 'https://images.unsplash.com/photo-1518893063132-36e46dbe2428?w=800&h=600&fit=crop',
      'tech': 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&h=600&fit=crop',
      'party': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&h=600&fit=crop',
      'hobbies': 'https://images.unsplash.com/photo-1452860606245-08befc0ff44b?w=800&h=600&fit=crop',
      'international': 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=600&fit=crop'
    }
    return defaultImages[category] || 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&h=600&fit=crop'
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
    
    // Disparar animación de shake
    setIsShaking(true)
    setTimeout(() => setIsShaking(false), 600) // Duración del shake
    
    // Disparar comentario contextual de los asistentes
    triggerEventComment({
      eventTitle: event.title,
      eventCategory: event.category,
      eventType: 'click',
      timestamp: new Date(),
      shouldConverse: Math.random() < 0.1 // 1/10 probabilidad
    })
    
    // Navegar a la página de detalle
    setTimeout(() => {
      navigate(`/event/${eventId}`)
    }, 700) // Después del shake
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    const eventId = event.title.toLowerCase().replace(/\s+/g, '-').replace(/[.,]/g, '')
    onToggleFavorite?.(eventId)
  }

  return (
    <div
      className={`relative group cursor-pointer transform transition-all duration-500 hover:scale-[1.02] ${isShaking ? 'animate-shake' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
    >
      {/* Glow effect */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${getCategoryGradient(event.category)} rounded-xl md:rounded-2xl blur-xl opacity-60 group-hover:opacity-100 transition-opacity duration-500`} />

      {/* Card content - Altura fija para todas las tarjetas */}
      <div className="relative bg-white dark:bg-gray-900 rounded-xl md:rounded-2xl overflow-hidden shadow-2xl h-[420px] sm:h-[450px] md:h-[480px] flex flex-col">
        {/* Image with overlay */}
        <div className="relative h-40 sm:h-48 md:h-56 overflow-hidden flex-shrink-0">
          {defaultImageError ? (
            // Fallback final: gradiente con emoji
            <div className={`w-full h-full bg-gradient-to-br ${getCategoryGradient(event.category)} flex items-center justify-center`}>
              <span className="text-6xl">{getCategoryIcon(event.category)}</span>
            </div>
          ) : (
            <img
              src={(!imageError && event.image_url && event.image_url.trim() !== "") ? event.image_url : getDefaultImage(event.category)}
              alt={event.title}
              className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110"
              onError={() => {
                if (!imageError) {
                  // Primera vez: intentar con imagen por defecto
                  setImageError(true)
                } else {
                  // Segunda vez: usar gradiente
                  setDefaultImageError(true)
                }
              }}
            />
          )}
          
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
          
          {/* Date badge */}
          <div className="absolute top-2 left-2 md:top-4 md:left-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md rounded-lg md:rounded-xl px-2 py-1.5 md:px-3 md:py-2 shadow-lg">
            <div className="text-center">
              <div className="text-xl md:text-2xl font-black text-gray-900 dark:text-white">{day}</div>
              <div className="text-[10px] md:text-xs font-bold text-gray-600 dark:text-gray-400">{month}</div>
            </div>
          </div>

          {/* Category badge with gradient */}
          <div className="absolute top-2 right-2 md:top-4 md:right-4">
            <div className={`bg-gradient-to-r ${getCategoryGradient(event.category)} px-2 py-0.5 md:px-3 md:py-1 rounded-full shadow-lg`}>
              <span className="text-white text-[10px] md:text-xs font-bold uppercase tracking-wider flex items-center gap-1">
                <span className="text-xs md:text-sm">{getCategoryIcon(event.category)}</span>
                <span className="hidden sm:inline">{event.category}</span>
              </span>
            </div>
          </div>

          {/* Price badge */}
          <div className="absolute bottom-2 left-2 md:bottom-4 md:left-4">
            <div className={`${event.is_free ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-blue-600 to-indigo-600'} text-white px-2 py-1 md:px-4 md:py-2 rounded-lg md:rounded-xl font-bold text-xs md:text-sm shadow-lg backdrop-blur-md`}>
              {formatPrice(event.price, event.currency, event.is_free)}
            </div>
          </div>
          
        </div>

        {/* Content - flex-grow para ocupar el espacio restante */}
        <div className="p-3 sm:p-4 md:p-5 flex flex-col flex-grow">
          {/* Title with gradient on hover - altura fija */}
          <h3 className="font-bold text-base sm:text-lg md:text-xl text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-purple-600 group-hover:to-pink-600 transition-all duration-300 h-12 sm:h-13 md:h-14">
            {event.title || 'Sin título'}
          </h3>

          {/* Description - altura fija */}
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3 md:mb-4 line-clamp-2 h-9 sm:h-10">
            {event.description || 'Sin descripción disponible'}
          </p>

          {/* Location and time with icons */}
          <div className="space-y-1.5 sm:space-y-2 mb-3 md:mb-4 flex-shrink-0">
            <div className="flex items-center text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">{time}</span>
            </div>
            <div className="flex items-center text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-pink-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <span className="truncate">{event.venue_name}</span>
            </div>
          </div>

          {/* Spacer para empujar botones al fondo */}
          <div className="flex-grow"></div>

          {/* Action buttons - 80% Ver más + 20% IA */}
          <div className="flex items-center gap-1.5 sm:gap-2 mt-auto flex-shrink-0">
            {/* Ver más - 80% del ancho */}
            <button
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white py-2 sm:py-2.5 px-3 sm:px-4 rounded-lg md:rounded-xl font-semibold text-xs sm:text-sm hover:shadow-lg transform transition-all duration-300 hover:-translate-y-0.5"
              style={{ width: '80%' }}
              onClick={handleCardClick}
            >
              Ver más
            </button>

            {/* AI Button - 20% del ancho */}
            <div style={{ width: '20%' }} className="flex justify-center">
              <EventAIHover event={{
                id: event.source || Math.random().toString(),
                title: event.title,
                venue_name: event.venue_name,
                category: event.category,
                location: event.venue_address || 'Buenos Aires'
              }} />
            </div>
          </div>
        </div>
        
        {/* Botón Corazón Flotante Estilo TikTok */}
        <div className={`absolute inset-0 flex items-center justify-center pointer-events-none transition-all duration-300 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}>
          <button 
            className={`pointer-events-auto transform transition-all duration-500 hover:scale-125 ${
              isHovered ? 'scale-110 animate-pulse' : 'scale-75'
            } ${
              isFavorite 
                ? 'text-red-500' 
                : 'text-white'
            }`}
            onClick={handleFavoriteClick}
          >
            <div className="relative">
              {/* Glow effect */}
              <div className="absolute inset-0 bg-white/20 rounded-full blur-xl"></div>
              {/* Corazón */}
              <svg className={`w-16 h-16 relative z-10 drop-shadow-2xl ${isFavorite ? 'fill-current' : ''}`} 
                   fill={isFavorite ? 'currentColor' : 'none'} 
                   stroke="currentColor" 
                   strokeWidth="2"
                   viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" 
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
          </button>
        </div>
        
      </div>

      {/* Event Detail Overlay */}
      <EventDetailOverlay 
        event={event}
        isOpen={showDetailOverlay}
        onClose={() => setShowDetailOverlay(false)}
      />
    </div>
  )
}

export default EventCardModern