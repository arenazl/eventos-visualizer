/**
 * Script para agregar URLs de imágenes usando Unsplash API
 * Es gratuito y no requiere complicaciones con Google Images
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const DATA_DIR = path.join(__dirname, 'data', 'image-better');

// Unsplash Access Key (necesitas crear una cuenta gratis en https://unsplash.com/developers)
// Por ahora usamos URLs de Unsplash Source que no requiere API key
function getImageUrl(query) {
  const encoded = encodeURIComponent(query);
  // Unsplash Source devuelve una URL directa a una imagen aleatoria relacionada
  return `https://source.unsplash.com/800x600/?${encoded}`;
}

async function processJsonFile(filepath) {
  console.log(`\n📄 Procesando: ${path.basename(filepath)}`);

  const data = fs.readFileSync(filepath, 'utf8');
  const events = JSON.parse(data);

  let updated = 0;
  for (let i = 0; i < events.length; i++) {
    const event = events[i];
    const query = `${event.titulo} ${event.pais}`;
    event.image_url = getImageUrl(query);
    updated++;

    if ((i + 1) % 50 === 0) {
      console.log(`  ✓ ${i + 1}/${events.length} eventos procesados`);
    }
  }

  fs.writeFileSync(filepath, JSON.stringify(events, null, 2), 'utf8');
  console.log(`  ✅ ${updated} eventos actualizados`);
  return updated;
}

async function main() {
  console.log('🚀 Iniciando proceso de agregar imágenes...\n');

  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.startsWith('eventos_') && f.endsWith('.json'))
    .map(f => path.join(DATA_DIR, f));

  if (files.length === 0) {
    console.log('❌ No se encontraron archivos JSON');
    return;
  }

  console.log(`📊 Archivos encontrados: ${files.length}\n`);

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
  console.log(`📁 Archivos procesados: ${files.length}`);
}

main().catch(console.error);
