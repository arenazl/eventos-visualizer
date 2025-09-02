<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-09-01 17:45
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-09-01 17:45: Creación del índice maestro de documentación
📋 TAGS: #index #documentacion #maestro #organizacion
-->

# 📋 ÍNDICE MAESTRO DE DOCUMENTACIÓN
## Sistema de Organización Inteligente

---

## 📊 DOCUMENTOS ACTIVOS (Por orden cronológico)

### 🌐 **APIs y Integraciones** (`docs/apis/`)
- **01-latinamerica-apis.md** - ACTIVE (2025-09-01) - APIs de eventos Latinoamérica y mundial
- **02-event-integrations.md** - ACTIVE (2025-09-01) - Integraciones específicas de eventos

### ✨ **Features y Funcionalidades** (`docs/features/`)
- **01-implemented-features.md** - ACTIVE (2025-09-01) - Estado actual de funcionalidades

### 🔧 **Backend** (`docs/backend/`)
- **01-gemini-integration.md** - ACTIVE (2025-09-01) - Estado integración Gemini
- **02-setup-windows.md** - ACTIVE (2025-09-01) - Setup en Windows
- **03-gemini-setup.md** - ACTIVE (2025-09-01) - Setup detallado Gemini
- **04-data-cleanup-report.md** - ACTIVE (2025-09-01) - Reporte limpieza datos

### 🎨 **Frontend** (`docs/frontend/`)
- **01-chat-setup.md** - ACTIVE (2025-09-01) - Configuración del chat

### 🚀 **Deployment** (`docs/deployment/`)
- **01-heroku-deploy.md** - ACTIVE (2025-09-01) - Proceso deploy Heroku
- **02-heroku-readme.md** - ACTIVE (2025-09-01) - README específico Heroku

### 🎨 **Templates** (`docs/templates/`)
- **01-templates-guide.md** - ACTIVE (2025-09-01) - Guía de templates HTML

---

## 📦 DOCUMENTOS ARCHIVADOS (`docs/archive/`)

### 🗃️ **Documentación Obsoleta**
- **initial-setup.md** - ARCHIVE (2025-09-01) - Setup inicial obsoleto
- **old-setup.md** - ARCHIVE (2025-09-01) - Configuración general obsoleta
- **structure-readme.md** - ARCHIVE (2025-09-01) - README estructura antigua

---

## 🎯 SISTEMA DE ESTADOS

- **ACTIVE** - Documento actual y válido para desarrollo
- **DEPRECATED** - Información obsoleta, conservar para referencia
- **MERGED** - Contenido fusionado en otro documento
- **SUPERSEDED** - Reemplazado por versión más nueva
- **ARCHIVE** - Histórico, no relevante para desarrollo actual

---

## 🔄 PROCESO DE ACTUALIZACIÓN

### Para Agentes Claude:
1. **Al modificar funcionalidad**: Buscar docs relacionados con `grep -r "tema" docs/`
2. **Actualizar headers**: Fecha, historial y estado
3. **Marcar obsoletos**: Como MERGED/DEPRECATED/SUPERSEDED
4. **Referencias cruzadas**: Indicar dónde está la nueva información
5. **Actualizar este índice**: Reflejar cambios de estado

### Template de Header:
```markdown
<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: YYYY-MM-DD HH:MM
📊 STATUS: ACTIVE | DEPRECATED | MERGED | SUPERSEDED | ARCHIVE
📝 HISTORIAL:
- YYYY-MM-DD HH:MM: Descripción del cambio
📋 TAGS: #tag1 #tag2 #funcionalidad
-->
```

---

## 🚨 REGLAS CRÍTICAS

1. **NUNCA eliminar documentos** - Solo cambiar estado a ARCHIVE
2. **SIEMPRE actualizar headers** cuando se modifica contenido
3. **REFERENCIAS cruzadas** cuando se merge o depreca
4. **MANTENER este índice actualizado** con cada cambio