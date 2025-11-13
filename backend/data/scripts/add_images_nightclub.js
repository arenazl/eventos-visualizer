#!/usr/bin/env node
/**
 * Agrega imágenes de Google SOLO a nightclub.json
 * Triple fallback: título completo → título reducido → venue
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

const GOOGLE_API_KEY = 'AIzaSyBnASoI0jTHdwiuzugYDwqghzzzDJ44Smg';
const GOOGLE_CX = '06b5ac72c42074af6';

const NIGHTCLUB_FILE = path.join(__dirname, '..', 'scrapper_results', 'latinamerica', 'sudamerica', 'argentina', 'buenosaliens', 'nightclub.json');

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

async function main() {
  console.log('='.repeat(70));
  console.log('🖼️  AGREGANDO IMÁGENES A NIGHTCLUB.JSON');
  console.log('='.repeat(70));
  console.log(`📂 Archivo: ${NIGHTCLUB_FILE}\n`);

  if (!fs.existsSync(NIGHTCLUB_FILE)) {
    console.log('❌ Archivo nightclub.json no encontrado');
    return;
  }

  const content = fs.readFileSync(NIGHTCLUB_FILE, 'utf8');
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
    console.log('⚠️  Sin eventos');
    return;
  }

  console.log(`📊 ${events.length} eventos encontrados\n`);

  let added = 0;
  let skipped = 0;

  for (let i = 0; i < events.length; i++) {
    const evento = events[i];

    // Si ya tiene imagen, skip
    if (evento.image_url) {
      skipped++;
      continue;
    }

    // Buscar por título o venue
    const title = evento.title || evento.nombre || evento.titulo || '';
    const venue = evento.venue || evento.lugar || '';
    const city = evento.city || evento.ciudad || data.city || data.ciudad || 'Buenos Aires';

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
  fs.writeFileSync(NIGHTCLUB_FILE, JSON.stringify(data, null, 2), 'utf8');

  console.log('\n' + '='.repeat(70));
  console.log('🎉 PROCESO COMPLETADO');
  console.log('='.repeat(70));
  console.log(`✅ Imágenes agregadas: ${added}`);
  console.log(`⏭️  Ya tenían imagen: ${skipped}`);
  console.log(`📊 Total eventos: ${events.length}`);
  console.log('='.repeat(70) + '\n');
}

main().catch(console.error);
