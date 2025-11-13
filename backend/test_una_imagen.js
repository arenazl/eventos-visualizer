const { obtenerPrimeraImagen } = require('./buscar-primera-imagen');

async function test() {
  console.log('🧪 Test: buscando imagen de "Festival Joy"...\n');

  const query = 'gato';
  console.log(`Query: "${query}"\n`);

  const url = await obtenerPrimeraImagen(query);

  console.log('Resultado:');
  console.log('URL completa:', url);
  console.log('¿Contiene gstatic?:', url ? url.includes('gstatic') : 'null');
  console.log('¿Es null?:', url === null);
}

test().catch(console.error);
