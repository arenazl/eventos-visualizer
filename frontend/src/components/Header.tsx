import React, { useState, useEffect } from 'react'
import { MagnifyingGlassIcon, MapPinIcon } from '@heroicons/react/24/outline'
import SourcesCounter from './SourcesCounter'

const Header: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className={`backdrop-blur-3xl bg-white/5 sticky top-0 z-40 transition-all duration-300 ${isScrolled ? 'py-2' : 'py-3'}`}>
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className={`font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 tracking-wider transition-all duration-300 ${
              isScrolled ? 'text-2xl' : 'text-4xl'
            }`}>
              FanAroundYou
            </h1>
            
            {/* Contador de eventos por fuente en tiempo real */}
            <SourcesCounter />
          </div>
          
          <div className="flex items-center space-x-4">
            <button className="p-2 text-white/70 hover:text-white transition-colors">
              <MapPinIcon className="h-6 w-6" />
            </button>
            <button className="p-2 text-white/70 hover:text-white transition-colors">
              <MagnifyingGlassIcon className="h-6 w-6" />
            </button>
            
            <button className="bg-white/10 hover:bg-white/20 text-white font-semibold py-2 px-6 border border-white/30 rounded-full shadow-md hover:shadow-lg transition-all duration-200 flex items-center space-x-2">
              <span>Registrarse</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header