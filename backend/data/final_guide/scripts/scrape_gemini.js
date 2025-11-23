/**
 * SCRIPT PUPPETEER PARA GEMINI
 * Uso con MCP Puppeteer
 */

const GEMINI_CONFIG = {
  url: "https://gemini.google.com",
  selectors: {
    input: ".ql-editor, textarea, [contenteditable='true']",
    submit: "button[aria-label='Enviar mensaje']",
    response: ".model-response-text, [data-message-author-role='model']"
  },
  waitTime: 15000,
  prompt: `me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} a partir de hoy y las próximas semanas?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas! En formato de tabla con tabs separando las columnas: N°	Nombre del Evento	Descripción	Fecha	Lugar / Dirección	Barrio	Precio	Info Extra`
};

// PASO 1: Navegar
// mcp__puppeteer__puppeteer_navigate({ url: GEMINI_CONFIG.url })

// PASO 2: Llenar prompt (reemplazar {lugar} con la ciudad)
// mcp__puppeteer__puppeteer_fill({ selector: GEMINI_CONFIG.selectors.input, value: prompt })

// PASO 3: Click en enviar
// mcp__puppeteer__puppeteer_click({ selector: GEMINI_CONFIG.selectors.submit })

// PASO 4: Extraer respuesta (después de esperar)
// mcp__puppeteer__puppeteer_evaluate({ script: `document.querySelector('${GEMINI_CONFIG.selectors.response}')?.innerText` })

// PASO 5: Guardar en raw/gemini/{ciudad}_{fecha}.txt

module.exports = GEMINI_CONFIG;
