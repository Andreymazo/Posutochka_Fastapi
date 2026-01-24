'use client'
import { useEffect, useState } from 'react'
// --- 1. ВСТАВЛЯЕМ КОМПОНЕНТ ДЛЯ КАРТИНКИ ТУТ ---
function ApartmentImage({ src, alt }: { src: string; alt: string }) {
  const [isError, setIsError] = useState(false)

  if (isError || !src) {
    return (
      <div className="w-full h-full bg-gray-200 flex flex-col items-center justify-center text-gray-400 font-sans">
        <span className="text-4xl">🏠</span>
        <p className="text-xs mt-2">Фото скоро появится</p>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
      onError={() => setIsError(true)}
    />
  )
}
interface Photo {
  id: number
  url: string
}

interface Apartment {
  id: number
  name: string // заменил на name, так как в базе у тебя было name
  address: string
  price_per_night: number
  photos: Photo[]
}

export default function Home() {
  const [apartments, setApartments] = useState<Apartment[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL
    const params = new URLSearchParams({
      lat: "59.9343", // Питерские координаты, чтобы точно видеть наш пентхаус
      lon: "30.3351",
      check_in: "2026-02-10",
      check_out: "2026-02-15",
      radius: "10000"
    })

    fetch(`${baseUrl}/apartments/search?${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`)
        return res.json()
      })
      .then(data => setApartments(data))
      .catch(err => {
        console.error(err)
        setError(err.message)
      })
  }, [])

  return (
    <div className="p-10 font-sans bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-8 text-blue-600">Посуточка 2026 🏠</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Ошибка: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {apartments.length > 0 ? (
          apartments.map(apt => (
            <div key={apt.id} className="bg-white border rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
              <div className="relative h-48 bg-gray-100 overflow-hidden">
                <ApartmentImage 
                  src={apt.photos?.[0]?.url} 
                  alt={apt.name} 
                />
                <div className="absolute top-2 right-2 bg-white/80 backdrop-blur px-2 py-1 rounded-md text-sm font-semibold">
                   {apt.price_per_night} ₽
                </div>
              </div>

              <div className="p-4">
                <h2 className="text-xl font-semibold mb-1">{apt.name}</h2>
                <p className="text-gray-500 text-sm mb-4">{apt.address}</p>
                <button className="w-full bg-blue-600 text-white py-2 rounded-xl font-medium hover:bg-blue-700 transition">
                  Забронировать
                </button>
              </div>
            </div>
          ))
        ) : (
          !error && <p className="text-gray-500 animate-pulse">Ищем жилье в Питере...</p>
        )}
      </div>
    </div>
  )
}
