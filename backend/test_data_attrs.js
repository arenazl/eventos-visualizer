const puppeteer = require('puppeteer');

async function debugDataAttrs() {
  console.log('🔍 Buscando atributos data-* en las imágenes\n');

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto('https://www.google.com/search?q=Festival Joy&tbm=isch', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    await page.waitForSelector('img', { timeout: 5000 });
    await new Promise(resolve => setTimeout(resolve, 3000));

    const atributos = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));

      return imgs.slice(0, 5).map(img => {
        const attrs = {};
        for (let attr of img.attributes) {
          if (attr.value && attr.value.length > 10) {
            attrs[attr.name] = attr.value.substring(0, 80) + '...';
          }
        }
        return attrs;
      });
    });

    console.log('Atributos de las primeras 5 imágenes:\n');
    atributos.forEach((attrs, i) => {
      console.log(`Imagen ${i + 1}:`);
      console.log(JSON.stringify(attrs, null, 2));
      console.log('---');
    });

    await browser.close();

  } catch (error) {
    await browser.close();
    console.error('Error:', error.message);
  }
}

debugDataAttrs().catch(console.error);
