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

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 mb-4">
      {/* Header clickable para toggle */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 text-left hover:bg-gray-50 rounded-t-lg transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="font-medium text-gray-900">
              Información de Scrapers
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
              {scrapers_info.filter(s => s.status === 'success').length}/{total_scrapers} exitosos
            </span>
            <svg
              className={`w-4 h-4 text-gray-500 transition-transform ${
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
        
        {/* Summary siempre visible */}
        <div className="text-sm text-gray-600 mt-1">
          {summary}
        </div>
      </button>

      {/* Contenido expandible */}
      {isVisible && (
        <div className="border-t border-gray-200 px-4 py-3">
          <div className="space-y-2">
            {scrapers_info.map((scraper, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
              >
                <div className="flex items-center space-x-3">
                  {/* Status icon */}
                  <div className={`w-2 h-2 rounded-full ${
                    scraper.status === 'success' 
                      ? 'bg-green-500' 
                      : scraper.status === 'failed' 
                        ? 'bg-red-500' 
                        : 'bg-yellow-500'
                  }`}></div>
                  
                  {/* Scraper name */}
                  <span className="font-medium text-gray-900">
                    {scraper.name}
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  {/* Events count */}
                  <span className={`px-2 py-1 rounded-full ${
                    scraper.events_count > 0 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {scraper.events_count} eventos
                  </span>
                  
                  {/* Response time */}
                  <span className="text-xs font-mono">
                    {scraper.response_time}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Footer stats */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Total eventos obtenidos: {scrapers_info.reduce((sum, s) => sum + s.events_count, 0)}</span>
              <span>Tiempo total: ~{scrapers_info.length > 0 ? '3-8s' : '0s'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScrapersInfo