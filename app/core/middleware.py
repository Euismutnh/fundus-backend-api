"""
Middleware aplikasi: security headers, access logging, dan rate limiting.

Catatan arsitektur (relevan untuk dokumentasi dan pengujian performa):

1. Rate limiting di sini memakai state in-memory per proses. Dengan konfigurasi
   Cloud Run project ini (satu worker gunicorn per instance, lihat Dockerfile),
   state konsisten di dalam satu instance, tetapi TIDAK dibagi antar-instance
   saat auto-scaling. Kuota efektif karena itu = limit x jumlah instance aktif.
   Penegakan kuota yang ketat lintas instance memerlukan shared state
   (Memorystore/Redis) atau penegakan di edge (Cloud Armor). Keterbatasan ini
   disengaja dan didokumentasikan, bukan kelalaian implementasi.

2. Middleware ini TIDAK memeriksa blacklist token. Tugasnya hanya
   MENGIDENTIFIKASI pengirim request agar kuota tidak tercampur antar user yang
   berada di belakang satu IP. Validasi otorisasi penuh (blacklist, keberadaan
   user, status aktif) tetap dilakukan dependency get_current_user di endpoint.
   Konsekuensi yang diterima: pemegang token yang sudah signout masih dapat
   menghabiskan kuota milik user tersebut sebelum ditolak endpoint. Risikonya
   rendah karena penyerang harus sudah memegang token valid milik korban, namun
   ini tetap dicatat sebagai risiko yang diterima, bukan sebagai nihil risiko.

3. Batas per-IP dan per-user sengaja berbeda dan diperiksa bersamaan. Batas
   per-user adalah throttle normal; batas per-IP jauh lebih longgar dan hanya
   berfungsi sebagai jaring pengaman terhadap penyalahgunaan dari satu sumber,
   sehingga klinik dengan banyak petugas di belakang satu NAT tidak saling
   memakan kuota.
"""
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
import logging
import time
import uuid

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.security import verify_token

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security headers, correlation id, dan access log untuk setiap request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # X-XSS-Protection sengaja dinonaktifkan. XSS auditor bawaan browser
        # lama justru pernah menjadi sumber kerentanan, dan OWASP kini
        # merekomendasikan nilai "0" dengan mengandalkan nosniff serta CSP.
        response.headers["X-XSS-Protection"] = "0"

        # HSTS hanya bermakna, dan hanya boleh dikirim, di atas HTTPS.
        is_https = (
            request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto") == "https"
        )
        if is_https:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Respons API dapat memuat data pasien, sehingga tidak boleh diendapkan
        # di cache perantara maupun di penyimpanan browser.
        if request.url.path.startswith(settings.API_V1_STR):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"

        # Yang dicatat adalah template rute ("/api/v1/patients/{patient_code}"),
        # bukan URL mentah, agar identitas pasien tidak bocor ke log. Query
        # string sengaja tidak pernah ikut dicatat dengan alasan yang sama.
        route = request.scope.get("route")
        path = getattr(route, "path", None) or request.url.path

        if response.status_code >= 500:
            emit = logger.error
        elif response.status_code >= 400:
            emit = logger.warning
        else:
            emit = logger.info
        emit(
            "%s %s %s %.4fs rid=%s",
            request.method,
            path,
            response.status_code,
            duration,
            request_id,
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting sliding-window dengan tiga bucket yang diperiksa bersamaan:

    - ``sensitive:<ip>`` : endpoint kredensial/OTP, kuota paling ketat.
    - ``ip:<ip>``        : jaring pengaman anti-abuse per sumber.
    - ``user:<user_id>`` : throttle normal, aktif bila request membawa JWT valid.

    Request ditolak bila salah satu bucket penuh. Lihat catatan modul di atas
    untuk batasan yang diketahui dan alasan desainnya.
    """

    # Endpoint operasional yang tidak boleh ikut terkena limit. Probe kesehatan
    # Cloud Run masuk lewat proxy yang sama dengan trafik anonim, sehingga bila
    # ikut dibatasi ia dapat memicu 429 dan membuat instance dinilai unhealthy.
    EXEMPT_PATHS = frozenset({"/", "/health", "/docs", "/redoc", "/openapi.json"})
    EXEMPT_PREFIXES = ("/admin/statics",)

    # Endpoint yang memverifikasi kredensial atau memicu pengiriman OTP/email.
    # Kuota ketat di sini adalah proteksi terhadap credential stuffing dan
    # penyalahgunaan pengiriman email.
    SENSITIVE_SUFFIXES = (
        "/auth/signup",
        "/auth/signin",
        "/auth/signin/verify-otp",
        "/auth/verify-otp",
        "/auth/resend-otp",
        "/auth/refresh",
        "/auth/forgot-password",
        "/auth/reset-password",
    )

    # Batas atas jumlah key yang dilacak, sebagai proteksi terhadap pertumbuhan
    # memori tak terbatas bila ada banyak sumber unik dalam satu jendela waktu.
    MAX_TRACKED_KEYS = 20_000

    # Jarak minimum antar pembersihan. Tanpa ini, kondisi kelebihan key akan
    # memicu pemindaian penuh pada setiap request dan justru menjadi beban
    # tersendiri saat aplikasi sedang ditekan.
    CLEANUP_MIN_INTERVAL = 1.0

    def __init__(
        self,
        app,
        calls: Optional[int] = None,
        period: Optional[int] = None,
        ip_calls: Optional[int] = None,
        sensitive_calls: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        super().__init__(app)
        self.user_calls = calls if calls is not None else settings.RATE_LIMIT_USER_CALLS
        self.ip_calls = ip_calls if ip_calls is not None else settings.RATE_LIMIT_IP_CALLS
        self.sensitive_calls = (
            sensitive_calls
            if sensitive_calls is not None
            else settings.RATE_LIMIT_SENSITIVE_CALLS
        )
        self.period = period if period is not None else settings.RATE_LIMIT_PERIOD
        self.enabled = enabled if enabled is not None else settings.RATE_LIMIT_ENABLED

        self.clients: Dict[str, Deque[float]] = {}
        # time.monotonic dipakai konsisten agar penyesuaian jam sistem tidak
        # pernah membuat jendela waktu melompat.
        self._last_cleanup = time.monotonic()

    def _is_exempt(self, path: str) -> bool:
        return path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if parts:
                hops = settings.TRUSTED_PROXY_HOPS
                if hops <= 0:
                    return parts[0]
                return parts[-min(hops, len(parts))]
        # request.client.host di belakang proxy berisi alamat proxy, bukan klien,
        # sehingga hanya dipakai bila X-Forwarded-For tidak tersedia.
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _user_id(request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:].strip()
        if not token:
            return None

        # Token invalid atau kedaluwarsa sengaja tidak ditolak di sini; itu
        # tanggung jawab dependency autentikasi. Request tersebut cukup jatuh
        # kembali ke bucket berbasis IP.
        payload = verify_token(token)
        if not payload:
            return None

        sub = payload.get("sub")
        return str(sub) if sub else None

    def _buckets(self, request: Request) -> List[Tuple[str, int]]:
        client_ip = self._client_ip(request)
        buckets: List[Tuple[str, int]] = []

        if request.url.path.endswith(self.SENSITIVE_SUFFIXES):
            buckets.append((f"sensitive:{client_ip}", self.sensitive_calls))

        buckets.append((f"ip:{client_ip}", self.ip_calls))

        user_id = self._user_id(request)
        if user_id:
            buckets.append((f"user:{user_id}", self.user_calls))

        return buckets

    def _cleanup(self, now: float) -> None:
        """Buang key yang seluruh catatannya sudah keluar dari jendela waktu."""
        cutoff = now - self.period
        stale = [key for key, hits in self.clients.items() if not hits or hits[-1] <= cutoff]
        for key in stale:
            del self.clients[key]

        # Bila setelah pembersihan jumlah key masih melampaui batas, key yang
        # paling lama tidak aktif dibuang secara paksa. Tanpa langkah ini
        # MAX_TRACKED_KEYS hanya menjadi ambang pemicu, bukan batas memori yang
        # sebenarnya. Konsekuensinya key yang dibuang kehilangan riwayatnya dan
        # kuotanya kembali penuh; ini pertukaran yang disengaja, karena menjaga
        # instance tetap hidup lebih penting daripada menegakkan kuota secara
        # sempurna pada kondisi ekstrem.
        excess = len(self.clients) - self.MAX_TRACKED_KEYS
        if excess > 0:
            oldest = sorted(self.clients, key=lambda k: self.clients[k][-1])[:excess]
            for key in oldest:
                del self.clients[key]

        self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        now = time.monotonic()
        cutoff = now - self.period

        # Pembersihan dilakukan berkala, bukan pada setiap request, agar biayanya
        # tidak sebanding dengan jumlah key yang sedang dilacak.
        since_cleanup = now - self._last_cleanup
        overflowing = (
            len(self.clients) > self.MAX_TRACKED_KEYS
            and since_cleanup >= self.CLEANUP_MIN_INTERVAL
        )
        if since_cleanup >= self.period or overflowing:
            self._cleanup(now)

        buckets = self._buckets(request)

        # Fase 1 dan fase 2 di bawah tidak dipisahkan oleh await mana pun,
        # sehingga keduanya atomik terhadap event loop dan tidak ada request
        # bersamaan yang dapat menyelinap di antaranya.

        # Fase 1: evaluasi. Request ditolak bila salah satu bucket sudah penuh.
        for key, limit in buckets:
            hits = self.clients.get(key)
            if hits is None:
                continue
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                # Request yang ditolak sengaja tidak ikut dicatat, agar klien
                # yang terus mencoba tidak memperpanjang blokirnya sendiri
                # tanpa batas.
                retry_after = max(1, int(hits[0] + self.period - now) + 1)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers={"Retry-After": str(retry_after)},
                )

        # Fase 2: seluruh bucket lolos, catat request ini.
        for key, _ in buckets:
            self.clients.setdefault(key, deque()).append(now)

        return await call_next(request)
