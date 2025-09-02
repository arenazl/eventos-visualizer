# 🎨 TEMPLATES HTML DE REFERENCIA - CLAVE DEL ÉXITO

Esta carpeta contiene **ejemplos HTML reales** que Claude debe usar como base para el diseño de la aplicación.

## 🔥 REGLA CRÍTICA ABSOLUTA

### **Template Principal Obligatorio:**
- **event-card-reference.html** es el template BASE que el usuario proporcionará
- **NO inventar diseño JAMÁS** - Copiar estructura HTML exacta
- **Solo adaptar contenido dinámico** - Mantener clases CSS y estructura
- **Resultado debe verse idéntico** al template original

## 📁 Templates Disponibles

```
templates/
├── README.md                    # Este archivo con instrucciones
├── SAMPLE-APW.html   # 🔥 TEMPLATE PRINCIPAL (user provides)

```

## 🚨 INSTRUCCIONES OBLIGATORIAS PARA CLAUDE

### **Proceso de Implementación EXACTO:**

#### **1. Leer Template Completo**
```bash
# ANTES DE ESCRIBIR CUALQUIER CÓDIGO:
# 1. Abrir docs/templates/event-card-reference.html  
# 2. Leer TODA la estructura HTML
# 3. Identificar todas las clases CSS
# 4. Entender la jerarquía de elementos
```

#### **2. Copiar Estructura Exacta**
```jsx
// ❌ MAL - Inventar diseño desde cero
function EventCard() {
  return <div className="my-custom-card">...</div>
}

// ✅ BIEN - Copiar template exacto
function EventCard({ event }) {
  // Estructura copiada exactamente de event-card-reference.html
  return (
    <div className="bg-white rounded-xl shadow-lg overf
    low-hidden hover:shadow-xl transition-shadow duration-300">
      <div className="relative aspect-video">
        <img 
          src={event.image} 
          alt={event.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute top-2 right-2">
          <span className="bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-medium">
            {event.category}
          </span>
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-bold text-lg text-gray-900 mb-2">{event.title}</h3>
        <p className="text-sm text-gray-600 mb-2">{event.description}</p>
        <div className="flex items-center text-sm text-gray-500">
          <span>{event.date}</span>
          <span className="mx-2">•</span>
          <span>{event.location}</span>
        </div>
      </div>
    </div>
  )
}
```

#### **3. Validación Visual Obligatoria**
- ✅ **Layout idéntico** al template HTML
- ✅ **Mismos colores** y typography
- ✅ **Mismo spacing** y padding
- ✅ **Mismas animaciones** (hover, transitions)
- ✅ **Solo contenido dinámico** diferente

### **Para Diferentes Frameworks:**

#### **React + TailwindCSS:**
```jsx
// Convertir clases HTML a className de React
// Mantener estructura de DIVs exacta
// Usar {event.property} para datos dinámicos
```

#### **Vanilla HTML:**
```html
<!-- Copiar exactamente -->
<!-- Solo cambiar {{placeholders}} por datos reales -->
```

#### **Vue.js:**
```vue
<template>
  <!-- Estructura exacta del template -->
  <!-- Usar {{ event.property }} para datos -->
</template>
```

## 🎯 Checklist de Validación

### **Antes de considerar componente "terminado":**

- [ ] ¿Abrí y leí el template HTML completamente?
- [ ] ¿Copié la estructura de DIVs exactamente?
- [ ] ¿Usé las mismas clases CSS/TailwindCSS?
- [ ] ¿El resultado se ve idéntico al template?
- [ ] ¿Solo cambié el contenido dinámico ({{placeholders}})?
- [ ] ¿Funciona responsive igual que el template?
- [ ] ¿Las animaciones son las mismas?

## 📝 Ejemplo de Template HTML

### **event-card-reference.html (Usuario debe reemplazar):**
```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Event Card Template</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-4 bg-gray-100">
  
  <!-- TEMPLATE PRINCIPAL - COPIAR ESTA ESTRUCTURA -->
  <div class="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 max-w-sm">
    <!-- Image Section -->
    <div class="relative aspect-video">
      <img 
        src="{{event.image}}" 
        alt="{{event.title}}"
        class="w-full h-full object-cover"
      >
      <!-- Category Badge -->
      <div class="absolute top-2 right-2">
        <span class="bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-medium">
          {{event.category}}
        </span>
      </div>
      <!-- Price Badge -->
      <div class="absolute bottom-2 left-2">
        <span class="bg-green-600 text-white px-2 py-1 rounded-lg text-sm font-bold">
          {{event.price}}
        </span>
      </div>
    </div>
    
    <!-- Content Section -->
    <div class="p-4">
      <!-- Title -->
      <h3 class="font-bold text-lg text-gray-900 mb-2 line-clamp-2">
        {{event.title}}
      </h3>
      
      <!-- Description -->
      <p class="text-sm text-gray-600 mb-3 line-clamp-2">
        {{event.description}}
      </p>
      
      <!-- Date & Location -->
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span>{{event.date}}</span>
        <span class="mx-2">•</span>
        <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
        </svg>
        <span>{{event.location}}</span>
      </div>
      
      <!-- Action Buttons -->
      <div class="flex space-x-2">
        <button class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors">
          Ver Detalles
        </button>
        <button class="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          <svg class="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
          </svg>
        </button>
      </div>
    </div>
  </div>

</body>
</html>
```

## 🔥 RECORDATORIO FINAL

### **ÉXITO = COPIAR TEMPLATE EXACTO**
### **FRACASO = INVENTAR DISEÑO PROPIO**

**El usuario pondrá su HTML en event-card-reference.html**  
**Claude DEBE copiar esa estructura al 100%**  
**Solo cambiar {{placeholders}} por datos reales**

---

**Esta es la diferencia entre el éxito (context-test) y el fracaso (frameworks genéricos)**
