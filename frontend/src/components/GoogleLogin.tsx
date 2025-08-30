import React from 'react'
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google'

// IMPORTANTE: Necesitas crear tu propio Client ID en Google Console
// https://console.cloud.google.com/apis/credentials
const GOOGLE_CLIENT_ID = '1043816040289-1j20cta02p73scou7dqiufd92n3a8j1t.apps.googleusercontent.com' // Demo ID

interface GoogleAuthProps {
  onSuccess: (userData: any) => void
  onError?: () => void
}

const GoogleAuth: React.FC<GoogleAuthProps> = ({ onSuccess, onError }) => {
  
  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      // Decodificar el JWT token de Google
      const base64Url = credentialResponse.credential.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      
      const userData = JSON.parse(jsonPayload)
      
      // Extraer datos del usuario
      const user = {
        id: userData.sub,
        email: userData.email,
        name: userData.name,
        avatar: userData.picture,
        givenName: userData.given_name,
        familyName: userData.family_name,
        emailVerified: userData.email_verified
      }
      
      console.log('Google login successful:', user)
      
      // Guardar en localStorage para persistencia
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('googleToken', credentialResponse.credential)
      
      // Llamar callback de éxito
      onSuccess(user)
      
      // Aquí también podrías enviar el token al backend para validación adicional
      // await saveUserToBackend(user)
      
    } catch (error) {
      console.error('Error processing Google login:', error)
      if (onError) onError()
    }
  }
  
  const handleGoogleError = () => {
    console.error('Google login failed')
    if (onError) onError()
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="w-full">
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={handleGoogleError}
          useOneTap
          theme="filled_black"
          size="large"
          shape="pill"
          text="signin_with"
          logo_alignment="left"
          width="280"
        />
      </div>
    </GoogleOAuthProvider>
  )
}

export default GoogleAuth