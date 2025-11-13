const axios = require('axios');

async function obtenerPrimeraImagen(query) {
  try {
    const response = await axios.get(
      `https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
      }
    );

    // Buscar URLs de imágenes en el HTML (Google cambió el formato)
    const jpgMatch = response.data.match(/(https:\/\/[^\s"'<>)]+\.jpg)/i);
    if (jpgMatch) return jpgMatch[1];

    const pngMatch = response.data.match(/(https:\/\/[^\s"'<>)]+\.png)/i);
    if (pngMatch) return pngMatch[1];

    const jpegMatch = response.data.match(/(https:\/\/[^\s"'<>)]+\.jpeg)/i);
    if (jpegMatch) return jpegMatch[1];

    return null;

  } catch (error) {
    return null;
  }
}

module.exports = { obtenerPrimeraImagen };
