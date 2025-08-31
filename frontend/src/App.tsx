import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePageModern from './pages/HomePageModern'
import EventDetailPage from './pages/EventDetailPage'
import { EventsProvider } from './stores/EventsStore'
import { AuthProvider } from './contexts/AuthContext'
import FloatingChat from './components/FloatingChat'

function App() {
  return (
    <AuthProvider>
      <EventsProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomePageModern />} />
            <Route path="/evento/:id" element={<EventDetailPage />} />
          </Routes>
          <FloatingChat />
        </Router>
      </EventsProvider>
    </AuthProvider>
  )
}

export default App