import React, { useState, useEffect } from 'react'

interface TypewriterLoadingProps {
  className?: string
}

const TypewriterLoading: React.FC<TypewriterLoadingProps> = ({ className = "" }) => {
  const [currentText, setCurrentText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)
  
  const messages = [
    "🎯 Vas a encontrar todo lo que estás buscando...",
    "🚀 Explorando los mejores eventos para vos...",
    "✨ Preparando experiencias increíbles...",
    "🎪 Conectando con lugares únicos...",
    "🎵 Descubriendo eventos que van a encantarte...",
    "🌟 Curandeando las mejores opciones..."
  ]

  useEffect(() => {
    const currentMessage = messages[currentIndex]
    
    const timeout = setTimeout(() => {
      if (!isDeleting && currentText === currentMessage) {
        // Pausa antes de empezar a borrar
        setTimeout(() => setIsDeleting(true), 1500)
      } else if (isDeleting && currentText === '') {
        // Cambiar al siguiente mensaje
        setIsDeleting(false)
        setCurrentIndex((prev) => (prev + 1) % messages.length)
      } else if (isDeleting) {
        // Borrar caracteres
        setCurrentText(currentMessage.substring(0, currentText.length - 1))
      } else {
        // Escribir caracteres
        setCurrentText(currentMessage.substring(0, currentText.length + 1))
      }
    }, isDeleting ? 30 : 80) // Más rápido escribir y borrar
    
    return () => clearTimeout(timeout)
  }, [currentText, currentIndex, isDeleting, messages])

  return (
    <div className={`flex flex-col items-center justify-center min-h-[400px] ${className}`}>
      {/* Contenedor principal con glassmorphism */}
      <div className="relative bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl p-8 shadow-2xl max-w-md mx-auto">
        
        {/* Animación de pulso de fondo */}
        <div className="absolute inset-0 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-3xl animate-pulse"></div>
        
        {/* Icono animado */}
        <div className="relative flex justify-center mb-6">
          <div className="relative">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-spin"></div>
            <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
              <span className="text-2xl animate-bounce">🎉</span>
            </div>
          </div>
        </div>
        
        {/* Texto typewriter */}
        <div className="relative text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            {currentText}
            <span className="animate-pulse text-purple-500">|</span>
          </h2>
          
          {/* Barra de progreso animada */}
          <div className="w-full bg-gray-200/50 rounded-full h-2 mt-4 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse"></div>
          </div>
          
          <p className="text-sm text-gray-600 mt-3 opacity-75">
            Preparando la mejor experiencia...
          </p>
        </div>
        
        {/* Elementos decorativos flotantes */}
        <div className="absolute -top-2 -right-2 w-6 h-6 bg-purple-400 rounded-full animate-ping opacity-75"></div>
        <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-pink-400 rounded-full animate-ping opacity-75 animation-delay-500"></div>
        <div className="absolute top-1/2 -left-4 w-3 h-3 bg-blue-400 rounded-full animate-bounce opacity-75 animation-delay-1000"></div>
      </div>
      
      {/* Elementos decorativos adicionales */}
      <div className="flex justify-center space-x-2 mt-6">
        <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce"></div>
        <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce animation-delay-200"></div>
        <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce animation-delay-400"></div>
      </div>
    </div>
  )
}

export default TypewriterLoading