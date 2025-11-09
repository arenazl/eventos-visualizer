# 🚀 START HERE - Setup en 3 minutos

**Sistema de eventos con MySQL en la nube - REALISTA**

---

## ⚡ 3 PASOS RÁPIDOS:

### 1️⃣ Configurar .env (1 min)

```bash
# Copiar ejemplo
cp backend/.env.example backend/.env
```

Editar `backend/.env` y cambiar esta línea con tus credenciales de MySQL:

```bash
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE

# Ejemplo real:
# DATABASE_URL=mysql+pymysql://root:MiPass123@mysql.railway.app:3306/railway
```

### 2️⃣ Instalar pymysql (30 segs)

```bash
pip install pymysql
```

### 3️⃣ Crear tablas (30 segs)

```bash
cd backend/batch
python setup_database.py
```

Verás:
```
🗄️  SETUP DE BASE DE DATOS
📊 Tipo: MySQL
✅ Tablas creadas: events, cities
✅ 24 ciudades cargadas
🎉 SETUP COMPLETADO
```

---

## ✅ ¡LISTO! Ahora podés:

### Iniciar el backend:
```bash
cd backend
python main.py
```

### Verificar que funciona:
```bash
curl http://localhost:8001/api/db/events/stats
```

Deberías ver:
```json
{
  "total_events": 0,
  "upcoming_events": 0,
  "top_cities": []
}
```

---

## 🎯 PRÓXIMO PASO: Primer Evento

### Con Claude Desktop:

1. Abre Claude Desktop
2. Decile: "Usá BrightData para scrapear 3 eventos en Buenos Aires para diciembre 2025. Dame JSON con esta estructura: {...}"
3. Guarda el JSON en: `backend/data/scraped/buenos_aires.json`
4. Ejecuta:
```bash
cd backend/batch
python upload_scraped_events.py ../data/scraped/buenos_aires.json
```

5. Verifica:
```bash
curl "http://localhost:8001/api/db/events/?city=Buenos%20Aires"
```

---

## 📚 DOCUMENTACIÓN COMPLETA:

- **[MYSQL_SETUP.md](backend/batch/MYSQL_SETUP.md)** - Guía completa MySQL
- **[MANUAL_WORKFLOW.md](backend/batch/MANUAL_WORKFLOW.md)** - Workflow semanal
- **[QUICK_START.md](backend/batch/QUICK_START.md)** - PostgreSQL (si preferís)

---

## 💡 CONCEPTOS CLAVE:

### ¿Por qué MySQL en la nube?
- ✅ No instalás nada local
- ✅ Acceso desde cualquier lado
- ✅ Gratis (Railway, TiDB, PlanetScale)

### ¿Por qué manual?
- ❌ BrightData NO tiene API programable
- ✅ Solo funciona con Claude Desktop manualmente
- ✅ 30 mins por semana es realista y sustentable

### ¿Cómo funciona?
```
TÚ (15 mins/semana)
  ↓ Claude Desktop + BrightData
  ↓ Scrapea eventos
  ↓ JSON
  ↓ python upload_scraped_events.py
  ↓
MySQL (en la nube)
  ↓
USUARIOS consultan < 100ms
  ✅ Sin esperar 30 segundos
```

---

## 🔧 SI ALGO FALLA:

### "No module named 'pymysql'"
```bash
pip install pymysql
```

### "Access denied for user"
- Verificar credenciales en `.env`
- User, password, host deben ser correctos

### "Can't connect to MySQL server"
- Verificar host y puerto
- Algunos proveedores tienen host interno vs externo

---

## 🎉 SISTEMA LISTO

Con 3 comandos ya tenés:
- ✅ MySQL conectado
- ✅ Tablas creadas
- ✅ 24 ciudades cargadas
- ✅ API lista para recibir eventos
- ✅ Consultas rápidas funcionando

**Solo falta scrapear eventos con Claude Desktop y subirlos!**

---

**Próximo paso**: Abrir Claude Desktop y scrapear tu primera ciudad 🚀
