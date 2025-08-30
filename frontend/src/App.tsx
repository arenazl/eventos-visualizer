import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePageModern from './pages/HomePageModern'
import EventDetailPage from './pages/EventDetailPage'
import { EventsProvider } from './stores/EventsStore'

function App() {
  return (
    <EventsProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePageModern />} />
          <Route path="/evento/:id" element={<EventDetailPage />} />
        </Routes>
      </Router>
    </EventsProvider>
  )
}

export default App