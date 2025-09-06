# 🧠 Context MCP - Sistema de Memoria del Proyecto

## ¿Qué es Context MCP?

**Context MCP** (Model Context Protocol - Memory Server) es un sistema que permite a Claude y otros asistentes AI **recordar información importante del proyecto entre diferentes sesiones de chat**. 

Funciona como una "memoria persistente" que almacena:
- Configuraciones del proyecto
- Reglas críticas que no deben violarse
- Estado actual del sistema
- Relaciones entre componentes
- Historial de decisiones importantes

## 🎯 ¿Para qué sirve?

### Sin Context MCP:
- Claude olvida todo al cerrar el chat
- Debes repetir las mismas instrucciones cada vez
- Riesgo de que se cambien configuraciones críticas
- No hay continuidad entre sesiones

### Con Context MCP:
- ✅ Claude recuerda las reglas del proyecto (ej: "NUNCA cambiar puerto 8001")
- ✅ Conoce el estado actual del sistema
- ✅ Mantiene contexto entre diferentes chats
- ✅ Evita errores repetitivos
- ✅ Mejora la consistencia del desarrollo

## 📂 Archivos del Sistema

```
eventos-visualizer/
├── project_context.json       # Base de conocimiento del proyecto
├── project_context.py         # Script para gestionar el contexto
├── claude_desktop_config.json # Configuración para Claude Desktop
└── mcp-servers/src/memory/    # Servidor de memoria MCP
```

## 🚀 Cómo Funciona

### 1. **Knowledge Graph (Grafo de Conocimiento)**
El sistema organiza la información en:
- **Entidades**: Nodos principales (proyecto, componentes, reglas)
- **Observaciones**: Hechos sobre cada entidad
- **Relaciones**: Conexiones entre entidades

### 2. **Ejemplo de Entidades**

```json
{
  "EventosVisualizer": {
    "tipo": "proyecto",
    "observaciones": [
      "Backend en puerto 8001",
      "Frontend en puerto 5174",
      "IP WSL: 172.29.228.80"
    ]
  },
  "CriticalRules": {
    "tipo": "reglas",
    "observaciones": [
      "NUNCA cambiar puerto 8001",
      "NUNCA usar localhost",
      "SIEMPRE usar templates HTML"
    ]
  }
}
```

## 📝 Uso Práctico

### Para Actualizar el Contexto:

```bash
# Ejecutar el script de contexto
python3 project_context.py
```

### Para Agregar Nueva Información:

```python
# En project_context.py, agregar observaciones:
context.add_observation("Backend", "Nueva API integrada: Spotify")
context.add_observation("CurrentStatus", "Migración a PostgreSQL completada")
```

## 🔧 Configuración con Claude Desktop

### Opción 1: Configuración Local
Copiar el contenido de `claude_desktop_config.json` a tu configuración de Claude Desktop.

### Opción 2: NPX Directo
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

## 📊 Información Almacenada Actualmente

### 🏗️ Componentes del Sistema:
- **Backend**: FastAPI, Puerto 8001, Python 3.12
- **Frontend**: React + Vite, Puerto 5174, TypeScript
- **Database**: PostgreSQL con PostGIS
- **APIs**: Eventbrite, Facebook, Ticketmaster, Meetup

### 🚨 Reglas Críticas:
- ❌ NUNCA cambiar puertos (8001, 5174)
- ❌ NUNCA usar localhost (usar IP WSL)
- ❌ NO crear eventos simulados
- ✅ SIEMPRE usar templates HTML
- ✅ SIEMPRE liberar conexiones DB

### 📈 Estado Actual:
- Servidores funcionando
- CloudScraper instalado
- Endpoints sincronizados
- Facebook sin UIDs
- Timeouts optimizados

## 🎯 Beneficios para el Desarrollo

1. **Consistencia**: Las reglas críticas nunca se olvidan
2. **Eficiencia**: No repetir configuraciones en cada sesión
3. **Seguridad**: Previene cambios accidentales peligrosos
4. **Continuidad**: El proyecto mantiene su contexto histórico
5. **Colaboración**: Múltiples desarrolladores comparten el mismo contexto

## 🔄 Actualización del Contexto

El contexto debe actualizarse cuando:
- Se agregan nuevas APIs o servicios
- Cambian configuraciones importantes
- Se descubren nuevas reglas críticas
- Se completan migraciones importantes
- Cambia el estado del sistema

## 💡 Tips de Uso

1. **Ejecutar semanalmente** `python3 project_context.py` para mantener actualizado
2. **Documentar decisiones importantes** como observaciones
3. **Revisar periódicamente** las reglas críticas
4. **Compartir el archivo** `project_context.json` con el equipo
5. **Hacer backup** del contexto antes de cambios mayores

---

**Última actualización**: 6 de Septiembre 2025
**Versión**: 1.0.0
**Estado**: ✅ Operativo y configurado