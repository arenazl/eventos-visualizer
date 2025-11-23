#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 PIPELINE COMPLETO: Scrape → Parse → Import

Orquesta las 3 fases del proceso de scraping elástico:

FASE 1 (Scraping):
  - Instrucciones para usar Puppeteer MCP con Gemini
  - Genera RAW text en scrapper_results/raw/

FASE 2 (Parsing):
  - Convierte RAW text a JSON estructurado
  - Aplica categorización y normalización
  - Guarda en scrapper_results/parsed/

FASE 3 (Import):
  - Importa JSONs a MySQL
  - Fuzzy duplicate detection (80%)
  - Maneja neighborhood null

Uso:
    python pipeline_completo.py                           # Ejecuta FASE 2 + FASE 3
    python pipeline_completo.py --parse-only              # Solo FASE 2
    python pipeline_completo.py --import-only             # Solo FASE 3
    python pipeline_completo.py --dry-run                 # Preview sin cambios
"""

import sys
import json
from pathlib import Path
from typing import Optional

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / 'config'
FASE2_SCRIPT = SCRIPT_DIR / 'fase2_parse.py'
FASE3_SCRIPT = SCRIPT_DIR / 'fase3_import.py'


def print_header(title: str):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def show_fase1_instructions(ciudad: str = "Buenos Aires"):
    """
    Muestra instrucciones para ejecutar FASE 1 con Puppeteer MCP
    """
    print_header("📡 FASE 1: SCRAPING CON PUPPETEER MCP")

    # Cargar prompt de configuración
    prompts_file = CONFIG_DIR / 'prompts.json'

    if not prompts_file.exists():
        print(f"❌ No se encontró {prompts_file}")
        print("💡 Creando configuración por defecto...")

        # Crear config por defecto
        default_config = {
            "_last_updated": "2025-11-14",
            "ai_scrapers": {
                "variations": {
                    "gemini": "me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas!",
                    "felo": "dame eventos en {lugar} desde hoy hasta fin de mes, necesito nombre, descripción, fecha, lugar, dirección, barrio y precio",
                    "grok": "qué eventos hay en {lugar} este mes? incluí nombre, descripción, fecha, ubicación, barrio y precio",
                    "perplexity": "lista eventos en {lugar} este mes con nombre, fecha, lugar, barrio y precio"
                }
            }
        }

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

    with open(prompts_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    prompt_template = config['ai_scrapers']['variations']['gemini']
    prompt_final = prompt_template.replace('{lugar}', ciudad)

    print("🤖 INSTRUCCIONES MANUALES:")
    print("\n1. Abre Claude Code con MCP Puppeteer habilitado")
    print("2. Ejecuta este comando:")
    print("\n   navigate: https://gemini.google.com")
    print(f"\n3. Escribe en el chat de Gemini:\n")
    print(f"   {prompt_final}")
    print("\n4. Espera la respuesta de Gemini (tabla con eventos)")
    print("\n5. COPIA TODO EL TEXTO de la respuesta")
    print("\n6. Guarda el texto en:")
    print(f"\n   backend/data/scrapper_results/raw/gemini/{ciudad.lower().replace(' ', '-')}_YYYY-MM-DD.txt")
    print("\n7. Ejecuta FASE 2 para parsear el archivo RAW\n")

    print("💡 TIP: Gemini debería retornar una tabla con estas columnas:")
    print("   Nombre | Descripción | Fecha | Lugar/Dirección | Barrio | Precio | Info Extra")
    print("\n")


def run_fase2(dry_run: bool = False) -> bool:
    """
    Ejecuta FASE 2 (Parsing)
    """
    print_header("🔧 FASE 2: PARSING DE RAW A JSON")

    if not FASE2_SCRIPT.exists():
        print(f"❌ No se encontró {FASE2_SCRIPT}")
        return False

    import subprocess

    cmd = ['python', str(FASE2_SCRIPT)]
    if dry_run:
        cmd.append('--dry-run')

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando FASE 2: {e}")
        return False


def run_fase3(dry_run: bool = False) -> bool:
    """
    Ejecuta FASE 3 (Import a MySQL)
    """
    print_header("📥 FASE 3: IMPORTACIÓN A MYSQL")

    if not FASE3_SCRIPT.exists():
        print(f"❌ No se encontró {FASE3_SCRIPT}")
        return False

    import subprocess

    cmd = ['python', str(FASE3_SCRIPT)]
    if dry_run:
        cmd.append('--dry-run')

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando FASE 3: {e}")
        return False


def main():
    """Main function"""
    # Parsear argumentos
    dry_run = '--dry-run' in sys.argv
    parse_only = '--parse-only' in sys.argv
    import_only = '--import-only' in sys.argv
    ciudad = 'Buenos Aires'  # Default

    # Extraer ciudad si se provee
    for arg in sys.argv:
        if arg.startswith('--ciudad='):
            ciudad = arg.split('=', 1)[1]

    print("\n" + "🌟" * 40)
    print("   PIPELINE COMPLETO DE SCRAPING ELÁSTICO")
    print("🌟" * 40)

    # FASE 1: Mostrar instrucciones (manual con Puppeteer MCP)
    if not import_only:
        show_fase1_instructions(ciudad)
        print("⏸️  PAUSA: Ejecuta FASE 1 manualmente antes de continuar\n")
        print("💡 Presiona ENTER cuando hayas guardado el archivo RAW, o Ctrl+C para salir")

        try:
            input()
        except KeyboardInterrupt:
            print("\n\n❌ Pipeline cancelado por el usuario\n")
            return

    # FASE 2: Parsing
    if not import_only:
        success = run_fase2(dry_run)
        if not success:
            print("\n❌ FASE 2 falló, abortando pipeline\n")
            return

    # FASE 3: Import
    if not parse_only:
        success = run_fase3(dry_run)
        if not success:
            print("\n❌ FASE 3 falló\n")
            return

    # Resumen final
    print_header("✅ PIPELINE COMPLETADO")

    if not dry_run:
        print("🎉 Todos los eventos fueron procesados exitosamente!")
        print("\n📊 SIGUIENTES PASOS:")
        print("   1. Verifica eventos en MySQL: SELECT * FROM events ORDER BY created_at DESC LIMIT 10")
        print("   2. Prueba con otra ciudad: python pipeline_completo.py --ciudad='Córdoba'")
        print("   3. Scraping de otro AI: Edita config/prompts.json y usa Felo/Grok/Perplexity\n")
    else:
        print("🔍 DRY-RUN completado - no se modificó nada\n")


if __name__ == "__main__":
    main()
