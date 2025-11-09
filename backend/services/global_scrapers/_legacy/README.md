# 🗄️ SCRAPERS LEGACY - Archivados

## ⚠️ ESTOS SCRAPERS NO SE USAN

Estos scrapers fueron movidos a `_legacy/` porque:
- Tienen errores de implementación
- Timeouts constantes sin resultados
- No cumplen con la interfaz BaseGlobalScraper
- Estrategia cambió a **calidad > cantidad**

---

## 📋 SCRAPERS ARCHIVADOS (12 total)

### ❌ **ERRORES DE IMPORTACIÓN (7 scrapers):**
1. **allevents_scraper.py** - `module has no attribute 'AlleventsScraper'`
2. **facebook_auth_scraper.py** - `module has no attribute 'Facebook_AuthScraper'`
3. **residentadvisor_scraper.py** - `module has no attribute 'ResidentadvisorScraper'`
4. **stubhub_scraper.py** - `module has no attribute 'StubhubScraper'`
5. **ticketleap_scraper.py** - `module has no attribute 'TicketleapScraper'`
6. **ticketmaster_scraper.py** - `module has no attribute 'TicketmasterScraper'`
   - **NOTA**: Reemplazar con Ticketmaster API oficial
7. **ticombo_scraper.py** - `module has no attribute 'TicomboScraper'`

### ⛔ **DESHABILITADOS POR TIMEOUTS (4 scrapers):**
8. **bandsintown_scraper.py** - Timeout constante (5s), sin eventos
9. **dice_scraper.py** - Timeout constante (5s), sin eventos
10. **events_scraper.py** - Muy lento (5s) sin resultados
11. **universe_scraper.py** - Timeout constante (5s), sin eventos

### ⚠️ **PROBLEMA DE HERENCIA (1 scraper):**
12. **showpass_scraper.py** - No hereda de BaseGlobalScraper correctamente

---

## ✅ SCRAPERS ACTIVOS (Solo 5 - Funcionando)

Los únicos scrapers que quedaron activos en `/global_scrapers/`:

1. ✅ **eventbrite_scraper.py** - Eventos variados, confirmado funcionando
2. ✅ **facebook_scraper.py** - Eventos de Facebook
3. ✅ **fever_scraper.py** - Eventos culturales/experiencias
4. ✅ **meetup_scraper.py** - Eventos comunitarios
5. ✅ **songkick_scraper.py** - Conciertos/música

---

## 🚀 PRÓXIMOS PASOS

**En lugar de arreglar estos 12 scrapers rotos, implementar:**

1. **Ticketmaster Discovery API** (5K llamadas/día gratis) - Reemplaza ticketmaster_scraper.py
2. **SeatGeek API** (agregador de 60+ plataformas)
3. **Gemini como scraper universal** - La estrategia clave 🔑

---

## 🔄 SI SE NECESITAN EN EL FUTURO

Si algún día se decide volver a usar alguno de estos scrapers:

1. Arreglar errores de importación (revisar nombres de clases)
2. Optimizar timeouts y parsing
3. Verificar que heredan de BaseGlobalScraper
4. Agregar tests antes de reactivar

**Por ahora: IGNORAR - Enfocarnos en calidad > cantidad**

---

**Fecha de archivo:** 2025-01-12
**Razón:** Estrategia cambió a APIs oficiales + Gemini scraper universal
