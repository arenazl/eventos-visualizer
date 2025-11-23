#!/usr/bin/env python3
"""
Genera reporte HTML de eventos desde los archivos JSON parseados.
Lee directamente los JSONs que YA tienen image_url.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PARSED_DIR = SCRIPT_DIR.parent / "scrapper_results" / "parsed"
REPORTS_DIR = SCRIPT_DIR.parent / "reports"

def load_all_events():
    """Carga todos los eventos de todos los JSONs parseados."""
    events_by_city = defaultdict(list)

    if not PARSED_DIR.exists():
        print(f"ERROR: No existe {PARSED_DIR}")
        return events_by_city

    # Recorrer todas las fuentes (gemini, felo, etc.)
    for source_dir in PARSED_DIR.iterdir():
        if not source_dir.is_dir():
            continue

        source_name = source_dir.name

        # Recorrer todos los JSONs de esta fuente
        for json_file in source_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Manejar diferentes estructuras
                if isinstance(data, list):
                    events = data
                elif isinstance(data, dict):
                    events = data.get('eventos', data.get('events', []))
                else:
                    continue

                for event in events:
                    # Normalizar ciudad
                    city = event.get('ciudad', event.get('city', 'Sin Ciudad'))
                    city = city.strip().title() if city else 'Sin Ciudad'

                    # Normalizar nombre de ciudad
                    city_mapping = {
                        'Buenosaires': 'Buenos Aires',
                        'Buenos Aires': 'Buenos Aires',
                        'Cordoba': 'Cordoba',
                        'Córdoba': 'Cordoba',
                    }
                    city = city_mapping.get(city, city)

                    events_by_city[city].append(event)

            except Exception as e:
                print(f"Error leyendo {json_file}: {e}")

    return events_by_city

def get_category_class(category):
    """Retorna la clase CSS para la categoria."""
    category = (category or 'other').lower()
    classes = {
        'music': 'cat-music',
        'cultural': 'cat-cultural',
        'nightlife': 'cat-nightlife',
        'food': 'cat-food',
        'sports': 'cat-sports',
        'tech': 'cat-tech',
        'entertainment': 'cat-entertainment',
    }
    return classes.get(category, 'cat-other')

def format_date(date_str):
    """Formatea la fecha para mostrar."""
    if not date_str:
        return 'Fecha por confirmar'
    try:
        # Intentar parsear diferentes formatos
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(date_str.split('T')[0], fmt.split('T')[0])
                return dt.strftime('%d %b %Y')
            except:
                continue
        return date_str
    except:
        return date_str

def generate_event_card(event):
    """Genera el HTML de una tarjeta de evento."""
    nombre = event.get('nombre', event.get('title', 'Sin titulo'))
    descripcion = event.get('descripcion', event.get('description', ''))
    fecha = format_date(event.get('fecha', event.get('date', '')))
    lugar = event.get('lugar', event.get('venue', 'Por confirmar'))
    barrio = event.get('barrio', event.get('neighborhood', ''))
    precio = event.get('precio', event.get('price', ''))
    category = event.get('category', 'other')
    source = event.get('source', 'unknown')
    image_url = event.get('image_url', '')
    es_gratis = event.get('es_gratis', False) or 'gratis' in str(precio).lower() or 'gratuito' in str(precio).lower()

    # Limpiar nombre (quitar numeros al inicio como "1. ", "2. ")
    if nombre and nombre[0].isdigit() and '. ' in nombre[:5]:
        nombre = nombre.split('. ', 1)[1] if '. ' in nombre else nombre

    # Truncar descripcion
    if descripcion and len(descripcion) > 150:
        descripcion = descripcion[:147] + '...'

    # Image HTML
    if image_url and not image_url.startswith('x-raw-image'):
        image_html = f'<img class="event-image" src="{image_url}" alt="{nombre}" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\'"><div class="event-image-placeholder" style="display:none">Sin imagen</div>'
    else:
        image_html = '<div class="event-image-placeholder">Sin imagen</div>'

    # Price display
    if es_gratis:
        price_html = '<span class="event-price free">GRATIS</span>'
    elif precio:
        price_html = f'<span class="event-price">{precio}</span>'
    else:
        price_html = '<span class="event-price">Consultar</span>'

    return f'''
            <div class="event-card">
                {image_html}
                <div class="event-content">
                    <span class="event-category {get_category_class(category)}">{category}</span>
                    <h3 class="event-title">{nombre}</h3>
                    <p class="event-description">{descripcion}</p>
                    <div class="event-meta">
                        <div class="event-meta-item">
                            <span class="icon">📅</span> {fecha}
                        </div>
                        <div class="event-meta-item">
                            <span class="icon">📍</span> {lugar}{f" - {barrio}" if barrio else ""}
                        </div>
                    </div>
                    <div class="event-footer">
                        {price_html}
                        <span class="event-source source-{source}">{source.upper()}</span>
                    </div>
                </div>
            </div>'''

def generate_html_report(events_by_city):
    """Genera el reporte HTML completo."""

    total_events = sum(len(events) for events in events_by_city.values())
    total_cities = len(events_by_city)
    total_free = sum(1 for events in events_by_city.values()
                     for e in events
                     if e.get('es_gratis') or 'gratis' in str(e.get('precio', '')).lower())

    # Ordenar ciudades por cantidad de eventos
    sorted_cities = sorted(events_by_city.items(), key=lambda x: -len(x[1]))

    # City icons
    city_icons = {
        'Buenos Aires': 'BA',
        'Rosario': 'RO',
        'Cordoba': 'CO',
        'Mendoza': 'MZ',
        'Mar Del Plata': 'MP',
    }

    cities_html = ""
    for city, events in sorted_cities:
        icon = city_icons.get(city, city[:2].upper())

        # Ordenar eventos por fecha
        events_sorted = sorted(events, key=lambda x: x.get('fecha', '9999'))

        events_cards = "\n".join(generate_event_card(e) for e in events_sorted)

        cities_html += f'''
    <div class="city-section">
        <div class="city-header">
            <div class="city-icon">{icon}</div>
            <h2 class="city-name">{city}</h2>
            <span class="city-count">{len(events)} eventos</span>
        </div>
        <div class="events-grid">
{events_cards}
        </div>
    </div>
'''

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Eventos - {datetime.now().strftime('%d %B %Y')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 40px 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        .header p {{ color: #a0a0a0; font-size: 1.1rem; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.1);
            padding: 15px 30px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-box .number {{ font-size: 2rem; font-weight: bold; color: #48dbfb; }}
        .stat-box .label {{ font-size: 0.9rem; color: #888; }}
        .city-section {{ margin-bottom: 50px; }}
        .city-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }}
        .city-icon {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: bold;
        }}
        .city-name {{ font-size: 1.8rem; font-weight: 600; }}
        .city-count {{
            background: rgba(72, 219, 251, 0.2);
            color: #48dbfb;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        .events-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }}
        .event-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .event-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        .event-image {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            background: linear-gradient(135deg, #2d2d44, #1a1a2e);
        }}
        .event-image-placeholder {{
            width: 100%;
            height: 180px;
            background: linear-gradient(135deg, #2d2d44, #1a1a2e);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 0.9rem;
        }}
        .event-content {{ padding: 20px; }}
        .event-category {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .cat-music {{ background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }}
        .cat-cultural {{ background: rgba(254, 202, 87, 0.2); color: #feca57; }}
        .cat-nightlife {{ background: rgba(155, 89, 182, 0.2); color: #9b59b6; }}
        .cat-food {{ background: rgba(46, 204, 113, 0.2); color: #2ecc71; }}
        .cat-sports {{ background: rgba(52, 152, 219, 0.2); color: #3498db; }}
        .cat-tech {{ background: rgba(72, 219, 251, 0.2); color: #48dbfb; }}
        .cat-entertainment {{ background: rgba(241, 196, 15, 0.2); color: #f1c40f; }}
        .cat-other {{ background: rgba(149, 165, 166, 0.2); color: #95a5a6; }}
        .event-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .event-description {{
            color: #a0a0a0;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 15px;
            min-height: 40px;
        }}
        .event-meta {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 0.85rem;
            color: #888;
        }}
        .event-meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .event-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .event-price {{ font-weight: 600; color: #2ecc71; }}
        .event-price.free {{ color: #48dbfb; }}
        .event-source {{
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            text-transform: uppercase;
        }}
        .source-gemini {{ color: #48dbfb; }}
        .source-felo {{ color: #feca57; }}
        .footer {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 0.9rem;
        }}
        @media (max-width: 768px) {{
            .events-grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte de Eventos Argentina</h1>
        <p>Generado el {datetime.now().strftime('%d de %B %Y a las %H:%M')}</p>
        <div class="stats">
            <div class="stat-box">
                <div class="number">{total_cities}</div>
                <div class="label">Ciudades</div>
            </div>
            <div class="stat-box">
                <div class="number">{total_events}</div>
                <div class="label">Eventos Totales</div>
            </div>
            <div class="stat-box">
                <div class="number">{total_free}</div>
                <div class="label">Eventos Gratis</div>
            </div>
        </div>
    </div>

{cities_html}

    <div class="footer">
        <p>Reporte generado automaticamente desde archivos JSON parseados</p>
        <p>Fuentes: Gemini AI + Felo AI</p>
    </div>
</body>
</html>'''

    return html

def main():
    print("=" * 60)
    print("GENERANDO REPORTE HTML DE EVENTOS")
    print("=" * 60)

    # Crear directorio de reportes si no existe
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar eventos
    print(f"\nLeyendo JSONs desde: {PARSED_DIR}")
    events_by_city = load_all_events()

    if not events_by_city:
        print("ERROR: No se encontraron eventos")
        return

    # Mostrar resumen
    total = sum(len(e) for e in events_by_city.values())
    print(f"\nEventos cargados: {total}")
    for city, events in sorted(events_by_city.items(), key=lambda x: -len(x[1])):
        with_images = sum(1 for e in events if e.get('image_url') and not e.get('image_url', '').startswith('x-raw'))
        print(f"  - {city}: {len(events)} eventos ({with_images} con imagen)")

    # Generar HTML
    print("\nGenerando HTML...")
    html = generate_html_report(events_by_city)

    # Guardar archivo
    output_file = REPORTS_DIR / f"eventos_{datetime.now().strftime('%Y-%m-%d')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Reporte generado: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
