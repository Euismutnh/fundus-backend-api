from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime,timezone
from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials

from app.database import get_db
from app.schemas.user_schema import (
    UserSignUpRequest, UserSignInRequest, OTPVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, UserResponse,
    TokenResponse, MessageResponse
)
from app.core.exceptions import AuthenticationError 
from fastapi import Body
from app.crud.crud_user import user_crud
from app.crud.crud_token import token_crud
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.email_service import email_service
from app.core.dependencies import get_current_active_user, security
from app.core.config import settings
from app.core.gcs_service import gcs_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=MessageResponse)
async def signup(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: Optional[str] = Form(None),
    profession: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    province_name: Optional[str] = Form(None),
    city_name: Optional[str] = Form(None),
    district_name: Optional[str] = Form(None),
    village_name: Optional[str] = Form(None),
    detailed_address: Optional[str] = Form(None),
    assignment_location: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Registrasi pengguna dengan manajemen transaksi yang benar.
    """
    
    # Normalize email (lowercase + strip whitespace)
    email = email.lower().strip()
    
    # 1. Pengecekan awal di luar transaksi
    if user_crud.is_email_exists(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 2. Validasi dan persiapan data dari Form
    parsed_date = None
    if date_of_birth:
        try:
            parsed_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format for date_of_birth. Use YYYY-MM-DD."
            )

    try:
        user_data = UserSignUpRequest(
            full_name=full_name, email=email, password=password, phone_number=phone_number,
            profession=profession, date_of_birth=parsed_date, province_name=province_name,
            city_name=city_name, district_name=district_name, village_name=village_name,
            detailed_address=detailed_address, assignment_location=assignment_location
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # --- MULAI BLOK TRANSAKSI ---
    try:
        # 3. Buat objek user di sesi (BELUM DISIMPAN PERMANEN)
        user = user_crud.create_user(db, user_data)
        db.flush()  # Mengirim data ke DB untuk mendapatkan ID, tapi belum di-commit

        # 4. Handle upload foto (jika ada)
        if photo:
            photo_url, _ = await gcs_service.upload_profile_photo(photo, user.id)
            user.photo_url = photo_url  # Update objek user di sesi
        
        # 5. Kirim email OTP verifikasi
        if not all([user.otp, user.email, user.full_name]):
             raise Exception("User data is incomplete for sending OTP.")

        if not user.otp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OTP was not generated properly"
            )
        
        email_sent = await email_service.send_otp_email(
            user.email, 
            user.full_name, 
            user.otp, 
            "account verification"
        )
        
        if not email_sent:
            raise Exception("Failed to send verification email. Please try again later.")
        
        # 6. COMMIT FINAL: Jika semua langkah berhasil, simpan semua perubahan ke DB.
        db.commit()
        
        return MessageResponse(
            message="Registration successful. Please check your email for OTP verification.",
            success=True
        )
        
    except Exception as e:
        # 7. ROLLBACK: Jika ada kegagalan di manapun, batalkan semua perubahan.
        db.rollback()
        
        # Beri pesan error yang jelas ke pengguna
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {str(e)}"
        )

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and activate user account
    Step 2: Complete registration by verifying OTP
    """
    try:
        # Verify OTP
        user = user_crud.verify_otp(db, request.email, request.otp)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Activate user
        user = user_crud.activate_user(db, user)
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Save refresh token
        user_crud.update_refresh_token(db, user, refresh_token)
        
        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )

@router.post("/signin", response_model=MessageResponse)
async def signin_step1(
    request: UserSignInRequest,
    db: Session = Depends(get_db)
):
    """
    User sign in - Step 1: Verify credentials and send OTP
    """
    try:
        # Authenticate user
        user = user_crud.authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Generate and update OTP
        otp = email_service.generate_otp()
        user_crud.update_user_otp(db, user, otp)
        
        # Send OTP email
        email_sent = await email_service.send_otp_email(
            user.email, 
            user.full_name, 
            otp, 
            "login verification"
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )
        
        return MessageResponse(
            message="OTP sent to your email. Please verify to complete login.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sign in failed: {str(e)}"
        )

