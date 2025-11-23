require('dotenv').config();
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;
const GOOGLE_CX = process.env.GOOGLE_CX;

const PARSED_BASE_DIR = path.join(__dirname, '..', 'scrapper_results', 'parsed');

async function getGoogleImage(searchQuery) {
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
    // Si es rate limit, propagar error para detener
    if (error.response && error.response.status === 429) {
      throw new Error('RATE_LIMIT');
    }
    return null;
  }
}

// Triple fallback: título completo → título reducido → venue
async function getImageWithFallback(title, venue, city) {
  // Intento 1: Título completo + venue + city
  let searchQuery = `${title} ${venue} ${city} event`;
  let imageUrl = await getGoogleImage(searchQuery);

  if (imageUrl) {
    console.log(`    ✅ Imagen (título completo)`);
    return imageUrl;
  }

  // Intento 2: Título reducido (primeras 3 palabras) + city
  const reducedTitle = title.split(' ').slice(0, 3).join(' ');
  if (reducedTitle && reducedTitle !== title) {
    await new Promise(resolve => setTimeout(resolve, 500));
    searchQuery = `${reducedTitle} ${city} event`;
    imageUrl = await getGoogleImage(searchQuery);

    if (imageUrl) {
      console.log(`    ✅ Imagen (título reducido)`);
      return imageUrl;
    }
  }

  // Intento 3: Solo venue + city
  if (venue) {
    await new Promise(resolve => setTimeout(resolve, 500));
    searchQuery = `${venue} ${city}`;
    imageUrl = await getGoogleImage(searchQuery);

    if (imageUrl) {
      console.log(`    ✅ Imagen (venue)`);
      return imageUrl;
    }
  }

  console.log(`    ⚠️  Sin imagen (3 intentos fallidos)`);
  return null;
}

async function processJSONFile(filePath) {
  console.log(`\n📄 Procesando: ${path.basename(filePath)}`);

  const content = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(content);

  // Detectar estructura
  let events = [];
  if (data.eventos) {
    events = data.eventos;
  } else if (data.events) {
    events = data.events;
  } else if (Array.isArray(data)) {
    events = data;
  }

  if (!events || events.length === 0) {
    console.log('  ⚠️  Sin eventos');
    return 0;
  }

  let added = 0;

  for (let i = 0; i < events.length; i++) {
    const evento = events[i];

    // Si ya tiene imagen, skip
    if (evento.image_url) {
      continue;
    }

    // Buscar por título o venue
    const title = evento.title || evento.nombre || evento.titulo || '';
    const venue = evento.venue || evento.lugar || '';
    const city = evento.city || evento.ciudad || data.city || data.ciudad || '';

    console.log(`  [${i + 1}/${events.length}] ${title.substring(0, 40)}...`);

    try {
      // Usar triple fallback
      const imageUrl = await getImageWithFallback(title, venue, city);

      if (imageUrl) {
        evento.image_url = imageUrl;
        added++;
      }
    } catch (error) {
      if (error.message === 'RATE_LIMIT') {
        console.log(`\n⚠️  ⚠️  ⚠️  LÍMITE DIARIO ALCANZADO ⚠️  ⚠️  ⚠️`);
        console.log(`Guardando progreso hasta aquí...\n`);
        break; // Salir del loop
      }
      console.log(`    ❌ Error: ${error.message}`);
    }

    // Rate limit: esperar 1 segundo entre eventos
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Guardar JSON actualizado
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
  console.log(`  💾 ${added} imágenes agregadas`);

  return added;
}

async function main() {
  console.log('======================================================================');
  console.log('🖼️  AGREGANDO IMÁGENES A EVENTOS');
  console.log('======================================================================');
  console.log(`📂 Carpeta base: ${PARSED_BASE_DIR}\n`);

  if (!GOOGLE_API_KEY || !GOOGLE_CX) {
    console.log('❌ ERROR: Faltan credenciales de Google en .env');
    console.log('   Necesitas: GOOGLE_API_KEY y GOOGLE_CX');
    process.exit(1);
  }

  // Obtener todas las fuentes (gemini, felo, grok, etc.)
  const sources = fs.readdirSync(PARSED_BASE_DIR).filter(f =>
    fs.statSync(path.join(PARSED_BASE_DIR, f)).isDirectory()
  );

  console.log(`🔍 Fuentes encontradas: ${sources.join(', ')}\n`);

  let totalFiles = 0;
  let totalAdded = 0;

  for (const source of sources) {
    const sourceDir = path.join(PARSED_BASE_DIR, source);
    console.log(`\n📁 Procesando fuente: ${source.toUpperCase()}`);
    console.log('─'.repeat(70));

    // Obtener todos los archivos JSON de esta fuente
    const files = fs.readdirSync(sourceDir).filter(f => f.endsWith('.json'));
    console.log(`📊 ${files.length} archivos JSON encontrados en ${source}\n`);

    for (const file of files) {
      const filePath = path.join(sourceDir, file);
      const added = await processJSONFile(filePath);
      totalAdded += added;
      totalFiles++;
    }
  }

  console.log('\n======================================================================');
  console.log('🎉 PROCESO COMPLETADO');
  console.log('======================================================================');
  console.log(`📁 Fuentes procesadas: ${sources.length} (${sources.join(', ')})`);
  console.log(`📊 Archivos procesados: ${totalFiles}`);
  console.log(`🖼️  Total imágenes agregadas: ${totalAdded}`);
  console.log('======================================================================\n');
}

main().catch(console.error);
