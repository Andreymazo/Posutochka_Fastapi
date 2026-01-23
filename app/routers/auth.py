from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_db
from app.models.user import User
from app.services.auth import AuthService
from app.schemas.user import UserCreate, UserRead


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
    # 1. Проверка уникальности email и телефона
    query = select(User).where((User.email == user_data.email) | (User.phone_number == user_data.phone_number))
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или телефоном уже существует"
        )
    
    # 2. Создание пользователя
    new_user = User(
        email=user_data.email,
        phone_number=user_data.phone_number,
        telegram_username=user_data.telegram_username,
        password_hash=AuthService.get_password_hash(user_data.password)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
