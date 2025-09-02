import React, { useState } from 'react'
import ScrapersProgressLoader from '../components/ScrapersProgressLoader'

const ScrapersTestPage: React.FC = () => {
  const [testLocation, setTestLocation] = useState('Rio de Janeiro')
  const [testResults, setTestResults] = useState<any>(null)
  const [allEvents, setAllEvents] = useState<any[]>([])

  const handleEventsReceived = (events: any[]) => {
    console.log('📨 Events received:', events.length)
    setAllEvents(events)
  }

  const handleComplete = (results: any) => {
    console.log('✅ Scraping completed:', results)
    setTestResults(results)
  }

  const handleError = (error: string) => {
    console.error('❌ Scraping error:', error)
  }

  const popularLocations = [
    'Rio de Janeiro',
    'Barcelona',
    'Buenos Aires',
    'Mexico City',
    'Madrid',
    'Paris',
    'London',
    'New York'
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="relative overflow-hidden py-12 px-6">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 via-pink-600/10 to-cyan-600/10"></div>
        <div className="relative container mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full px-4 py-2 mb-6">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-white/80 text-sm font-medium">Sistema de Streaming en Vivo</span>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent mb-4">
            🔄 Scrapers en Tiempo Real
          </h1>
          
          <p className="text-xl text-white/70 mb-8 max-w-2xl mx-auto">
            Monitorea el progreso de cada scraper mientras busca eventos internacionales
          </p>

          {/* Location Selector */}
          <div className="relative max-w-md mx-auto mb-8">
            <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-cyan-600/20 rounded-2xl blur opacity-30"></div>
            <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-4">
              <label className="block text-white/70 text-sm font-medium mb-2">
                📍 Ubicación para probar
              </label>
              <input
                type="text"
                value={testLocation}
                onChange={(e) => setTestLocation(e.target.value)}
                placeholder="Ingresa una ciudad..."
                className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              
              {/* Quick location buttons */}
              <div className="flex flex-wrap gap-2 mt-3">
                {popularLocations.map(location => (
                  <button
                    key={location}
                    onClick={() => setTestLocation(location)}
                    className={`px-3 py-1 rounded-full text-xs transition-all ${
                      testLocation === location
                        ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                        : 'bg-white/10 text-white/60 hover:bg-white/20 border border-white/20'
                    }`}
                  >
                    {location}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 pb-12">
        <ScrapersProgressLoader
          location={testLocation}
          limit={30}
          onEventsReceived={handleEventsReceived}
          onComplete={handleComplete}
          onError={handleError}
        />

        {/* Results Summary */}
        {testResults && (
          <div className="mt-8 space-y-6">
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-green-600/20 via-blue-600/20 to-purple-600/20 rounded-2xl blur opacity-30"></div>
              <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  📊 Resumen Final
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-400">
                      {testResults.total_events}
                    </div>
                    <div className="text-white/60 text-sm">Total Eventos</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">
                      {testResults.successful_scrapers}
                    </div>
                    <div className="text-white/60 text-sm">Scrapers Exitosos</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-400">
                      {testResults.total_scrapers}
                    </div>
                    <div className="text-white/60 text-sm">Total Scrapers</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-yellow-400">
                      {Math.round((testResults.successful_scrapers / testResults.total_scrapers) * 100)}%
                    </div>
                    <div className="text-white/60 text-sm">Tasa de Éxito</div>
                  </div>
                </div>

                {/* Detailed Results */}
                {testResults.scrapers_summary && testResults.scrapers_summary.length > 0 && (
                  <div>
                    <h4 className="text-white font-medium mb-3">Detalles por Scraper:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {testResults.scrapers_summary.map((scraper: any, index: number) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-lg">
                              {scraper.name === 'Eventbrite' ? '🎫' : 
                               scraper.name === 'Meetup' ? '🤝' : 
                               scraper.name === 'Facebook' ? '🎯' : '🔍'}
                            </span>
                            <span className="text-white font-medium">{scraper.name}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-white/80">{scraper.events_count} eventos</span>
                            <span className="text-white/60 text-sm">{scraper.execution_time}</span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              scraper.status === 'success' ? 'bg-green-500/20 text-green-300' :
                              scraper.status === 'timeout' ? 'bg-yellow-500/20 text-yellow-300' :
                              'bg-red-500/20 text-red-300'
                            }`}>
                              {scraper.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 bg-black/20 py-6">
        <div className="container mx-auto px-6 text-center">
          <p className="text-white/60 text-sm">
            🚀 Sistema de Streaming WebSocket • 🌍 Scrapers Globales • ⚡ Tiempo Real
          </p>
        </div>
      </div>
    </div>
  )
}

export default ScrapersTestPage