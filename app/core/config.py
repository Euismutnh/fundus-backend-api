from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Fundus AI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = ""

    # Database connection pool
    # Total koneksi per instance = (DB_POOL_SIZE + DB_MAX_OVERFLOW) x jumlah worker.
    # Jaga hasil kali ini, dikali jumlah maksimum instance Cloud Run, tetap di
    # bawah max_connections milik Cloud SQL.
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_RECYCLE: int = 1800

    # Rate limiting
    # RATE_LIMIT_ENABLED dapat dimatikan saat pengujian throughput, agar yang
    # terukur adalah kapasitas aplikasi dan bukan ambang rate limiter.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PERIOD: int = 60
    RATE_LIMIT_USER_CALLS: int = 100
    RATE_LIMIT_IP_CALLS: int = 1000
    RATE_LIMIT_SENSITIVE_CALLS: int = 20

    # Jumlah proxy tepercaya di depan aplikasi, dipakai untuk menentukan IP klien
    # dari header X-Forwarded-For. 0 = ambil entri pertama (perilaku Cloud Run
    # tanpa load balancer tambahan). Naikkan bila ada Cloud Load Balancing/CDN
    # di depan Cloud Run, karena entri pertama menjadi dapat dipalsukan klien.
    TRUSTED_PROXY_HOPS: int = 0

    # Security
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    ADMIN_SECRET_KEY: str = ""
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""  
    
    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "noreply.drdetection@gmail.com"
    
    # External services
    AI_SERVICE_URL: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost","http://localhost:3000","http://localhost:8080"]
    
    # Google Cloud Storage
    GCS_BUCKET_NAME: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
