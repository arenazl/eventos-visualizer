import React, { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import EventCardModern from '../components/EventCardModern'
import SmartLocationBar from '../components/SmartLocationBar'
import AIRecommendations, { NoResultsWithAI } from '../components/AIRecommendations'
import { EventsGridSkeleton, EmptyState, MultiSourceSkeleton, ScrapingSkeleton } from '../components/LoadingStates'
import { EmptyEventsAnimation, EmptyEventsCompact } from '../components/EmptyEventsAnimation'
import AuthModal from '../components/AuthModal'
import Header from '../components/Header'
import ScrapersDetailPanel from '../components/ScrapersDetailPanel'
import { useEvents } from '../stores/EventsStore'
import { useAuth } from '../contexts/AuthContext'
import { useAssistants } from '../contexts/AssistantsContext'
import bgImage from '../assets/bg.webp'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faStar, faMusic, faTrophy, faTheaterMasks, faLaptopCode, faGlassCheers,
  faPalette, faGlobe, faCalendar, faBullseye, faFilm, faUtensils,
  faPaintBrush, faDrum, faLandmark, faTicket, faMapMarkerAlt
} from '@fortawesome/free-solid-svg-icons'

interface Location {
  name: string
  coordinates?: { lat: number; lng: number }
  country?: string
  detected: 'gps' | 'manual' | 'prompt' | 'fallback'
  // Metadata para barrios (info de la base de datos)
  metadata?: {
    neighborhood?: string
    city?: string
    country?: string | null
    province?: string | null
  }
}

