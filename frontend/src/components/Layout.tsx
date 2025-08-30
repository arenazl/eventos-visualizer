import React from 'react'
import Header from './Header'
import { useEvents } from '../stores/EventsStore'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { loading } = useEvents()

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-gray-700">Cargando eventos...</span>
          </div>
        </div>
      )}
      
      <main className="pb-20">
        {children}
      </main>
    </div>
  )
}

export default Layout