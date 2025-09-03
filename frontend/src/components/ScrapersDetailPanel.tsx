import React from 'react'
import { useEvents } from '../stores/EventsStore'

const ScrapersDetailPanel: React.FC = () => {
  const { 
    sourceTiming, 
    performanceStats, 
    isStreaming,
    streamingSource,
    streamingProgress,
    streamingMessage,
    events,
    scrapersExecution
  } = useEvents()

  const totalEvents = events.length
  const hasScrapersData = scrapersExecution?.scrapers_info?.length > 0
  const hasSourceTiming = sourceTiming.length > 0

  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      {/* Header siempre visible */}
      <div className={`w-full flex items-center justify-between px-4 py-2 backdrop-blur-xl border transition-all duration-200 rounded-t-lg ${
          isStreaming 
            ? 'bg-green-500/20 border-green-400/30 text-green-300' 
            : 'bg-white/10 border-white/20 text-white/80'
        }`}
      >
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className="font-medium text-sm">
            {isStreaming ? 'Scrapers En Vivo' : 'Panel Técnico'}
          </span>
        </div>
        
        <div className="flex items-center space-x-3 text-xs">
          {isStreaming && streamingSource && (
            <span className="text-green-300">
              🔄 {streamingSource}
            </span>
          )}
          <span className="font-bold">{totalEvents} eventos</span>
          {hasScrapersData ? (
            <span className="text-white/60">
              {scrapersExecution.scrapers_called.length} scrapers
            </span>
          ) : hasSourceTiming && (
            <span className="text-white/60">
              {sourceTiming.length} APIs
            </span>
          )}
        </div>
      </div>

      {/* Panel detallado */}
      <div className="backdrop-blur-xl bg-black/40 border-l border-r border-b border-white/20 rounded-b-lg p-3 shadow-2xl">
        
        {/* Streaming actual */}
        {isStreaming && streamingSource && (
          <div className="mb-3 p-2 bg-green-500/20 border border-green-400/30 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-green-300 text-sm">🔄 {streamingSource}</span>
              <span className="text-green-400 text-xs">{streamingProgress}%</span>
            </div>
            <div className="text-green-200 text-xs">{streamingMessage}</div>
            <div className="mt-1 bg-green-900/50 rounded-full h-1">
              <div 
                className="bg-green-400 h-1 rounded-full transition-all duration-300"
                style={{ width: `${streamingProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* SCRAPERS DINÁMICOS - Priorizar scrapersExecution */}
        {hasScrapersData ? (
          <div className="space-y-2">
            <div className="text-xs text-white/60 mb-2">
              📊 {scrapersExecution.summary}
            </div>
            {scrapersExecution.scrapers_info.map((scraper, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-white/5 rounded text-xs">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">
                    {scraper.name.includes('Facebook') ? '🔥' : 
                     scraper.name.includes('Eventbrite') ? '🎫' : 
                     scraper.name.includes('Meetup') ? '👥' :
                     scraper.name.includes('Bandsintown') ? '🎵' : '🕷️'}
                  </span>
                  <span className="text-white/90">{scraper.name}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-white/60">{scraper.events_count} eventos</span>
                  <span className="text-white/60">{scraper.response_time}</span>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    scraper.status === 'success' ? 'bg-green-400/20 text-green-400' :
                    scraper.status === 'failed' ? 'bg-red-400/20 text-red-400' : 
                    'bg-yellow-400/20 text-yellow-400'
                  }`}>
                    {scraper.status === 'success' ? '✅' : scraper.status === 'failed' ? '❌' : '⏳'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : hasSourceTiming ? (
          // Fallback: Usar sourceTiming si no hay scrapersExecution
          <div className="space-y-2">
            {sourceTiming.map((timing, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-white/5 rounded text-xs">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">
                    {timing.source === 'facebook' ? '🔥' : 
                     timing.source === 'eventbrite' ? '🎫' : 
                     timing.source === 'meetup' ? '👥' : '🕷️'}
                  </span>
                  <span className="text-white/90 capitalize">{timing.source}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-white/60">{timing.eventTimes.length} eventos</span>
                  <span className="text-white/60">{timing.totalTime ? Math.round(timing.totalTime) : '⏳'}ms</span>
                  <span className="px-2 py-1 bg-green-400/20 text-green-400 rounded-full text-xs">✅</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Estado inicial
          <div className="text-center py-3">
            <div className="text-white/60 text-sm">
              🔍 Esperando scrapers... {totalEvents > 0 ? `(${totalEvents} eventos cargados)` : ''}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScrapersDetailPanel