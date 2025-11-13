import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { API_BASE_URL } from '../config/api'

interface EventAIHoverProps {
  event: {
    id: string
    title: string
    venue_name: string
    category: string
    location?: string
  }
}

const EventAIHover: React.FC<EventAIHoverProps> = ({ event }) => {
  const [showInsight, setShowInsight] = useState(false)
  const [loading, setLoading] = useState(false)
  const [insight, setInsight] = useState<any>(null)

  const fetchAIInsight = async () => {
    console.log('🤖 Fetching AI insight for:', event.title)
    if (insight) return // Ya lo tenemos cargado

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/event-insight`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event)
      })

      const data = await response.json()
      console.log('🤖 AI Response:', data)
      if (data.success) {
        setInsight(data.insight)
        // Auto-abrir el panel cuando los datos lleguen
        setShowInsight(true)
      }
    } catch (error) {
      console.error('Error fetching AI insight:', error)
      // Datos de fallback
      setInsight({
        quick_insight: "Evento interesante en " + event.venue_name,
        transport: "Colectivos: 60, 152, 29",
        nearby: "Varios bares y restaurantes cerca",
        vibe: "Ambiente copado",
        pro_tip: "Llegá temprano para mejor ubicación"
      })
      // Auto-abrir el panel incluso con datos de fallback
      setShowInsight(true)
    } finally {
      setLoading(false)
    }
  }

  const handleClick = (e: React.MouseEvent) => {
    console.log('🤖 AI Button clicked for:', event.title)
    e.stopPropagation() // Evitar que se active el click de la tarjeta

    // Si ya está abierto, cerrarlo
    if (showInsight) {
      setShowInsight(false)
      return
    }

    // Si ya tenemos datos, mostrarlos inmediatamente
    if (insight) {
      setShowInsight(true)
      return
    }

    // Si no tenemos datos, iniciar fetch y mostrar loading en el botón
    fetchAIInsight()
  }

  console.log('🤖 EventAIHover rendering for:', event.title)

  return (
    <>
      {/* Botón de IA - Integrado en el layout sin posición absoluta */}
      <button
        onClick={handleClick}
        disabled={loading}
        className={`w-10 h-10 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl transition-all duration-300 ${
          loading ? 'cursor-wait' : 'hover:scale-110'
        } flex items-center justify-center text-lg shadow-lg`}
        title={loading ? "Analizando..." : "Análisis con IA"}
      >
        {loading ? (
          <div className="animate-spin h-5 w-5 border-2 border-white rounded-full border-t-transparent"></div>
        ) : (
          '✨'
        )}
      </button>

      {/* Panel lateral sin overlay - No bloquea la navegación */}
      {showInsight && createPortal(
        <div
          className="fixed top-0 right-0 h-full w-96 max-w-[90vw] bg-white dark:bg-gray-900 shadow-2xl z-[9999] overflow-y-auto animate-slide-in-bounce"
          onClick={(e) => e.stopPropagation()}
        >
            {/* Header del modal */}
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">✨</span>
                  <h2 className="text-lg font-bold">Análisis IA</h2>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowInsight(false)
                  }}
                  className="text-white/80 hover:text-white text-xl"
                >
                  ✕
                </button>
              </div>
              <p className="text-sm text-white/90 mt-1">{event.title}</p>
            </div>

            {/* Contenido del modal */}
            <div className="p-4">
              {loading ? (
                <div className="flex items-center justify-center gap-2 py-8">
                  <div className="animate-spin h-6 w-6 border-2 border-purple-500 rounded-full border-t-transparent"></div>
                  <span className="text-gray-600 dark:text-gray-300">Analizando con IA...</span>
                </div>
              ) : insight ? (
                <div className="space-y-4">
                  {/* Insight principal */}
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-4 rounded-xl">
                    <h3 className="font-bold text-purple-600 dark:text-purple-400 mb-2 flex items-center gap-2">
                      <span>🎯</span>
                      Qué esperar
                    </h3>
                    <p className="text-gray-700 dark:text-gray-300">{insight.quick_insight}</p>
                  </div>

                  {/* Info del artista */}
                  {insight.artist_info && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl">
                      <h3 className="font-bold text-blue-600 dark:text-blue-400 mb-2 flex items-center gap-2">
                        <span>🎤</span>
                        Sobre el artista
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300">{insight.artist_info}</p>
                    </div>
                  )}

                  {/* Grid de información práctica */}
                  <div className="grid grid-cols-1 gap-3">
                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-xl">
                      <h3 className="font-bold text-green-600 dark:text-green-400 mb-2 flex items-center gap-2">
                        <span>🚌</span>
                        Cómo llegar
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300">{insight.transport || "Colectivos 60, 152, 29"}</p>
                    </div>

                    <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-xl">
                      <h3 className="font-bold text-orange-600 dark:text-orange-400 mb-2 flex items-center gap-2">
                        <span>📍</span>
                        Cerca del lugar
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300">{insight.nearby || "Bares y restaurantes"}</p>
                    </div>

                    {insight.venue_tip && (
                      <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl">
                        <h3 className="font-bold text-indigo-600 dark:text-indigo-400 mb-2 flex items-center gap-2">
                          <span>🏛️</span>
                          Sobre el lugar
                        </h3>
                        <p className="text-gray-700 dark:text-gray-300">{insight.venue_tip}</p>
                      </div>
                    )}
                  </div>

                  {/* Pro tip destacado */}
                  <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 p-4 rounded-xl border-l-4 border-yellow-400">
                    <h3 className="font-bold text-yellow-600 dark:text-yellow-400 mb-2 flex items-center gap-2">
                      <span>💡</span>
                      Tip Pro
                    </h3>
                    <p className="text-gray-700 dark:text-gray-300">{insight.pro_tip || "Llegá 30 min antes"}</p>
                  </div>

                  {/* Botones de acciones adicionales */}
                  <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button 
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg transform transition-all duration-200 hover:-translate-y-0.5 flex items-center justify-center gap-2"
                      onClick={(e) => {
                        e.stopPropagation()
                        alert('Próximamente: Opiniones sobre el evento')
                      }}
                    >
                      <span>💬</span>
                      Opiniones sobre el evento
                    </button>
                    
                    <button 
                      className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg transform transition-all duration-200 hover:-translate-y-0.5 flex items-center justify-center gap-2"
                      onClick={(e) => {
                        e.stopPropagation()
                        alert('Próximamente: Eventos similares')
                      }}
                    >
                      <span>🔍</span>
                      Eventos similares
                    </button>

                    <button 
                      className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg transform transition-all duration-200 hover:-translate-y-0.5 flex items-center justify-center gap-2"
                      onClick={(e) => {
                        e.stopPropagation()
                        alert('Próximamente: Más detalles')
                      }}
                    >
                      <span>📋</span>
                      Más detalles
                    </button>
                  </div>

                  {/* Footer del análisis */}
                  <div className="text-center pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Ambiente: <span className="font-semibold">{insight.vibe || "Copado"}</span>
                    </p>
                    <p className="text-xs text-purple-500 dark:text-purple-400 mt-1">
                      ✨ Powered by Grok AI
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600 dark:text-gray-300">No se pudo obtener información</p>
                </div>
              )}
            </div>
        </div>,
        document.body
      )}
    </>
  )
}

export default EventAIHover