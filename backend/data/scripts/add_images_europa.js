#!/usr/bin/env node
/**
 * Agrega imágenes de Google a eventos de Europa
 * Usa título o venue para buscar imágenes relevantes
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

const GOOGLE_API_KEY = 'AIzaSyBnASoI0jTHdwiuzugYDwqghzzzDJ44Smg';
const GOOGLE_CX = '06b5ac72c42074af6';

const EUROPA_DIR = path.join(__dirname, '..', 'scrapper_results', 'europa');

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
    console.error(`  ❌ Error buscando imagen: ${error.message.substring(0, 50)}`);
    return null;
  }
}

async function processJSONFile(filePath) {
  console.log(`\n📄 Procesando: ${path.basename(filePath)}`);

  const content = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(content);

  if (!data.eventos || data.eventos.length === 0) {
    console.log('  ⚠️  Sin eventos');
    return 0;
  }

  let added = 0;

  for (let i = 0; i < data.eventos.length; i++) {
    const evento = data.eventos[i];

    // Si ya tiene imagen, skip
    if (evento.image_url) {
      continue;
    }

    // Buscar por título o venue
    const searchQuery = `${evento.title} ${evento.venue || evento.city} event`;

    console.log(`  [${i + 1}/${data.eventos.length}] ${evento.title.substring(0, 40)}...`);

    const imageUrl = await getGoogleImage(searchQuery);

    if (imageUrl) {
      evento.image_url = imageUrl;
      added++;
      console.log(`    ✅ Imagen encontrada`);
    } else {
      console.log(`    ⚠️  Sin imagen`);
    }

    // Rate limit: esperar 1 segundo entre requests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Guardar JSON actualizado
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
  console.log(`  💾 ${added} imágenes agregadas`);

  return added;
}

async function main() {
  console.log('='.repeat(70));
  console.log('🖼️  AGREGANDO IMÁGENES A EVENTOS DE EUROPA');
  console.log('='.repeat(70));
  console.log(`📂 Carpeta: ${EUROPA_DIR}\n`);

  let totalAdded = 0;
  let totalFiles = 0;

  // Recorrer todas las carpetas de países
  const countries = fs.readdirSync(EUROPA_DIR);

  for (const country of countries) {
    const countryPath = path.join(EUROPA_DIR, country);

    if (!fs.statSync(countryPath).isDirectory()) {
      continue;
    }

    console.log(`\n🌍 ${country.toUpperCase()}`);
    console.log('-'.repeat(70));

    const files = fs.readdirSync(countryPath);

    for (const file of files) {
      if (!file.endsWith('.json')) {
        continue;
      }

      const filePath = path.join(countryPath, file);
      totalFiles++;

      const added = await processJSONFile(filePath);
      totalAdded += added;
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('🎉 PROCESO COMPLETADO');
  console.log('='.repeat(70));
  console.log(`📊 Archivos procesados: ${totalFiles}`);
  console.log(`🖼️  Total imágenes agregadas: ${totalAdded}`);
  console.log('='.repeat(70) + '\n');
}

main().catch(console.error);
