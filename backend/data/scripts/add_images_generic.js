/**
 * Script genérico para agregar imágenes a eventos
 * Busca todos los archivos JSON en una ubicación y agrega imágenes desde Google
 *
 * Uso:
 *   node add_images_generic.js scrapper_results/europa
 *   node add_images_generic.js data/eventos
 *   node add_images_generic.js ./mis_eventos
 */

const { obtenerPrimeraImagen } = require('./buscar-primera-imagen');
const fs = require('fs');
const path = require('path');

// Obtener ubicación desde argumentos
const targetPath = process.argv[2];

if (!targetPath) {
  console.log('❌ Uso: node add_images_generic.js <ruta/carpeta>');
  process.exit(1);
}

const BASE_DIR = path.join(__dirname, '..');
const TARGET_DIR = path.isAbsolute(targetPath) 
  ? targetPath 
  : path.join(BASE_DIR, targetPath);

console.log(`📂 Directorio objetivo: ${TARGET_DIR}`);

/**
 * Encuentra todos los JSONs recursivamente
 */
function findJsonFiles(dir) {
  let results = [];
  
  try {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        results = results.concat(findJsonFiles(fullPath));
      } else if (item.endsWith('.json')) {
        results.push(fullPath);
      }
    }
  } catch (error) {
    console.log(`  ⚠️  No se pudo leer directorio: ${dir}`);
  }

  return results;
}

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.relative(BASE_DIR, filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  let cityData;

  try {
    cityData = JSON.parse(data);
  } catch (error) {
    console.log(`  ❌ Error parseando JSON: ${error.message}`);
    return 0;
  }

  // Detectar estructura del JSON
  let events = [];

  if (cityData.eventos && Array.isArray(cityData.eventos)) {
    // Estructura: {ciudad, pais, eventos: [...]}
    events = cityData.eventos;
  } else if (Array.isArray(cityData)) {
    // Estructura: [...eventos...]
    events = cityData;
  } else if (cityData.eventos_ferias_festivales || cityData.recitales_shows_fiestas) {
    // Estructura Puerto Rico: {eventos_ferias_festivales: [...], recitales_shows_fiestas: [...]}
    events = [
      ...(cityData.eventos_ferias_festivales || []),
      ...(cityData.recitales_shows_fiestas || [])
    ];
  } else {
    console.log('  ⚠️  Estructura de JSON no reconocida o sin eventos');
    return 0;
  }

  if (events.length === 0) {
    console.log('  ⚠️  No hay eventos en este archivo');
    return 0;
  }

  let updated = 0;
  let errores = 0;
  let skipped = 0;

  for (let i = 0; i < events.length; i++) {
    const event = events[i];

    // Saltar si ya tiene imagen_url
    if (event.image_url) {
      skipped++;
      if (skipped <= 3) {
        console.log(`  ⏭️  [${i + 1}/${events.length}] Ya tiene imagen`);
      } else if (skipped === 4) {
        console.log(`  ⏭️  ... (saltando eventos con imagen)`);
      }
      continue;
    }

    // Detectar campo de título (nombre, titulo, title)
    const query = event.nombre || event.titulo || event.title || 'evento';
    const displayName = query.substring(0, 50);

    console.log(`  🔍 [${i + 1}/${events.length}] ${displayName}...`);

    try {
      const imageUrl = await obtenerPrimeraImagen(query);

      if (imageUrl && !imageUrl.includes('gstatic')) {
        event.image_url = imageUrl;
        console.log(`  ✅ Imagen encontrada`);
        updated++;
      } else {
        console.log(`  ⚠️  Solo logo de Google`);
      }

    } catch (error) {
      console.log(`  ❌ Error: ${error.message.substring(0, 50)}`);
      errores++;
    }

    // Pausa para no ser bloqueado
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Guardar progreso cada 10 eventos
    if ((i + 1) % 10 === 0) {
      const outputData = Array.isArray(cityData) ? events : cityData;
      fs.writeFileSync(filepath, JSON.stringify(outputData, null, 2), 'utf8');
      console.log(`  💾 Progreso guardado (${updated} actualizados, ${errores} errores)`);
    }
  }

  // Guardar al final
  const outputData = Array.isArray(cityData) ? events : cityData;
  fs.writeFileSync(filepath, JSON.stringify(outputData, null, 2), 'utf8');
  console.log(`  📊 Total: ${updated}/${events.length} actualizados, ${skipped} ya tenían, ${errores} errores`);
  return updated;
}

async function main() {
  console.log('🚀 Script genérico para agregar imágenes a eventos\n');

  if (!fs.existsSync(TARGET_DIR)) {
    console.log(`❌ Directorio no existe: ${TARGET_DIR}`);
    return;
  }

  const files = findJsonFiles(TARGET_DIR);

  if (files.length === 0) {
    console.log('❌ No se encontraron archivos JSON en la ubicación');
    return;
  }

  console.log(`📊 ${files.length} archivos JSON encontrados\n`);

  let totalUpdated = 0;
  for (const file of files) {
    try {
      const count = await processJsonFile(file);
      totalUpdated += count;
    } catch (error) {
      console.error(`  ❌ Error en archivo: ${error.message}`);
    }
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`🎉 Proceso completado!`);
  console.log(`✅ Total eventos actualizados: ${totalUpdated}`);
  console.log(`📂 Archivos procesados: ${files.length}`);
  console.log(`${'='.repeat(60)}\n`);
}

main().catch(console.error);