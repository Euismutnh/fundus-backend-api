from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """
    Custom authentication error with support for custom headers
    
    Usage:
        # Basic usage
        raise AuthenticationError("Invalid credentials")
        
        # With custom headers (untuk frontend)
        raise AuthenticationError(
            detail="Token expired",
            headers={"X-Token-Expired": "true"}
        )
    """
    def __init__(
        self, 
        detail: str = "Authentication failed",
        headers: Optional[Dict[str, str]] = None
    ):
        # Merge default headers dengan custom headers
        default_headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            default_headers.update(headers)
        
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=default_headers
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(HTTPException):
    """Custom validation error"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class DatabaseError(HTTPException):
    """Custom database error"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation errors"""
    if isinstance(exc, RequestValidationError):
        formatted_errors = []
        for error in exc.errors():
            formatted_errors.append({
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type"),
            })
        
        logger.error(f"Validation error: {formatted_errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation failed",
                "errors": formatted_errors
            }
        )
    raise exc


async def integrity_exception_handler(request: Request, exc: Exception):
    """Handle database integrity errors"""
    if isinstance(exc, IntegrityError):
        logger.error(f"Database integrity error: {str(exc)}")

        msg = str(exc).lower()
        if "duplicate key" in msg:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "Resource already exists"}
            )
        elif "foreign key" in msg:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Referenced resource does not exist"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Database operation failed"}
            )
    raise exc


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )