from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routers import users, landlords, clients, apartments, photos, bookings, payments
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


# Create FastAPI application
app = FastAPI(
    title="Posutochka API",
    description="API for apartment rental service",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(users.router)
app.include_router(landlords.router)
app.include_router(clients.router)
app.include_router(apartments.router)
app.include_router(photos.router)
app.include_router(bookings.router)
app.include_router(payments.router)


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
