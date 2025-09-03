import React from 'react'

// Animación para cuando no hay eventos con mensaje personalizado
export const EmptyEventsAnimation: React.FC<{ location?: string }> = ({ location = 'esta zona' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      {/* Animación principal con robots trabajando */}
      <div className="relative mb-8">
        {/* Robot principal animado */}
        <div className="relative">
          <div className="w-32 h-32 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-3xl flex items-center justify-center mb-4 animate-bounce" style={{ animationDuration: '2s' }}>
            <div className="text-6xl animate-pulse">🤖</div>
          </div>
          
          {/* Partículas flotantes */}
          <div className="absolute -top-2 -right-2 w-6 h-6 bg-purple-400/30 rounded-full animate-ping"></div>
          <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-pink-400/30 rounded-full animate-ping" style={{ animationDelay: '0.5s' }}></div>
          <div className="absolute top-4 -left-4 w-3 h-3 bg-cyan-400/30 rounded-full animate-ping" style={{ animationDelay: '1s' }}></div>
        </div>
        
        {/* Herramientas flotantes */}
        <div className="absolute -left-8 top-8 animate-bounce" style={{ animationDelay: '0.3s', animationDuration: '1.8s' }}>
          <div className="text-2xl">🔧</div>
        </div>
        <div className="absolute -right-8 top-12 animate-bounce" style={{ animationDelay: '0.6s', animationDuration: '2.2s' }}>
          <div className="text-2xl">⚙️</div>
        </div>
        <div className="absolute -right-4 bottom-4 animate-bounce" style={{ animationDelay: '0.9s', animationDuration: '1.5s' }}>
          <div className="text-xl">🔍</div>
        </div>
        
        {/* Líneas de conexión animadas */}
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2">
          <div className="flex space-x-1">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className="w-2 h-2 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-pulse"
                style={{ animationDelay: `${index * 0.2}s` }}
              ></div>
            ))}
          </div>
        </div>
      </div>

      {/* Título principal con animación de escritura */}
      <div className="mb-4">
        <h3 className="text-3xl font-bold text-white/90 mb-2 animate-fade-in">
          🔄 ¡Te esperamos pronto!
        </h3>
        <div className="h-1 w-32 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto animate-pulse"></div>
      </div>

      {/* Mensaje personalizado con animación typewriter */}
      <div className="max-w-lg space-y-3">
        <p className="text-xl text-white/80 font-medium animate-slide-up">
          Estamos actualizando la base todos los días
        </p>
        <p className="text-lg text-white/70 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          Nuestros robots están trabajando 24/7 para encontrar los mejores eventos en <span className="text-purple-300 font-semibold">{location}</span>
        </p>
        <p className="text-base text-white/60 animate-slide-up" style={{ animationDelay: '0.6s' }}>
          ¡Vuelve pronto para descubrir experiencias increíbles! 🎉
        </p>
      </div>

      {/* Barra de progreso animada */}
      <div className="mt-8 w-full max-w-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-white/60">Actualizando eventos</span>
          <span className="text-sm text-white/60">∞</span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500 rounded-full animate-progress-bar"></div>
        </div>
      </div>

      {/* Mini robots trabajando */}
      <div className="mt-8 flex space-x-6">
        {[
          { emoji: '🤖', label: 'Facebook', delay: '0s' },
          { emoji: '🔍', label: 'Eventbrite', delay: '0.5s' },
          { emoji: '⚡', label: 'Instagram', delay: '1s' },
          { emoji: '🎯', label: 'Venues', delay: '1.5s' }
        ].map((robot, index) => (
          <div key={robot.label} className="flex flex-col items-center animate-float" style={{ animationDelay: robot.delay }}>
            <div className="text-2xl mb-2 transform hover:scale-110 transition-transform cursor-pointer">
              {robot.emoji}
            </div>
            <div className="text-xs text-white/50 font-medium">{robot.label}</div>
            <div className="w-8 h-1 bg-white/10 rounded-full mt-1 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-pulse" 
                style={{ 
                  width: `${60 + (index * 20)}%`,
                  animationDelay: robot.delay 
                }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes progress-bar {
          0% { transform: translateX(-100%); }
          50% { transform: translateX(0%); }
          100% { transform: translateX(100%); }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        
        .animate-fade-in {
          animation: fade-in 1s ease-out;
        }
        
        .animate-slide-up {
          animation: slide-up 0.8s ease-out;
        }
        
        .animate-progress-bar {
          animation: progress-bar 3s ease-in-out infinite;
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}

// Versión compacta para espacios pequeños
export const EmptyEventsCompact: React.FC<{ location?: string }> = ({ location = 'esta zona' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="text-4xl mb-4 animate-bounce">🤖</div>
      <h4 className="text-xl font-semibold text-white/90 mb-2">¡Actualizando eventos!</h4>
      <p className="text-white/70 text-sm max-w-xs">
        Nuestros robots están buscando eventos geniales en {location}. ¡Vuelve pronto! 🎉
      </p>
      
      <div className="mt-4 flex space-x-2">
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            className="w-2 h-2 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-bounce"
            style={{ animationDelay: `${index * 0.2}s` }}
          ></div>
        ))}
      </div>
    </div>
  )
}

export default EmptyEventsAnimation