from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.models.user import User
from app.schemas.user_schema import UserSignUpRequest, UserUpdateRequest
from app.core.security import get_password_hash, verify_password, is_otp_valid
from app.core.email_service import email_service

# Batas hidup registrasi yang belum diverifikasi OTP
UNVERIFIED_TTL_MINUTES = 10

class UserCRUD:
    def __init__(self):
        pass

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, db: Session, user_data: UserSignUpRequest, photo_url: Optional[str] = None) -> User:
        """Create new user with hashed password"""
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Generate OTP for email verification
        otp = email_service.generate_otp()
        otp_expires_at = email_service.get_otp_expiry()
        
        # Create user object
        db_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            profession=user_data.profession,
            date_of_birth=user_data.date_of_birth,
            photo_url=photo_url,
            province_name=user_data.province_name,
            city_name=user_data.city_name,
            district_name=user_data.district_name,
            village_name=user_data.village_name,
            detailed_address=user_data.detailed_address,
            assignment_location=user_data.assignment_location,
            password_hash=hashed_password,
            is_active=False,  
            otp=otp,
            otp_expires_at=otp_expires_at
        )
        
        db.add(db_user)
        return db_user

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def update_user_otp(self, db: Session, user: User, otp: str) -> User:
        """Update user OTP and expiry"""
        user.otp = otp
        user.otp_expires_at = email_service.get_otp_expiry()
        db.commit()
        db.refresh(user)
        return user

    def verify_otp(self, db: Session, email: str, otp: str) -> Optional[User]:
        """Verify OTP for user"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        # Check if OTP matches and is not expired
        if user.otp != otp:
            return None
        
        if not is_otp_valid(user.otp_expires_at):
            return None
        
        return user

    def activate_user(self, db: Session, user: User) -> User:
        """Activate user account after OTP verification"""
        user.is_active = True
        user.otp = None
        user.otp_expires_at = None
        db.commit()
        db.refresh(user)
        return user

    def update_refresh_token(self, db: Session, user: User, refresh_token: Optional[str]) -> User:
        """Update user refresh token"""
        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)
        return user

    def get_user_by_refresh_token(self, db: Session, refresh_token: str) -> Optional[User]:
        """Get user by refresh token"""
        return db.query(User).filter(User.refresh_token == refresh_token).first()

    def update_password(self, db: Session, user: User, new_password: str) -> User:
        """Update user password"""
        user.password_hash = get_password_hash(new_password)
        user.otp = None
        user.otp_expires_at = None
        db.commit()
        db.refresh(user)
        return user

    def update_user_profile(self, db: Session, user: User, user_data: UserUpdateRequest) -> User:
        """Update user profile information intelligently"""
    
        update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
    
        db.commit()
        db.refresh(user)
        return user

    def clear_refresh_token(self, db: Session, user: User) -> User:
        """Clear user refresh token (for logout)"""
        user.refresh_token = None
        db.commit()
        db.refresh(user)
        return user

    def is_email_exists(self, db: Session, email: str) -> bool:
        """Check if email already exists"""
        return db.query(User).filter(User.email == email).first() is not None

    def get_active_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Cari user yang SUDAH aktif saja (untuk cek email benar-benar terpakai)."""
        return db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()

    def get_unverified_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Cari registrasi yang BELUM diverifikasi."""
        return db.query(User).filter(
            User.email == email,
            User.is_active == False
        ).first()

    def purge_unverified_user(self, db: Session, user: User) -> None:
        """Hapus permanen registrasi yang tidak pernah diverifikasi."""
        db.delete(user)
        db.commit()

    def cleanup_stale_registrations(self, db: Session) -> int:
        """
        Hapus semua registrasi belum aktif yang OTP-nya sudah lewat TTL.
        Aman dipanggil berkala -- hanya menyentuh akun is_active = False.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=UNVERIFIED_TTL_MINUTES)
        deleted = db.query(User).filter(
            User.is_active == False,
            User.created_at < cutoff
        ).delete(synchronize_session=False)
        db.commit()
        return deleted

    def resend_otp(self, db: Session, user: User) -> User:
        """Generate and update new OTP for user"""
        otp = email_service.generate_otp()
        return self.update_user_otp(db, user, otp)

# Create global CRUD instance
user_crud = UserCRUD()
