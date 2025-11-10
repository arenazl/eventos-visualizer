# 🌐 GOOGLE CLOUD CONSOLE - GUÍA VISUAL PASO A PASO

## ⏱️ Tiempo estimado: 10-15 minutos

---

## PASO 1: Acceder a Google Cloud Console

### 1.1 Abrir la consola
1. Abre tu navegador
2. Ve a: **https://console.cloud.google.com/**
3. Inicia sesión con tu cuenta Google personal

---

## PASO 2: Crear un Nuevo Proyecto

### 2.1 Abrir selector de proyectos
1. **Busca en la parte superior izquierda**, al lado del logo "Google Cloud"
2. Verás un texto que dice "My Project" o el nombre de un proyecto existente
3. **Haz click en ese texto** (es un selector desplegable)

### 2.2 Crear proyecto
1. En el popup que aparece, busca arriba a la derecha el botón **"NEW PROJECT"**
2. Haz click en "NEW PROJECT"

### 2.3 Configurar proyecto
Te aparecerá un formulario:

```
┌─────────────────────────────────────────┐
│ New Project                              │
├─────────────────────────────────────────┤
│ Project name:                            │
│ [Eventos Visualizer____________]        │  ← Escribe esto
│                                          │
│ Location:                                │
│ [No organization]                        │  ← Dejar así
│                                          │
│                  [CANCEL]     [CREATE]   │  ← Click CREATE
└─────────────────────────────────────────┘
```

4. **Espera 10-30 segundos** mientras se crea el proyecto
5. Verás una notificación arriba: "Creating project Eventos Visualizer..."

### 2.4 Seleccionar el proyecto
1. Cuando termine, click en **"SELECT PROJECT"** en la notificación
2. O vuelve al selector de proyectos y selecciona "Eventos Visualizer"

---

## PASO 3: Configurar Pantalla de Consentimiento OAuth

### 3.1 Ir a OAuth consent screen
1. En el menú lateral (≡ arriba a la izquierda), busca:
   ```
   ≡ Navigation menu
   ├─ Home
   ├─ APIs & Services
   │  ├─ Enabled APIs & services
   │  ├─ Library
   │  ├─ Credentials          ← ¡Aquí vamos después!
   │  └─ OAuth consent screen  ← ¡Aquí vamos ahora!
   ```

2. Haz click en **"APIs & Services" > "OAuth consent screen"**

### 3.2 Configurar tipo de usuario
Te preguntará el "User Type":

```
┌──────────────────────────────────────────────┐
│ Which user type do you want to configure?    │
│                                               │
│  ⚪ Internal                                  │
│     Only for Google Workspace users          │
│                                               │
│  ⦿ External                                  │  ← Selecciona este
│     Available to any test user with          │
│     a Google Account                          │
│                                               │
│                             [CREATE]          │
└──────────────────────────────────────────────┘
```

3. Selecciona **"External"**
4. Click en **"CREATE"**

### 3.3 Llenar información de la app

**PASO 1: App information**

```
App name: [Eventos Visualizer_____________]  ← Exacto
User support email: [tu-email@gmail.com____]  ← Tu email
App logo: [Skip Optional__________________]  ← Opcional, déjalo vacío
```

Scroll hacia abajo:

```
App domain (Optional) - Todo opcional, déjalo vacío

Developer contact information:
Email addresses: [tu-email@gmail.com_______]  ← Tu email

                         [SAVE AND CONTINUE]  ← Click aquí
```

**PASO 2: Scopes**

```
┌──────────────────────────────────────────┐
│ Scopes                                    │
│                                           │
│ No scopes added yet                       │  ← Dejar vacío está bien
│                                           │
│                  [SAVE AND CONTINUE]      │  ← Click aquí
└──────────────────────────────────────────┘
```

**PASO 3: Test users**

```
┌──────────────────────────────────────────┐
│ Test users                                │
│                                           │
│ [+ ADD USERS]                             │  ← Click aquí
│                                           │
│ Add test users (optional):                │
│ [tu-email@gmail.com____________]          │  ← Agrega tu email
│                                           │
│                         [ADD]             │
│                                           │
│ Test users:                               │
│ • tu-email@gmail.com              [×]     │
│                                           │
│                  [SAVE AND CONTINUE]      │  ← Click aquí
└──────────────────────────────────────────┘
```

**PASO 4: Summary**

```
┌──────────────────────────────────────────┐
│ Summary                                   │
│                                           │
│ ✓ App information                         │
│ ✓ Scopes (0)                              │
│ ✓ Test users (1)                          │
│                                           │
│                  [BACK TO DASHBOARD]      │  ← Click aquí
└──────────────────────────────────────────┘
```

---

## PASO 4: Crear Credenciales OAuth 2.0

### 4.1 Ir a Credentials
1. En el menú lateral: **"APIs & Services" > "Credentials"**

### 4.2 Crear credenciales
1. En la parte superior, click en **"+ CREATE CREDENTIALS"**
2. Selecciona **"OAuth client ID"**

### 4.3 Configurar credenciales

