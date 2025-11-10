# 🔄 REINICIAR BACKEND

Se hicieron cambios críticos en el backend. Necesitas reiniciarlo.

## Pasos:

### 1. Para el backend actual
En la terminal donde está corriendo el backend:
```
Ctrl + C
```

### 2. Reinicia el backend
```bash
cd backend
python main.py
```

## Deberías ver:
```
🚀 Starting Eventos Visualizer Backend...
🔐 Autenticación Google OAuth2 habilitada
✅ Database pool created successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## Cambios aplicados:
- ✅ SessionMiddleware agregado (necesario para OAuth)
- ✅ Redirect URI explícito configurado
- ✅ Scopes simplificados (solo perfil básico)
- ✅ itsdangerous instalado

---

**Después de reiniciar, prueba el botón "Registrarse" de nuevo!**
