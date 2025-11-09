import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePageModern from './pages/HomePageModern'
import EventDetailPage from './pages/EventDetailPage'
import ScrapersTestPage from './pages/ScrapersTestPage'
import { EventsProvider } from './stores/EventsStore'
import { AuthProvider } from './contexts/AuthContext'
import { AssistantsProvider } from './contexts/AssistantsContext'
import FloatingChat from './components/FloatingChat'
import FloatingJuan from './components/FloatingJuan'

function App() {
  return (
    <AuthProvider>
      <AssistantsProvider>
        <EventsProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomePageModern />} />
            <Route path="/event/:id" element={<EventDetailPage />} />
            <Route path="/scrapers-test" element={<ScrapersTestPage />} />
          </Routes>
          {/* DESACTIVADO TEMPORALMENTE: Asistentes flotantes */}
          {/* <FloatingChat /> */}
          {/* <FloatingJuan /> */}
        </Router>
      </EventsProvider>
      </AssistantsProvider>
    </AuthProvider>
  )
}

export default App