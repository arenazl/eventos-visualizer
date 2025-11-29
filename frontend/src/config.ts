/**
 * Configuration for different environments
 */

// Detect environment
const isDevelopment = import.meta.env.MODE === 'development'
const isProduction = import.meta.env.MODE === 'production'

// API Base URLs - SIEMPRE usar VITE_API_URL si está definido
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (isDevelopment ? 'http://localhost:8001' : 'https://funaroundyou-f21e91cae36c.herokuapp.com')

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