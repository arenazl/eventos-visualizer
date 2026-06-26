// URL de la API - same-origin por defecto (proxy /api de Netlify -> backend).
// En dev, Vite proxea /api/* y /auth/* al backend local (ver vite.config).
// Eliminar barra final si existe para evitar doble barra en las rutas.
const rawApiUrl = import.meta.env.VITE_API_URL || ''
export const API_BASE_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl