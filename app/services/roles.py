from fastapi import Depends, HTTPException, status
from app.services.auth import get_current_user
from app.models.user import User

async def get_current_landlord(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь Арендодателем."""
    if not current_user.landlord:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Эта операция доступна только для Арендодателей"
        )
    return current_user

async def get_current_client(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь Клиентом."""
    if not current_user.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Эта операция доступна только для Клиентов"
        )
    return current_user

async def get_current_owner(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь Собственником (Owner)."""
    if not current_user.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только для Собственников"
        )
    return current_user

async def get_current_investor(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь Инвестором."""
    if not current_user.investor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только для Инвесторов"
        )
    return current_user


# пример использхования на фото
# # app/routers/photos.py

# @router.post("/upload/{apartment_id}")
# async def upload_photo(
#     apartment_id: int,
#     file: UploadFile = File(...),
#     # Теперь сюда не попадет никто, кроме зарегистрированного арендодателя
#     current_user: User = Depends(get_current_landlord), 
#     db: AsyncSession = Depends(get_async_db)
# ):
#     # Дополнительная проверка "Свой-Чужой"
#     # Мы проверяем, что квартира принадлежит ИМЕННО ЭТОМУ арендодателю
#     from app.models.apartment import Apartment
#     res = await db.execute(select(Apartment).where(Apartment.id == apartment_id))
#     apt = res.scalar_one_or_none()
    
#     if not apt or apt.landlord_id != current_user.landlord.id:
#         raise HTTPException(status_code=403, detail="Вы не можете загружать фото в чужой объект")
    
#     # ... логика сохранения ...

# Маленький совет по оптимизации (для 2026г):
# Чтобы SQLAlchemy не делала лишних запросов к базе при каждой проверке роли, убедись, что когда ты получаешь User в get_current_user, ты используешь selectinload или joinedload для ролей.
# В app/services/auth.py обнови запрос юзера:
# python

# from sqlalchemy.orm import selectinload

# # Внутри get_current_user:
# query = (
#     select(User)
#     .where(User.id == int(user_id))
#     .options(
#         selectinload(User.landlord), 
#         selectinload(User.client)
#     )
# )
# result = await db.execute(query)
