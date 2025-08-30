# 📁 Estructura del Proyecto - Eventos Visualizer

Este documento explica la organización completa del framework exitoso.

## 🗂️ Estructura Completa

```
eventos-visualizer/
├── 📄 README.md                   # Guía principal del usuario
├── 📄 CLAUDE.md                   # Reglas críticas para Claude (PUERTO INMUTABLE, TEMPLATES)
├── 📁 docs/                       # Documentación completa
│   ├── 📁 templates/              # 🔥 CLAVE DEL ÉXITO - Templates HTML
│   │   ├── README.md              # Instrucciones para usar templates
│   │   └── event-card-reference.html # Template principal (USUARIO REEMPLAZA)
│   ├── 📁 setup/                  # Configuración del proyecto
│   │   ├── INITIAL.md             # Especificaciones detalladas (confidence 9/10)
│   │   └── SETUP.md               # Variables de entorno y configuración
│   ├── 📁 guides/                 # Guías adicionales (este archivo)
│   └── 📁 research/               # Se llena automáticamente con research
├── 📁 .claude/
│   └── 📁 commands/               # Solo 2 comandos (como context-test exitoso)
│       ├── generate-prp.md        # Genera PRP usando templates + research
│       └── execute-prp.md         # Implementa siguiendo templates exactos
└── 📁 PRPs/                       # Se genera automáticamente
    └── eventos-visualizer-completo.md
```

## 🔑 Archivos Clave del Framework

### **📄 README.md - Guía del Usuario**
- Instrucciones claras para usar el framework
- Explicación del sistema de templates HTML
- Comandos exactos a ejecutar
- Qué esperar al final

### **📄 CLAUDE.md - Reglas para Claude**
- **Puertos inmutables** (8001, 5174)
- **IP de WSL** nunca localhost  
- **Templates HTML obligatorios**
- APIs reales, nunca mock data
- Patrones de arquitectura específicos

### **📁 docs/templates/ - CLAVE DEL ÉXITO**
- **README.md**: Instrucciones exactas sobre cómo usar templates
- **event-card-reference.html**: Template principal que usuario reemplaza
- Otros templates adicionales para diferentes componentes

### **📄 docs/setup/INITIAL.md - Especificación Técnica**
- Especificación completa del proyecto
- APIs a integrar (Eventbrite, Ticketmaster, Meetup)
- Arquitectura técnica detallada
- Success criteria específicos
- **Confidence: 9/10** como context-test exitoso

### **📁 .claude/commands/ - Comandos Simples**
- **generate-prp.md**: Lee templates + hace research → genera PRP
- **execute-prp.md**: Implementa usando templates como base
- Solo 2 comandos (no 3 agentes complejos como el framework fallido)

## 🎯 Diferencias vs Framework Fallido

### **❌ Lo que FALLÓ en simple-context:**
```
- 3 agentes complejos con instrucciones largas
- Sin templates HTML concretos
- Referencias abstractas
- Workflow muy complejo
- Sin confidence scoring
- Genérico "ecommerce profesional"
```

### **✅ Lo que FUNCIONA en eventos-visualizer:**
```
- 2 comandos simples como context-test
- Templates HTML concretos
- Referencias específicas (apps reales)
- Workflow directo
- Confidence 9/10 target
- Dominio específico "eventos mobile-first"
```

## 🔄 Flujo de Uso Exitoso

### **1. Preparación (Usuario)**
```bash
# Usuario pone su diseño HTML en:
docs/templates/event-card-reference.html
```

### **2. Generación de PRP (~15 min)**
```bash
/generate-prp docs/setup/INITIAL.md
# - Lee templates HTML
# - Hace research de apps reales  
# - Genera PRP súper detallado
# - Output: PRPs/eventos-visualizer-completo.md
```

### **3. Implementación (~2-3 horas)**
```bash
/execute-prp PRPs/eventos-visualizer-completo.md
# - Copia estructura HTML exacta del template
# - Implementa APIs reales (Eventbrite, Ticketmaster, etc.)
# - Genera PWA completa mobile-first
# - Output: App funcionando en puertos 8001 + 5174
```

## 🎨 Sistema de Templates (Innovación Clave)

### **Cómo Funciona:**
1. **Usuario diseña HTML** como quiere que se vea la app
2. **Claude lee el template** y copia estructura exacta  
3. **Solo cambia datos** - mantiene diseño idéntico
4. **Resultado visual perfecto** sin inventar diseño

### **Ejemplo:**
```html
<!-- Usuario pone en template: -->
<div class="bg-white rounded-xl shadow-lg">
  <h3 class="font-bold text-lg">{{event.title}}</h3>
  <p class="text-gray-600">{{event.date}}</p>
</div>

<!-- Claude genera React idéntico: -->
<div className="bg-white rounded-xl shadow-lg">
  <h3 className="font-bold text-lg">{event.title}</h3>
  <p className="text-gray-600">{event.date}</p>
</div>
```

## 📊 Confidence Scoring

### **Target: 9/10 (como context-test exitoso)**

**Factores que aseguran 9/10:**
- ✅ Templates HTML concretos (no inventar diseño)
- ✅ APIs reales documentadas (Eventbrite, Ticketmaster)
- ✅ Dominio específico (eventos, no genérico)
- ✅ Patrones probados (PWA, mobile-first)
- ✅ References reales (Mobbin.com screenshots)
- ✅ Workflow simple (2 pasos vs 3 agentes)

## 🚀 Próximos Pasos

### **Para el Usuario:**
1. **Personalizar template**: Editar `docs/templates/event-card-reference.html` con su diseño
2. **Configurar APIs** (opcional): Obtener keys de Eventbrite/Ticketmaster
3. **Ejecutar comandos**: Los 2 comandos en secuencia
4. **Obtener resultado**: App de eventos funcionando perfectamente

### **Resultado Final Esperado:**
- 📱 **PWA mobile-first** instalable
- 🎨 **Diseño idéntico** al template HTML
- 🔌 **APIs reales** integradas  
- 📍 **Geolocalización** funcional
- 📅 **Google Calendar** sync
- 🔔 **Push notifications** working
- ⚡ **Performance**: <3s loading
- 📊 **Confidence**: 9/10 success rate

---

**Este framework aplica exactamente la fórmula que funcionó en context-test.**
**La diferencia está en los templates HTML concretos + dominio específico.**
