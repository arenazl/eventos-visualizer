import React, { useState, useEffect } from 'react'
import { User, Settings, Heart, Calendar, LogOut, LogIn, ChevronDown } from 'lucide-react'
import GoogleAuth from './GoogleLogin'

interface UserMenuProps {
  user?: {
    id: string
    name: string
    email: string
    avatar?: string
  } | null
  onLogin?: (userData?: any) => void
  onLogout?: () => void
}

const UserMenu: React.FC<UserMenuProps> = ({ user, onLogin, onLogout }) => {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showGoogleLogin, setShowGoogleLogin] = useState(false)

  const handleLogin = () => {
    setShowDropdown(false)
    setShowGoogleLogin(true)
  }

  const handleLogout = () => {
    setShowDropdown(false)
    localStorage.removeItem('user')
    localStorage.removeItem('googleToken')
    if (onLogout) onLogout()
  }

  const handleGoogleSuccess = (userData: any) => {
    setShowGoogleLogin(false)
    if (onLogin) onLogin(userData)
  }

  if (!user) {
    // Usuario no logueado
    return (
      <div className="relative">
        {showGoogleLogin ? (
          <div className="absolute right-0 top-0 z-50">
            <div className="bg-black/90 backdrop-blur-xl border border-white/20 rounded-lg p-4 shadow-xl">
              <GoogleAuth 
                onSuccess={handleGoogleSuccess}
                onError={() => setShowGoogleLogin(false)}
              />
              <button
                onClick={() => setShowGoogleLogin(false)}
                className="mt-3 text-white/60 hover:text-white text-sm w-full text-center transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={handleLogin}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white px-3 py-2 rounded-lg font-medium transition-all text-sm"
          >
            <LogIn className="w-4 h-4" />
            <span>Iniciar sesión</span>
          </button>
        )}
      </div>
    )
  }

  // Usuario logueado
  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white px-3 py-2 rounded-lg transition-all duration-200 group"
      >
        {user.avatar ? (
          <img 
            src={user.avatar} 
            alt={user.name}
            className="w-7 h-7 rounded-full border border-white/30"
          />
        ) : (
          <div className="w-7 h-7 bg-white/20 rounded-full flex items-center justify-center">
            <span className="text-white font-medium text-sm">
              {user.name.charAt(0).toUpperCase()}
            </span>
          </div>
        )}
        <div className="text-left hidden sm:block">
          <p className="text-sm font-medium text-white/90 group-hover:text-white transition-colors">{user.name}</p>
        </div>
        <ChevronDown className="w-3 h-3 text-white/50 group-hover:text-white/80 transition-colors" />
      </button>

      {/* Dropdown menu */}
      {showDropdown && (
        <div className="absolute top-full mt-1 right-0 w-64 bg-black/90 backdrop-blur-xl border border-white/20 rounded-lg shadow-xl z-50 overflow-hidden">
          {/* User info header */}
          <div className="p-3 border-b border-white/10">
            <div className="flex items-center gap-3">
              {user.avatar ? (
                <img 
                  src={user.avatar} 
                  alt={user.name}
                  className="w-10 h-10 rounded-full border border-white/30"
                />
              ) : (
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium">
                    {user.name.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <p className="text-white font-medium text-sm">{user.name}</p>
                <p className="text-white/60 text-xs">{user.email}</p>
              </div>
            </div>
          </div>

          {/* Menu options */}
          <div className="p-1">
            <button
              onClick={() => setShowDropdown(false)}
              className="w-full text-left text-white/80 hover:text-white py-2 px-3 rounded-md hover:bg-white/10 transition-all flex items-center gap-3 text-sm"
            >
              <User className="w-4 h-4" />
              <span>Mi Perfil</span>
            </button>
            
            <button
              onClick={() => setShowDropdown(false)}
              className="w-full text-left text-white/80 hover:text-white py-2 px-3 rounded-md hover:bg-white/10 transition-all flex items-center gap-3 text-sm"
            >
              <Heart className="w-4 h-4" />
              <span>Mis Favoritos</span>
            </button>
            
            <button
              onClick={() => setShowDropdown(false)}
              className="w-full text-left text-white/80 hover:text-white py-2 px-3 rounded-md hover:bg-white/10 transition-all flex items-center gap-3 text-sm"
            >
              <Calendar className="w-4 h-4" />
              <span>Mis Eventos</span>
            </button>
            
            <button
              onClick={() => setShowDropdown(false)}
              className="w-full text-left text-white/80 hover:text-white py-2 px-3 rounded-md hover:bg-white/10 transition-all flex items-center gap-3 text-sm"
            >
              <Settings className="w-4 h-4" />
              <span>Configuración</span>
            </button>
          </div>

          {/* Logout */}
          <div className="p-1 border-t border-white/10">
            <button
              onClick={handleLogout}
              className="w-full text-left text-white/60 hover:text-red-400 py-2 px-3 rounded-md hover:bg-red-500/10 transition-all flex items-center gap-3 text-sm"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar sesión</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserMenu