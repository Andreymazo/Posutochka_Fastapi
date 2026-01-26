from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import AuthService # 1. Импортируй сервис
from app.database import get_async_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def get_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)) -> list[User]:
    """Get all users with pagination."""
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)) -> User:
    """Get a specific user by ID."""
    query = select(User).filter(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user



@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)) -> User:
    """Create a new user."""
    # Check if email already exists
    query = select(User).filter(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Check if phone number already exists
    query = select(User).filter(User.phone_number == user_data.phone_number)
    result = await db.execute(query)
    existing_phone = result.scalar_one_or_none()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered"
        )

    # Create new user с реальным хешированием
    user = User(
        email=user_data.email,
        phone_number=user_data.phone_number,
        telegram_username=user_data.telegram_username,
        # ИСПРАВЛЕНИЕ ТУТ: берем password из схемы и хешируем его через сервис
        password_hash=AuthService.get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name

    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
# @router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
# async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)) -> User:
#     """Create a new user."""
#     # Check if email already exists
#     query = select(User).filter(User.email == user_data.email)
#     result = await db.execute(query)
#     existing_user = result.scalar_one_or_none()
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
#         )

#     # Check if phone number already exists
#     query = select(User).filter(User.phone_number == user_data.phone_number)
#     result = await db.execute(query)
#     existing_phone = result.scalar_one_or_none()
#     if existing_phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered"
#         )

#     # Create new user (in real app, hash the password)
#     user = User(
#         email=user_data.email,
#         phone_number=user_data.phone_number,
#         password_hash=user_data.password_hash,  # Already hashed in real app
#         telegram_username=user_data.telegram_username,
#     )
#     db.add(user)
#     await db.commit()
#     await db.refresh(user)
#     return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_async_db)) -> User:
    """Update a user."""
    query = select(User).filter(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = update_data.pop("password")  # TODO: Hash

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a user."""
    query = select(User).filter(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()
