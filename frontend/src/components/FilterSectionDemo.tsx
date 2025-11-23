import React, { useState } from 'react'

// Tipos
interface PlaceInfo {
  name: string
  city: string
  country: string | null
  province: string | null
  event_count: number
}

interface Category {
  id: string
  name: string
  icon: string
  color: string
}

interface FilterSectionDemoProps {
  popularPlaces: PlaceInfo[]
  categories: Category[]
  selectedPlace: string | null
  selectedCategory: string
  onPlaceSelect: (place: PlaceInfo) => void
  onCategorySelect: (categoryId: string) => void
  designOption?: 1 | 2 | 3
}

// Categorías por defecto (fallback)
const DEFAULT_CATEGORIES: Category[] = [
  { id: 'all', name: 'Todos', icon: '✨', color: 'from-purple-500 to-pink-500' },
  { id: 'music', name: 'Música', icon: '🎵', color: 'from-pink-500 to-rose-500' },
  { id: 'cultural', name: 'Cultural', icon: '🎭', color: 'from-amber-500 to-orange-500' },
  { id: 'sports', name: 'Deportes', icon: '⚽', color: 'from-green-500 to-emerald-500' },
  { id: 'nightlife', name: 'Nightlife', icon: '🌙', color: 'from-indigo-500 to-purple-500' },
  { id: 'tech', name: 'Tech', icon: '💻', color: 'from-cyan-500 to-blue-500' },
  { id: 'food', name: 'Comida', icon: '🍽️', color: 'from-orange-500 to-red-500' },
  { id: 'art', name: 'Arte', icon: '🎨', color: 'from-fuchsia-500 to-pink-500' },
]

// Gradientes para barrios
const BARRIO_GRADIENTS = [
  'from-violet-600 to-indigo-600',
  'from-pink-600 to-rose-600',
  'from-cyan-600 to-blue-600',
  'from-emerald-600 to-teal-600',
  'from-amber-600 to-orange-600',
  'from-fuchsia-600 to-purple-600',
  'from-red-600 to-pink-600',
  'from-blue-600 to-indigo-600',
]

