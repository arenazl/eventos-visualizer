/**
 * Script para obtener URLs reales de Google Images usando Puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'image-better');

async function getGoogleImageUrl(query) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  try {
    // Ir a Google Images
    const searchUrl = `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(query)}`;
    await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });

    // Hacer clic en la primera imagen
    await page.waitForSelector('div[data-id]', { timeout: 5000 });
    await page.click('div[data-id]');

    // Esperar que cargue el panel
    await page.waitForTimeout(2000);

    // Buscar la URL de la imagen en el panel
    const imageUrl = await page.evaluate(() => {
      // Intentar diferentes selectores donde Google muestra la imagen grande
      const selectors = [
        'img.n3VNCb',
        'img.sFlh5c',
        'img[jsname="HiaYvf"]',
        '#Sva75c img',
        '[data-item-title] img'
      ];

      for (const selector of selectors) {
        const img = document.querySelector(selector);
        if (img && img.src && !img.src.startsWith('data:') && !img.src.includes('gstatic.com')) {
          return img.src;
        }
      }

      // Si no encuentra, buscar cualquier imagen grande que no sea thumbnail
      const allImages = Array.from(document.querySelectorAll('img'));
      for (const img of allImages) {
        if (img.naturalWidth > 200 && img.src && !img.src.startsWith('data:') && !img.src.includes('gstatic.com')) {
          return img.src;
        }
      }

      return null;
    });

    await browser.close();
    return imageUrl;

  } catch (error) {
    console.error(`  ⚠️ Error obteniendo imagen: ${error.message}`);
    await browser.close();
    return null;
  }
}

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.basename(filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  const events = JSON.parse(data);

  let updated = 0;
  const limit = 5; // Procesar solo 5 eventos para probar

  for (let i = 0; i < Math.min(limit, events.length); i++) {
    const event = events[i];
    const query = `${event.titulo} ${event.pais}`;

    console.log(`  🔍 Buscando: ${query.substring(0, 50)}...`);
    const imageUrl = await getGoogleImageUrl(query);

    if (imageUrl) {
      event.image_url = imageUrl;
      console.log(`  ✅ Imagen encontrada`);
      updated++;
    } else {
      console.log(`  ❌ No se encontró imagen`);
    }

    // Pausa para no ser bloqueados por Google
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
  console.log(`  📊 ${updated}/${limit} eventos actualizados`);
  return updated;
}

async function main() {
  console.log('🚀 Obteniendo imágenes reales de Google Images...\n');
  console.log('⚠️  MODO PRUEBA: Solo primeros 5 eventos por archivo\n');

  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.startsWith('eventos_Argentina') && f.endsWith('.json'))
    .map(f => path.join(DATA_DIR, f));

  if (files.length === 0) {
    console.log('❌ No se encontraron archivos JSON');
    return;
  }

  for (const file of files) {
    try {
      await processJsonFile(file);
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}`);
    }
  }

  console.log(`\n🎉 Prueba completada!`);
}

main().catch(console.error);
