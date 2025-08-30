import React from 'react'

// Skeleton Card para loading de eventos
export const EventCardSkeleton: React.FC = () => {
  return (
    <div className="relative group animate-pulse">
      <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-cyan-600/20 rounded-2xl blur opacity-30"></div>
      <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6 hover:border-white/40 transition-all duration-500">
        {/* Imagen skeleton */}
        <div className="w-full h-48 bg-white/10 rounded-xl mb-4"></div>
        
        {/* Título skeleton */}
        <div className="h-6 bg-white/15 rounded-lg mb-3"></div>
        <div className="h-4 bg-white/10 rounded-lg w-3/4 mb-4"></div>
        
        {/* Detalles skeleton */}
        <div className="flex items-center gap-3 mb-3">
          <div className="w-4 h-4 bg-white/10 rounded-full"></div>
          <div className="h-4 bg-white/10 rounded-lg flex-1"></div>
        </div>
        
        <div className="flex items-center gap-3 mb-4">
          <div className="w-4 h-4 bg-white/10 rounded-full"></div>
          <div className="h-4 bg-white/10 rounded-lg w-2/3"></div>
        </div>
        
        {/* Precio skeleton */}
        <div className="flex justify-between items-center">
          <div className="h-6 bg-white/15 rounded-lg w-20"></div>
          <div className="w-8 h-8 bg-white/10 rounded-full"></div>
        </div>
      </div>
    </div>
  )
}

// Grid de skeletons
export const EventsGridSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }).map((_, index) => (
        <EventCardSkeleton key={index} />
      ))}
    </div>
  )
}

// Loading moderno con efecto de ondas
export const WaveLoader: React.FC = () => {
  return (
    <div className="flex justify-center items-center py-12">
      <div className="flex space-x-2">
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            className="w-4 h-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-bounce"
            style={{
              animationDelay: `${index * 0.1}s`,
              animationDuration: '0.6s'
            }}
          ></div>
        ))}
      </div>
      <span className="ml-4 text-white/70 text-lg font-medium animate-pulse">
        Buscando eventos geniales...
      </span>
    </div>
  )
}

// Spinner circular elegante
export const CircularLoader: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-white/20 rounded-full animate-spin"></div>
        <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
        <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-r-pink-500 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
      </div>
      <p className="mt-6 text-white/80 text-lg font-medium animate-pulse">
        Cargando experiencias únicas...
      </p>
    </div>
  )
}

// Loading para geolocalización
export const LocationLoader: React.FC = () => {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-blue-500/20 backdrop-blur-xl rounded-full border border-blue-400/30">
      <div className="relative">
        <div className="w-5 h-5 border-2 border-blue-400/30 rounded-full animate-ping"></div>
        <div className="absolute top-1 left-1 w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
      </div>
      <span className="text-blue-200 text-sm font-medium">
        Detectando tu ubicación...
      </span>
    </div>
  )
}

// Estado vacío elegante
export const EmptyState: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-24 h-24 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full flex items-center justify-center mb-6">
        <svg className="w-12 h-12 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>
      <h3 className="text-2xl font-bold text-white/90 mb-3">{title}</h3>
      <p className="text-white/60 text-lg max-w-md">{subtitle}</p>
    </div>
  )
}

export default {
  EventCardSkeleton,
  EventsGridSkeleton,
  WaveLoader,
  CircularLoader,
  LocationLoader,
  EmptyState
}