#!/usr/bin/env node
/**
 * MEGA SCRAPER - Pipeline TODO EN UNO
 *
 * 1. Lee URLs de archivos .md en carpeta sites/
 * 2. Detecta tipo de sitio (BuenosAliens, genérico, etc.)
 * 3. Aplica scraper específico o genérico
 * 4. Agrega imágenes: primero Ticketmaster, luego Google
 * 5. Formatea JSON correctamente
 * 6. Inserta en MySQL automáticamente
 *
 * USO: node mega_scraper.js
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const cheerio = require('cheerio');

// Configuración
const SITES_DIR = path.join(__dirname, '..', 'sites');
const OUTPUT_DIR = path.join(__dirname, '..', 'scrapper_results', 'mega_scraped');

const GOOGLE_API_KEY = 'AIzaSyBnASoI0jTHdwiuzugYDwqghzzzDJ44Smg';
const GOOGLE_CX = '06b5ac72c42074af6';
const TICKETMASTER_KEY = 'BnAVSbJZ7dVvPwFh91UVOmwX4CU1Ft5g';

const MYSQL_CONFIG = {
  host: 'autorack.proxy.rlwy.net',
  port: 43437,
  user: 'root',
  password: 'EBkvwVVMpJhSDORUWhUfLUfDTRXJYFPM',
  database: 'railway'
};

// Crear carpeta output
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

class MegaScraper {
  constructor() {
    this.mysql = null;
    this.connection = null;
  }

  // ============ PASO 1: Leer URL del .md ============
  extractUrlFromMd(mdFile) {
    try {
      const content = fs.readFileSync(mdFile, 'utf8');
      const lines = content.split('\n').filter(l => l.trim());

      const firstLine = lines[0].trim();

      if (firstLine.startsWith('http')) {
        return firstLine;
      }

      if (firstLine.includes('.') && !firstLine.startsWith('#')) {
        return `https://${firstLine}`;
      }

      return null;
    } catch (error) {
      return null;
    }
  }

  // ============ PASO 2: Detectar tipo de sitio ============
  detectSiteType(url) {
    if (url.includes('buenosaliens')) {
      return 'buenosaliens';
    }
    if (url.includes('feverup')) {
      return 'feverup';
    }
    if (url.includes('eventbrite')) {
      return 'eventbrite';
    }
    if (url.includes('ticketmaster')) {
      return 'ticketmaster';
    }
    if (url.includes('turismo.buenosaires')) {
      return 'turismo_ba';
    }

    return 'generic';
  }

  // ============ PASO 3: Scrapers específicos ============

  async scrapeBuenosAliens(url) {
    console.log('  🎵 Scraper específico: BuenosAliens');

    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });

      const $ = cheerio.load(response.data);
      const events = [];

      // Buscar eventos en la estructura de BuenosAliens
      $('article.event, .event-item, [class*="event-card"]').each((i, elem) => {
        try {
          const $elem = $(elem);

          const title = $elem.find('h2, h3, .event-title').first().text().trim();
          const date = $elem.find('.event-date, time').first().text().trim();
          const venue = $elem.find('.venue, .location').first().text().trim();
          const description = $elem.find('.description, .summary').first().text().trim();

          let imageUrl = $elem.find('img').first().attr('src') || $elem.find('img').first().attr('data-src');
          if (imageUrl && !imageUrl.startsWith('http')) {
            imageUrl = new URL(imageUrl, url).href;
          }

          let eventUrl = $elem.find('a').first().attr('href');
          if (eventUrl && !eventUrl.startsWith('http')) {
            eventUrl = new URL(eventUrl, url).href;
          }

          if (title && title.length > 3) {
            events.push({
              title,
              date: date || null,
              venue: venue || null,
              description: description || null,
              image_url: imageUrl || null,
              url: eventUrl || url,
              category: 'Nightclub',
              source: 'buenosaliens'
            });
          }
        } catch (e) {
          // Skip
        }
      });

      console.log(`  ✅ ${events.length} eventos encontrados`);
      return events;
    } catch (error) {
      console.log(`  ❌ Error: ${error.message.substring(0, 50)}`);
      return [];
    }
  }

  async scrapeFeverup(url) {
    console.log('  🔥 Scraper específico: Feverup');

    try {
      const response = await axios.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
      });

      const $ = cheerio.load(response.data);
      const events = [];

      $('[class*="event"], [data-testid*="event"]').slice(0, 50).each((i, elem) => {
        const $elem = $(elem);

        const title = $elem.find('h2, h3, [class*="title"]').first().text().trim();
        const price = $elem.find('[class*="price"]').first().text().trim();

        let imageUrl = $elem.find('img').attr('src');
        if (imageUrl && !imageUrl.startsWith('http')) {
          imageUrl = new URL(imageUrl, url).href;
        }

        if (title) {
          events.push({
            title,
            venue: null,
            image_url: imageUrl,
            price: price || null,
            category: 'Cultural',
            source: 'feverup'
          });
        }
      });

      console.log(`  ✅ ${events.length} eventos encontrados`);
      return events;
    } catch (error) {
      console.log(`  ❌ Error: ${error.message.substring(0, 50)}`);
      return [];
    }
  }

  async scrapeGeneric(url) {
    console.log('  🌐 Scraper genérico');

    try {
      const response = await axios.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' },
        timeout: 30000
      });

      const $ = cheerio.load(response.data);
      const events = [];

      // Buscar contenedores comunes
      const selectors = [
        'article',
        '[class*="event"]',
        '[class*="card"]',
        '[data-testid*="event"]'
      ];

      const containers = [];
      selectors.forEach(sel => {
        $(sel).each((i, elem) => {
          if (containers.length < 50) {
            containers.push(elem);
          }
        });
      });

      console.log(`  📦 ${containers.length} contenedores encontrados`);

      containers.forEach((elem) => {
        try {
          const $elem = $(elem);

          const title = (
            $elem.find('h1').first().text() ||
            $elem.find('h2').first().text() ||
            $elem.find('h3').first().text() ||
            $elem.find('[class*="title"]').first().text()
          ).trim();

          if (!title || title.length < 5) return;

          const date = $elem.find('[class*="date"], [class*="time"], time').first().text().trim();
          const venue = $elem.find('[class*="venue"], [class*="location"], [class*="place"]').first().text().trim();
          const description = $elem.find('[class*="description"], [class*="summary"], p').first().text().trim();

          let imageUrl = $elem.find('img').first().attr('src') || $elem.find('img').first().attr('data-src');
          if (imageUrl && !imageUrl.startsWith('http')) {
            imageUrl = new URL(imageUrl, url).href;
          }

          let eventUrl = $elem.find('a').first().attr('href');
          if (eventUrl && !eventUrl.startsWith('http')) {
            eventUrl = new URL(eventUrl, url).href;
          }

          events.push({
            title,
            date: date || null,
            venue: venue || null,
            description: description || null,
            image_url: imageUrl || null,
            url: eventUrl || url,
            category: 'General',
            source: 'web_scraping'
          });
        } catch (e) {
          // Skip
        }
      });

      console.log(`  ✅ ${events.length} eventos encontrados`);
      return events;
    } catch (error) {
      console.log(`  ❌ Error: ${error.message.substring(0, 50)}`);
      return [];
    }
  }

  // ============ PASO 4: Imágenes ============

  async addTicketmasterImages(events, city = 'Buenos Aires', countryCode = 'AR') {
    console.log('  🎟️  Buscando imágenes en Ticketmaster...');

    let added = 0;

    for (const event of events) {
      if (event.image_url) continue;

      try {
        const searchTerm = event.title.split('-')[0].split('|')[0].trim().substring(0, 50);

        const response = await axios.get('https://app.ticketmaster.com/discovery/v2/events.json', {
          params: {
            apikey: TICKETMASTER_KEY,
            keyword: searchTerm,
            city: city,
            countryCode: countryCode,
            size: 1
          },
          timeout: 10000
        });

        const tmEvents = response.data._embedded?.events || [];

        if (tmEvents.length > 0) {
          const images = tmEvents[0].images || [];
          if (images.length > 0) {
            const bestImage = images.reduce((prev, curr) =>
              (curr.width * curr.height) > (prev.width * prev.height) ? curr : prev
            );
            event.image_url = bestImage.url;
            added++;
          }
        }

        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        // Skip
      }
    }

    console.log(`  ✅ ${added} imágenes de Ticketmaster`);
    return added;
  }

  async addGoogleImages(events, city = 'Buenos Aires') {
    console.log('  🖼️  Agregando imágenes de Google...');

    let added = 0;

    for (const event of events) {
      if (event.image_url) continue;

      // Triple fallback
      const queries = [
        `${event.title} ${event.venue || ''} ${city} event`,
        `${event.title.split(' ').slice(0, 3).join(' ')} ${city}`,
        event.venue ? `${event.venue} ${city}` : null
      ].filter(Boolean);

      for (const query of queries) {
        try {
          const response = await axios.get('https://www.googleapis.com/customsearch/v1', {
            params: {
              key: GOOGLE_API_KEY,
              cx: GOOGLE_CX,
              q: query,
              searchType: 'image',
              num: 1,
              imgSize: 'large'
            },
            timeout: 10000
          });

          if (response.data.items && response.data.items.length > 0) {
            event.image_url = response.data.items[0].link;
            added++;
            break;
          }
        } catch (error) {
          if (error.response && error.response.status === 429) {
            console.log('  ⚠️  Límite diario de Google alcanzado');
            return added;
          }
        }

        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    console.log(`  ✅ ${added} imágenes de Google`);
    return added;
  }

  // ============ PASO 5: Formatear JSON ============

  formatForDatabase(events, sourceName, city = 'Buenos Aires', country = 'Argentina') {
    return {
      source: sourceName,
      city: city,
      country: country,
      total: events.length,
      scraped_at: new Date().toISOString(),
      eventos: events.map(e => ({
        title: e.title || 'Sin título',
        date: e.date || null,
        start_datetime: e.date || null,
        venue_name: e.venue || null,
        venue: e.venue || null,
        description: e.description || null,
        image_url: e.image_url || null,
        event_url: e.url || null,
        url: e.url || null,
        source: e.source || sourceName,
        external_id: null,
        category: e.category || 'General',
        price: e.price || null,
        is_free: !e.price,
        scraped_at: new Date().toISOString()
      }))
    };
  }

  // ============ PASO 6: Insertar en MySQL ============

  async connectMySQL() {
    if (this.connection) return this.connection;

    try {
      this.mysql = require('mysql2/promise');
      this.connection = await this.mysql.createConnection(MYSQL_CONFIG);
      console.log('  ✅ Conectado a MySQL');
      return this.connection;
    } catch (error) {
      console.log(`  ⚠️  MySQL no disponible: ${error.message.substring(0, 50)}`);
      return null;
    }
  }

  async insertToMySQL(data) {
    console.log('  💾 Insertando en MySQL...');

    const conn = await this.connectMySQL();
    if (!conn) {
      console.log('  ⚠️  Saltando inserción (sin conexión)');
      return 0;
    }

    let inserted = 0;

    try {
      for (const event of data.eventos) {
        try {
          const query = `
            INSERT INTO events (
              title, start_datetime, venue_name, description,
              image_url, event_url, source_api, category,
              is_free, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
              image_url = COALESCE(VALUES(image_url), image_url),
              updated_at = NOW()
          `;

          await conn.execute(query, [
            event.title,
            event.start_datetime,
            event.venue_name,
            event.description,
            event.image_url,
            event.event_url,
            event.source,
            event.category,
            event.is_free ? 1 : 0
          ]);

          inserted++;
        } catch (error) {
          // Skip duplicados
        }
      }

      console.log(`  ✅ ${inserted} eventos insertados`);
    } catch (error) {
      console.log(`  ❌ Error insertando: ${error.message.substring(0, 50)}`);
    }

    return inserted;
  }

  async close() {
    if (this.connection) {
      await this.connection.end();
      console.log('  ✅ Conexión MySQL cerrada');
    }
  }

  // ============ PIPELINE COMPLETO ============

  async processMdFile(mdFile) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`📄 ${path.basename(mdFile)}`);
    console.log('='.repeat(70));

    // PASO 1: Extraer URL
    const url = this.extractUrlFromMd(mdFile);
    if (!url) {
      console.log('  ⚠️  No se encontró URL');
      return null;
    }

    console.log(`  🔗 ${url}`);

    // PASO 2: Detectar tipo
    const siteType = this.detectSiteType(url);
    console.log(`  🎯 Tipo: ${siteType}`);

    // PASO 3: Scraping específico
    let events = [];

    switch (siteType) {
      case 'buenosaliens':
        events = await this.scrapeBuenosAliens(url);
        break;
      case 'feverup':
        events = await this.scrapeFeverup(url);
        break;
      default:
        events = await this.scrapeGeneric(url);
    }

    if (events.length === 0) {
      console.log('  ⚠️  Sin eventos');
      return null;
    }

    // PASO 4: Imágenes (Ticketmaster primero, luego Google)
    await this.addTicketmasterImages(events);
    await this.addGoogleImages(events);

    // PASO 5: Formatear
    const sourceName = path.basename(mdFile, '.md');
    const formattedData = this.formatForDatabase(events, sourceName);

    // Guardar JSON
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
    const outputFile = path.join(OUTPUT_DIR, `${sourceName}_${timestamp}.json`);
    fs.writeFileSync(outputFile, JSON.stringify(formattedData, null, 2), 'utf8');
    console.log(`  💾 JSON: ${path.basename(outputFile)}`);

    // PASO 6: Insertar en MySQL
    await this.insertToMySQL(formattedData);

    return {
      file: outputFile,
      events: events.length
    };
  }
}

async function main() {
  console.log('='.repeat(70));
  console.log('🚀 MEGA SCRAPER - TODO EN UNO');
  console.log('='.repeat(70));
  console.log('Scraping + Imágenes (Ticketmaster + Google) + MySQL\n');

  const scraper = new MegaScraper();

  // Buscar archivos .md
  const mdFiles = fs.readdirSync(SITES_DIR)
    .filter(f => f.endsWith('.md') && f !== 'sites.md') // Excluir índice
    .map(f => path.join(SITES_DIR, f));

  if (mdFiles.length === 0) {
    console.log('⚠️  No se encontraron archivos .md');
    return;
  }

  console.log(`📊 ${mdFiles.length} archivos encontrados\n`);

  const results = {
    success: 0,
    failed: 0,
    totalEvents: 0,
    totalInserted: 0
  };

  for (const mdFile of mdFiles) {
    try {
      const result = await scraper.processMdFile(mdFile);

      if (result) {
        results.success++;
        results.totalEvents += result.events;
      } else {
        results.failed++;
      }

      // Rate limit entre archivos
      await new Promise(resolve => setTimeout(resolve, 3000));
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      results.failed++;
    }
  }

  await scraper.close();

  console.log('\n' + '='.repeat(70));
  console.log('🎉 MEGA SCRAPER COMPLETADO');
  console.log('='.repeat(70));
  console.log(`✅ Éxitos: ${results.success}`);
  console.log(`❌ Fallos: ${results.failed}`);
  console.log(`🎫 Total eventos: ${results.totalEvents}`);
  console.log('='.repeat(70) + '\n');
}

main().catch(console.error);
