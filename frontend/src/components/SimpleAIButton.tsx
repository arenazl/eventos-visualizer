import React from 'react'

interface SimpleAIButtonProps {
  eventId: string
}

const SimpleAIButton: React.FC<SimpleAIButtonProps> = ({ eventId }) => {
  console.log('✅ SimpleAIButton rendering for event:', eventId)
  
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    console.log('🔴 Simple AI button clicked for event:', eventId)
    alert(`AI clicked for event: ${eventId}`)
  }

  return (
    <button
      onClick={handleClick}
      style={{
        position: 'absolute',
        bottom: '16px',
        right: '16px',
        width: '60px',
        height: '60px',
        backgroundColor: '#ff0000',
        color: 'white',
        border: '4px solid #ffff00',
        borderRadius: '50%',
        fontSize: '24px',
        cursor: 'pointer',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      🤖
    </button>
  )
}

export default SimpleAIButton