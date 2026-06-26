/**
 * Configuration for different environments
 */

// Detect environment
const isDevelopment = import.meta.env.MODE === 'development'
const isProduction = import.meta.env.MODE === 'production'

// API Base URLs - same-origin por defecto (proxy /api de Netlify -> backend).
// Vacio en prod => rutas relativas (/api/...). En dev, Vite proxea al backend local.
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const config = {
  // API Configuration
  API_BASE_URL,
  
  // Environment flags
  isDevelopment,
  isProduction,
  
  // Feature flags
  ENABLE_DEBUG_LOGS: isDevelopment,
  ENABLE_AI_FEATURES: true,
  ENABLE_PUSH_NOTIFICATIONS: isProduction,
  
  // App Configuration
  APP_NAME: 'Eventos Visualizer',
  APP_VERSION: '1.0.0',
  
  // Timeouts
  API_TIMEOUT: 30000, // 30 seconds
  WEBSOCKET_TIMEOUT: 5000, // 5 seconds
  
  // Pagination
  DEFAULT_PAGE_SIZE: 30,
  MAX_PAGE_SIZE: 100,
}

export default config