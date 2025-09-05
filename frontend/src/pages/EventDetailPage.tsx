import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import SidePanel from '../components/SidePanel'

interface Event {
  title: string
  description?: string
  start_datetime: string
  venue_name: string
  venue_address?: string
  category: string
  price: number | null | undefined
  currency: string
  is_free: boolean
  image_url: string
  latitude?: number
  longitude?: number
  source?: string
  status?: string
}

const EventDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false)
  const [aiInsight, setAiInsight] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    console.log('🔄 EventDetailPage useEffect triggered - ID changed to:', id)
    fetchEventDetails()
  }, [id, location.state])

  useEffect(() => {
    if (event) {
      fetchAIInsight()
    }
  }, [event])

  const fetchAIInsight = async () => {
    if (!event) return

    setAiLoading(true)
    try {
      const response = await fetch('http://172.29.228.80:8001/api/ai/event-insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: event.title.toLowerCase().replace(/\s+/g, '-').replace(/[.,]/g, ''),
          title: event.title,
          venue_name: event.venue_name,
          category: event.category,
          location: event.venue_address || 'Buenos Aires'
        })
      })

      const data = await response.json()
      if (data.success) {
        setAiInsight(data.insight)
      }
    } catch (error) {
      console.error('Error fetching AI insight:', error)
    } finally {
      setAiLoading(false)
    }
  }

  const fetchEventDetails = async () => {
    try {
      // 1. Primero intentar usar los datos pasados por navegación
      const eventFromState = location.state?.event
      console.log('🔍 EventDetailPage - URL ID:', id)
      console.log('🔍 EventDetailPage - Navigation State:', location.state)
      console.log('🔍 EventDetailPage - Event from state:', eventFromState)

      if (eventFromState) {
        console.log('✅ Using event from navigation state:', eventFromState.title)
        setEvent(eventFromState)
        setLoading(false)
        return
      }

      // 2. Si no hay state, buscar en sessionStorage
      // Primero intentamos con el ID tal cual viene de la URL
      console.log('🔍 Looking for sessionStorage key:', `event-${id}`)
      let storedEvent = sessionStorage.getItem(`event-${id}`)

      // Si no se encuentra, intentamos decodificar caracteres especiales
      if (!storedEvent) {
        const decodedId = decodeURIComponent(id || '')
        console.log('🔍 Trying decoded ID:', decodedId)
        storedEvent = sessionStorage.getItem(`event-${decodedId}`)
      }

      // También intentamos buscar por todas las keys en sessionStorage
      if (!storedEvent) {
        console.log('🔍 Searching all sessionStorage keys...')
        const allKeys = Object.keys(sessionStorage)
        const eventKeys = allKeys.filter(key => key.startsWith('event-'))
        console.log('🔍 Found event keys in storage:', eventKeys)

        // Intentar encontrar una coincidencia parcial
        for (const key of eventKeys) {
          const storedData = sessionStorage.getItem(key)
          if (storedData) {
            const parsedData = JSON.parse(storedData)
            // Generar el mismo ID que generaría EventCardModern
            const generatedId = parsedData.title
              .toLowerCase()
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-+|-+$/g, '')

            console.log(`🔍 Comparing: URL ID "${id}" vs Generated "${generatedId}" for "${parsedData.title}"`)

            if (generatedId === id) {
              console.log('✅ Found matching event by generated ID!')
              storedEvent = storedData
              break
            }
          }
        }
      }

      if (storedEvent) {
        console.log('✅ Using event from sessionStorage')
        const parsedEvent = JSON.parse(storedEvent)
        setEvent(parsedEvent)
        setLoading(false)
        return
      }

      // Fallback to show not found
      setLoading(false)
    } catch (error) {
      console.error('Error fetching event details:', error)
      setLoading(false)
    }
  }

  const formatDate = (dateString: string | null | undefined) => {
        if (!dateString) return 'Fecha por confirmar'

        const date = new Date(dateString)
        if (isNaN(date.getTime())) return 'Fecha por confirmar'

        return date.toLocaleDateString('es-AR', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      }

      const formatPrice = (price: number | null | undefined, currency: string, isFree: boolean) => {
        if (isFree) return 'Evento Gratuito'
        if (!price || price === 0) return 'Consultar Precio'
        return `${currency} ${price.toLocaleString()}`
      }

      if (loading) {
        return (
          <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )
      }

      if (!event) {
        return (
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Evento no encontrado</h2>
              <button
                onClick={() => navigate('/')}
                className="text-blue-600 hover:underline"
              >
                Volver al inicio
              </button>
            </div>
          </div>
        )
      }

      return (
        <>
          <div className="min-h-screen bg-gray-50">
            {/* Hero Image */}
            <div className="relative h-64 md:h-96 w-full">
              <img
                src={event.image_url}
                alt={event.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />

              {/* Back button */}
              <button
                onClick={() => navigate('/')}
                className="absolute top-4 left-4 p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>

              {/* Edit button */}
              <button
                onClick={() => setIsEditPanelOpen(true)}
                className="absolute top-4 right-4 px-4 py-2 bg-white/90 backdrop-blur rounded-lg hover:bg-white transition-colors flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Editar</span>
              </button>
            </div>

            {/* Content */}
            <div className="max-w-4xl mx-auto px-4 py-8 -mt-20 relative z-10">
              <div className="bg-white rounded-xl shadow-lg p-6 md:p-8">
                {/* Category & Price badges */}
                <div className="flex items-center justify-between mb-4">
                  <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                    {event.category}
                  </span>
                  <span className={`${event.is_free ? 'bg-green-600' : 'bg-gray-800'} text-white px-4 py-2 rounded-lg font-bold`}>
                    {formatPrice(event.price, event.currency, event.is_free)}
                  </span>
                </div>

                {/* Title */}
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                  {event.title}
                </h1>

                {/* Date & Location */}
                <div className="space-y-3 mb-6">
                  <div className="flex items-start space-x-3">
                    <svg className="w-6 h-6 text-gray-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">Fecha y hora</p>
                      <p className="text-gray-600">{formatDate(event.start_datetime)}</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <svg className="w-6 h-6 text-gray-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">{event.venue_name}</p>
                      <p className="text-gray-600">{event.venue_address}</p>
                      {event.latitude && event.longitude && (
                        <a
                          href={`https://maps.google.com/?q=${event.latitude},${event.longitude}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-sm mt-1 inline-block"
                        >
                          Ver en Google Maps →
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div className="border-t pt-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">Acerca del evento</h2>
                  <p className="text-gray-700 leading-relaxed">{event.description}</p>
                </div>

                {/* Action buttons */}
                <div className="flex flex-col sm:flex-row gap-3 mt-8">
                  <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg font-medium transition-colors">
                    Comprar entradas
                  </button>
                  <button className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                    <span>Guardar evento</span>
                  </button>
                  <button className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.032 4.026A9.001 9.001 0 1112 3a9.001 9.001 0 015.716 14.026m-7.432-2.368A3 3 0 1115 12a3 3 0 01-5.716 2.658z" />
                    </svg>
                    <span>Compartir</span>
                  </button>
                </div>
              </div>

              {/* Sección de IA - Abajo de la página como pidió el usuario */}
              <div className="bg-white rounded-xl shadow-lg mt-6 overflow-hidden">
                <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">✨</span>
                    <div>
                      <h2 className="text-xl font-bold">Análisis Inteligente</h2>
                      <p className="text-purple-100 text-sm">Información generada por IA para este evento</p>
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  {aiLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin h-6 w-6 border-2 border-purple-500 rounded-full border-t-transparent"></div>
                      <span className="ml-2 text-gray-600">Analizando evento con IA...</span>
                    </div>
                  ) : aiInsight ? (
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Columna izquierda */}
                      <div className="space-y-4">
                        {/* Qué esperar */}
                        <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-xl">
                          <h3 className="font-bold text-purple-600 mb-2 flex items-center gap-2">
                            <span>🎯</span>
                            Qué esperar
                          </h3>
                          <p className="text-gray-700">{aiInsight.quick_insight}</p>
                        </div>

                        {/* Info del artista */}
                        {aiInsight.artist_info && (
                          <div className="bg-blue-50 p-4 rounded-xl">
                            <h3 className="font-bold text-blue-600 mb-2 flex items-center gap-2">
                              <span>🎤</span>
                              Sobre el artista
                            </h3>
                            <p className="text-gray-700">{aiInsight.artist_info}</p>
                          </div>
                        )}

                        {/* Cómo llegar */}
                        <div className="bg-green-50 p-4 rounded-xl">
                          <h3 className="font-bold text-green-600 mb-2 flex items-center gap-2">
                            <span>🚌</span>
                            Cómo llegar
                          </h3>
                          <p className="text-gray-700">{aiInsight.transport || "Colectivos 60, 152, 29"}</p>
                        </div>
                      </div>

                      {/* Columna derecha */}
                      <div className="space-y-4">
                        {/* Cerca del lugar */}
                        <div className="bg-orange-50 p-4 rounded-xl">
                          <h3 className="font-bold text-orange-600 mb-2 flex items-center gap-2">
                            <span>📍</span>
                            Cerca del lugar
                          </h3>
                          <p className="text-gray-700">{aiInsight.nearby || "Bares y restaurantes"}</p>
                        </div>

                        {/* Sobre el lugar */}
                        {aiInsight.venue_tip && (
                          <div className="bg-indigo-50 p-4 rounded-xl">
                            <h3 className="font-bold text-indigo-600 mb-2 flex items-center gap-2">
                              <span>🏛️</span>
                              Sobre el lugar
                            </h3>
                            <p className="text-gray-700">{aiInsight.venue_tip}</p>
                          </div>
                        )}

                        {/* Tip Pro */}
                        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-xl border-l-4 border-yellow-400">
                          <h3 className="font-bold text-yellow-600 mb-2 flex items-center gap-2">
                            <span>💡</span>
                            Tip Pro
                          </h3>
                          <p className="text-gray-700">{aiInsight.pro_tip || "Llegá 30 min antes"}</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-600">No se pudo obtener información inteligente para este evento</p>
                    </div>
                  )}

                  {/* Footer de la sección IA */}
                  {aiInsight && (
                    <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between items-center">
                      <div className="text-sm text-gray-500">
                        Ambiente: <span className="font-semibold text-gray-700">{aiInsight.vibe || "Copado"}</span>
                      </div>
                      <div className="text-xs text-purple-500 flex items-center gap-1">
                        <span>✨</span>
                        <span>Powered by Gemini AI</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Side Panel para edición */}
          <SidePanel
            isOpen={isEditPanelOpen}
            onClose={() => setIsEditPanelOpen(false)}
            title="Editar evento"
            width="lg"
          >
            <form className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Título del evento
                </label>
                <input
                  type="text"
                  defaultValue={event.title}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Descripción
                </label>
                <textarea
                  rows={4}
                  defaultValue={event.description}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Precio
                  </label>
                  <input
                    type="number"
                    defaultValue={event.price}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoría
                  </label>
                  <select
                    defaultValue={event.category}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="music">Música</option>
                    <option value="sports">Deportes</option>
                    <option value="cultural">Cultural</option>
                    <option value="tech">Tecnología</option>
                    <option value="party">Fiestas</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lugar
                </label>
                <input
                  type="text"
                  defaultValue={event.venue_name}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dirección
                </label>
                <input
                  type="text"
                  defaultValue={event.venue_address}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_free"
                  defaultChecked={event.is_free}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_free" className="ml-2 block text-sm text-gray-900">
                  Evento gratuito
                </label>
              </div>

              <div className="pt-6 border-t flex space-x-3">
                <button
                  type="button"
                  onClick={() => setIsEditPanelOpen(false)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  Guardar cambios
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditPanelOpen(false)}
                  className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </SidePanel>
        </>
      )
    }

export default EventDetailPage