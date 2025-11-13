#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Procesa los 164 eventos crudos de BuenosAliens y crea JSON limpio
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import re

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Datos crudos extraídos
raw_data = """{"total":164,"eventos":[{"titulo":"ETTA!","fecha":" 177 - VIE 07 NOV","lugar":"","resto":""},{"titulo":"DEL OLMO","fecha":" 176 - JUE 17 JUL","lugar":"","resto":""},{"titulo":"AGUSTINA VILLARRAZA","fecha":" 175 - MIE 18 JUN","lugar":"","resto":""},{"titulo":"Marco Carola y Frank Storm","fecha":"DOM 16 NOV","lugar":"Native Beach Club, Cardales","resto":"Line up | Marco Carola (Italia) | Frank Storm (Italia) | Desde las 16hs. | Native Beach Club queda en Panamericana km 60, Cardales."},{"titulo":"Massano, Fideles y más","fecha":"SAB 15 NOV","lugar":"Mandarine Park","resto":"Line up | Massano (UK/Afterlife) | Fideles (Italia) | Pacs b2b Soel | Mandarine queda en el Complejo Punta Carrasco, Av Costanera y Av Sarmiento, Ciudad de Buenos Aires."},{"titulo":"Paul Van Dyk, Will Atkinson y más","fecha":"SAB 15 NOV","lugar":"Amerika","resto":"Line up | Paul Van Dyk (Alemania/Armada) | Will Atkinson (UK) | Desde las 23:59hs. | Estilo: trance. | Amerika queda en Gascón 1040, Ciudad de Buenos Aires."},{"titulo":"Shanti Celeste, Gop Tun Djs y más","fecha":"SAB 15 NOV","lugar":"Deseo","resto":"Line up | Shanti Celeste (Chile) | Guido Sartoris | Gop Tun djs (Brasil) | Desde las 23hs. | Deseo queda en Chorroarin 1040, Ciudad de Buenos Aires"},{"titulo":"Marron y Fausto","fecha":"SAB 15 NOV","lugar":"Under Club @ Blow, Palermo","resto":"Line up | Marron (Holanda) | Fausto | Desde las 23hs. | Estilo: techno. | Blow queda en Niceto Vega 5699, Palermo, Ciudad de Buenos Aires."},{"titulo":"Paul Oakenfold, Paul (AR) y más","fecha":"SAB 15 NOV","lugar":"Moscú, Costanera","resto":"Line up | Paul Oakenfold (UK) | Paul (AR) | Anunnakis | Desde las 18hs. | Moscú queda en Av. Rafael Obligado 6151, Costanera Norte, Cap. Fed."},{"titulo":"999999999, Odymel y más","fecha":"VIE 14 NOV","lugar":"Utopic @ Groove","resto":"Line up | 999999999 (Italia) | Odymel (Suiza) | Callush (Alemania) | Fjusha (Alemania) | Dist | Desde las 23hs. | Estilo: techno. | Groove queda en Av Santa Fe 4389, Palermo, Ciudad de Buenos Aires."},{"titulo":"Marcelo Vasami y Nicolás Rada","fecha":"VIE 14 NOV","lugar":"Crobar","resto":"Line up | Marcelo Vasami | Nicolás Rada | Desde las 23:59hs. | Estilo: progressive house. | Crobar es Marcelino Freyre s/n, Paseo de La Infanta, Palermo, Ciudad de Buenos Aires. "},{"titulo":"Cloudy, Adrián Mills y más","fecha":"VIE 14 NOV","lugar":"Heiss @ Amerika","resto":"Line up | Sophhiakahn f2f Juan Nuciforo | Serafina f2f Fumi | Cloudy f2f Adrián Mills | Kessler f2f Ko:Lab | Desde las 23hs. | Estilo: techno. | Amerika queda en Gascón 1040, Ciudad de Buenos Aires."},{"titulo":"Mylah, Julieta Lake y más","fecha":"VIE 14 NOV","lugar":"Under Club @ Blow, Palermo","resto":"Line up | Mylah | Julieta Lake | Ntrm | Gonzalo Trejo | Desde las 23hs. | Estilo: techno. | Blow es en: Niceto Vega 5699, Palermo, Ciudad de Buenos Aires."},{"titulo":"Marsh y más","fecha":"VIE 14 NOV","lugar":"2GTHR @ Morocco Costanera","resto":"Line up | Marsh (Anjunadeep) | Mas a confirmar. | Desde las 23:59hs. | Morocco Costanera queda en Costa Salguero, Ciudad de Buenos Aires."},{"titulo":"Graziano Raffa","fecha":"SAB 15 NOV","lugar":"La Biblioteca, San Telmo","resto":"Line up | Graziano Raffa | Desde las 23hs. | La Biblioteca queda en México 524, Ciudad de Buenos Aires."},{"titulo":"Stefano Andriezzi y Manu Oubiña","fecha":"VIE 14 NOV","lugar":"Dune Park","resto":"Line up | Stefano Andriezzi | Manu Oubiña | Desde las 23hs. | Dune Park queda en Araoz 740, Capital Federal."},{"titulo":"Cosima, Saint Pablo y más","fecha":"VIE 14 NOV","lugar":"Shamrock Basement","resto":"Line up | Iman | Cosima | Saint Pablo | Desde las 23hs. | The Shamrock Basement queda en Rodriguez Peña 1220, Ciudad de Buenos Aires."},{"titulo":"Mayro, Hassan y más","fecha":"SAB 15 NOV","lugar":"Club de Pescadores","resto":"Line up | Mayro | Hassan | Mareveg | Sebastián Huel | Desde las 23hs. | Muelle de Pescadores queda en Av Rafael Obligado y Av Sarmiento, Ciudad de Buenos Aires."},{"titulo":"Eclipse Sonar, Borja y más","fecha":"SAB 15 NOV","lugar":"Dune Park","resto":"Line up | Eclipse Sonar | Borja b2b Sirio | Hazzed | Ailen DC b2b Candela | Desde las 23hs. | Dune Park queda en Araoz 740, Capital Federal."},{"titulo":"Vicky Sand, Ina y más","fecha":"SAB 15 NOV","lugar":"Shamrock Basement","resto":"Line up | Krypta b2b Yanacone | San Nicolas  | Vicky Sand b2b Ina | Desde las 23hs. | The Shamrock Basement queda en Rodriguez Peña 1220, Ciudad de Buenos Aires."},{"titulo":"Jesica Falaschi, Lucas Sosa (AR) y más","fecha":"SAB 15 NOV","lugar":"Complejo Art Media","resto":"Line up | JXXXO  | Pakard | Hers | Jesica Falaschi | Lucas Sosa (AR) | Desde las 23hs. | Estilo: techno. | Complejo Art Media queda en Av. Corrientes 6271, Ciudad de Buenos Aires"},{"titulo":"Gonzalo Seijas, Santiago Cardinal y más","fecha":"VIE 14 NOV","lugar":"Club de Pescadores","resto":"Line up | Gonzalo Seijas | Santiago Cardinal | Levo Jaimes | Colau | Desde las 23hs. | Muelle de Pescadores queda en Av Rafael Obligado y Av Sarmiento, Ciudad de Buenos Aires."},{"titulo":"Soundexile, Mark y más","fecha":"SAB 15 NOV","lugar":"Downtempo Rooftop","resto":"Line up | Soundexile | Mark & Math | Gonza Siles | Desde las 18hs. | Downtempo Rooftop queda en Av. Constituyentes 3552, Ciudad de Buenos Aires"},{"titulo":"Sgalia, Juan GL y más","fecha":"SAB 15 NOV","lugar":"Frida Club","resto":"Line up | Sgalia | Juan GL | Manuel Roverano b2b Sax | Alejandra Torres b2b Mati Montes | Desde las 23hs. | Frida Club queda en Dorrego 1735, Cap. Fed."},{"titulo":"Roberto Ceratti, Saflo y más","fecha":"VIE 14 NOV","lugar":"La Biblioteca, San Telmo","resto":"Line up | Roberto Ceratti | Saflo | Juan M | Desde las 23hs. | La Biblioteca queda en México 524, Ciudad de Buenos Aires."}]}"""

