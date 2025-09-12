import React, { useState } from 'react'
import StreamingProgressLoader from '../components/StreamingProgressLoader'
import { Link } from 'react-router-dom'

const StreamingTestPage: React.FC = () => {
  const [searchLocation, setSearchLocation] = useState('Barcelona')
  const [showSearch, setShowSearch] = useState(false)
  const [showRecommend, setShowRecommend] = useState(false)
  const [allEvents, setAllEvents] = useState<any[]>([])

  const handleEventsReceived = (events: any[]) => {
    console.log('📨 Eventos recibidos:', events.length)
    setAllEvents(prev => {
      const combined = [...prev, ...events]
      // Deduplicar por título
      const unique = combined.filter((event, index, self) => 
        index === self.findIndex(e => e.title === event.title)
      )
      return unique
    })
  }

  const handleComplete = (results: any) => {
    console.log('✅ Streaming completado:', results)
  }

  const handleError = (error: string) => {
    console.error('❌ Error en streaming:', error)
  }

  const resetTest = () => {
    setShowSearch(false)
    setShowRecommend(false)
    setAllEvents([])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link 
              to="/" 
              className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Volver al inicio
            </Link>
            <button
              onClick={resetTest}
              className="px-4 py-2 bg-red-500/20 text-red-300 border border-red-500/20 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              Reset Test
            </button>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">
              🚀 Test WebSocket Streaming
            </h1>
            <p className="text-white/60 text-lg">
              Prueba de los nuevos WebSockets optimizados con streaming real-time
            </p>
          </div>

          {/* Location Input */}
          <div className="max-w-md mx-auto mb-8">
            <label className="block text-white/80 text-sm font-medium mb-2">
              📍 Ubicación para la prueba:
            </label>
            <input
              type="text"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-purple-500 focus:bg-white/15 transition-all"
              placeholder="Ingresa una ciudad..."
            />
          </div>

          {/* Test Controls */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              onClick={() => {
                resetTest()
                setShowSearch(true)
              }}
              disabled={!searchLocation.trim()}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2 justify-center"
            >
              <span>🔍</span>
              Probar WebSocket Search
            </button>
            
            <button
              onClick={() => {
                resetTest()
                setShowRecommend(true)
              }}
              disabled={!searchLocation.trim()}
              className="px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2 justify-center"
            >
              <span>💡</span>
              Probar WebSocket Recommend
            </button>
          </div>

          {/* Stats */}
          <div className="bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6 mb-8">
            <h3 className="text-lg font-bold text-white mb-4">📊 Estadísticas del Test</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{allEvents.length}</div>
                <div className="text-sm text-white/60">Eventos Totales</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {new Set(allEvents.map(e => e.source)).size}
                </div>
                <div className="text-sm text-white/60">Fuentes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {showSearch || showRecommend ? '🟢' : '⚪'}
                </div>
                <div className="text-sm text-white/60">Estado</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">{searchLocation}</div>
                <div className="text-sm text-white/60">Ubicación</div>
              </div>
            </div>
          </div>
        </div>

        {/* WebSocket Search Test */}
        {showSearch && (
          <div className="mb-8">
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl p-1 mb-4">
              <div className="bg-black/40 backdrop-blur-xl rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-4">
                  🔍 WebSocket Search Test
                </h2>
                <p className="text-white/60 mb-6">
                  Conectándose a <code className="bg-white/10 px-2 py-1 rounded text-sm">ws://172.29.228.80:8001/ws/search-events</code>
                </p>
                <StreamingProgressLoader
                  location={searchLocation}
                  mode="search"
                  onEventsReceived={handleEventsReceived}
                  onComplete={handleComplete}
                  onError={handleError}
                />
              </div>
            </div>
          </div>
        )}

        {/* WebSocket Recommend Test */}
        {showRecommend && (
          <div className="mb-8">
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl p-1 mb-4">
              <div className="bg-black/40 backdrop-blur-xl rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-4">
                  💡 WebSocket Recommend Test
                </h2>
                <p className="text-white/60 mb-6">
                  Conectándose a <code className="bg-white/10 px-2 py-1 rounded text-sm">ws://172.29.228.80:8001/ws/recommend</code>
                </p>
                <StreamingProgressLoader
                  location={searchLocation}
                  mode="recommend"
                  onEventsReceived={handleEventsReceived}
                  onComplete={handleComplete}
                  onError={handleError}
                />
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        {!showSearch && !showRecommend && (
          <div className="bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-8 text-center">
            <div className="text-6xl mb-4">🧪</div>
            <h3 className="text-2xl font-bold text-white mb-4">
              Prueba los WebSockets Streaming
            </h3>
            <p className="text-white/60 mb-6 max-w-2xl mx-auto">
              Este página permite probar los nuevos WebSockets optimizados que muestran 
              eventos en tiempo real conforme cada scraper va completando su ejecución.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              <div className="bg-blue-500/10 rounded-xl p-6">
                <h4 className="text-lg font-bold text-blue-300 mb-2">🔍 Search WebSocket</h4>
                <p className="text-white/60 text-sm">
                  Conecta al endpoint <code>/ws/search-events</code> y muestra eventos 
                  de la ubicación principal en tiempo real.
                </p>
              </div>
              <div className="bg-purple-500/10 rounded-xl p-6">
                <h4 className="text-lg font-bold text-purple-300 mb-2">💡 Recommend WebSocket</h4>
                <p className="text-white/60 text-sm">
                  Conecta al endpoint <code>/ws/recommend</code> y muestra eventos 
                  de ciudades aledañas usando el servicio que detecta ciudades cercanas.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Debug Info */}
        <div className="mt-8 text-center">
          <details className="bg-black/20 rounded-xl p-4">
            <summary className="text-white/60 cursor-pointer">
              🔧 Debug Info (click para expandir)
            </summary>
            <div className="mt-4 text-left">
              <pre className="text-xs text-white/50 bg-black/40 p-4 rounded-lg overflow-auto">
{JSON.stringify({
  location: searchLocation,
  totalEvents: allEvents.length,
  sources: [...new Set(allEvents.map(e => e.source))],
  activeConnections: {
    search: showSearch,
    recommend: showRecommend
  }
}, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}

export default StreamingTestPage