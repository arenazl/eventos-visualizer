import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  email: string
  name: string
  avatar?: string
  givenName?: string
  familyName?: string
  emailVerified?: boolean
  profile?: UserProfile
}

interface UserProfile {
  city: string
  country: string
  age?: number
  interests: string[]
  eventPreferences: {
    categories: string[]
    priceRange: 'free' | 'cheap' | 'moderate' | 'premium' | 'any'
    distance: number
    notifications: boolean
  }
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (userData: User) => void
  logout: () => void
  updateProfile: (profile: UserProfile) => void
  googleToken: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  console.log('🔧 DEBUG: AuthProvider initializing');
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [googleToken, setGoogleToken] = useState<string | null>(null)

  // Cargar usuario del localStorage al inicializar
  useEffect(() => {
    const loadUserFromStorage = async () => {
      try {
        const storedUser = localStorage.getItem('user')
        const storedToken = localStorage.getItem('googleToken')
        const storedProfile = localStorage.getItem('userProfile')
        
        if (storedUser && storedToken) {
          const userData = JSON.parse(storedUser)
          const profileData = storedProfile ? JSON.parse(storedProfile) : null
          
          setUser({
            ...userData,
            profile: profileData
          })
          setGoogleToken(storedToken)
          
          // Opcional: Validar token con backend
          // await validateTokenWithBackend(storedToken)
        }
      } catch (error) {
        console.error('Error loading user from storage:', error)
        // Limpiar storage si hay error
        localStorage.removeItem('user')
        localStorage.removeItem('googleToken')
        localStorage.removeItem('userProfile')
      } finally {
        setIsLoading(false)
      }
    }

    loadUserFromStorage()
  }, [])

  const login = async (userData: User) => {
    try {
      console.log('🔧 DEBUG: Login function called', userData);
      setUser(userData)
      
      // Guardar en localStorage
      localStorage.setItem('user', JSON.stringify(userData))
      
      // Opcional: Enviar al backend para registro/actualización
      // await saveUserToBackend(userData)
      
      console.log('User logged in:', userData.name)
    } catch (error) {
      console.error('Error during login:', error)
    }
  }

  const logout = () => {
    setUser(null)
    setGoogleToken(null)
    
    // Limpiar localStorage
    localStorage.removeItem('user')
    localStorage.removeItem('googleToken')
    localStorage.removeItem('userProfile')
    
    console.log('User logged out')
  }

  const updateProfile = (profile: UserProfile) => {
    if (user) {
      const updatedUser = {
        ...user,
        profile
      }
      
      setUser(updatedUser)
      
      // Guardar profile en localStorage
      localStorage.setItem('userProfile', JSON.stringify(profile))
      localStorage.setItem('user', JSON.stringify(updatedUser))
      
      console.log('Profile updated for:', user.name)
      
      // Opcional: Enviar al backend
      // await saveProfileToBackend(user.id, profile)
    }
  }

  // Opcional: Función para validar token con backend
  const validateTokenWithBackend = async (token: string) => {
    try {
      // const response = await fetch('/api/auth/validate', {
      //   method: 'POST',
      //   headers: { 
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${token}`
      //   }
      // })
      // 
      // if (!response.ok) {
      //   throw new Error('Token validation failed')
      // }
      
      console.log('Token validated')
    } catch (error) {
      console.error('Token validation failed:', error)
      logout()
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updateProfile,
    googleToken
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext