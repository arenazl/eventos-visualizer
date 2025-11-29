import React, { useState, useEffect, useRef } from 'react'
import { MagnifyingGlassIcon, MapPinIcon } from '@heroicons/react/24/outline'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import GoogleLoginButton from './auth/GoogleLoginButton'

interface LocationSuggestion {
  name: string
  displayName: string
  country: string  // Nombre completo del país
  countryCode: string  // Código ISO para la bandera
  lat: number
  lon: number
}

interface HeaderProps {
  searchQuery?: string
  onSearchChange?: (value: string) => void
  onSearchSubmit?: () => void
  onVoiceSearch?: () => void
  onLocationClick?: () => void
  isSearching?: boolean
  onLocationSelect?: (location: LocationSuggestion) => void
  showBackButton?: boolean
  onBackClick?: () => void
  currentLocation?: string
}

const Header: React.FC<HeaderProps> = ({
  searchQuery = '',
  onSearchChange = () => {},
  onSearchSubmit = () => {},
  onVoiceSearch = () => {},
  onLocationClick = () => {},
  isSearching = false,
  onLocationSelect = () => {},
  showBackButton = false,
  onBackClick = () => {},
  currentLocation
}) => {
  const navigate = useNavigate()
  const [isScrolled, setIsScrolled] = useState(false)
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1) // ⌨️ Índice de sugerencia seleccionada con teclado
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const justSelectedRef = useRef(false) // 🔒 Evita reabrir dropdown después de seleccionar
  const abortControllerRef = useRef<AbortController | null>(null) // 🛑 Cancela requests anteriores
  const cacheRef = useRef<Map<string, LocationSuggestion[]>>(new Map()) // 💾 Cache de sugerencias
  const [nearbyCitiesLoaded, setNearbyCitiesLoaded] = useState(false) // 🌍 Ciudades cercanas ya cargadas
  const [isHoveringInput, setIsHoveringInput] = useState(false) // 🖱️ Mouse sobre input

  useEffect(() => {
    let lastScrollY = window.scrollY

    const handleScroll = () => {
      const currentScrollY = window.scrollY

      // Hysteresis: diferentes thresholds para evitar oscilación
      if (currentScrollY > lastScrollY) {
        // Scrolling DOWN: activar después de 100px
        if (currentScrollY > 100) {
          setIsScrolled(true)
        }
      } else {
        // Scrolling UP: desactivar antes de 20px
        if (currentScrollY < 20) {
          setIsScrolled(false)
        }
      }

      lastScrollY = currentScrollY
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // 🔍 Buscar sugerencias de ubicación con debounce y cache
  useEffect(() => {
    const fetchSuggestions = async () => {
      // 🔒 NO abrir si acabamos de seleccionar del dropdown
      if (justSelectedRef.current) {
        return
      }

      if (!searchQuery || searchQuery.length < 3) {
        setSuggestions([])
        setShowSuggestions(false)
        return
      }

      // 💾 Verificar cache primero
      const cachedResults = cacheRef.current.get(searchQuery.toLowerCase())
      if (cachedResults) {
        console.log('✅ Cache hit para:', searchQuery)
        setSuggestions(cachedResults)
        setShowSuggestions(cachedResults.length > 0)
        return
      }

      // 🛑 Cancelar request anterior si existe
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      // 🆕 Crear nuevo AbortController
      const abortController = new AbortController()
      abortControllerRef.current = abortController

      setIsLoadingSuggestions(true)

      try {
        // 🗄️ Usar backend para obtener solo ciudades con eventos
        console.log('📱 [HEADER-DEBUG] Fetching suggestions para:', searchQuery)
        const response = await fetch(
          `${API_BASE_URL}/api/cities/available?q=${encodeURIComponent(searchQuery)}&limit=5`,
          { signal: abortController.signal }
        )

        // ⚠️ Si el request fue cancelado, no continuar
        if (abortController.signal.aborted) {
          return
        }

        const data = await response.json()
        console.log('📱 [HEADER-DEBUG] Response recibida:', data)

        // 📋 Mapear respuesta del backend al formato LocationSuggestion
        const locationSuggestions: LocationSuggestion[] = (data.locations || []).map((item: any) => {
          return {
            name: item.location,
            displayName: item.displayName || `${item.location} (${item.event_count} eventos)`,
            country: item.country || '', // País real (Argentina, España, etc.)
            countryCode: '',
            lat: 0,
            lon: 0
          }
        })

        // 💾 Guardar en cache
        cacheRef.current.set(searchQuery.toLowerCase(), locationSuggestions)
        console.log('💾 Guardado en cache:', searchQuery, locationSuggestions.length, 'ubicaciones con eventos (ciudades/provincias/países)')

        setSuggestions(locationSuggestions)
        setShowSuggestions(locationSuggestions.length > 0)
      } catch (error: any) {
        // ⚠️ Si es AbortError, no mostrar error (es normal)
        if (error instanceof Error && error.name === 'AbortError') {
          console.log('⏹️ Request cancelado:', searchQuery)
          return
        }
        console.error('❌ [HEADER-ERROR] Error fetching suggestions:', error)
        // 📱 ALERT PARA MÓVIL
        alert(`[ERROR fetchSuggestions]\nMessage: ${error?.message || 'Unknown'}\nURL: /api/cities/available`)
        setSuggestions([])
      } finally {
        setIsLoadingSuggestions(false)
      }
    }

    // 🕐 Debounce aumentado a 600ms para reducir requests
    const debounceTimer = setTimeout(fetchSuggestions, 600)
    return () => {
      clearTimeout(debounceTimer)
      // 🛑 Cleanup: Cancelar request si el componente se desmonta o searchQuery cambia
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [searchQuery])

  // Resetear índice seleccionado cuando cambien las sugerencias
  useEffect(() => {
    setSelectedIndex(-1)
  }, [suggestions])

  // Cerrar sugerencias al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // ⬇️ Flecha abajo - mover al siguiente
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!showSuggestions && suggestions.length > 0) {
        setShowSuggestions(true)
      }
      setSelectedIndex(prev =>
        prev < suggestions.length - 1 ? prev + 1 : prev
      )
    }
    // ⬆️ Flecha arriba - mover al anterior
    else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
    }
    // ↩️ Enter - seleccionar sugerencia o buscar
    else if (e.key === 'Enter') {
      e.preventDefault()
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        // Seleccionar la sugerencia resaltada
        handleSuggestionClick(suggestions[selectedIndex])
      } else {
        // Buscar con el texto actual
        setShowSuggestions(false)
        onSearchSubmit()
      }
    }
    // ⎋ Escape - cerrar sugerencias
    else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setSelectedIndex(-1)
    }
  }

  const handleSuggestionClick = (suggestion: LocationSuggestion) => {
    // 🔒 Marcar que acabamos de seleccionar (evita reabrir dropdown)
    justSelectedRef.current = true

    // Llenar el input con el texto (solo el nombre de la ciudad)
    onSearchChange(suggestion.name)
    setShowSuggestions(false)

    // 🔥 Actualizar la ubicación en el store y ejecutar búsqueda
    onLocationSelect({
      name: suggestion.name,
      country: suggestion.country || '',
      lat: suggestion.lat,
      lon: suggestion.lon
    })

    // 🔒 Resetear flag después de 1 segundo
    setTimeout(() => {
      justSelectedRef.current = false
    }, 1000)
  }

  // 🔒 Lock para prevenir llamadas concurrentes
  const isLoadingNearbyCitiesRef = React.useRef(false)

  // 🌍 Cargar ciudades cercanas basadas en IP al hacer hover
  const handleInputHover = async () => {
    // Si ya se cargaron o el usuario ya está escribiendo, no hacer nada
    if (nearbyCitiesLoaded || searchQuery.length > 0) {
      return
    }

    // 🔒 LOCK: Prevenir llamadas concurrentes
    if (isLoadingNearbyCitiesRef.current) {
      console.log('⏸️ Ya hay una llamada en progreso - ignorando hover duplicado')
      return
    }

    // Establecer lock INMEDIATAMENTE
    isLoadingNearbyCitiesRef.current = true

    setIsLoadingSuggestions(true)
    setShowSuggestions(true)
    setIsHoveringInput(true)

    try {
      // Si no hay ubicación actual, no mostrar nada
      if (!currentLocation) {
        console.log('No hay ubicacion actual para mostrar ciudades cercanas')
        setSuggestions([])
        return
      }

      console.log(`🔍 [HEADER-DEBUG] Buscando ciudades cercanas a: ${currentLocation}`)

      // Pedir a IA ciudades cercanas a la ubicacion actual
      const nearbyResponse = await fetch(
        `${API_BASE_URL}/api/ai/nearby-cities?location=${encodeURIComponent(currentLocation)}&limit=10`
      )
      const nearbyData = await nearbyResponse.json()
      console.log('📱 [HEADER-DEBUG] Nearby cities response:', nearbyData)

      if (nearbyData.success && nearbyData.cities) {
        // Mapear ciudades cercanas a LocationSuggestion
        const nearbyCities: LocationSuggestion[] = nearbyData.cities.map((city: any) => ({
          name: city.name,
          displayName: city.displayName || `${city.name} (${city.distance || 'Cercana'})`,
          country: city.country || '',
          countryCode: city.countryCode || '',
          lat: city.lat || 0,
          lon: city.lon || 0
        }))

        setSuggestions(nearbyCities)
        setNearbyCitiesLoaded(true)
        console.log(`✅ Ciudades cercanas cargadas: ${nearbyCities.length}`)
      }
    } catch (error: any) {
      console.error('❌ [HEADER-ERROR] Error loading nearby cities:', error)
      // 📱 ALERT PARA MÓVIL
      alert(`[ERROR handleInputHover]\nMessage: ${error?.message || 'Unknown'}\nURL: /api/ai/nearby-cities`)
      setSuggestions([])
    } finally {
      setIsLoadingSuggestions(false)
      // Liberar lock
      isLoadingNearbyCitiesRef.current = false
    }
  }

  return (
    <header className={`backdrop-blur-3xl bg-white/5 sticky top-0 z-50 transition-all duration-300 border-b border-white/10 ${
      isScrolled ? 'py-1.5 md:py-2' : 'py-2 md:py-3'
    }`}>
      <div className="max-w-7xl mx-auto px-2 md:px-6">
        <div className="flex items-center justify-between gap-1.5 md:gap-6">
          {/* Logo a la izquierda con flecha opcional - más compacto en mobile */}
          <div className="flex items-center gap-1 md:gap-3 flex-shrink-0">
            {showBackButton && (
              <button
                onClick={onBackClick}
                className="p-1 md:p-2 hover:bg-white/10 rounded-full transition-colors text-white/80 hover:text-white active:scale-95"
                title="Volver"
              >
                <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <h1
              onClick={() => navigate('/')}
              className={`font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 tracking-wider transition-all duration-300 cursor-pointer active:scale-95 md:hover:scale-105 ${
              isScrolled ? 'text-sm md:text-xl' : 'text-base md:text-2xl'
            }`}>
              <span className="hidden sm:inline">FunAroundYou ✨</span>
              <span className="sm:hidden">Fun ✨</span>
            </h1>
          </div>

          {/* Buscador en el medio - más compacto en mobile */}
          <div className="flex-1 max-w-2xl">
            <div className="relative group" ref={suggestionsRef}>
              <div className="relative bg-black/40 backdrop-blur-xl border border-white/30 rounded-full shadow-lg hover:shadow-xl transition-all duration-300">
                <div className="flex items-center gap-1 md:gap-2 px-2 md:px-4">
                  <MagnifyingGlassIcon className="w-4 h-4 md:w-5 md:h-5 text-white/60 flex-shrink-0" />

                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      console.log('🔥 Header onChange:', e.target.value)
                      onSearchChange(e.target.value)
                      // Resetear ciudades cercanas para permitir búsqueda en DB
                      if (e.target.value.length > 0) {
                        setNearbyCitiesLoaded(false)
                      }
                    }}
                    onKeyDown={handleKeyDown}
                    onFocus={() => {
                      if (searchQuery.length >= 3 && suggestions.length > 0) {
                        setShowSuggestions(true)
                      }
                    }}
                    placeholder={currentLocation || "Ciudad, provincia o país..."}
                    className={`w-full bg-transparent text-white placeholder-white/60 outline-none font-medium transition-all duration-300 ${
                      isScrolled ? 'py-1.5 text-xs md:text-sm' : 'py-2 md:py-3 text-xs md:text-base'
                    }`}
                  />

                  {/* Botón para limpiar texto (X) */}
                  {searchQuery.length > 0 && (
                    <button
                      onClick={() => {
                        onSearchChange('')
                        setNearbyCitiesLoaded(false)
                        setSuggestions([])
                        setShowSuggestions(false)
                      }}
                      className="p-2 rounded-full transition-all duration-300 bg-white/10 hover:bg-white/20 active:scale-95 flex-shrink-0"
                      title="Limpiar búsqueda"
                    >
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}

                  <button
                    onClick={onVoiceSearch}
                    className="hidden md:block p-2 rounded-full transition-all duration-300 bg-white/10 hover:bg-white/20 active:scale-95 flex-shrink-0"
                    title="Búsqueda por voz"
                  >
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                      <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                  </button>
                  <button
                    onClick={onSearchSubmit}
                    disabled={isSearching}
                    className={`p-1.5 md:p-2 rounded-full transition-all duration-300 flex-shrink-0 active:scale-90 ${
                      isSearching
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-700'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 md:hover:from-purple-500 md:hover:to-pink-500'
                    } disabled:opacity-50 ${isLoadingSuggestions ? 'animate-spin' : ''}`}
                    title="Buscar"
                  >
                    {isSearching ? (
                      <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    ) : (
                      <MagnifyingGlassIcon className="w-4 h-4 md:w-5 md:h-5 text-white" />
                    )}
                  </button>
                </div>
              </div>

              {/* Dropdown de sugerencias - mejor para mobile */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900/95 backdrop-blur-xl border border-white/20 rounded-xl md:rounded-2xl shadow-2xl overflow-hidden z-50 max-h-[60vh] overflow-y-auto">
                  {isLoadingSuggestions && (
                    <div className="p-4 text-center text-white/60">
                      <div className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    </div>
                  )}
                  {!isLoadingSuggestions && suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`w-full px-3 md:px-4 py-2.5 md:py-3 text-left transition-colors border-b border-white/5 last:border-b-0 group active:scale-[0.98] ${
                        selectedIndex === index
                          ? 'bg-gradient-to-r from-purple-600/30 to-pink-600/30'
                          : 'hover:bg-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-2 md:gap-3">
                        <MapPinIcon className={`w-4 h-4 md:w-5 md:h-5 flex-shrink-0 ${
                          selectedIndex === index ? 'text-pink-400' : 'text-purple-400'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="text-white font-medium truncate text-sm md:text-base">{suggestion.name}</div>
                          <div className="text-white/50 text-xs md:text-sm truncate">{suggestion.displayName}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Botones a la derecha - más compacto en mobile */}
          <div className="flex items-center gap-1 md:gap-3 flex-shrink-0">
            <button
              onClick={onLocationClick}
              className="p-1.5 md:p-2 text-white/70 hover:text-white transition-colors rounded-full hover:bg-white/10 active:scale-95"
              title="Cambiar ubicación"
            >
              <MapPinIcon className="h-5 w-5 md:h-6 md:w-6" />
            </button>
            <GoogleLoginButton />
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header