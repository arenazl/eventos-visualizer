import React, { createContext, useContext, useState, ReactNode } from 'react'

interface EventInteraction {
  eventTitle: string
  eventCategory: string
  eventType: string
  timestamp: Date
  shouldConverse: boolean // Para activar conversación 1/10
}

interface AssistantsContextType {
  lastEventInteraction: EventInteraction | null
  triggerEventComment: (event: EventInteraction) => void
  selectedCategories: string[]
  setSelectedCategories: (categories: string[]) => void
  triggerCategoryComment: (category: string) => void
  sofiaEnabled: boolean
  juanEnabled: boolean
  setSofiaEnabled: (enabled: boolean) => void
  setJuanEnabled: (enabled: boolean) => void
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
  const [sofiaEnabled, setSofiaEnabled] = useState(true)
  const [juanEnabled, setJuanEnabled] = useState(true)

  const triggerEventComment = (event: Omit<EventInteraction, 'shouldConverse'>) => {
    // Determinar si debería haber conversación (1 de cada 10)
    const shouldConverse = Math.random() < 0.1 // 10% de chance
    
    const fullEvent: EventInteraction = {
      ...event,
      shouldConverse
    }
    
    setLastEventInteraction(fullEvent)
    
    // Si hay conversación, mantener más tiempo para ver ambos comentarios
    const timeout = shouldConverse ? 8000 : 5000
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

  const value: AssistantsContextType = {
    lastEventInteraction,
    triggerEventComment,
    selectedCategories,
    setSelectedCategories,
    triggerCategoryComment,
    sofiaEnabled,
    juanEnabled,
    setSofiaEnabled,
    setJuanEnabled
  }

  return (
    <AssistantsContext.Provider value={value}>
      {children}
    </AssistantsContext.Provider>
  )
}