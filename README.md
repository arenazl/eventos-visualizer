# 🎉 EVENTOS VISUALIZER - Sistema Completo de Gestión de Eventos
*Framework exitoso: De idea a app funcionando usando Claude Code + Templates HTML*

---

## 🚀 **INICIO RÁPIDO**

### **¿Qué es esto?**
Un sistema completo de visualización y gestión de eventos (deportivos, culturales, fiestas, conciertos) con integración a agenda personal, notificaciones y diseño mobile-first.

### **¿Cómo funciona?**
1. **Ya completé** las especificaciones (docs/setup/INITIAL.md) ✅
2. **Tienes template HTML** en docs/templates/ para copiar diseño ✅
3. **Ejecutas** 2 comandos secuenciales ⚡  
4. **Obtienes** app de eventos funcionando perfectamente 📱

---

## ⚡ **EJECUTAR AHORA (2 PASOS)**

### **Paso 1: Generar PRP** (~15 min)
```bash
/generate-prp docs/setup/INITIAL.md
```
**Qué hace:** Lee especificaciones + usa templates HTML + scraping de referencias

### **Paso 2: Implementar** (~2-3 horas)
```bash
/execute-prp PRPs/eventos-visualizer-completo.md
```
**Resultado:** 🎉 **Tu app de eventos completa funcionando**

---

## 🎨 **TEMPLATES HTML INCLUIDOS**

### **📁 docs/templates/ - CLAVE DEL ÉXITO**
- ✅ **event-card-reference.html** - Template principal para event cards
- ✅ **event-list-mobile.html** - Lista mobile-optimized
- ✅ **category-filters.html** - UI de filtros por categoría
- ✅ **calendar-integration.html** - Integración con agenda
- ✅ **event-details-page.html** - Página de detalles completa

### **🔥 REGLA CLAVE (Como context-test):**
**Claude NO inventa diseño - Solo copia templates HTML exactos**
- Misma estructura de elementos
- Mismas clases CSS
- Solo cambiar contenido dinámico
- Resultado idéntico visualmente

---

## 📊 **QUÉ TENDRÁS AL FINAL**

### **📱 App de Eventos Profesional con:**
- ✅ **Múltiples APIs integradas:** Eventbrite, Ticketmaster, Meetup, Facebook Events
- ✅ **Diseño pixel-perfect:** Basado en templates HTML reales
- ✅ **Categorización inteligente:** Deportes, música, cultural, tech, fiestas
- ✅ **Integración con agenda:** Google Calendar, Outlook, Apple Calendar
- ✅ **Geolocalización avanzada:** Eventos cerca de ti con mapas
- ✅ **Notificaciones push:** Recordatorios personalizados
- ✅ **PWA completa:** Instalable, offline support, background sync
- ✅ **Mobile-first responsive:** Optimizado para uso móvil

---

## 📁 **ESTRUCTURA DEL PROYECTO**

```
eventos-visualizer/
├── 📄 README.md                   # ✅ Este archivo
├── 📄 CLAUDE.md                   # ✅ Reglas para Claude + templates
├── 📁 docs/                       
│   ├── templates/                 # 🔥 TEMPLATES HTML REALES
│   │   ├── README.md              # Instrucciones de uso
│   │   ├── event-card-reference.html    # PRINCIPAL
│   │   ├── event-list-mobile.html
│   │   ├── category-filters.html
│   │   ├── calendar-integration.html
│   │   └── event-details-page.html
│   ├── research/                  # Referencias scrapeadas automáticamente
│   ├── guides/                    # Guías de implementación
│   └── setup/
│       ├── INITIAL.md             # ✅ Especificaciones detalladas
│       └── SETUP.md               # Configuración APIs
├── 📁 .claude/commands/           
│   ├── generate-prp.md            # Genera PRP usando templates
│   └── execute-prp.md             # Implementa copiando HTML
└── 📁 PRPs/                       # Se genera automáticamente
    └── eventos-visualizer-completo.md
```

---

## 🎯 **TIPOS DE EVENTOS SOPORTADOS**

