# 🔧 ARREGLAR ERROR: redirect_uri_mismatch

## ❌ El Error
```
Error 400: redirect_uri_mismatch
```

Esto significa que la URI de redirección que tu app envía a Google **NO coincide** con las que configuraste en Google Cloud Console.

---

## ✅ SOLUCIÓN - Verificar y Corregir en Google Cloud Console

### PASO 1: Ir a Google Cloud Console

1. Abre: https://console.cloud.google.com/
2. Selecciona tu proyecto "funaroundyou" (o como lo hayas llamado)

### PASO 2: Ir a Credentials

1. Menú lateral (≡) > **APIs & Services** > **Credentials**
2. Busca en la sección **"OAuth 2.0 Client IDs"**
3. Verás algo como: `Eventos Visualizer Web Client` o `funaroundyou`
4. **Haz click en el nombre** (NO en el icono de descarga)

### PASO 3: Verificar URIs Autorizadas

Te aparecerá una pantalla con:

```
┌──────────────────────────────────────────────────────────┐
│ Edit OAuth client                                         │
├──────────────────────────────────────────────────────────┤
│ Name: Eventos Visualizer Web Client                      │
│                                                           │
│ Authorized JavaScript origins                             │
│ [+ ADD URI]                                               │
│ URIs:                                                     │
│ 1. http://localhost:8001                                 │ ← Debe estar
│ 2. http://127.0.0.1:8001                                 │ ← Debe estar
│ 3. http://localhost:5174                                 │ ← Debe estar
│ 4. http://127.0.0.1:5174                                 │ ← Debe estar
│                                                           │
│ Authorized redirect URIs          ← ¡ESTA ES LA CLAVE!   │
│ [+ ADD URI]                                               │
│ URIs:                                                     │
│ 1. http://localhost:8001/auth/google/callback           │ ← ¡CRÍTICO!
│ 2. http://127.0.0.1:8001/auth/google/callback           │ ← ¡CRÍTICO!
│                                                           │
│                           [CANCEL]     [SAVE]             │
└──────────────────────────────────────────────────────────┘
```

### PASO 4: Verificar EXACTAMENTE estas URIs

**Authorized redirect URIs** DEBE tener **EXACTAMENTE** estas 2 líneas:

```
http://localhost:8001/auth/google/callback
http://127.0.0.1:8001/auth/google/callback
```

**⚠️ IMPORTANTE:**
- SIN espacios antes o después
- SIN mayúsculas (todo minúscula)
- SIN trailing slash (/) al final
- SIN `https` (es `http`)
- CON el puerto `:8001`
- CON `/auth/google/callback` al final

### PASO 5: Agregar/Corregir URIs

Si NO están o están mal escritas:

1. **Borra** las URIs incorrectas (click en el ícono 🗑️)
2. **Click en "+ ADD URI"** debajo de "Authorized redirect URIs"
3. **Pega EXACTAMENTE:**
   ```
   http://localhost:8001/auth/google/callback
   ```
4. **Click en "+ ADD URI"** de nuevo
5. **Pega EXACTAMENTE:**
   ```
   http://127.0.0.1:8001/auth/google/callback
   ```

### PASO 6: Guardar Cambios

1. **Scroll down** hasta el final de la página
2. Click en **"SAVE"** (azul)
3. Espera que aparezca el mensaje de confirmación

### PASO 7: Esperar Propagación

⏱️ **Espera 1-2 minutos** para que Google actualice las URIs.

---

## 🧪 VERIFICAR QUE QUEDÓ BIEN

Después de guardar, deberías ver algo así:

```
OAuth 2.0 Client ID: Eventos Visualizer Web Client

Authorized JavaScript origins
  http://localhost:8001
  http://127.0.0.1:8001
  http://localhost:5174
  http://127.0.0.1:5174

Authorized redirect URIs
  http://localhost:8001/auth/google/callback     ← ✅
  http://127.0.0.1:8001/auth/google/callback     ← ✅
```

---

## 🎯 PROBAR DE NUEVO

1. **Espera 1-2 minutos** (Google necesita propagar los cambios)
2. **Recarga tu app**: `http://localhost:5174`
3. **Click en "Registrarse"**
4. Ahora debería funcionar! ✨

---

## 🆘 Si TODAVÍA da error

Si después de esto sigue dando error:

### Opción 1: Verificar que el backend esté usando localhost

```bash
# En tu navegador, verifica que estés usando:
http://localhost:5174    ← NO 127.0.0.1

# Si estás usando 127.0.0.1, cámbialo a localhost
```

### Opción 2: Captura de pantalla

Si quieres estar 100% seguro, toma una captura de pantalla de la página de Google Cloud Console mostrando las "Authorized redirect URIs" y verifica que tengan EXACTAMENTE:

```
http://localhost:8001/auth/google/callback
```

---

**¿Ya corregiste las URIs en Google Cloud Console?**

Recuerda esperar 1-2 minutos después de guardar antes de probar de nuevo.
