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
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        # Gagal cepat ketika pool habis, agar beban berlebih terlihat sebagai
        # error yang jelas dan bukan sebagai request yang menggantung.
        pool_timeout=settings.DB_POOL_TIMEOUT,
        # Daur ulang koneksi sebelum sempat diputus diam-diam oleh infrastruktur.
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        # Echo hanya untuk debugging lokal. Menyalakannya di produksi menuliskan
        # setiap statement SQL ke Cloud Logging pada setiap request: latensi naik
        # signifikan dan isi query, termasuk data pasien, ikut tercetak ke log.
        echo=settings.SQL_ECHO
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
