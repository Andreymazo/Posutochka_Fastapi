import pytest
from httpx import AsyncClient
from app.services.auth import AuthService
from app.models import User
import uuid

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session, sample_user_data_factory):
    original_data = sample_user_data_factory()
    user_data = original_data.copy() 
    # 1. Извлекаем чистый пароль для логина
    # Теперь удаление ключей безопасно для остальных тестов
    raw_password = user_data.pop("password") 
    user_data.pop("password_hash", None)
    
    # 2. Убираем password_hash, если хотим захешировать его правильно через сервис
    user_data.pop("password_hash", None)
    
    # 3. Теперь в user_data нет лишних ключей, и SQLAlchemy не ругается
    user = User(**user_data)
    user.password_hash = AuthService.get_password_hash(raw_password)
    
    db_session.add(user)
    await db_session.commit()
    # OAuth2PasswordRequestForm ожидает данные как form-data
   # 4. Пытаемся войти под этим пользователем
    response = await client.post(
        "/auth/login", 
        # OAuth2 стандарт требует передачи данных как Form Data, а не JSON
        data={
            "username": user_data["email"], 
            "password": raw_password
        }
    )

    # 5. Проверяем результат
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session, sample_user_data_factory):
    """Тест на неверный пароль с корректно созданным пользователем."""
    password = "correct_password"
    # 1. Убедитесь, что фабрика возвращает 'first_name' и 'last_name'
    user_data = sample_user_data_factory()
    
    # 2. Извлекаем email заранее, чтобы не обращаться к expired объекту после комита
    email = user_data["email"]
    
    # Удаляем пароль из словаря, если он там есть, так как в модели password_hash
    user_data.pop("password", None) 
    
    user = User(**user_data)
    user.password_hash = AuthService.get_password_hash(password)
    
    db_session.add(user)
    await db_session.commit()
    # await db_session.refresh(user) # Если нужно использовать объект дальше

    # 3. Выполняем логин
    response = await client.post(
        "/auth/login", 
        # Убедитесь, что ваш эндпоинт ожидает Form-data (OAuth2 стандарт), 
        # либо json=... если вы используете кастомный JSON логин
        data={"username": email, "password": "wrong_password"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Покрывает JWTError (строки 55-57)"""
    # Запрос к любому защищенному эндпоинту с плохим токеном
    response = await client.get("/documents/1", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_user_not_found(client: AsyncClient):
    """Покрывает случай, когда ID в токене есть, но юзера нет в БД (строка 65)"""
    # Создаем токен для несуществующего ID
    token = AuthService.create_access_token(data={"sub": "99999"})
    response = await client.get("/documents/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

@pytest.mark.asyncio(loop_scope="session")
async def test_register_user_success(client: AsyncClient, db_session):
    """Тест успешной регистрации нового пользователя."""
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": unique_email,
        "phone_number": "+79991234567",
        "password": "strongpassword123",
        "telegram_username": "traveler_tg",
        "first_name": "Иван", 
        "last_name": "Иванов",
        "role": "user"
    }
    
    response = await client.post("/auth/register", json=payload)
    
    # Это поможет увидеть ошибку, если она останется
    if response.status_code != 201:
        print(f"Ошибка: {response.json()}")
        
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["first_name"] == "Иван"  # Проверяем, что имя сохранилось
    assert "id" in data


# @pytest.mark.asyncio
# async def test_register_duplicate_phone(client: AsyncClient, db_session, mock_client_profile: User):
#     """Тест ошибки при дублировании телефона подтвержденного пользователя."""
    
#     # 1. Помечаем пользователя как подтвержденного прямо в базе
#     # mock_client_profile — это объект User из твоей фикстуры
#     mock_client_profile.is_email_verified = True
    
#     db_session.add(mock_client_profile)
#     await db_session.commit()
#     await db_session.refresh(mock_client_profile)

#     # 2. Пытаемся зарегистрировать НОВОГО пользователя с ТЕМ ЖЕ телефоном
#     payload = {
#         "email": "entirely_new_email_2026@example.com",
#         "phone_number": mock_client_profile.phone_number, # Дубликат!
#         "password": "securepassword123",
#         "telegram_username": "new_guy_tg"
#     }

#     response = await client.post("/auth/register", json=payload)
    
#     # 3. Теперь роутер увидит, что существующий юзер подтвержден, и выдаст 400
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Пользователь с таким номером телефона уже существует"

# @pytest.mark.asyncio
# async def test_register_rate_limit(client: AsyncClient, db_session):
#     payload = {
#         "email": "speedy_gonzales_2026@example.com",
#         "phone_number": "+79001112233",
#         "password": "password123"
#     }

#     # Первая попытка — успех
#     response1 = await client.post("/auth/register", json=payload)
#     assert response1.status_code == 201

#     # Вторая попытка сразу же — ошибка 429
#     response2 = await client.post("/auth/register", json=payload)
#     assert response2.status_code == 429
#     assert "Код уже отправлен" in response2.json()["detail"]

