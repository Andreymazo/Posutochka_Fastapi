from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientRead])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Client]:
    """Get all clients with pagination."""
    clients = db.query(Client).offset(skip).limit(limit).all()
    return clients


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)) -> Client:
    """Get a specific client by ID."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)) -> Client:
    """Create a new client."""
    client = Client(
        user_id=client_data.user_id,
        first_name=client_data.first_name,
        last_name=client_data.last_name,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int, client_data: ClientUpdate, db: Session = Depends(get_db)
) -> Client:
    """Update a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    db.delete(client)
    db.commit()
