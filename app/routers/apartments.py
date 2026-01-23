
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from geoalchemy2 import Geography
from geoalchemy2.shape import from_shape
from shapely.geometry.point import Point
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Any
from app.database import get_async_db
from app.models.apartment import Apartment
from app.schemas.apartment import ApartmentCreate, ApartmentRead, ApartmentUpdate
from app.services.roles import get_current_landlord 
from app.models.user import User
from app.models.apartmentavailability import ApartmentAvailability
from sqlalchemy.dialects.postgresql import DATERANGE
from datetime import date
import uuid
import aioboto3
from app.models import Photo

router = APIRouter(prefix="/apartments", tags=["apartments"])


@router.post("/", response_model=ApartmentRead, status_code=status.HTTP_201_CREATED)
async def create_apartment(
    apartment_data: ApartmentCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_landlord: User = Depends(get_current_landlord)) -> Apartment:
    data = apartment_data.model_dump(mode="python")
    if not isinstance(data["location"], Point):
        from shapely import wkt
        data["location"] = wkt.loads(data["location"])

    # Convert to GeoAlchemy2 WKBElement
    data["location"] = from_shape(data["location"], srid=4326)
     # АВТОМАТИЧЕСКАЯ ПРИВЯЗКА
    # Мы берем id именно из связанной модели Landlord
    data["landlord_id"] = current_landlord.landlord.id 
    
    db_apartment = Apartment(**data)
    db.add(db_apartment)
    await db.commit()
    query = (
        select(Apartment)
        .options(
            selectinload(Apartment.photos), 
            selectinload(Apartment.landlord) # Подгружаем владельца, чтобы Pydantic не упал
        )
        .filter(Apartment.id == db_apartment.id)
    )
    # query = select(Apartment).options(selectinload(Apartment.photos)).filter(Apartment.id == db_apartment.id)
    result = await db.execute(query)
    return result.scalar_one()


@router.get("/search", response_model=list[ApartmentRead])
async def search_apartments(
    lat: float, lon: float,
    check_in: date, check_out: date,
    radius: float = 1000.0,
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Создаем диапазон для поиска
    requested_range = (check_in, check_out)

    # 2. Подзапрос: находим апартаменты, которые заблокированы
    # Оператор '&&' в Postgres проверяет перекрытие диапазонов
    blocked_subquery = (
        select(ApartmentAvailability.apartment_id)
        .where(
            ApartmentAvailability.blocked_period.overlaps(requested_range),
            ApartmentAvailability.is_blocked == True
        )
    )

    # 3. Основной запрос: Поиск + Гео + Проверка доступности
    user_geo = func.ST_GeographyFromText(f"POINT({lon} {lat})")
    # Для теста: сначала просто проверим гео, без дат
    #user_geo = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    query = (
        select(Apartment)
        .options(selectinload(Apartment.photos))
        .where(
            # Исключаем тех, у кого есть пересечение с заблокированным периодом
            ~Apartment.id.in_(blocked_subquery),
            func.ST_DWithin(cast(Apartment.location, Geography), user_geo, radius)
        )
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/", response_model=list[ApartmentRead])
async def get_apartments(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)
    ) -> Any:
    """Get all apartments with pagination."""
    query = (
        select(Apartment)
        .options(selectinload(Apartment.photos))  # ЖАДНАЯ ЗАГРУЗКА ФОТО
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{apartment_id}", response_model=ApartmentRead)
async def get_apartment(apartment_id: int, db: AsyncSession = Depends(get_async_db)):
    query = (
        select(Apartment)
        .options(selectinload(Apartment.photos)) # <-- ДОБАВИТЬ ЭТО
        .where(Apartment.id == apartment_id)
    )
    result = await db.execute(query)
    apartment = result.scalar_one_or_none()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    return apartment


@router.patch("/{apartment_id}", response_model=ApartmentRead)
async def update_apartment(
    apartment_id: int, 
    apartment_data: ApartmentUpdate, 
    db: AsyncSession = Depends(get_async_db),
    # Только лендлорд может редактировать
    current_landlord: User = Depends(get_current_landlord)
) -> Apartment:
    """Update an apartment."""
    query = select(Apartment).filter(Apartment.id == apartment_id)
    result = await db.execute(query)
    apartment = result.scalar_one_or_none()

    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

    # ПРОВЕРКА ВЛАДЕНИЯ: может ли этот лендлорд редактировать ЭТОТ апартамент?
    if apartment.landlord_id != current_landlord.landlord.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы можете редактировать только свои объекты"
        )

    update_data = apartment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(apartment, field, value)

    await db.commit()

    final_query = (
        select(Apartment)
        .options(selectinload(Apartment.photos))
        .filter(Apartment.id == apartment_id)
    )
    final_result = await db.execute(final_query)
    return final_result.scalar_one()

@router.delete("/{apartment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apartment(apartment_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete an apartment."""
    query = select(Apartment).filter(Apartment.id == apartment_id)
    result = await db.execute(query)
    apartment = result.scalar_one_or_none()

    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

    await db.delete(apartment)
    await db.commit()



router = APIRouter()

# Конфигурация из docker-compose
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "strong_password_2026"
BUCKET_NAME = "apartments"

@router.post("/{apartment_id}/photos", status_code=status.HTTP_201_CREATED)
async def upload_apartment_photo(
    apartment_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Валидация формата
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Можно загружать только изображения")

    # 2. Уникальное имя (папка апартамента + UUID)
    file_ext = file.filename.split(".")[-1]
    object_name = f"{apartment_id}/{uuid.uuid4()}.{file_ext}"

    # 3. Асинхронная загрузка
    session = aioboto3.Session()
    try:
        async with session.client(
            "s3", 
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        ) as s3:
            # Загружаем файл
            await s3.upload_fileobj(file.file, BUCKET_NAME, object_name)
    except Exception as e:
        # Если MinIO упал, не идем дальше
        raise HTTPException(status_code=500, detail=f"Ошибка хранилища: {str(e)}")

    # 4. URL для фронтенда (localhost, так как порты проброшены)
    photo_url = f"http://localhost:9000/{BUCKET_NAME}/{object_name}"

    # 5. Запись в БД
    new_photo = Photo(
        apartment_id=apartment_id,
        url=photo_url
    )
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo) # Чтобы получить ID из базы

    return new_photo
