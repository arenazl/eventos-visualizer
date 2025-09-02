# CLAUDE.md - TEMPLATE PARA NUEVOS PROYECTOS

## 🚨🚨🚨 REGLAS ESPECÍFICAS DEL PROYECTO 🚨🚨🚨
### 🔥 PUERTOS DEL PROYECTO (CAMBIAR SEGÚN PROYECTO):
- **BACKEND**: Puerto 8001 (CAMBIAR SI ES NECESARIO)
- **FRONTEND**: Puerto 5174 (CAMBIAR SI ES NECESARIO)

### 🎯 CONTEXTO DEL PROYECTO (PERSONALIZAR):
- **Proyecto**: [NOMBRE Y DESCRIPCIÓN]
- **Dominio**: [DESCRIPCIÓN DEL DOMINIO]  
- **Tecnologías**: [STACK TECNOLÓGICO]
- **Base de datos**: [TIPO DE BD]
- **Deployment**: [PLATAFORMA DE DEPLOY]

## 📚 SISTEMA DE DOCUMENTACIÓN INTELIGENTE

### 🗂️ **ESTRUCTURA OBLIGATORIA:**
- **Ubicación central**: `/docs/` (categorizada por funcionalidad)
- **Índice maestro**: `/docs/00-INDEX.md` (orden cronológico completo)
- **Headers obligatorios**: Todos los .md DEBEN tener audit header
- **Estados de documentos**: ACTIVE | DEPRECATED | MERGED | SUPERSEDED | ARCHIVE

### 📋 **GESTIÓN DE ESTADOS OBLIGATORIA:**
**PROCESO CRÍTICO:** Al modificar cualquier funcionalidad:

1. **🔍 BUSCAR docs relacionados**:
   ```bash
   grep -r "tema_funcionalidad" docs/
   find docs/ -name "*.md" -exec grep -l "keyword" {} \;
   ```

2. **📝 ACTUALIZAR headers** de documentos afectados:
   - Cambiar fecha de última actualización
   - Agregar entrada al historial
   - Actualizar estado si es necesario

3. **🔗 MARCAR obsoletos** como MERGED/DEPRECATED/SUPERSEDED:
   - Indicar dónde está la información actual
   - Agregar referencias cruzadas
   - NUNCA eliminar, solo cambiar estado

4. **📊 ACTUALIZAR índice maestro** (`docs/00-INDEX.md`)

### 🔄 **TEMPLATE DE HEADER OBLIGATORIO:**
```markdown
<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: YYYY-MM-DD HH:MM
📊 STATUS: ACTIVE | DEPRECATED | MERGED | SUPERSEDED | ARCHIVE
📝 HISTORIAL:
- YYYY-MM-DD HH:MM: Descripción específica del cambio
- YYYY-MM-DD HH:MM: Cambios anteriores...
📋 TAGS: #tag1 #tag2 #funcionalidad #categoria
-->
```

### 🎯 **EJEMPLOS DE GESTIÓN DE ESTADOS:**

#### **Caso: Funcionalidad actualizada**
```markdown
<!-- En archivo-viejo.md -->
📊 STATUS: MERGED → carpeta/nuevo-archivo.md
📝 HISTORIAL:
- 2025-09-01 17:45: MERGED - Información consolidada en nuevo archivo
```

### 🚨 **REGLAS CRÍTICAS DE DOCUMENTACIÓN:**

1. **NUNCA eliminar documentos** - Solo cambiar estado a ARCHIVE
2. **SIEMPRE actualizar headers** al modificar contenido
3. **OBLIGATORIO referencias cruzadas** cuando se merge o depreca
4. **MANTENER /docs/00-INDEX.md actualizado** con cada cambio
5. **UN AGENTE debe buscar docs relacionados** antes de crear nuevos

### 📂 **ESTRUCTURA DE CARPETAS:**
```
docs/
├── 00-INDEX.md                 # 📋 Índice maestro
├── apis/                       # 🌐 APIs e integraciones
├── backend/                    # 🔧 Documentación backend
├── frontend/                   # 🎨 Documentación frontend
├── deployment/                 # 🚀 Deploy y producción
├── features/                   # ✨ Features implementadas
├── templates/                  # 🎨 Templates HTML (si aplica)
└── archive/                    # 📦 Documentación obsoleta
```

## 🚀 **INSTRUCCIONES PARA SETUP INICIAL:**

### **Al crear proyecto nuevo:**
1. `claude init`
2. Copiar este template como `CLAUDE.md` 
3. Personalizar secciones marcadas con [CAMBIAR]
4. Crear estructura `docs/` con carpetas básicas:
   ```bash
   mkdir -p docs/{apis,backend,frontend,deployment,features,archive}
   ```
5. Crear `docs/00-INDEX.md` vacío con header

### **Para agentes nuevos:**
**UN SOLO COMANDO:** *"Lee el CLAUDE.md"*
- Ya tienen TODO el sistema
- Saben cómo organizar documentación  
- Saben cómo gestionar estados
- Tienen templates y procesos