import React, { useState } from 'react'
// import GoogleAuth from './GoogleLogin'
// import UserProfileForm from './UserProfileForm'
import { useAuth } from '../contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  mode?: 'login' | 'profile'
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, mode = 'login' }) => {
  console.log('🔧 DEBUG: AuthModal render', { isOpen, mode });
  
  if (!isOpen) return null

  // VERSIÓN ULTRA SIMPLE PARA DEBUG
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <div className="relative z-10 bg-white p-8 rounded-lg max-w-md mx-4">
        <h2 className="text-2xl font-bold mb-4">🔧 Debug Mode</h2>
        <p className="mb-4">Modal funcionando en modo debug</p>
        <button
          onClick={onClose}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
  
}


export default AuthModal