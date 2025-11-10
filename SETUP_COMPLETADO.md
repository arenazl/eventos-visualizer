# ✅ Setup de Autenticación Google - COMPLETADO

## 📊 Estado Actual

### Base de Datos MySQL (Aiven Cloud) ✅
**Conexión:** mysql-aiven-arenazl.e.aivencloud.com:23108

**Tablas creadas:**
- `users` - Usuarios con Google OAuth
- `user_events` - Eventos guardados por usuarios
- `user_preferences` - Preferencias de IA y personalización
- `user_interactions` - Historial de interacciones
- `notifications` - Sistema de notificaciones
- `preference_updates` - Historial de cambios
- `categories` - Categorías de eventos

### Archivos Backend Creados ✅
```
backend/
├── api/
│   └── auth.py                    # Endpoints OAuth2 y perfil
├── middleware/
│   └── jwt.py                     # Middleware JWT
├── utils/
│   └── auth_utils.py              # Utilidades JWT
├── scripts/
│   ├── init_db.py                 # Inicialización DB
│   └── fix_models_mysql.py        # Corrección MySQL
└── setup_google_auth.py           # Script de instalación
```

### Archivos Frontend Creados ✅
```
frontend/src/
├── contexts/
│   └── AuthContext.tsx            # Context de autenticación
├── components/auth/
│   └── GoogleLoginButton.tsx     # Botón de login
└── pages/
    ├── AuthCallback.tsx           # Callback OAuth
    └── AuthError.tsx              # Página de error
```

### Dependencias Instaladas ✅
- `authlib` - OAuth2 client
- `python-jose[cryptography]` - JWT tokens
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data
- `httpx` - HTTP client
- `pydantic-settings` - Settings management

## 🚀 Próximos Pasos

### 1. Configurar Google Cloud Console

1. Ir a https://console.cloud.google.com/
2. Crear proyecto "Eventos Visualizer"
3. Habilitar APIs:
   - Google+ API
   - Google Calendar API (opcional)

4. Crear credenciales OAuth 2.0:
   ```
   Tipo: Web application
   Nombre: Eventos Visualizer

   JavaScript origins:
   - http://localhost:8001
   - http://172.29.228.80:8001
   - http://localhost:5174
   - http://172.29.228.80:5174

   Redirect URIs:
   - http://localhost:8001/auth/google/callback
   - http://172.29.228.80:8001/auth/google/callback
   ```

### 2. Actualizar Variables de Entorno

Editar `backend/.env` con las credenciales de Google:

```env
# Google OAuth (REEMPLAZAR CON TUS CREDENCIALES)
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# JWT (GENERAR UNA NUEVA)
JWT_SECRET_KEY=<generar-con-secrets.token_urlsafe(32)>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Para generar JWT_SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Integrar en Backend

Editar `backend/main.py`:

```python
from api.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

# Agregar CORS
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

# Incluir rutas de auth
app.include_router(auth_router)
```

### 4. Integrar en Frontend

Editar `frontend/src/main.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AuthCallback from './pages/AuthCallback';
import AuthError from './pages/AuthError';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/auth/error" element={<AuthError />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

Usar el botón de login:

```tsx
import { GoogleLoginButton } from './components/auth/GoogleLoginButton';
import { useAuth } from './contexts/AuthContext';

function App() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div>
      <nav>
        <GoogleLoginButton />
      </nav>

      {isAuthenticated && (
        <div>Bienvenido, {user?.name}!</div>
      )}
    </div>
  );
}
```

## 🔒 Endpoints Disponibles

### Autenticación
- `GET /auth/google/login` - Iniciar login con Google
- `GET /auth/google/callback` - Callback OAuth (automático)
- `GET /auth/me` - Info del usuario actual (requiere auth)
- `POST /auth/logout` - Cerrar sesión
- `PUT /auth/profile` - Actualizar perfil
- `DELETE /auth/account` - Eliminar cuenta

### Ejemplo con curl:
```bash
# Obtener info del usuario
curl -H "Authorization: Bearer <tu-token>" \
  http://localhost:8001/auth/me

# Actualizar perfil
curl -X PUT \
  -H "Authorization: Bearer <tu-token>" \
  -H "Content-Type: application/json" \
  -d '{"city":"Buenos Aires","radius_km":25}' \
  http://localhost:8001/auth/profile
```

## 🧪 Testing

```bash
# 1. Iniciar backend
cd backend
python main.py

# 2. Iniciar frontend
cd frontend
npm run dev

# 3. Abrir navegador
http://localhost:5174

# 4. Click en "Continuar con Google"
```

## 📚 Documentación Adicional

- Ver `GOOGLE_AUTH_SETUP.md` para guía completa
- Ver `backend/api/auth.py` para endpoints disponibles
- Ver `frontend/src/contexts/AuthContext.tsx` para uso en React

## ✅ Checklist

- [x] Base de datos MySQL inicializada
- [x] Tablas de usuarios creadas
- [x] Scripts de backend implementados
- [x] Componentes de frontend creados
- [x] Dependencias instaladas
- [ ] Google Cloud Console configurado
- [ ] Credenciales en .env
- [ ] JWT_SECRET_KEY generado
- [ ] Rutas integradas en main.py
- [ ] AuthProvider en frontend
- [ ] Testing completo

---

**Fecha de setup:** 2025-11-09
**Versión:** 1.0.0
**Base de datos:** MySQL (Aiven Cloud)
