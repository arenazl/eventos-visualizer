# 🎉 ¡TODO CONFIGURADO! - LISTO PARA PROBAR

## ✅ Configuración Completada

**Google OAuth Credentials:**
- ✅ Client ID: Configurado en .env
- ✅ Client Secret: Configurado en .env
- ✅ JWT Secret: Configurado
- ✅ Base de datos MySQL: Conectada

**Backend:**
- ✅ Endpoints de auth integrados
- ✅ Middleware JWT configurado
- ✅ Tablas de usuarios creadas

**Frontend:**
- ✅ AuthProvider configurado
- ✅ Rutas de callback agregadas
- ✅ Página de prueba lista

---

## 🚀 CÓMO PROBAR (3 pasos)

### PASO 1: Iniciar Backend

Abre una terminal en el directorio del proyecto:

```bash
cd backend
python main.py
```

**Deberías ver:**
```
🚀 Starting Eventos Visualizer Backend...
🔐 Autenticación Google OAuth2 habilitada
✅ Database pool created successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**¡NO CIERRES ESTA TERMINAL!** Déjala corriendo.

---

### PASO 2: Iniciar Frontend

Abre **OTRA TERMINAL** (nueva):

```bash
cd frontend
npm run dev
```

**Deberías ver:**
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5174/
  ➜  Network: use --host to expose
```

**¡NO CIERRES ESTA TERMINAL!** Déjala corriendo también.

---

### PASO 3: Abrir Navegador y Probar

1. **Abre tu navegador** (Chrome, Edge, Firefox)

2. **Ve a:**
   ```
   http://localhost:5174/auth/test
   ```

3. **Deberías ver** una página bonita con:
   - Título: "🔐 Test de Autenticación"
   - Un botón: "Continuar con Google"
   - Estado: "Desconectado" (con un punto rojo)

4. **Haz click en "Continuar con Google"**

5. **Te redirigirá a Google:**
   - Selecciona tu cuenta Google
   - Click en "Continuar"
   - Acepta los permisos (si te pide)

6. **Serás redirigido de vuelta** a tu app

7. **¡ÉXITO!** Deberías ver:
   - Tu nombre
   - Tu email
   - Tu foto de perfil
   - Estado: "Conectado" (punto verde)
   - Tu información de usuario

---

## 🎯 QUÉ ESPERAR

### En la página de prueba verás:

```
┌─────────────────────────────────────────┐
│ 🔐 Test de Autenticación                │
│                                          │
│ Estado de Sesión           ● Conectado  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Control de Sesión                  │  │
│ │                                    │  │
│ │ 👤 [Foto]  Tu Nombre               │  │
│ │            tu-email@gmail.com      │  │
│ │                                    │  │
│ │ [Cerrar sesión]                    │  │
│ └────────────────────────────────────┘  │
│                                          │
│ Información del Usuario                 │
│ ┌────────────────────────────────────┐  │
│ │ ID de Usuario: abc-123-def-456     │  │
│ │ Último Login: 2025-11-09 20:30     │  │
│ └────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🔍 VERIFICAR EN BASE DE DATOS

Después de hacer login, verifica que tu usuario se guardó:

```bash
cd backend
python -c "
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Usar credenciales del .env
conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()
cursor.execute('SELECT id, email, name, google_id FROM users')
users = cursor.fetchall()
print('Usuarios en la base de datos:')
for user in users:
    print(f'  ✓ {user[2]} ({user[1]})')
    print(f'    ID: {user[0]}')
    print(f'    Google ID: {user[3]}')
    print()
conn.close()
"
```

Deberías ver TU usuario listado! 🎉

---

## 🆘 Troubleshooting

### Error: "redirect_uri_mismatch"

**Problema:** Google dice que la URI de redirección no coincide.

**Solución:**
1. Ve a Google Cloud Console
2. APIs & Services > Credentials
3. Click en "Eventos Visualizer Web Client"
4. Verifica que en "Authorized redirect URIs" esté EXACTAMENTE:
   ```
   http://localhost:8001/auth/google/callback
   ```
5. Si no está, agrégalo y guarda
6. Espera 1 minuto para que se actualice
7. Intenta de nuevo

### Error: "This app is blocked"

**Problema:** Google dice que la app está bloqueada.

**Solución:**
1. Ve a Google Cloud Console
2. APIs & Services > OAuth consent screen
3. En "Test users", agrega tu email
4. Click en "SAVE"
5. Intenta de nuevo

### Frontend no carga / página en blanco

**Solución:**
```bash
cd frontend
npm install
npm run dev
```

### Backend no inicia

**Solución:**
```bash
cd backend
pip install authlib python-jose passlib httpx pydantic-settings
python main.py
```

### "Cannot connect to database"

**Solución:**
- La app funciona sin base de datos PostgreSQL
- Usa MySQL configurado en .env
- El error es solo un warning, ignóralo

---

## 📱 PRÓXIMOS PASOS (Después de que funcione)

Una vez que el login funcione, puedes:

1. **Agregar el botón en tu app principal:**
   - Editar `HomePageModern.tsx`
   - Importar `GoogleLoginButton`
   - Agregarlo en la navegación

2. **Proteger rutas:**
   ```tsx
   import { useAuth } from './contexts/AuthContext';

   function ProtectedPage() {
     const { isAuthenticated } = useAuth();

     if (!isAuthenticated) {
       return <div>Por favor inicia sesión</div>
     }

     return <div>Contenido protegido</div>
   }
   ```

3. **Usar datos del usuario:**
   ```tsx
   const { user } = useAuth();

   console.log(user?.name);     // Nombre
   console.log(user?.email);    // Email
   console.log(user?.avatar_url); // Foto
   ```

4. **Hacer requests autenticados:**
   ```tsx
   const { token } = useAuth();

   fetch('http://localhost:8001/api/eventos/favoritos', {
     headers: {
       'Authorization': `Bearer ${token}`
     }
   })
   ```

---

## ✅ Checklist Final

Antes de empezar, verifica:

- [x] Google Cloud Console configurado
- [x] Client ID y Secret en `.env`
- [x] Backend integrado
- [x] Frontend configurado
- [x] Base de datos con tablas
- [ ] Backend corriendo (Paso 1)
- [ ] Frontend corriendo (Paso 2)
- [ ] Login probado (Paso 3)

---

**¿Listo? ¡Ejecuta los 3 pasos arriba y prueba tu login con Google!** 🚀

Si algo no funciona, mira el troubleshooting o avísame.
