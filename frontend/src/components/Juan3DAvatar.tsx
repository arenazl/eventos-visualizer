import React from 'react'

interface Juan3DAvatarProps {
  isHovered?: boolean
}

export default function Juan3DAvatar({ isHovered = false }: Juan3DAvatarProps) {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <style>{`
        @keyframes pulsar-rayo {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }

        @keyframes rebotar-pelo {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-3px); }
            100% { transform: translateY(0px); }
        }

        @keyframes brillo-guitarra {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }

        #rayo-camiseta {
            animation: pulsar-rayo 0.7s infinite alternate;
            transform-origin: center;
        }

        #pelo-azul {
            animation: rebotar-pelo 1.5s infinite ease-in-out;
            transform-origin: bottom center;
        }

        #brillo-guitarra {
             animation: brillo-guitarra 2s infinite alternate;
        }
      `}</style>

      <svg width="100%" height="100%" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Cara */}
        <circle cx="100" cy="100" r="70" fill="#D2B48C"/>

        {/* Pelo */}
        <path id="pelo-azul" d="M60 55 C40 25 60 10 100 10 C140 10 160 25 140 55 L120 85 H80 L60 55 Z" fill="#1a1a1a"/>

        {/* Lentes */}
        <rect x="60" y="85" width="30" height="20" rx="5" fill="black"/>
        <rect x="110" y="85" width="30" height="20" rx="5" fill="black"/>
        <rect x="88" y="92" width="24" height="5" fill="black"/>

        {/* Ojos */}
        <circle cx="75" cy="95" r="5" fill="white"/>
        <circle cx="125" cy="95" r="5" fill="white"/>

        {/* Boca */}
        <path d="M70 125 Q100 140 130 125" stroke="black" stroke-width="3" fill="none"/>
      </svg>
    </div>
  )
}
