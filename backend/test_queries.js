/**
 * Test para comparar diferentes queries y ver cuál da mejores resultados
 */

const NewsAPI = require('newsapi');
const fs = require('fs');
const path = require('path');

const API_KEY = 'e5d1536b1d6448c29fa1eab6b5e8d09a';
const newsapi = new NewsAPI(API_KEY);

async function testQuery(query, label) {
  try {
    const response = await newsapi.v2.everything({
      q: query,
      language: 'es',
      pageSize: 5,
      sortBy: 'relevancy'
    });

    const conImagen = response.articles.filter(art => art.urlToImage);

    console.log(`\n${label}:`);
    console.log(`  Query: "${query}"`);
    console.log(`  Resultados: ${response.articles.length} artículos, ${conImagen.length} con imagen`);

    if (conImagen.length > 0) {
      console.log(`  ✅ Primera imagen: ${conImagen[0].urlToImage.substring(0, 60)}...`);
      console.log(`     Título artículo: ${conImagen[0].title.substring(0, 60)}...`);
      return conImagen[0].urlToImage;
    } else {
      console.log(`  ❌ No se encontraron imágenes`);
      return null;
    }

  } catch (error) {
    console.log(`  ⚠️ Error: ${error.message}`);
    return null;
  }
}

async function main() {
  console.log('🔬 PRUEBA DE QUERIES - NewsAPI\n');
  console.log('Probando con un evento de ejemplo...\n');

  // Leer un evento real
  const dataPath = path.join(__dirname, 'data', 'image-better', 'eventos_Argentina.json');
  const events = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

  const evento = events[0]; // Festival Joy

  console.log(`📌 Evento de prueba:`);
  console.log(`   Título: ${evento.titulo}`);
  console.log(`   País: ${evento.pais}`);
  console.log(`   Descripción: ${evento.descripcion.substring(0, 100)}...`);

  // Probar 3 variantes
  const img1 = await testQuery(evento.titulo, '1️⃣  SOLO TÍTULO');
  await new Promise(r => setTimeout(r, 1000));

  const img2 = await testQuery(`${evento.titulo} ${evento.descripcion}`, '2️⃣  TÍTULO + DESCRIPCIÓN');
  await new Promise(r => setTimeout(r, 1000));

  const img3 = await testQuery(`${evento.titulo} ${evento.pais}`, '3️⃣  TÍTULO + PAÍS');

  console.log(`\n\n📊 RESUMEN:`);
  console.log(`   Solo título: ${img1 ? '✅ SÍ' : '❌ NO'}`);
  console.log(`   Título + descripción: ${img2 ? '✅ SÍ' : '❌ NO'}`);
  console.log(`   Título + país: ${img3 ? '✅ SÍ' : '❌ NO'}`);

  console.log(`\n💡 RECOMENDACIÓN:`);
  if (img1 && img2 && img3) {
    console.log(`   Las 3 variantes funcionan. Usar la más simple: SOLO TÍTULO`);
  } else if (img3) {
    console.log(`   TÍTULO + PAÍS da mejores resultados`);
  } else if (img2) {
    console.log(`   TÍTULO + DESCRIPCIÓN funciona mejor`);
  } else if (img1) {
    console.log(`   SOLO TÍTULO es suficiente`);
  } else {
    console.log(`   Ninguna variante funcionó para este evento`);
  }
}

main().catch(console.error);
