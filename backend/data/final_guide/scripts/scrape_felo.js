/**
 * SCRIPT PUPPETEER PARA FELO
 * Uso con MCP Puppeteer
 * VERIFICADO: 2025-11-22
 */

const FELO_CONFIG = {
  url: "https://felo.ai",
  selectors: {
    input: "textarea",  // Campo "Ask anything..."
    submit: 'button[aria-label="Send"]',  // CRÍTICO: Este es el selector correcto
    response: ".prose",  // Contenedor de respuesta
    subscriptionButton: "button"  // Para popup de suscripción
  },
  waitTime: 25000,  // Felo tarda más (usa 49 fuentes)
  prompt: `dame por lo menos 20 eventos en {lugar} a partir de hoy y las próximas semanas, necesito nombre, descripción, fecha, lugar, dirección, barrio y precio`
};

// PASO 1: Navegar con viewport grande
// mcp__puppeteer__puppeteer_navigate({
//   url: FELO_CONFIG.url,
//   launchOptions: { headless: false, args: ["--incognito", "--start-maximized", "--window-size=1920,1080"] }
// })

// PASO 2: Llenar prompt (reemplazar {lugar} con la ciudad)
// mcp__puppeteer__puppeteer_fill({ selector: FELO_CONFIG.selectors.input, value: prompt })

// PASO 3: Click en enviar - USAR EXACTAMENTE ESTE SELECTOR
// mcp__puppeteer__puppeteer_click({ selector: 'button[aria-label="Send"]' })

// PASO 4: Si aparece popup de suscripción, buscar botón "gratis" o "free"
/*
mcp__puppeteer__puppeteer_evaluate({ script: `
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.toLowerCase().includes('gratis') || btn.textContent.toLowerCase().includes('free')) {
      btn.click();
      break;
    }
  }
`})
*/

// PASO 5: Extraer respuesta (después de esperar 25 segundos)
// mcp__puppeteer__puppeteer_evaluate({ script: `document.querySelector('.prose')?.innerText` })

// PASO 6: Guardar en raw/felo/{ciudad}_{fecha}.txt

// PROBLEMAS CONOCIDOS:
// - El botón de enviar a veces no responde con puppeteer_click
// - Alternativa: usar JavaScript para simular click
/*
mcp__puppeteer__puppeteer_evaluate({ script: `
  const sendBtn = document.querySelector('button.rounded-full[class*="text-gray-600"]');
  if (sendBtn) sendBtn.click();
`})
*/

module.exports = FELO_CONFIG;