### **🎵 Música & Entretenimiento**
- Conciertos, festivales, fiestas electrónicas
- Shows en vivo, stand-up comedy, karaoke

### **⚽ Deportes**  
- Fútbol, basketball, tenis, deportes extremos
- Maratones y competencias

### **🎨 Cultural & Arte**
- Exposiciones, teatro, danza
- Ferias gastronómicas, talleres

### **💻 Tech & Networking**
- Meetups, conferencias, hackathons
- Workshops de programación

### **🚗 Hobbies & Comunidades**
- Encuentros de autos, convenciones
- Fotografía, lectura, gaming

### **🌍 Eventos Internacionales**
- Conferencias globales, festivales
- Ferias comerciales, eventos diplomáticos

---

## 🔌 **APIs INTEGRADAS (4 PRINCIPALES)**

### **🎫 Eventbrite API**
- Eventos públicos y pagados
- Sistema de tickets integrado

### **🎪 Ticketmaster API** 
- Eventos comerciales y grandes venues
- 230K+ eventos disponibles

### **👥 Meetup API**
- Eventos comunitarios gratuitos
- Networking local

### **📘 Facebook Events API**
- Eventos sociales y trending
- Integración con redes sociales

---

## 📱 **CARACTERÍSTICAS MOBILE-FIRST**

### **🗺️ Geolocalización:**
- GPS + IP geolocation
- Radio de búsqueda: 5km-50km
- Mapas interactivos con clustering

### **📅 Integración Agenda:**
- Google Calendar sync bidireccional
- Outlook y Apple Calendar support
- Detección de conflictos automática

### **🔔 Notificaciones Push:**
- 24h y 1h antes del evento
- Nuevos eventos en categorías favoritas
- Cambios en eventos guardados

### **💾 PWA Completa:**
- Instalable como app nativa
- Offline support para eventos guardados
- Background sync automático

---

## 🎨 **SISTEMA DE TEMPLATES (CLAVE)**

### **Como Funciona (Siguiendo context-test exitoso):**

1. **📄 Pones tu HTML** en `docs/templates/event-card-reference.html`
2. **🤖 Claude lo lee** y copia estructura exacta
3. **🎨 Resultado idéntico** visualmente a tu template
4. **✅ Solo cambia datos** - mantiene todo el diseño

### **Ejemplo de Uso:**
```html
<!-- Tu HTML en templates/event-card-reference.html -->
<div class="bg-white rounded-xl shadow-lg">
  <img class="w-full h-48 object-cover" src="{{event.image}}" />
  <div class="p-4">
    <h3 class="font-bold text-lg">{{event.title}}</h3>
    <p class="text-gray-600">{{event.date}}</p>
  </div>
</div>
```

**Claude genera React component idéntico:**
```jsx
function EventCard({ event }) {
  return (
    <div className="bg-white rounded-xl shadow-lg">
      <img className="w-full h-48 object-cover" src={event.image} />
      <div className="p-4">
        <h3 className="font-bold text-lg">{event.title}</h3>
        <p className="text-gray-600">{event.date}</p>
      </div>
    </div>
  )
}
```

---

## 🎯 **¡LISTO PARA USAR!**

### **Tu Próximo Paso:**
1. **📄 Agrega tu HTML** en `docs/templates/event-card-reference.html`
2. **⚡ Ejecuta**: `/generate-prp docs/setup/INITIAL.md`
3. **👀 Observa** como genera PRP usando tu template
4. **🚀 Implementa**: `/execute-prp PRPs/eventos-visualizer-completo.md`

### **Al Finalizar:**
📱 **¡Tu app de eventos con diseño exacto a tu template HTML!**

---

## 📞 **Información del Proyecto**
- **Tipo:** Mobile-first PWA de eventos
- **Tiempo:** ~3-4 horas total
- **Basado en:** Framework exitoso context-test
- **Clave:** Templates HTML reales (no inventar diseño)

**Estado:** ✅ Listo para recibir tu template HTML y ejecutar
