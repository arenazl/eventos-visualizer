/**
 * Script para obtener imágenes usando NewsAPI
 * Obtener API Key gratis en: https://newsapi.org/register
 */

const NewsAPI = require('newsapi');
const fs = require('fs');
const path = require('path');

// API Key de NewsAPI (configurar en .env o aquí)
const API_KEY = process.env.NEWSAPI_KEY || 'TU_API_KEY_AQUI';
const newsapi = new NewsAPI(API_KEY);

const DATA_DIR = path.join(__dirname, 'data', 'image-better');

async function buscarImagenNoticia(query) {
  try {
    const response = await newsapi.v2.everything({
      q: query,
      language: 'es',
      pageSize: 5, // Traer 5 artículos
      sortBy: 'relevancy'
    });

    if (response.articles && response.articles.length > 0) {
      // Buscar el primer artículo con imagen
      const conImagen = response.articles.find(art => art.urlToImage);
      return conImagen ? conImagen.urlToImage : null;
    }

    return null;

  } catch (error) {
    console.error(`  ⚠️ Error API: ${error.message}`);
    return null;
  }
}

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.basename(filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  const events = JSON.parse(data);

  let updated = 0;
  const LIMIT = 5; // Solo procesar 5 para probar

  for (let i = 0; i < Math.min(LIMIT, events.length); i++) {
    const event = events[i];
    const query = event.titulo;

    console.log(`  🔍 [${i + 1}/${LIMIT}] ${query.substring(0, 40)}...`);

    const imageUrl = await buscarImagenNoticia(query);

    if (imageUrl) {
      event.image_url = imageUrl;
      console.log(`  ✅ Imagen encontrada`);
      updated++;
    } else {
      console.log(`  ❌ No se encontró`);
    }

    // Pausa para respetar rate limits (gratis: 100 requests/día)
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
  console.log(`  📊 Total actualizado: ${updated}/${LIMIT}`);
  return updated;
}

async function main() {
  console.log('🚀 Obteniendo imágenes usando NewsAPI...\n');
  console.log('⚠️  MODO PRUEBA: Solo primeros 5 eventos por archivo\n');

  if (API_KEY === 'TU_API_KEY_AQUI') {
    console.log('❌ ERROR: Necesitas configurar NEWSAPI_KEY');
    console.log('   Obtén una gratis en: https://newsapi.org/register');
    console.log('   Luego agrega: export NEWSAPI_KEY=tu_clave');
    return;
  }

  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.startsWith('eventos_Argentina') && f.endsWith('.json'))
    .map(f => path.join(DATA_DIR, f));

  if (files.length === 0) {
    console.log('❌ No se encontraron archivos JSON');
    return;
  }

  let totalUpdated = 0;
  for (const file of files) {
    try {
      const count = await processJsonFile(file);
      totalUpdated += count;
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}`);
    }
  }

  console.log(`\n🎉 Prueba completada!`);
  console.log(`✅ Total eventos actualizados: ${totalUpdated}`);
  console.log(`\n💡 Plan gratuito: 100 requests/día`);
}

main().catch(console.error);
