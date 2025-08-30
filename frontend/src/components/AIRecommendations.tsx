import React from 'react'

interface AIRecommendation {
  analysis: string
  recommendations: any[]
  alternative_suggestions: string[]
  follow_up_questions: string[]
  personalized_message: string
}

interface AIRecommendationsProps {
  recommendations: AIRecommendation
  originalQuery: string
  onFollowUpClick: (question: string) => void
}

export const AIRecommendations: React.FC<AIRecommendationsProps> = ({
  recommendations,
  originalQuery,
  onFollowUpClick
}) => {
  if (!recommendations) return null

  return (
    <div className="mb-8 space-y-6">
      {/* Mensaje personalizado de Gemini */}
      {recommendations.personalized_message && (
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 rounded-2xl blur opacity-50"></div>
          <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  🧠
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Asistente AI
                </h3>
                <p className="text-white/80 leading-relaxed">
                  {recommendations.personalized_message}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Análisis de búsqueda */}
      {recommendations.analysis && (
        <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
          <h4 className="text-white/90 font-medium mb-2">💡 Análisis de tu búsqueda:</h4>
          <p className="text-white/70 text-sm">{recommendations.analysis}</p>
        </div>
      )}

      {/* Sugerencias alternativas */}
      {recommendations.alternative_suggestions && recommendations.alternative_suggestions.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-white/90 font-semibold flex items-center gap-2">
            ✨ También podrías considerar:
          </h4>
          <div className="grid gap-3">
            {recommendations.alternative_suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-xl rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all duration-300 cursor-pointer group"
                onClick={() => onFollowUpClick(suggestion)}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {index + 1}
                  </div>
                  <p className="text-white/80 group-hover:text-white transition-colors">
                    {suggestion}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preguntas de seguimiento */}
      {recommendations.follow_up_questions && recommendations.follow_up_questions.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-white/90 font-semibold flex items-center gap-2">
            🤔 ¿Te interesa saber más?
          </h4>
          <div className="flex flex-wrap gap-2">
            {recommendations.follow_up_questions.map((question, index) => (
              <button
                key={index}
                onClick={() => onFollowUpClick(question)}
                className="px-4 py-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 border border-purple-400/30 hover:border-purple-400/50 rounded-full text-white/80 hover:text-white text-sm transition-all duration-300 hover:scale-105"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Indicador de que es AI */}
      <div className="flex items-center justify-center">
        <div className="flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-full border border-white/10">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-white/50 text-xs">Recomendaciones generadas por IA</span>
        </div>
      </div>
    </div>
  )
}

// Componente para mostrar cuando no hay resultados pero hay sugerencias
export const NoResultsWithAI: React.FC<{
  query: string
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
}> = ({ query, suggestions, onSuggestionClick }) => {
  return (
    <div className="text-center py-16 px-6">
      <div className="max-w-md mx-auto">
        {/* Icono de búsqueda sin resultados */}
        <div className="w-24 h-24 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full flex items-center justify-center mb-6 mx-auto">
          <svg className="w-12 h-12 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>

        <h3 className="text-2xl font-bold text-white/90 mb-3">
          No encontré "{query}" exactamente
        </h3>
        <p className="text-white/60 text-lg mb-8">
          Pero tengo algunas ideas geniales para ti 🧠✨
        </p>

        {/* Sugerencias AI */}
        {suggestions.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-white/80 font-medium mb-4">💡 Probá con esto:</h4>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="w-full p-4 bg-white/5 hover:bg-white/10 backdrop-blur-xl rounded-xl border border-white/10 hover:border-white/20 text-left transition-all duration-300 hover:scale-105 group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-white/80 group-hover:text-white">
                    {suggestion}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AIRecommendations