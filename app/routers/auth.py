from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.database import get_async_db
from app.models.user import User
from app.services.auth import AuthService
from app.schemas.user import UserCreate, UserRead
from app.services.notification_tasks import send_verification_task
import redis.asyncio as redis
from app.services.auth import get_current_user
import os
from app.core.redis import get_redis
import uuid 


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    # Поиск юзера по email (username в форме OAuth2)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    # Проверка пароля через твое поле password_hash
    if not user or not AuthService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен, упаковывая ID пользователя в "sub"
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    redis_client = await get_redis()
    limit_key = f"register_limit:{user_data.email}"
    
    try:
        # 1. ПРОВЕРКА RATE LIMIT (защита от спама кодами)
        is_locked = await redis_client.get(limit_key)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Код уже отправлен. Повторный запрос возможен через 60 секунд."
            )

        # 2. ПОИСК СУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ
        query = select(User).where(
            or_(
                User.email == user_data.email,
                User.phone_number == user_data.phone_number
            )
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Если юзер уже подтвержден — это жесткий дубликат
            if existing_user.is_email_verified:
                detail = "Пользователь с таким email уже существует" if existing_user.email == user_data.email \
                         else "Пользователь с таким номером телефона уже существует"
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
            
            # МЯГКАЯ РЕГИСТРАЦИЯ: Обновляем данные неподтвержденного юзера
            existing_user.password_hash = AuthService.get_password_hash(user_data.password)
            existing_user.telegram_username = user_data.telegram_username
            existing_user.telegram_id = getattr(user_data, "telegram_id", None)
            # Сбрасываем дату регистрации на текущую (2026), чтобы отложить очистку
            existing_user.registration_date = func.now() 
            
            new_user = existing_user
        else:
            # СОЗДАНИЕ НОВОГО
            new_user = User(
                email=user_data.email,
                phone_number=user_data.phone_number,
                telegram_username=user_data.telegram_username,
                telegram_id=getattr(user_data, "telegram_id", None),
                password_hash=AuthService.get_password_hash(user_data.password),
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
            db.add(new_user)

        # 3. СОХРАНЕНИЕ И УСТАНОВКА ЛИМИТА
        try:
            await db.commit()
            await db.refresh(new_user)
            
            # Ставим блокировку на Email в Redis на 60 секунд
            await redis_client.set(limit_key, "1", ex=60)
            
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка при регистрации. Попробуйте позже."
            )
        # 3.1. Генерация токена для Telegram
        tg_link_token = str(uuid.uuid4())
        
        # 2. Сохраняем связь "токен -> user_id" в Redis на 15 минут
        # Это позволит вебхуку узнать, кто нажал /start
        await redis_client.set(f"tg_link:{tg_link_token}", new_user.id, ex=900)

        # 4. Формируем ссылку на бота
        # Замени 'your_posutochka_bot' на имя своего бота
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "posutochka_rent_bot")
        telegram_link = f"https://t.me/{bot_username}?start={tg_link_token}"

        # 4. ЗАПУСК CELERY (отправка кода)
        send_verification_task.delay(
            user_id=new_user.id,
            email=new_user.email,
            tg_id=new_user.telegram_id
        )
        # Добавляем ссылку в объект (нужно расширить схему UserRead или вернуть в заголовке/ответе)
        # Для начала просто выведем в лог или добавим в описание
        print(f"--- [DEBUG 2026] Ссылка для привязки TG: {telegram_link} ---")
        
        # Чтобы фронтенд видел ссылку, её нужно добавить в схему UserRead
        # Либо возвращать её отдельно. Если схема не расширена,
        # пользователь просто увидит стандартные данные.
        return new_user

    finally:
        await redis_client.aclose()


@router.post("/verify-otp")
async def verify_otp(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    redis_client = await get_redis()
    try:
        # 1. Достаем код
        stored_code = await redis_client.get(f"otp:{current_user.id}")
        
        if not stored_code:
            raise HTTPException(status_code=400, detail="Код истек или не запрашивался")
        
        # 2. Сравниваем
        if stored_code != code:
            raise HTTPException(status_code=400, detail="Неверный код подтверждения")
        
        # 3. Обновляем статус в БД (только Email пока)
        current_user.is_email_verified = True
        await db.commit()
        
        # 4. Удаляем код
        await redis_client.delete(f"otp:{current_user.id}")
        
        return {"message": "Почта успешно подтверждена"}
    finally:
        # Важно закрывать соединение, если get_redis не делает этого сам
        await redis_client.aclose()


'''Если не получил письма'''
@router.post("/resend-otp")
async def resend_otp(
    current_user: User = Depends(get_current_user)
):
    # Можно добавить проверку на Rate Limit, чтобы не спамили (раз в 60 сек)
    
    send_verification_task.delay(
        user_id=current_user.id,
        email=current_user.email,
        tg_id=current_user.telegram_id
    )
    return {"message": "Новый код отправлен"}
