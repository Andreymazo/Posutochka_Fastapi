from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_async_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from typing import Any

router = APIRouter(prefix="/clients", tags=["clients"])

# Вспомогательная функция, чтобы не дублировать логику загрузки связей
async def get_client_db(client_id: int, db: AsyncSession) -> Client | None:
    query = (
        select(Client)
        .options(
            selectinload(Client.user), 
            selectinload(Client.reviews_about_me),
            selectinload(Client.reviews_i_wrote), 
        )
        .where(Client.id == client_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

@router.get("/", response_model=list[ClientRead])
async def get_clients(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    """Get all clients with pagination and reviews."""
    query = (
        select(Client)
        .options(
            selectinload(Client.reviews_about_me),
            selectinload(Client.reviews_i_wrote)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_async_db)):
    client = await get_client_db(client_id, db)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client

@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_async_db)):
    client = Client(
        user_id=client_data.user_id,
       
    )
    db.add(client)
    await db.commit()
    # Загружаем со связями для корректного ответа API
    return await get_client_db(client.id, db)

@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(client_id: int, client_data: ClientUpdate, db: AsyncSession = Depends(get_async_db)):
    # Используем вспомогательную функцию для получения объекта
    client = await get_client_db(client_id, db)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    # После коммита обновляем состояние объекта со связями
    return await get_client_db(client.id, db)

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_async_db)):
    query = select(Client).filter(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    await db.delete(client)
    await db.commit()
