/**
 * Botón de login con Google
 */
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

// Función para obtener las iniciales del nombre (tipo Gmail)
const getInitials = (name: string): string => {
  if (!name) return '?';

  const words = name.trim().split(' ');
  if (words.length === 1) {
    return words[0].charAt(0).toUpperCase();
  }

  // Tomar la primera letra del primer nombre y la primera del apellido
  return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase();
};

// Colores para avatares (tipo Gmail)
const AVATAR_COLORS = [
  'bg-gradient-to-br from-red-500 to-red-600',
  'bg-gradient-to-br from-blue-500 to-blue-600',
  'bg-gradient-to-br from-green-500 to-green-600',
  'bg-gradient-to-br from-yellow-500 to-yellow-600',
  'bg-gradient-to-br from-purple-500 to-purple-600',
  'bg-gradient-to-br from-pink-500 to-pink-600',
  'bg-gradient-to-br from-indigo-500 to-indigo-600',
  'bg-gradient-to-br from-orange-500 to-orange-600',
];

// Seleccionar color basado en el email (consistente)
const getAvatarColor = (email?: string): string => {
  if (!email) return AVATAR_COLORS[0];

  const hash = email.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc);
  }, 0);

  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
};

export const GoogleLoginButton: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  const handleGoogleLogin = () => {
    // Redirigir a la URL de login de Google en el backend
    window.location.href = `${API_BASE_URL}/auth/google/login`;
  };

  if (isAuthenticated && user) {
    const initials = getInitials(user.name || user.email || 'User');
    const avatarColor = getAvatarColor(user.email);
    const displayName = user.name ? user.name.split(' ')[0] : user.email?.split('@')[0] || 'Usuario';

    return (
      <div className="relative">
        {/* Avatar clickeable - visible en mobile y desktop */}
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="flex items-center gap-2 focus:outline-none active:scale-95 transition-transform"
          title={user.name || user.email || 'Usuario'}
        >
          {/* Avatar con iniciales o imagen */}
          {user.avatar ? (
            <img
              src={user.avatar}
              alt={user.name || 'Usuario'}
              className="w-8 h-8 md:w-9 md:h-9 rounded-full border-2 border-white/30 hover:border-white/50 transition-colors"
            />
          ) : (
            <div className={`w-8 h-8 md:w-9 md:h-9 rounded-full ${avatarColor} flex items-center justify-center text-white font-semibold text-sm md:text-base border-2 border-white/30 hover:border-white/50 transition-colors shadow-lg`}>
              {initials}
            </div>
          )}

          {/* Nombre - solo visible en desktop */}
          <span className="hidden md:inline-block text-sm font-medium text-white">
            {displayName}
          </span>
        </button>

        {/* Dropdown menu */}
        {showMenu && (
          <>
            {/* Overlay para cerrar el menu */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowMenu(false)}
            />

            {/* Menu */}
            <div className="absolute right-0 mt-2 w-48 bg-gray-900/95 backdrop-blur-xl border border-white/20 rounded-xl shadow-2xl overflow-hidden z-20 animate-in fade-in slide-in-from-top-2 duration-200">
              {/* Info del usuario */}
              <div className="px-4 py-3 border-b border-white/10">
                <p className="text-sm font-semibold text-white truncate">
                  {user.name || 'Usuario'}
                </p>
                <p className="text-xs text-white/60 truncate">
                  {user.email}
                </p>
              </div>

              {/* Opciones */}
              <button
                onClick={() => {
                  logout();
                  setShowMenu(false);
                }}
                className="w-full px-4 py-2.5 text-left text-sm text-white/80 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Cerrar sesión
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={handleGoogleLogin}
      className="flex items-center gap-1.5 md:gap-2 bg-white/10 hover:bg-white/20 text-white font-semibold py-1.5 md:py-2 px-2.5 md:px-6 border border-white/30 rounded-full shadow-md hover:shadow-lg transition-all duration-200 active:scale-95"
    >
      <svg className="w-4 h-4" viewBox="0 0 24 24">
        <path
          fill="#4285F4"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="#34A853"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="#FBBC05"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="#EA4335"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
      <span className="hidden sm:inline text-xs md:text-sm">Registrarse</span>
      <span className="sm:hidden text-xs">Login</span>
    </button>
  );
};

export default GoogleLoginButton;
