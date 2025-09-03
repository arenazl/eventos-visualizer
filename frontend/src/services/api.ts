/**
 * API Service - Centraliza todas las llamadas a la API
 * Con geolocalización automática y búsqueda inteligente
 */

import { config } from '../config'

const API_BASE_URL = config.API_BASE_URL

export interface Location {
  city: string
  country: string
  latitude: number
  longitude: number
  display_name: string
}

export interface Event {
  title: string
  description?: string
  start_datetime?: string | null
  venue_name: string
  venue_address?: string
  category: string
  price?: number | null
  currency?: string
  is_free?: boolean
  image_url?: string | null
  latitude?: number
  longitude?: number
  source?: string
  status?: string
}

export interface EventsResponse {
  events: Event[]
  scrapers_execution: any
}

// Interfaces para IA
export interface AIRecommendation {
  titulo: string
  porque_te_va_a_encantar: string
  vibe: string
  precio_estimado: string
  match_score: number
}

export interface AIChatResponse {
  status: string
  response: string
  recommendations: AIRecommendation[]
  preferences_detected: any
  follow_up: string
}

export class EventsAPI {
  /**
   * Detecta automáticamente la ubicación del usuario
   * Usa IP como método principal
   */
  static async detectLocation(): Promise<Location> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/location/detect`)
      if (!response.ok) throw new Error('Failed to detect location')
      
      const data = await response.json()
      return data.location
    } catch (error) {
      console.error('Error detecting location:', error)
      // Fallback to Buenos Aires
      return {
        city: 'Buenos Aires',
        country: 'Argentina',
        latitude: -34.6037,
        longitude: -58.3816,
        display_name: 'Buenos Aires, Argentina'
      }
    }
  }

  /**
   * Obtiene eventos con detección automática de ubicación
   * Si no se proporciona ubicación, el backend la detecta por IP
   */
  static async getEvents(location?: string, category?: string): Promise<EventsResponse> {
    try {
      const params = new URLSearchParams()
      if (location) params.append('location', location)
      if (category) params.append('category', category)
      
      const url = params.toString() 
        ? `${API_BASE_URL}/api/events?${params}`
        : `${API_BASE_URL}/api/events`
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch events')
      
      const data = await response.json()
      return {
        events: data.events || [],
        scrapers_execution: data.scrapers_execution || null
      } as EventsResponse
    } catch (error) {
      console.error('Error fetching events:', error)
      return {
        events: [],
        scrapers_execution: null
      } as EventsResponse
    }
  }

  /**
   * Búsqueda inteligente que entiende lenguaje natural
   * Ejemplos: "bares en Mendoza", "restaurantes en Palermo", "conciertos este fin de semana"
   */
  static async smartSearch(query: string, location?: string): Promise<{
    query: string
    detected_location: string | null
    detected_category: string | null
    results: Event[]
  }> {
    try {
      const params = new URLSearchParams({ q: query })
      if (location) params.append('location', location)
      
      const response = await fetch(`${API_BASE_URL}/api/events/smart-search?${params}`)
      if (!response.ok) throw new Error('Smart search failed')
      
      return await response.json()
    } catch (error) {
      console.error('Error in smart search:', error)
      return {
        query,
        detected_location: null,
        detected_category: null,
        results: []
      }
    }
  }

  /**
   * Obtiene lista de ciudades disponibles
   */
  static async getAvailableCities(): Promise<Array<{
    city: string
    country: string
    display_name: string
    latitude: number
    longitude: number
  }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/location/cities`)
      if (!response.ok) throw new Error('Failed to fetch cities')
      
      const data = await response.json()
      return data.cities || []
    } catch (error) {
      console.error('Error fetching cities:', error)
      return []
    }
  }

  /**
   * Establece la ubicación del usuario manualmente
   */
  static async setLocation(locationData: {
    city?: string
    latitude?: number
    longitude?: number
  }): Promise<Location> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/location/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(locationData)
      })
      
      if (!response.ok) throw new Error('Failed to set location')
      
      const data = await response.json()
      return data.location
    } catch (error) {
      console.error('Error setting location:', error)
      throw error
    }
  }

  /**
   * Obtiene la ubicación actual del navegador (GPS)
   */
  static async getCurrentPosition(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        position => resolve(position),
        error => reject(error),
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      )
    })
  }

  /**
   * Combina detección por IP con GPS del navegador
   */
  static async getBestLocation(): Promise<Location> {
    try {
      // Primero intentar con GPS del navegador
      const gpsPosition = await EventsAPI.getCurrentPosition().catch(() => null)
      
      if (gpsPosition) {
        // Si tenemos GPS, enviar las coordenadas al backend
        return await EventsAPI.setLocation({
          latitude: gpsPosition.coords.latitude,
          longitude: gpsPosition.coords.longitude
        })
      }
    } catch (error) {
      console.log('GPS not available, using IP detection')
    }

    // Si no hay GPS, usar detección por IP
    return await EventsAPI.detectLocation()
  }

  /**
   * Chat inteligente con IA sobre eventos
   * Entiende lenguaje natural y da recomendaciones personalizadas
   */
  static async chatWithAI(message: string, context: any = {}): Promise<AIChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message,
          context
        })
      })
      
      if (!response.ok) throw new Error('AI chat failed')
      
      return await response.json()
    } catch (error) {
      console.error('Error in AI chat:', error)
      throw error
    }
  }

  /**
   * Obtiene recomendaciones personalizadas con IA
   */
  static async getAIRecommendations(preferences: {
    budget?: number
    categories?: string[]
    mood?: string
    with_who?: string
  }): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(preferences)
      })
      
      if (!response.ok) throw new Error('Failed to get recommendations')
      
      return await response.json()
    } catch (error) {
      console.error('Error getting AI recommendations:', error)
      throw error
    }
  }

  /**
   * Planifica el fin de semana perfecto con IA
   */
  static async planWeekend(budget: number, preferences: string[], peopleCount: number = 1): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/plan-weekend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          budget,
          preferences,
          people_count: peopleCount
        })
      })
      
      if (!response.ok) throw new Error('Failed to plan weekend')
      
      return await response.json()
    } catch (error) {
      console.error('Error planning weekend:', error)
      throw error
    }
  }

  /**
   * Obtiene eventos trending en este momento
   */
  static async getTrendingNow(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/trending-now`)
      if (!response.ok) throw new Error('Failed to get trending events')
      
      return await response.json()
    } catch (error) {
      console.error('Error getting trending events:', error)
      throw error
    }
  }
}