/**
 * Página de callback para autenticación con Google
 * Maneja la redirección después del login con Google
 */
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      const error = searchParams.get('error');

      if (error) {
        console.error('Error en autenticación:', error);
        alert('Error al iniciar sesión con Google. Por favor intenta de nuevo.');
        navigate('/');
        return;
      }

      if (token) {
        try {
          console.log('🔧 DEBUG: Token recibido:', token);

          // Guardar el token JWT en localStorage
          localStorage.setItem('googleToken', token);

          // Obtener datos del usuario desde el backend
          const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          if (!response.ok) {
            throw new Error('Error al obtener datos del usuario');
          }

          const userData = await response.json();
          console.log('🔧 DEBUG: Datos del usuario obtenidos:', userData);

          // Transformar datos del backend al formato del AuthContext
          const user = {
            id: userData.id,
            email: userData.email,
            name: userData.name,
            avatar: userData.avatar_url,
            givenName: userData.name ? userData.name.split(' ')[0] : undefined,
            familyName: userData.name ? userData.name.split(' ').slice(1).join(' ') : undefined,
            emailVerified: true
          };

          // Llamar a login con el objeto de usuario
          await login(user);

          console.log('✅ Login exitoso:', user.name);
          navigate('/'); // Redirigir a home después del login exitoso
        } catch (error) {
          console.error('❌ Error en autenticación:', error);
          alert('Error al procesar la autenticación. Por favor intenta de nuevo.');
          navigate('/');
        }
      } else {
        navigate('/');
      }
    };

    handleCallback();
  }, [searchParams, login, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid border-blue-500 border-r-transparent"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">
          Iniciando sesión...
        </p>
      </div>
    </div>
  );
};

export default AuthCallback;
