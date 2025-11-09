import React, { createContext, useContext, useState, ReactNode } from 'react'

interface EventInteraction {
  eventTitle: string
  eventCategory: string
  eventType: string
  timestamp: Date
  shouldConverse: boolean // Para activar conversación 1/10
  assistant?: 'sofia' | 'juan' // Especifica quién debe hablar (solo para detail_recommendation)
}

interface SearchContext {
  timestamp: Date
  dayOfWeek: string
  hour: number
  cityName?: string // Ciudad que se está cargando
}

interface NoEventsContext {
  cityName: string
  searchingNearby: boolean
}

interface AssistantsContextType {
  lastEventInteraction: EventInteraction | null
  triggerEventComment: (event: EventInteraction) => void
  selectedCategories: string[]
  setSelectedCategories: (categories: string[]) => void
  triggerCategoryComment: (category: string) => void
  // 🔍 Comentario general al hacer búsqueda (basado en día/hora + ciudad)
  lastSearchContext: SearchContext | null
  triggerSearchComment: (cityName?: string) => void
  // 🚫 Comentario cuando no hay eventos
  lastNoEventsContext: NoEventsContext | null
  triggerNoEventsComment: (cityName: string, searchingNearby: boolean) => void
  sofiaEnabled: boolean
  juanEnabled: boolean
  setSofiaEnabled: (enabled: boolean) => void
  setJuanEnabled: (enabled: boolean) => void
  // 📋 Recomendaciones en página de detalle (continuo cada 10 segundos)
  triggerDetailRecommendations: (eventTitle: string, eventCategory: string) => () => void
}

const AssistantsContext = createContext<AssistantsContextType | undefined>(undefined)

export const useAssistants = () => {
  const context = useContext(AssistantsContext)
  if (!context) {
    throw new Error('useAssistants must be used within an AssistantsProvider')
  }
  return context
}

interface AssistantsProviderProps {
  children: ReactNode
}

export const AssistantsProvider: React.FC<AssistantsProviderProps> = ({ children }) => {
  const [lastEventInteraction, setLastEventInteraction] = useState<EventInteraction | null>(null)
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [lastSearchContext, setLastSearchContext] = useState<SearchContext | null>(null)
  const [lastNoEventsContext, setLastNoEventsContext] = useState<NoEventsContext | null>(null)
  const [sofiaEnabled, setSofiaEnabled] = useState(true)
  const [juanEnabled, setJuanEnabled] = useState(true)

  const triggerEventComment = (event: Omit<EventInteraction, 'shouldConverse'>) => {
    // Determinar si debería haber conversación (1 de cada 5-6 mensajes = ~17-20%)
    const shouldConverse = Math.random() < 0.18 // 18% de chance para conversaciones más frecuentes
    
    const fullEvent: EventInteraction = {
      ...event,
      shouldConverse
    }
    
    console.log(`🎭 Asistentes: ${event.eventTitle} - Conversación: ${shouldConverse ? 'SÍ' : 'NO'}`)
    
    setLastEventInteraction(fullEvent)
    
    // Si hay conversación, mantener más tiempo para ver ambos comentarios
    const timeout = shouldConverse ? 12000 : 6000 // Más tiempo para leer las conversaciones
    setTimeout(() => {
      setLastEventInteraction(null)
    }, timeout)
  }

  const triggerCategoryComment = (category: string) => {
    // Generar comentario específico sobre la categoría seleccionada
    const categoryEvent: EventInteraction = {
      eventTitle: `Categoría: ${category}`,
      eventCategory: category,
      eventType: 'category_selection',
      timestamp: new Date(),
      shouldConverse: Math.random() < 0.3 // 30% chance para categorías
    }

    setLastEventInteraction(categoryEvent)

    // Mantener comentario más tiempo para categorías
    setTimeout(() => {
      setLastEventInteraction(null)
    }, 6000)
  }

  // 🔍 Trigger comentario general al hacer búsqueda (basado en día/hora + ciudad)
  const triggerSearchComment = (cityName?: string) => {
    const now = new Date()
    const days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

    const searchContext: SearchContext = {
      timestamp: now,
      dayOfWeek: days[now.getDay()],
      hour: now.getHours(),
      cityName: cityName
    }

    console.log(`🔍 Asistentes: Búsqueda ejecutada - ${cityName || 'sin ciudad'} - ${searchContext.dayOfWeek} a las ${searchContext.hour}hs`)

    setLastSearchContext(searchContext)

    // Mantener comentario visible por 7 segundos
    setTimeout(() => {
      setLastSearchContext(null)
    }, 7000)
  }

  // 🚫 Trigger comentario cuando no hay eventos
  const triggerNoEventsComment = (cityName: string, searchingNearby: boolean) => {
    const noEventsContext: NoEventsContext = {
      cityName,
      searchingNearby
    }

    console.log(`🚫 Asistentes: Sin eventos en ${cityName}, buscando cercanos: ${searchingNearby}`)

    setLastNoEventsContext(noEventsContext)

    // Mantener comentario visible por 6 segundos
    setTimeout(() => {
      setLastNoEventsContext(null)
    }, 6000)
  }

  // 📋 Trigger recomendaciones en página de detalle (alternando Sofia/Juan cada 10s)
  const triggerDetailRecommendations = (eventTitle: string, eventCategory: string) => {
    console.log(`📋 Asistentes: Iniciando recomendaciones alternadas cada 10s para "${eventTitle}"`)

    let currentIndex = 0
    const assistants: ('sofia' | 'juan')[] = ['sofia', 'juan'] // Alternar: Sofia primero, Juan segundo

    // Función para mostrar el próximo tip
    const showNextTip = () => {
      const currentAssistant = assistants[currentIndex]
      const shouldConverse = false // Sin conversaciones en página de detalle, solo tips individuales

      const eventInteraction: EventInteraction = {
        eventTitle: eventTitle,
        eventCategory: eventCategory,
        eventType: 'detail_recommendation',
        timestamp: new Date(),
        shouldConverse: shouldConverse,
        assistant: currentAssistant // Especifica quién debe hablar
      }

      console.log(`💬 ${currentAssistant === 'sofia' ? 'Sofia' : 'Juan'} hablando ahora...`)
      setLastEventInteraction(eventInteraction)

      // Limpiar después de 9.5 segundos (justo antes del próximo)
      setTimeout(() => {
        setLastEventInteraction(null)
      }, 9500)

      // Alternar al siguiente asistente
      currentIndex = (currentIndex + 1) % assistants.length
    }

    // Mostrar el primer tip (Sofia) después de 2 segundos
    const firstTimeout = setTimeout(showNextTip, 2000)

    // Luego mostrar uno cada 10 segundos (Sofia -> Juan -> Sofia -> Juan...)
    const interval = setInterval(showNextTip, 10000)

    // Retornar función de limpieza
    return () => {
      console.log(`📋 Asistentes: Deteniendo recomendaciones para "${eventTitle}"`)
      clearTimeout(firstTimeout)
      clearInterval(interval)
      setLastEventInteraction(null)
    }
  }

  const value: AssistantsContextType = {
    lastEventInteraction,
    triggerEventComment,
    selectedCategories,
    setSelectedCategories,
    triggerCategoryComment,
    lastSearchContext,
    triggerSearchComment,
    lastNoEventsContext,
    triggerNoEventsComment,
    sofiaEnabled,
    juanEnabled,
    setSofiaEnabled,
    setJuanEnabled,
    triggerDetailRecommendations
  }

  return (
    <AssistantsContext.Provider value={value}>
      {children}
    </AssistantsContext.Provider>
  )
}