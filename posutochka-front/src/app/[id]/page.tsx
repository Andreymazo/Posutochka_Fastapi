'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { DayPicker, DateRange } from 'react-day-picker'
import { format } from 'date-fns'
import { apiRequest } from '@/lib/api'
import 'react-day-picker/dist/style.css'

// --- Интерфейсы ---
interface Apartment {
  id: number;
  name: string;
  address: string;
  price_per_night: number;
  description: string;
  photos: { url: string }[];
}

export default function ApartmentPage() {
  const { id } = useParams();
  const router = useRouter();
  
  const [apt, setApt] = useState<Apartment | null>(null);
  const [range, setRange] = useState<DateRange | undefined>();
  const [loading, setLoading] = useState(true);
  
  // Состояния авторизации
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [credentials, setCredentials] = useState({ email: '', password: '', first_name: '', last_name: '', phone_number: '' });

  useEffect(() => {
    apiRequest(`/apartments/${id}`)
      .then(setApt)
      .catch(() => alert('Ошибка при загрузке данных'))
      .finally(() => setLoading(false));
  }, [id]);

  // --- Логика Бронирования ---
  const handleBooking = async () => {
    if (!range?.from || !range?.to) return alert('Выберите даты!');
    
    const token = localStorage.getItem('token');
    if (!token) {
      setAuthMode('login');
      setIsAuthModalOpen(true);
      return;
    }

    try {
      await apiRequest('/bookings/', {
        method: 'POST',
        body: JSON.stringify({
          apartment_id: Number(id),
          check_in: format(range.from, 'yyyy-MM-dd'),
          check_out: format(range.to, 'yyyy-MM-dd')
        })
      });
      alert('✅ Забронировано!');
      router.push('/');
    } catch (err: any) {
      alert(`❌ ${err.message}`);
    }
  };

  // --- Логика Авторизации ---
  const handleAuth = async () => {
    const endpoint = authMode === 'register' ? '/auth/register' : '/auth/login';
    try {
      const data = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(credentials)
      });
      localStorage.setItem('token', data.access_token);
      setIsAuthModalOpen(false);
      handleBooking(); // Повтор попытки после входа
    } catch (err: any) {
      alert(`❌ Ошибка: ${err.message}`);
    }
  };

  if (loading) return <div className="p-20 text-center animate-pulse text-xl">Загрузка...</div>
  if (!apt) return <div className="p-20 text-center">Объект не найден</div>

  return (
    <div className="max-w-6xl mx-auto p-6 font-sans">
      <h1 className="text-4xl font-bold mb-2 text-slate-900">{apt.name}</h1>
      <p className="text-gray-500 mb-6">{apt.address}</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Фото и описание */}
        <div className="lg:col-span-2">
          <div className="rounded-3xl overflow-hidden h-[450px] mb-6 shadow-2xl bg-gray-100 border border-slate-200">
            <img src={apt.photos?.[0]?.url || '/placeholder.jpg'} className="w-full h-full object-cover" alt={apt.name} />
          </div>
          <h3 className="text-2xl font-semibold mb-4 text-slate-800">Описание</h3>
          <p className="text-gray-600 leading-relaxed text-lg">{apt.description}</p>
        </div>

        {/* Виджет календаря */}
        <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-2xl sticky top-6 h-fit">
          <div className="text-3xl font-bold mb-6 text-slate-900">
            {apt.price_per_night?.toLocaleString()} ₽ <span className="text-base font-normal text-gray-400">/ ночь</span>
          </div>
          
          <div className="mb-6 flex justify-center border border-slate-100 rounded-2xl p-2 bg-slate-50/50">
            <DayPicker mode="range" selected={range} onSelect={setRange} disabled={{ before: new Date() }} />
          </div>

          <button onClick={handleBooking} className="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-indigo-700 transition-all hover:shadow-lg active:scale-[0.98]">
            Забронировать сейчас
          </button>
        </div>
      </div>

      {/* Модальное окно */}
     {isAuthModalOpen && (
  <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-md p-4">
    <div className="bg-white p-8 rounded-[2.5rem] w-full max-w-md shadow-2xl border border-white/20">
      
      {/* ПЕРЕКЛЮЧАТЕЛЬ (Tabs) */}
      <div className="flex bg-slate-100 p-1 rounded-2xl mb-8">
        <button 
          onClick={() => setAuthMode('login')}
          className={`flex-1 py-2 text-sm font-bold rounded-xl transition-all ${authMode === 'login' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500'}`}
        >
          Вход
        </button>
        <button 
          onClick={() => setAuthMode('register')}
          className={`flex-1 py-2 text-sm font-bold rounded-xl transition-all ${authMode === 'register' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500'}`}
        >
          Регистрация
        </button>
      </div>

      <div className="space-y-4">
        {/* ПОЛЯ РЕГИСТРАЦИИ (появляются только в режиме register) */}
        {authMode === 'register' && (
          <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="grid grid-cols-2 gap-2">
              <input 
                type="text" placeholder="Имя" className="auth-input" 
                onChange={e => setCredentials({...credentials, first_name: e.target.value})} 
              />
              <input 
                type="text" placeholder="Фамилия" className="auth-input" 
                onChange={e => setCredentials({...credentials, last_name: e.target.value})} 
              />
            </div>
            <input 
              type="tel" placeholder="Телефон (+7...)" className="auth-input" 
              onChange={e => setCredentials({...credentials, phone_number: e.target.value})} 
            />
          </div>
        )}

        {/* ОБЩИЕ ПОЛЯ (Email и Пароль) */}
        <input 
          type="email" placeholder="Email" className="auth-input" 
          onChange={e => setCredentials({...credentials, email: e.target.value})} 
        />
        <input 
          type="password" placeholder="Пароль" className="auth-input" 
          onChange={e => setCredentials({...credentials, password: e.target.value})} 
        />

        <button 
          onClick={handleAuth} 
          className="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-indigo-700 transition-all active:scale-95 shadow-lg shadow-indigo-200 mt-4"
        >
          {authMode === 'login' ? 'Войти и забронировать' : 'Создать аккаунт'}
        </button>

        <button 
          onClick={() => setIsAuthModalOpen(false)}
          className="w-full text-slate-400 text-sm font-medium hover:text-slate-600 transition-colors"
        >
          Отмена
        </button>
      </div>
    </div>
  </div>
)}

      <style jsx>{`
        .auth-input {
          width: 100%;
          padding: 1rem 1.25rem;
          border: 1px solid #e2e8f0;
          border-radius: 1rem;
          outline: none;
          transition: all 0.2s;
          color: #1e293b;
        }
        .auth-input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }
      `}</style>
    </div>
  )
}
