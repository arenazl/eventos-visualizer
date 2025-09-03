import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'

interface UserProfile {
  id?: string
  email?: string
  name: string
  avatar?: string
  city: string
  country: string
  age?: number
  interests: string[]
  eventPreferences: {
    categories: string[]
    priceRange: 'free' | 'cheap' | 'moderate' | 'premium' | 'any'
    distance: number // km
    notifications: boolean
  }
}

interface UserProfileFormProps {
  initialData?: Partial<UserProfile>
  onSave: (profile: UserProfile) => void
  onCancel?: () => void
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ 
  initialData, 
  onSave, 
  onCancel 
}) => {
  const { register, handleSubmit, formState: { errors }, setValue, watch } = useForm<UserProfile>({
    defaultValues: {
      name: initialData?.name || '',
      city: initialData?.city || '',
      country: initialData?.country || 'Argentina',
      age: initialData?.age || undefined,
      interests: initialData?.interests || [],
      eventPreferences: {
        categories: initialData?.eventPreferences?.categories || [],
        priceRange: initialData?.eventPreferences?.priceRange || 'any',
        distance: initialData?.eventPreferences?.distance || 25,
        notifications: initialData?.eventPreferences?.notifications ?? true
      }
    }
  })

  const [selectedInterests, setSelectedInterests] = useState<string[]>(
    initialData?.interests || []
  )
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    initialData?.eventPreferences?.categories || []
  )

  const availableInterests = [
    'Música', 'Arte', 'Deportes', 'Tecnología', 'Gastronomía', 
    'Cine', 'Teatro', 'Lectura', 'Viajes', 'Fotografía',
    'Baile', 'Idiomas', 'Fitness', 'Gaming', 'Networking'
  ]

  const eventCategories = [
    'Música', 'Arte y Cultura', 'Deportes', 'Tecnología', 
    'Gastronomía', 'Negocios', 'Educación', 'Salud y Bienestar',
    'Entretenimiento', 'Familia', 'Caridad', 'Moda'
  ]

  const countries = [
    'Argentina', 'Chile', 'Colombia', 'México', 'España',
    'Brasil', 'Perú', 'Uruguay', 'Estados Unidos', 'Otro'
  ]

  const toggleInterest = (interest: string) => {
    const updated = selectedInterests.includes(interest)
      ? selectedInterests.filter(i => i !== interest)
      : [...selectedInterests, interest]
    setSelectedInterests(updated)
    setValue('interests', updated)
  }

  const toggleCategory = (category: string) => {
    const updated = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category]
    setSelectedCategories(updated)
    setValue('eventPreferences.categories', updated)
  }

  const onSubmit = (data: UserProfile) => {
    const profile: UserProfile = {
      ...data,
      interests: selectedInterests,
      eventPreferences: {
        ...data.eventPreferences,
        categories: selectedCategories
      }
    }
    onSave(profile)
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-black/40 backdrop-blur-xl border border-white/20 rounded-2xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Perfil de Usuario</h2>
        <p className="text-white/60">Personaliza tu experiencia de eventos</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Información básica */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white/90">Información Básica</h3>
          
          <div>
            <label className="block text-white/80 text-sm font-medium mb-2">
              Nombre Completo *
            </label>
            <input
              {...register('name', { required: 'El nombre es requerido' })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-purple-400 focus:outline-none transition-colors"
              placeholder="Tu nombre completo"
            />
            {errors.name && (
              <p className="text-red-400 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white/80 text-sm font-medium mb-2">
                Ciudad *
              </label>
              <input
                {...register('city', { required: 'La ciudad es requerida' })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-purple-400 focus:outline-none transition-colors"
                placeholder="Buenos Aires, Madrid, etc."
              />
              {errors.city && (
                <p className="text-red-400 text-sm mt-1">{errors.city.message}</p>
              )}
            </div>

            <div>
              <label className="block text-white/80 text-sm font-medium mb-2">
                País *
              </label>
              <select
                {...register('country', { required: 'El país es requerido' })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:border-purple-400 focus:outline-none transition-colors"
              >
                {countries.map(country => (
                  <option key={country} value={country} className="bg-gray-800">
                    {country}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-white/80 text-sm font-medium mb-2">
              Edad (opcional)
            </label>
            <input
              type="number"
              {...register('age', { min: 13, max: 120 })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-purple-400 focus:outline-none transition-colors"
              placeholder="25"
              min="13"
              max="120"
            />
          </div>
        </div>

        {/* Intereses */}
        <div>
          <h3 className="text-lg font-semibold text-white/90 mb-4">Intereses</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {availableInterests.map(interest => (
              <button
                key={interest}
                type="button"
                onClick={() => toggleInterest(interest)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedInterests.includes(interest)
                    ? 'bg-purple-500 text-white border border-purple-400'
                    : 'bg-white/10 text-white/70 border border-white/20 hover:bg-white/20'
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        {/* Preferencias de eventos */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white/90">Preferencias de Eventos</h3>
          
          <div>
            <label className="block text-white/80 text-sm font-medium mb-3">
              Categorías de Eventos
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {eventCategories.map(category => (
                <button
                  key={category}
                  type="button"
                  onClick={() => toggleCategory(category)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedCategories.includes(category)
                      ? 'bg-pink-500 text-white border border-pink-400'
                      : 'bg-white/10 text-white/70 border border-white/20 hover:bg-white/20'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white/80 text-sm font-medium mb-2">
                Rango de Precio
              </label>
              <select
                {...register('eventPreferences.priceRange')}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:border-purple-400 focus:outline-none transition-colors"
              >
                <option value="free" className="bg-gray-800">Solo Gratis</option>
                <option value="cheap" className="bg-gray-800">Económico ($0-2000)</option>
                <option value="moderate" className="bg-gray-800">Moderado ($2000-8000)</option>
                <option value="premium" className="bg-gray-800">Premium ($8000+)</option>
                <option value="any" className="bg-gray-800">Cualquier precio</option>
              </select>
            </div>

            <div>
              <label className="block text-white/80 text-sm font-medium mb-2">
                Distancia máxima ({watch('eventPreferences.distance')} km)
              </label>
              <input
                type="range"
                {...register('eventPreferences.distance')}
                min="5"
                max="100"
                step="5"
                className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-white/50 mt-1">
                <span>5 km</span>
                <span>100 km</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              {...register('eventPreferences.notifications')}
              className="w-5 h-5 rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-400 focus:ring-offset-0"
            />
            <label className="text-white/80 text-sm">
              Recibir notificaciones de eventos recomendados
            </label>
          </div>
        </div>

        {/* Botones */}
        <div className="flex gap-4 pt-6">
          <button
            type="submit"
            className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
          >
            Guardar Perfil
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 bg-white/10 border border-white/20 text-white/80 font-medium rounded-xl hover:bg-white/20 transition-all duration-200"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      <style>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: linear-gradient(45deg, #8b5cf6, #ec4899);
          cursor: pointer;
          border: 2px solid white;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        .slider::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: linear-gradient(45deg, #8b5cf6, #ec4899);
          cursor: pointer;
          border: 2px solid white;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
      `}</style>
    </div>
  )
}

export default UserProfileForm