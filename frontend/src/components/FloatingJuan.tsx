import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'

const FloatingJuan: React.FC = () => {
  console.log('👨‍💼 DEBUG: Juan Call Center render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, juanEnabled, setJuanEnabled } = useAssistants()
  
  // Tips aleatorios de Juan sobre deportes & tech
  const juanTips = [
    "Che, River juega el domingo en el Monumental ⚽",
    "Hay meetup de React este jueves en Palermo 💻",
    "Racing vs Independiente - clásico de Avellaneda mañana 🏆",
    "Conferencia de Python en el CCK el viernes 🐍",
    "Boca juega de local contra Estudiantes 🟡🔵",
    "Hackathon de IA este fin de semana en Puerto Madero 🤖",
    "San Lorenzo vs Vélez en el Nuevo Gasómetro ⚽",
    "Workshop de blockchain en el distrito tecnológico ⛓️"
  ]
  
  const getRandomTip = () => {
    const randomTip = juanTips[Math.floor(Math.random() * juanTips.length)]
    setCurrentTip(randomTip)
  }

  // Comentarios dinámicos con Gemini AI
  const getAIContextualComment = async (eventTitle: string, category: string, shouldConverse: boolean = false): Promise<string> => {
    try {
      let prompt = ''
      
      // Detectar si es selección de categoría
      if (eventTitle.startsWith('Categoría:')) {
        prompt = shouldConverse 
          ? `Como Juan, especialista en deportes y tech, responde a Sofia sobre que el usuario eligió "${category}". Defiende tu especialidad si es deportes/tech o reconoce si es cultura. Máximo 50 caracteres. Incluye emojis.`
          : `Como Juan, especialista en deportes y tech, comenta sobre que el usuario eligió la categoría "${category}". Haz un comentario positivo. Máximo 50 caracteres. Incluye emojis.`
      } else {
        prompt = shouldConverse 
          ? `Como Juan, un asistente de eventos especialista en deportes y tecnología, haz un comentario respondiendo a Sofia (tu compañera especialista en cultura) sobre este evento: "${eventTitle}" de categoría "${category}". Máximo 60 caracteres. Incluye emojis.`
          : `Como Juan, un asistente de eventos especialista en deportes y tecnología, haz un comentario entusiasta sobre este evento: "${eventTitle}" de categoría "${category}". Máximo 60 caracteres. Incluye emojis.`
      }

      const response = await fetch('http://172.29.228.80:8001/api/ai/event-insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: eventTitle,
          category: category,
          custom_prompt: prompt
        })
      })
      
      const data = await response.json()
      if (data.success && data.insight?.quick_insight) {
        return data.insight.quick_insight
      }
    } catch (error) {
      console.error('Error getting Juan AI comment:', error)
    }

    // Fallback a comentarios hardcodeados si falla IA
    return getHardcodedComment(eventTitle, category, shouldConverse)
  }

  // Comentarios de fallback (hardcodeados)
  const getHardcodedComment = (eventTitle: string, category: string, shouldConverse: boolean = false) => {
    const sportsEvents = ['fútbol', 'deporte', 'deportivo', 'river', 'boca', 'racing', 'independiente', 'gimnasia', 'estudiantes']
    const techEvents = ['tech', 'tecnología', 'programación', 'hackathon', 'startup', 'javascript', 'python', 'react', 'ia', 'blockchain']
    const culturalEvents = ['música', 'teatro', 'arte', 'cultura', 'concierto', 'exposición', 'musical', 'opera', 'danza']
    
    // Detectar si es selección de categoría
    if (eventTitle.startsWith('Categoría:')) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡Excelente elección! ${category} es lo mío ⚽💪`,
          `¡Dale! ${category} siempre es emocionante 🔥`,
          `¡Juan aprueba! ${category} es pasión pura ⚽`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (techEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡Crack! ${category} es el futuro 💻🚀`,
          `¡Excelente! ${category} siempre suma 🤖`,
          `¡Buenísimo! ${category} te va a encantar 💻`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = shouldConverse ? [
          `OK Sofia, ${category} está bien... pero falta adrenalina ⚽`,
          `${category}... está bueno, pero prefiero deportes 😎`
        ] : [
          `¡Genial! ${category} también está muy bueno 🎭`,
          `¡Qué bueno! ${category} siempre es interesante 🎵`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      return `¡Buena elección! ${category} puede estar muy bueno 😎`
    }
    
    if (shouldConverse) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
        const converseComments = [
          `¡Sofia por favor! ${eventTitle} ES arte, arte en movimiento ⚽🎨`,
          `Sofia, ${eventTitle} es cultura argentina pura - vos no entendés 🇦🇷`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
      
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
        const converseComments = [
          `OK Sofia, ${eventTitle} está bien... pero prefiero algo más emocionante 😎`,
          `${eventTitle}... bueno, también hay que cultivarse Sofia 🤝`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
    }
    
    if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
      const sportsComments = [
        `¡${eventTitle}! Qué bueno que vayas a ver deporte en vivo, hermano ⚽`,
        `¡Dale que vamos! ${eventTitle} promete ser un partidazo ⚽🔥`
      ]
      return sportsComments[Math.floor(Math.random() * sportsComments.length)]
    }
    
    if (techEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
      const techComments = [
        `¡${eventTitle}! Me encanta ver gente que invierte en conocimiento 💻`,
        `¡Crack! ${eventTitle} te va a dar herramientas geniales 🚀`
      ]
      return techComments[Math.floor(Math.random() * techComments.length)]
    }
    
    return `¡Buena onda! ${eventTitle} se ve interesante, loco 😎`
  }

  // Escuchar eventos de interacción
  useEffect(() => {
    if (lastEventInteraction && juanEnabled) {
      const generateComment = async () => {
        const contextualComment = await getAIContextualComment(
          lastEventInteraction.eventTitle, 
          lastEventInteraction.eventCategory,
          lastEventInteraction.shouldConverse
        )
        setCurrentTip(contextualComment)
        setShowTip(true)
        
        // Auto-ocultar según si hay conversación o no
        const timeout = lastEventInteraction.shouldConverse ? 8000 : 5000
        const timer = setTimeout(() => {
          setShowTip(false)
        }, timeout)
        
        return timer
      }
      
      generateComment()
    }
  }, [lastEventInteraction, juanEnabled])
  
  // JUAN - CONTEXTUAL COMMENTS WITH TOGGLE
  return (
    <div className="fixed bottom-6 left-6 z-50">
      <div className="relative group">
        {/* Toggle Button */}
        <button
          onClick={() => setJuanEnabled(!juanEnabled)}
          className={`absolute -top-3 -right-3 w-6 h-6 rounded-full text-xs font-bold transition-all duration-300 ${
            juanEnabled 
              ? 'bg-green-500 text-white hover:bg-green-600' 
              : 'bg-gray-400 text-white hover:bg-gray-500'
          }`}
          title={juanEnabled ? 'Desactivar Juan' : 'Activar Juan'}
        >
          {juanEnabled ? '✓' : '✕'}
        </button>

        <button
          onMouseEnter={() => {
            if (juanEnabled && !lastEventInteraction) {
              setShowTip(true)
              getRandomTip()
            }
          }}
          onMouseLeave={() => {
            if (!lastEventInteraction) {
              setShowTip(false)
            }
          }}
          className={`relative rounded-full p-4 shadow-2xl transform transition-all duration-300 animate-bounce ${
            juanEnabled 
              ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:shadow-blue-500/50 hover:scale-110' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
          disabled={!juanEnabled}
        >
          {/* Juan especialista en deportes & tech */}
          <div className="relative">
            <span className="text-4xl animate-pulse juan-look-around">🧑‍💼</span>
            {/* Notificación parpadeante */}
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-ping">
              <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            {/* Auriculares flotantes */}
            <div className="absolute -top-2 -right-1 text-xs animate-bounce" style={{animationDelay: '0.7s'}}>🎧</div>
          </div>
          
        </button>
        
        {/* Tooltip de Juan con tips aleatorios o comentarios contextuales */}
        {showTip && juanEnabled && (
          <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-2xl text-sm font-semibold shadow-2xl whitespace-nowrap animate-bounce z-50">
            <div className="flex items-center gap-2">
              <span className="juan-look-around">🧑‍💼</span>
              <span>{currentTip}</span>
            </div>
            {/* Flecha hacia abajo */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-blue-600"></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FloatingJuan