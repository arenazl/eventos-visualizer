import React, { useState, useEffect } from 'react'
import { MapPin, Sparkles } from 'lucide-react'
import { useEvents } from '../stores/EventsStore'

interface NearbyCitiesLinksProps {
  currentCity: string
  onCityClick: (location: any) => void
}

const NearbyCitiesLinks: React.FC<NearbyCitiesLinksProps> = ({ currentCity, onCityClick }) => {
  const storeNearbyCities = useEvents(state => state.nearbyCities)
  const [nearbyCities, setNearbyCities] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)

  useEffect(() => {
    // First check if we have cities from the store (from recommend endpoint)
    if (storeNearbyCities && storeNearbyCities.length > 0) {
      setNearbyCities(storeNearbyCities)
      setHasLoaded(true)
    } else if (currentCity && !hasLoaded) {
      // ✅ REMOVED: fetchNearbyCities - use fallback cities instead of HTTP call
      setDefaultCitiesForLocation()
    }
  }, [currentCity, storeNearbyCities])

  const fetchNearbyCities = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://172.29.228.80:8001/api/ai/nearby-cities?city=${encodeURIComponent(currentCity)}`)
      if (response.ok) {
        const data = await response.json()
        if (data.nearby_cities && Array.isArray(data.nearby_cities)) {
          setNearbyCities(data.nearby_cities.slice(0, 3))
          setHasLoaded(true)
        }
      }
    } catch (error) {
      console.error('Error fetching nearby cities:', error)
      // Fallback cities based on location
      setDefaultCitiesForLocation()
    } finally {
      setLoading(false)
    }
  }

  const setDefaultCitiesForLocation = () => {
    const cityDefaults: Record<string, string[]> = {
      'Miami': ['Fort Lauderdale', 'West Palm Beach', 'Hollywood'],
      'Buenos Aires': ['La Plata', 'San Isidro', 'Tigre'],
      'Madrid': ['Alcalá de Henares', 'Getafe', 'Leganés'],
      'Barcelona': ['Badalona', 'Hospitalet', 'Sabadell'],
      'Mexico City': ['Ecatepec', 'Guadalajara', 'Puebla'],
      'São Paulo': ['Guarulhos', 'Campinas', 'Santo André'],
      'New York': ['Newark', 'Jersey City', 'Yonkers'],
      'Los Angeles': ['Long Beach', 'Santa Monica', 'Pasadena']
    }
    
    const defaults = cityDefaults[currentCity] || []
    if (defaults.length > 0) {
      setNearbyCities(defaults)
      setHasLoaded(true)
    }
  }

  const handleCityClick = (city: string) => {
    onCityClick({
      name: city,
      detected: 'manual',
      coordinates: undefined,
      country: undefined
    })
  }

  if (!nearbyCities.length && !loading) {
    return null
  }

  return (
    <div className="mt-4 mb-6 flex items-center justify-center gap-2 flex-wrap">
      {loading ? (
        <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500">
          <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-purple-500 rounded-full" />
          <span>Finding nearby cities...</span>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-1 text-sm text-gray-500 mr-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <span>Explore nearby:</span>
          </div>
          {nearbyCities.map((city, index) => (
            <button
              key={city}
              onClick={() => handleCityClick(city)}
              className="group relative px-4 py-2 text-sm font-medium text-gray-700 
                       bg-white hover:bg-gradient-to-r hover:from-purple-500 hover:to-pink-500 
                       hover:text-white border border-gray-200 hover:border-transparent
                       rounded-full transition-all duration-200 transform hover:scale-105
                       shadow-sm hover:shadow-lg"
            >
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5 opacity-60 group-hover:opacity-100" />
                {city}
              </span>
              {/* Subtle gradient overlay on hover */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/10 to-pink-500/10 
                            opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none" />
            </button>
          ))}
        </>
      )}
    </div>
  )
}

export default NearbyCitiesLinks