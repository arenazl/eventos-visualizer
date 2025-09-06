#!/usr/bin/env python3
"""
Gestor de Contexto del Proyecto usando MCP Memory Server
Almacena y recupera información importante del proyecto Eventos Visualizer
"""

import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

class ProjectContext:
    """
    Gestiona el contexto del proyecto usando el Knowledge Graph Memory Server
    """
    
    def __init__(self):
        self.project_name = "Eventos Visualizer"
        self.entities = {}
        self.relations = []
        self.context_file = "project_context.json"
        
    def initialize_project_context(self):
        """
        Inicializa el contexto básico del proyecto
        """
        # Entidad principal: El proyecto
        self.add_entity(
            name="EventosVisualizer",
            entity_type="project",
            observations=[
                "Sistema de agregación de eventos de múltiples fuentes",
                "Usa FastAPI para el backend en puerto 8001",
                "Frontend React + Vite en puerto 5174",
                "Base de datos PostgreSQL con PostGIS",
                "APIs integradas: Eventbrite, Ticketmaster, Meetup, Facebook",
                "Implementa PWA con service workers",
                "WebSockets para notificaciones en tiempo real",
                "IP WSL: 172.29.228.80",
                "Proyecto iniciado en Agosto 2025"
            ]
        )
        
        # Tecnologías principales
        self.add_entity(
            name="Backend",
            entity_type="component",
            observations=[
                "FastAPI framework",
                "Python 3.12",
                "Puerto 8001 INMUTABLE",
                "Archivo principal: main.py",
                "Middleware de timeout: 8 segundos",
                "Pool de conexiones PostgreSQL: 20",
                "Scraping con CloudScraper instalado",
                "Pattern Service para análisis de tendencias"
            ]
        )
        
        self.add_entity(
            name="Frontend",
            entity_type="component",
            observations=[
                "React 18 con Vite",
                "TypeScript",
                "Puerto 5174 INMUTABLE",
                "Tailwind CSS para estilos",
                "Zustand para estado global",
                "React Router para navegación",
                "PWA con offline support",
                "Mobile-first design"
            ]
        )
        
        self.add_entity(
            name="Database",
            entity_type="component",
            observations=[
                "PostgreSQL 14+ con PostGIS",
                "Tablas: events, users, user_events",
                "Geolocalización con lat/long",
                "Timezone: America/Argentina/Buenos_Aires",
                "Charset UTF8",
                "Índices optimizados para geo-queries"
            ]
        )
        
        # APIs externas
        self.add_entity(
            name="ExternalAPIs",
            entity_type="integration",
            observations=[
                "Eventbrite API (necesita key)",
                "Facebook RapidAPI funcionando",
                "Ticketmaster API configurada",
                "Meetup API disponible",
                "Instagram RapidAPI (temporal HTTP 500)",
                "Google Calendar para sincronización",
                "31 plataformas potenciales identificadas"
            ]
        )
        
        # Estado actual
        self.add_entity(
            name="CurrentStatus",
            entity_type="state",
            observations=[
                "Servidores funcionando correctamente",
                "CloudScraper instalado y operativo",
                "Endpoints sincronizados frontend-backend",
                "Sin datos simulados (solo APIs reales)",
                "Facebook sin UIDs (query directo)",
                "Timeouts optimizados (3-5 segundos)",
                "Caché mensual para Facebook events",
                "MCP Memory Server configurado"
            ]
        )
        
        # Reglas críticas
        self.add_entity(
            name="CriticalRules",
            entity_type="rules",
            observations=[
                "NUNCA cambiar puerto 8001 del backend",
                "NUNCA cambiar puerto 5174 del frontend",
                "NUNCA usar localhost - usar IP WSL",
                "SIEMPRE usar templates HTML proporcionados",
                "NO crear eventos simulados/mockup",
                "SIEMPRE liberar conexiones con try-finally",
                "NO crear nuevos servidores (solo main.py)",
                "SIEMPRE usar python3 (nunca python)"
            ]
        )
        
        # Relaciones
        self.add_relation("EventosVisualizer", "Backend", "uses")
        self.add_relation("EventosVisualizer", "Frontend", "uses")
        self.add_relation("EventosVisualizer", "Database", "uses")
        self.add_relation("Backend", "Database", "connects_to")
        self.add_relation("Backend", "ExternalAPIs", "integrates_with")
        self.add_relation("Frontend", "Backend", "calls_api")
        self.add_relation("EventosVisualizer", "CurrentStatus", "has_status")
        self.add_relation("EventosVisualizer", "CriticalRules", "follows")
        
    def add_entity(self, name: str, entity_type: str, observations: List[str]):
        """
        Agrega una entidad al contexto
        """
        self.entities[name] = {
            "name": name,
            "entityType": entity_type,
            "observations": observations,
            "created_at": datetime.now().isoformat()
        }
        
    def add_relation(self, from_entity: str, to_entity: str, relation_type: str):
        """
        Agrega una relación entre entidades
        """
        self.relations.append({
            "from": from_entity,
            "to": to_entity,
            "relationType": relation_type,
            "created_at": datetime.now().isoformat()
        })
        
    def add_observation(self, entity_name: str, observation: str):
        """
        Agrega una observación a una entidad existente
        """
        if entity_name in self.entities:
            if observation not in self.entities[entity_name]["observations"]:
                self.entities[entity_name]["observations"].append(observation)
                self.entities[entity_name]["updated_at"] = datetime.now().isoformat()
        
    def save_context(self):
        """
        Guarda el contexto en un archivo JSON
        """
        context = {
            "project": self.project_name,
            "entities": list(self.entities.values()),
            "relations": self.relations,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Contexto guardado en {self.context_file}")
        
    def load_context(self):
        """
        Carga el contexto desde archivo
        """
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                context = json.load(f)
                
            # Reconstruir entities como diccionario
            self.entities = {}
            for entity in context.get("entities", []):
                self.entities[entity["name"]] = entity
                
            self.relations = context.get("relations", [])
            
            print(f"✅ Contexto cargado: {len(self.entities)} entidades, {len(self.relations)} relaciones")
            return True
            
        except FileNotFoundError:
            print("⚠️ No se encontró archivo de contexto previo")
            return False
        except Exception as e:
            print(f"❌ Error cargando contexto: {e}")
            return False
    
    def get_summary(self):
        """
        Obtiene un resumen del contexto actual
        """
        print("\n" + "=" * 60)
        print(f"📊 CONTEXTO DEL PROYECTO: {self.project_name}")
        print("=" * 60)
        
        print(f"\n📦 Entidades ({len(self.entities)}):")
        for name, entity in self.entities.items():
            print(f"  • {name} ({entity['entityType']}): {len(entity['observations'])} observaciones")
        
        print(f"\n🔗 Relaciones ({len(self.relations)}):")
        for rel in self.relations[:10]:  # Mostrar primeras 10
            print(f"  • {rel['from']} → {rel['relationType']} → {rel['to']}")
        
        if len(self.relations) > 10:
            print(f"  ... y {len(self.relations) - 10} relaciones más")
        
        print("\n" + "=" * 60)

def main():
    """
    Función principal para gestionar el contexto
    """
    print("🧠 GESTOR DE CONTEXTO - EVENTOS VISUALIZER")
    print("=" * 60)
    
    # Crear gestor de contexto
    context = ProjectContext()
    
    # Intentar cargar contexto existente
    if not context.load_context():
        print("📝 Inicializando nuevo contexto...")
        context.initialize_project_context()
        context.save_context()
    
    # Agregar observaciones recientes
    print("\n➕ Agregando observaciones de la sesión actual...")
    
    context.add_observation("CurrentStatus", f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    context.add_observation("EventosVisualizer", "MCP Memory Server implementado para persistencia de contexto")
    
    # Guardar contexto actualizado
    context.save_context()
    
    # Mostrar resumen
    context.get_summary()
    
    print("\n💡 USO CON CLAUDE:")
    print("  1. Copiar claude_desktop_config.json a la configuración de Claude")
    print("  2. El servidor de memoria recordará el contexto entre sesiones")
    print("  3. El archivo project_context.json contiene todo el conocimiento del proyecto")
    print("\n✅ Contexto del proyecto listo para usar con MCP Memory Server")

if __name__ == "__main__":
    main()