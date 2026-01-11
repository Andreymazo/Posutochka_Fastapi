from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routers import (
    apartments,
    availability,
    balances,
    bookings,
    clients,
    landlords,
    owners,
    payments,
    photos,
    reviews,
    transactions,
    users,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan: create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


# Create FastAPI application
app = FastAPI(
    title="Posutochka API",
    description="API for apartment rental service",
    version="1.0.0",
    lifespan=lifespan,
)
# Ниже закомменчено, это для логированния ошибок
# from fastapi.exceptions import ResponseValidationError
# from fastapi.responses import JSONResponse
# import logging

# # Настройка логирования, чтобы видеть ошибки в консоли при pytest -s
# logger = logging.getLogger("fastapi")

# @app.exception_handler(ResponseValidationError)
# async def validation_exception_handler(request, exc):
#     # Этот код напечатает подробности ошибки прямо в консоль при запуске тестов
#     error_details = exc.errors()
#     print(f"\n❌ Ошибка валидации ответа в {request.url.path}:")
#     for err in error_details:
#         print(f"  - Поле: {'.'.join(map(str, err['loc']))}")
#         print(f"    Ошибка: {err['msg']}")
#         print(f"    Данные: {err.get('input')}")
    
#     return JSONResponse(
#         status_code=422,
#         content={"detail": error_details},
#     )
# Include routers
app.include_router(users.router)
app.include_router(landlords.router)
app.include_router(clients.router)
app.include_router(apartments.router)
app.include_router(photos.router)
app.include_router(bookings.router)
app.include_router(availability.router)
app.include_router(payments.router)
app.include_router(balances.router)
app.include_router(reviews.router)
app.include_router(owners.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to Posutochka API"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
