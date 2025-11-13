import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'
import Sofia3DAvatar from './Sofia3DAvatar'

const FloatingChat: React.FC = () => {
  console.log('💁‍♀️ DEBUG: Call Center Girl Sofia render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, lastSearchContext, lastNoEventsContext, sofiaEnabled, setSofiaEnabled } = useAssistants()
  
  // Sofia solo comenta sobre eventos reales - NO tips hardcodeados

  // DESACTIVADO: Comentarios dinámicos con Gemini AI (para evitar llamadas duplicadas)
  // Ahora usa solo comentarios hardcoded
  const getAIContextualComment = async (eventTitle: string, category: string, shouldConverse: boolean = false): Promise<string> => {
    console.log('💁‍♀️ Sofia usando comentarios hardcoded (AI desactivado para evitar duplicados)')
    // Usar directamente comentarios hardcodeados
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
    // Solo responder si:
    // 1. Sofia está habilitada
    // 2. El evento no especifica assistant (cualquiera puede responder) O especifica 'sofia'
    const shouldRespond = sofiaEnabled &&
                          lastEventInteraction &&
                          (!lastEventInteraction.assistant || lastEventInteraction.assistant === 'sofia')

    if (shouldRespond) {
      const generateComment = async () => {
        const contextualComment = await getAIContextualComment(
          lastEventInteraction!.eventTitle,
          lastEventInteraction!.eventCategory,
          lastEventInteraction!.shouldConverse
        )
        setCurrentTip(contextualComment)
        setShowTip(true)

        // Auto-ocultar según si hay conversación o no (timeouts más largos)
        const timeout = lastEventInteraction!.shouldConverse ? 15000 : 10000
        const timer = setTimeout(() => {
          setShowTip(false)
        }, timeout)

        return timer
      }

      generateComment()
    }
  }, [lastEventInteraction, sofiaEnabled])

  // 🔍 Comentario general al hacer búsqueda (perfil: graciosa, humor negro)
  useEffect(() => {
    if (lastSearchContext && sofiaEnabled) {
      const { dayOfWeek, hour, cityName } = lastSearchContext
      let comment = ''
      const cityPrefix = cityName ? `🌆 ${cityName}: ` : ''

      // Comentarios SIEMPRE, incluso sin eventos - basados en día y hora (con humor negro y sarcasmo + ciudad)
      if (dayOfWeek === 'Lunes' && hour < 12) {
        const mondayMorning = [
          `${cityPrefix}¿Lunes a la mañana buscando planes? Alguien no durmió bien 😴💀`,
          `${cityPrefix}Lunes temprano y con energía? Qué optimista! Me caés bien 😂☕`,
          `${cityPrefix}¿Escapando del lunes? Same, bestie. SAME. 💀☕`
        ]
        comment = mondayMorning[Math.floor(Math.random() * mondayMorning.length)]
      } else if (dayOfWeek === 'Viernes' && hour >= 18) {
        const fridayNight = [
          `${cityPrefix}¡VIERNES! Si no salís ahora te declaran legalmente anciano 🎉💀`,
          `${cityPrefix}Viernes de noche buscando planes? Tardaste pero llegaste! 😂🍾`,
          `${cityPrefix}¡AL FIN VIERNES! Ya me estaba preocupando por vos 🎊😈`
        ]
        comment = fridayNight[Math.floor(Math.random() * fridayNight.length)]
      } else if (['Sábado', 'Domingo'].includes(dayOfWeek) && hour < 14) {
        const weekendMorning = [
          `${cityPrefix}Finde a la mañana? Recién te levantaste o nunca dormiste 😎🌅`,
          `${cityPrefix}¿Buscando cosas antes del mediodía? Respeto tu rareza 😂☀️`,
          `${cityPrefix}Finde temprano buscando eventos? No es normal pero me divierte 🤣🌄`
        ]
        comment = weekendMorning[Math.floor(Math.random() * weekendMorning.length)]
      } else if (hour >= 23 || hour < 5) {
        const lateNight = [
          `${cityPrefix}Las ${hour}hs buscando eventos? Muy nocturno o muy desesperado 🌙💀`,
          `${cityPrefix}A esta hora? No juzgo... mentira sí. Pero me gusta 😂🦇`,
          `${cityPrefix}Insomnio productivo? Tu soulmate de búsqueda soy yo 🌃😈`
        ]
        comment = lateNight[Math.floor(Math.random() * lateNight.length)]
      } else {
        const generic = [
          `${cityPrefix}¿Buscando algo para no aburrirte? Misión aceptada! 🎯😎`,
          `${cityPrefix}Buscando eventos... o sea, no querés Netflix otra vez 😂📺`,
          `${cityPrefix}¡A encontrar algo bueno! (Que no sea TikTok por favor) 🎭🤳`
        ]
        comment = generic[Math.floor(Math.random() * generic.length)]
      }

      setCurrentTip(comment)
      setShowTip(true)

      // Ocultar después de 12 segundos
      const timer = setTimeout(() => {
        setShowTip(false)
      }, 12000)

      return () => clearTimeout(timer)
    }
  }, [lastSearchContext, sofiaEnabled])

  // 🚫 Comentario cuando no hay eventos (perfil: graciosa, humor negro)
  useEffect(() => {
    if (lastNoEventsContext && sofiaEnabled) {
      const { cityName, searchingNearby } = lastNoEventsContext
      let comment = ''

      if (searchingNearby) {
        const searchingComments = [
          `🌆 ${cityName}: Vacío total! Buscando en lugares más movidos... 🔍💃`,
          `🌆 ${cityName}: Esto está más muerto que mi vida social del 2020 😂 Buscando...`,
          `🌆 ${cityName}: Houston tenemos un problema... buscando plan B 🚀`
        ]
        comment = searchingComments[Math.floor(Math.random() * searchingComments.length)]
      } else {
        const noEventsComments = [
          `🌆 ${cityName}: Nada que ver acá! Literal NADA. F por ${cityName} 💀`,
          `🌆 ${cityName}: Más vacío que promesa de político! Probá otras zonas 😂`,
          `🌆 ${cityName}: Evento 404 not found. Expandí la búsqueda! 🔍`
        ]
        comment = noEventsComments[Math.floor(Math.random() * noEventsComments.length)]
      }

      setCurrentTip(comment)
      setShowTip(true)

      // Ocultar después de 10 segundos
      const timer = setTimeout(() => {
        setShowTip(false)
      }, 10000)

      return () => clearTimeout(timer)
    }
  }, [lastNoEventsContext, sofiaEnabled])

  // SOFIA - CONTEXTUAL COMMENTS WITH TOGGLE
  return (
    <div className="fixed bottom-4 right-4 md:bottom-6 md:right-6 z-50">
      <div className="relative group">
        {/* Toggle Button Modernizado */}
        <button
          onClick={() => setSofiaEnabled(!sofiaEnabled)}
          className={`absolute -top-1 -left-1 md:-top-2 md:-left-2 w-6 h-6 md:w-7 md:h-7 rounded-full text-xs font-bold transition-all duration-300 backdrop-blur-xl border-2 z-10 shadow-lg ${
            sofiaEnabled
              ? 'bg-gradient-to-br from-teal-400 to-cyan-600 border-white/30 text-white hover:scale-110 hover:shadow-teal-500/50'
              : 'bg-gray-500/80 border-gray-400/50 text-white/70 hover:bg-gray-400/80'
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
          className={`relative transform transition-all duration-500 ${
            sofiaEnabled
              ? 'hover:scale-110 animate-float'
              : 'opacity-40 cursor-not-allowed grayscale'
          }`}
          disabled={!sofiaEnabled}
        >
          {/* Glow effect exterior */}
          <div className={`absolute -inset-2 bg-gradient-to-br from-pink-500 via-purple-500 to-pink-600 rounded-full blur-xl transition-opacity duration-500 ${
            sofiaEnabled ? 'opacity-60 group-hover:opacity-90' : 'opacity-0'
          }`}></div>

          {/* Sofia Avatar Modernizado */}
          <div className="relative w-20 h-20 md:w-24 md:h-24 bg-gradient-to-br from-pink-500 via-purple-500 to-pink-600 rounded-full flex items-center justify-center shadow-2xl overflow-hidden border-4 border-white/20 backdrop-blur-xl">
            {/* Brillo animado */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent animate-pulse"></div>
            {/* Emoji */}
            <span className="relative text-5xl md:text-6xl filter drop-shadow-lg">👩‍🎨</span>
          </div>

        </button>

        {/* Tooltip de Sofia - DISEÑO MEJORADO */}
        {showTip && sofiaEnabled && (
          <div className="absolute bottom-full mb-4 md:mb-5 -right-4 md:-left-80 md:right-auto animate-fade-in-up">
            <div className="relative bg-gradient-to-br from-pink-500/90 to-purple-600/90 backdrop-blur-xl text-white px-8 py-4 rounded-3xl font-medium transition-all shadow-[0_8px_30px_rgb(0,0,0,0.3)] z-50 w-auto max-w-[calc(100vw-3rem)] hover:shadow-[0_12px_40px_rgb(0,0,0,0.4)] hover:scale-105 border border-white/20">
              <span className="break-words whitespace-normal leading-relaxed text-sm md:text-base">{currentTip}</span>
              {/* Flecha hacia la derecha (hacia Sofia) - desktop */}
              <div className="hidden md:block absolute top-1/2 -right-2 transform -translate-y-1/2 w-4 h-4 bg-gradient-to-br from-pink-500/90 to-purple-600/90 rotate-45 border-r border-t border-white/20"></div>
              {/* Flecha hacia abajo (móvil) */}
              <div className="md:hidden absolute -bottom-2 right-8 w-4 h-4 bg-gradient-to-br from-pink-500/90 to-purple-600/90 rotate-45 border-r border-b border-white/20"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FloatingChat