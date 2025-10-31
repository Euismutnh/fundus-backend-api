from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for additional protection"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Log request
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: times for ip, times in self.clients.items()
            if any(t > current_time - self.period for t in times)
        }
        
        # Check rate limit
        if client_ip in self.clients:
            # Filter recent calls
            recent_calls = [t for t in self.clients[client_ip] if t > current_time - self.period]
            
            if len(recent_calls) >= self.calls:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            self.clients[client_ip] = recent_calls + [current_time]
        else:
            self.clients[client_ip] = [current_time]
        
        response = await call_next(request)
        return response
