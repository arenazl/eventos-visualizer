# 🔄 CAMBIO URGENTE: Usar MySQL en vez de Gemini

## Archivo a Modificar:
`c:\Code\eventos-visualizer\backend\main.py`

## Ubicación:
Líneas **1037 a 1084** (función `event_generator()` dentro de `@app.get("/api/events/stream")`)

## Cambio Requerido:

### REEMPLAZAR ESTA FUNCIÓN:
```python
async def event_generator():
    """Generator para SSE"""
    try:
        if not location:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Ubicación requerida'})}\n\n"
            return

        # Enviar evento de inicio
        yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos en {location}', 'location': location})}\n\n"

        # Import dentro de la función para evitar circular imports
        from services.gemini_factory import gemini_factory

        factory = gemini_factory
        total_events = 0
        scrapers_completed = 0

        # 🔥 STREAMING: Usa async for para procesar resultados apenas estén listos
        async for result in factory.execute_streaming(location=location, category=category, limit=limit):
            scrapers_completed += 1

            scraper_name = result.get('scraper', 'unknown')
            events = result.get('events', [])
            events_count = len(events)
            success = result.get('success', False)
            error = result.get('error')
            execution_time = result.get('execution_time', '0.0s')

            total_events += events_count

            if success and events_count > 0:
                yield f"data: {json.dumps({'type': 'events', 'scraper': scraper_name, 'events': events, 'count': events_count, 'total_events': total_events, 'execution_time': execution_time})}\n\n"
                logger.info(f"📡 SSE: {scraper_name} - {events_count} eventos enviados en {execution_time}")
            elif success:
                yield f"data: {json.dumps({'type': 'no_events', 'scraper': scraper_name, 'count': 0, 'execution_time': execution_time})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'scraper_error', 'scraper': scraper_name, 'error': error, 'execution_time': execution_time})}\n\n"

        yield f"data: {json.dumps({'type': 'complete', 'total_events': total_events, 'scrapers_completed': scrapers_completed})}\n\n"
        logger.info(f"🏁 SSE: Streaming completado - {total_events} eventos, {scrapers_completed} scrapers")

    except Exception as e:
        logger.error(f"❌ Error en SSE streaming: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
```

### POR ESTA NUEVA VERSIÓN (CONSULTA MYSQL):
```python
async def event_generator():
    """Generator para SSE - Consulta MySQL en vez de Gemini"""
    import time
    try:
        if not location:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Ubicación requerida'})}\n\n"
            return

        # Enviar evento de inicio
        yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos en {location}', 'location': location})}\n\n"

        # 🗄️ BUSCAR EN MYSQL EN VEZ DE GEMINI
        from services.events_db_service import search_events_by_location

        start_time = time.time()
        logger.info(f"🔍 Consultando MySQL para ubicación: {location}")

        # Consultar base de datos
        events = await search_events_by_location(
            location=location,
            category=category,
            limit=limit,
            days_ahead=90
        )

        execution_time = f"{time.time() - start_time:.2f}s"
        total_events = len(events)

        if total_events > 0:
            # Enviar eventos desde base de datos
            yield f"data: {json.dumps({'type': 'events', 'scraper': 'mysql_database', 'events': events, 'count': total_events, 'total_events': total_events, 'execution_time': execution_time})}\n\n"
            logger.info(f"📡 SSE: MySQL - {total_events} eventos enviados en {execution_time}")
        else:
            # No se encontraron eventos
            yield f"data: {json.dumps({'type': 'no_events', 'scraper': 'mysql_database', 'count': 0, 'execution_time': execution_time, 'message': f'No hay eventos disponibles para {location}'})}\n\n"
            logger.info(f"📡 SSE: MySQL - 0 eventos para '{location}' en {execution_time}")

        # Enviar evento de completado
        yield f"data: {json.dumps({'type': 'complete', 'total_events': total_events, 'scrapers_completed': 1})}\n\n"
        logger.info(f"🏁 SSE: Streaming completado - {total_events} eventos desde MySQL")

    except Exception as e:
        logger.error(f"❌ Error en SSE streaming desde MySQL: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
```

## 🚀 Después del cambio:

1. **Guardar** el archivo
2. **Reiniciar** el servidor (Ctrl+C y `python main.py`)
3. **Probar** con: `curl "http://localhost:8001/api/events/stream?location=Miami&limit=5"`

## ✅ Resultado Esperado:
- Debería retornar eventos de Miami desde MySQL en < 1 segundo
- Logs mostrarán: `🔍 Consultando MySQL para ubicación: Miami`
- Eventos reales de la base de datos (no de Gemini)
