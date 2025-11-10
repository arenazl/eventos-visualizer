# 🚀 GUÍA COMPLETA: Autenticación Google OAuth2

## PASO 1: Configurar Google Cloud Console (15 minutos)

### 1.1 Crear Proyecto en Google Cloud

1. **Abrir navegador** e ir a:
   ```
   https://console.cloud.google.com/
   ```

2. **Iniciar sesión** con tu cuenta Google

3. **Crear proyecto nuevo:**
   - Click en el selector de proyectos (arriba a la izquierda, al lado de "Google Cloud")
   - Click en "NEW PROJECT" (Nuevo Proyecto)
   - Nombre: `Eventos Visualizer`
   - Click en "CREATE" (Crear)
   - Espera 30 segundos mientras se crea

4. **Seleccionar el proyecto:**
   - Click en el selector de proyectos
   - Seleccionar "Eventos Visualizer"

### 1.2 Habilitar APIs Necesarias

1. **Ir al menú de navegación** (≡ arriba a la izquierda)

2. **Ir a "APIs & Services" > "Library"**

3. **Habilitar Google+ API:**
   - Buscar: `Google+ API`
   - Click en el resultado
   - Click en "ENABLE" (Habilitar)
   - Esperar que se habilite

4. **Habilitar Google People API** (recomendado):
   - Volver atrás (← flecha)
   - Buscar: `Google People API`
   - Click en "ENABLE"

### 1.3 Crear Credenciales OAuth 2.0

1. **Ir a "APIs & Services" > "Credentials"** (Credenciales)

2. **Configurar pantalla de consentimiento** (si es primera vez):
   - Click en "CONFIGURE CONSENT SCREEN"
   - Seleccionar **"External"** (Externo)
   - Click en "CREATE"

   **Llenar formulario:**
   - App name: `Eventos Visualizer`
   - User support email: tu email
   - Developer contact: tu email
   - Click en "SAVE AND CONTINUE"
   - En "Scopes", click en "SAVE AND CONTINUE" (sin agregar nada)
   - En "Test users", agregar tu email
   - Click en "SAVE AND CONTINUE"
   - Click en "BACK TO DASHBOARD"

3. **Crear credenciales OAuth:**
   - Click en "CREATE CREDENTIALS" (arriba)
   - Seleccionar "OAuth client ID"

   **Configurar:**
   - Application type: **"Web application"**
   - Name: `Eventos Visualizer Web Client`

   **Authorized JavaScript origins:** (click "ADD URI" para cada uno)
   ```
   http://localhost:8001
   http://127.0.0.1:8001
   http://localhost:5174
   http://127.0.0.1:5174
   ```

   **Authorized redirect URIs:** (click "ADD URI" para cada uno)
   ```
   http://localhost:8001/auth/google/callback
   http://127.0.0.1:8001/auth/google/callback
   ```

   - Click en "CREATE"

4. **Copiar credenciales:**
   - Aparecerá un popup con:
     - `Client ID` (algo como: 123456-abc.apps.googleusercontent.com)
     - `Client secret` (algo como: GOCSPX-abc123def456)
   - **COPIAR ambos** (los vas a necesitar en 2 minutos)
   - Click en "OK"

5. **Guardar credenciales:**
   - Abre `backend/.env` en tu editor
   - Reemplaza:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id-here
   GOOGLE_CLIENT_SECRET=your-google-client-secret-here
   ```

   Con tus credenciales reales:
   ```env
   GOOGLE_CLIENT_ID=123456-abc.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456
   ```

✅ **PASO 1 COMPLETADO!** Google Cloud Console configurado.

---

## PASO 2: Integrar en Backend (5 minutos)

Ahora voy a integrar los endpoints de autenticación en tu `main.py`.

### 2.1 Lo que voy a agregar

En el archivo `backend/main.py`, después de la línea 317 (después de CORS), voy a agregar:

```python
# ═══════════════════════════════════════════════════════════════════
# 🔐 AUTENTICACIÓN CON GOOGLE OAUTH2
# ═══════════════════════════════════════════════════════════════════
from api.auth import router as auth_router

