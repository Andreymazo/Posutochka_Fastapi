FROM node:20-alpine

WORKDIR /app

# Копируем файлы зависимостей
COPY package*.json ./

# В 2026 году в РФ лучше использовать зеркало прямо при сборке
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

# Копируем остальной код
COPY . .

EXPOSE 3000

# Запуск в режиме разработки с поддержкой Hot Reload
CMD ["npm", "run", "dev"]
