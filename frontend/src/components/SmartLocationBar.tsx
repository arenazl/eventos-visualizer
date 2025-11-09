import React, { useState, useEffect, useRef } from 'react'
import { LocationLoader } from './LoadingStates'

interface Location {
  name: string
  coordinates?: { lat: number; lng: number }
  country?: string
  detected: 'gps' | 'manual' | 'prompt' | 'fallback'
}

interface CitySuggestion {
  display_name: string
  name: string
  country: string
  state?: string
  lat: string
  lon: string
}

interface SmartLocationBarProps {
  onLocationChange: (location: Location) => void
  currentLocation?: Location

  // 🏙️ Metadata de búsqueda expandida
  parentCityDetected?: string | null
  searchLocationQuery?: string | null
  expandedSearch?: boolean
  totalEvents?: number
}

export const SmartLocationBar: React.FC<SmartLocationBarProps> = ({
  onLocationChange,
  currentLocation,
  parentCityDetected,
  searchLocationQuery,
  expandedSearch,
  totalEvents
}) => {
  const [location, setLocation] = useState<Location | null>(currentLocation || null)
  const [isDetecting, setIsDetecting] = useState(false)
  const [showManualInput, setShowManualInput] = useState(false)
  const [manualInput, setManualInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  // 🔍 Autocomplete states
  const [suggestions, setSuggestions] = useState<CitySuggestion[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [hasSelectedFromDropdown, setHasSelectedFromDropdown] = useState(false) // 🔒 Solo permitir búsqueda si seleccionó del dropdown
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  // Sincronizar con currentLocation cuando cambie
  useEffect(() => {
    if (currentLocation) {
      setLocation(currentLocation)
    }
  }, [currentLocation])

  // 🔍 Autocomplete con Nominatim (debounced)
  useEffect(() => {
    // 🔒 Resetear flag cuando el usuario escribe (no ha seleccionado aún)
    setHasSelectedFromDropdown(false)

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    if (manualInput.trim().length >= 3) {
      debounceTimer.current = setTimeout(() => {
        fetchCitySuggestions(manualInput)
      }, 500) // Debounce de 500ms
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
    }
  }, [manualInput])

  const fetchCitySuggestions = async (query: string) => {
    if (query.length < 3) return

    setIsLoadingSuggestions(true)

    try {
      // Nominatim API (OpenStreetMap) - Gratis, sin API key
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` +
        `q=${encodeURIComponent(query)}&` +
        `format=json&` +
        `addressdetails=1&` +
        `limit=5&` +
        `featuretype=city`,
        {
          headers: {
            'User-Agent': 'EventosVisualizerApp/1.0' // Requerido por Nominatim
          }
        }
      )

      if (!response.ok) {
        console.warn('Nominatim API error:', response.status)
        setIsLoadingSuggestions(false)
        return
      }

      const data = await response.json()

      // Parsear resultados a formato CitySuggestion
      const parsedSuggestions: CitySuggestion[] = data
        .filter((item: any) =>
          item.type === 'city' ||
          item.type === 'town' ||
          item.type === 'administrative' ||
          item.class === 'place'
        )
        .map((item: any) => ({
          display_name: item.display_name,
          name: item.address?.city || item.address?.town || item.address?.village || item.name,
          country: item.address?.country || '',
          state: item.address?.state || item.address?.province || '',
          lat: item.lat,
          lon: item.lon
        }))

      console.log('🔍 Nominatim sugerencias:', parsedSuggestions)

      setSuggestions(parsedSuggestions.slice(0, 5))
      setShowSuggestions(parsedSuggestions.length > 0)
      setIsLoadingSuggestions(false)
    } catch (error) {
      console.error('Error fetching city suggestions:', error)
      setIsLoadingSuggestions(false)
      setSuggestions([])
    }
  }

  const selectSuggestion = (suggestion: CitySuggestion) => {
    // 🌍 Formato inteligente: incluir estado si está disponible
    let locationName = suggestion.name
    if (suggestion.state) {
      locationName = `${suggestion.name}, ${suggestion.state}, ${suggestion.country}`
    } else {
      locationName = `${suggestion.name}, ${suggestion.country}`
    }

    const selectedLocation: Location = {
      name: locationName,
      coordinates: {
        lat: parseFloat(suggestion.lat),
        lng: parseFloat(suggestion.lon)
      },
      country: suggestion.country,
      detected: 'manual'
    }

    console.log('✅ Ubicación seleccionada del dropdown:', selectedLocation)

    setLocation(selectedLocation)
    onLocationChange(selectedLocation)
    setManualInput('')
    setShowManualInput(false)
    setShowSuggestions(false)
    setSuggestions([])
    setHasSelectedFromDropdown(true) // ✅ Marca que se seleccionó del dropdown
  }

  // NO auto-detectar ubicación por IP - dejamos que Gemini maneje todo
  // Comentado porque interfiere con la detección de Gemini
  // useEffect(() => {
  //   if (!currentLocation && !location) {
  //     detectLocation()
  //   }
  // }, [])

  const detectLocation = async () => {
    setIsDetecting(true)
    setError(null)

    try {
      // 1. Intentar geolocalización HTML5
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            const { latitude, longitude } = position.coords
            
            // Geocodificación reversa con API pública
            try {
              const response = await fetch(
                `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=es`
              )
              const data = await response.json()
              
              const detectedLocation: Location = {
                name: `${data.locality || data.city}, ${data.countryName}`,
                coordinates: { lat: latitude, lng: longitude },
                country: data.countryName,
                detected: 'gps'
              }
              
              setLocation(detectedLocation)
              onLocationChange(detectedLocation)
            } catch {
              // Fallback si falla geocoding
              const fallbackLocation: Location = {
                name: `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
                coordinates: { lat: latitude, lng: longitude },
                detected: 'gps'
              }
              setLocation(fallbackLocation)
              onLocationChange(fallbackLocation)
            }
            
            setIsDetecting(false)
          },
          async (error) => {
            console.warn('Geolocation failed:', error)
            await fallbackToIPLocation()
          },
          { timeout: 10000, enableHighAccuracy: true }
        )
      } else {
        await fallbackToIPLocation()
      }
    } catch (err) {
      await fallbackToIPLocation()
    }
  }

  const fallbackToIPLocation = async () => {
    try {
      // Usar IP geolocation como fallback
      const response = await fetch('https://ipapi.co/json/')
      const data = await response.json()
      
      const ipLocation: Location = {
        name: `${data.city}, ${data.country_name}`,
        coordinates: { lat: data.latitude, lng: data.longitude },
        country: data.country_name,
        detected: 'fallback'
      }
      
      setLocation(ipLocation)
      onLocationChange(ipLocation)
      setIsDetecting(false)
    } catch {
      // Si falla la detección IP, no establecer ubicación por defecto
      setIsDetecting(false)
      setError('No se pudo detectar tu ubicación')
    }
  }

  // 🔒 ELIMINADA - Ya no permitimos texto libre, solo selección del dropdown

  const getLocationIcon = (detected: Location['detected']) => {
    switch (detected) {
      case 'gps':
        return (
          <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        )
      case 'manual':
        return (
          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
          </svg>
        )
      case 'fallback':
        return (
          <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9"></path>
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="mb-6">
      {/* Barra de ubicación actual */}
      <div className="flex items-center justify-center gap-4 mb-4">
        {isDetecting ? (
          <LocationLoader />
        ) : location ? (
          <div className="flex items-center gap-3 px-6 py-3 bg-white/10 backdrop-blur-xl rounded-full border border-white/20 hover:border-white/40 transition-all duration-300">
            {getLocationIcon(location.detected)}

            {/* 🏙️ Mostrar expansión de búsqueda si existe */}
            {expandedSearch && searchLocationQuery && parentCityDetected ? (
              <div className="flex items-center gap-2">
                <span className="text-white/80 font-medium">{searchLocationQuery}</span>
                <svg className="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                </svg>
                <span className="text-white font-medium">{parentCityDetected}</span>

                {/* Contador de eventos si está disponible */}
                {totalEvents !== undefined && totalEvents > 0 && (
                  <span className="ml-2 px-2 py-1 bg-purple-500/30 rounded-full text-xs text-purple-200 font-medium">
                    {totalEvents} eventos
                  </span>
                )}
              </div>
            ) : (
              <span className="text-white font-medium">{location.name || "🎩 En Wonderland"}</span>
            )}

            {/* Botón para cambiar ubicación */}
            <button
              onClick={() => setShowManualInput(true)}
              className="ml-2 p-1 hover:bg-white/10 rounded-full transition-colors"
              title="Cambiar ubicación"
            >
              <svg className="w-4 h-4 text-white/60 hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
              </svg>
            </button>
          </div>
        ) : (
          <button
            onClick={detectLocation}
            className="flex items-center gap-3 px-6 py-3 bg-purple-500/20 backdrop-blur-xl rounded-full border border-purple-400/30 hover:border-purple-400/60 transition-all duration-300"
          >
            <svg className="w-5 h-5 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            </svg>
            <span className="text-purple-200 font-medium">Detectar mi ubicación</span>
          </button>
        )}
      </div>

      {/* Input manual de ubicación con Autocomplete */}
      {showManualInput && (
        <div className="max-w-md mx-auto">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 rounded-2xl blur opacity-50"></div>
            <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-4">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    placeholder="Escribe al menos 3 caracteres para buscar..."
                    className="w-full bg-transparent text-white placeholder-white/50 border-none outline-none text-lg"
                    autoFocus
                  />

                  {/* 🔒 Mensaje: Solo se permite selección del dropdown */}
                  {manualInput.trim().length >= 3 && !isLoadingSuggestions && suggestions.length === 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 px-4 py-3 bg-yellow-500/20 backdrop-blur-xl border border-yellow-400/30 rounded-xl text-yellow-200 text-sm">
                      ⚠️ No se encontraron ubicaciones. Intenta con otra búsqueda.
                    </div>
                  )}

                  {/* 🔍 Autocomplete Dropdown */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 backdrop-blur-xl border border-white/20 rounded-xl overflow-hidden z-50 shadow-2xl">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => selectSuggestion(suggestion)}
                          className="w-full px-4 py-3 text-left hover:bg-white/10 transition-colors border-b border-white/10 last:border-b-0 group"
                        >
                          <div className="flex items-center gap-3">
                            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                            </svg>
                            <div className="flex-1">
                              <div className="text-white font-medium group-hover:text-blue-300 transition-colors">
                                {suggestion.name}
                              </div>
                              <div className="text-white/60 text-sm">
                                {suggestion.state && `${suggestion.state}, `}{suggestion.country}
                              </div>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Loading spinner para autocomplete */}
                  {isLoadingSuggestions && (
                    <div className="absolute right-0 top-1/2 -translate-y-1/2">
                      <svg className="animate-spin h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {/* 🔒 Solo botón de cancelar - Usuario DEBE seleccionar del dropdown */}
                  <button
                    onClick={() => {
                      setShowManualInput(false)
                      setManualInput('')
                      setShowSuggestions(false)
                      setSuggestions([])
                      setHasSelectedFromDropdown(false)
                    }}
                    className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-lg transition-colors"
                    title="Cancelar"
                  >
                    ✗
                  </button>
                </div>
              </div>

              {/* 💡 Hint: Debe seleccionar del dropdown */}
              <div className="mt-3 text-center text-white/60 text-sm">
                💡 Selecciona una ubicación de la lista para continuar
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error state - Solo mostrar si hay error Y no hay ubicación */}
      {error && !location && (
        <div className="text-center">
          <p className="text-red-300 text-sm">{error}</p>
          <button
            onClick={() => setShowManualInput(true)}
            className="mt-2 text-white/60 hover:text-white text-sm underline"
          >
            Ingresar ubicación manualmente
          </button>
        </div>
      )}

      {/* Hint sobre búsquedas inteligentes */}
      {location && (
        <div className="text-center mt-4">
          <p className="text-white/50 text-sm">
            {location.detected === 'manual' ? (
              <span>🎯 Ubicación de búsqueda: <strong>{location.name}</strong></span>
            ) : (
              <>💡 Tip: Escribe "bares en Barcelona" para cambiar la ubicación automáticamente</>
            )}
          </p>
        </div>
      )}
    </div>
  )
}

export default SmartLocationBar