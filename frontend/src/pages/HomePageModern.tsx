import React, { useState, useEffect } from 'react'
import EventCardModern from '../components/EventCardModern'
import SmartLocationBar from '../components/SmartLocationBar'
import AIRecommendations, { NoResultsWithAI } from '../components/AIRecommendations'
import { EventsGridSkeleton, EmptyState } from '../components/LoadingStates'
import { useEvents } from '../stores/EventsStore'

interface Location {
  name: string
  coordinates?: { lat: number; lng: number }
  country?: string
  detected: 'gps' | 'manual' | 'prompt' | 'fallback'
}

const HomePageModern: React.FC = () => {
  const { 
    events, 
    loading, 
    currentLocation, 
    aiRecommendations,
    lastQuery,
    fetchEvents, 
    aiSearch,
    searchEvents, 
    setLocation,
    // WebSocket streaming
    isStreaming,
    streamingProgress,
    streamingMessage,
    streamingSource,
    
    // Performance metrics
    sourceTiming,
    performanceStats,
    startStreamingSearch,
    stopStreaming
  } = useEvents()
  const [isScrolled, setIsScrolled] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('Todos')
  const [locationDetected, setLocationDetected] = useState(false)

  // Detectar ubicación automáticamente al cargar
  useEffect(() => {
    const detectAndLoadEvents = async () => {
      if (!locationDetected) {
        // Usar ubicación inicial más amplia: Argentina
        const initialLocation = {
          name: 'Argentina',
          coordinates: { lat: -34.6037, lng: -58.3816 },
          country: 'Argentina',
          detected: 'initial' as const
        }
        
        setLocation(initialLocation)
        setLocationDetected(true)
        
        // Solo UNA llamada inicial con ubicación amplia
        await fetchEvents(initialLocation)
        
        // Detectar ubicación específica después (sin recargar eventos)
        try {
          const { EventsAPI } = await import('../services/api')
          const specificLocation = await EventsAPI.getBestLocation()
          
          // Solo actualizar ubicación para futuros cambios manuales
          setLocation({
            name: specificLocation.display_name,
            coordinates: { lat: specificLocation.latitude, lng: specificLocation.longitude },
            country: specificLocation.country,
            detected: 'gps'
          })
        } catch (error) {
          console.error('Error detecting specific location:', error)
          // Ya tenemos Argentina cargado, no hacer nada más
        }
      }
    }

    detectAndLoadEvents()
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Handlers para ubicación y búsqueda
  const handleLocationChange = (location: Location) => {
    setLocation(location)
    // Solo buscar eventos si el usuario cambió manualmente la ubicación
    // y es diferente a la actual
    if (location.name !== currentLocation?.name) {
      if (activeCategory === 'Todos') {
        fetchEvents(location)
      } else {
        // Re-aplicar filtro de categoría activa con nueva ubicación
        handleCategoryClick(activeCategory)
      }
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    try {
      // Detectar si el query menciona una ciudad
      const cities = ['córdoba', 'cordoba', 'mendoza', 'rosario', 'la plata', 'mar del plata', 
                     'salta', 'tucumán', 'tucuman', 'bariloche', 'neuquén', 'neuquen',
                     'santa fe', 'bahía blanca', 'bahia blanca', 'chile', 'uruguay', 'brasil']
      
      const queryLower = searchQuery.toLowerCase()
      const hasCityInQuery = cities.some(city => queryLower.includes(city))
      
      // Si el query contiene una ciudad, NO enviar location para que el backend la detecte
      const locationToSend = hasCityInQuery ? undefined : currentLocation?.name
      
      // Usar búsqueda inteligente del backend
      const { EventsAPI } = await import('../services/api')
      const result = await EventsAPI.smartSearch(
        searchQuery, 
        locationToSend
      )
      
      // Si detectó ubicación en la query, actualizar
      if (result.detected_location && result.detected_location !== currentLocation?.name) {
        setLocation({
          name: result.detected_location,
          detected: 'manual'
        })
      }
      
      // Actualizar eventos con los resultados
      if (result.results && result.results.length > 0) {
        // Aquí deberías actualizar el store con los nuevos eventos
        // Por ahora solo los mostramos
        console.log('Smart search results:', result)
        // Simulamos actualización del store
        await searchEvents(searchQuery, currentLocation)
      }
    } catch (error) {
      console.error('Search failed:', error)
      // Fallback a búsqueda AI si falla
      await aiSearch(searchQuery, currentLocation)
    }
  }

  const handleVoiceSearch = () => {
    if ('speechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      
      recognition.lang = 'es-AR'
      recognition.continuous = false
      recognition.interimResults = false

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        setSearchQuery(transcript)
        // Usar streaming también para búsqueda por voz
        setTimeout(() => startStreamingSearch(currentLocation), 500)
      }

      recognition.start()
    }
  }

  // Handler para seguimientos de IA
  const handleFollowUpClick = (question: string) => {
    setSearchQuery(question)
    setTimeout(() => aiSearch(question, currentLocation), 300)
  }

  // Handler para categorías - AI-first con fallback
  const handleCategoryClick = async (category: string) => {
    setActiveCategory(category)
    
    if (category === 'Todos') {
      // Buscar todos los eventos en ubicación actual
      setSearchQuery('Todos los eventos')
      await fetchEvents(currentLocation)
    } else {
      // Búsqueda específica por categoría
      const categoryQueries = {
        'Música': 'música rock concierto',
        'Deportes': 'fútbol deporte partido',
        'Cultural': 'teatro arte cultura',
        'Tech': 'tecnología hackathon',
        'Fiestas': 'fiesta party after'
      }
      
      const searchQuery = categoryQueries[category] || category.toLowerCase()
      setSearchQuery(searchQuery)
      
      // Intentar AI primero, luego fallback a búsqueda tradicional
      try {
        const result = await aiSearch(searchQuery, currentLocation)
        // Si AI no devuelve resultados, usar búsqueda tradicional
        if (!result || events.length === 0) {
          setTimeout(() => {
            searchEvents(searchQuery, currentLocation)
          }, 500)
        }
      } catch (error) {
        // Fallback directo a búsqueda tradicional
        searchEvents(searchQuery, currentLocation)
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* TOP BAR */}
      <nav className={`fixed top-0 left-0 right-0 z-50 backdrop-blur-3xl bg-white/5 transition-all duration-300 ${isScrolled ? 'py-2' : 'py-4'}`}>
        <div className="container mx-auto px-6">
          <div className="flex justify-center items-center">
            <div className="text-center">
              <h1 className={`font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 tracking-wider transition-all duration-300 ${
                isScrolled ? 'text-3xl' : 'text-5xl'
              }`}>
                FanAroundYou
              </h1>
              
              {/* Performance stats debajo del logo */}
              {performanceStats.fastestSource && (
                <div className="mt-2 text-xs text-white/60 space-y-1">
                  <div className="flex justify-center gap-4 text-xs">
                    <span>🏆 Más rápido: {performanceStats.fastestSource} ({Math.round(performanceStats.fastestTime || 0)}ms)</span>
                    {performanceStats.slowestSource && (
                      <span>🐌 Más lento: {performanceStats.slowestSource} ({Math.round(performanceStats.slowestTime || 0)}ms)</span>
                    )}
                  </div>
                  
                  {/* Timing detallado de cada fuente */}
                  {sourceTiming.length > 0 && (
                    <div className="flex justify-center gap-2 flex-wrap mt-1">
                      {sourceTiming.map((timing) => {
                        if (timing.eventTimes.length === 0) return null
                        const emoji = timing.source === 'eventbrite' ? '🎫' : 
                                     timing.source === 'facebook' ? '🔥' : 
                                     timing.source === 'instagram' ? '📸' : 
                                     timing.source === 'argentina_venues' ? '🏛️' : '🔍'
                        return (
                          <span key={timing.source} className="bg-black/20 px-2 py-1 rounded-full text-xs">
                            {emoji} {timing.eventTimes.length} eventos - {Math.round(timing.totalTime || 0)}ms
                          </span>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* CONTENIDO PRINCIPAL */}
      <main className="pt-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Smart Location Bar */}
          <SmartLocationBar 
            onLocationChange={handleLocationChange}
            currentLocation={currentLocation}
          />

          {/* Search Bar */}
          <div className="mb-12 text-center">
            <p className="text-xl text-white/80 mb-8">
              {currentLocation 
                ? `Descubre experiencias únicas en ${currentLocation.name} ✨`
                : "Descubre experiencias únicas ✨"
              }
            </p>
            
            <div className="max-w-4xl mx-auto">
              <div className="relative group">
                <div className="absolute -inset-2 bg-gradient-to-r from-purple-600 via-pink-600 to-cyan-600 rounded-3xl blur-2xl opacity-50 group-hover:opacity-75 transition-all duration-500 animate-pulse"></div>
                <div className="relative bg-black/40 backdrop-blur-xl border border-white/30 rounded-3xl p-3 shadow-2xl">
                  <div className="flex items-center gap-3">
                    <div className="pl-4">
                      <svg className="w-7 h-7 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                      </svg>
                    </div>
                    <input 
                      type="text" 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                      placeholder="🔥 ¿Qué obra hay para ver? ¿Eventos en Chile? ¡Pregunta!" 
                      className="flex-1 bg-transparent text-white text-lg placeholder-white/40 py-5 outline-none font-medium"
                    />
                    <button 
                      onClick={handleVoiceSearch}
                      className="p-4 rounded-2xl transition-all duration-300 bg-white/10 hover:bg-white/20 hover:scale-110"
                      title="Búsqueda por voz"
                    >
                      <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                      </svg>
                    </button>
                    
                    {/* Botón de búsqueda con ícono únicamente */}
                    <button 
                      onClick={() => startStreamingSearch(currentLocation)}
                      disabled={loading || isStreaming}
                      className="p-4 rounded-2xl transition-all duration-300 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 hover:scale-110 shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Buscar eventos"
                    >
                      {isStreaming ? (
                        <div className="w-7 h-7 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Category Filters */}
          <div className="mb-10">
            <div className="flex flex-wrap justify-center gap-3">
              {['Todos', 'Música', 'Deportes', 'Cultural', 'Tech', 'Fiestas'].map((category, index) => {
                const gradients = {
                  'Todos': 'from-gray-600 to-gray-400',
                  'Música': 'from-purple-600 via-pink-500 to-red-500',
                  'Deportes': 'from-green-600 via-emerald-500 to-teal-500',
                  'Cultural': 'from-blue-600 via-indigo-500 to-purple-500',
                  'Tech': 'from-indigo-600 via-blue-500 to-cyan-500',
                  'Fiestas': 'from-pink-600 via-rose-500 to-orange-500'
                }
                const emojis = {
                  'Todos': '✨',
                  'Música': '🎵',
                  'Deportes': '⚽',
                  'Cultural': '🎭',
                  'Tech': '💻',
                  'Fiestas': '🎉'
                }
                const isActive = activeCategory === category

                return (
                  <button 
                    key={category}
                    onClick={() => handleCategoryClick(category)}
                    className={`group relative transition-all duration-300 ${isActive ? 'scale-110' : ''}`}
                  >
                    <div className={`absolute -inset-1 bg-gradient-to-r ${gradients[category]} rounded-full blur opacity-60 group-hover:opacity-100 transition-opacity`}></div>
                    <div className={`relative px-6 py-3 rounded-full font-semibold transition-all ${
                      isActive 
                        ? `bg-gradient-to-r ${gradients[category]} text-white shadow-lg`
                        : 'bg-white/10 backdrop-blur-lg text-white hover:bg-white/20'
                    }`}>
                      <span className="mr-2">{emojis[category]}</span>
                      {category}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* AI Recommendations */}
          {aiRecommendations && lastQuery && (
            <AIRecommendations
              recommendations={aiRecommendations}
              originalQuery={lastQuery}
              onFollowUpClick={handleFollowUpClick}
            />
          )}

          {/* No Results with AI Suggestions */}
          {!loading && events.length === 0 && lastQuery && aiRecommendations?.alternative_suggestions && (
            <NoResultsWithAI
              query={lastQuery}
              suggestions={aiRecommendations.alternative_suggestions}
              onSuggestionClick={handleFollowUpClick}
            />
          )}

          {/* Events Stats */}
          <div className="mb-8 flex justify-center">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl px-6 py-3 inline-flex items-center gap-6">
              <div className="text-white">
                <span className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                  {events.length}
                </span>
                <span className="ml-2 text-white/60">eventos encontrados</span>
              </div>
              <div className="h-6 w-px bg-white/20"></div>
              <div className="text-white">
                <span className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                  0
                </span>
                <span className="ml-2 text-white/60">favoritos</span>
              </div>
            </div>
          </div>

          {/* Progreso con información completa pero más finito */}
          {isStreaming && (
            <div className="mb-3 -mt-2">
              {/* Línea de progreso fina */}
              <div className="w-full bg-white/10 rounded-full h-0.5 overflow-hidden mb-2">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 transition-all duration-300 ease-out"
                  style={{ width: `${streamingProgress}%` }}
                ></div>
              </div>
              
              {/* Info completa pero más chiquitita */}
              <div className="bg-black/15 backdrop-blur-sm rounded-lg px-3 py-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    {streamingSource && (
                      <span className="text-sm">
                        {streamingSource === 'eventbrite' ? '🎫' : 
                         streamingSource === 'facebook' ? '🔥' : 
                         streamingSource === 'instagram' ? '📸' : 
                         streamingSource === 'argentina_venues' ? '🏛️' : 
                         streamingSource === 'meetup' ? '👥' : 
                         streamingSource === 'ticketmaster' ? '🎪' : '🔍'}
                      </span>
                    )}
                    <span className="text-white/70 text-xs">
                      {streamingMessage || 'Buscando eventos...'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Circulito moderno con contador */}
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center animate-pulse">
                      {events.length}
                    </div>
                    <span className="text-white/50 text-xs">{Math.round(streamingProgress)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Events Grid */}
          {loading && !isStreaming ? (
            <EventsGridSkeleton />
          ) : events.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">
                  Eventos encontrados ({events.length})
                </h2>
                {isStreaming && (
                  <div className="flex items-center gap-2 text-white/60">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm">Buscando más...</span>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
                {events.map((event, index) => (
                  <div
                    key={event.title + '-' + index}
                    className="opacity-0 animate-fade-in-up"
                    style={{
                      animationDelay: `${(index % 6) * 0.1}s`,
                      animationFillMode: 'forwards'
                    }}
                  >
                    <EventCardModern event={event} />
                  </div>
                ))}
                
                {/* Show skeleton cards while streaming */}
                {isStreaming && (
                  <>
                    {Array.from({ length: 3 }).map((_, index) => (
                      <div key={`skeleton-${index}`} className="animate-pulse">
                        <div className="relative group">
                          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-cyan-600/20 rounded-2xl blur opacity-30"></div>
                          <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
                            <div className="w-full h-48 bg-white/10 rounded-xl mb-4"></div>
                            <div className="h-6 bg-white/15 rounded-lg mb-3"></div>
                            <div className="h-4 bg-white/10 rounded-lg w-3/4 mb-4"></div>
                            <div className="flex justify-between items-center">
                              <div className="h-6 bg-white/15 rounded-lg w-20"></div>
                              <div className="w-8 h-8 bg-white/10 rounded-full"></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          ) : !lastQuery ? (
            <EmptyState 
              message="🧠 ¡Usa la búsqueda inteligente para encontrar eventos increíbles!"
              submessage="Pregunta lo que quieras: 'shows de rock', 'eventos en Chile', 'algo divertido para mañana'"
            />
          ) : null}
        </div>
      </main>

      {/* Floating AI Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button className="group relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 via-pink-600 to-cyan-600 rounded-full blur-lg opacity-75 group-hover:opacity-100 transition-all animate-pulse"></div>
          <div className="relative bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 rounded-full shadow-2xl hover:shadow-3xl transition-all">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 010 2h-1v1a3 3 0 01-3 3h-1v1a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1h-4v1a1 1 0 01-1 1H8a1 1 0 01-1-1v-1H6a3 3 0 01-3-3v-1H2a1 1 0 010-2h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
            </svg>
          </div>
          <span className="absolute -top-12 right-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm px-3 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            ¡Pregúntame sobre eventos!
          </span>
        </button>
      </div>
    </div>
  )
}

export default HomePageModern