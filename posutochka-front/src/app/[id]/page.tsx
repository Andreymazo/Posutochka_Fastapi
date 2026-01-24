'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { DayPicker, DateRange } from 'react-day-picker'
import { format } from 'date-fns'
import 'react-day-picker/dist/style.css'

interface Apartment {
  id: number
  name: string
  address: string
  price_per_night: number
  description: string
  photos: { url: string }[]
}

export default function ApartmentPage() {
  const { id } = useParams()
  const [apt, setApt] = useState<Apartment | null>(null)
  const [range, setRange] = useState<DateRange | undefined>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // В 2026 году используем переменную окружения из docker-compose
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/apartments/${id}`)
      .then(res => res.json())
      .then(data => {
        setApt(data)
        setLoading(false)
      })
  }, [id])

  const handleBooking = async () => {
    if (!range?.from || !range?.to) return alert('Выберите даты!')
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/bookings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        apartment_id: Number(id),
        check_in: format(range.from, 'yyyy-MM-dd'),
        check_out: format(range.to, 'yyyy-MM-dd')
      })
    })

    if (res.ok) {
      alert('✅ Бронирование создано! Проверьте Telegram.')
    } else {
      const err = await res.json()
      alert(`❌ Ошибка: ${err.detail || 'Даты заняты'}`)
    }
  }

  if (loading) return <div className="p-20 text-center animate-pulse">Загрузка объекта...</div>
  if (!apt) return <div className="p-20 text-center">Объект не найден</div>

  return (
    <div className="max-w-6xl mx-auto p-6 font-sans">
      <h1 className="text-4xl font-bold mb-2">{apt.name}</h1>
      <p className="text-gray-500 mb-6">{apt.address}</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Левая колонка: Галерея и Описание */}
        <div className="lg:col-span-2">
          <div className="rounded-3xl overflow-hidden h-[400px] mb-6 shadow-lg">
            <img 
              src={apt.photos?.[0]?.url || '/images/4Gostinaya_1.jpg'} 
              className="w-full h-full object-cover"
              alt={apt.name}
            />
          </div>
          <h3 className="text-2xl font-semibold mb-4">Об апартаментах</h3>
          <p className="text-gray-700 leading-relaxed">{apt.description}</p>
        </div>

        {/* Правая колонка: Календарь и Бронирование */}
        <div className="bg-white p-6 rounded-3xl border shadow-xl sticky top-6 h-fit">
          <div className="text-2xl font-bold mb-4">{apt.price_per_night} ₽ <span className="text-sm font-normal text-gray-500">/ ночь</span></div>
          
          <div className="mb-6 flex justify-center">
            <DayPicker
              mode="range"
              selected={range}
              onSelect={setRange}
              disabled={{ before: new Date() }}
              className="border rounded-xl p-2"
            />
          </div>

          <button 
            onClick={handleBooking}
            className="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-blue-700 transition active:scale-95"
          >
            Забронировать
          </button>
          
          <p className="text-center text-xs text-gray-400 mt-4">
            Вы не будете списаны до подтверждения арендодателем
          </p>
        </div>
      </div>
    </div>
  )
}
