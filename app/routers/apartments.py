
from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/apartments", tags=["apartments"])


@router.post("/", response_model=ApartmentRead, status_code=status.HTTP_201_CREATED)
async def create_apartment(apartment_data: ApartmentCreate, db: AsyncSession = Depends(get_async_db)) -> Apartment:
    data = apartment_data.model_dump(mode="python")
    if not isinstance(data["location"], Point):
        from shapely import wkt
        data["location"] = wkt.loads(data["location"])

    # Convert to GeoAlchemy2 WKBElement
    data["location"] = from_shape(data["location"], srid=4326)

    db_apartment = Apartment(**data)
    db.add(db_apartment)
    await db.commit()

    # ПРАВИЛЬНЫЙ REFRESH с подгрузкой связей
    query = select(Apartment).options(selectinload(Apartment.photos)).filter(Apartment.id == db_apartment.id)
    result = await db.execute(query)
    return result.scalar_one()

# 1. Сначала специфичный поиск (чтобы не перехватывал {apartment_id})
@router.get("/search", response_model=list[ApartmentRead])
async def search_apartments_by_location(
    lat: float,
    lon: float,
    radius: float = 1000.0,
    db: AsyncSession = Depends(get_async_db)
):
    """Поиск апартаментов по гео-локации (PostGIS)."""
    # 1. Создаем точку (lon первым!)
    user_geo = func.ST_GeographyFromText(f"POINT({lon} {lat})")

    # 2. Формируем запрос БЕЗ троеточий
    query = (
        select(Apartment)
        .options(selectinload(Apartment.photos)) # Подгружаем связи асинхронно
        .where(
            func.ST_DWithin(
                cast(Apartment.location, Geography),
                user_geo,
                radius
            )
        )
        .order_by(
            func.ST_Distance(
                cast(Apartment.location, Geography),
                user_geo
            )
        )
    )

    # 3. Выполняем асинхронно
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
    db: AsyncSession = Depends(get_async_db)
) -> Apartment:
    """Update an apartment."""
    # 1. Ищем апартамент
    query = select(Apartment).filter(Apartment.id == apartment_id)
    result = await db.execute(query)
    apartment = result.scalar_one_or_none()

    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

    # 2. Обновляем поля
    update_data = apartment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(apartment, field, value)

    # 3. Сохраняем
    await db.commit()

    # 4. ВАЖНО: Вместо db.refresh делаем новый SELECT с загрузкой связей
    # Это гарантирует, что Pydantic увидит поле 'photos'
    final_query = (
        select(Apartment)
        .options(selectinload(Apartment.photos))
        .filter(Apartment.id == apartment_id)
    )
    final_result = await db.execute(final_query)
    return final_result.scalar_one()


# @router.get("/{apartment_id}", response_model=ApartmentRead)
# async def get_apartment(apartment_id: int, db: AsyncSession = Depends(get_async_db)) -> Apartment:
#     """Get a specific apartment by ID."""
#     query = select(Apartment).filter(Apartment.id == apartment_id)
#     result = await db.execute(query)
#     apartment = result.scalar_one_or_none()
#     if not apartment:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")
#     return apartment

# @router.post("/", response_model=ApartmentRead, status_code=status.HTTP_201_CREATED)
# async def create_apartment(apartment_data: ApartmentCreate, db: AsyncSession = Depends(get_async_db)) -> Apartment:
#     data = apartment_data.model_dump(mode="python")

#     if not isinstance(data["location"], Point):
#         from shapely import wkt
#         data["location"] = wkt.loads(data["location"])

#     # Convert to GeoAlchemy2 WKBElement
#     data["location"] = from_shape(data["location"], srid=4326)

#     db_apartment = Apartment(**data)
#     db.add(db_apartment)
#     await db.commit()
#     await db.refresh(db_apartment)
#     return db_apartment

# @router.patch("/{apartment_id}", response_model=ApartmentRead)
# async def update_apartment(
#     apartment_id: int, apartment_data: ApartmentUpdate, db: AsyncSession = Depends(get_async_db)
# ) -> Apartment:
#     """Update an apartment."""
#     query = select(Apartment).filter(Apartment.id == apartment_id)
#     result = await db.execute(query)
#     apartment = result.scalar_one_or_none()

#     if not apartment:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

#     update_data = apartment_data.model_dump(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(apartment, field, value)

#     await db.commit()
#     await db.refresh(apartment)
#     return apartment

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
