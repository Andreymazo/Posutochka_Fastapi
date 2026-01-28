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
  
  // Вычисляем количество ночей
  const checkInDate = range?.from;
  const checkOutDate = range?.to;

  const nights = checkInDate && checkOutDate 
    ? Math.ceil((checkOutDate.getTime() - checkInDate.getTime()) / (1000 * 60 * 60 * 24))
    : 0;

  // Итоговая стоимость
  const totalCost = nights * (apt?.price_per_night ?? 0);

  // Состояния авторизации
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [credentials, setCredentials] = useState({ email: '', password: '', first_name: '', last_name: '', phone_number: '', role: ''});
  const [selectedRole, setSelectedRole] = useState<'client' | 'landlord' | null>(null);

  useEffect(() => {
    apiRequest(`/apartments/${id}`)
      .then(setApt)
      .catch(() => alert('Ошибка при загрузке данных'))
      .finally(() => setLoading(false));
  }, [id]);

  // --- Логика Бронирования ---
 const handleBooking = async () => {
  // 1. Сначала проверяем даты (это мы уже делаем)
  if (!range?.from || !range?.to) return alert('Выберите даты!');
  
  // 2. ПРОВЕРКА ТОКЕНА (Критично!)
  const token = localStorage.getItem('token');
  
  if (!token) {
    // Если токена нет — не шлем запрос, а открываем вход
    setAuthMode('login'); // или 'register'
    setIsAuthModalOpen(true);
    // Прерываем выполнение функции, чтобы не получить 401 в консоли
    return;
  }

  // 3. Только если токен ЕСТЬ, делаем запрос
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
    // Если токен оказался невалидным (401), тоже открываем модалку
    if (err.message.includes('401') || err.message.includes('credentials')) {
      localStorage.removeItem('token'); // чистим битый токен
      setIsAuthModalOpen(true);
    } else {
      alert(`❌ ${err.message}`);
    }
  }
};
const handleAuth = async () => {
  try {
    let token = '';

    if (authMode === 'login') {
      const formData = new URLSearchParams();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);

      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка входа');
      token = data.access_token;
    } else {
      // РЕГИСТРАЦИЯ
      const regData = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      // Если бэк после регистрации сразу логинит (возвращает токен):
      token = regData.access_token;
      
      // ЕСЛИ БЭК НЕ ВОЗВРАЩАЕТ ТОКЕН ПРИ РЕГИСТРАЦИИ:
      if (!token) {
          // Выполняем скрытый логин, чтобы получить токен
          const loginRes = await fetch('http://localhost:8000/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              body: new URLSearchParams({ username: credentials.email, password: credentials.password })
          });
          const loginData = await loginRes.json();
          token = loginData.access_token;
      }
    }

    if (token) {
      localStorage.setItem('token', token);
      setIsAuthModalOpen(false);
      // Важно: передаем токен напрямую, чтобы handleBooking не ждал обновления localStorage
      await executeBooking(token); 
    }
  } catch (err: any) {
    alert(`❌ Ошибка: ${err.message}`);
  }
};

// Вынесите логику запроса брони в отдельную подфункцию
const executeBooking = async (currentToken: string) => {
  try {
    await apiRequest('/bookings/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${currentToken}` }, // Передаем принудительно
      body: JSON.stringify({
        apartment_id: Number(id),
        check_in: format(range!.from!, 'yyyy-MM-dd'),
        check_out: format(range!.to!, 'yyyy-MM-dd')
      })
    });
    alert('✅ Забронировано!');
    router.push('/');
  } catch (err: any) {
    alert(`❌ Ошибка бронирования: ${err.message}`);
  }
};

//   // --- Логика Авторизации ---
// const handleAuth = async () => {
//   try {
//     let data;

//     if (authMode === 'login') {
//       // 1. ЛОГИН: Шлем как Form Data (чтобы работало с OAuth2PasswordRequestForm на бэке)
//       const formData = new URLSearchParams();
//       // Передаем email в поле username, как того требует стандарт FastAPI
//       formData.append('username', credentials.email); 
//       formData.append('password', credentials.password);

//       const res = await fetch('http://localhost:8000/auth/login', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/x-www-form-urlencoded',
//         },
//         body: formData.toString(),
//       });

//       if (!res.ok) {
//         const err = await res.json().catch(() => ({}));
//         throw new Error(err.detail || 'Неверный логин или пароль');
//       }
//       data = await res.json();
//     } else {
//       // 2. РЕГИСТРАЦИЯ: Оставляем JSON (как и было)
//       data = await apiRequest('/auth/register', {
//         method: 'POST',
//         body: JSON.stringify(credentials),
//       });
//     }

//     // Сохраняем токен и продолжаем процесс
//     localStorage.setItem('token', data.access_token);
//     setIsAuthModalOpen(false);
    
//     // Небольшая пауза, чтобы токен "улегся" в памяти, и вызываем бронь
//     setTimeout(() => {
//       handleBooking();
//     }, 100);

