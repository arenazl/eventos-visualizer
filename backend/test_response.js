const axios = require('axios');

async function debugResponse() {
  try {
    const query = 'gato';
    console.log(`Buscando: "${query}"\n`);

    const response = await axios.get(
      `https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
      }
    );

    console.log('Status:', response.status);
    console.log('Content-Type:', response.headers['content-type']);
    console.log('\nTamaño de respuesta:', response.data.length, 'caracteres\n');

    // Buscar todas las ocurrencias de imgurl
    const matches = response.data.match(/imgurl/g);
    console.log('Ocurrencias de "imgurl":', matches ? matches.length : 0);

    // Mostrar las primeras apariciones
    const index = response.data.indexOf('imgurl');
    if (index !== -1) {
      console.log('\nContexto de la primera aparición:');
      console.log(response.data.substring(index, index + 200));
    } else {
      console.log('\n❌ No se encontró "imgurl" en la respuesta');
      console.log('\nPrimeros 500 caracteres de la respuesta:');
      console.log(response.data.substring(0, 500));
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

debugResponse();
