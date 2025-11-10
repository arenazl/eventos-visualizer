# Setup de Autenticación con Google OAuth2

Este documento explica cómo configurar e implementar la autenticación con Google en la aplicación Eventos Visualizer.

## 📋 Archivos Creados

### Backend
- `backend/setup_google_auth.py` - Script de instalación y configuración
- `backend/api/auth.py` - Endpoints de autenticación OAuth2
- `backend/middleware/jwt.py` - Middleware JWT
- `backend/utils/auth_utils.py` - Utilidades de autenticación
- `backend/scripts/init_db.py` - Inicialización de base de datos

### Frontend
- `frontend/src/contexts/AuthContext.tsx` - Context de autenticación
- `frontend/src/components/auth/GoogleLoginButton.tsx` - Botón de login
- `frontend/src/pages/AuthCallback.tsx` - Página de callback OAuth
- `frontend/src/pages/AuthError.tsx` - Página de error de autenticación

## 🚀 Instalación

### Paso 1: Ejecutar el script de setup

```bash
cd backend
python setup_google_auth.py
```

Este script:
- Instala las dependencias necesarias (authlib, python-jose, etc.)
- Actualiza el archivo `.env` con las variables necesarias
- Crea las tablas de base de datos

### Paso 2: Configurar Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)

2. Crea un nuevo proyecto o selecciona uno existente

3. Habilita las APIs necesarias:
   - Google+ API
   - Google Calendar API (opcional)

4. Crea credenciales OAuth 2.0:
   - Ve a "APIs & Services" > "Credentials"
   - Click en "Create Credentials" > "OAuth client ID"
   - Tipo: "Web application"
   - Nombre: "Eventos Visualizer"

5. Configura las URIs autorizadas:

   **JavaScript origins:**
   ```
   http://localhost:8001
   http://172.29.228.80:8001
   http://localhost:5174
   http://172.29.228.80:5174
   ```

   **Redirect URIs:**
   ```
   http://localhost:8001/auth/google/callback
   http://172.29.228.80:8001/auth/google/callback
   ```

6. Copia las credenciales y actualiza el archivo `.env`:

```env
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# Genera una clave secreta para JWT
JWT_SECRET_KEY=tu-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Paso 3: Generar JWT Secret Key

En Python:
```python
import secrets
print(secrets.token_urlsafe(32))
```

Copia el resultado y actualiza `JWT_SECRET_KEY` en `.env`

### Paso 4: Inicializar la base de datos

```bash
cd backend
python scripts/init_db.py
```

## 🔧 Integración en el Backend

### Agregar las rutas de autenticación en `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from middleware.jwt import JWTAuthMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://172.29.228.80:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware JWT (opcional, para proteger rutas automáticamente)
# app.add_middleware(JWTAuthMiddleware)

