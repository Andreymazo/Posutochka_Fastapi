import os
from collections.abc import AsyncGenerator, Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables BEFORE reading them
load_dotenv()

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/posutochka")

# Convert sync DATABASE_URL to async for AsyncEngine
# Replace postgresql:// or postgres:// with postgresql+psycopg://
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://").replace(
    "postgres://", "postgresql+psycopg://"
)

# Create SQLAlchemy engines (both sync and async)
# Sync engine for backward compatibility and migrations
engine = create_engine(DATABASE_URL)

# Async engine for new async services
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session (sync).
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    Ensures the session is closed after use.
    """
    async with AsyncSessionLocal() as session:
        yield session
