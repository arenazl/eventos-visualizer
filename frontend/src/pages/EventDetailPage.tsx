import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import SidePanel from '../components/SidePanel'
import Header from '../components/Header'
import { useAssistants } from '../contexts/AssistantsContext'
import { useEvents } from '../stores/EventsStore'
import { API_BASE_URL } from '../config/api'
import bgImage from '../assets/bg.webp'

interface Event {
  title: string
  description?: string
  start_datetime: string
  venue_name: string
  venue_address?: string
  city?: string
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
  // 🔥 URL format: /event/{uuid}/{slug}
  // uuid = ID real de la DB para operaciones
  // slug = nombre legible para SEO (opcional)
  const { uuid, slug } = useParams<{ uuid: string; slug?: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { triggerDetailRecommendations } = useAssistants()
  const eventsStore = useEvents()
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false)
  const [aiInsight, setAiInsight] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiCalled, setAiCalled] = useState(false) // Flag para evitar llamadas duplicadas
  const [imageUpdateCalled, setImageUpdateCalled] = useState(false) // Flag para evitar loop de auto-update
  const [isScrolled, setIsScrolled] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [updatingCategory, setUpdatingCategory] = useState(false)
  const [updatingImage, setUpdatingImage] = useState(false)
  const [relatedEvents, setRelatedEvents] = useState<Event[]>([])
  const [relatedLoading, setRelatedLoading] = useState(false)

  // Chat de IA flotante
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatResponse, setChatResponse] = useState<{
    answer: string
    relatedEvents: Array<{ id: string; title: string; slug: string; venue: string; date: string }>
  } | null>(null)


  // Handler para actualizar imagen - Definido temprano para ser usado en useEffect
  const handleUpdateImage = useCallback(async () => {
    if (!event || !uuid) return

    setUpdatingImage(true)
    try {
      // 🔥 Usar el UUID del path directamente (ya es el ID real de la DB)
      const eventId = uuid
      console.log('🖼️ Buscando nueva imagen para:', event.title, '| UUID:', eventId)

      const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/update-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: event.title,
          venue_name: event.venue_name,
          city: event.city || '',
          event_id: eventId  // 🆕 También enviar el ID en el body
        })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.image_url) {
          console.log('✅ Nueva imagen encontrada:', data.image_url)

          // Actualizar el evento local
          setEvent({ ...event, image_url: data.image_url })
          setImageError(false)

          // 🔥 ACTUALIZAR EN EL STORE GLOBAL para que se vea en el listado
          // Intentar con múltiples identificadores para asegurar que se encuentre
          const eventSlug = event.title?.toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')

          // Primero intentar con el ID real del evento (si existe)
          if ((event as any).id) {
            eventsStore.updateEventImage((event as any).id, data.image_url)
            console.log('✅ Imagen actualizada en store con ID real:', (event as any).id)
          }
          // También actualizar con el slug por si acaso
          if (eventSlug) {
            eventsStore.updateEventImage(eventSlug, data.image_url)
            console.log('✅ Imagen actualizada en store con slug:', eventSlug)
          }

          // 🧹 Limpiar sessionStorage para forzar datos frescos
          sessionStorage.removeItem(`event-${uuid}`)
          sessionStorage.removeItem(`event-${eventSlug}`)
          console.log('🧹 SessionStorage limpiado para:', uuid)

          // Mostrar si se guardó en la base de datos
          if (data.db_updated) {
            console.log('✅ Imagen guardada en MySQL correctamente')
          } else {
            console.warn('⚠️ Imagen encontrada pero NO guardada en MySQL:', data.message)
          }
        } else {
          console.warn('⚠️ No se encontró nueva imagen')
        }
      } else {
        console.error('❌ Error actualizando imagen')
      }
    } catch (error) {
      console.error('❌ Error:', error)
    } finally {
      setUpdatingImage(false)
    }
  }, [event, uuid])

  useEffect(() => {
    console.log('🔄 EventDetailPage useEffect triggered - UUID changed to:', uuid)
    // 🔄 Reset ALL states when navigating to a new event
    setEvent(null) // Clear previous event to force fresh load
    setImageError(false) // Reset image error when navigating to new event
    setAiCalled(false) // Reset AI flag cuando cambia el evento
    setImageUpdateCalled(false) // Reset image update flag cuando cambia el evento
    setAiInsight(null) // Clear AI insights
    setRelatedEvents([]) // Clear related events
    setChatResponse(null) // Clear chat response
    setLoading(true) // Show loading state
    fetchEventDetails()
  }, [uuid, location.state])

  useEffect(() => {
    if (event && !imageUpdateCalled) {
      fetchAIInsight()

      // Solo auto-actualizar imagen si el evento NO tiene image_url
      if (!event.image_url || event.image_url.trim() === '') {
        console.log('🖼️ Evento sin imagen - Iniciando búsqueda automática...')
        setImageUpdateCalled(true)
        handleUpdateImage()
      } else {
        console.log('✅ Evento ya tiene imagen:', event.image_url.substring(0, 50) + '...')
        setImageUpdateCalled(true) // Marcar como procesado para no volver a verificar
      }

      // DESACTIVADO: Trigger recomendaciones automáticas cada 10 segundos
      // const cleanup = triggerDetailRecommendations(event.title, event.category)
      // return cleanup
    }
  }, [event, imageUpdateCalled])

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
      const response = await fetch(`${API_BASE_URL}/api/ai/event-insight`, {
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
      console.log('🔍 EventDetailPage - Fetching fresh data from API for UUID:', uuid)

      // SIEMPRE fetch desde el backend para obtener datos frescos con imágenes actualizadas
      const response = await fetch(`${API_BASE_URL}/api/events/${uuid}`)

      if (!response.ok) {
        throw new Error(`Event not found: ${response.status}`)
      }

      const data = await response.json()
      const freshEvent = data.event

      console.log('✅ Fresh event data loaded from MySQL:', freshEvent.title)
      console.log('🖼️ Image URL from database:', freshEvent.image_url)

      // Actualizar el estado con datos frescos
      setEvent(freshEvent)

      // Actualizar sessionStorage con datos frescos para uso futuro
      const eventId = freshEvent.title
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')

      sessionStorage.setItem(`event-${eventId}`, JSON.stringify(freshEvent))
      console.log('💾 Updated sessionStorage with fresh data')

    } catch (error) {
      console.error('❌ Error fetching event from API:', error)

      // FALLBACK: Intentar usar datos de navegación o sessionStorage solo si el API falla
      const eventFromState = location.state?.event
      if (eventFromState) {
        console.log('⚠️ Using fallback from navigation state:', eventFromState.title)
        setEvent(eventFromState)
        return
      }

      // Último intento: buscar en sessionStorage
      let storedEvent = sessionStorage.getItem(`event-${uuid}`)
      if (!storedEvent) {
        const decodedUuid = decodeURIComponent(uuid || '')
        storedEvent = sessionStorage.getItem(`event-${decodedUuid}`)
      }

      if (storedEvent) {
        console.log('⚠️ Using fallback from sessionStorage')
        const parsedEvent = JSON.parse(storedEvent)
        setEvent(parsedEvent)
        return
      }

      // Si todo falla, mostrar mensaje de error
      console.error('❌ No data available for event:', uuid)
      setEvent(null)
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

  // Cargar eventos relacionados por categoría y ciudad
  const fetchRelatedEvents = async () => {
    if (!event) return

    setRelatedLoading(true)
    try {
      // Buscar eventos de la misma categoría y/o ciudad
      const params = new URLSearchParams()
      if (event.category) params.append('category', event.category)
      if (event.city) params.append('city', event.city)
      params.append('limit', '6')
      params.append('exclude', uuid || '')

      const response = await fetch(`${API_BASE_URL}/api/events/related?${params.toString()}`)

      if (response.ok) {
        const data = await response.json()
        setRelatedEvents(data.events || [])
      }
    } catch (error) {
      console.error('Error loading related events:', error)
    } finally {
      setRelatedLoading(false)
    }
  }

  // Cargar eventos relacionados cuando el evento principal esté listo
  useEffect(() => {
    if (event && !relatedLoading && relatedEvents.length === 0) {
      fetchRelatedEvents()
    }
  }, [event])

  // Handler para el chat de IA
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatMessage.trim() || chatLoading) return

    setChatLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/chat-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: chatMessage,
          context_event: event ? {
            title: event.title,
            category: event.category,
            city: event.city,
            venue: event.venue_name
          } : null
        })
      })

      if (response.ok) {
        const data = await response.json()
        setChatResponse({
          answer: data.answer || 'No encontré información específica.',
          relatedEvents: data.events || []
        })
      } else {
        setChatResponse({
          answer: 'Hubo un error al procesar tu consulta. Intentá de nuevo.',
          relatedEvents: []
        })
      }
    } catch (error) {
      console.error('Error en chat:', error)
      setChatResponse({
        answer: 'Error de conexión. Verificá tu conexión a internet.',
        relatedEvents: []
      })
    } finally {
      setChatLoading(false)
    }
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

  // Imágenes placeholder por categoría (Unsplash)
  const getDefaultImage = (category: string) => {
    const defaultImages: Record<string, string> = {
      'music': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&h=300&fit=crop',
      'sports': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop',
      'cultural': 'https://images.unsplash.com/photo-1518893063132-36e46dbe2428?w=400&h=300&fit=crop',
      'tech': 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400&h=300&fit=crop',
      'party': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400&h=300&fit=crop',
      'nightlife': 'https://images.unsplash.com/photo-1566737236500-c8ac43014a67?w=400&h=300&fit=crop',
      'hobbies': 'https://images.unsplash.com/photo-1452860606245-08befc0ff44b?w=400&h=300&fit=crop',
      'international': 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop',
      'other': 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=400&h=300&fit=crop'
    }
    return defaultImages[category] || defaultImages['other']
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

  // Handler para actualizar categoría
  const handleCategoryChange = async (newCategory: string) => {
    if (!event || !uuid) return

    setUpdatingCategory(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/${uuid}/category`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: newCategory })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Categoría actualizada:', newCategory)

        // Actualizar el evento local
        setEvent({ ...event, category: newCategory })

        // Actualizar en sessionStorage
        const eventKey = `event-${uuid}`
        const storedEvent = sessionStorage.getItem(eventKey)
        if (storedEvent) {
          const parsedEvent = JSON.parse(storedEvent)
          parsedEvent.category = newCategory
          sessionStorage.setItem(eventKey, JSON.stringify(parsedEvent))
        }
      } else {
        console.error('❌ Error actualizando categoría')
      }
    } catch (error) {
      console.error('❌ Error:', error)
    } finally {
      setUpdatingCategory(false)
    }
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
    <div className="min-h-screen relative">
      {/* Fondo animado con imagen del evento - GLOBAL */}
      {!imageError && event?.image_url && event.image_url.trim() !== "" && (
        <>
          {/* Capa 1: Imagen base con zoom lento - SIN BLUR */}
          <div
            className="fixed inset-0 animated-bg-zoom-global pointer-events-none"
            style={{
              backgroundImage: `url(${event.image_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: 'saturate(1.4)',
              opacity: 0.4,
            }}
          />
          {/* Capa 2: Imagen con paneo - SIN BLUR */}
          <div
            className="fixed inset-0 animated-bg-pan-global pointer-events-none"
            style={{
              backgroundImage: `url(${event.image_url})`,
              backgroundSize: '120% 120%',
              backgroundPosition: 'center',
              filter: 'saturate(1.2)',
              opacity: 0.2,
              mixBlendMode: 'overlay',
            }}
          />
        </>
      )}

      {/* Gradiente azul encima con opacity 0.5 */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-900/50 via-blue-900/50 to-indigo-900/50 pointer-events-none"></div>

      {/* CSS Animations globales */}
      <style>{`
        .animated-bg-zoom-global {
          animation: bgZoomGlobal 25s ease-in-out infinite;
        }
        .animated-bg-pan-global {
          animation: bgPanGlobal 20s ease-in-out infinite;
        }
        @keyframes bgZoomGlobal {
          0%, 100% { transform: scale(1.0); }
          50% { transform: scale(1.1); }
        }
        @keyframes bgPanGlobal {
          0%, 100% { background-position: 30% 30%; }
          25% { background-position: 70% 30%; }
          50% { background-position: 70% 70%; }
          75% { background-position: 30% 70%; }
        }
      `}</style>

      {/* Contenido principal */}
      <div className="relative z-10">
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

      <div>

        {/* Hero Image */}
        <div className="relative h-80 md:h-[500px] w-full mt-16 overflow-hidden">
          {!imageError && event.image_url && event.image_url.trim() !== "" ? (
            <img
              src={event.image_url}
              alt={event.title}
              className="w-full h-full object-cover object-center"
              onError={() => setImageError(true)}
              style={{ objectPosition: 'center 30%' }}
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${getCategoryGradient(event.category)} flex items-center justify-center`}>
              <span className="text-9xl">{getCategoryIcon(event.category)}</span>
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 py-8 -mt-20 relative z-10">
          {/* Background pattern container */}
          <div className="relative">
            {/* Fondo animado - Video YouTube o Imagen */}
            <div
              className="absolute rounded-xl overflow-hidden pointer-events-none"
              style={{
                top: '-40px',
                left: '-40px',
                right: '-40px',
                bottom: '-40px',
                zIndex: 0
              }}
            >
              {/* Imagen animada con efecto de video - muy dinámico */}
              {!imageError && event.image_url && event.image_url.trim() !== "" && (
                <>
                  {/* Capa 1: Imagen base con zoom lento */}
                  <div
                    className="absolute inset-0 animated-bg-zoom"
                    style={{
                      backgroundImage: `url(${event.image_url})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      filter: 'blur(15px) saturate(1.5)',
                      opacity: 0.6,
                    }}
                  />
                  {/* Capa 2: Imagen duplicada con movimiento diferente */}
                  <div
                    className="absolute inset-0 animated-bg-pan"
                    style={{
                      backgroundImage: `url(${event.image_url})`,
                      backgroundSize: '150% 150%',
                      backgroundPosition: 'center',
                      filter: 'blur(25px) saturate(1.3)',
                      opacity: 0.3,
                      mixBlendMode: 'overlay',
                    }}
                  />
                  {/* Capa 3: Efecto de luz/brillo que se mueve */}
                  <div
                    className="absolute inset-0 animated-light-sweep"
                    style={{
                      background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                      backgroundSize: '200% 200%',
                    }}
                  />
                </>
              )}

              {/* CSS Animations más dinámicas - simula video */}
              <style>{`
                .animated-bg-zoom {
                  animation: bgZoom 20s ease-in-out infinite;
                }
                .animated-bg-pan {
                  animation: bgPan 15s ease-in-out infinite;
                }
                .animated-light-sweep {
                  animation: lightSweep 8s ease-in-out infinite;
                }
                @keyframes bgZoom {
                  0%, 100% { transform: scale(1.0); }
                  50% { transform: scale(1.15); }
                }
                @keyframes bgPan {
                  0%, 100% { background-position: 0% 0%; }
                  25% { background-position: 100% 0%; }
                  50% { background-position: 100% 100%; }
                  75% { background-position: 0% 100%; }
                }
                @keyframes lightSweep {
                  0%, 100% { background-position: -100% -100%; opacity: 0; }
                  50% { background-position: 100% 100%; opacity: 1; }
                }
              `}</style>
            </div>

            {/* Content card with opacity */}
            <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 md:p-8">
            {/* Category & Price badges + Edit buttons */}
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                {/* Category dropdown */}
                <select
                  value={event.category}
                  onChange={(e) => handleCategoryChange(e.target.value)}
                  disabled={updatingCategory}
                  className={`bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium border-none outline-none cursor-pointer hover:bg-blue-700 transition-colors ${updatingCategory ? 'opacity-50' : ''}`}
                >
                  <option value="music">Música</option>
                  <option value="sports">Deportes</option>
                  <option value="cultural">Cultural</option>
                  <option value="tech">Tech</option>
                  <option value="party">Fiestas</option>
                  <option value="hobbies">Hobbies</option>
                  <option value="international">Internacional</option>
                  <option value="food">Comida</option>
                  <option value="art">Arte</option>
                  <option value="theater">Teatro</option>
                  <option value="film">Cine</option>
                  <option value="festival">Festival</option>
                </select>

                {/* Update Image button */}
                <button
                  onClick={handleUpdateImage}
                  disabled={updatingImage}
                  className={`bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ${updatingImage ? 'opacity-50 cursor-wait' : ''}`}
                  title="Actualizar imagen"
                >
                  {updatingImage ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="hidden sm:inline">Buscando...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="hidden sm:inline">Actualizar imagen</span>
                    </>
                  )}
                </button>
              </div>

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
          </div>

          {/* ════════════════════════════════════════════════════════════════════════ */}
          {/* SEPARADOR VISUAL - EVENTOS RELACIONADOS */}
          {/* ════════════════════════════════════════════════════════════════════════ */}
          <div className="mt-12 pt-8 border-t border-white/20">
            {/* Título con estilo destacado */}
            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent"></div>
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <span className="text-purple-400">✨</span>
                También te puede interesar
              </h2>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent"></div>
            </div>

            {relatedLoading ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="bg-white/5 backdrop-blur-sm rounded-xl overflow-hidden animate-pulse">
                    <div className="aspect-[4/3] bg-white/10"></div>
                    <div className="p-3">
                      <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-white/10 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : relatedEvents.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {relatedEvents.map((relEvent, index) => (
                  <div
                    key={index}
                    onClick={() => {
                      const eventId = (relEvent as any).id
                      const eventSlug = relEvent.title
                        .toLowerCase()
                        .normalize("NFD")
                        .replace(/[\u0300-\u036f]/g, "")
                        .replace(/[^a-z0-9]+/g, '-')
                        .replace(/^-+|-+$/g, '')
                      // Scroll suave al top antes de navegar
                      window.scrollTo({ top: 0, behavior: 'smooth' })
                      // Pequeño delay para que se vea el scroll antes de cambiar de página
                      setTimeout(() => {
                        navigate(`/event/${eventId}/${eventSlug}`)
                      }, 300)
                    }}
                    className="group bg-white/5 backdrop-blur-sm rounded-xl overflow-hidden cursor-pointer opacity-80 hover:opacity-100 hover:bg-white/15 transition-all duration-500 ease-out hover:scale-[1.05] hover:-translate-y-1 border border-white/10 hover:border-white/30 hover:shadow-xl hover:shadow-purple-500/20"
                  >
                    <div className="aspect-[4/3] relative overflow-hidden">
                      <img
                        src={relEvent.image_url || getDefaultImage(relEvent.category)}
                        alt={relEvent.title}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = getDefaultImage(relEvent.category)
                        }}
                      />
                      {/* Overlay gradient on hover */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      <div className="absolute top-2 left-2 transition-transform duration-300 group-hover:scale-110">
                        <span className={`text-xs px-2 py-1 rounded-full bg-gradient-to-r ${getCategoryGradient(relEvent.category)} text-white font-medium shadow-lg`}>
                          {relEvent.category}
                        </span>
                      </div>
                      {/* Play icon on hover */}
                      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-100 scale-50">
                        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/30">
                          <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    <div className="p-3 transition-all duration-300 group-hover:bg-white/5">
                      <h3 className="text-sm font-semibold text-white line-clamp-2 mb-1 group-hover:text-purple-200 transition-colors duration-300">{relEvent.title}</h3>
                      <p className="text-xs text-white/60 group-hover:text-white/80 transition-colors duration-300">{relEvent.venue_name}</p>
                      {relEvent.start_datetime && (
                        <p className="text-xs text-white/50 mt-1 group-hover:text-white/70 transition-colors duration-300">
                          {new Date(relEvent.start_datetime).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-8 text-center border border-white/10">
                <svg className="w-12 h-12 text-white/30 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <p className="text-white/50">No hay eventos relacionados disponibles</p>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════ */}
      {/* CHAT FLOTANTE - ESQUINA INFERIOR DERECHA */}
      {/* ════════════════════════════════════════════════════════════════════════ */}
      <div className="fixed bottom-4 right-4 z-50">
        {/* Botón para abrir/cerrar */}
        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="w-14 h-14 bg-gradient-to-br from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group hover:scale-110"
          >
            <span className="text-2xl group-hover:scale-110 transition-transform">🤖</span>
          </button>
        )}

        {/* Panel del chat */}
        {chatOpen && (
          <div className="w-80 sm:w-96 bg-black/90 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🤖</span>
                <div>
                  <h3 className="text-sm font-semibold text-white">Preguntá sobre eventos</h3>
                  <p className="text-xs text-white/70">Busco en toda la base</p>
                </div>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
              >
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Contenido del chat */}
            <div className="max-h-80 overflow-y-auto p-4">
              {/* Respuesta */}
              {chatResponse && (
                <div className="mb-3 p-3 bg-white/5 rounded-lg border border-white/10">
                  <p className="text-sm text-white/90 mb-2">{chatResponse.answer}</p>

                  {chatResponse.relatedEvents.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-white/10">
                      <p className="text-xs text-purple-300 mb-2 font-medium">Eventos encontrados:</p>
                      <div className="space-y-1.5 max-h-40 overflow-y-auto">
                        {chatResponse.relatedEvents.map((ev, idx) => (
                          <div
                            key={idx}
                            onClick={() => {
                              setChatOpen(false)
                              window.scrollTo({ top: 0, behavior: 'smooth' })
                              setTimeout(() => navigate(`/event/${ev.id}/${ev.slug}`), 200)
                            }}
                            className="flex items-center gap-2 p-2 bg-white/5 hover:bg-white/10 rounded-lg cursor-pointer transition-colors group"
                          >
                            <span className="text-purple-400 group-hover:text-purple-300">→</span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-white truncate group-hover:text-purple-200">{ev.title}</p>
                              <p className="text-xs text-white/50">{ev.venue} • {ev.date}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Loading */}
              {chatLoading && (
                <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm text-white/70">Buscando...</span>
                  </div>
                </div>
              )}

              {/* Mensaje inicial si no hay respuesta */}
              {!chatResponse && !chatLoading && (
                <div className="text-center py-4">
                  <p className="text-white/50 text-sm">Preguntame sobre cualquier evento</p>
                  <p className="text-white/30 text-xs mt-1">Ej: "rock", "teatro", "córdoba"</p>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-3 border-t border-white/10">
              <form onSubmit={handleChatSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="¿Qué eventos buscás?"
                  className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                  disabled={chatLoading}
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatMessage.trim()}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 py-2 rounded-lg text-sm font-medium transition-all"
                >
                  {chatLoading ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* PANELES IA - Responsivos: Stack en mobile, laterales en desktop */}
      {(aiLoading || aiInsight) && (
        <>
          {/* === MOBILE/TABLET: Stack vertical debajo del contenido === */}
          <div className="xl:hidden max-w-4xl mx-auto px-4 pb-8">
            <div className="space-y-3">
              {aiLoading ? (
                <>
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                      <div className="h-3 w-24 bg-white/20 rounded animate-pulse mb-2"></div>
                      <div className="space-y-1.5">
                        <div className="h-2.5 bg-white/10 rounded animate-pulse"></div>
                        <div className="h-2.5 bg-white/10 rounded w-4/5 animate-pulse"></div>
                      </div>
                    </div>
                  ))}
                </>
              ) : aiInsight && (
                <>
                  {/* Qué esperar */}
                  <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                    <div className="text-xs text-purple-300 mb-1 flex items-center gap-1 font-medium">
                      <span>✨</span> Qué esperar
                    </div>
                    <p className="text-white/80 text-xs leading-relaxed">{aiInsight.quick_insight}</p>
                  </div>

                  {/* Cómo llegar */}
                  <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                    <div className="text-xs text-green-300 mb-1 flex items-center gap-1 font-medium">
                      <span>🚌</span> Cómo llegar
                    </div>
                    <p className="text-white/80 text-xs leading-relaxed">{aiInsight.transport || "Colectivos cercanos disponibles"}</p>
                  </div>

                  {/* Cerca del lugar */}
                  <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                    <div className="text-xs text-orange-300 mb-1 flex items-center gap-1 font-medium">
                      <span>🍽️</span> Cerca del lugar
                    </div>
                    <p className="text-white/80 text-xs leading-relaxed">{aiInsight.nearby || "Bares y restaurantes en la zona"}</p>
                  </div>

                  {/* Tip Pro */}
                  <div className="bg-black/30 backdrop-blur-xl border border-yellow-500/30 rounded-xl p-3 shadow-xl">
                    <div className="text-xs text-yellow-300 mb-1 flex items-center gap-1 font-medium">
                      <span>💡</span> Tip Pro
                    </div>
                    <p className="text-white/80 text-xs leading-relaxed">{aiInsight.pro_tip || "Llegá temprano para mejor ubicación"}</p>
                  </div>

                  {/* Ambiente - opcional */}
                  {aiInsight.vibe && (
                    <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                      <div className="text-xs text-blue-300 mb-1 flex items-center gap-1 font-medium">
                        <span>🎭</span> Ambiente
                      </div>
                      <p className="text-white/80 text-xs leading-relaxed">{aiInsight.vibe}</p>
                    </div>
                  )}

                  {/* Sobre el lugar - opcional */}
                  {aiInsight.venue_tip && (
                    <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-xl">
                      <div className="text-xs text-indigo-300 mb-1 flex items-center gap-1 font-medium">
                        <span>🏛️</span> Sobre el lugar
                      </div>
                      <p className="text-white/80 text-xs leading-relaxed">{aiInsight.venue_tip}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* === DESKTOP XL+: Paneles fijos a los laterales - TAMAÑO REDUCIDO === */}
          {/* Panel izquierdo */}
          <div className="hidden xl:flex flex-col fixed left-4 top-24 w-56 z-20 animate-fade-in-up gap-2">
            {aiLoading ? (
              <>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                    <div className="h-3 w-20 bg-white/20 rounded animate-pulse mb-2"></div>
                    <div className="space-y-1">
                      <div className="h-2.5 bg-white/10 rounded animate-pulse"></div>
                      <div className="h-2.5 bg-white/10 rounded w-4/5 animate-pulse"></div>
                    </div>
                  </div>
                ))}
              </>
            ) : aiInsight && (
              <>
                {/* Qué esperar */}
                <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                  <div className="text-xs text-purple-300 mb-1 flex items-center gap-1.5 font-semibold">
                    <span>✨</span> Qué esperar
                  </div>
                  <p className="text-white/90 text-xs leading-relaxed">{aiInsight.quick_insight}</p>
                </div>

                {/* Cómo llegar */}
                <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                  <div className="text-xs text-green-300 mb-1 flex items-center gap-1.5 font-semibold">
                    <span>🚌</span> Cómo llegar
                  </div>
                  <p className="text-white/90 text-xs leading-relaxed">{aiInsight.transport || "Colectivos cercanos disponibles"}</p>
                </div>

                {/* Ambiente */}
                {aiInsight.vibe && (
                  <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                    <div className="text-xs text-blue-300 mb-1 flex items-center gap-1.5 font-semibold">
                      <span>🎭</span> Ambiente
                    </div>
                    <p className="text-white/90 text-xs leading-relaxed">{aiInsight.vibe}</p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Panel derecho */}
          <div className="hidden xl:flex flex-col fixed right-4 top-24 w-56 z-20 animate-fade-in-up gap-2">
            {aiLoading ? (
              <>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                    <div className="h-3 w-24 bg-white/20 rounded animate-pulse mb-2"></div>
                    <div className="space-y-1">
                      <div className="h-2.5 bg-white/10 rounded animate-pulse"></div>
                      <div className="h-2.5 bg-white/10 rounded w-3/4 animate-pulse"></div>
                    </div>
                  </div>
                ))}
              </>
            ) : aiInsight && (
              <>
                {/* Cerca del lugar */}
                <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                  <div className="text-xs text-orange-300 mb-1 flex items-center gap-1.5 font-semibold">
                    <span>🍽️</span> Cerca del lugar
                  </div>
                  <p className="text-white/90 text-xs leading-relaxed">{aiInsight.nearby || "Bares y restaurantes en la zona"}</p>
                </div>

                {/* Tip Pro */}
                <div className="bg-black/30 backdrop-blur-xl border border-yellow-500/30 rounded-lg p-3 shadow-xl">
                  <div className="text-xs text-yellow-300 mb-1 flex items-center gap-1.5 font-semibold">
                    <span>💡</span> Tip Pro
                  </div>
                  <p className="text-white/90 text-xs leading-relaxed">{aiInsight.pro_tip || "Llegá temprano para mejor ubicación"}</p>
                </div>

                {/* Sobre el lugar */}
                {aiInsight.venue_tip && (
                  <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-xl">
                    <div className="text-xs text-indigo-300 mb-1 flex items-center gap-1.5 font-semibold">
                      <span>🏛️</span> Sobre el lugar
                    </div>
                    <p className="text-white/90 text-xs leading-relaxed">{aiInsight.venue_tip}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}

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
    </div>
  )
}

export default EventDetailPage