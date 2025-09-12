# 🚀 Guía de Inicio Rápido - Eventos Visualizer

## ✅ Estado Actual
- **Backend**: Funcionando en http://172.29.228.80:8001
- **Frontend**: Funcionando en http://localhost:5174
- **Base de datos**: PostgreSQL (configuración en .env)

## 📋 Comandos de Inicio

### Backend (Puerto 8001)
```bash
cd backend
python3 main.py
```

### Frontend (Puerto 5174)
```bash
cd frontend
npm run dev
```

## 🔍 Verificación de Funcionamiento

### 1. Backend Health Check
```bash
curl http://172.29.228.80:8001/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-06T04:09:02.233359",
  "server": "http://172.29.228.80:8001",
  "service": "eventos-visualizer-backend",
  "version": "1.0.0"
}
```

### 2. API de Eventos
```bash
curl "http://172.29.228.80:8001/api/events?location=Buenos%20Aires&limit=5"
```

### 3. Categorías Disponibles
```bash
curl http://172.29.228.80:8001/api/events/categories
```

## 🛠️ Troubleshooting

### Si el puerto está ocupado:
```bash
# Para backend (8001)
lsof -ti:8001 | xargs kill -9

# Para frontend (5174)
lsof -ti:5174 | xargs kill -9
```

### Si hay errores de sintaxis en main.py:
- Revisar líneas 3629-3694 (indentación del for loop)
- El archivo ya está corregido y funcionando

## 📊 Arquitectura

### Servidor Monolítico (Actual)
- `backend/main.py`: 3,737 líneas con 52 endpoints
- Funcional pero necesita refactorización

### Arquitectura Modular (Refactorizada - En Testing)
- `backend/app/`: App factory y configuración
- `backend/api/v1/routers/`: 5 routers por dominio
- `backend/main_new.py`: ~50 líneas (pendiente de migración completa)

## 🔄 Endpoints Principales

### Eventos
- `GET /api/events` - Lista eventos con filtros
- `GET /api/events/categories` - Categorías disponibles
- `GET /api/events/{event_id}` - Detalle de evento

### Búsqueda
- `POST /api/smart/search` - Búsqueda inteligente
- `POST /api/parallel/search` - Búsqueda paralela

### WebSocket
- `WS /ws` - Conexión WebSocket para tiempo real

## 📝 Notas Importantes

1. **NUNCA cambiar los puertos** - Siempre usar 8001 (backend) y 5174 (frontend)
2. **IP en WSL**: Usar 172.29.228.80, no localhost
3. **Base de datos**: PostgreSQL debe estar corriendo
4. **APIs externas**: Configurar keys en .env para Eventbrite, Ticketmaster, etc.

## 🎯 Próximos Pasos

1. Completar migración a arquitectura modular
2. Implementar tests unitarios
3. Configurar CI/CD
4. Documentar APIs con OpenAPI/Swagger

---
**Última actualización**: 6 de Septiembre 2025
**Estado**: ✅ Aplicación funcionando correctamente