/**
 * Script final para agregar imágenes usando Puppeteer + Google Images
 */

const { obtenerPrimeraImagen } = require('./buscar-primera-imagen');
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'image-better');

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.basename(filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  const events = JSON.parse(data);

  let updated = 0;
  let errores = 0;
  const LIMIT = events.length; // Procesar TODOS los eventos

  for (let i = 0; i < Math.min(LIMIT, events.length); i++) {
    const event = events[i];

    // Saltar si ya tiene imagen_url
    if (event.image_url) {
      console.log(`  ⏭️  [${i + 1}/${events.length}] Ya tiene imagen`);
      continue;
    }

    // Query: solo título (prueba con 10 eventos)
    const query = event.titulo;

    console.log(`  🔍 [${i + 1}/${events.length}] ${event.titulo.substring(0, 40)}...`);

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
      fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
      console.log(`  💾 Progreso guardado (${updated} actualizados, ${errores} errores)`);
    }
  }

  // Guardar al final
  fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
  console.log(`  📊 Total: ${updated}/${LIMIT} actualizados, ${errores} errores`);
  return updated;
}

async function main() {
  console.log('🚀 Agregando imágenes de Google Images...\n');

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
      console.error(`  ❌ Error en archivo: ${error.message}`);
    }
  }

  console.log(`\n🎉 Proceso completado!`);
  console.log(`✅ Total eventos actualizados: ${totalUpdated}`);
}

main().catch(console.error);