// =============================================================================
// OPCIÓN 1: Pill Chips con Scroll Horizontal
// =============================================================================
const Option1: React.FC<FilterSectionDemoProps> = ({
  popularPlaces,
  categories,
  selectedPlace,
  selectedCategory,
  onPlaceSelect,
  onCategorySelect,
}) => {
  const cats = categories.length > 0 ? categories : DEFAULT_CATEGORIES
  const scrollContainerRef = React.useRef<HTMLDivElement>(null)

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = direction === 'left' ? -200 : 200
      scrollContainerRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' })
    }
  }

  return (
    <div className="space-y-4">
      {/* Barrios con scroll horizontal */}
      <div className="relative">
        <div className="flex items-center justify-between mb-2">
          <span className="text-white/70 text-sm font-medium flex items-center gap-2">
            <span className="text-lg">📍</span> Barrios cercanos
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => scroll('left')}
              className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={() => scroll('right')}
              className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <div
          ref={scrollContainerRef}
          className="flex gap-2 overflow-x-auto scrollbar-hide pb-2 scroll-smooth"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {popularPlaces.map((place, index) => {
            const isSelected = selectedPlace === place.name
            return (
              <button
                key={index}
                onClick={() => onPlaceSelect(place)}
                className={`flex-shrink-0 px-4 py-2 rounded-full border transition-all duration-300 ${
                  isSelected
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 border-purple-400 text-white shadow-lg shadow-purple-500/30 scale-105'
                    : 'bg-white/10 border-white/20 text-white/80 hover:bg-white/20 hover:border-white/40'
                }`}
              >
                <span className="font-medium">{place.name}</span>
                <span className={`ml-2 text-xs ${isSelected ? 'text-white/90' : 'text-white/50'}`}>
                  {place.event_count}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Categorías como iconos circulares */}
      <div>
        <span className="text-white/70 text-sm font-medium flex items-center gap-2 mb-3">
          <span className="text-lg">🎭</span> Categorías
        </span>
        <div className="flex flex-wrap gap-3 justify-center">
          {cats.map((cat) => {
            const isSelected = selectedCategory === cat.id || selectedCategory === cat.name.toLowerCase()
            return (
              <button
                key={cat.id}
                onClick={() => onCategorySelect(cat.id)}
                className={`flex flex-col items-center gap-1 transition-all duration-300 ${
                  isSelected ? 'scale-110' : 'hover:scale-105'
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all duration-300 ${
                    isSelected
                      ? `bg-gradient-to-br ${cat.color} shadow-lg ring-2 ring-white/50`
                      : 'bg-white/10 hover:bg-white/20'
                  }`}
                >
                  {cat.icon}
                </div>
                <span className={`text-xs ${isSelected ? 'text-white font-medium' : 'text-white/60'}`}>
                  {cat.name}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// OPCIÓN 2: Cards con Gradiente (Estilo Spotify)
// =============================================================================
const Option2: React.FC<FilterSectionDemoProps> = ({
  popularPlaces,
  categories,
  selectedPlace,
  selectedCategory,
  onPlaceSelect,
  onCategorySelect,
}) => {
  const cats = categories.length > 0 ? categories : DEFAULT_CATEGORIES
  return (
    <div className="space-y-6">
      {/* Barrios como cards con gradiente */}
      <div>
        <span className="text-white/70 text-sm font-medium flex items-center gap-2 mb-3">
          <span className="text-lg">🔥</span> Zonas populares
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {popularPlaces.slice(0, 10).map((place, index) => {
            const isSelected = selectedPlace === place.name
            const gradient = BARRIO_GRADIENTS[index % BARRIO_GRADIENTS.length]
            return (
              <button
                key={index}
                onClick={() => onPlaceSelect(place)}
                className={`relative overflow-hidden rounded-xl p-4 transition-all duration-300 group ${
                  isSelected
                    ? 'ring-2 ring-white shadow-xl scale-105'
                    : 'hover:scale-105 hover:shadow-lg'
                }`}
              >
                {/* Fondo con gradiente */}
                <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-${isSelected ? '100' : '80'} group-hover:opacity-100 transition-opacity`} />

                {/* Patrón decorativo */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-white rounded-full -translate-y-10 translate-x-10" />
                </div>

                {/* Contenido */}
                <div className="relative z-10">
                  <h3 className="text-white font-bold text-sm truncate">{place.name.toUpperCase()}</h3>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-white/80 text-xs">{place.event_count}</span>
                    <span className="text-lg">🎉</span>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Categorías en grid con iconos grandes */}
      <div>
        <span className="text-white/70 text-sm font-medium flex items-center gap-2 mb-3">
          <span className="text-lg">🎯</span> ¿Qué buscás hoy?
        </span>
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          {cats.map((cat) => {
            const isSelected = selectedCategory === cat.id || selectedCategory === cat.name.toLowerCase()
            return (
              <button
                key={cat.id}
                onClick={() => onCategorySelect(cat.id)}
                className={`flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-300 ${
                  isSelected
                    ? `bg-gradient-to-br ${cat.color} shadow-lg scale-105`
                    : 'bg-white/10 hover:bg-white/20 hover:scale-105'
                }`}
              >
                <span className="text-2xl">{cat.icon}</span>
                <span className={`text-xs font-medium ${isSelected ? 'text-white' : 'text-white/70'}`}>
                  {cat.name}
                </span>
                {/* Barra indicadora */}
                <div className={`w-full h-0.5 rounded-full transition-all ${
                  isSelected ? 'bg-white/80' : 'bg-white/20'
                }`} />
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// OPCIÓN 3: Segmented Control + Tags (Estilo iOS/Apple)
// =============================================================================
const Option3: React.FC<FilterSectionDemoProps> = ({
  popularPlaces,
  categories,
  selectedPlace,
  selectedCategory,
  onPlaceSelect,
  onCategorySelect,
}) => {
  const cats = categories.length > 0 ? categories : DEFAULT_CATEGORIES
  const [activeTab, setActiveTab] = useState<'barrios' | 'categorias'>('barrios')

  return (
    <div className="space-y-4">
      {/* Segmented Control */}
      <div className="flex justify-center">
        <div className="inline-flex bg-white/10 rounded-xl p-1 backdrop-blur-xl">
          <button
            onClick={() => setActiveTab('barrios')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
              activeTab === 'barrios'
                ? 'bg-white text-gray-900 shadow-lg'
                : 'text-white/70 hover:text-white'
            }`}
          >
            🏘️ Barrios
          </button>
          <button
            onClick={() => setActiveTab('categorias')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
              activeTab === 'categorias'
                ? 'bg-white text-gray-900 shadow-lg'
                : 'text-white/70 hover:text-white'
            }`}
          >
            🎭 Categorías
          </button>
        </div>
      </div>

      {/* Contenido según tab activo */}
      <div className="min-h-[120px]">
        {activeTab === 'barrios' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 animate-fadeIn">
            {popularPlaces.map((place, index) => {
              const isSelected = selectedPlace === place.name
              return (
                <button
                  key={index}
                  onClick={() => onPlaceSelect(place)}
                  className={`px-4 py-3 rounded-xl border transition-all duration-300 text-left ${
                    isSelected
                      ? 'bg-white text-gray-900 border-white shadow-lg'
                      : 'bg-white/5 border-white/20 text-white hover:bg-white/10 hover:border-white/40'
                  }`}
                >
                  <div className="font-medium text-sm truncate">{place.name}</div>
                  <div className={`text-xs flex items-center gap-1 mt-1 ${isSelected ? 'text-gray-600' : 'text-white/50'}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {place.event_count} eventos
                  </div>
                </button>
              )
            })}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 animate-fadeIn">
            {cats.map((cat) => {
              const isSelected = selectedCategory === cat.id || selectedCategory === cat.name.toLowerCase()
              return (
                <button
                  key={cat.id}
                  onClick={() => onCategorySelect(cat.id)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-300 ${
                    isSelected
                      ? 'bg-white text-gray-900 border-white shadow-lg'
                      : 'bg-white/5 border-white/20 text-white hover:bg-white/10 hover:border-white/40'
                  }`}
                >
                  <span className="text-xl">{cat.icon}</span>
                  <span className="font-medium text-sm">{cat.name}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// COMPONENTE PRINCIPAL CON SELECTOR DE DISEÑO
// =============================================================================
export const FilterSectionDemo: React.FC<Omit<FilterSectionDemoProps, 'designOption'> & {
  onDesignChange?: (design: 1 | 2 | 3) => void
}> = (props) => {
  const [designOption, setDesignOption] = useState<1 | 2 | 3>(2)

  const handleDesignChange = (design: 1 | 2 | 3) => {
    setDesignOption(design)
    props.onDesignChange?.(design)
  }

  return (
    <div className="space-y-6">
      {/* Selector de diseño */}
      <div className="flex justify-center gap-2 pb-4 border-b border-white/10">
        <span className="text-white/50 text-sm mr-2 self-center">Diseño:</span>
        {[1, 2, 3].map((num) => (
          <button
            key={num}
            onClick={() => handleDesignChange(num as 1 | 2 | 3)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              designOption === num
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Opción {num}
          </button>
        ))}
      </div>

      {/* Renderizar diseño seleccionado */}
      {designOption === 1 && <Option1 {...props} designOption={1} />}
      {designOption === 2 && <Option2 {...props} designOption={2} />}
      {designOption === 3 && <Option3 {...props} designOption={3} />}
    </div>
  )
}

export default FilterSectionDemo
