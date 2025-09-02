# 🌍 Eventos Visualizer - Global Traveler App

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 🚀 IA-First Event Discovery

The smartest way to find events while traveling. Currently supports:

- 🇪🇸 **Spain**: Barcelona, Madrid
- 🇦🇷 **Argentina**: Buenos Aires, Mendoza, Córdoba  
- 🇫🇷 **France**: Paris (coming soon)
- 🇲🇽 **Mexico**: Mexico City (coming soon)

## ✨ Features

- **Natural Language Search**: "eventos románticos en barcelona"
- **City-Specific Scrapers**: Local venues and events
- **Real-time Streaming**: WebSocket updates
- **Smart Recommendations**: AI-powered contextual suggestions
- **Multiple Sources**: Eventbrite, Ticketmaster, local venues

## 🔧 Quick Deploy

1. Click "Deploy to Heroku" button above
2. Set your API keys (Gemini is required)
3. Deploy!

## 📡 API Endpoints

- `GET /health` - Health check
- `POST /api/ai/chat` - Natural language search
- `GET /api/events` - List events
- `WS /ws/search-events` - Real-time search

## 🌟 Example Queries

```bash
curl -X POST "https://your-app.herokuapp.com/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "conciertos en barcelona este fin de semana"}'
```

## 🗺️ Supported Cities

Each city has specialized scrapers for local venues and events:

### Barcelona 🇪🇸
- Palau de la Música Catalana
- Camp Nou, Razzmatazz
- TimeOut Barcelona, CCCB

### Buenos Aires 🇦🇷  
- Luna Park, Teatro Colón
- Eventbrite Argentina
- Local cultural venues

### More cities coming soon! 🚀

---

Built with ❤️ for global travelers