data = json.loads(raw_data)

def parse_date(fecha_str):
    """Parsea fechas de BuenosAliens"""
    if not fecha_str or fecha_str.strip() == "":
        return None

    # Mapeo meses español
    meses = {
        'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
    }

    # Formato: "VIE 14 NOV" o "DOM 16 NOV"
    match = re.search(r'(\d+)\s+(\w+)', fecha_str)
    if match:
        dia = match.group(1).zfill(2)
        mes_str = match.group(2)
        mes = meses.get(mes_str, '11')
        ano = '2025'
        return f"{ano}-{mes}-{dia}"

    return None

def extract_lineup(resto):
    """Extrae lineup del texto resto"""
    if not resto or 'Line up' not in resto:
        return []

    lineup = []
    lines = resto.split('|')
    for line in lines:
        line = line.strip()
        # Buscar artistas con país entre paréntesis
        if '(' in line and ')' in line:
            lineup.append(line)
        elif line and not any(x in line.lower() for x in ['desde', 'estilo', 'queda', 'line up', 'será']):
            # Otros artistas sin país
            if len(line) > 3 and len(line) < 50:
                lineup.append(line)

    return lineup[:10]  # Max 10 artistas

def clean_events(eventos):
    """Limpia y procesa eventos"""
    cleaned = []
    seen = set()

    for evento in eventos:
        titulo = evento.get('titulo', '').strip()
        fecha = evento.get('fecha', '').strip()
        lugar = evento.get('lugar', '').strip()

        # Filtrar eventos vacíos o inválidos
        if not titulo or not fecha or not lugar:
            continue

        # Filtrar duplicados
        key = f"{titulo}_{fecha}_{lugar}"
        if key in seen:
            continue
        seen.add(key)

        # Parsear fecha
        date_iso = parse_date(fecha)
        if not date_iso:
            continue

        # Extraer lineup y detalles
        resto = evento.get('resto', '')
        lineup = extract_lineup(resto)

        # Extraer horario
        time_match = re.search(r'Desde las (\d+(?::\d+)?hs?)', resto)
        time = time_match.group(1) if time_match else 'Todo el día'

        # Extraer dirección
        address_match = re.search(r'queda en (.+?)(?:\.|$)', resto)
        address = address_match.group(1).strip() if address_match else lugar

        # Detectar categoría
        category = 'música electrónica'
        if 'techno' in resto.lower():
            category = 'techno'
        elif 'trance' in resto.lower():
            category = 'trance'
        elif 'house' in resto.lower():
            category = 'house'

        cleaned.append({
            'title': titulo,
            'date': date_iso,
            'venue': lugar,
            'lineup': lineup,
            'time': time,
            'address': address,
            'city': 'Buenos Aires',
            'country': 'Argentina',
            'category': category
        })

    return cleaned

# Procesar
print('🔄 Procesando 164 eventos crudos...')
eventos_limpios = clean_events(data['eventos'])

print(f'✅ {len(eventos_limpios)} eventos válidos')

# Guardar
output = {
    "source": "buenosaliens.com",
    "url": "https://www.buenosaliens.com/#agenda",
    "scraped_at": datetime.now().isoformat(),
    "total_events": len(eventos_limpios),
    "method": "puppeteer_mcp_extraction_processed",
    "eventos": eventos_limpios
}

output_file = Path(__file__).parent.parent / 'scrapper_results' / 'latinamerica' / 'sudamerica' / 'argentina' / 'buenosaliens' / 'nightclub.json'
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f'💾 Guardado: {output_file}')
print(f'📊 Total: {len(eventos_limpios)} eventos')
