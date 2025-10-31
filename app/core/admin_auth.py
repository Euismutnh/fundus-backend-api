from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminAuth(AuthenticationBackend):
    """
    Simple single-admin authentication backend for SQLAdmin.
    Uses hardcoded credentials from environment variables.
    Perfect for skripsi/thesis projects with single administrator.
    """
    
    async def login(self, request: Request) -> bool:
        """
        Handle admin login with environment variable credentials.
        """
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        if not username or not password:
            return False
        
        # Verify against environment variables
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            # Store admin session
            request.session.update({
                "admin_authenticated": True,
                "admin_username": username
            })
            return True
        
        return False
    
    async def logout(self, request: Request) -> bool:
        """Handle admin logout"""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        """Check if admin is authenticated"""
        return request.session.get("admin_authenticated", False)
