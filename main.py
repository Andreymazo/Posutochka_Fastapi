from fastapi import FastAPI, Depends
from pydantic import BaseModel
import databases
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import uvicorn


# Импорт вашей схемы модели
from your_models_file import Base, User

app = FastAPI()

# URI базы данных
DATABASE_URL = "postgresql://postgres:123456@localhost:5433/postgres"

# Создание движка и сессии
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модель Pydantic для представления пользователя
class UserSchema(BaseModel):
    id: int
    email: str
    phone_number: str
    role: str
    registration_date: str  # Используем строку, так как FastAPI не поддерживает datetime напрямую в ответах
    telegram_username: str

    class Config:
        orm_mode = True

@app.get("/users", response_model=List[UserSchema])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserSchema.from_orm(user) for user in users]




if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