@router.post("/signin/verify-otp", response_model=TokenResponse)
async def signin_step2(
    request: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    User sign in - Step 2: Verify OTP and return tokens
    """
    try:
        # Verify OTP
        user = user_crud.verify_otp(db, request.email, request.otp)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Clear OTP
        user.otp = None
        user.otp_expires_at = None
        db.commit()
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Save refresh token
        user_crud.update_refresh_token(db, user, refresh_token)
        
        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )
@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Returns new access_token dengan same refresh_token.
    
    Error handling dengan custom headers:
    - 401 + X-Token-Expired: Refresh token expired
    - 401 + X-Token-Revoked: Refresh token revoked (user logout)
    
    Frontend should handle 401 → clear storage → redirect to login
    """
    try:
        # 1. Verify refresh token signature & expiry
        payload = verify_token(refresh_token)
        if not payload:
            raise AuthenticationError(
                detail="Refresh token has expired. Please login again.",
                headers={"X-Token-Expired": "true"}  # ← Custom header
            )
        
        # 2. Get user_id from token
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError(
                detail="Invalid token payload"
            )
        
        # 3. Get user from database
        user = user_crud.get_user_by_id(db, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 4. Verify refresh token matches database
        if user.refresh_token != refresh_token:
            raise AuthenticationError(
                detail="Refresh token has been revoked. Please login again.",
                headers={"X-Token-Revoked": "true"}  # ← Custom header
            )
        
        # 5. Check if user is still active
        if not user.is_active:
            raise AuthenticationError(
                detail="User account is not active"
            )
        
        # 6. Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        # 7. Return tokens (same refresh token)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # ← Return same refresh token
            token_type="bearer"
        )
        
    except AuthenticationError:
        # Re-raise AuthenticationError (preserve custom headers)
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Forgot password - Send OTP to email for password reset
    """
    try:
        # Check if user exists
        user = user_crud.get_user_by_email(db, request.email)
        if not user:
            # Don't reveal if email exists or not for security
            return MessageResponse(
                message="If the email is registered, you will receive a password reset OTP.",
                success=True
            )
        
        # Generate and update OTP
        otp = email_service.generate_otp()
        user_crud.update_user_otp(db, user, otp)
        
        # Send forgot password email
        email_sent = await email_service.send_forgot_password_email(
            user.email, 
            user.full_name, 
            otp
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
        
        return MessageResponse(
            message="If the email is registered, you will receive a password reset OTP.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using OTP
    """
    try:
        # Verify OTP
        user = user_crud.verify_otp(db, request.email, request.otp)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Update password
        user_crud.update_password(db, user, request.new_password)
        
        # Clear all refresh tokens for security
        user_crud.clear_refresh_token(db, user)
        
        return MessageResponse(
            message="Password reset successful. Please login with your new password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.post("/signout", response_model=MessageResponse)
async def signout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Sign out user and blacklist current access token
    
    Process:
    1. Blacklist current access token (prevent reuse)
    2. Clear refresh token from database
    3. Return success message
    
    After logout:
    - Access token → Cannot be used (blacklisted)
    - Refresh token → Cannot be used (deleted from DB)
    """
    try:
        token = credentials.credentials
        
        # Get user from database
        user = user_crud.get_user_by_id(db, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # ✅ BLACKLIST ACCESS TOKEN
        payload = verify_token(token)
        if payload:
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                
                token_crud.blacklist_token(
                    db=db,
                    token=token,
                    user_id=current_user.id,
                    expires_at=expires_at
                )

        # ✅ CLEAR REFRESH TOKEN
        user_crud.clear_refresh_token(db, user)

        return MessageResponse(
            message="Successfully signed out. Your session has been terminated.",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sign out failed: {str(e)}"
        )

@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resend OTP to user email
    """
    try:
        user = user_crud.get_user_by_email(db, request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_crud.resend_otp(db, user)
        
        if not user.otp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OTP was not generated properly"
            )

        email_sent = await email_service.send_otp_email(
            user.email,
            user.full_name,
            user.otp,
            "account verification"
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )
        
        return MessageResponse(
            message="OTP resent successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend OTP failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user

@router.post("/update-profile-photo", response_model=MessageResponse)
async def update_profile_photo(
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile photo
    """
    try:
        # Get the current user from database
        user = user_crud.get_user_by_id(db, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete old photo if exists
        if user.photo_url:
            # Extract filename from URL to delete from GCS
            old_filename = user.photo_url.split('/')[-1]
            if old_filename:
                gcs_service.delete_file(f"profile_photos/user_{user.id}/{old_filename}")
        
        # Upload new photo
        photo_url, filename = await gcs_service.upload_profile_photo(photo, user.id)
        
        # Update user photo URL
        user.photo_url = photo_url
        db.commit()
        
        return MessageResponse(
            message="Profile photo updated successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile photo: {str(e)}"
        )

@router.delete("/delete-profile-photo", response_model=MessageResponse)
async def delete_profile_photo(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete user profile photo
    """
    try:
        # Get the current user from database
        user = user_crud.get_user_by_id(db, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.photo_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profile photo to delete"
            )
        
        # Extract filename from URL to delete from GCS
        old_filename = user.photo_url.split('/')[-1]
        if old_filename:
            gcs_service.delete_file(f"profile_photos/user_{user.id}/{old_filename}")
        
        # Remove photo URL from user
        user.photo_url = None
        db.commit()
        
        return MessageResponse(
            message="Profile photo deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile photo: {str(e)}"
        )