# Incluir rutas de autenticación
app.include_router(auth_router)
logger.info("🔐 Autenticación Google OAuth2 habilitada")
```

### 2.2 Actualizar configuración

También voy a actualizar `backend/utils/config.py` para que lea las variables de entorno correctas.

---

## PASO 3: Configurar Frontend (10 minutos)

### 3.1 Actualizar dependencias de React Router

Primero verifica que tengas instalado React Router:

```bash
cd frontend
npm install react-router-dom
```

### 3.2 Configurar rutas principales

Voy a crear/actualizar tu archivo principal del frontend para incluir:
- AuthProvider (context de autenticación)
- Rutas para callback y error
- Botón de login en la navegación

### 3.3 Archivos que voy a modificar/crear:

1. **`frontend/src/main.tsx`** - Agregar AuthProvider y rutas
2. **`frontend/src/App.tsx`** - Agregar botón de login
3. **`frontend/src/pages/TestAuth.tsx`** - Página de prueba (NUEVA)

---

## PASO 4: Probar el Sistema (5 minutos)

### 4.1 Iniciar Backend

```bash
cd backend
python main.py
```

Deberías ver:
```
🚀 Starting Eventos Visualizer Backend...
🔐 Autenticación Google OAuth2 habilitada
✅ Database pool created successfully
```

### 4.2 Iniciar Frontend

En otra terminal:
```bash
cd frontend
npm run dev
```

### 4.3 Probar Login

1. Abrir navegador en `http://localhost:5174`
2. Click en "Continuar con Google"
3. Seleccionar tu cuenta Google
4. Aceptar permisos
5. Deberías ser redirigido de vuelta con tu sesión iniciada
6. Ver tu nombre y avatar en la esquina

---

## PASO 5: Verificar en Base de Datos

Después de hacer login, verifica que el usuario se creó:

```bash
cd backend
python -c "
import pymysql
conn = pymysql.connect(
    host='mysql-aiven-arenazl.e.aivencloud.com',
    port=23108,
    user='avnadmin',
    password='AVNS_Fqe0qsChCHnqSnVsvoi',
    database='events'
)
cursor = conn.cursor()
cursor.execute('SELECT id, email, name FROM users')
users = cursor.fetchall()
print('Usuarios registrados:')
for user in users:
    print(f'  - {user[1]} ({user[2]})')
conn.close()
"
```

---

## 🎯 RESUMEN RÁPIDO

**¿Qué vas a tener después de esto?**

1. ✅ Login con Google funcionando
2. ✅ Usuarios guardados en MySQL
3. ✅ JWT tokens para mantener sesión
4. ✅ Botón de login/logout en tu app
5. ✅ Perfil de usuario con avatar y nombre
6. ✅ Listo para agregar features protegidas (favoritos, notificaciones, etc.)

**Endpoints disponibles:**
- `GET /auth/google/login` - Iniciar login
- `GET /auth/me` - Obtener info del usuario actual
- `PUT /auth/profile` - Actualizar perfil
- `POST /auth/logout` - Cerrar sesión

---

## 🆘 Troubleshooting

### Error: "redirect_uri_mismatch"
**Solución:** Verifica que las URIs en Google Cloud Console sean EXACTAMENTE:
- `http://localhost:8001/auth/google/callback`
- Sin espacios, sin https, sin puerto extra

### Error: "Invalid client"
**Solución:** Verifica que copiaste bien Client ID y Secret en `.env`

### Frontend no redirige
**Solución:** Verifica que CORS esté configurado y que el frontend esté en puerto 5174

### Usuario no se crea en DB
**Solución:** Verifica la conexión a MySQL ejecutando:
```bash
cd backend
python scripts/init_db.py
```

---

## ✅ Checklist Final

Antes de probar, verifica que tengas:

- [ ] Google Cloud Console configurado
- [ ] Client ID y Secret en `.env`
- [ ] Backend con endpoints integrados
- [ ] Frontend con AuthProvider configurado
- [ ] Rutas de callback agregadas
- [ ] Backend corriendo en puerto 8001
- [ ] Frontend corriendo en puerto 5174

---

**¿Listo para empezar?**

Lee PASO 1 arriba y cuando tengas las credenciales de Google, avísame para continuar con los pasos 2-5 automáticamente.
