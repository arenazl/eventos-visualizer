// URL de la API - Se configura automáticamente por ambiente
// Eliminar barra final si existe para evitar doble barra en las rutas
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001'
export const API_BASE_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl