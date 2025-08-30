import React, { useState, useEffect } from 'react'
import { MapPin, ChevronDown, Loader } from 'lucide-react'

interface LocationBarProps {
  onLocationChange?: (location: any) => void
  onStyleChange?: (styleNumber: number) => void
}

const LocationBar: React.FC<LocationBarProps> = ({ onLocationChange, onStyleChange }) => {
  const [location, setLocation] = useState<string>('🎨 Estilo 1 - Invisible')
  const [coordinates, setCoordinates] = useState<{ lat: number; lon: number } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)


  const detectUserLocation = async () => {
    setIsLoading(true)
    
    // Primero intentar con la API de geolocalización del navegador
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords
          setCoordinates({ lat: latitude, lon: longitude })
          
          // Obtener el barrio más cercano
          try {
            const response = await fetch('http://172.29.228.80:8001/api/location/nearest', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ latitude, longitude })
            })
            
            const data = await response.json()
            if (data.status === 'success') {
              setLocation(`📍 ${data.neighborhood}`)
              if (onLocationChange) {
                onLocationChange({
                  neighborhood: data.neighborhood,
                  coordinates: { latitude, longitude },
                  distance: data.distance_km
                })
              }
            }
          } catch (error) {
            console.error('Error getting neighborhood:', error)
            fallbackToIPLocation()
          }
          
          setIsLoading(false)
        },
        async (error) => {
          console.log('Geolocation denied or error:', error)
          // Si no da permiso, usar detección por IP
          fallbackToIPLocation()
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      )
    } else {
      // Si no hay soporte de geolocalización
      fallbackToIPLocation()
    }
  }

  const fallbackToIPLocation = async () => {
    try {
      const response = await fetch('http://172.29.228.80:8001/api/location/detect')
      const data = await response.json()
      
      if (data.status === 'success' || data.status === 'fallback') {
        const loc = data.location
        setLocation(`📍 ${loc.neighborhood}`)
        setCoordinates({ lat: loc.latitude, lon: loc.longitude })
        
        if (onLocationChange) {
          onLocationChange({
            neighborhood: loc.neighborhood,
            city: loc.city,
            coordinates: { 
              latitude: loc.latitude, 
              longitude: loc.longitude 
            },
            method: 'ip'
          })
        }
      }
    } catch (error) {
      console.error('Error detecting location by IP:', error)
      setLocation('📍 Buenos Aires')
      setLocationError('No pudimos detectar tu ubicación')
    } finally {
      setIsLoading(false)
    }
  }

  const styleOptions = [
    { number: 1, name: 'Estilo 1 - Invisible' },
    { number: 2, name: 'Estilo 2 - Línea Fina' },
    { number: 3, name: 'Estilo 3 - Texto Flotante' },
    { number: 4, name: 'Estilo 4 - Barra Oscura' },
    { number: 5, name: 'Estilo 5 - Minimalista' },
    { number: 6, name: 'Estilo 6 - Solo Iconos' },
    { number: 7, name: 'Estilo 7 - Gradiente' },
    { number: 8, name: 'Estilo 8 - Ultra Mini' },
    { number: 9, name: 'Estilo 9 - Blur Fuerte' },
    { number: 10, name: 'Estilo 10 - MacOS' }
  ]

  const handleStyleSelect = (styleNumber: number, styleName: string) => {
    setLocation(`🎨 ${styleName}`)
    setShowDropdown(false)
    
    if (onStyleChange) {
      onStyleChange(styleNumber)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white px-3 py-2 rounded-lg transition-all duration-200 text-sm group"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader className="w-4 h-4 animate-spin text-white/80" />
            <span className="font-medium">Detectando...</span>
          </>
        ) : (
          <>
            <MapPin className="w-4 h-4 text-white/70 group-hover:text-white transition-colors" />
            <span className="font-medium text-white/90 group-hover:text-white transition-colors">{location}</span>
            <ChevronDown className="w-3 h-3 text-white/50 group-hover:text-white/80 transition-colors" />
          </>
        )}
      </button>

      {/* Dropdown de ubicaciones */}
      {showDropdown && !isLoading && (
        <div className="absolute top-full mt-1 left-0 w-64 bg-black/90 backdrop-blur-xl border border-white/20 rounded-lg shadow-xl z-50 overflow-hidden">
          
          <div className="p-2">
            <p className="text-white/50 text-xs mb-2 px-3 uppercase tracking-wide font-medium">Estilos de barra</p>
            <div className="max-h-64 overflow-y-auto">
              {styleOptions.map(style => (
                <button
                  key={style.number}
                  onClick={() => handleStyleSelect(style.number, style.name)}
                  className="w-full text-left text-white/80 hover:text-white py-2 px-3 rounded-md hover:bg-white/10 transition-all text-sm"
                >
                  {style.number}. {style.name}
                </button>
              ))}
            </div>
          </div>

          {locationError && (
            <div className="p-3 border-t border-white/10">
              <p className="text-yellow-400 text-xs">{locationError}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LocationBar