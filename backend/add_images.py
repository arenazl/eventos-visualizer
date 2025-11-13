"""
Script para agregar URLs de imágenes a los eventos usando búsqueda de Google Images
"""
import json
import os
from pathlib import Path
import requests
from urllib.parse import quote_plus
import time

# Carpeta con los JSONs
DATA_DIR = Path("data/image-better")

def search_google_image(query):
    """
    Busca una imagen en Google usando Custom Search API
    Por ahora, retornamos un placeholder
    """
    # Placeholder - necesitarías configurar Google Custom Search API
    # https://developers.google.com/custom-search/v1/overview

    # Por ahora retornamos un placeholder basado en Unsplash
    search_term = quote_plus(query)
    # Unsplash Source API - imágenes aleatorias relacionadas
    return f"https://source.unsplash.com/800x600/?{search_term}"

def process_json_file(filepath):
    """Procesa un archivo JSON y agrega image_url a cada evento"""
    print(f"\n📄 Procesando: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        events = json.load(f)

    updated_count = 0
    for i, event in enumerate(events):
        # Crear query de búsqueda con título + país
        query = f"{event['titulo']} {event['pais']}"

        # Obtener URL de imagen
        image_url = search_google_image(query)

        # Agregar al evento
        event['image_url'] = image_url
        updated_count += 1

        # Mostrar progreso cada 10 eventos
        if (i + 1) % 10 == 0:
            print(f"  ✓ {i + 1}/{len(events)} eventos procesados")

        # Pequeña pausa para no saturar
        time.sleep(0.1)

    # Guardar archivo actualizado
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {updated_count} eventos actualizados")
    return updated_count

def main():
    print("🚀 Iniciando proceso de agregar imágenes a eventos...")
    print(f"📁 Directorio: {DATA_DIR}\n")

    # Obtener todos los archivos JSON de eventos
    json_files = list(DATA_DIR.glob("eventos_*.json"))

    if not json_files:
        print("❌ No se encontraron archivos JSON de eventos")
        return

    print(f"📊 Archivos encontrados: {len(json_files)}\n")

    total_updated = 0
    for json_file in sorted(json_files):
        try:
            count = process_json_file(json_file)
            total_updated += count
        except Exception as e:
            print(f"  ❌ Error procesando {json_file.name}: {e}")

    print(f"\n🎉 Proceso completado!")
    print(f"✅ Total de eventos actualizados: {total_updated}")
    print(f"📁 Archivos procesados: {len(json_files)}")

if __name__ == "__main__":
    main()
