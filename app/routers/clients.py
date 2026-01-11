from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_async_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from typing import Any

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientRead])
async def get_clients(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)) -> list[Client]:
    """Get all clients with pagination."""
    query = select(Client).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int, 
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Get client details with reviews."""
    query = (
        select(Client)
        .options(
            selectinload(Client.reviews_about_me), # Отзывы о клиенте от арендодателей
            selectinload(Client.reviews_i_wrote)   # Отзывы, которые написал сам клиент
        )
        .where(Client.id == client_id)
    )
    
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Client not found"
        )
        
    return client

@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_async_db)) -> Client:
    """Create a new client."""
    client = Client(
        user_id=client_data.user_id,
        first_name=client_data.first_name,
        last_name=client_data.last_name,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int, client_data: ClientUpdate, db: AsyncSession = Depends(get_async_db)
) -> Client:
    """Update a client."""
    query = select(Client).filter(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a client."""
    query = select(Client).filter(Client.id == client_id)
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    await db.delete(client)
    await db.commit()
