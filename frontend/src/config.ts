/**
 * Configuration for different environments
 */

// Detect environment
const isDevelopment = import.meta.env.MODE === 'development'
const isProduction = import.meta.env.MODE === 'production'

// API Base URLs
const API_URLS = {
  development: 'http://localhost:8001',
  production: import.meta.env.VITE_API_URL || 'https://funaroundyou-f21e91cae36c.herokuapp.com'
}

export const config = {
  // API Configuration
  API_BASE_URL: isDevelopment ? API_URLS.development : API_URLS.production,
  
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