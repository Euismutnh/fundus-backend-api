# ===================================
# Dockerfile Produksi (JIKA main.py DI DALAM APP)
# ===================================

# 1. Base Image
FROM python:3.12-slim

# 2. Set environment variables
#
# WEB_CONCURRENCY: FastAPI berjalan async, sehingga satu worker per instance
#   sudah dapat melayani banyak request bersamaan; penskalaan diserahkan ke
#   Cloud Run. Satu worker juga membuat state rate limiter konsisten di dalam
#   instance. Naikkan hanya bila instance dialokasikan lebih dari satu vCPU.
#
# GUNICORN_TIMEOUT: harus di atas timeout klien AI (60 detik, lihat
#   app/core/ai_service.py) agar cold start layanan AI menghasilkan error yang
#   tertangani aplikasi, bukan worker yang dibunuh gunicorn di tengah jalan.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    WEB_CONCURRENCY=1 \
    GUNICORN_TIMEOUT=120

# 3. Install compiler
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Set working directory
WORKDIR /app

# 5. Copy requirements dan install dependensi + GUNICORN
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# 6. Copy application code
#    PERUBAHAN 1: Kita hanya copy folder 'app'
#    Baris 'COPY main.py .' sudah dihapus.
COPY ./app ./app

# 7. Buat non-root user untuk security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 8. Expose port (hanya dokumentasi)
EXPOSE 8080

# 9. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health')"

# 10. Run application (PERUBAHAN 2)
#     Kita panggil 'app.main:app'
CMD exec gunicorn -b "0.0.0.0:${PORT}" \
    -w "${WEB_CONCURRENCY}" \
    -k uvicorn.workers.UvicornWorker \
    --timeout "${GUNICORN_TIMEOUT}" \
    --graceful-timeout 30 \
    app.main:app