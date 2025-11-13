import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'
import Juan3DAvatar from './Juan3DAvatar'

const FloatingJuan: React.FC = () => {
  console.log('👨‍💼 DEBUG: Juan Call Center render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, lastSearchContext, lastNoEventsContext, juanEnabled, setJuanEnabled } = useAssistants()
  
  // Juan solo comenta sobre eventos reales - NO tips hardcodeados

  // DESACTIVADO TEMPORALMENTE: Comentarios dinámicos con Gemini AI
  // Para pruebas de performance solo Análisis Inteligente llama a Gemini
  const getAIContextualComment = async (eventTitle: string, category: string, shouldConverse: boolean = false): Promise<string> => {
    console.log('👨‍💼 Juan: AI calls DISABLED - usando fallback hardcoded')
    return getHardcodedComment(eventTitle, category, shouldConverse)
  }

  // Comentarios contextuales basados en evento real
  const getHardcodedComment = (eventTitle: string, category: string, shouldConverse: boolean = false) => {
    const sportsEvents = ['fútbol', 'deporte', 'deportivo', 'river', 'boca', 'racing', 'independiente', 'gimnasia', 'estudiantes']
    const techEvents = ['tech', 'tecnología', 'programación', 'hackathon', 'startup', 'javascript', 'python', 'react', 'ia', 'blockchain']
    const culturalEvents = ['música', 'teatro', 'arte', 'cultura', 'concierto', 'exposición', 'musical', 'opera', 'danza', 'vino', 'cocktail', 'feria', 'retro']
    
    // Detectar si es selección de categoría
    if (eventTitle.startsWith('Categoría:')) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡Algoritmo aprobado! ${category} = 99.8% de adrenalina ⚽🤓`,
          `¡Juan.exe funcionando! ${category} activó modo HYPE 🔥💻`,
          `¡Error 404: Aburrimiento not found! ${category} detected ⚽📊`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (techEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = [
          `¡Stack overflow de felicidad! ${category} = infinite possibilities 💻∞`,
          `¡git commit -m "Usuario inteligente detected"! ${category} FTW 🤖⭐`,
          `¡Juan aprende new skills! ${category} > Netflix, siempre 🧠💻`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword))) {
        const categoryComments = shouldConverse ? [
          `Sofia, ${category} está bien... pero necesita más estadísticas 📊🎭`,
          `${category}... ¿no hay versión .exe de esto? 😅💻`,
          `Hmm Sofia, ${category} loading... ¿dónde están los gráficos? 📈🎨`
        ] : [
          `¡Aprobado! ${category} también compila bien en mi sistema 🎭💻`,
          `¡Cool! ${category} = new Experience() - me gusta 🎵⚡`
        ]
        return categoryComments[Math.floor(Math.random() * categoryComments.length)]
      }
      
      return `¡Buena elección! ${category} puede estar muy bueno 😎`
    }
    
    // Análisis contextual del título real del evento
    const lowerTitle = eventTitle.toLowerCase()
    
    // Eventos específicos de vino/bebidas
    if (lowerTitle.includes('vino') || lowerTitle.includes('cocktail') || lowerTitle.includes('bebida')) {
      const wineComments = shouldConverse ? [
        `Sofia, "${eventTitle}" tiene algorithm complexity O(delicioso) 🍷📊`,
        `${eventTitle}... ok Sofia, es wine.sort() por sabor, análisis aprobado 🍷💻`,
        `Database query: SELECT * FROM eventos WHERE "${eventTitle}" = culture++ 🍷🤓`
      ] : [
        `"${eventTitle}" = optimal user experience detectado 🍷💻`,
        `¡Interesante! "${eventTitle}" parece high-quality social networking 🍷📈`,
        `"${eventTitle}" analysis: cultural event with high engagement probability 🍷⚡`
      ]
      return wineComments[Math.floor(Math.random() * wineComments.length)]
    }
    
    // Eventos de música/conciertos
    if (lowerTitle.includes('concierto') || lowerTitle.includes('música') || lowerTitle.includes('retro') || lowerTitle.includes('festival')) {
      const musicComments = shouldConverse ? [
        `Sofia, "${eventTitle}" = audio streaming en 4K real life, te acepto 🎵💻`,
        `${eventTitle}... hmm, no hay stats pero el user engagement se ve alto 🎶📊`,
        `Ok Sofia, "${eventTitle}" compiled successfully en mi brain.exe 🎵🤓`
      ] : [
        `"${eventTitle}" = real-time audio experience, algoritmo aprobado 🎵💻`,
        `¡Cool! "${eventTitle}" parece excellent performance metrics 🎶⚡`,
        `"${eventTitle}" análisis: high-quality live streaming detected 🎵📈`
      ]
      return musicComments[Math.floor(Math.random() * musicComments.length)]
    }
    
    // Ferias y eventos culturales
    if (lowerTitle.includes('feria') || lowerTitle.includes('expo') || lowerTitle.includes('cultural')) {
      const fairComments = shouldConverse ? [
        `Sofia, "${eventTitle}" = database full de experiencias, ok acepto 🎨💻`,
        `${eventTitle}... ¿tiene APIs disponibles? Se ve interesting 🎭📊`,
        `Debug mode: "${eventTitle}" tiene potential, te acompaño Sofia 🎨🤓`
      ] : [
        `"${eventTitle}" = nueva librería cultural disponible, downloading... 🎨💻`,
        `¡Interesting! "${eventTitle}" parece good social networking event 🎭⚡`,
        `"${eventTitle}" status: ready for installation en mi agenda 🎨📈`
      ]
      return fairComments[Math.floor(Math.random() * fairComments.length)]
    }
    
    if (shouldConverse) {
      if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || lowerTitle.includes(keyword))) {
        const converseComments = [
          `¡Sofia! "${eventTitle}" = 90min de algoritmos perfectos en vivo ⚽🤓`,
          `Error 404 Sofia: "${eventTitle}" ES máxima expresión del analytics 📊⚽`,
          `Sofia.exe stopped working? "${eventTitle}" > cualquier streaming 🇦🇷💻`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
      
      if (culturalEvents.some(keyword => category.toLowerCase().includes(keyword) || lowerTitle.includes(keyword))) {
        const converseComments = [
          `Sofia, "${eventTitle}" está ok... pero ¿tiene Wi-Fi gratis? 😅📶`,
          `"${eventTitle}"... puede ser, si no interfiere con mi deploy del viernes 💻🤝`,
          `Acepto "${eventTitle}" Sofia... si después analizamos estadísticas ⚽📈`
        ]
        return converseComments[Math.floor(Math.random() * converseComments.length)]
      }
    }
    
    if (sportsEvents.some(keyword => category.toLowerCase().includes(keyword) || lowerTitle.includes(keyword))) {
      const sportsComments = [
        `¡"${eventTitle}"! Probability(golazo) = 85.7% - voy con stats 📊⚽`,
        `¡Perfecto! "${eventTitle}" = Real time analytics en vivo, hermano 🤓⚽`,
        `¡Juan approves! "${eventTitle}" > streaming, experiencia 4K IRL 🔥💻`
      ]
      return sportsComments[Math.floor(Math.random() * sportsComments.length)]
    }
    
    if (techEvents.some(keyword => category.toLowerCase().includes(keyword) || lowerTitle.includes(keyword))) {
      const techComments = [
        `¡"${eventTitle}"! Level up++ confirmado, excelente ROI cerebral 💻🧠`,
        `¡Master quest unlocked! "${eventTitle}" = new skills += conocimiento 🚀⚡`,
        `¡Juan.learn("${eventTitle}")! Me gusta esa mentalidad growth mindset 💪🤓`
      ]
      return techComments[Math.floor(Math.random() * techComments.length)]
    }
    
    // Fallback general contextual
    return `¡"${eventTitle}" parece high-quality content! Analytics look promising 🤓📊`
  }

  // Escuchar eventos de interacción
  useEffect(() => {
    // Solo responder si:
    // 1. Juan está habilitado
    // 2. El evento no especifica assistant (cualquiera puede responder) O especifica 'juan'
    const shouldRespond = juanEnabled &&
                          lastEventInteraction &&
                          (!lastEventInteraction.assistant || lastEventInteraction.assistant === 'juan')

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
  }, [lastEventInteraction, juanEnabled])

  // 🔍 Comentario general al hacer búsqueda (perfil: estricto, sensato, práctico)
  useEffect(() => {
    if (lastSearchContext && juanEnabled) {
      const { dayOfWeek, hour, cityName } = lastSearchContext
      let comment = ''
      const cityPrefix = cityName ? `📍 ${cityName}: ` : ''

      // Comentarios SIEMPRE, incluso sin eventos - basados en día y hora (con recordatorios prácticos y sensatos + ciudad)
      if (dayOfWeek === 'Lunes' && hour < 12) {
        const mondayMorning = [
          `${cityPrefix}Lunes temprano buscando eventos? Verificá transporte y horarios ⏰🚌`,
          `${cityPrefix}Planificando con tiempo? Smart move. Confirmá disponibilidad 📅✅`,
          `${cityPrefix}Lunes organizando? Perfecto. Checklist: horarios, transporte, DNI 📝🆔`
        ]
        comment = mondayMorning[Math.floor(Math.random() * mondayMorning.length)]
      } else if (dayOfWeek === 'Viernes' && hour >= 18) {
        const fridayNight = [
          `${cityPrefix}Viernes! Revisá clima y llevá efectivo por las dudas 🌤️💵`,
          `${cityPrefix}Finde cerca! Confirmá ubicaciones exactas y transporte 📍🚗`,
          `${cityPrefix}Viernes tarde! Salí temprano, el tráfico complica 🚙⏰`
        ]
        comment = fridayNight[Math.floor(Math.random() * fridayNight.length)]
      } else if (['Sábado', 'Domingo'].includes(dayOfWeek) && hour < 14) {
        const weekendMorning = [
          `${cityPrefix}Finde activo! Verificá horarios de apertura y precios 💼🕐`,
          `${cityPrefix}Organizando? Checklist: DNI, efectivo, transporte 🆔🚇`,
          `${cityPrefix}Plan de finde! Confirmá ubicaciones antes de salir 📍✅`
        ]
        comment = weekendMorning[Math.floor(Math.random() * weekendMorning.length)]
      } else if (hour >= 23 || hour < 5) {
        const lateNight = [
          `${cityPrefix}Las ${hour}hs! Importante: verificá transporte nocturno 🚍🌙`,
          `${cityPrefix}Tarde ya! Seguridad first: avisá dónde vas 📱🔒`,
          `${cityPrefix}Madrugada! Planificá bien y descansá antes del evento 😴💪`
        ]
        comment = lateNight[Math.floor(Math.random() * lateNight.length)]
      } else {
        const generic = [
          `${cityPrefix}Buscando eventos! Tip: reservar temprano = mejor precio 💰📅`,
          `${cityPrefix}Organizando salidas! Verificá: precio, ubicación, horario ✅🎯`,
          `${cityPrefix}Planificando! Esenciales: DNI, efectivo, cargador 🆔💵🔋`
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
  }, [lastSearchContext, juanEnabled])

  // 🚫 Comentario cuando no hay eventos (perfil: pragmático, solucionador)
  useEffect(() => {
    if (lastNoEventsContext && juanEnabled) {
      const { cityName, searchingNearby } = lastNoEventsContext
      let comment = ''

      if (searchingNearby) {
        const searchingComments = [
          `📍 ${cityName}: No hay eventos aquí. Checkeando zonas cercanas... 🔍`,
          `📍 ${cityName}: 0 resultados. Buscando en ciudades nearby... ⏳`,
          `📍 ${cityName}: Vacío. Expandiendo radio de búsqueda... 🌍`
        ]
        comment = searchingComments[Math.floor(Math.random() * searchingComments.length)]
      } else {
        const noEventsComments = [
          `📍 ${cityName}: Sin eventos disponibles. Tip: probá ciudades cercanas 🔍`,
          `📍 ${cityName}: 0 eventos en calendario. Ampliá tu búsqueda 📅`,
          `📍 ${cityName}: No hay nada programado. Considerá zonas nearby 🌍`
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
  }, [lastNoEventsContext, juanEnabled])

  // JUAN - CONTEXTUAL COMMENTS WITH TOGGLE
  return (
    <div className="fixed bottom-4 left-4 md:bottom-6 md:left-6 z-50">
      <div className="relative group">
        {/* Toggle Button Modernizado */}
        <button
          onClick={() => setJuanEnabled(!juanEnabled)}
          className={`absolute -top-1 -right-1 md:-top-2 md:-right-2 w-6 h-6 md:w-7 md:h-7 rounded-full text-xs font-bold transition-all duration-300 backdrop-blur-xl border-2 z-10 shadow-lg ${
            juanEnabled
              ? 'bg-gradient-to-br from-teal-400 to-cyan-600 border-white/30 text-white hover:scale-110 hover:shadow-teal-500/50'
              : 'bg-gray-500/80 border-gray-400/50 text-white/70 hover:bg-gray-400/80'
          }`}
          title={juanEnabled ? 'Desactivar Juan' : 'Activar Juan'}
        >
          {juanEnabled ? '✓' : '✕'}
        </button>

        <button
          onMouseEnter={() => {
            // Juan solo comenta sobre eventos reales, no tips hardcodeados
          }}
          onMouseLeave={() => {
            // Juan solo comenta sobre eventos reales, no tips hardcodeados
          }}
          className={`relative transform transition-all duration-500 ${
            juanEnabled
              ? 'hover:scale-110 animate-float'
              : 'opacity-40 cursor-not-allowed grayscale'
          }`}
          disabled={!juanEnabled}
        >
          {/* Glow effect exterior */}
          <div className={`absolute -inset-2 bg-gradient-to-br from-cyan-400 via-blue-500 to-cyan-600 rounded-full blur-xl transition-opacity duration-500 ${
            juanEnabled ? 'opacity-60 group-hover:opacity-90' : 'opacity-0'
          }`}></div>

          {/* Juan Avatar Modernizado */}
          <div className="relative w-20 h-20 md:w-24 md:h-24 bg-gradient-to-br from-cyan-400 via-blue-500 to-cyan-600 rounded-full flex items-center justify-center shadow-2xl overflow-hidden border-4 border-white/20 backdrop-blur-xl">
            {/* Brillo animado */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent animate-pulse"></div>
            {/* Emoji */}
            <span className="relative text-5xl md:text-6xl filter drop-shadow-lg">🧑‍💼</span>
          </div>

        </button>

        {/* Tooltip de Juan - DISEÑO MEJORADO HORIZONTAL */}
        {showTip && juanEnabled && (
          <div className="absolute bottom-full mb-4 md:mb-5 -left-4 md:-right-80 md:left-auto animate-fade-in-up">
            <div className="relative bg-gradient-to-br from-cyan-500/90 to-blue-600/90 backdrop-blur-xl text-white px-8 py-4 rounded-3xl font-medium transition-all shadow-[0_8px_30px_rgb(0,0,0,0.3)] z-50 w-auto max-w-[calc(100vw-3rem)] hover:shadow-[0_12px_40px_rgb(0,0,0,0.4)] hover:scale-105 border border-white/20">
              <span className="break-words whitespace-normal leading-relaxed text-sm md:text-base">{currentTip}</span>
              {/* Flecha hacia la izquierda (hacia Juan) - desktop */}
              <div className="hidden md:block absolute top-1/2 -left-2 transform -translate-y-1/2 w-4 h-4 bg-gradient-to-br from-cyan-500/90 to-blue-600/90 rotate-45 border-l border-b border-white/20"></div>
              {/* Flecha hacia abajo (móvil) */}
              <div className="md:hidden absolute -bottom-2 left-8 w-4 h-4 bg-gradient-to-br from-cyan-500/90 to-blue-600/90 rotate-45 border-r border-b border-white/20"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FloatingJuan