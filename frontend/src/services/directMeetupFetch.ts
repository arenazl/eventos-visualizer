/**
 * Direct Meetup Fetch - Simple HTTP call without backend
 */

export async function fetchMeetupEventsDirect(location: string = 'us--fl--Miami') {
  const url = `https://www.meetup.com/find/?location=${location}&source=EVENTS`;
  
  try {
    // Note: This will likely hit CORS issues when called directly from browser
    // Meetup blocks direct browser requests for security
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const html = await response.text();
    
    // Parse the HTML to extract event data
    // In reality, you'd need to parse the HTML or find JSON data in the page
    console.log('Raw HTML received:', html.substring(0, 500));
    
    // Meetup embeds JSON data in their HTML, look for it
    const jsonMatch = html.match(/window\.__NEXT_DATA__\s*=\s*({.*?})<\/script>/);
    if (jsonMatch) {
      const jsonData = JSON.parse(jsonMatch[1]);
      console.log('Found embedded JSON data:', jsonData);
      return jsonData;
    }

    return { error: 'Could not parse Meetup data' };
    
  } catch (error) {
    console.error('Error fetching Meetup events:', error);
    
    // CORS error expected - browsers block cross-origin requests
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      return {
        error: 'CORS blocked - Direct browser requests to Meetup are not allowed',
        solution: 'Use a backend proxy or CORS proxy service',
        alternatives: [
          '1. Route through your backend API',
          '2. Use a CORS proxy like cors-anywhere',
          '3. Use Meetup\'s official API with authentication',
          '4. Scrape server-side with Puppeteer/Playwright'
        ]
      };
    }
    
    return { error: error.message };
  }
}

// Alternative using CORS proxy (for development only!)
export async function fetchMeetupViaProxy(location: string = 'us--fl--Miami') {
  // Public CORS proxies (use cautiously, only for development)
  const corsProxies = [
    'https://cors-anywhere.herokuapp.com/',
    'https://api.allorigins.win/raw?url=',
    'https://corsproxy.io/?'
  ];
  
  const meetupUrl = `https://www.meetup.com/find/?location=${location}&source=EVENTS`;
  const proxyUrl = corsProxies[0] + encodeURIComponent(meetupUrl);
  
  try {
    const response = await fetch(proxyUrl);
    const data = await response.text();
    
    // Extract JSON from HTML
    const jsonMatch = data.match(/window\.__NEXT_DATA__\s*=\s*({.*?})<\/script>/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1]);
    }
    
    return { error: 'Could not extract data from Meetup page' };
    
  } catch (error) {
    return { error: `Proxy request failed: ${error.message}` };
  }
}