const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  // Пытаемся достать токен (только на стороне клиента)
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    // FastAPI обычно возвращает ошибку в поле detail
    const errorMessage = errorData.detail || 'Произошла ошибка при запросе';
    throw new Error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
  }
  
  return response.json();
}