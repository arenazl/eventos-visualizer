"""
🧹 Daily Cleanup Process - Limpieza diaria de eventos vencidos
Proceso automático que se ejecuta a las 4:00 AM para limpiar eventos pasados
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DailyCleanupManager:
    """
    🧹 Gestor de limpieza diaria - elimina eventos vencidos
    """
    
    def __init__(self):
        self.cleanup_hour = 4  # 4:00 AM
        self.retention_days = 1  # Eliminar eventos con más de 1 día vencidos
        
        # Paths para archivos de cache que necesitan limpieza
        self.cache_files = [
            "/mnt/c/Code/eventos-visualizer/backend/data/facebook_events_cache.json",
            "/mnt/c/Code/eventos-visualizer/backend/data/eventbrite_cache.json",
            "/mnt/c/Code/eventos-visualizer/backend/data/multi_source_cache.json"
        ]
        
    async def run_daily_cleanup(self) -> Dict[str, Any]:
        """
        🧹 Ejecutar limpieza completa diaria
        """
        start_time = datetime.now()
        logger.info("🧹 INICIANDO LIMPIEZA DIARIA DE EVENTOS")
        
        results = {
            "timestamp": start_time.isoformat(),
            "cache_files_cleaned": 0,
            "expired_events_removed": 0,
            "total_processing_time": 0,
            "errors": [],
            "status": "success"
        }
        
        try:
            # 1. Limpiar archivos de cache
            cache_result = await self._cleanup_cache_files()
            results["cache_files_cleaned"] = cache_result["files_processed"]
            results["expired_events_removed"] = cache_result["events_removed"]
            
            # 2. Si hay base de datos conectada, limpiar también
            if await self._is_database_available():
                db_result = await self._cleanup_database_events()
                results["database_events_removed"] = db_result["events_removed"]
            
            # 3. Log de estadísticas
            processing_time = (datetime.now() - start_time).total_seconds()
            results["total_processing_time"] = processing_time
            
            logger.info(f"✅ LIMPIEZA COMPLETADA:")
            logger.info(f"   📁 Archivos cache procesados: {results['cache_files_cleaned']}")
            logger.info(f"   🗑️ Eventos expirados eliminados: {results['expired_events_removed']}")
            logger.info(f"   ⏱️ Tiempo total: {processing_time:.2f}s")
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ Error en limpieza diaria: {e}")
        
        return results
    
    async def _cleanup_cache_files(self) -> Dict[str, Any]:
        """
        🗑️ Limpiar eventos expirados de archivos de cache
        """
        files_processed = 0
        total_events_removed = 0
        cutoff_datetime = datetime.now() - timedelta(days=self.retention_days)
        
        for cache_file in self.cache_files:
            try:
                if not os.path.exists(cache_file):
                    continue
                    
                # Leer cache actual
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if not cache_data:
                    continue
                
                # Procesar según estructura del cache
                events_removed = 0
                
                if "events" in cache_data:
                    # Cache con estructura {events: [...], cache_info: {...}}
                    original_count = len(cache_data["events"])
                    cache_data["events"] = self._filter_expired_events(
                        cache_data["events"], cutoff_datetime
                    )
                    events_removed = original_count - len(cache_data["events"])
                
                elif isinstance(cache_data, list):
                    # Cache que es directamente lista de eventos
                    original_count = len(cache_data)
                    cache_data = self._filter_expired_events(cache_data, cutoff_datetime)
                    events_removed = original_count - len(cache_data)
                
                # Actualizar timestamp de cache
                if "cache_info" in cache_data:
                    cache_data["cache_info"]["last_cleanup"] = datetime.now().isoformat()
                
                # Escribir cache limpio
                if events_removed > 0:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"🧹 {os.path.basename(cache_file)}: {events_removed} eventos expirados eliminados")
                
                files_processed += 1
                total_events_removed += events_removed
                
            except Exception as e:
                logger.error(f"❌ Error limpiando {cache_file}: {e}")
                continue
        
        return {
            "files_processed": files_processed,
            "events_removed": total_events_removed
        }
    
    def _filter_expired_events(self, events: List[Dict], cutoff_datetime: datetime) -> List[Dict]:
        """
        🔍 Filtrar eventos que no han expirado
        """
        filtered_events = []
        
        for event in events:
            try:
                # Buscar fecha de fin del evento
                end_date_str = None
                
                # Intentar diferentes campos de fecha
                for date_field in ["end_datetime", "end_date", "date_end", "fecha_fin", "start_datetime", "start_date", "date"]:
                    if date_field in event and event[date_field]:
                        end_date_str = event[date_field]
                        break
                
                if not end_date_str:
                    # Si no tiene fecha, mantenerlo (podría ser evento permanente)
                    filtered_events.append(event)
                    continue
                
                # Parsear fecha
                try:
                    # Intentar diferentes formatos
                    for date_format in [
                        "%Y-%m-%dT%H:%M:%S.%f",      # 2025-08-31T14:30:45.123456
                        "%Y-%m-%dT%H:%M:%S",         # 2025-08-31T14:30:45
                        "%Y-%m-%d %H:%M:%S",         # 2025-08-31 14:30:45
                        "%Y-%m-%d",                  # 2025-08-31
                        "%d/%m/%Y",                  # 31/08/2025
                    ]:
                        try:
                            event_datetime = datetime.strptime(end_date_str, date_format)
                            break
                        except ValueError:
                            continue
                    else:
                        # Si no pudo parsear, mantener el evento
                        filtered_events.append(event)
                        continue
                    
                    # Solo mantener eventos que no han expirado hace más del retention_days
                    if event_datetime >= cutoff_datetime:
                        filtered_events.append(event)
                        
                except Exception as parse_error:
                    # Si hay error parseando, mantener el evento por seguridad
                    filtered_events.append(event)
                    logger.debug(f"🔍 No se pudo parsear fecha '{end_date_str}': {parse_error}")
                    
            except Exception as e:
                # Si hay cualquier error, mantener el evento por seguridad
                filtered_events.append(event)
                logger.debug(f"🔍 Error procesando evento: {e}")
        
        return filtered_events
    
    async def _is_database_available(self) -> bool:
        """
        🔍 Verificar si hay base de datos disponible
        """
        try:
            # TODO: Agregar lógica de conexión a PostgreSQL cuando esté configurada
            return False
        except:
            return False
    
    async def _cleanup_database_events(self) -> Dict[str, Any]:
        """
        🗑️ Limpiar eventos expirados de base de datos PostgreSQL
        """
        # TODO: Implementar cuando PostgreSQL esté configurada
        return {"events_removed": 0}
    
    def should_run_cleanup(self) -> bool:
        """
        🕐 Verificar si es hora de ejecutar la limpieza
        """
        now = datetime.now()
        return now.hour == self.cleanup_hour
    
    async def schedule_daily_cleanup(self):
        """
        ⏰ Scheduler que ejecuta limpieza diaria automáticamente
        """
        logger.info(f"⏰ Scheduler de limpieza iniciado - se ejecutará a las {self.cleanup_hour}:00")
        
        while True:
            try:
                if self.should_run_cleanup():
                    await self.run_daily_cleanup()
                    
                    # Esperar hasta el día siguiente para evitar múltiples ejecuciones
                    await asyncio.sleep(3600)  # Esperar 1 hora
                else:
                    # Verificar cada 10 minutos si es hora de limpiar
                    await asyncio.sleep(600)  # 10 minutos
                    
            except Exception as e:
                logger.error(f"❌ Error en scheduler de limpieza: {e}")
                await asyncio.sleep(600)  # Esperar 10 minutos antes de reintentar


# 🎯 FUNCIÓN PARA EJECUTAR LIMPIEZA MANUAL
async def run_manual_cleanup() -> Dict[str, Any]:
    """
    🧹 Ejecutar limpieza manual (para testing o comando directo)
    """
    cleanup_manager = DailyCleanupManager()
    return await cleanup_manager.run_daily_cleanup()


# 🎯 FUNCIÓN PARA INICIAR SCHEDULER AUTOMÁTICO
async def start_cleanup_scheduler():
    """
    ⏰ Iniciar el scheduler automático de limpieza
    """
    cleanup_manager = DailyCleanupManager()
    await cleanup_manager.schedule_daily_cleanup()


if __name__ == "__main__":
    # Para testing - ejecutar limpieza manual
    import asyncio
    
    async def test_cleanup():
        result = await run_manual_cleanup()
        print("🧹 Resultado de limpieza manual:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_cleanup())