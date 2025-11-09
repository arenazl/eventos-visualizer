import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import SidePanel from '../components/SidePanel'
import Header from '../components/Header'
import { useAssistants } from '../contexts/AssistantsContext'

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

interface LocationSuggestion {
  name: string
  displayName?: string
  country: string
  countryCode?: string
  lat: number
  lon: number
}

const EventDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { triggerDetailRecommendations } = useAssistants()
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false)
  const [aiInsight, setAiInsight] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiCalled, setAiCalled] = useState(false) // Flag para evitar llamadas duplicadas
  const [isScrolled, setIsScrolled] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    console.log('🔄 EventDetailPage useEffect triggered - ID changed to:', id)
    setImageError(false) // Reset image error when navigating to new event
    setAiCalled(false) // Reset AI flag cuando cambia el evento
    fetchEventDetails()
  }, [id, location.state])

  useEffect(() => {
    if (event) {
      fetchAIInsight()
      // DESACTIVADO: Trigger recomendaciones automáticas cada 10 segundos
      // const cleanup = triggerDetailRecommendations(event.title, event.category)
      // return cleanup
    }
  }, [event])

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const fetchAIInsight = async () => {
    if (!event || aiCalled) {
      console.log('⏭️ Skipping AI insight - Already called or no event')
      return
    }

    console.log('🤖 Fetching AI insight for:', event.title)
    setAiCalled(true)
    setAiLoading(true)

    try {
      const response = await fetch('http://localhost:8001/api/ai/event-insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: event.title.toLowerCase().replace(/\s+/g, '-').replace(/[.,]/g, ''),
          title: event.title,
          venue_name: event.venue_name,
          category: event.category,
          location: event.venue_address || 'Buenos Aires'
        })
      })

      const data = await response.json()
      if (data.success) {
        // Mostrar progresivamente cada campo con delay
        const insight = data.insight
        const tempInsight: any = {}

        // Ir agregando campos uno por uno con delay
        const fields = Object.keys(insight)
        for (let i = 0; i < fields.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 150)) // 150ms entre campos
          tempInsight[fields[i]] = insight[fields[i]]
          setAiInsight({ ...tempInsight })
        }

        console.log('✅ AI insight loaded successfully')
      } else {
        console.warn('⚠️ AI insight request unsuccessful:', data)
      }
    } catch (error) {
      console.error('❌ Error fetching AI insight:', error)
    } finally {
      setAiLoading(false)
    }
  }

  const fetchEventDetails = async () => {
    try {
      // 1. Primero intentar usar los datos pasados por navegación
      const eventFromState = location.state?.event
      console.log('🔍 EventDetailPage - URL ID:', id)
      console.log('🔍 EventDetailPage - Navigation State:', location.state)
      console.log('🔍 EventDetailPage - Event from state:', eventFromState)
      
      if (eventFromState) {
        console.log('✅ Using event from navigation state:', eventFromState.title)
        setEvent(eventFromState)
        setLoading(false)
        return
      }

      // 2. Si no hay state, buscar en sessionStorage
      // Primero intentamos con el ID tal cual viene de la URL
      console.log('🔍 Looking for sessionStorage key:', `event-${id}`)
      let storedEvent = sessionStorage.getItem(`event-${id}`)
      
      // Si no se encuentra, intentamos decodificar caracteres especiales
      if (!storedEvent) {
        const decodedId = decodeURIComponent(id || '')
        console.log('🔍 Trying decoded ID:', decodedId)
        storedEvent = sessionStorage.getItem(`event-${decodedId}`)
      }
      
      // También intentamos buscar por todas las keys en sessionStorage
      if (!storedEvent) {
        console.log('🔍 Searching all sessionStorage keys...')
        const allKeys = Object.keys(sessionStorage)
        const eventKeys = allKeys.filter(key => key.startsWith('event-'))
        console.log('🔍 Found event keys in storage:', eventKeys)
        
        // Intentar encontrar una coincidencia parcial
        for (const key of eventKeys) {
          const storedData = sessionStorage.getItem(key)
          if (storedData) {
            const parsedData = JSON.parse(storedData)
            // Generar el mismo ID que generaría EventCardModern
            const generatedId = parsedData.title
              .toLowerCase()
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-+|-+$/g, '')
            
            console.log(`🔍 Comparing: URL ID "${id}" vs Generated "${generatedId}" for "${parsedData.title}"`)
            
            if (generatedId === id) {
              console.log('✅ Found matching event by generated ID!')
              storedEvent = storedData
              break
            }
          }
        }
      }
      
      if (storedEvent) {
        console.log('✅ Using event from sessionStorage')
        const parsedEvent = JSON.parse(storedEvent)
        setEvent(parsedEvent)
        setLoading(false)
        return
      }

      // 3. Si tampoco está en sessionStorage, intentar fetch del backend
      console.log('⚠️ No event data in state or storage, attempting backend fetch...')
      const response = await fetch(`http://localhost:8001/api/events/${id}`)
      if (!response.ok) throw new Error('Event not found')
      const data = await response.json()
      setEvent(data.event)
    } catch (error) {
      console.error('Error fetching event:', error)
      // Si no encuentra el evento, usar datos de ejemplo
      setEvent({
        title: "Festival de Rock en Buenos Aires",
        description: "Gran festival con las mejores bandas locales. Una experiencia única con artistas de renombre nacional e internacional.",
        start_datetime: "2025-01-15T20:00:00",
        venue_name: "Luna Park",
        venue_address: "Av. Madero 470, Buenos Aires",
        category: "music",
        price: 15000.00,
        currency: "ARS",
        is_free: false,
        image_url: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
        latitude: -34.6037,
        longitude: -58.3816
      })
    } finally {
      setLoading(false)
    }
  }

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

  const formatPrice = (price: number | null | undefined, currency: string, isFree: boolean) => {
    if (isFree) return 'Evento Gratuito'
    if (!price || price === 0) return 'Consultar Precio'
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

  // Handlers para el Header
  const handleSearchSubmit = () => {
    // Navegar a home con el query de búsqueda
    if (searchQuery.trim()) {
      navigate('/', { state: { searchQuery: searchQuery.trim() } })
    } else {
      navigate('/')
    }
  }

  const handleVoiceSearch = () => {
    // Navegar a home para búsqueda por voz
    navigate('/')
  }

  const handleLocationSelect = (location: LocationSuggestion) => {
    // Navegar a home con la ubicación seleccionada
    navigate('/', { state: { selectedLocation: location } })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!event) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Evento no encontrado</h2>
          <button
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:underline"
          >
            Volver atrás
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header completo igual que en landing page */}
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearchSubmit={handleSearchSubmit}
        onVoiceSearch={handleVoiceSearch}
        onLocationClick={() => {}}
        onLocationSelect={handleLocationSelect}
        isSearching={loading}
        showBackButton={true}
        onBackClick={() => navigate(-1)}
      />

      <div className="pt-20">

        {/* Hero Image */}
        <div className="relative h-64 md:h-96 w-full">
          {!imageError && event.image_url && event.image_url.trim() !== "" ? (
            <img
              src={event.image_url}
              alt={event.title}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${getCategoryGradient(event.category)} flex items-center justify-center`}>
              <span className="text-9xl">{getCategoryIcon(event.category)}</span>
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 py-8 -mt-20 relative z-10">
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl shadow-lg p-6 md:p-8">
            {/* Category & Price badges */}
            <div className="flex items-center justify-between mb-4">
              <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                {event.category}
              </span>
              <span className={`${event.is_free ? 'bg-green-600' : 'bg-gray-800'} text-white px-4 py-2 rounded-lg font-bold`}>
                {formatPrice(event.price, event.currency, event.is_free)}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {event.title}
            </h1>

            {/* Date & Location */}
            <div className="space-y-3 mb-6">
              <div className="flex items-start space-x-3">
                <svg className="w-6 h-6 text-purple-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <div>
                  <p className="font-medium text-white">Fecha y hora</p>
                  <p className="text-white/70">{formatDate(event.start_datetime)}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <svg className="w-6 h-6 text-pink-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <div>
                  <p className="font-medium text-white">{event.venue_name}</p>
                  <p className="text-white/70">{event.venue_address}</p>
                  {event.latitude && event.longitude && (
                    <a
                      href={`https://maps.google.com/?q=${event.latitude},${event.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm mt-1 inline-block"
                    >
                      Ver en Google Maps →
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="border-t border-white/20 pt-6">
              <h2 className="text-xl font-semibold text-white mb-3">Acerca del evento</h2>
              <p className="text-white/80 leading-relaxed">{event.description}</p>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3 mt-8">
              <button className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3 px-6 rounded-lg font-medium transition-all duration-300 shadow-lg hover:shadow-xl">
                Comprar entradas
              </button>
              <button className="flex-1 bg-white/10 hover:bg-white/20 border border-white/30 text-white py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                <span>Guardar</span>
              </button>
              <button className="flex-1 bg-white/10 hover:bg-white/20 border border-white/30 text-white py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.032 4.026A9.001 9.001 0 1112 3a9.001 9.001 0 015.716 14.026m-7.432-2.368A3 3 0 1115 12a3 3 0 01-5.716 2.658z" />
                </svg>
                <span>Compartir</span>
              </button>
            </div>
          </div>

          {/* Sección de IA - Moderna sin header duplicado */}
          <div className="mt-6 animate-fade-in-up">
            {aiLoading ? (
              <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl shadow-lg p-6 border-l-4 border-purple-500 relative overflow-hidden">
                {/* Shimmer effect overlay */}
                <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>

                {/* Header skeleton */}
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-8 h-8 bg-white/20 rounded animate-pulse"></div>
                  <div className="h-6 w-48 bg-white/20 rounded animate-pulse"></div>
                  <div className="ml-auto h-6 w-32 bg-purple-500/20 rounded-full animate-pulse"></div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Columna izquierda - Skeletons */}
                  <div className="space-y-4">
                    {/* Qué esperar skeleton */}
                    <div className="bg-purple-500/20 backdrop-blur-sm p-4 rounded-xl border border-purple-400/30 relative overflow-hidden">
                      <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-purple-400/20 to-transparent"></div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 bg-purple-300/30 rounded animate-pulse"></div>
                        <div className="h-4 w-24 bg-purple-300/30 rounded animate-pulse"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 bg-white/10 rounded animate-pulse"></div>
                        <div className="h-3 bg-white/10 rounded w-5/6 animate-pulse"></div>
                      </div>
                    </div>

                    {/* Cómo llegar skeleton */}
                    <div className="bg-green-500/20 backdrop-blur-sm p-4 rounded-xl border border-green-400/30 relative overflow-hidden">
                      <div className="absolute inset-0 animate-shimmer [animation-delay:0.3s] bg-gradient-to-r from-transparent via-green-400/20 to-transparent"></div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 bg-green-300/30 rounded animate-pulse"></div>
                        <div className="h-4 w-28 bg-green-300/30 rounded animate-pulse"></div>
                      </div>
                      <div className="h-3 bg-white/10 rounded w-4/6 animate-pulse"></div>
                    </div>
                  </div>

                  {/* Columna derecha - Skeletons */}
                  <div className="space-y-4">
                    {/* Cerca del lugar skeleton */}
                    <div className="bg-orange-500/20 backdrop-blur-sm p-4 rounded-xl border border-orange-400/30 relative overflow-hidden">
                      <div className="absolute inset-0 animate-shimmer [animation-delay:0.6s] bg-gradient-to-r from-transparent via-orange-400/20 to-transparent"></div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 bg-orange-300/30 rounded animate-pulse"></div>
                        <div className="h-4 w-32 bg-orange-300/30 rounded animate-pulse"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 bg-white/10 rounded animate-pulse"></div>
                        <div className="h-3 bg-white/10 rounded w-3/4 animate-pulse"></div>
                      </div>
                    </div>

                    {/* Tip Pro skeleton */}
                    <div className="bg-yellow-500/20 backdrop-blur-sm p-4 rounded-xl border-l-4 border-yellow-400 relative overflow-hidden">
                      <div className="absolute inset-0 animate-shimmer [animation-delay:0.9s] bg-gradient-to-r from-transparent via-yellow-400/20 to-transparent"></div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 bg-yellow-300/30 rounded animate-pulse"></div>
                        <div className="h-4 w-20 bg-yellow-300/30 rounded animate-pulse"></div>
                      </div>
                      <div className="h-3 bg-white/10 rounded w-5/6 animate-pulse"></div>
                    </div>
                  </div>
                </div>

                {/* Footer skeleton */}
                <div className="mt-6 pt-4 border-t border-white/20 flex justify-between items-center">
                  <div className="h-4 w-40 bg-white/10 rounded animate-pulse"></div>
                  <div className="h-4 w-32 bg-purple-300/20 rounded animate-pulse"></div>
                </div>
              </div>
            ) : aiInsight ? (
              <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                <div className="flex items-center gap-2 mb-6">
                  <span className="text-2xl">✨</span>
                  <h3 className="text-lg font-semibold text-white">Análisis Inteligente</h3>
                  <span className="ml-auto text-xs text-purple-300 bg-purple-500/20 px-2 py-1 rounded-full">Powered by Gemini AI</span>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Columna izquierda */}
                  <div className="space-y-4">
                    {/* Qué esperar */}
                    <div className="bg-purple-500/20 backdrop-blur-sm p-4 rounded-xl border border-purple-400/30">
                      <h3 className="font-bold text-purple-300 mb-2 flex items-center gap-2">
                        <span>🎯</span>
                        Qué esperar
                      </h3>
                      <p className="text-white/90">{aiInsight.quick_insight}</p>
                    </div>

                    {/* Info del artista */}
                    {aiInsight.artist_info && (
                      <div className="bg-blue-500/20 backdrop-blur-sm p-4 rounded-xl border border-blue-400/30">
                        <h3 className="font-bold text-blue-300 mb-2 flex items-center gap-2">
                          <span>🎤</span>
                          Sobre el artista
                        </h3>
                        <p className="text-white/90">{aiInsight.artist_info}</p>
                      </div>
                    )}

                    {/* Cómo llegar */}
                    <div className="bg-green-500/20 backdrop-blur-sm p-4 rounded-xl border border-green-400/30">
                      <h3 className="font-bold text-green-300 mb-2 flex items-center gap-2">
                        <span>🚌</span>
                        Cómo llegar
                      </h3>
                      <p className="text-white/90">{aiInsight.transport || "Colectivos 60, 152, 29"}</p>
                    </div>
                  </div>

                  {/* Columna derecha */}
                  <div className="space-y-4">
                    {/* Cerca del lugar */}
                    <div className="bg-orange-500/20 backdrop-blur-sm p-4 rounded-xl border border-orange-400/30">
                      <h3 className="font-bold text-orange-300 mb-2 flex items-center gap-2">
                        <span>📍</span>
                        Cerca del lugar
                      </h3>
                      <p className="text-white/90">{aiInsight.nearby || "Bares y restaurantes"}</p>
                    </div>

                    {/* Sobre el lugar */}
                    {aiInsight.venue_tip && (
                      <div className="bg-indigo-500/20 backdrop-blur-sm p-4 rounded-xl border border-indigo-400/30">
                        <h3 className="font-bold text-indigo-300 mb-2 flex items-center gap-2">
                          <span>🏛️</span>
                          Sobre el lugar
                        </h3>
                        <p className="text-white/90">{aiInsight.venue_tip}</p>
                      </div>
                    )}

                    {/* Tip Pro */}
                    <div className="bg-yellow-500/20 backdrop-blur-sm p-4 rounded-xl border-l-4 border-yellow-400">
                      <h3 className="font-bold text-yellow-300 mb-2 flex items-center gap-2">
                        <span>💡</span>
                        Tip Pro
                      </h3>
                      <p className="text-white/90">{aiInsight.pro_tip || "Llegá 30 min antes"}</p>
                    </div>
                  </div>
                </div>

                {/* Footer de la sección IA */}
                {aiInsight && (
                  <div className="mt-6 pt-4 border-t border-white/20 flex justify-between items-center">
                    <div className="text-sm text-white/70">
                      Ambiente: <span className="font-semibold text-white">{aiInsight.vibe || "Copado"}</span>
                    </div>
                    <div className="text-xs text-purple-300 flex items-center gap-1">
                      <span>✨</span>
                      <span>Powered by Gemini AI</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl shadow-lg p-8">
                <div className="text-center py-8">
                  <p className="text-white/70">No se pudo obtener información inteligente para este evento</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Side Panel para edición */}
      <SidePanel
        isOpen={isEditPanelOpen}
        onClose={() => setIsEditPanelOpen(false)}
        title="Editar evento"
        width="lg"
      >
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Título del evento
            </label>
            <input
              type="text"
              defaultValue={event.title}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descripción
            </label>
            <textarea
              rows={4}
              defaultValue={event.description}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Precio
              </label>
              <input
                type="number"
                defaultValue={event.price}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Categoría
              </label>
              <select
                defaultValue={event.category}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="music">Música</option>
                <option value="sports">Deportes</option>
                <option value="cultural">Cultural</option>
                <option value="tech">Tecnología</option>
                <option value="party">Fiestas</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Lugar
            </label>
            <input
              type="text"
              defaultValue={event.venue_name}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dirección
            </label>
            <input
              type="text"
              defaultValue={event.venue_address}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_free"
              defaultChecked={event.is_free}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_free" className="ml-2 block text-sm text-gray-900">
              Evento gratuito
            </label>
          </div>

          <div className="pt-6 border-t flex space-x-3">
            <button
              type="button"
              onClick={() => setIsEditPanelOpen(false)}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
            >
              Guardar cambios
            </button>
            <button
              type="button"
              onClick={() => setIsEditPanelOpen(false)}
              className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 py-2 px-4 rounded-lg font-medium transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </SidePanel>
    </div>
  )
}

export default EventDetailPage