//   } catch (err: any) {
//     alert(`❌ Ошибка: ${err.message}`);
//   }
// };


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
            <img src={apt.photos?.[0]?.url ? `http://localhost:9000${apt.photos[0].url}` : '/placeholder.jpg'}  className="w-full h-full object-cover" alt={apt.name} />
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
          {/* Детализация цены */}
          {nights > 0 && (
            <div className="mt-6 space-y-3 border-t border-slate-100 pt-4 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="flex justify-between text-slate-600">
                <span>{apt.price_per_night?.toLocaleString()} ₽ × {nights} ночей</span>
                <span>{(apt.price_per_night * nights).toLocaleString()} ₽</span>
              </div>
              
              {/* Можно добавить сервисный сбор, если планируешь в 2026-м */}
              <div className="flex justify-between text-slate-600">
                <span className="underline cursor-help">Сервисный сбор 0%</span>
                <span>0 ₽</span>
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-slate-200 mt-2">
                <span className="text-lg font-bold text-slate-900">Итого</span>
                <span className="text-2xl font-black text-indigo-600">{totalCost.toLocaleString()} ₽</span>
              </div>
            </div>
          )}

          <button onClick={handleBooking} className="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-indigo-700 transition-all hover:shadow-lg active:scale-[0.98]">
            Забронировать сейчас
          </button>
        </div>
      </div>

      {/* Модальное окно */}
    {isAuthModalOpen && (
  <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-md p-4">
    <div className="bg-white p-8 rounded-[2.5rem] w-full max-w-md shadow-2xl border border-white/20">
      
      {/* ПЕРЕКЛЮЧАТЕЛЬ (Вход / Регистрация) */}
      <div className="flex bg-slate-100 p-1 rounded-2xl mb-8">
        <button 
          onClick={() => { setAuthMode('login'); setSelectedRole(null); }}
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
        {/* --- РЕЖИМ РЕГИСТРАЦИИ --- */}
        {authMode === 'register' && (
          <div className="space-y-6">
            {!selectedRole ? (
              <div className="space-y-4 animate-in fade-in zoom-in duration-300">
                <h3 className="text-center text-slate-800 font-bold text-lg mb-4">Кто вы?</h3>
                <div className="grid grid-cols-2 gap-4">
                  <button 
                    onClick={() => { setSelectedRole('client'); setCredentials({...credentials, role: 'client'}); }}
                    className="flex flex-col items-center justify-center p-6 border-2 border-slate-100 rounded-[2rem] hover:border-indigo-500 hover:bg-indigo-50/30 transition-all group"
                  >
                    <span className="text-4xl mb-3 group-hover:scale-110 transition-transform">🎒</span>
                    <span className="font-bold text-slate-700 text-sm text-center">Я гость</span>
                  </button>

                  <button 
                    onClick={() => { setSelectedRole('landlord'); setCredentials({...credentials, role: 'landlord'}); }}
                    className="flex flex-col items-center justify-center p-6 border-2 border-slate-100 rounded-[2rem] hover:border-rose-500 hover:bg-rose-50/30 transition-all group"
                  >
                    <span className="text-4xl mb-3 group-hover:scale-110 transition-transform">🔑</span>
                    <span className="font-bold text-slate-700 text-sm text-center">Я хозяин</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3 animate-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between mb-2">
                   <span className="text-[10px] font-black uppercase text-indigo-500 bg-indigo-50 px-2 py-1 rounded-md">
                     {selectedRole === 'client' ? 'Клиент' : 'Арендодатель'}
                   </span>
                   <button onClick={() => setSelectedRole(null)} className="text-[10px] text-slate-400 hover:text-indigo-600 font-bold">ИЗМЕНИТЬ</button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input type="text" placeholder="Имя" className="auth-input" onChange={e => setCredentials({...credentials, first_name: e.target.value})} />
                  <input type="text" placeholder="Фамилия" className="auth-input" onChange={e => setCredentials({...credentials, last_name: e.target.value})} />
                </div>
                <input type="tel" placeholder="Телефон (+7...)" className="auth-input" onChange={e => setCredentials({...credentials, phone_number: e.target.value})} />
                <input type="email" placeholder="Email" className="auth-input" onChange={e => setCredentials({...credentials, email: e.target.value})} />
                <input type="password" placeholder="Пароль" className="auth-input" onChange={e => setCredentials({...credentials, password: e.target.value})} />
              </div>
            )}
          </div>
        )}

        {/* --- РЕЖИМ ВХОДА --- */}
        {authMode === 'login' && (
          <div className="space-y-3 animate-in fade-in duration-300">
            <input 
              type="email" placeholder="Email" className="auth-input" 
              onChange={e => setCredentials({...credentials, email: e.target.value})} 
            />
            <input 
              type="password" placeholder="Пароль" className="auth-input" 
              onChange={e => setCredentials({...credentials, password: e.target.value})} 
            />
          </div>
        )}

        {/* ГЛАВНАЯ КНОПКА ДЕЙСТВИЯ */}
        {(authMode === 'login' || selectedRole) && (
          <button 
            onClick={handleAuth} 
            className="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-indigo-700 transition-all active:scale-95 shadow-lg mt-2"
          >
            {authMode === 'login' ? 'Войти и забронировать' : 'Создать аккаунт'}
          </button>
        )}

        <button 
          onClick={() => { setIsAuthModalOpen(false); setSelectedRole(null); }}
          className="w-full text-slate-400 text-sm font-medium hover:text-slate-600 transition-colors py-2"
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
