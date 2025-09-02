import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'

const FloatingChat: React.FC = () => {
  console.log('💁‍♀️ DEBUG: Call Center Girl Sofia render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, sofiaEnabled, setSofiaEnabled } = useAssistants()
  
  // Tips aleatorios de Sofía sobre arte y cultura
  const sofiaTips = [
    "Che, hay una obra buenísima en el San Martín este finde 🎭",
    "Miranda! toca en el Luna Park el sábado - imperdible 🎵",
    "Exposición de Milo Lockett en el MALBA hasta fin de mes 🎨",
    "Stand up de Capusotto en el Metropolitan mañana 🎭",
    "Feria de San Telmo los domingos - re copada para caminar 🎨",
    "Concierto de la Orquesta Filarmónica en el CCK 🎶",
    "Noche de los museos este viernes - entrada libre 🏛️",
    "Recital de Divididos en el Hipódromo de Palermo 🎸"
  ]
  
  const getRandomTip = () => {
    const randomTip = sofiaTips[Math.floor(Math.random() * sofiaTips.length)]
    setCurrentTip(randomTip)
  }

  // Comentarios dinámicos con Gemini AI
  const getAIContextualComment = async (eventTitle: string, category: string, shouldConverse: boolean = false): Promise<string> => {
    try {
      let prompt = ''
      
      // Detectar si es selección de categoría
      if (eventTitle.startsWith('Categoría:')) {
        prompt = shouldConverse 
          ? `Como Sofia, especialista en arte y cultura, comenta provocativamente a Juan sobre que el usuario eligió la categoría "${category}". Sugiere que es mejor que deportes. Máximo 50 caracteres. Incluye emojis.`
          : `Como Sofia, especialista en arte y cultura, celebra que el usuario eligió la categoría "${category}". Haz un comentario entusiasta. Máximo 50 caracteres. Incluye emojis.`
      } else {
        prompt = shouldConverse 
          ? `Como Sofia, una asistente de eventos especialista en arte y cultura, haz un comentario provocativo dirigido a Juan (tu compañero especialista en deportes) sobre este evento: "${eventTitle}" de categoría "${category}". Máximo 60 caracteres. Incluye emojis.`
          : `Como Sofia, una asistente de eventos especialista en arte y cultura, haz un comentario entusiasta sobre este evento: "${eventTitle}" de categoría "${category}". Máximo 60 caracteres. Incluye emojis.`
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
      console.error('Error getting Sofia AI comment:', error)
    }

    // Fallback a comentarios hardcodeados si falla IA
    return getHardcodedComment(eventTitle, category, shouldConverse)
  }

  // Comentarios de fallback (hardcodeados)
  const getHardcodedComment = (eventTitle: string, category: string, shouldConverse: boolean = false) => {
    const culturalEvents = ['música', 'teatro', 'arte', 'cultura', 'concierto', 'exposición', 'musical', 'opera', 'danza']
    const sportsEvents = ['fútbol', 'deporte', 'deportivo', 'river', 'boca', 'racing', 'independiente']
    
    // Detectar si es selección de categoría
    if (eventTitle.startsWith('Categoría:')) {
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡Excelente! ${category} es lo mejor 🎭✨`,
          `¡Qué buen gusto! ${category} siempre 🎵`,
          `¡Sofia aprueba! ${category} es cultura pura ✨`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = shouldConverse ? [
          `Juan, ¿${category} en serio? ¿No hay nada cultural? 🙄`,
          `Ay, ${category}... esperaba algo más refinado 🎭`
        ] : [
          `Bueno... ${category} también está bien, supongo ⚽`,
          `${category}... no es mi favorito pero ok 😊`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      return `¡Interesante elección! ${category} puede sorprender 😊`
    }
    
    if (shouldConverse) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
        const converseComments = [
          `Juan, ¿en serio ${eventTitle}? ¿No preferirías algo más refinado? 🎭`,
          `Ay Juan, siempre con el fútbol... ${eventTitle} no es cultura 🙄`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
      
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
        const converseComments = [
          `¡Perfecto! ${eventTitle} - al fin algo con clase 🎭✨`,
          `¡Ves Juan! ${eventTitle} es cultura de verdad 🎵`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
    }
    
    if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
      const culturalComments = [
        `¡${eventTitle}! Ese tipo de eventos siempre tienen buena vibra 🎭✨`,
        `Me encanta cuando la gente elige cultura. ¡${eventTitle} va a estar genial! 🎵`
      ]
      return culturalComments[Math.floor(Math.random() * culturalComments.length)]
    }
    
    return `¡Buena elección! ${eventTitle} se ve interesante 😊✨`
  }

  // Escuchar eventos de interacción
  useEffect(() => {
    if (lastEventInteraction && sofiaEnabled) {
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
  }, [lastEventInteraction, sofiaEnabled])
  
  // SOFIA - CONTEXTUAL COMMENTS WITH TOGGLE
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="relative group">
        {/* Toggle Button */}
        <button
          onClick={() => setSofiaEnabled(!sofiaEnabled)}
          className={`absolute -top-3 -left-3 w-6 h-6 rounded-full text-xs font-bold transition-all duration-300 ${
            sofiaEnabled 
              ? 'bg-green-500 text-white hover:bg-green-600' 
              : 'bg-gray-400 text-white hover:bg-gray-500'
          }`}
          title={sofiaEnabled ? 'Desactivar Sofia' : 'Activar Sofia'}
        >
          {sofiaEnabled ? '✓' : '✕'}
        </button>

        <button
          onMouseEnter={() => {
            if (sofiaEnabled && !lastEventInteraction) {
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
            sofiaEnabled 
              ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white hover:shadow-pink-500/50 hover:scale-110' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
          disabled={!sofiaEnabled}
        >
          {/* Chica de call center con auriculares */}
          <div className="relative">
            <span className="text-4xl animate-pulse sofia-look-around">💁‍♀️</span>
            {/* Notificación parpadeante */}
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-ping">
              <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
            </div>
            {/* Auriculares flotantes */}
            <div className="absolute -top-2 -left-1 text-xs animate-bounce" style={{animationDelay: '0.5s'}}>🎧</div>
          </div>
          
        </button>
        
        {/* Tooltip de Sofia apuntando hacia Juan (izquierda) */}
        {showTip && sofiaEnabled && (
          <div className="absolute -top-20 -left-80 bg-gradient-to-r from-pink-600 to-purple-600 text-white px-4 py-2 rounded-2xl text-sm font-semibold shadow-2xl animate-bounce z-50 w-72">
            <div className="flex items-center gap-2">
              <span className="sofia-look-around">💁‍♀️</span>
              <span className="break-words whitespace-normal">{currentTip}</span>
            </div>
            {/* Flecha apuntando hacia la derecha (hacia Sofia) */}
            <div className="absolute top-4 -right-2 w-0 h-0 border-l-8 border-t-4 border-b-4 border-l-pink-600 border-t-transparent border-b-transparent"></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FloatingChat