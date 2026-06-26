import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'

// 🔴 GLOBAL ERROR HANDLER - Captura errores no manejados en móvil
const API_URL = import.meta.env.VITE_API_URL || ''

// Helper para enviar logs remotos
const sendRemoteLog = async (type: string, data: any) => {
  try {
    await fetch(`${API_URL}/api/mobile-log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type,
        data,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    })
  } catch (e) {
    // Silently fail - don't want logging to break the app
  }
}

// Capturar errores globales
window.onerror = (message, source, lineno, colno, error) => {
  console.error('🔴 [GLOBAL ERROR]:', message, source, lineno, colno)
  sendRemoteLog('global_error', {
    message: String(message),
    source,
    lineno,
    colno,
    stack: error?.stack
  })
  return false
}

// Capturar promesas rechazadas no manejadas
window.onunhandledrejection = (event) => {
  console.error('🔴 [UNHANDLED REJECTION]:', event.reason)
  sendRemoteLog('unhandled_rejection', {
    reason: String(event.reason),
    stack: event.reason?.stack
  })
}

// Exportar para uso en componentes
;(window as any).sendRemoteLog = sendRemoteLog

ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)