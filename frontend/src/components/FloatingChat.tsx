import React, { useState } from 'react'

interface ChatMessage {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

const FloatingChat: React.FC = () => {
  console.log('🔧 DEBUG: FloatingChat render');
  const [isOpen, setIsOpen] = useState(false)
  
  // VERSIÓN ULTRA SIMPLE PARA DEBUG
  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen && (
        <button
          onClick={() => {
            console.log('🔧 DEBUG: Opening chat (simple version)');
            setIsOpen(true);
          }}
          className="bg-purple-600 text-white rounded-full p-4 shadow-lg hover:bg-purple-700"
        >
          💬
        </button>
      )}
      {isOpen && (
        <div className="bg-white rounded-lg shadow-lg p-4 w-80">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold">🔧 Debug Chat</h3>
            <button
              onClick={() => {
                console.log('🔧 DEBUG: Closing chat (simple version)');
                setIsOpen(false);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <p>Chat funcionando en modo debug</p>
        </div>
      )}
    </div>
  )
}

export default FloatingChat