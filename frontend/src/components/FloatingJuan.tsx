import React, { useState, useEffect } from 'react'
import { useAssistants } from '../contexts/AssistantsContext'

const FloatingJuan: React.FC = () => {
  console.log('👨‍💼 DEBUG: Juan Call Center render');
  const [showTip, setShowTip] = useState(false)
  const [currentTip, setCurrentTip] = useState('')
  const { lastEventInteraction, juanEnabled, setJuanEnabled } = useAssistants()
  
  // Juan solo comenta sobre eventos reales - NO tips hardcodeados

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
            // Juan solo comenta sobre eventos reales, no tips hardcodeados
          }}
          onMouseLeave={() => {
            // Juan solo comenta sobre eventos reales, no tips hardcodeados
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
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-ping"></div>
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