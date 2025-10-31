from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

if "sqlite" in DATABASE_URL:
    # SQLite configuration (for testing)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
else:
    # PostgreSQL configuration (for production)
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=True  # Set to True for SQL debugging
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

# Create Base class for models
Base = declarative_base()

# Metadata with schema
metadata = MetaData(schema="schema_retinophaty")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