# Incluir rutas de autenticación
app.include_router(auth_router)
```

### Proteger rutas específicas

```python
from fastapi import Depends, APIRouter
from utils.auth_utils import get_current_user
from models.users import User

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Ruta protegida - requiere autenticación"""
    return {
        "email": current_user.email,
        "name": current_user.name
    }

@router.get("/public")
async def public_route():
    """Ruta pública - no requiere autenticación"""
    return {"message": "Esta ruta es pública"}
```

### Rutas opcionales (con o sin autenticación)

```python
from utils.auth_utils import get_current_user_optional

@router.get("/events")
async def get_events(current_user: User = Depends(get_current_user_optional)):
    """
    Ruta que funciona con o sin autenticación
    Si el usuario está autenticado, puede personalizar la respuesta
    """
    if current_user:
        # Usuario autenticado - mostrar favoritos
        return {"events": [...], "user_favorites": [...]}
    else:
        # Usuario anónimo - mostrar solo eventos
        return {"events": [...]}
```

## 🎨 Integración en el Frontend

### Paso 1: Agregar el AuthProvider en `main.tsx` o `App.tsx`

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import HomePage from './pages/HomePage';
import AuthCallback from './pages/AuthCallback';
import AuthError from './pages/AuthError';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/auth/error" element={<AuthError />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

### Paso 2: Usar el botón de login en tu componente

```tsx
import React from 'react';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';
import { useAuth } from '../contexts/AuthContext';

export const HomePage: React.FC = () => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  return (
    <div>
      <nav className="p-4">
        <GoogleLoginButton />
      </nav>

      {isAuthenticated && user && (
        <div>
          <h1>Bienvenido, {user.name}!</h1>
          <p>Email: {user.email}</p>
        </div>
      )}
    </div>
  );
};
```

### Paso 3: Hacer requests autenticados

```tsx
import { useAuth } from '../contexts/AuthContext';

export const EventsPage: React.FC = () => {
  const { token } = useAuth();

  const saveEvent = async (eventId: string) => {
    const response = await fetch(`${API_URL}/api/user/events/${eventId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Error guardando evento');
    }

    return response.json();
  };

  return (
    <div>
      {/* Tu componente aquí */}
    </div>
  );
};
```

## 📊 Endpoints de API Disponibles

### Autenticación
- `GET /auth/google/login` - Inicia el flujo de OAuth con Google
- `GET /auth/google/callback` - Callback de Google (manejado automáticamente)
- `GET /auth/me` - Obtiene información del usuario autenticado
- `POST /auth/logout` - Cierra sesión
- `PUT /auth/profile` - Actualiza el perfil del usuario
- `DELETE /auth/account` - Elimina la cuenta del usuario

### Ejemplos de uso

```bash
# Obtener información del usuario
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8001/auth/me

# Actualizar perfil
curl -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Nuevo Nombre","city":"Buenos Aires"}' \
  http://localhost:8001/auth/profile
```

## 🔒 Seguridad

### Mejores prácticas implementadas:

1. **JWT Tokens**: Tokens seguros con expiración de 24 horas
2. **HTTPS recomendado**: En producción, usar siempre HTTPS
3. **Tokens en localStorage**: Para persistencia del login
4. **Refresh tokens**: Google provee refresh tokens para renovar acceso
5. **Validación de tokens**: Middleware valida cada request protegido

### Variables de entorno sensibles:

```env
# NUNCA commitear estas variables al repositorio
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET_KEY=...
```

Asegúrate de que `.env` esté en `.gitignore`:

```gitignore
# .gitignore
.env
.env.local
.env.production
```

## 🧪 Testing

### Test manual del flujo:

1. Iniciar el backend:
   ```bash
   cd backend
   python main.py
   ```

2. Iniciar el frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Abrir el navegador en `http://localhost:5174`

4. Click en "Continuar con Google"

5. Completar el login con Google

6. Deberías ser redirigido de vuelta con tu sesión iniciada

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"
- Verifica que las URIs en Google Cloud Console coincidan exactamente
- Incluye http:// y el puerto exacto

### Error: "Token inválido"
- Verifica que JWT_SECRET_KEY esté configurado
- Revisa que el token no haya expirado (24 horas por defecto)

### Error: "No se puede obtener información del usuario"
- Verifica que Google+ API esté habilitada
- Revisa los scopes solicitados en `api/auth.py`

### Frontend no redirige después del login
- Verifica las rutas en React Router
- Revisa que AuthCallback esté configurado correctamente
- Verifica CORS en el backend

## 📚 Referencias

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI OAuth2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Authlib Documentation](https://docs.authlib.org/en/latest/)
- [Python-JOSE Documentation](https://python-jose.readthedocs.io/)

## ✅ Checklist Final

- [ ] Script de setup ejecutado
- [ ] Google Cloud Console configurado
- [ ] Client ID y Secret en `.env`
- [ ] JWT Secret Key generado
- [ ] Base de datos inicializada
- [ ] Backend con rutas de auth incluidas
- [ ] Frontend con AuthProvider configurado
- [ ] Rutas de callback agregadas a React Router
- [ ] CORS configurado correctamente
- [ ] Test manual completado exitosamente

---

¡Listo! Ahora tienes autenticación con Google completamente funcional. 🎉
