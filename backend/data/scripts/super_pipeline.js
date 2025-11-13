#!/usr/bin/env node
/**
 * SUPER PIPELINE - Pipeline completo de scraping
 * 1. Lee URLs de archivos .md
 * 2. Scraping con Puppeteer
 * 3. Agrega imágenes de Google
 * 4. Formatea JSON
 * 5. Inserta en MySQL
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { execSync } = require('child_process');

// Configuración
const SITES_DIR = path.join(__dirname, '..', 'sites');
const OUTPUT_DIR = path.join(__dirname, '..', 'scrapper_results', 'auto_scraped');
const GOOGLE_API_KEY = 'AIzaSyBnASoI0jTHdwiuzugYDwqghzzzDJ44Smg';
const GOOGLE_CX = '06b5ac72c42074af6';
const BACKEND_API = 'http://localhost:8001';

// Crear carpeta output
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

class SuperPipeline {
  constructor() {
    this.puppeteer = null;
    this.browser = null;
  }

  async init() {
    console.log('🔧 Inicializando Puppeteer...');
    try {
      this.puppeteer = require('puppeteer');
      this.browser = await this.puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      console.log('✅ Puppeteer listo\n');
    } catch (error) {
      console.log('⚠️  Puppeteer no disponible, usando fetch\n');
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  extractUrlFromMd(mdFile) {
    try {
      const content = fs.readFileSync(mdFile, 'utf8');
      const firstLine = content.split('\n')[0].trim();

      if (firstLine.startsWith('http')) {
        return firstLine;
      }

      if (firstLine.includes('.') && !firstLine.startsWith('#')) {
        return `https://${firstLine}`;
      }

      return null;
    } catch (error) {
      console.log(`  ❌ Error leyendo ${path.basename(mdFile)}: ${error.message}`);
      return null;
    }
  }

  async scrapePage(url) {
    console.log(`  🌐 Scraping: ${url}`);

    if (this.browser) {
      // Usar Puppeteer
      try {
        const page = await this.browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

        // Esperar que cargue contenido dinámico
        await page.waitForTimeout(2000);

        const html = await page.content();
        await page.close();

        return html;
      } catch (error) {
        console.log(`  ⚠️  Error Puppeteer: ${error.message.substring(0, 50)}`);
        return null;
      }
    } else {
      // Fallback: usar axios
      try {
        const response = await axios.get(url, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          },
          timeout: 30000
        });
        return response.data;
      } catch (error) {
        console.log(`  ⚠️  Error fetch: ${error.message.substring(0, 50)}`);
        return null;
      }
    }
  }

  extractEventsGeneric(html, sourceUrl) {
    const events = [];

    // Patrones regex para encontrar eventos
    const patterns = [
      // Buscar bloques tipo JSON embebidos
      /"event":\s*\{[^}]+\}/gi,
      // Buscar títulos de eventos
      /<h[1-3][^>]*class="[^"]*event[^"]*"[^>]*>([^<]+)<\/h[1-3]>/gi,
      // Buscar artículos
      /<article[^>]*>([\s\S]{0,500})<\/article>/gi
    ];

    // Intentar extraer con cheerio si está disponible
    try {
      const cheerio = require('cheerio');
      const $ = cheerio.load(html);

      // Buscar contenedores comunes
      const containers = [
        ...$.find('[class*="event"]').toArray(),
        ...$.find('[class*="card"]').toArray(),
        ...$.find('article').toArray()
      ].slice(0, 50); // Limitar a 50

      console.log(`  📦 ${containers.length} contenedores encontrados`);

      containers.forEach((elem) => {
        try {
          const $elem = $(elem);

          // Título
          const title = (
            $elem.find('h1').first().text() ||
            $elem.find('h2').first().text() ||
            $elem.find('h3').first().text() ||
            $elem.find('[class*="title"]').first().text()
          ).trim();

          if (!title || title.length < 5) return;

          // Fecha
          const date = $elem.find('[class*="date"], [class*="time"]').first().text().trim();

          // Lugar
          const venue = $elem.find('[class*="venue"], [class*="location"]').first().text().trim();

          // Descripción
          const description = $elem.find('[class*="description"], [class*="summary"]').first().text().trim();

          // Imagen
          let imageUrl = $elem.find('img').first().attr('src') || $elem.find('img').first().attr('data-src');
          if (imageUrl && !imageUrl.startsWith('http')) {
            imageUrl = new URL(imageUrl, sourceUrl).href;
          }

          // Link
          let eventUrl = $elem.find('a').first().attr('href');
          if (eventUrl && !eventUrl.startsWith('http')) {
            eventUrl = new URL(eventUrl, sourceUrl).href;
          }

          events.push({
            title,
            date: date || null,
            venue: venue || null,
            description: description || null,
            image_url: imageUrl || null,
            url: eventUrl || sourceUrl,
            source: sourceUrl,
            scraped_at: new Date().toISOString()
          });
        } catch (e) {
          // Skip
        }
      });
    } catch (error) {
      console.log(`  ⚠️  Cheerio no disponible, extracción básica`);
    }

    return events;
  }

  async addGoogleImages(events, city = 'Buenos Aires') {
    console.log(`  🖼️  Agregando imágenes de Google...`);

    let added = 0;

    for (let i = 0; i < events.length; i++) {
      const event = events[i];

      if (event.image_url) continue;

      // Triple fallback
      const queries = [
        `${event.title} ${event.venue || ''} ${city} event`,
        `${event.title.split(' ').slice(0, 3).join(' ')} ${city}`,
        event.venue ? `${event.venue} ${city}` : null
      ].filter(Boolean);

      for (const query of queries) {
        const imageUrl = await this.getGoogleImage(query);

        if (imageUrl) {
          event.image_url = imageUrl;
          added++;
          break;
        }

        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }

    console.log(`  ✅ ${added} imágenes agregadas`);
    return added;
  }

  async getGoogleImage(searchQuery) {
    try {
      const url = 'https://www.googleapis.com/customsearch/v1';
      const params = {
        key: GOOGLE_API_KEY,
        cx: GOOGLE_CX,
        q: searchQuery,
        searchType: 'image',
        num: 1,
        imgSize: 'large'
      };

      const response = await axios.get(url, { params, timeout: 10000 });

      if (response.data.items && response.data.items.length > 0) {
        return response.data.items[0].link;
      }

      return null;
    } catch (error) {
      return null;
    }
  }

  formatForDatabase(events, sourceName) {
    return {
      source: sourceName,
      city: 'Buenos Aires', // Detectar automáticamente si es posible
      country: 'Argentina',
      total: events.length,
      scraped_at: new Date().toISOString(),
      eventos: events.map(e => ({
        title: e.title,
        date: e.date,
        start_datetime: e.date,
        venue_name: e.venue,
        venue: e.venue,
        description: e.description,
        image_url: e.image_url,
        event_url: e.url,
        url: e.url,
        source: sourceName,
        external_id: null,
        category: 'General',
        price: null,
        is_free: true
      }))
    };
  }

  async insertToDatabase(data) {
    console.log(`  💾 Insertando en base de datos...`);

    try {
      // Endpoint de inserción (crear si no existe)
      const response = await axios.post(`${BACKEND_API}/api/events/bulk`, data, {
        headers: { 'Content-Type': 'application/json' }
      });

      console.log(`  ✅ ${data.total} eventos insertados`);
      return true;
    } catch (error) {
      console.log(`  ⚠️  Error insertando: ${error.message.substring(0, 50)}`);
      console.log(`  💾 Guardando solo en archivo JSON...`);
      return false;
    }
  }

  async processMdFile(mdFile) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`📄 Procesando: ${path.basename(mdFile)}`);
    console.log('='.repeat(70));

    // 1. Extraer URL
    const url = this.extractUrlFromMd(mdFile);
    if (!url) {
      console.log('  ⚠️  No se encontró URL válida');
      return null;
    }

    console.log(`  🔗 URL: ${url}`);

    // 2. Scraping
    const html = await this.scrapePage(url);
    if (!html) {
      return null;
    }

    // 3. Extraer eventos
    console.log('  🔍 Extrayendo eventos...');
    const events = this.extractEventsGeneric(html, url);

    if (events.length === 0) {
      console.log('  ⚠️  No se encontraron eventos');
      return null;
    }

    console.log(`  ✅ ${events.length} eventos extraídos`);

    // 4. Agregar imágenes
    await this.addGoogleImages(events);

    // 5. Formatear para DB
    const sourceName = path.basename(mdFile, '.md');
    const formattedData = this.formatForDatabase(events, sourceName);

    // 6. Guardar JSON
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
    const outputFile = path.join(OUTPUT_DIR, `${sourceName}_${timestamp}.json`);
    fs.writeFileSync(outputFile, JSON.stringify(formattedData, null, 2), 'utf8');
    console.log(`  💾 JSON guardado: ${path.basename(outputFile)}`);

    // 7. Insertar en DB
    await this.insertToDatabase(formattedData);

    return outputFile;
  }
}

async function main() {
  console.log('='.repeat(70));
  console.log('🚀 SUPER PIPELINE - Scraping Completo Automático');
  console.log('='.repeat(70));
  console.log(`📂 Sites: ${SITES_DIR}`);
  console.log(`📂 Output: ${OUTPUT_DIR}\n`);

  const pipeline = new SuperPipeline();
  await pipeline.init();

  // Buscar archivos .md
  const mdFiles = fs.readdirSync(SITES_DIR)
    .filter(f => f.endsWith('.md'))
    .map(f => path.join(SITES_DIR, f));

  if (mdFiles.length === 0) {
    console.log('⚠️  No se encontraron archivos .md');
    await pipeline.close();
    return;
  }

  console.log(`📊 ${mdFiles.length} archivos encontrados\n`);

  const results = {
    success: 0,
    failed: 0,
    totalEvents: 0
  };

  for (const mdFile of mdFiles) {
    try {
      const output = await pipeline.processMdFile(mdFile);

      if (output) {
        results.success++;
        const data = JSON.parse(fs.readFileSync(output, 'utf8'));
        results.totalEvents += data.total;
      } else {
        results.failed++;
      }

      // Rate limit
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      results.failed++;
    }
  }

  await pipeline.close();

  console.log('\n' + '='.repeat(70));
  console.log('🎉 PIPELINE COMPLETADO');
  console.log('='.repeat(70));
  console.log(`✅ Éxitos: ${results.success}`);
  console.log(`❌ Fallos: ${results.failed}`);
  console.log(`🎫 Total eventos: ${results.totalEvents}`);
  console.log('='.repeat(70) + '\n');
}

main().catch(console.error);
