"""
Authentication Dependencies

Handle authentication dengan 5 layer security menggunakan custom exceptions.
Semua error menggunakan AuthenticationError dengan custom headers.
"""
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError
from app.crud.crud_user import user_crud
from app.crud.crud_token import token_crud
from app.models.user import User

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Security checks:
    1. Token not blacklisted (user hasn't logged out)
    2. Token signature valid
    3. Token not expired
    4. User exists in database
    5. User account is active
    
    Raises:
        AuthenticationError: With custom headers for frontend
            - X-Token-Revoked: true (if token blacklisted)
            - X-Token-Expired: true (if token expired)
    """
    try:
        token = credentials.credentials
        
        # ✅ CHECK 1: Token blacklisted? (user sudah logout)
        if token_crud.is_token_blacklisted(db, token):
            raise AuthenticationError(
                detail="Token has been revoked. Please login again.",
                headers={"X-Token-Revoked": "true"}  # ← Custom header untuk frontend
            )
        
        # ✅ CHECK 2: Token signature & expiry valid?
        payload = verify_token(token)
        if payload is None:
            raise AuthenticationError(
                detail="Invalid or expired token. Please login again.",
                headers={"X-Token-Expired": "true"}  # ← Custom header untuk frontend
            )
        
        # ✅ CHECK 3: Extract user ID
        sub = payload.get("sub")
        if sub is None:
            raise AuthenticationError(
                detail="Invalid token payload"
            )

        try:
            user_id = int(sub)
        except ValueError:
            raise AuthenticationError(
                detail="Invalid user ID in token"
            )
        
        # ✅ CHECK 4: User exists?
        user = user_crud.get_user_by_id(db, user_id=user_id)
        if user is None:
            raise AuthenticationError(
                detail="User not found"
            )
        
        # ✅ CHECK 5: User is active?
        if not user.is_active:
            raise AuthenticationError(
                detail="User account is not active"
            )
        
        return user
        
    except AuthenticationError:
        # Re-raise AuthenticationError as-is (preserve custom headers)
        raise
    except Exception as e:
        # Catch any unexpected error
        raise AuthenticationError(
            detail=f"Authentication failed: {str(e)}"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (double check for active status)
    
    This is a secondary check, but should never fail if get_current_user passed.
    """
    if not current_user.is_active:
        raise AuthenticationError(
            detail="User account is not active"
        )
    return current_user