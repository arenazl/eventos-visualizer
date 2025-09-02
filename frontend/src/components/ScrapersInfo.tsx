import React from 'react'

interface ScraperInfo {
  name: string
  status: 'success' | 'failed' | 'timeout'
  events_count: number
  response_time: string
  message: string
}

interface ScrapersExecution {
  scrapers_called: string[]
  total_scrapers: number
  scrapers_info: ScraperInfo[]
  summary: string
}

interface ScrapersInfoProps {
  scrapersExecution: ScrapersExecution | null
  isVisible: boolean
  onToggle: () => void
}

export const ScrapersInfo: React.FC<ScrapersInfoProps> = ({
  scrapersExecution,
  isVisible,
  onToggle,
}) => {
  if (!scrapersExecution) return null

  const { scrapers_info, total_scrapers, summary } = scrapersExecution
  
  // Validación adicional para evitar errores
  if (!scrapers_info || !Array.isArray(scrapers_info)) {
    return null
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 backdrop-blur-sm rounded-xl shadow-sm border border-purple-100/50 mb-4 transition-all duration-300 hover:shadow-md">
      {/* Header clickable para toggle */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 text-left hover:bg-white/30 rounded-xl transition-all duration-200"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse shadow-sm"></div>
            <span className="font-medium text-gray-700 text-sm">
              🏭 Factory Industrial • {scrapers_info.filter(s => s.status === 'success').length} scrapers activos
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-purple-600 bg-purple-100/70 px-2 py-1 rounded-full font-medium">
              {scrapers_info.reduce((sum, s) => sum + s.events_count, 0)} eventos
            </span>
            <span className="text-xs text-gray-500 font-mono">
              {scrapers_info.length > 0 ? '~2.5s' : '0s'}
            </span>
            <svg
              className={`w-3 h-3 text-gray-400 transition-transform duration-200 ${
                isVisible ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        
        {/* Summary más sutil */}
        <div className="text-xs text-gray-500 mt-1 opacity-75">
          {summary}
        </div>
      </button>

      {/* Contenido expandible */}
      {isVisible && (
        <div className="border-t border-purple-100/50 px-4 py-3 bg-white/20 rounded-b-xl">
          <div className="space-y-2">
            {scrapers_info.map((scraper, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white/60 backdrop-blur-sm rounded-lg hover:bg-white/80 transition-all duration-200"
              >
                <div className="flex items-center space-x-3">
                  {/* Status icon */}
                  <div className={`w-2 h-2 rounded-full shadow-sm ${
                    scraper.status === 'success' 
                      ? 'bg-emerald-400' 
                      : scraper.status === 'failed' 
                        ? 'bg-red-400' 
                        : 'bg-amber-400'
                  }`}></div>
                  
                  {/* Scraper name */}
                  <span className="font-medium text-gray-700 text-sm">
                    {scraper.name}
                  </span>
                </div>
                
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  {/* Events count */}
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    scraper.events_count > 0 
                      ? 'bg-emerald-100 text-emerald-700' 
                      : 'bg-gray-100/80 text-gray-600'
                  }`}>
                    {scraper.events_count}
                  </span>
                  
                  {/* Response time */}
                  <span className="text-xs font-mono text-gray-500 bg-gray-100/50 px-2 py-1 rounded">
                    {scraper.response_time}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Footer stats mejorado */}
          <div className="mt-3 pt-3 border-t border-purple-100/50">
            <div className="flex justify-between text-xs text-gray-500 bg-white/40 rounded-lg px-3 py-2">
              <span className="flex items-center space-x-1">
                <span className="text-purple-600 font-medium">📊</span>
                <span>{scrapers_info.reduce((sum, s) => sum + s.events_count, 0)} eventos totales</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="text-purple-600 font-medium">⚡</span>
                <span>{scrapers_info.length > 0 ? '~2.5s' : '0s'} promedio</span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScrapersInfo