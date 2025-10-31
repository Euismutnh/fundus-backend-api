from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.schemas.user_schema import UserUpdateRequest, UserResponse, MessageResponse
from app.crud.crud_user import user_crud
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile (partial update supported).
    You can send only the fields you want to update.
    """
    try:
        user_to_update = user_crud.get_user_by_id(db, current_user.id)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        updated_user = user_crud.update_user_profile(db=db, user=user_to_update, user_data=update_data)
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )