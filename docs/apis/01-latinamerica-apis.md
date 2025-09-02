<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-09-01 17:45
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-09-01 17:45: Reorganización docs + audit header agregado
- 2025-08-28 00:51: Documentación completa APIs Latinoamérica
📋 TAGS: #apis #latinamerica #eventos #integraciones
-->

# 🌎 APIS DE EVENTOS - LATINOAMÉRICA Y MUNDIAL
## Clasificación Completa: Gratuitas, Pagas y Scraping

---

## 🆓 APIS GRATUITAS (PRIORIDAD ALTA)

### 🌟 LATINOAMÉRICA - APIS GRATUITAS

#### 🇦🇷 **ARGENTINA**

1. **Buenos Aires Data (Gobierno Ciudad)**
   - **URL**: https://data.buenosaires.gob.ar
   - **Endpoints**: 
     - `/dataset/agenda-cultural` - Eventos culturales
     - `/dataset/actividades-culturales` - Actividades gratuitas
   - **Límite**: Sin límite
   - **Auth**: No requiere
   - **Datos**: Teatro, música, arte, festivales gratuitos
   ```python
   GET https://cdn.buenosaires.gob.ar/datosabiertos/datasets/cultura/agenda-cultural/agenda-cultural.json
   ```

2. **AllEvents Argentina** 
   - **URL**: https://allevents.in/argentina
   - **API**: https://allevents.in/api/v2/
   - **Límite**: 100 req/día gratis
   - **Auth**: API Key gratuita
   - **Ciudades**: Buenos Aires, Córdoba, Rosario, Mendoza

3. **Cultura.gob.ar**
   - **URL**: https://www.cultura.gob.ar/api/
   - **Datos**: Eventos culturales nacionales
   - **Auth**: No requiere

#### 🇲🇽 **MÉXICO**

4. **CDMX Cultura API**
   - **URL**: https://datos.cdmx.gob.mx
   - **Endpoints**: `/dataset/cartelera-cultural`
   - **Datos**: Eventos Ciudad de México
   - **Auth**: No requiere

5. **Ticketmaster México API**
   - **URL**: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
   - **Límite**: 5000 req/día
   - **Auth**: API Key gratuita
   - **Cobertura**: Todo México

6. **Boletia API** (Semi-pública)
   - **URL**: https://boletia.com
   - **Método**: JSON endpoints públicos
   - **Datos**: Conciertos, teatro, deportes

#### 🇨🇴 **COLOMBIA**

7. **Datos Abiertos Colombia**
   - **URL**: https://www.datos.gov.co
   - **Dataset**: Agenda cultural Bogotá
   - **Auth**: No requiere

8. **TuBoleta Colombia** (Endpoints públicos)
   - **URL**: https://www.tuboleta.com
   - **Método**: API REST no documentada pero accesible
   ```python
   GET https://www.tuboleta.com/api/events/city/bogota
   ```

#### 🇨🇱 **CHILE**

9. **PuntoTicket API** (No oficial)
   - **URL**: https://www.puntoticket.com
   - **Endpoints descubiertos**: `/api/eventos/santiago`
   - **Auth**: No requiere para lectura

10. **Santiago Cultura**
    - **URL**: https://www.santiagocapital.cl/api/eventos
    - **Datos**: Eventos gratuitos Santiago

#### 🇧🇷 **BRASIL**

11. **Sympla API**
    - **URL**: https://developers.sympla.com.br
    - **Límite**: 1000 req/hora (gratis)
    - **Auth**: OAuth2
    - **Datos**: Eventos, workshops, conferencias

12. **São Paulo Aberta**
    - **URL**: http://dados.prefeitura.sp.gov.br
    - **Dataset**: Agenda cultural SP
    - **Auth**: No requiere

#### 🇵🇪 **PERÚ**

13. **Joinnus API** (No oficial)
    - **URL**: https://www.joinnus.com
    - **Endpoints**: `/api/events/lima`
    - **Método**: Scraping JSON

14. **Teleticket Perú**
    - **URL**: https://teleticket.com.pe
    - **Método**: Endpoints JSON públicos

#### 🇺🇾 **URUGUAY**

15. **RedTickets Uruguay**
    - **URL**: https://redtickets.uy
    - **API**: Endpoints REST públicos
    - **Datos**: Eventos Montevideo

16. **Montevideo Cultura**
    - **URL**: https://montevideo.gub.uy/api/cultura
    - **Auth**: No requiere

---

### 🌍 APIS INTERNACIONALES GRATUITAS

17. **Eventbrite API** ⭐⭐⭐⭐⭐
    - **URL**: https://www.eventbrite.com/platform/api
    - **Límite**: 1000 req/hora
    - **Cobertura**: Global, fuerte en LATAM
    - **Auth**: OAuth2
    ```python
    GET https://www.eventbriteapi.com/v3/events/search/?location.address=Buenos+Aires
    ```

18. **Meetup GraphQL API**
    - **URL**: https://www.meetup.com/api
    - **Límite**: Variable
    - **Cobertura**: Global
    - **Auth**: OAuth2

19. **Bandsintown API**
    - **URL**: https://www.artists.bandsintown.com/support/api-installation
    - **Gratis**: Para apps no comerciales
    - **Datos**: Conciertos mundiales
    ```python
    GET https://rest.bandsintown.com/artists/{artist}/events?app_id=YOUR_APP_ID
    ```

20. **SeatGeek API**
    - **URL**: https://platform.seatgeek.com
    - **Límite**: 1000 req/mes gratis
    - **Auth**: Client ID

21. **Songkick API**
    - **URL**: https://www.songkick.com/developer
    - **Límite**: Por aplicación
    - **Datos**: Conciertos, tours

22. **AllEvents.in Global**
    - **URL**: https://allevents.in/api/
    - **Límite**: 100 req/día
    - **Cobertura**: 40+ países

23. **10times API** (Conferencias)
    - **URL**: https://10times.com/api
    - **Datos**: Conferencias, expos, ferias
    - **Límite**: 500 req/día

---

## 💰 APIS PAGAS (OPCIONAL)

### TIER 1 - BAJO COSTO ($10-50/mes)

24. **PredictHQ** 
    - **Precio**: $49/mes starter
    - **Ventaja**: Data normalizada, 19M+ eventos
    - **Cobertura**: Global incluyendo LATAM

25. **Ticketmaster Partner API**
    - **Precio**: $25/mes pro
    - **Ventaja**: Inventory real-time
    
26. **StubHub API Pro**
    - **Precio**: $30/mes
    - **Ventaja**: Secondary market data

### TIER 2 - EMPRESARIAL ($100+/mes)

27. **SeatGeek Enterprise**
    - **Precio**: $299/mes
    - **Ventaja**: Full inventory access

28. **Eventbrite Premium**
    - **Precio**: $99/mes
    - **Ventaja**: Sin límites de rate

29. **Facebook Events API** (Business)
    - **Precio**: Variable
    - **Restricción**: Solo para partners verificados

---

## 🕷️ SITIOS PARA SCRAPING (LATINOAMÉRICA)

### 🇦🇷 ARGENTINA - SCRAPING

```python
ARGENTINA_SCRAPING = {
    # Ticketing
    "ticketek": "https://www.ticketek.com.ar",
    "plateanet": "https://www.plateanet.com",
    "tickethoy": "https://tickethoy.com.ar",
    "entrada1": "https://www.entrada1.com.ar",
    
    # Teatros Buenos Aires
    "alternativa_teatral": "https://www.alternativateatral.com",
    "teatro_colon": "https://teatrocolon.org.ar",
    "complejo_teatral": "https://complejoteatral.gob.ar",
    "paseo_la_plaza": "https://www.paseolaaplaza.com.ar",
    "teatro_gran_rex": "https://www.teatrogranrex.com.ar",
    "teatro_opera": "https://teatroopera.com.ar",
    
    # Música/Clubs
    "la_trastienda": "https://www.latrastienda.com",
    "niceto_club": "https://www.nicetoclub.com",
    "luna_park": "https://www.lunapark.com.ar",
    "estadio_obras": "https://www.estadioobras.com.ar",
    "teatro_vorterix": "https://www.teatrovorterix.com",
    "quality_espacio": "https://www.qualityespacio.com.ar",
    "konex": "https://www.ciudadculturalkonex.com",
    
    # Centros Culturales
    "centro_cultural_recoleta": "https://www.centroculturalrecoleta.org",
    "usina_del_arte": "https://www.usinadelarte.org",
    "cck": "https://www.cck.gob.ar",
    "malba": "https://www.malba.org.ar",
    
    # Guías/Agregadores
    "voy_de_viaje": "https://www.voydeviaje.com.ar",
    "buenos_aires_ciudad": "https://turismo.buenosaires.gob.ar",
    "timeout_ba": "https://www.timeout.com/buenos-aires",
    "la_nacion_espectaculos": "https://www.lanacion.com.ar/espectaculos",
}
```

### 🇲🇽 MÉXICO - SCRAPING

```python
MEXICO_SCRAPING = {
    "ticketmaster_mx": "https://www.ticketmaster.com.mx",
    "boletia": "https://boletia.com",
    "superboletos": "https://www.superboletos.com",
    "stubhub_mx": "https://www.stubhub.com.mx",
    "eticket": "https://www.eticket.mx",
    "ticketbis_mx": "https://www.ticketbis.com.mx",
    
    # Venues CDMX
    "palacio_deportes": "https://www.palaciodelosdeportes.mx",
    "foro_sol": "https://www.forosol.com.mx",
    "teatro_metropolitan": "https://teatrometropolitan.com.mx",
    "auditorio_nacional": "https://www.auditorio.com.mx",
}
```

### 🇨🇴 COLOMBIA - SCRAPING

```python
COLOMBIA_SCRAPING = {
    "tuboleta": "https://www.tuboleta.com",
    "primerafi la": "https://www.primerafila.com.co",
    "eticket_co": "https://www.eticket.co",
    "colboletos": "https://www.colboletos.com",
    
    # Venues Bogotá
    "teatro_colon_bogota": "https://teatrocolon.gov.co",
    "movistar_arena": "https://www.movistararena.co",
}
```

### 🇨🇱 CHILE - SCRAPING

```python
CHILE_SCRAPING = {
    "puntoticket": "https://www.puntoticket.com",
    "ticketek_cl": "https://www.ticketek.cl",
    "passline_cl": "https://www.passline.cl",
    "ticketpro": "https://www.ticketpro.cl",
    
    # Venues Santiago
    "teatro_municipal": "https://www.municipal.cl",
    "movistar_arena_cl": "https://www.movistararena.cl",
    "teatro_caupolican": "https://www.teatrocaupolican.cl",
}
```

### 🇧🇷 BRASIL - SCRAPING

```python
BRASIL_SCRAPING = {
    "sympla": "https://www.sympla.com.br",
    "ingresso": "https://www.ingresso.com",
    "blueticket": "https://www.blueticket.com.br",
    "eventim": "https://www.eventim.com.br",
    "bilheteriadigital": "https://www.bilheteriadigital.com",
    
    # São Paulo
    "teatro_municipal_sp": "https://theatromunicipal.org.br",
    "casas_shows": "https://www.guiadasemana.com.br",
}
```

---

## 🚀 ESTRATEGIA DE IMPLEMENTACIÓN RECOMENDADA

### FASE 1: APIs Gratuitas LATAM (Semana 1)
1. ✅ **Buenos Aires Data** (Argentina)
2. ✅ **Eventbrite API** (Global/LATAM)  
3. ✅ **Ticketmaster México**
4. ✅ **Sympla** (Brasil)
5. ✅ **AllEvents** (Argentina/Global)

### FASE 2: Scraping Principales (Semana 2)
1. 🕷️ **Ticketek Argentina**
2. 🕷️ **Alternativa Teatral**
3. 🕷️ **TuBoleta Colombia**
4. 🕷️ **PuntoTicket Chile**

### FASE 3: APIs Internacionales (Semana 3)
1. ✅ **Meetup**
2. ✅ **Bandsintown**
3. ✅ **SeatGeek**
4. ✅ **Songkick**

### FASE 4: Scraping Venues (Semana 4)
1. 🕷️ Teatros principales cada país
2. 🕷️ Clubs de música
3. 🕷️ Centros culturales

---

## 📊 COBERTURA ESPERADA

| País | APIs Gratuitas | Scraping | Total Fuentes |
|------|---------------|----------|---------------|
| 🇦🇷 Argentina | 5 | 25+ | 30+ |
| 🇲🇽 México | 4 | 15+ | 19+ |
| 🇨🇴 Colombia | 3 | 10+ | 13+ |
| 🇨🇱 Chile | 3 | 8+ | 11+ |
| 🇧🇷 Brasil | 3 | 12+ | 15+ |
| 🇵🇪 Perú | 2 | 5+ | 7+ |
| 🇺🇾 Uruguay | 2 | 3+ | 5+ |

**TOTAL: 100+ fuentes de datos**

---

## 🔧 CÓDIGO DE INICIO RÁPIDO

```python
# backend/services/latam_aggregator.py

class LatamEventAggregator:
    def __init__(self):
        self.sources = {
            # APIs Gratuitas prioritarias
            'buenos_aires_data': BuenosAiresDataConnector(),
            'eventbrite': EventbriteConnector(),
            'ticketmaster_mx': TicketmasterMXConnector(),
            'sympla': SymplaConnector(),
            
            # Scrapers principales
            'ticketek_ar': TicketekArgentinaScraper(),
            'alternativa_teatral': AlternativaTeatralScraper(),
            'tuboleta': TuBoletaScraper(),
        }
    
    async def fetch_argentina_events(self):
        """Obtiene todos los eventos de Argentina"""
        tasks = [
            self.sources['buenos_aires_data'].fetch(),
            self.sources['eventbrite'].fetch(location='Buenos Aires'),
            self.sources['ticketek_ar'].scrape(),
            self.sources['alternativa_teatral'].scrape(),
        ]
        
        results = await asyncio.gather(*tasks)
        return self.normalize_and_dedupe(results)
```

---

## 📝 NOTAS IMPORTANTES

1. **Priorizar APIs gratuitas** antes que scraping
2. **Buenos Aires Data** es excelente para eventos gratuitos/culturales
3. **Eventbrite** tiene la mejor cobertura en LATAM
4. **Sympla** domina Brasil
5. **Ticketmaster** solo México tiene buena API
6. Para Argentina, Colombia, Chile: combinar APIs + scraping
7. **Rate limiting**: Respetar límites de cada API
8. **Cache agresivo**: 30-60 minutos mínimo

---