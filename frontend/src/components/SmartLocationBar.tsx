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
  event_count?: number // Para barrios
  is_neighborhood?: boolean // Indica si es un barrio
  parent_city?: string // Ciudad padre del barrio
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

  // 🏘️ Neighborhoods state
  const [neighborhoods, setNeighborhoods] = useState<Map<string, CitySuggestion[]>>(new Map())
  const [expandedCities, setExpandedCities] = useState<Set<string>>(new Set())

  // 🎯 Popular places state
  const [popularPlaces, setPopularPlaces] = useState<string[]>([])
  const [loadingPopularPlaces, setLoadingPopularPlaces] = useState(false)

  // 🎯 Fetch popular places nearby
  const fetchPopularPlaces = async (locationName: string) => {
    if (!locationName || locationName.trim() === '') return

    setLoadingPopularPlaces(true)
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(
        `${API_BASE_URL}/api/popular-places/${encodeURIComponent(locationName)}`
      )

      if (!response.ok) {
        console.warn('Popular places API error:', response.status)
        setPopularPlaces([])
        return
      }

      const data = await response.json()
      if (data.success && data.places && data.places.length > 0) {
        setPopularPlaces(data.places)
        console.log('✅ Lugares populares:', data.places)
      } else {
        setPopularPlaces([])
      }
    } catch (error) {
      console.error('❌ Error fetching popular places:', error)
      setPopularPlaces([])
    } finally {
      setLoadingPopularPlaces(false)
    }
  }

  // Sincronizar con currentLocation cuando cambie
  useEffect(() => {
    if (currentLocation) {
      setLocation(currentLocation)
      // Cargar lugares populares cuando cambie la ubicación
      fetchPopularPlaces(currentLocation.name)
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

  const fetchNeighborhoods = async (cityName: string) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(
        `${API_BASE_URL}/api/neighborhoods/${encodeURIComponent(cityName)}`
      )

      if (!response.ok) {
        console.warn('Neighborhoods API error:', response.status)
        return []
      }

      const data = await response.json()

      if (!data.success || !data.neighborhoods) {
        return []
      }

      // Parsear barrios a formato CitySuggestion
      const neighborhoodSuggestions: CitySuggestion[] = data.neighborhoods.map((n: any) => ({
        display_name: `${n.name} (${n.event_count} eventos)`,
        name: n.name,
        country: 'Argentina',
        state: cityName,
        lat: '0',
        lon: '0',
        event_count: n.event_count,
        is_neighborhood: true,
        parent_city: cityName
      }))

      console.log(`🏘️ Barrios de ${cityName}:`, neighborhoodSuggestions)
      return neighborhoodSuggestions
    } catch (error) {
      console.error('Error fetching neighborhoods:', error)
      return []
    }
  }

  const fetchCitySuggestions = async (query: string) => {
    if (query.length < 3) return

    setIsLoadingSuggestions(true)

    try {
      // Usar backend API para buscar barrios, ciudades, países
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(
        `${API_BASE_URL}/api/cities/available?q=${encodeURIComponent(query)}&limit=5`
      )

      if (!response.ok) {
        console.warn('Backend API error:', response.status)
        setIsLoadingSuggestions(false)
        return
      }

      const data = await response.json()

      if (!data.success || !data.locations) {
        setSuggestions([])
        setShowSuggestions(false)
        setIsLoadingSuggestions(false)
        return
      }

      // 🏘️ Procesar resultados: separar barrios y ciudades
      const cities: CitySuggestion[] = []
      const neighborhoodsByCity: Map<string, CitySuggestion[]> = new Map()

      data.locations.forEach((item: any) => {
        if (item.location_type === 'barrio' && item.city) {
          // Es un barrio
          const parentCity = item.city
          const neighborhood: CitySuggestion = {
            display_name: `${item.location} (${item.event_count} eventos)`,
            name: item.location,
            country: item.country || 'Argentina',
            state: parentCity,
            lat: '0',
            lon: '0',
            event_count: item.event_count,
            is_neighborhood: true,
            parent_city: parentCity
          }

          // Agrupar barrio bajo ciudad
          if (!neighborhoodsByCity.has(parentCity)) {
            neighborhoodsByCity.set(parentCity, [])
          }
          neighborhoodsByCity.get(parentCity)!.push(neighborhood)

          // Asegurarse de que la ciudad padre esté en la lista
          if (!cities.find(c => c.name === parentCity)) {
            cities.push({
              display_name: parentCity,
              name: parentCity,
              country: item.country || 'Argentina',
              state: '',
              lat: '0',
              lon: '0'
            })
          }
        } else {
          // Es ciudad o país
          cities.push({
            display_name: item.displayName,
            name: item.location,
            country: item.country || item.location_type,
            state: item.city || '',
            lat: '0',
            lon: '0'
          })
        }
      })

      console.log('🔍 Ciudades:', cities)
      console.log('🏘️ Barrios por ciudad:', neighborhoodsByCity)

      // Actualizar estado de barrios y expandir ciudades con barrios
      const newNeighborhoods = new Map(neighborhoods)
      const citiesToExpand = new Set<string>()

      neighborhoodsByCity.forEach((barrios, ciudad) => {
        newNeighborhoods.set(ciudad, barrios)
        citiesToExpand.add(ciudad)
      })

      setNeighborhoods(newNeighborhoods)
      setExpandedCities(citiesToExpand)

      setSuggestions(cities)
      setShowSuggestions(cities.length > 0)
      setIsLoadingSuggestions(false)
    } catch (error) {
      console.error('Error fetching city suggestions:', error)
      setIsLoadingSuggestions(false)
      setSuggestions([])
    }
  }

  const selectSuggestion = (suggestion: CitySuggestion) => {
    // 🌍 Si es un barrio (tiene state), usar solo el nombre del barrio para búsqueda
    // pero mostrar la ciudad padre en la UI
    let locationName = suggestion.name  // Solo el barrio/ciudad, no el formato completo

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
    console.log('🏙️ Ciudad padre (si es barrio):', suggestion.state || 'N/A')

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
    // 🔒 NO ejecutar si ya hay ubicación válida (GPS o manual)
    if (currentLocation && currentLocation.detected !== 'fallback') {
      console.log('✅ Ya hay ubicación válida, no re-detectar:', currentLocation.name)
      return
    }

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

              let cityName = data.locality || data.city

              // 🔧 CORRECCIÓN: Villa Gesell está en coordenadas aproximadas: lat -37.26, lon -56.97
              // Si el servicio devuelve "La Pampa" pero las coordenadas están en Villa Gesell, corregir
              if ((cityName === 'La Pampa' || data.principalSubdivision === 'La Pampa') &&
                  latitude > -37.5 && latitude < -37.0 &&
                  longitude > -57.2 && longitude < -56.7) {
                console.log('🔧 Corrección aplicada: La Pampa → Villa Gesell (coordenadas GPS correctas)')
                cityName = 'Villa Gesell'
              }

              const detectedLocation: Location = {
                name: `${cityName}, ${data.countryName}`,
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
      // 🔒 NO sobrescribir si ya hay una ubicación válida detectada
      if (currentLocation && currentLocation.detected !== 'fallback') {
        console.log('✅ Ya hay ubicación válida, no sobrescribir con IP:', currentLocation.name)
        setIsDetecting(false)
        return
      }

      // Usar IP geolocation como fallback SOLO si no hay ubicación previa
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

            {/* 🏙️ Mostrar ciudad principal detectada - CLICKEABLE */}
            {expandedSearch && parentCityDetected ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const cityLocation: Location = {
                      name: parentCityDetected,
                      detected: 'manual'
                    }
                    setLocation(cityLocation)
                    onLocationChange(cityLocation)
                  }}
                  className="text-white font-medium hover:text-blue-300 transition-colors cursor-pointer underline decoration-dotted"
                  title={`Buscar todos los eventos en ${parentCityDetected}`}
                >
                  {parentCityDetected}
                </button>

                {/* 🚫 NO mostrar contador aquí - es el count del barrio, no de la ciudad */}
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
                    <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 backdrop-blur-xl border border-white/20 rounded-xl overflow-hidden z-50 shadow-2xl max-h-96 overflow-y-auto">
                      {suggestions.map((suggestion, index) => {
                        const cityNeighborhoods = neighborhoods.get(suggestion.name) || []
                        const isCityExpanded = expandedCities.has(suggestion.name)
                        const hasNeighborhoods = cityNeighborhoods.length > 0

                        return (
                          <div key={index}>
                            {/* Ciudad */}
                            <button
                              onClick={() => selectSuggestion(suggestion)}
                              className="w-full px-4 py-3 text-left hover:bg-white/10 transition-colors border-b border-white/10 group"
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
                                {hasNeighborhoods && (
                                  <svg
                                    className={`w-4 h-4 text-white/60 transition-transform ${isCityExpanded ? 'rotate-180' : ''}`}
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                                  </svg>
                                )}
                              </div>
                            </button>

                            {/* Barrios (si está expandido) */}
                            {hasNeighborhoods && isCityExpanded && (
                              <div className="bg-black/50">
                                {cityNeighborhoods.map((neighborhood, nIndex) => (
                                  <button
                                    key={nIndex}
                                    onClick={() => selectSuggestion(neighborhood)}
                                    className="w-full pl-12 pr-4 py-2 text-left hover:bg-white/10 transition-colors border-b border-white/5 last:border-b-0 group"
                                  >
                                    <div className="flex items-center gap-2">
                                      <svg className="w-4 h-4 text-blue-300/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
                                      </svg>
                                      <div className="flex-1">
                                        <div className="text-white/90 text-sm group-hover:text-blue-300 transition-colors">
                                          {neighborhood.name}
                                        </div>
                                        <div className="text-white/40 text-xs">
                                          {neighborhood.event_count} eventos
                                        </div>
                                      </div>
                                    </div>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )
                      })}
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

      {/* 🎯 Popular Places - Top 3 lugares cercanos */}
      {location && popularPlaces.length > 0 && (
        <div className="text-center mt-3">
         
          <div className="flex justify-center gap-2 flex-wrap">
            {popularPlaces.map((place, index) => (
              <button
                key={index}
                onClick={() => {
                  const newLocation: Location = {
                    name: place,
                    coordinates: undefined,
                    detected: 'manual'
                  }
                  setLocation(newLocation)
                  onLocationChange(newLocation)
                  setManualInput('')
                  setShowManualInput(false)
                }}
                className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white/80 text-md font-large hover:bg-white/20 transition-colors cursor-pointer"
              >
                {place}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading state para lugares populares */}
      {location && loadingPopularPlaces && (
        <div className="text-center mt-3">
          <div className="flex justify-center gap-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="px-3 py-1 bg-white/5 backdrop-blur-sm rounded-full animate-pulse"
                style={{ width: '80px', height: '26px' }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SmartLocationBar