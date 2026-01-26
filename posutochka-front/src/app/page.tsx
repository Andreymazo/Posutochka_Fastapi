'use client'

import { useEffect, useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import 'leaflet/dist/leaflet.css'

// Динамически загружаем карту, чтобы не было ошибок SSR
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false })
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false })
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false })


// Компонент, который следит за движением карты
const MapUpdater = ({ onSearch }: { onSearch: (lat: number, lon: number, radius: number) => void }) => {
  const { useMapEvents } = require('react-leaflet')
  useMapEvents({
    moveend: (e: any) => {
      const map = e.target
      const center = map.getCenter()
      // Вычисляем радиус поиска в зависимости от того, как сильно приближена карта
      const radius = Math.round(20000 / Math.pow(2, map.getZoom() - 10))
      onSearch(center.lat, center.lng, radius)
    }
  })
  return null
}
export default function Home() {
  // 1. Состояния для данных (у тебя они уже есть)
  // Данные апартаментов
  const [apartments, setApartments] = useState<Apartment[]>([])
  // Выбранный сейчас апартамент (для подсветки)
  const [activeApt, setActiveApt] = useState<Apartment | null>(null)
  // Иконка маркера
  const [leafletIcon, setLeafletIcon] = useState<any>(null)
  // Идет ли загрузка прямо сейчас?
  const [loading, setLoading] = useState(false)
   // 2. Твой useEffect со стилями (пусть остается здесь)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const style = document.createElement('style');
      style.innerHTML = `
        /* Убираем страшную дефолтную обводку Leaflet */
        .leaflet-div-icon {
          background: transparent !important;
          border: none !important;
        }

        /* Наш красивый ценник-чипс */
        .custom-price-tag {
          background: white !important;
          border: 1px solid #e2e8f0 !important;
          border-radius: 24px !important;
          padding: 6px 12px !important;
          font-weight: 800 !important;
          font-size: 14px !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
          white-space: nowrap !important;
          color: #0f172a !important;
          transition: all 0.2s ease-out !important;
          display: flex !important;
          align-items: center;
          justify-content: center;
        }

        /* Стиль при наведении или когда карточка активна */
        .custom-price-tag:hover, .active-price-tag {
          background: #000 !important;
          color: #fff !important;
          transform: scale(1.1);
          z-index: 999 !important;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);
   // 3. ВОТ ЭТО МЫ ЗАМЕНИЛИ (Новые "живые" даты) 
  // Пустые скобки значат: выполнить 1 раз при загрузке
  // Параметры поиска (Питер, лето 2026)
 // 1. Создаем переменные для дат. По умолчанию поставим февраль 2026.
  const [checkIn, setCheckIn] = useState('2026-02-10');
  const [checkOut, setCheckOut] = useState('2026-02-15');

  // 2. Теперь обновляем наши параметры поиска, чтобы они использовали эти даты
  const [searchParams, setSearchParams] = useState({
    lat: 59.9343,
    lon: 30.3351,
    radius: 10000,
    checkIn: checkIn,   // берем из переменной выше
    checkOut: checkOut  // берем из переменной выше
  });

    // Функция запроса к бэкенду
  const fetchApartments = useCallback(async (overrides = {}) => {
    setLoading(true)
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const finalParams = { ...searchParams, ...overrides }
      
      const query = new URLSearchParams({
        lat: finalParams.lat.toString(),
        lon: finalParams.lon.toString(),
        radius: finalParams.radius.toString(),
        check_in: finalParams.checkIn,
        check_out: finalParams.checkOut
      })

      const res = await fetch(`${baseUrl}/apartments/search?${query}`)
      const data = await res.json()
      setApartments(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error("Ошибка API:", err)
    } finally {
      setLoading(false)
    }
  }, [searchParams])

  // Эффект для создания иконки и первого поиска при открытии страницы
  useEffect(() => {
    const L = require('leaflet')
  
    fetchApartments()
  }, [])
  
  const createPriceIcon = (price: number, isActive: boolean) => {
  const L = require('leaflet');
  return L.divIcon({
    className: 'bg-transparent', // Это критично!
    html: `<div class="custom-price-tag ${isActive ? 'active-price-tag' : ''}">
             ${price.toLocaleString()} ₽
           </div>`,
    iconSize: [70, 34],
    iconAnchor: [35, 17]
  });
};
useEffect(() => {
  const newParams = { ...searchParams, checkIn, checkOut };
  setSearchParams(newParams);
  fetchApartments(newParams);
}, [checkIn, checkOut]); // Следит за окошками даты

   return (
    <div className="flex flex-col h-screen bg-white">
      {/* ХЕДЕР */}
      <header className="p-4 border-b flex justify-between items-center bg-white z-50 shadow-sm">
        <h1 className="text-xl font-black text-rose-500 italic">posutochka 2026</h1>

        {/* НАШИ НОВЫЕ ОКОШКИ ДАТ */}
        <div className="flex items-center gap-2 bg-slate-100 p-2 rounded-2xl border border-slate-200">
          <div className="flex flex-col px-3">
            <span className="text-[10px] uppercase font-bold text-slate-400">Заезд</span>
            <input 
              type="date" 
              value={checkIn} 
              onChange={(e) => setCheckIn(e.target.value)}
              className="bg-transparent text-sm font-bold outline-none cursor-pointer text-slate-700"
            />
          </div>
          
          <div className="w-px h-8 bg-slate-300 mx-1"></div>

          <div className="flex flex-col px-3">
            <span className="text-[10px] uppercase font-bold text-slate-400">Выезд</span>
            <input 
              type="date" 
              value={checkOut} 
              onChange={(e) => setCheckOut(e.target.value)}
              className="bg-transparent text-sm font-bold outline-none cursor-pointer text-slate-700"
            />
          </div>
        </div>

        <div className="flex gap-3 items-center">
    <span className="hidden md:block text-xs text-slate-400">
        {loading ? 'Ищем варианты...' : `Найдено: ${apartments.length}`}
    </span>
    
     {/* Кнопка Регистрации — спокойная, в стиле "Войти" */}
    <button 
      onClick={() => { setAuthMode('register'); setIsAuthModalOpen(true); }}
      className="bg-slate-100 text-slate-900 px-5 py-2 rounded-full text-sm font-bold hover:bg-slate-200 transition active:scale-95"
    >
      Регистрация
    </button>

    {/* Кнопка Войти — более спокойная */}
    <button 
      onClick={() => { setAuthMode('login'); setIsAuthModalOpen(true); }}
      className="bg-slate-100 text-slate-900 px-5 py-2 rounded-full text-sm font-bold hover:bg-slate-200 transition active:scale-95"
    >
      Войти
    </button>
</div>
      </header>


      <main className="flex flex-1 overflow-hidden">
        {/* СПИСОК СЛЕВА (1/3 экрана) */}
        <div className="w-1/3 overflow-y-auto p-4 flex flex-col gap-4 border-r bg-gray-50">
          {apartments.map(apt => (
            
            <div 
              key={apt.id} 
              onClick={() => setActiveApt(apt)}
              className={`flex bg-white border rounded-xl overflow-hidden h-28 cursor-pointer transition-all ${activeApt?.id === apt.id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'}`}
            >
              <div className="w-1/3 bg-gray-200">
                {/* Если есть фото, выводим его, если нет — иконку */}
                {apt.photos && apt.photos[0] ? (
                  <img src={apt.photos[0].url} className="w-full h-full object-cover" alt="" />
                ) : <div className="w-full h-full flex items-center justify-center">🏠</div>}
              </div>
              <div className="w-2/3 p-3 flex flex-col justify-between">
                <h2 className="font-bold text-sm truncate">{apt.name}</h2>
                <p className="text-blue-600 font-bold">{apt.price_per_night} ₽</p>
              </div>
            </div>
          ))}
        </div>

        {/* КАРТА СПРАВА (2/3 экрана) */}
        <div className="w-2/3 h-full relative">
          <MapContainer center={[59.9343, 30.3351]} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            
            {/* Слушатель движений карты */}
            <MapUpdater onSearch={(lat, lon, rad) => {
                const newParams = { ...searchParams, lat, lon, radius: rad };
                setSearchParams(newParams);
                fetchApartments(newParams);
            }} />

             {apartments.map(apt => (
        <Marker 
          key={apt.id} 
          position={[apt.latitude, apt.longitude]} 
          icon={createPriceIcon(apt.price_per_night, activeApt?.id === apt.id)}
          eventHandlers={{
            click: () => { window.location.href = `/${apt.id}` }
          }}
        >
          <Popup>
            <div className="font-bold text-sm">
              {apt.name} <br/>
              <span className="text-blue-600">{apt.price_per_night} ₽</span>
            </div>
          </Popup>
        </Marker>
      ))}
          </MapContainer>
        </div>
      </main>
    </div>
  )
} // Конец функции Home
