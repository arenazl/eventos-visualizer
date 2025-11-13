/**
 * Script para actualizar imágenes de eventos en MySQL
 * Busca eventos con imágenes de Picsum y les pone imágenes reales de Google
 */

const { obtenerPrimeraImagen } = require('./buscar-primera-imagen');
const mysql = require('mysql2/promise');
require('dotenv').config();

async function main() {
  console.log('🚀 Actualizando imágenes de eventos en MySQL\n');

  // Conectar a MySQL
  const connection = await mysql.createConnection({
    host: process.env.MYSQL_HOST || 'localhost',
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'events'
  });

  console.log('✅ Conectado a MySQL\n');

  // Buscar TODOS los eventos de Buenos Aires sin imagen real
  const [eventos] = await connection.execute(`
    SELECT id, title, city, image_url
    FROM events
    WHERE city = 'Buenos Aires'
    AND (image_url IS NULL OR image_url LIKE '%picsum%' OR image_url LIKE '%placeholder%')
  `);

  console.log(`📊 ${eventos.length} eventos de Buenos Aires a procesar\n`);

  let updated = 0;
  let errors = 0;

  for (let i = 0; i < eventos.length; i++) {
    const evento = eventos[i];
    const displayName = evento.title.substring(0, 50);

    console.log(`🔍 [${i + 1}/${eventos.length}] ${displayName}...`);

    try {
      // Buscar imagen en Google usando el título
      const imageUrl = await obtenerPrimeraImagen(evento.title);

      if (imageUrl && !imageUrl.includes('gstatic')) {
        // Actualizar en MySQL
        await connection.execute(
          'UPDATE events SET image_url = ? WHERE id = ?',
          [imageUrl, evento.id]
        );
        console.log(`  ✅ Imagen actualizada`);
        updated++;
      } else {
        console.log(`  ⚠️  Solo logo de Google`);
      }

    } catch (error) {
      console.log(`  ❌ Error: ${error.message.substring(0, 50)}`);
      errors++;
    }

    // Pausa para no ser bloqueado
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mostrar progreso cada 50 eventos
    if ((i + 1) % 50 === 0) {
      const porcentaje = ((i + 1) / eventos.length * 100).toFixed(1);
      console.log(`\n💾 Progreso: ${i + 1}/${eventos.length} (${porcentaje}%) - ${updated} actualizados, ${errors} errores\n`);
    }
  }

  await connection.end();

  console.log('\n' + '='.repeat(60));
  console.log('🎉 Proceso completado!');
  console.log(`✅ Imágenes actualizadas: ${updated}`);
  console.log(`❌ Errores: ${errors}`);
  console.log('='.repeat(60) + '\n');
}

main().catch(console.error);
