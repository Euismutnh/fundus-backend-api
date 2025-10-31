from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import date, datetime
from typing import Optional
import re
from app.core.utils import validate_email  # ← IMPORT validator dari utils

class UserSignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone_number: Optional[str] = None
    profession: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    
    # Address fields
    province_name: Optional[str] = Field(None, max_length=100)
    city_name: Optional[str] = Field(None, max_length=100)
    district_name: Optional[str] = Field(None, max_length=100)
    village_name: Optional[str] = Field(None, max_length=100)
    detailed_address: Optional[str] = None
    assignment_location: Optional[str] = Field(None, max_length=255)

    @field_validator('email')
    def validate_email_format(cls, v):
        """Custom email validation with strict rules"""
        if not validate_email(v):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        return v.lower().strip()  # Normalize: lowercase & remove whitespace

    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Indonesian phone number validation (starts with 08, 10-15 digits)
        if not re.match(r'^08\d{8,13}$', v):
            raise ValueError('Phone number must start with 08 and be 10-15 digits long')
        return v

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserSignInRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    def validate_email_format(cls, v):
        """Custom email validation"""
        if not validate_email(v):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        return v.lower().strip()


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator('email')
    def validate_email_format(cls, v):
        """Custom email validation"""
        if not validate_email(v):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        return v.lower().strip()
    
    @field_validator('otp')
    def validate_otp_format(cls, v):
        """Validate OTP is 6 digits"""
        if not v.isdigit():
            raise ValueError('OTP must contain only numbers')
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator('email')
    def validate_email_format(cls, v):
        """Custom email validation"""
        if not validate_email(v):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        return v.lower().strip()


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('email')
    def validate_email_format(cls, v):
        """Custom email validation"""
        if not validate_email(v):
            raise ValueError('Invalid email format. Please provide a valid email address.')
        return v.lower().strip()
    
    @field_validator('otp')
    def validate_otp_format(cls, v):
        """Validate OTP is 6 digits"""
        if not v.isdigit():
            raise ValueError('OTP must contain only numbers')
        return v

    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = None
    profession: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    
    # Address fields
    province_name: Optional[str] = Field(None, max_length=100)
    city_name: Optional[str] = Field(None, max_length=100)
    district_name: Optional[str] = Field(None, max_length=100)
    village_name: Optional[str] = Field(None, max_length=100)
    detailed_address: Optional[str] = None
    assignment_location: Optional[str] = Field(None, max_length=255)

    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        # Skip validation jika None atau empty string
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None  # Ubah empty string jadi None
        
        # Validasi hanya jika ada value
        if not re.match(r'^08\d{8,13}$', v):
            raise ValueError('Phone number must start with 08 and be 10-15 digits long')
        return v

    @field_validator('full_name', 'profession', 'province_name', 'city_name', 
                     'district_name', 'village_name', 'detailed_address', 
                     'assignment_location')
    def validate_string_fields(cls, v):
        # Ubah empty string jadi None untuk semua string fields
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator('date_of_birth', mode='before')
    def validate_date_of_birth(cls, v):
        # Skip validation jika None atau empty string
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
        
        # Jika sudah date object, return langsung
        if isinstance(v, date):
            return v
            
        # Jika string, parse
        if isinstance(v, str):
            try:
                return datetime.strptime(v.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        
        return v


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: Optional[str]
    profession: Optional[str]
    date_of_birth: Optional[date]
    photo_url: Optional[str]
    
    # Address fields
    province_name: Optional[str]
    city_name: Optional[str]
    district_name: Optional[str]
    village_name: Optional[str]
    detailed_address: Optional[str]
    assignment_location: Optional[str]
    
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
    success: bool = True