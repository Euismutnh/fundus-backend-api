from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware
import logging
import uvicorn
import os

from app.core.config import settings
from app.core.middleware import SecurityMiddleware, RateLimitMiddleware
from app.core.exceptions import (
    validation_exception_handler,
    integrity_exception_handler,
    general_exception_handler
)
from app.routers import auth, users, patients, detections, dashboard
from app.database import engine, Base
from app.core.admin import setup_admin

# ===================================
# Logging
# ===================================
# Dikonfigurasi di sini, bukan sebagai efek samping saat modul di-import, agar
# hanya ada satu tempat yang mengatur logging untuk seluruh aplikasi.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

# ===================================
# Initialize FastAPI app
# ===================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DR Detection App Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===================================
# Add Middleware
# ===================================
# Urutan penting. add_middleware menaruh yang ditambahkan TERAKHIR di lapisan
# TERLUAR, sehingga urutan pemrosesan request menjadi:
#
#     CORS -> Security -> RateLimit -> Session -> router
#
# CORS diletakkan terluar agar setiap respons, termasuk 429 dari rate limiter
# dan respons error lainnya, tetap membawa header CORS; tanpa ini klien web
# hanya melihat error CORS dan tidak pernah tahu bahwa dirinya kena 429.
# Security berada di atas RateLimit agar respons 429 pun tetap memperoleh
# security header dan tercatat di access log. RateLimit tetap berada sebelum
# routing dan sebelum pekerjaan basis data apa pun.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.ADMIN_SECRET_KEY or settings.SECRET_KEY
)

# Batas diambil dari settings agar dapat disesuaikan per environment tanpa
# mengubah kode, termasuk saat pengujian beban.
app.add_middleware(RateLimitMiddleware)

app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)

# ===================================
# Exception Handlers
# ===================================
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ===================================
# Include Routers
# ===================================
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(detections.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)

# ===================================
# Setup Admin Panel
# ===================================
setup_admin(app, engine)

# ===================================
# Root Endpoints
# ===================================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DR Detection App Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "admin": "/admin"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "service": "dr-detection-backend",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

# ===================================
# Development Server (Local Only)
# ===================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )