const axios = require('axios');

async function buscarPatrones() {
  try {
    const query = 'gato';
    console.log(`Buscando patrones en respuesta de: "${query}"\n`);

    const response = await axios.get(
      `https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
      }
    );

    const patrones = [
      { nombre: 'imgurl', regex: /imgurl=([^&\s"']+)/g },
      { nombre: 'imgrefurl', regex: /imgrefurl=([^&\s"']+)/g },
      { nombre: 'imgres', regex: /imgres=([^&\s"']+)/g },
      { nombre: 'https URLs', regex: /(https:\/\/[^\s"'<>)]+\.jpg)/gi },
      { nombre: 'https URLs (png)', regex: /(https:\/\/[^\s"'<>)]+\.png)/gi },
      { nombre: 'ou= URLs', regex: /ou=([^&\s"']+)/g }
    ];

    for (const patron of patrones) {
      const matches = response.data.match(patron.regex);
      console.log(`${patron.nombre}: ${matches ? matches.length : 0} matches`);
      if (matches && matches.length > 0) {
        console.log(`  Ejemplo: ${matches[0].substring(0, 100)}`);
      }
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

buscarPatrones();
