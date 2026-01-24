'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import 'leaflet/dist/leaflet.css'

// 1. Динамический импорт компонентов карты
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false })
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false })
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false })

// Компонент для смены фокуса карты
const ChangeView = ({ center }: { center: [number, number] }) => {
  const { useMap } = require('react-leaflet')
  const mapInstance = useMap()
  
  useEffect(() => {
    if (mapInstance) {
      mapInstance.setView(center, 14, { animate: true })
    }
  }, [center, mapInstance])
  
  return null
}

function ApartmentImage({ src, alt }: { src?: string; alt: string }) {
  const [isError, setIsError] = useState(false)
  if (isError || !src) {
    return (
      <div className="w-full h-full bg-gray-200 flex items-center justify-center text-gray-400">
        <span className="text-2xl">🏠</span>
      </div>
    )
  }
  return (
    <img src={src} alt={alt} className="w-full h-full object-cover" onError={() => setIsError(true)} />
  )
}

interface Apartment {
  id: number; name: string; address: string; price_per_night: number;
  latitude: number; longitude: number; photos?: { id: number; url: string }[]
}

export default function Home() {
  const [apartments, setApartments] = useState<Apartment[]>([])
  const [activeApt, setActiveApt] = useState<Apartment | null>(null)
  const [leafletIcon, setLeafletIcon] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // ИНИЦИАЛИЗАЦИЯ ИКОНКИ (Исправлены ссылки!)
  useEffect(() => {
    const L = require('leaflet')
    const icon = L.icon({
      iconUrl: 'https://https://cdnjs.cloudflare.com',
      shadowUrl: 'https://cdnjs.cloudflare.com',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
    })
    setLeafletIcon(icon)
  }, [])

  // ЗАГРУЗКА ДАННЫХ
  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const params = new URLSearchParams({
      lat: "59.9343",
      lon: "30.3351",
      radius: "15000",
      check_in: "2026-02-10", 
      check_out: "2026-02-15"
    });

    fetch(`${baseUrl}/apartments/search?${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        return res.json();
      })
      .then(data => {
        const finalData = Array.isArray(data) ? data : (data.items || []);
        setApartments(finalData);
      })
      .catch(err => {
        console.error("Ошибка:", err);
        setError("Ошибка подключения к бэкенду");
      });
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="p-4 border-b">
        <h1 className="text-xl font-bold text-blue-600">Посуточка 2026 🏠</h1>
        {error && <span className="text-red-500 text-sm ml-4">{error}</span>}
      </header>

      <main className="flex flex-1 overflow-hidden">
        {/* Список */}
        <div className="w-1/2 overflow-y-auto p-4 flex flex-col gap-4">
          {apartments.map(apt => (
            <div 
              key={apt.id} 
              onClick={() => setActiveApt(apt)}
              className={`flex border rounded-xl overflow-hidden h-32 cursor-pointer transition-all ${activeApt?.id === apt.id ? 'ring-2 ring-blue-500 shadow-md' : 'hover:bg-gray-50'}`}
            >
              <div className="w-1/3 bg-gray-100">
                <ApartmentImage src={apt.photos?.[0]?.url} alt={apt.name} />
              </div>
              <div className="w-2/3 p-3 flex flex-col justify-between">
                <div>
                  <h2 className="font-bold text-sm line-clamp-1">{apt.name}</h2>
                  <p className="text-gray-500 text-xs line-clamp-1">{apt.address}</p>
                </div>
                <p className="text-blue-600 font-bold">{apt.price_per_night} ₽</p>
              </div>
            </div>
          ))}
        </div>

        {/* Карта */}
        <div className="w-1/2 h-full relative bg-gray-200">
        <MapContainer 
          center={[59.9343, 30.3351]} 
          zoom={12} 
          style={{ height: '100%', width: '100%' }}
        >
          {/* ВАЖНО: Проверьте этот URL, он должен быть ровно таким! */}
          <TileLayer 
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" 
            attribution='&copy; OpenStreetMap contributors'
          />
          
          {activeApt && <ChangeView center={[activeApt.latitude, activeApt.longitude]} />}

          {leafletIcon && apartments.map(apt => (
            <Marker 
              key={apt.id} 
              position={[apt.latitude, apt.longitude]} 
              icon={leafletIcon}
            >
              <Popup>
                <div className="text-xs font-sans">
                  <p className="font-bold">{apt.name}</p>
                  <p className="text-blue-600">{apt.price_per_night} ₽</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      </main>
    </div>
  )
}
