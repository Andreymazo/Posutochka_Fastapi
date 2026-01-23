FROM python:3.12-slim

# Настройки Python для Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
# добавили gcc и python3-dev для сборки некоторых библиотек (если потребуется)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем только requirements (для кэширования слоев)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Expose port
EXPOSE 8000

# Команда запуска (в compose она может быть переопределена, но здесь база)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

