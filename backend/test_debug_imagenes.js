const puppeteer = require('puppeteer');

async function debugImagenes() {
  console.log('🔍 Debug: analizando qué imágenes encuentra Puppeteer\n');

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto('https://www.google.com/search?q=Festival Joy&tbm=isch', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    await page.waitForSelector('img', { timeout: 5000 });

    // Esperar un poco más para que carguen las imágenes
    await new Promise(resolve => setTimeout(resolve, 3000));

    const todasLasImagenes = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));
      return imgs.map(img => ({
        src: img.src.substring(0, 100),
        hasHttp: img.src.startsWith('http'),
        hasGstatic: img.src.includes('gstatic'),
        alt: img.alt || '',
        width: img.width,
        height: img.height
      }));
    });

    console.log(`Total imágenes encontradas: ${todasLasImagenes.length}\n`);

    console.log('Primeras 10 imágenes:');
    todasLasImagenes.slice(0, 10).forEach((img, i) => {
      console.log(`\n${i + 1}. ${img.hasGstatic ? '❌ GSTATIC' : '✅ REAL'}`);
      console.log(`   src: ${img.src}`);
      console.log(`   ${img.width}x${img.height}`);
    });

    await browser.close();

  } catch (error) {
    await browser.close();
    console.error('Error:', error.message);
  }
}

debugImagenes().catch(console.error);
