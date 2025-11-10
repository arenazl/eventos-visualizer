/**
 * Página de prueba para autenticación con Google
 * Muestra el estado de autenticación y permite hacer login/logout
 */
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import GoogleLoginButton from '../components/auth/GoogleLoginButton';

export const TestAuthPage: React.FC = () => {
  const { isAuthenticated, user, isLoading, token } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid border-blue-500 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Cargando autenticación...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            🔐 Test de Autenticación
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Prueba el sistema de login con Google OAuth2
          </p>
        </div>

        {/* Card Principal */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Estado de Sesión
            </h2>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isAuthenticated ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {isAuthenticated ? 'Conectado' : 'Desconectado'}
              </span>
            </div>
          </div>

          {/* Botón de Login/Logout */}
          <div className="mb-8 p-6 bg-gray-50 dark:bg-gray-700 rounded-xl">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Control de Sesión
            </h3>
            <GoogleLoginButton />
          </div>

          {/* Información del Usuario */}
          {isAuthenticated && user ? (
            <div className="space-y-6">
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Información del Usuario
                </h3>

                <div className="flex items-center gap-4 mb-6">
                  {user.avatar_url && (
                    <img
                      src={user.avatar_url}
                      alt={user.name}
                      className="w-20 h-20 rounded-full border-4 border-blue-500"
                    />
                  )}
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {user.name}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">
                      {user.email}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      ID de Usuario
                    </p>
                    <p className="font-mono text-sm text-gray-900 dark:text-white break-all">
                      {user.id}
                    </p>
                  </div>

                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      Último Login
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {user.last_login ? new Date(user.last_login).toLocaleString('es-AR') : 'N/A'}
                    </p>
                  </div>

                  {user.location?.city && (
                    <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        Ubicación
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {user.location.city}, {user.location.country}
                      </p>
                    </div>
                  )}

                  {user.preferences?.favorite_categories && user.preferences.favorite_categories.length > 0 && (
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        Categorías Favoritas
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {user.preferences.favorite_categories.join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Token Info (solo para desarrollo) */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <details className="cursor-pointer">
                  <summary className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    🔑 JWT Token (desarrollo)
                  </summary>
                  <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-900 rounded-lg">
                    <p className="font-mono text-xs text-gray-600 dark:text-gray-400 break-all">
                      {token}
                    </p>
                  </div>
                </details>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔓</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No has iniciado sesión
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Haz click en "Continuar con Google" arriba para iniciar sesión
              </p>
            </div>
          )}
        </div>

        {/* Instrucciones */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            ℹ️ Cómo funciona
          </h3>
          <ol className="list-decimal list-inside space-y-2 text-blue-800 dark:text-blue-200">
            <li>Click en "Continuar con Google"</li>
            <li>Serás redirigido a Google para autenticarte</li>
            <li>Autoriza la aplicación "Eventos Visualizer"</li>
            <li>Serás redirigido de vuelta con tu sesión iniciada</li>
            <li>Tu información se guardará en la base de datos MySQL</li>
          </ol>
        </div>

        {/* Botón para volver al home */}
        <div className="text-center mt-8">
          <a
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
          >
            ← Volver al inicio
          </a>
        </div>
      </div>
    </div>
  );
};

export default TestAuthPage;
