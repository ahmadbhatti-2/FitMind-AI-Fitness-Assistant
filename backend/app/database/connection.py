import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

# Database connection string loaded from environment config
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(f"DATABASE_URL is missing from {PROJECT_ROOT / '.env'}")

# Initialize database engine instance
engine = create_engine(DATABASE_URL)

# Configure session factory with manual transaction boundary controls
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarative class inherited by ORM models
Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a transactional database session per request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()