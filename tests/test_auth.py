import pytest
from httpx import AsyncClient
from app.services.auth import AuthService
from app.models import User

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session, sample_user_data_factory):
    """Тест успешного входа (покрывает auth.py и AuthService)"""
    # 1. Создаем пользователя с реальным хешем
    password = "secret_password"
    hashed = AuthService.get_password_hash(password)
    
    from app.models.user import User
    user_data = sample_user_data_factory()
    user = User(**user_data)
    user.password_hash = hashed # Используем твое имя поля
    db_session.add(user)
    await db_session.commit()

    # 2. Пытаемся залогиниться
    login_data = {
        "username": user.email,
        "password": password
    }
    # OAuth2PasswordRequestForm ожидает данные как form-data
    response = await client.post("/auth/login", data=login_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session, sample_user_data_factory):
    """Неверный пароль: теперь passlib получит валидный хеш и сможет его сравнить."""
    password = "correct_password"
    user_data = sample_user_data_factory()
    
    user = User(**user_data)
    user.password_hash = AuthService.get_password_hash(password)
    
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/auth/login", 
        data={"username": user.email, "password": "wrong_password"}
    )
    # Теперь тут будет 401, а не ошибка passlib
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

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, db_session):
    """Тест успешной регистрации нового пользователя."""
    payload = {
        "email": "new_traveler_2026@example.com",
        "phone_number": "+79991234567",
        "password": "strongpassword123",
        "telegram_username": "traveler_tg"
    }
    
    response = await client.post("/auth/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "registration_date" in data

@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient, db_session, mock_client_profile: User):
    """Тест ошибки при дублировании телефона подтвержденного пользователя."""
    
    # 1. Помечаем пользователя как подтвержденного прямо в базе
    # mock_client_profile — это объект User из твоей фикстуры
    mock_client_profile.is_email_verified = True
    
    db_session.add(mock_client_profile)
    await db_session.commit()
    await db_session.refresh(mock_client_profile)

    # 2. Пытаемся зарегистрировать НОВОГО пользователя с ТЕМ ЖЕ телефоном
    payload = {
        "email": "entirely_new_email_2026@example.com",
        "phone_number": mock_client_profile.phone_number, # Дубликат!
        "password": "securepassword123",
        "telegram_username": "new_guy_tg"
    }

    response = await client.post("/auth/register", json=payload)
    
    # 3. Теперь роутер увидит, что существующий юзер подтвержден, и выдаст 400
    assert response.status_code == 400
    assert response.json()["detail"] == "Пользователь с таким номером телефона уже существует"

@pytest.mark.asyncio
async def test_register_rate_limit(client: AsyncClient, db_session):
    payload = {
        "email": "speedy_gonzales_2026@example.com",
        "phone_number": "+79001112233",
        "password": "password123"
    }

    # Первая попытка — успех
    response1 = await client.post("/auth/register", json=payload)
    assert response1.status_code == 201

    # Вторая попытка сразу же — ошибка 429
    response2 = await client.post("/auth/register", json=payload)
    assert response2.status_code == 429
    assert "Код уже отправлен" in response2.json()["detail"]

