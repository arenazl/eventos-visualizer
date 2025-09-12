import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'

const FloatingChat: React.FC = () => {
  console.log('💁‍♀️ DEBUG: Call Center Girl Sofia render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, sofiaEnabled, setSofiaEnabled } = useAssistants()
  
  // Sofia solo comenta sobre eventos reales - NO tips hardcodeados

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

  // Comentarios contextuales basados en evento real
  const getHardcodedComment = (eventTitle: string, category: string, shouldConverse: boolean = false) => {
    const culturalEvents = ['música', 'teatro', 'arte', 'cultura', 'concierto', 'exposición', 'musical', 'opera', 'danza', 'vino', 'cocktail', 'feria', 'retro']
    const sportsEvents = ['fútbol', 'deporte', 'deportivo', 'river', 'boca', 'racing', 'independiente']
    
    // Detectar si es selección de categoría
    if (eventTitle.startsWith('Categoría:')) {
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡AY SÍ! ${category} me llena el alma de colores 🎭🌈`,
          `¡AMOR TOTAL! ${category} = vibra alta siempre 🎵✨`,
          `¡Sofia is LIVING! ${category} es lo que mi corazón necesitaba 💖🎨`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = shouldConverse ? [
          `¡Juan! ¿${category}? ¿Y la música dónde queda, che? 🎵🙄`,
          `Ay Juan... ${category} está ok, pero ¿no preferís un recital? 🎸😏`,
          `¿En serio Juan? ${category}... ok, pero después hablamos de Soda Stereo ⚽🎶`
        ] : [
          `Bueno Juan... ${category} tiene su onda también, supongo ⚽💜`,
          `${category}... ok, cada uno con su vibra, no judge 😊✨`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      return `¡Interesante elección! ${category} puede sorprender 😊`
    }
    
    // Análisis contextual del título real del evento
    const lowerTitle = eventTitle.toLowerCase()
    
    // Eventos específicos de vino/bebidas
    if (lowerTitle.includes('vino') || lowerTitle.includes('cocktail') || lowerTitle.includes('bebida')) {
      const wineComments = shouldConverse ? [
        `¡Juan! "${eventTitle}" es ARTE líquido, no solo fútbol existe 🍷✨`,
        `Ay Juan, "${eventTitle}" va a ser mejor que cualquier asado con amigos 🍷🎵`,
        `¡Por favor Juan! "${eventTitle}" = cultura en copa, animate 🍷🎭`
      ] : [
        `¡"${eventTitle}"! Wine not? Esta vibra me encanta 🍷💃`,
        `¡AMO! "${eventTitle}" = plan perfecto para el alma 🍷✨`,
        `"${eventTitle}" me tiene emocionada, va a estar genial 🍷🎵`
      ]
      return wineComments[Math.floor(Math.random() * wineComments.length)]
    }
    
    // Eventos de música/conciertos  
    if (lowerTitle.includes('concierto') || lowerTitle.includes('música') || lowerTitle.includes('retro') || lowerTitle.includes('festival')) {
      const musicComments = shouldConverse ? [
        `¡SÍ JUAN! "${eventTitle}" - por fin algo que alimenta el alma 🎵💖`,
        `¡GRACIAS! Juan eligió "${eventTitle}" - hay esperanza para ti 🎶✨`,
        `¡Juan! "${eventTitle}" te va a dar feels que el fútbol nunca 🎭😍`
      ] : [
        `¡"${eventTitle}"! Esta vibra me tiene en las nubes 🎵🌟`,
        `¡AMO! "${eventTitle}" va a estar ÉPICO, siento la energía ya 🎶💫`,
        `"${eventTitle}" me tiene haciendo happy dance mental 🎵✨`
      ]
      return musicComments[Math.floor(Math.random() * musicComments.length)]
    }
    
    // Ferias y eventos culturales
    if (lowerTitle.includes('feria') || lowerTitle.includes('expo') || lowerTitle.includes('cultural')) {
      const fairComments = shouldConverse ? [
        `¡Juan che! "${eventTitle}" tiene más cultura que un estadio lleno 🎨⚽`,
        `Ay Juan... "${eventTitle}" va a estar buenísimo, animate 🎭💭`,
        `Juan, "${eventTitle}" = experiencia que ningún gol te da 🎨🎵`
      ] : [
        `¡"${eventTitle}"! Me fascina este tipo de propuestas 🎨✨`,
        `"${eventTitle}" suena increíble, va a estar genial 🎭💫`,
        `¡Qué buena onda! "${eventTitle}" tiene pinta de ser memorable 🎨🌟`
      ]
      return fairComments[Math.floor(Math.random() * fairComments.length)]
    }
    
    if (shouldConverse) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || lowerTitle.includes(keyword))) {
        const converseComments = [
          `¡Juan che! "${eventTitle}" está bueno... pero ¿viste el lineup del Lolla? 🎵⚽`,
          `Ay Juan... "${eventTitle}" tiene onda, pero un recital te cambia la vida 🙄🎶`,
          `Ok Juan, "${eventTitle}"... pero después me acompañás al teatro ⚽🎭`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
    }
    
    // Fallback general contextual
    return `¡"${eventTitle}" suena interesante! Me gusta la vibra que trae 😊🎶`
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
            // Sofia solo comenta sobre eventos reales, no tips hardcodeados
          }}
          onMouseLeave={() => {
            // Sofia solo comenta sobre eventos reales, no tips hardcodeados  
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
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-ping"></div>
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