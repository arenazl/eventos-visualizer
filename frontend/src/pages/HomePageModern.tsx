import React, { useState, useEffect } from 'react'
import EventCardModern from '../components/EventCardModern'
import SmartLocationBar from '../components/SmartLocationBar'
import NearbyCitiesLinks from '../components/NearbyCitiesLinks'
import AIRecommendations, { NoResultsWithAI } from '../components/AIRecommendations'
import { EventsGridSkeleton, EmptyState, MultiSourceSkeleton, ScrapingSkeleton } from '../components/LoadingStates'
import { EmptyEventsAnimation, EmptyEventsCompact } from '../components/EmptyEventsAnimation'
import ScrapersInfo from '../components/ScrapersInfo'
import AuthModal from '../components/AuthModal'
import Header from '../components/Header'
import { useEvents, useEventsStore } from '../stores/EventsStore'
import { useAuth } from '../contexts/AuthContext'
import { useAssistants } from '../contexts/AssistantsContext'

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
    // ✅ REMOVED: fetchEvents and searchEvents deprecated
    aiSearch,
    aiInitialSearch, 
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
    stopStreaming,
    
    // ✨ Scrapers execution info
    scrapersExecution
  } = useEvents()
  const [isScrolled, setIsScrolled] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [detectedTags, setDetectedTags] = useState<Array<{text: string, type: 'location' | 'keyword', animated: boolean}>>([])
  const [activeCategory, setActiveCategory] = useState('Todos')
  const [locationDetected, setLocationDetected] = useState(false)
  const [showScrapersInfo, setShowScrapersInfo] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showAIRecommendations, setShowAIRecommendations] = useState(false)
  const [isEventsFadingOut, setIsEventsFadingOut] = useState(false)
  const [isSearchButtonSpinning, setIsSearchButtonSpinning] = useState(false)
  
  // Auth context
  const { user, isAuthenticated } = useAuth()
  
  // Assistants context for category-based comments and auto-commenting
  const { triggerCategoryComment, triggerEventComment } = useAssistants()

  // Detectar ubicación automáticamente al cargar
  useEffect(() => {
    const detectAndLoadEvents = async () => {
      if (!locationDetected) {
        // Usar Buenos Aires como ubicación inicial confiable
        const initialLocation = {
          name: 'Buenos Aires',
          coordinates: { lat: -34.6037, lng: -58.3816 },
          country: 'Argentina',
          detected: 'fallback' as const
        }
        
        setLocation(initialLocation)
        setLocationDetected(true)
        
        // 🧠 USAR AI SEARCH COMPLETO: Intent + Search + Recommend
        await aiInitialSearch(initialLocation)
        
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

  // 🔄 Detectar cuando aparece el primer evento para detener el spinner del botón search
  useEffect(() => {
    if (events.length > 0 && isSearchButtonSpinning) {
      // Pequeño delay para que se vea la transición
      setTimeout(() => {
        setIsSearchButtonSpinning(false)
      }, 500)
    }
  }, [events.length, isSearchButtonSpinning])

  // 🎭 Comentarios automáticos cuando aparecen eventos en pantalla
  useEffect(() => {
    if (events.length > 0) {
      // Solo comentar de vez en cuando (30% chance cuando aparecen eventos)
      if (Math.random() < 0.3) {
        // Seleccionar un evento al azar para comentar
        const randomEvent = events[Math.floor(Math.random() * events.length)]
        
        // Pequeño delay para que se vean aparecer los eventos primero
        setTimeout(() => {
          triggerEventComment({
            eventTitle: randomEvent.title,
            eventCategory: randomEvent.category,
            eventType: 'auto_display',
            timestamp: new Date(),
            shouldConverse: true // Siempre conversar en auto display
          })
        }, 2000 + Math.random() * 3000) // Entre 2-5 segundos de delay aleatorio
      }
    }
  }, [events.length, triggerEventComment]) // Solo cuando cambia el número de eventos

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Efecto para animación suave de recomendaciones AI
  useEffect(() => {
    if (aiRecommendations && lastQuery) {
      // Resetear primero para forzar re-animación
      setShowAIRecommendations(false)
      // Delay para que aparezca suavemente después de cargar
      const timer = setTimeout(() => {
        setShowAIRecommendations(true)
      }, 100)
      return () => clearTimeout(timer)
    } else {
      setShowAIRecommendations(false)
    }
  }, [aiRecommendations, lastQuery])

  // Efecto para resetear fade out cuando llegan nuevos eventos
  useEffect(() => {
    if (events.length > 0 && isEventsFadingOut) {
      // Resetear fade out cuando llegan nuevos eventos
      setTimeout(() => {
        setIsEventsFadingOut(false)
      }, 100)
    }
  }, [events, isEventsFadingOut])

  // Handlers para ubicación y búsqueda
  const handleLocationChange = (location: Location) => {
    setLocation(location)
    // Solo buscar eventos si el usuario cambió manualmente la ubicación
    // y es diferente a la actual
    if (location.name !== currentLocation?.name) {
      if (activeCategory === 'Todos') {
        // ✅ REMOVED: fetchEvents deprecated - use WebSocket streaming via startStreamingSearch
        startStreamingSearch(undefined, location)
      } else {
        // Re-aplicar filtro de categoría activa con nueva ubicación
        handleCategoryClick(activeCategory)
      }
    }
  }

  // 🤖 Usar Gemini IA para detectar ubicaciones (GRATIS y súper inteligente)
  const detectLocationWithAI = async (query: string) => {
    try {
      console.log('🧠 Usando Gemini IA para detectar ubicación en:', query)
      
      // Crear un prompt específico para detección de ubicaciones
      const locationPrompt = `
      Analiza este texto y detecta si menciona alguna ciudad, país o ubicación específica:
      "${query}"
      
      Si detectas una ubicación, responde en JSON:
      {
        "detected": true,
        "location": "Nombre de la ciudad/país detectado",
        "cleanQuery": "El query sin la ubicación",
        "confidence": 0.9
      }
      
      Si NO detectas ubicación específica, responde:
      {
        "detected": false
      }
      
      Ejemplos:
      - "bares en Barcelona" → location: "Barcelona", cleanQuery: "bares"
      - "eventos en Chile" → location: "Chile", cleanQuery: "eventos" 
      - "conciertos rock" → detected: false
      `
      
      // Usar el endpoint de análisis de intención con prompt específico
      const response = await fetch('http://172.29.228.80:8001/api/ai/analyze-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: locationPrompt,
          context: {
            current_location: currentLocation?.name,
            task: 'location_detection' 
          }
        })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('🤖 Gemini respondió:', result)
        
        // Gemini debería devolver el JSON que pedimos
        if (result.analysis && result.analysis.includes('detected')) {
          try {
            // Extraer JSON de la respuesta de Gemini
            const jsonMatch = result.analysis.match(/\{[\s\S]*\}/)
            if (jsonMatch) {
              const locationData = JSON.parse(jsonMatch[0])
              return locationData
            }
          } catch (e) {
            console.warn('Error parseando respuesta Gemini:', e)
          }
        }
      }
    } catch (error) {
      console.warn('⚠️ Error con Gemini, usando fallback:', error)
    }
    
    // 🛡️ Fallback súper simple si Gemini falla
    const quickPatterns = ['barcelona', 'madrid', 'chile', 'córdoba', 'cordoba', 'mendoza', 'brasil', 'uruguay', 'santiago']
    const queryLower = query.toLowerCase()
    
    for (const pattern of quickPatterns) {
      if (queryLower.includes(pattern)) {
        return {
          detected: true,
          location: pattern.charAt(0).toUpperCase() + pattern.slice(1),
          cleanQuery: query.replace(new RegExp(pattern, 'gi'), '').replace(/\s+/g, ' ').trim(),
          confidence: 0.7
        }
      }
    }
    
    return { detected: false }
  }

  // 🗑️ FUNCIÓN SIMPLIFICADA DE FALLBACK (Solo para detectar al escribir)
  const quickLocationFallback = (value: string) => {
    const locationKeywords = [
      'barcelona', 'madrid', 'valencia', 'parís', 'paris',
      'chile', 'santiago', 'córdoba', 'cordoba', 'mendoza',
      'brasil', 'rio', 'méxico', 'mexico', 'miami'
    ]
    
    const queryLower = value.toLowerCase()
    for (const keyword of locationKeywords) {
      if (queryLower.includes(keyword)) {
        console.log('🔍 Quick fallback detectó:', keyword)
        setDetectedTags([{
          text: keyword.charAt(0).toUpperCase() + keyword.slice(1),
          type: 'location',
          animated: true
        }])
        return true
      }
    }
    setDetectedTags([])
    return false
  }

  // Handle input change - detectar al escribir espacio
  const handleInputChange = async (value: string) => {
    setSearchQuery(value)
    
    // Detectar solo si termina con espacio (feedback visual inmediato)
    if (value.endsWith(' ') && value.trim().length > 0) {
      quickLocationFallback(value)
    } else {
      setDetectedTags([])
    }
  }

  // Handle Enter - detectar al presionar Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch() // handleSearch ya incluye detectLocationWithAI
    }
  }

  // Handle Click - detectar al hacer click en buscar
  const handleSearchClick = () => {
    handleSearch() // handleSearch ya incluye detectLocationWithAI
  }

  // 🗑️ Remover tag al hacer click
  const removeTag = (tagToRemove: string) => {
    setDetectedTags(prev => prev.filter(tag => tag.text !== tagToRemove))
    // También remover la palabra del query
    const newQuery = searchQuery.replace(new RegExp(`\\b${tagToRemove}\\b`, 'gi'), '').replace(/\s+/g, ' ').trim()
    setSearchQuery(newQuery)
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    // ✨ Activar spinner del botón search
    setIsSearchButtonSpinning(true)
    
    // Fade out de eventos actuales
    if (events.length > 0) {
      setIsEventsFadingOut(true)
      // Esperar un poco para que se vea la animación
      await new Promise(resolve => setTimeout(resolve, 300))
    }
    
    try {
      // 🚀 USAR WEBSOCKET STREAMING para búsqueda en tiempo real
      console.log(`🔍 Búsqueda WebSocket: "${searchQuery}" en ${currentLocation?.name || 'ubicación actual'}`)
      
      // Usar WebSocket streaming que muestra progreso en tiempo real
      await startStreamingSearch(searchQuery, currentLocation)
      
      // Limpiar tags después de iniciar búsqueda
      setDetectedTags([])
      
      // El spinner se desactivará cuando el WebSocket complete
      setTimeout(() => {
        setIsSearchButtonSpinning(false)
      }, 3000) // Timeout de seguridad
      
    } catch (error) {
      console.error('❌ Error en búsqueda WebSocket:', error)
      // ✨ Detener spinner en caso de error
      setIsSearchButtonSpinning(false)
      // Fallback a búsqueda AI
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
        setTimeout(() => startStreamingSearch(transcript, currentLocation), 500)
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
    
    // Trigger assistant comments when category is selected
    if (category !== 'Todos') {
      triggerCategoryComment(category)
    }
    
    if (category === 'Todos') {
      // ✅ REMOVED: fetchEvents deprecated - use WebSocket streaming
      setSearchQuery('Todos los eventos')
      await startStreamingSearch(undefined, currentLocation)
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
        await aiSearch(searchQuery, currentLocation)
        // Si AI no devuelve resultados, usar búsqueda tradicional
        if (events.length === 0) {
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
      {/* HEADER CON CONTADOR EN TIEMPO REAL */}
      <Header />
      
      {/* USER AUTHENTICATION BUTTON */}
      <div className="fixed top-4 right-6 z-50">
        <div className="flex items-center">
            {/* User Button - Right aligned */}
            <div>
              {isAuthenticated ? (
                <button
                  onClick={() => {
                    try {
                      console.log('🔧 DEBUG: Opening auth modal');
                      setShowAuthModal(true);
                    } catch (error) {
                      console.error('Error opening auth modal:', error);
                    }
                  }}
                  className="flex items-center gap-2 px-3 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-xl border border-white/20 rounded-full transition-all duration-200"
                >
                  {user?.avatar ? (
                    <img 
                      src={user.avatar} 
                      alt={user.name}
                      className="w-8 h-8 rounded-full"
                    />
                  ) : (
                    <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">
                        {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                      </span>
                    </div>
                  )}
                  {!isScrolled && (
                    <span className="text-white/80 text-sm font-medium hidden sm:block">
                      {user?.name?.split(' ')[0] || 'Usuario'}
                    </span>
                  )}
                </button>
              ) : (
                <button
                  onClick={() => {
                    try {
                      console.log('🔧 DEBUG: Opening auth modal');
                      setShowAuthModal(true);
                    } catch (error) {
                      console.error('Error opening auth modal:', error);
                    }
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 backdrop-blur-xl border border-white/20 rounded-full transition-all duration-200 text-white/80 hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {!isScrolled && <span className="text-sm font-medium hidden sm:block">Iniciar Sesión</span>}
                </button>
              )}
            </div>
          </div>
      </div>

      {/* CONTENIDO PRINCIPAL */}
      <main className="pt-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Smart Location Bar */}
          <SmartLocationBar 
            onLocationChange={handleLocationChange}
            currentLocation={currentLocation}
          />
          
          {/* Nearby Cities Links */}
          {currentLocation && (
            <NearbyCitiesLinks 
              currentCity={currentLocation.name}
              onCityClick={handleLocationChange}
            />
          )}


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
                    <div className="flex-1 relative">
                      {/* Input transparente */}
                      <input 
                        type="text" 
                        value={searchQuery}
                        onChange={(e) => handleInputChange(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder=""
                        className="w-full bg-transparent text-transparent text-lg placeholder-white/40 py-5 outline-none font-medium relative z-10"
                      />
                      
                      {/* Placeholder personalizado - solo cuando no hay texto */}
                      {!searchQuery && (
                        <div className="absolute top-0 left-0 w-full py-5 pointer-events-none text-lg font-medium text-white/40">
                          🔍 Busca: 'bares en Barcelona', 'eventos en Miami'...
                        </div>
                      )}
                      
                      {/* Overlay con texto resaltado */}
                      <div className="absolute top-0 left-0 w-full py-5 pointer-events-none text-lg font-medium">
                        {searchQuery ? (
                          <span className="text-white">
                            {searchQuery.split(' ').map((word, index) => {
                              const isLocation = detectedTags.some(tag => 
                                word.toLowerCase().includes(tag.text.toLowerCase()) ||
                                tag.text.toLowerCase().includes(word.toLowerCase())
                              )
                              
                              return (
                                <span key={index}>
                                  {isLocation ? (
                                    <span className="font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent animate-pulse">
                                      🌍{word}
                                    </span>
                                  ) : (
                                    <span className="text-white">{word}</span>
                                  )}
                                  {index < searchQuery.split(' ').length - 1 && ' '}
                                </span>
                              )
                            })}
                          </span>
                        ) : (
                          <span className="text-white/40">🔍 Busca: 'bares en Barcelona', 'eventos en Miami'...</span>
                        )}
                      </div>
                    </div>
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
                      onClick={handleSearchClick}
                      disabled={loading || isStreaming || isSearchButtonSpinning}
                      className={`p-4 rounded-2xl transition-all duration-500 ${
                        isSearchButtonSpinning 
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-700 scale-105 shadow-2xl shadow-purple-500/50' 
                          : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 hover:scale-110'
                      } shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed`}
                      title={isSearchButtonSpinning ? "Buscando eventos..." : "Buscar eventos"}
                    >
                      {isSearchButtonSpinning || isStreaming ? (
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

          {/* AI Recommendations - Relocated with Slide Animation */}
          {aiRecommendations && lastQuery && (
            <div 
              className={`mb-8 transition-all duration-700 ease-out transform ${
                showAIRecommendations 
                  ? 'translate-y-0 opacity-100 scale-100' 
                  : '-translate-y-8 opacity-0 scale-95'
              }`}
              style={{
                transformOrigin: 'center top'
              }}
            >
              <div className="transform transition-all duration-300 ease-out hover:scale-105">
                <AIRecommendations
                  recommendations={aiRecommendations}
                  originalQuery={lastQuery}
                  onFollowUpClick={handleFollowUpClick}
                />
              </div>
            </div>
          )}

          {/* No Results with AI Suggestions */}
          {!loading && events.length === 0 && lastQuery && aiRecommendations?.alternative_suggestions && (
            <div className="mb-8">
              <NoResultsWithAI
                query={lastQuery}
                suggestions={aiRecommendations.alternative_suggestions}
                onSuggestionClick={handleFollowUpClick}
              />
            </div>
          )}

          {/* ✨ Scrapers Execution Info */}
          {scrapersExecution && (
            <div className="mb-8">
              <ScrapersInfo
                scrapersExecution={scrapersExecution}
                isVisible={showScrapersInfo}
                onToggle={() => setShowScrapersInfo(!showScrapersInfo)}
              />
            </div>
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
            <div className="mb-6 -mt-2 space-y-4">
              {/* Línea de progreso fina */}
              <div className="w-full bg-white/10 rounded-full h-0.5 overflow-hidden mb-2">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 transition-all duration-300 ease-out"
                  style={{ width: `${streamingProgress}%` }}
                ></div>
              </div>
              
              {/* Skeleton para la fuente actual */}
              {streamingSource && (
                <ScrapingSkeleton source={streamingSource} />
              )}
              
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
            <div className="space-y-8">
              <MultiSourceSkeleton />
              <EventsGridSkeleton />
            </div>
          ) : events.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                {isStreaming && (
                  <div className="flex items-center gap-2 text-white/60">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm">Buscando más...</span>
                  </div>
                )}
              </div>
              
              <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20 transition-all duration-300 ${
                isEventsFadingOut ? 'opacity-20 scale-95 blur-sm' : 'opacity-100 scale-100 blur-0'
              }`}>
                {events.map((event, index) => (
                  <div
                    key={event.title + '-' + index}
                    className={`${
                      isEventsFadingOut 
                        ? 'opacity-20' 
                        : 'opacity-0 animate-fade-in-up'
                    }`}
                    style={{
                      animationDelay: isEventsFadingOut ? '0s' : `${(index % 6) * 0.1}s`,
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
            <EmptyEventsAnimation location={currentLocation?.name || 'tu ubicación'} />
          ) : events.length === 0 && !loading && !isStreaming && lastQuery ? (
            <EmptyEventsCompact location={currentLocation?.name || 'esta zona'} />
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

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </div>
  )
}

export default HomePageModern