import React, { useState, useEffect } from 'react'
import { LocationLoader } from './LoadingStates'

interface Location {
  name: string
  coordinates?: { lat: number; lng: number }
  country?: string
  detected: 'gps' | 'manual' | 'prompt' | 'fallback'
}

interface SmartLocationBarProps {
  onLocationChange: (location: Location) => void
  currentLocation?: Location
}

export const SmartLocationBar: React.FC<SmartLocationBarProps> = ({ 
  onLocationChange, 
  currentLocation 
}) => {
  const [location, setLocation] = useState<Location | null>(currentLocation || null)
  const [isDetecting, setIsDetecting] = useState(false)
  const [showManualInput, setShowManualInput] = useState(false)
  const [manualInput, setManualInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Sincronizar con currentLocation cuando cambie
  useEffect(() => {
    if (currentLocation) {
      setLocation(currentLocation)
    }
  }, [currentLocation])

  // Auto-detectar ubicación al montar
  useEffect(() => {
    if (!currentLocation && !location) {
      detectLocation()
    }
  }, [])

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
      // Último fallback - Buenos Aires por defecto
      const defaultLocation: Location = {
        name: 'Buenos Aires',
        coordinates: { lat: -34.6037, lng: -58.3816 },
        country: 'Argentina',
        detected: 'fallback'
      }
      setLocation(defaultLocation)
      onLocationChange(defaultLocation)
      setIsDetecting(false)
      setError('No se pudo detectar tu ubicación')
    }
  }

  const handleManualLocationSubmit = async () => {
    if (!manualInput.trim()) return

    setIsDetecting(true)
    
    // Aquí podrías enviar a Gemini para parsear ubicaciones complejas
    // Por ejemplo: "eventos en la costa argentina" -> detectar ciudades costeras
    
    try {
      // Geocodificación simple con API pública
      const response = await fetch(
        `https://api.bigdatacloud.net/data/forward-geocode?query=${encodeURIComponent(manualInput)}&key=YOUR_API_KEY`
      )
      
      if (response.ok) {
        const data = await response.json()
        if (data.results && data.results[0]) {
          const result = data.results[0]
          const manualLocation: Location = {
            name: manualInput,
            coordinates: { lat: result.latitude, lng: result.longitude },
            country: result.country,
            detected: 'manual'
          }
          setLocation(manualLocation)
          onLocationChange(manualLocation)
        }
      } else {
        // Fallback - aceptar texto como está
        const textLocation: Location = {
          name: manualInput,
          detected: 'manual'
        }
        setLocation(textLocation)
        onLocationChange(textLocation)
      }
      
      setShowManualInput(false)
      setManualInput('')
      setIsDetecting(false)
    } catch {
      // Aceptar input manual sin geocodificar
      const textLocation: Location = {
        name: manualInput,
        detected: 'manual'
      }
      setLocation(textLocation)
      onLocationChange(textLocation)
      setShowManualInput(false)
      setManualInput('')
      setIsDetecting(false)
    }
  }

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
            <span className="text-white font-medium">{location.name}</span>
            
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

      {/* Input manual de ubicación */}
      {showManualInput && (
        <div className="max-w-md mx-auto">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 rounded-2xl blur opacity-50"></div>
            <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={manualInput}
                  onChange={(e) => setManualInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleManualLocationSubmit()}
                  placeholder="Ej: Buenos Aires, Santiago, eventos en Mendoza..."
                  className="flex-1 bg-transparent text-white placeholder-white/50 border-none outline-none text-lg"
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleManualLocationSubmit}
                    disabled={isDetecting}
                    className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-200 rounded-lg transition-colors disabled:opacity-50"
                  >
                    ✓
                  </button>
                  <button
                    onClick={() => {
                      setShowManualInput(false)
                      setManualInput('')
                    }}
                    className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-lg transition-colors"
                  >
                    ✗
                  </button>
                </div>
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