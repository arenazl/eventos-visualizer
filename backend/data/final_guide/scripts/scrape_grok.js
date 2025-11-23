/**
 * SCRIPT PUPPETEER PARA GROK
 * Uso con MCP Puppeteer
 */

const GROK_CONFIG = {
  url: "https://grok.com",
  selectors: {
    input: "textarea",
    submit: "button[aria-label='Send']",
    response: ".response-text, .message-content",
    captchaCheckbox: "input[type='checkbox']"
  },
  waitTime: 15000,
  prompt: `me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} a partir de hoy y las próximas semanas?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas! En formato de tabla con tabs separando las columnas: N°	Nombre del Evento	Descripción	Fecha	Lugar / Dirección	Barrio	Precio (ARS)	Info Extra`
};

// PASO 1: Navegar
// mcp__puppeteer__puppeteer_navigate({ url: GROK_CONFIG.url, launchOptions: { headless: false, args: ["--incognito", "--start-maximized"] } })

// PASO 2: Si hay captcha Cloudflare, esperar o clickear checkbox
// mcp__puppeteer__puppeteer_click({ selector: GROK_CONFIG.selectors.captchaCheckbox })

// PASO 3: Llenar prompt (reemplazar {lugar} con la ciudad)
// mcp__puppeteer__puppeteer_fill({ selector: GROK_CONFIG.selectors.input, value: prompt })

// PASO 4: Click en enviar
// mcp__puppeteer__puppeteer_click({ selector: GROK_CONFIG.selectors.submit })

// PASO 5: Extraer respuesta (después de esperar)
// mcp__puppeteer__puppeteer_evaluate({ script: `document.querySelector('${GROK_CONFIG.selectors.response}')?.innerText` })

// PASO 6: Guardar en raw/grok/{ciudad}_{fecha}.txt

module.exports = GROK_CONFIG;
