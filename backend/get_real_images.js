/**
 * Script para obtener URLs reales de Google Images
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'image-better');

async function buscarImagenesGoogle(query) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto(`https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch`, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    const imagenes = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));
      const urls = imgs
        .map(img => img.src)
        .filter(src => src.startsWith('http') && !src.includes('gstatic.com'));
      return urls;
    });

    await browser.close();
    return imagenes.length > 0 ? imagenes[0] : null;

  } catch (error) {
    await browser.close();
    return null;
  }
}

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.basename(filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  const events = JSON.parse(data);

  let updated = 0;

  const LIMIT = 3; // Solo procesar 3 para probar

  for (let i = 0; i < Math.min(LIMIT, events.length); i++) {
    const event = events[i];
    const query = event.titulo; // Solo el título

    console.log(`  🔍 [${i + 1}/${LIMIT}] ${query.substring(0, 40)}...`);

    const imageUrl = await buscarImagenesGoogle(query);

    if (imageUrl) {
      event.image_url = imageUrl;
      console.log(`  ✅ ${imageUrl.substring(0, 60)}...`);
      updated++;
    } else {
      console.log(`  ❌ No se encontró`);
    }

    // Pausa para no ser bloqueados
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
  console.log(`  📊 Total actualizado: ${updated}/${events.length}`);
  return updated;
}

async function main() {
  console.log('🚀 Obteniendo imágenes reales de Google Images...\n');

  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.startsWith('eventos_') && f.endsWith('.json'))
    .sort()
    .map(f => path.join(DATA_DIR, f));

  if (files.length === 0) {
    console.log('❌ No se encontraron archivos JSON');
    return;
  }

  console.log(`📊 ${files.length} archivos a procesar\n`);

  let totalUpdated = 0;
  for (const file of files) {
    try {
      const count = await processJsonFile(file);
      totalUpdated += count;
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}`);
    }
  }

  console.log(`\n🎉 Proceso completado!`);
  console.log(`✅ Total eventos actualizados: ${totalUpdated}`);
}

main().catch(console.error);