```
┌──────────────────────────────────────────────────────┐
│ Create OAuth client ID                                │
├──────────────────────────────────────────────────────┤
│ Application type:                                     │
│ [▼ Web application                           ]        │  ← Selecciona esto
│                                                       │
│ Name:                                                 │
│ [Eventos Visualizer Web Client______________]        │  ← Escribe esto
│                                                       │
│ Authorized JavaScript origins                         │
│ To prevent CORS errors, add your app's URL:          │
│ [+ ADD URI]                                           │  ← Click aquí 4 veces
│                                                       │
│ URIs:                                                 │
│ 1. http://localhost:8001                             │  ← Agregar este
│ 2. http://127.0.0.1:8001                             │  ← Agregar este
│ 3. http://localhost:5174                             │  ← Agregar este
│ 4. http://127.0.0.1:5174                             │  ← Agregar este
│                                                       │
│ Authorized redirect URIs                              │
│ [+ ADD URI]                                           │  ← Click aquí 2 veces
│                                                       │
│ URIs:                                                 │
│ 1. http://localhost:8001/auth/google/callback        │  ← ¡IMPORTANTE!
│ 2. http://127.0.0.1:8001/auth/google/callback        │  ← ¡IMPORTANTE!
│                                                       │
│                           [CANCEL]     [CREATE]       │  ← Click CREATE
└──────────────────────────────────────────────────────┘
```

**⚠️ MUY IMPORTANTE:**
- Los "Redirect URIs" deben ser **EXACTAMENTE**:
  - `http://localhost:8001/auth/google/callback`
  - `http://127.0.0.1:8001/auth/google/callback`
- Nota que termina en `/auth/google/callback`
- **SIN** espacios, **SIN** mayúsculas, **SIN** trailing slash

### 4.4 Copiar credenciales

Aparecerá un popup:

```
┌──────────────────────────────────────────────────────┐
│ OAuth client created                                  │
├──────────────────────────────────────────────────────┤
│ Here is your client ID and secret. Save these        │
│ somewhere secure.                                     │
│                                                       │
│ Your Client ID:                                       │
│ ┌────────────────────────────────────────────────┐   │
│ │ 123456789-abc123def456.apps.googleusercontent. │   │  ← COPIAR ESTO
│ │ com                                             │   │
│ └────────────────────────────────────────────────┘   │
│                                       [📋 Copy]       │
│                                                       │
│ Your Client Secret:                                   │
│ ┌────────────────────────────────────────────────┐   │
│ │ GOCSPX-abc123def456ghi789jkl                   │   │  ← COPIAR ESTO
│ └────────────────────────────────────────────────┘   │
│                                       [📋 Copy]       │
│                                                       │
│                                           [OK]        │
└──────────────────────────────────────────────────────┘
```

**ACCIÓN INMEDIATA:**

1. **Copia el Client ID** (click en el icono 📋)
2. **Copia el Client Secret** (click en el icono 📋)
3. **PEGA ambos en un lugar seguro** (Notepad, archivo .txt, etc.)

---

## PASO 5: Guardar Credenciales en tu Proyecto

### 5.1 Abrir archivo .env
1. En tu editor de código, abre: `backend/.env`

### 5.2 Reemplazar credenciales
Busca estas líneas:
```env
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

Y reemplázalas con tus credenciales reales:
```env
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456ghi789jkl
```

### 5.3 Guardar archivo
- **Ctrl + S** para guardar
- **¡MUY IMPORTANTE!** No commitear este archivo a Git

---

## ✅ VERIFICACIÓN FINAL

Antes de continuar, verifica que tu archivo `.env` tenga:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=<tu-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-<tu-secret>
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# JWT Configuration
JWT_SECRET_KEY=SVJvdSYVR3Uyn0WtZpB1RaBIVtcteNq0xnZWI3lkMzk
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 🎉 ¡LISTO!

Ya tienes Google Cloud Console configurado.

**Ahora puedes:**
1. Iniciar tu backend: `cd backend && python main.py`
2. Iniciar tu frontend: `cd frontend && npm run dev`
3. Abrir `http://localhost:5174/auth/test`
4. Click en "Continuar con Google"

---

## 🆘 Problemas Comunes

### "redirect_uri_mismatch"
**Causa:** Las URIs no coinciden exactamente

**Solución:**
1. Ve a Google Cloud Console > Credentials
2. Click en tu OAuth client
3. Verifica que los Redirect URIs sean EXACTAMENTE:
   - `http://localhost:8001/auth/google/callback`
   - Sin espacios, sin mayúsculas

### "Access blocked: This app's request is invalid"
**Causa:** Falta configurar la pantalla de consentimiento

**Solución:**
1. Ve a "OAuth consent screen"
2. Completa PASO 3.3 arriba
3. Agrega tu email como test user

### "Invalid client"
**Causa:** Client ID o Secret mal copiados

**Solución:**
1. Ve a Credentials en Google Cloud
2. Click en tu OAuth client
3. Copia nuevamente Client ID y Secret
4. Pega en `.env` sin espacios extras

---

**¿Listo? Avísame cuando hayas completado este paso!**
