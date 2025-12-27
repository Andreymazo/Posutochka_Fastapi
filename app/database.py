import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables BEFORE reading them
load_dotenv()

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/posutochka")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