const HomePageModern: React.FC = () => {
  const location = useLocation()
  const {
    events,
    loading,
    currentLocation,
    aiRecommendations,
    lastQuery,
    fetchEvents,
    aiSearch,
    aiInitialSearch,
    searchEvents,
    setLocation,
    // getSmartRecommendations, // DISABLED
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
    scrapersExecution,

    // 📍 Eventos cercanos y provincia (nuevo sistema multi-ciudad)
    fetchLocationEnrichment,
    searchSpecificCity,
    fetchNearbyEvents,
    fetchProvinceEvents,
    autoLoadExpandedEvents,
    searchMultipleNearbyCities,
    nearbyEventsAvailable,
    nearbyCities,
    nearbyCity,
    loadingNearby,
    provinceEventsAvailable,
    provinceName,
    loadingProvince,
    loadingEnrichment,
    selectedCity,
    originalSearchLocation,
    showReturnButton,
    loadingCityName,

    // 🏙️ Búsqueda expandida a ciudad principal
    parentCityDetected,
    searchLocationQuery,
    expandedSearch,

    // 🎭 Callback para asistentes
    setOnNoEventsCallback
  } = useEvents()
  const [isScrolled, setIsScrolled] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [detectedTags, setDetectedTags] = useState<Array<{ text: string, type: 'location' | 'keyword', animated: boolean }>>([])
  const [activeCategory, setActiveCategory] = useState('Todos')
  const [locationDetected, setLocationDetected] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showAIRecommendations, setShowAIRecommendations] = useState(false)
  const [isEventsFadingOut, setIsEventsFadingOut] = useState(false)
  const [isSearchButtonSpinning, setIsSearchButtonSpinning] = useState(false)
  const [isManualSearch, setIsManualSearch] = useState(false) // 🔥 Evita auto-effects en búsquedas manuales
  const [allEvents, setAllEvents] = useState<any[]>([]) // 🎯 Guardar TODOS los eventos para filtrar localmente
  const [categories, setCategories] = useState<Array<{name: string, count: number}>>([]) // 🏷️ Categorías dinámicas
  const [loadingCategories, setLoadingCategories] = useState(false)
  const [isDetectingLocation, setIsDetectingLocation] = useState(false)

  // 🤖 Chat flotante de IA
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatResponse, setChatResponse] = useState<{
    answer: string
    relatedEvents: Array<{ id: string; title: string; slug: string; venue: string; date: string }>
  } | null>(null)

  // 🔒 Ref para prevenir doble ejecución del auto-load inicial
  const hasAutoLoaded = useRef(false)
  // 🔒 Ref para prevenir loop infinito de enrichment
  const hasEnriched = useRef(false)
  // 🔒 Ref para bloquear búsquedas automáticas cuando el usuario selecciona manualmente
  const isManualSelectionRef = useRef(false)

  // Auth context
  const { user, isAuthenticated } = useAuth()

  // Assistants context for category-based comments and auto-commenting
  const { triggerCategoryComment, triggerEventComment, triggerSearchComment, triggerNoEventsComment } = useAssistants()

  // Registrar callback para eventos "sin eventos" desde el store
  useEffect(() => {
    if (setOnNoEventsCallback) {
      setOnNoEventsCallback(triggerNoEventsComment)
    }
  }, [setOnNoEventsCallback, triggerNoEventsComment])

  // 🔄 SIEMPRE RECARGAR cuando vuelve al home
  const lastLocationRef = useRef(location.pathname)
  useEffect(() => {
    // 🔒 NO recargar si el usuario está seleccionando manualmente una ubicación
    if (isManualSelectionRef.current) {
      console.log('⏸️ Navegación BLOQUEADA - selección manual en progreso')
      return
    }

    // Si vuelves de una página de detalle (/event/*) al home (/)
    if (lastLocationRef.current.startsWith('/event/') && location.pathname === '/' && currentLocation) {
      console.log('🔙 Volviendo de detalle - recargando eventos frescos desde MySQL...')
      // Limpiar eventos primero para forzar recarga
      startStreamingSearch(currentLocation)
    }
    lastLocationRef.current = location.pathname
  }, [location.pathname, currentLocation, startStreamingSearch])

  // 🔄 DETECTAR CUANDO VUELVES DE DETALLE Y RECARGAR EVENTOS (visibilidad)
  useEffect(() => {
    const handleVisibilityChange = () => {
      // 🔒 NO recargar si el usuario está seleccionando manualmente una ubicación
      if (isManualSelectionRef.current) {
        console.log('⏸️ visibilitychange BLOQUEADO - selección manual en progreso')
        return
      }

      // Solo recargar si la página se vuelve visible Y hay eventos en memoria
      if (!document.hidden && events.length > 0 && currentLocation) {
        console.log('👁️ Página visible de nuevo - recargando eventos desde MySQL...')
        startStreamingSearch(currentLocation)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [events.length, currentLocation, startStreamingSearch])

  // 🏷️ Calcular categorías dinámicamente desde los eventos VÁLIDOS existentes
  useEffect(() => {
    if (events.length === 0) {
      setCategories([])
      setLoadingCategories(false)
      return
    }

    // Filtrar eventos válidos (misma lógica que en el render)
    const validEvents = events.filter(event => {
      // Excluir eventos sin título o con "Sin título"
      if (!event.title || event.title.trim() === '' ||
          event.title.toLowerCase() === 'sin título' ||
          event.title.toLowerCase() === 'sin titulo') {
        return false
      }
      return true
    })

    // Calcular DISTINCT de categorías que tienen eventos VÁLIDOS
    const categoryCount = new Map<string, number>()

    validEvents.forEach(event => {
      if (event.category) {
        // Normalizar: lowercase + quitar acentos
        const normalizedCategory = event.category.toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '') // Quitar acentos

        categoryCount.set(
          normalizedCategory,
          (categoryCount.get(normalizedCategory) || 0) + 1
        )
      }
    })

    // Convertir a array y ordenar por cantidad de eventos
    const dynamicCategories = Array.from(categoryCount.entries())
      .map(([name, count]) => ({ name, count }))
      .filter(cat => cat.count > 0) // Solo categorías con al menos 1 evento
      .sort((a, b) => b.count - a.count) // Ordenar por cantidad descendente

    setCategories(dynamicCategories)
    console.log(`✅ Categorías calculadas desde ${validEvents.length} eventos válidos (de ${events.length} totales):`, dynamicCategories)
  }, [events]) // 🔥 Recalcular cuando cambien los eventos

  // Detectar ubicación automáticamente al cargar
  useEffect(() => {
    const detectAndLoadEvents = async () => {
      // 🔒 Prevenir doble ejecución (React StrictMode)
      if (hasAutoLoaded.current) {
        console.log('⏸️ Auto-load ya ejecutado - saltando duplicado')
        return
      }

      // 🔒 NO ejecutar si el usuario está seleccionando manualmente una ubicación
      // Verificar AMBOS: ref local Y flag global en window
      if (isManualSelectionRef.current || (window as any).__isManualSelection) {
        console.log('⏸️ Auto-load BLOQUEADO - selección manual en progreso (ref:', isManualSelectionRef.current, ', window:', (window as any).__isManualSelection, ')')
        return
      }

      // 🔒 NO ejecutar si ya hay eventos cargados (volviendo desde detalle)
      if (events.length > 0) {
        console.log('✅ Eventos ya cargados en memoria - usando cache (navegación back)')
        setLocationDetected(true) // Marcar como detectado para evitar loop
        hasAutoLoaded.current = true
        return
      }

      // 🔒 NO ejecutar si el usuario está viendo eventos de una ciudad específica
      if (selectedCity) {
        console.log('⏸️ Auto-load deshabilitado - usuario viendo eventos de:', selectedCity)
        return
      }

      if (!locationDetected) {
        console.log('🌍 Iniciando detección de ubicación...')
        hasAutoLoaded.current = true // 🔒 Marcar como ejecutado
        setIsDetectingLocation(true) // Mostrar loading state

        try {
          let detectedLocation: Location | null = null

          // 1. Intentar primero con geolocalización del navegador (más precisa)
          if ('geolocation' in navigator) {
            console.log('📍 Intentando geolocalización del navegador...')
            try {
              const position = await new Promise<GeolocationPosition>((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                  timeout: 10000,
                  maximumAge: 300000 // Cache por 5 minutos
                })
              })

              console.log('✅ Geolocalización obtenida:', position.coords)

              // Usar reverse geocoding con Nominatim (gratuito)
              const reverseResponse = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
              )
              const reverseData = await reverseResponse.json()

              // 🔧 BUGFIX: Extraer ciudad REAL de reverseData en lugar de hardcodear Buenos Aires
              const cityName = reverseData.address?.city
                || reverseData.address?.town
                || reverseData.address?.municipality
                || reverseData.address?.village
                || 'Buenos Aires' // Solo fallback si no hay nada

              // 🌍 Extraer provincia/estado para desambiguar ciudades con mismo nombre
              const stateName = reverseData.address?.state || ''
              const countryName = reverseData.address?.country || 'Argentina'

              // 🔧 Construir nombre completo con provincia para evitar ambigüedad
              // Ej: "Merlo, Buenos Aires" en lugar de solo "Merlo"
              const fullLocationName = stateName
                ? `${cityName}, ${stateName}`
                : cityName

              console.log('📍 [GPS] Reverse geocoding result:', reverseData.address)
              console.log('📍 [GPS] Full location name:', fullLocationName)

              detectedLocation = {
                name: fullLocationName,
                coordinates: { lat: position.coords.latitude, lng: position.coords.longitude },
                country: countryName,
                detected: 'gps'
              }

              console.log('✅ Ubicación GPS detectada:', detectedLocation.name)
            } catch (geoError) {
              console.warn('⚠️ Geolocalización no disponible o denegada:', geoError)
            }
          }

          // 2. Si falló GPS, intentar con IP
          if (!detectedLocation) {
            console.log('📡 Intentando detección por IP...')
            const ipResponse = await fetch('https://ipapi.co/json/')
            const ipData = await ipResponse.json()

            // 🌍 Incluir región/provincia para desambiguar
            const ipCity = ipData.city || 'Buenos Aires'
            const ipRegion = ipData.region || ''
            const ipFullName = ipRegion ? `${ipCity}, ${ipRegion}` : ipCity

            detectedLocation = {
              name: ipFullName,
              coordinates: { lat: ipData.latitude, lng: ipData.longitude },
              country: ipData.country_name,
              detected: 'fallback'
            }

            console.log('✅ Ubicación por IP detectada:', detectedLocation.name)
          }

          // 3. Set the detected location in store
          console.log('📍 [INIT] Seteando ubicación detectada:', detectedLocation.name)
          setLocation(detectedLocation)

          // ⏳ Pequeño delay para asegurar que el store se actualizó
          await new Promise(resolve => setTimeout(resolve, 100))

          // 4. 🌍 BUSCAR EN MÚLTIPLES CIUDADES CERCANAS
          console.log('🔍 [INIT] Iniciando búsqueda multi-ciudad para:', detectedLocation.name)
          console.log('🔍 [INIT] currentLocation antes de búsqueda:', currentLocation?.name)
          await searchMultipleNearbyCities(detectedLocation)

          console.log('✅ [INIT] Búsqueda multi-ciudad completada, marcando location como detectada')
          setLocationDetected(true)
          setIsDetectingLocation(false) // Ocultar loading state
        } catch (error: any) {
          console.error('❌ Error detectando ubicación:', error)

          // 📱 DEBUG MÓVIL: Ver cuando se dispara este fallback
          alert(`[DEBUG FALLBACK Buenos Aires]\nEsto NO debería aparecer si seleccionaste Bogotá!\nError: ${error?.message || 'Sin error'}\nManual: ${(window as any).__isManualSelection}`)

          // Fallback a ubicación por defecto
          const fallbackLocation: Location = {
            name: 'Buenos Aires',
            coordinates: { lat: -34.6037, lng: -58.3816 },
            country: 'Argentina',
            detected: 'fallback'
          }
          console.log('🔄 Usando ubicación por defecto:', fallbackLocation.name)
          setLocation(fallbackLocation)
          await searchMultipleNearbyCities(fallbackLocation)
          setLocationDetected(true)
          setIsDetectingLocation(false) // Ocultar loading state
        }
      }
    }

    detectAndLoadEvents()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationDetected, selectedCity, events.length]) // Incluir events.length para detectar cache

  // 🔄 Detectar cuando aparece el primer evento para detener el spinner del botón search
  useEffect(() => {
    if (events.length > 0 && isSearchButtonSpinning) {
      // Pequeño delay para que se vea la transición
      setTimeout(() => {
        setIsSearchButtonSpinning(false)
      }, 500)
    }
  }, [events.length, isSearchButtonSpinning])

  // 🎯 Actualizar allEvents cuando lleguen eventos nuevos (resetear categoría a Todos)
  useEffect(() => {
    if (events.length > 0 && activeCategory === 'Todos') {
      setAllEvents(events)
    }
  }, [events])

  // ❌ AUTO-LOAD DE EVENTOS EXPANDIDOS ELIMINADO
  // Ya NO se auto-cargan eventos cuando hay pocos resultados

  // 🌍 ENRIQUECIMIENTO DE UBICACIÓN - Se llama MANUALMENTE en handleSearch
  // NO usar useEffect automático para evitar llamadas constantes

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
  const handleLocationChange = async (location: Location) => {
    // 🔥 ACTIVAR FLAG - Evita cascada de auto-effects
    setIsManualSearch(true)

    setLocation(location)

    try {
      // Solo buscar eventos si el usuario cambió manualmente la ubicación
      // y es diferente a la actual
      if (location.name !== currentLocation?.name) {
        // 🚀 Streaming primero para resultados progresivos
        await startStreamingSearch(location)

        // 🧠 Recomendaciones AI async en background (no bloquea)
        if (activeCategory !== 'Todos') {
          // Re-aplicar filtro de categoría con AI
          // DISABLED: getSmartRecommendations removed - use client-side scoring instead
          // const categoryQuery = activeCategory.toLowerCase()
          // getSmartRecommendations(categoryQuery, events, location.name)
          //   .catch(err => console.warn('⚠️ Recomendaciones fallaron:', err))
        }
      }
    } finally {
      // 🔥 DESACTIVAR FLAG después de 2 segundos
      setTimeout(() => {
        console.log('✅ Reseteo flag isManualSearch (location change)')
        setIsManualSearch(false)
      }, 2000)
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/ai/analyze-intent`, {
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
  const handleSearchClick = async () => {
    await handleSearch()
  }

  // 🗑️ Remover tag al hacer click
  const removeTag = (tagToRemove: string) => {
    setDetectedTags(prev => prev.filter(tag => tag.text !== tagToRemove))
    // También remover la palabra del query
    const newQuery = searchQuery.replace(new RegExp(`\\b${tagToRemove}\\b`, 'gi'), '').replace(/\s+/g, ' ').trim()
    setSearchQuery(newQuery)
  }

  const handleSearch = async () => {
    // ✅ Si hay texto en searchQuery, usarlo como ubicación temporal
    let searchLocation = currentLocation

    if (searchQuery.trim()) {
      // Crear ubicación temporal desde el texto del search bar
      searchLocation = {
        name: searchQuery.trim(),
        coordinates: undefined,
        country: '',
        detected: 'manual'
      }
      // Actualizar también el currentLocation en el store
      setLocation(searchLocation)
    }

    if (!searchQuery.trim() && !currentLocation) {
      console.warn('⚠️ Búsqueda bloqueada: Se requiere ubicación o query text')
      return
    }

    // 🔥 ACTIVAR FLAG - Evita cascada de auto-effects
    setIsManualSearch(true)

    // ✨ Activar spinner del botón search
    setIsSearchButtonSpinning(true)

    // Fade out de eventos actuales
    if (events.length > 0) {
      setIsEventsFadingOut(true)
      // Esperar un poco para que se vea la animación
      await new Promise(resolve => setTimeout(resolve, 300))
    }

    try {
      // 🚀 PRIMERO: Streaming para mostrar eventos progresivamente
      console.log(`🔍 Búsqueda: "${searchQuery}" en ${searchLocation?.name || 'ubicación actual'}`)

      // 🎭 Disparar comentario general de búsqueda (basado en día/hora + ciudad)
      triggerSearchComment(searchLocation?.name)

      // Iniciar streaming SSE para resultados progresivos
      await startStreamingSearch(searchLocation)

      // 🧠 SEGUNDO: Después del streaming, pedir recomendaciones AI
      // Esto NO bloquea la UI, los eventos ya se están mostrando
      const foundEvents = events.length
      // DISABLED: getSmartRecommendations removed - use client-side scoring instead
      // if (foundEvents > 0) {
      //   // Llamar a recomendaciones en background
      //   getSmartRecommendations(searchQuery, events, currentLocation?.name)
      //     .catch(err => console.warn('⚠️ Recomendaciones AI fallaron:', err))
      // }

      // Limpiar tags
      setDetectedTags([])

    } catch (error) {
      console.error('❌ Error en búsqueda:', error)
      // ✨ Detener spinner en caso de error
      setIsSearchButtonSpinning(false)
      // Fallback a búsqueda tradicional
      await searchEvents(searchQuery, currentLocation)
    } finally {
      // 🔥 DESACTIVAR FLAG - Permitir auto-effects nuevamente después de 2 segundos
      setTimeout(() => {
        console.log('✅ Reseteo flag isManualSearch - auto-effects habilitados')
        setIsManualSearch(false)
      }, 2000) // Delay para que termine toda la cascada de updates
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
  const handleFollowUpClick = async (question: string) => {
    // 🔥 ACTIVAR FLAG - Evita cascada de auto-effects
    setIsManualSearch(true)

    setSearchQuery(question)

    try {
      await new Promise(resolve => setTimeout(resolve, 300))
      await aiSearch(question, currentLocation)
    } finally {
      // 🔥 DESACTIVAR FLAG después de 2 segundos
      setTimeout(() => {
        console.log('✅ Reseteo flag isManualSearch (follow-up click)')
        setIsManualSearch(false)
      }, 2000)
    }
  }

  // Handler para categorías - FILTRADO LOCAL (sin modificar search box)
  const handleCategoryClick = (category: string) => {
    if (!currentLocation) {
      console.warn('⚠️ No hay ubicación seleccionada')
      return
    }

    console.log(`🏷️ Categoría seleccionada: ${category}`)
    setActiveCategory(category)

    // Trigger assistant comments when category is selected
    if (category !== 'Todos') {
      triggerCategoryComment(category)
    }

    // 🎯 FILTRAR LOCALMENTE - Solo cambiar categoría activa, NO modificar search box
    if (category === 'Todos') {
      console.log(`✨ Mostrando todos los eventos: ${events.length}`)
    } else {
      // Contar cuántos eventos coinciden con la categoría
      const normalizedCategory = category.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      const filteredCount = events.filter(event => {
        const eventCategory = (event.category || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        return eventCategory.includes(normalizedCategory) || normalizedCategory.includes(eventCategory)
      }).length

      console.log(`🔍 Filtrando eventos por categoría: ${category}`)
      console.log(`📊 Total eventos en ${category}: ${filteredCount} de ${events.length}`)
    }
  }

  // 📍 Handler cuando el usuario selecciona una ubicación del autocompletado
  const handleLocationSelect = async (location: any) => {
    try {
      console.log('📍 [MOBILE-DEBUG] handleLocationSelect INICIO:', JSON.stringify(location))

      // 🔒 BLOQUEAR búsquedas automáticas durante selección manual
      // Usar AMBOS: ref local Y flag global en window para máxima robustez
      isManualSelectionRef.current = true
      ;(window as any).__isManualSelection = true  // 🔒 FLAG GLOBAL
      setIsManualSearch(true) // 🔒 También activar state para que SmartLocationBar lo vea
      console.log('🔒 [MOBILE-DEBUG] Flags activados (ref + window.__isManualSelection)')

      const selectedLocation: Location = {
        name: location.name,
        coordinates: { lat: location.lat, lng: location.lon },
        country: location.country,
        detected: 'manual'
      }
      console.log('📍 [MOBILE-DEBUG] selectedLocation creado:', JSON.stringify(selectedLocation))

      // 🔒 Resetear flag de enrichment para nueva ubicación
      hasEnriched.current = false
      console.log('📍 [MOBILE-DEBUG] hasEnriched reseteado')

      // Actualizar ubicación en el store
      setLocation(selectedLocation)
      console.log('✅ [MOBILE-DEBUG] Store actualizado con:', selectedLocation.name, ',', selectedLocation.country)

      // 🚀 EJECUTAR BÚSQUEDA AUTOMÁTICAMENTE al seleccionar del dropdown
      setIsSearchButtonSpinning(true)
      console.log('📍 [MOBILE-DEBUG] isSearchButtonSpinning = true')

      // Fade out eventos actuales
      if (events.length > 0) {
        console.log('📍 [MOBILE-DEBUG] Iniciando fade out de', events.length, 'eventos')
        setIsEventsFadingOut(true)
        await new Promise(resolve => setTimeout(resolve, 300))
        console.log('📍 [MOBILE-DEBUG] Fade out completado')
      }

      console.log('📍 [MOBILE-DEBUG] Iniciando searchMultipleNearbyCities...')
      // 🌍 Buscar en múltiples ciudades cercanas (igual que carga inicial)
      await searchMultipleNearbyCities(selectedLocation)
      console.log('📍 [MOBILE-DEBUG] searchMultipleNearbyCities completado')

    } catch (error: any) {
      // 🔴 CAPTURAR ERROR EN MÓVIL - CON ALERT PARA DEBUG
      console.error('🔴 [MOBILE-ERROR] Error en handleLocationSelect:', error)
      setIsSearchButtonSpinning(false)
      setIsEventsFadingOut(false)

      // 📱 ALERT PARA VER ERRORES EN MÓVIL
      alert(`[ERROR handleLocationSelect]\nMessage: ${error?.message || 'Unknown'}\nName: ${error?.name || 'N/A'}\nStack: ${error?.stack?.substring(0, 200) || 'No stack'}`)
    } finally {
      // 🔓 DESBLOQUEAR después de 5 segundos (tiempo suficiente para que termine todo)
      console.log('📍 [MOBILE-DEBUG] Finally block - programando desbloqueo en 5s')
      setTimeout(() => {
        isManualSelectionRef.current = false
        ;(window as any).__isManualSelection = false  // 🔓 FLAG GLOBAL
        setIsManualSearch(false) // 🔓 También desactivar state
        console.log('🔓 isManualSelectionRef = false, window.__isManualSelection = false (auto-searches habilitadas)')
      }, 5000)
    }
  }

  // 🤖 Enviar mensaje al chat de IA
  const handleChatSubmit = async () => {
    if (!chatMessage.trim() || chatLoading) return

    setChatLoading(true)
    setChatResponse(null)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/ai/chat-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: chatMessage })
      })

      if (response.ok) {
        const data = await response.json()
        setChatResponse({
          answer: data.answer || 'Encontré estos eventos relacionados:',
          relatedEvents: data.events || []
        })
      } else {
        setChatResponse({
          answer: 'No pude buscar eventos en este momento. Intenta de nuevo.',
          relatedEvents: []
        })
      }
    } catch (error) {
      console.error('Error en chat:', error)
      setChatResponse({
        answer: 'Error de conexión. Verifica tu internet.',
        relatedEvents: []
      })
    } finally {
      setChatLoading(false)
      setChatMessage('')
    }
  }

  // 🎨 Helper functions para mapear categorías dinámicas
  const getCategoryDisplayName = (category: string): string => {
    const displayNames: Record<string, string> = {
      'music': 'Música',
      'sports': 'Deportes',
      'cultural': 'Cultural',
      'tech': 'Tech',
      'party': 'Fiestas',
      'hobbies': 'Hobbies',
      'international': 'Internacional',
      'film': 'Cine',
      'theater': 'Teatro',
      'food': 'Comida',
      'art': 'Arte',
      'festival': 'Festival'
    }
    return displayNames[category.toLowerCase()] || category.charAt(0).toUpperCase() + category.slice(1)
  }

  const getCategoryGradient = (displayName: string): string => {
    const gradients: Record<string, string> = {
      'Todos': 'from-gray-600 to-gray-400',
      'Música': 'from-purple-600 via-pink-500 to-red-500',
      'Deportes': 'from-green-600 via-emerald-500 to-teal-500',
      'Cultural': 'from-blue-600 via-indigo-500 to-purple-500',
      'Tech': 'from-indigo-600 via-blue-500 to-cyan-500',
      'Fiestas': 'from-pink-600 via-rose-500 to-orange-500',
      'Hobbies': 'from-yellow-500 via-orange-500 to-red-500',
      'Internacional': 'from-cyan-500 via-blue-500 to-indigo-500',
      'Cine': 'from-red-600 via-orange-500 to-yellow-500',
      'Teatro': 'from-purple-600 via-violet-500 to-fuchsia-500',
      'Comida': 'from-orange-600 via-amber-500 to-yellow-500',
      'Arte': 'from-pink-600 via-purple-500 to-indigo-500',
      'Festival': 'from-fuchsia-600 via-pink-500 to-rose-500'
    }
    return gradients[displayName] || 'from-gray-600 to-gray-400'
  }

  const getCategoryIcon = (displayName: string) => {
    const icons: Record<string, any> = {
      'Todos': faStar,
      'Música': faMusic,
      'Deportes': faTrophy,
      'Cultural': faLandmark,
      'Tech': faLaptopCode,
      'Fiestas': faGlassCheers,
      'Hobbies': faPalette,
      'Internacional': faGlobe,
      'General': faCalendar,
      'Cine': faFilm,
      'Teatro': faTheaterMasks,
      'Comida': faUtensils,
      'Arte': faPaintBrush,
      'Festival': faDrum
    }
    return icons[displayName] || faTicket
  }

  // 🏷️ Construir lista de categorías con "Todos" al principio (sin duplicados)
  const displayCategories = [
    'Todos',
    ...Array.from(new Set(categories.map(cat => getCategoryDisplayName(cat.name))))
  ]

  return (
    <div className="min-h-screen relative">
      {/* Imagen de fondo */}
      <div
        className="fixed inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: `url(${bgImage})`,
          backgroundSize: '100% 100%',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      ></div>

      {/* Gradiente encima de la imagen */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-900/85 via-blue-900/80 to-indigo-900/85 pointer-events-none"></div>

      {/* Contenido principal */}
      <div className="relative z-10">
      {/* HEADER CONSOLIDADO */}
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearchSubmit={handleSearchClick}
        onVoiceSearch={handleVoiceSearch}
        onLocationClick={() => { }}
        onLocationSelect={handleLocationSelect}
        isSearching={loading || isStreaming || isSearchButtonSpinning}
        currentLocation={
          // Si es un barrio (tiene metadata.city), mostrar "Barrio, Ciudad"
          currentLocation?.metadata?.neighborhood && currentLocation?.metadata?.city
            ? `${currentLocation.metadata.neighborhood}, ${currentLocation.metadata.city}`
            : currentLocation?.name
        }
      />

      {/* CONTENIDO PRINCIPAL - padding reducido en mobile */}
      <main className="pt-4 px-2 sm:px-4 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Loading inicial - Detectando ubicación */}
          {isDetectingLocation && (
            <div className="mb-6 bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-orange-500/20 backdrop-blur-xl border border-white/20 rounded-2xl p-6 animate-pulse">
              <div className="flex items-center justify-center gap-3">
                <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
                <div className="text-white">
                  <p className="font-semibold">Detectando tu ubicación...</p>
                  <p className="text-sm text-white/70 mt-1">{streamingMessage || 'Buscando ciudades cercanas'}</p>
                </div>
              </div>
              {streamingProgress > 0 && (
                <div className="mt-4 w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 transition-all duration-300"
                    style={{ width: `${streamingProgress}%` }}
                  ></div>
                </div>
              )}
            </div>
          )}

          {/* Smart Location Bar */}
          <SmartLocationBar
            onLocationChange={handleLocationChange}
            currentLocation={currentLocation}
            parentCityDetected={parentCityDetected}
            searchLocationQuery={searchLocationQuery}
            expandedSearch={expandedSearch}
            totalEvents={events.length}
            isManualSelectionActive={isManualSearch}
          />

          {/* Panel Técnico Detallado */}
          <ScrapersDetailPanel />

          {/* 🏷️ CATEGORÍAS - Botones con iconos y gradientes - CENTRADAS */}
          <div className="mb-6">
            <div className="flex justify-center gap-2 sm:gap-3 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
              {displayCategories.map((category) => (
                <button
                  key={category}
                  onClick={() => handleCategoryClick(category)}
                  className={`flex-shrink-0 group relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ease-out whitespace-nowrap bg-gradient-to-r ${getCategoryGradient(category)} transform ${
                    activeCategory === category
                      ? 'text-white shadow-lg shadow-purple-500/30 scale-110 opacity-100 animate-[bounce_0.3s_ease-out]'
                      : 'opacity-70 hover:opacity-90 text-white hover:scale-105 active:scale-95'
                  }`}
                >
                  <FontAwesomeIcon
                    icon={getCategoryIcon(category)}
                    className={`w-4 h-4 transition-transform duration-300 ${activeCategory === category ? 'scale-110' : 'group-hover:scale-110'}`}
                  />
                  <span>{category}</span>
                  {/* Badge con cantidad */}
                  {category !== 'Todos' && categories.find(c => getCategoryDisplayName(c.name) === category) && (
                    <span className={`ml-1 text-xs px-1.5 py-0.5 rounded-full ${
                      activeCategory === category ? 'bg-white/30' : 'bg-white/20'
                    }`}>
                      {categories.find(c => getCategoryDisplayName(c.name) === category)?.count || 0}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* 🌍 CIUDADES CERCANAS - Botones para buscar en ciudades con eventos */}
          {nearbyCities && nearbyCities.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-center gap-2 mb-3">
                <FontAwesomeIcon icon={faMapMarkerAlt} className="w-4 h-4 text-white/60" />
                <span className="text-sm text-white/60 font-medium">Ciudades cercanas con eventos</span>
              </div>
              <div className="flex justify-center gap-2 sm:gap-3 flex-wrap">
                {/* 🌐 Botón "Todos" - Busca en todas las ciudades cercanas */}
                <button
                  onClick={() => {
                    // Buscar en todas las ciudades cercanas a la vez
                    nearbyCities.forEach(city => searchSpecificCity(city))
                  }}
                  className="group flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ease-out whitespace-nowrap bg-gradient-to-r from-purple-500/80 to-indigo-500/80 hover:from-purple-500 hover:to-indigo-500 text-white opacity-90 hover:opacity-100 hover:scale-105 active:scale-95 shadow-lg hover:shadow-purple-500/30"
                >
                  <FontAwesomeIcon
                    icon={faGlobe}
                    className="w-3.5 h-3.5 transition-transform duration-300 group-hover:scale-110"
                  />
                  <span>Todos</span>
                </button>
                {/* Ciudades individuales */}
                {nearbyCities.map((city) => (
                  <button
                    key={city}
                    onClick={() => searchSpecificCity(city)}
                    className="group flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ease-out whitespace-nowrap bg-gradient-to-r from-emerald-500/80 to-teal-500/80 hover:from-emerald-500 hover:to-teal-500 text-white opacity-80 hover:opacity-100 hover:scale-105 active:scale-95 shadow-lg hover:shadow-emerald-500/30"
                  >
                    <FontAwesomeIcon
                      icon={faMapMarkerAlt}
                      className="w-3.5 h-3.5 transition-transform duration-300 group-hover:scale-110"
                    />
                    <span>{city}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ❌ MENSAJES AUTO-LOAD ELIMINADOS - Ya no se auto-cargan eventos expandidos */}

          {/* AI Recommendations - Relocated with Slide Animation */}
          {aiRecommendations && lastQuery && (
            <div
              className={`mb-8 transition-all duration-700 ease-out transform ${showAIRecommendations
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


          {/* Events Stats */}
          <div className="mb-8 flex flex-col items-center gap-3">
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

              <div className={`grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3 md:gap-4 lg:gap-6 pb-20 transition-all duration-300 ${isEventsFadingOut ? 'opacity-20 scale-95 blur-sm' : 'opacity-100 scale-100 blur-0'
                }`}>
                {(() => {
                  // 🔥 DEDUPLICACIÓN MEJORADA: Agrupar SOLO por título, mostrar rango de horarios
                  const eventsGroupMap = new Map()

                  events.forEach(event => {
                    // Clave SOLO por título (ignorando venue y horario)
                    const groupKey = event.title.toLowerCase().trim()

                    if (!eventsGroupMap.has(groupKey)) {
                      eventsGroupMap.set(groupKey, [event])
                    } else {
                      eventsGroupMap.get(groupKey).push(event)
                    }
                  })

                  // Procesar grupos: si hay múltiples horarios, usar rango
                  const uniqueEvents = Array.from(eventsGroupMap.values()).map(group => {
                    if (group.length === 1) {
                      return group[0]
                    }

                    // Múltiples eventos con mismo título + venue → Calcular rango de horarios
                    const sortedByTime = group
                      .filter(e => e.start_datetime)
                      .sort((a, b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime())

                    if (sortedByTime.length === 0) return group[0]

                    // Tomar el primer evento como base
                    const mergedEvent = { ...sortedByTime[0] }

                    // Si hay múltiples horarios, crear un campo especial para el rango
                    if (sortedByTime.length > 1) {
                      mergedEvent.start_datetime = sortedByTime[0].start_datetime // Hora más temprana
                      mergedEvent.end_datetime = sortedByTime[sortedByTime.length - 1].start_datetime // Hora más tardía
                      mergedEvent.has_multiple_times = true // Flag para el componente
                    }

                    return mergedEvent
                  })


                  return uniqueEvents
                    .filter(event => {
                      // 1️⃣ Filtrar eventos sin título o con "Sin título"
                      if (!event.title || event.title.trim() === '' ||
                          event.title.toLowerCase() === 'sin título' ||
                          event.title.toLowerCase() === 'sin titulo') {
                        return false
                      }

                    // 2️⃣ Filtrar por categoría si no es "Todos"
                    if (activeCategory !== 'Todos') {
                      const eventCategory = (event.category || '').toLowerCase()
                        .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Eliminar acentos
                      const selectedCategory = activeCategory.toLowerCase()
                        .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Eliminar acentos

                      // Mapeo de categorías en español/inglés (COMPLETO)
                      const categoryMap: Record<string, string[]> = {
                        'musica': ['music', 'musica', 'música'],
                        'deportes': ['sports', 'deportes'],
                        'cultural': ['cultural', 'culture'],
                        'tech': ['tech', 'technology', 'tecnologia', 'tecnología'],
                        'fiestas': ['party', 'fiestas', 'nightlife'],
                        'hobbies': ['hobbies', 'hobby'],
                        'general': ['general'],
                        'cine': ['film', 'movie', 'cinema', 'cine'],
                        'teatro': ['theater', 'theatre', 'teatro'],
                        'comida': ['food', 'comida', 'gastronomy', 'gastronomia', 'gastronomía'],
                        'arte': ['art', 'arte'],
                        'festival': ['festival'],
                        'internacional': ['international', 'internacional']
                      }

                      // Buscar coincidencia
                      let matches = false
                      for (const [key, aliases] of Object.entries(categoryMap)) {
                        if (aliases.includes(selectedCategory)) {
                          // Ver si la categoría del evento coincide con algún alias del grupo
                          matches = aliases.some(alias => eventCategory.includes(alias) || alias.includes(eventCategory))
                          if (matches) break
                        }
                      }

                      // También permitir coincidencia directa parcial
                      if (!matches) {
                        matches = eventCategory.includes(selectedCategory) || selectedCategory.includes(eventCategory)
                      }

                      return matches
                    }

                    return true
                  })
                  .map((event, index) => {
                    const uniqueKey = `${event.title}-${event.start_datetime}-${event.venue_name || ''}-${index}`
                    return (
                      <div
                        key={uniqueKey}
                        className={`${isEventsFadingOut
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
                    )
                  })
                })()}

                {/* Show skeleton cards while streaming */}
                {isStreaming && (
                  <>
                    {Array.from({ length: 2 }).map((_, index) => (
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

      {/* 🤖 Chat flotante de IA */}
      <div className="fixed bottom-4 right-4 z-50">
        {/* Botón flotante cuando está cerrado */}
        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="w-14 h-14 bg-gradient-to-br from-purple-600 to-pink-600 rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-300 flex items-center justify-center group"
          >
            <span className="text-2xl">🤖</span>
            <span className="absolute -top-10 right-0 bg-black/80 text-white text-xs px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              Preguntame sobre eventos
            </span>
          </button>
        )}

        {/* Panel de chat cuando está abierto */}
        {chatOpen && (
          <div className="w-80 sm:w-96 bg-black/90 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🤖</span>
                <span className="text-white font-semibold text-sm">Asistente de Eventos</span>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="text-white/80 hover:text-white text-xl"
              >
                ×
              </button>
            </div>

            {/* Contenido */}
            <div className="p-4 max-h-80 overflow-y-auto">
              {!chatResponse && !chatLoading && (
                <p className="text-white/60 text-sm text-center">
                  ¡Hola! Preguntame sobre eventos, artistas, lugares o cualquier cosa relacionada.
                </p>
              )}

              {chatLoading && (
                <div className="flex items-center justify-center gap-2 py-4">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              )}

              {chatResponse && (
                <div className="space-y-3">
                  <p className="text-white/80 text-sm">{chatResponse.answer}</p>

                  {chatResponse.relatedEvents.length > 0 && (
                    <div className="space-y-2">
                      {chatResponse.relatedEvents.map((event, idx) => (
                        <a
                          key={idx}
                          href={`/event/${event.id}/${event.slug}`}
                          className="block bg-white/10 hover:bg-white/20 rounded-lg p-2 transition-colors"
                        >
                          <p className="text-white text-sm font-medium truncate">{event.title}</p>
                          <p className="text-white/50 text-xs">{event.venue} • {event.date}</p>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-white/10 p-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleChatSubmit()}
                  placeholder="Ej: rock en Córdoba, teatro mañana..."
                  className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-purple-500"
                />
                <button
                  onClick={handleChatSubmit}
                  disabled={chatLoading || !chatMessage.trim()}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {chatLoading ? '...' : '→'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
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