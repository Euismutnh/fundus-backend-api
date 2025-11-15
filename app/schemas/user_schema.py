from pydantic import BaseModel, field_validator, Field, EmailStr
from datetime import date, datetime
from typing import Optional

# Import semua validator dari utils
from app.core.utils import (
    validate_phone_number,
    validate_password_strength,
    validate_date_of_birth,
)


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

    @field_validator("phone_number")
    def validate_phone(cls, v):
        """Validate Indonesian phone number (08xxxxxxxxxx)"""
        if v is None:
            return v

        if not validate_phone_number(v):
            raise ValueError(
                "Invalid phone number. Must start with 08 and be 10-15 digits long "
                "(e.g., 08123456789)"
            )
        return v

    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength dengan requirements lengkap"""
        result = validate_password_strength(v)

        if not result["is_valid"]:
            # Gabungkan semua error messages
            error_message = ". ".join(result["errors"])
            raise ValueError(error_message)

        return v

    @field_validator("date_of_birth")
    def validate_dob(cls, v):
        """Validate date of birth (opsional, tapi kalau ada harus valid)"""
        if v is None:
            return v

        result = validate_date_of_birth(v)
        if not result["is_valid"]:
            raise ValueError(result["error"])

        return v


class UserSignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    def validate_otp_format(cls, v):
        """Validate OTP is 6 digits"""
        if not v.isdigit():
            raise ValueError("OTP must contain only numbers")
        if len(v) != 6:
            raise ValueError("OTP must be exactly 6 digits")
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("otp")
    def validate_otp_format(cls, v):
        """Validate OTP is 6 digits"""
        if not v.isdigit():
            raise ValueError("OTP must contain only numbers")
        if len(v) != 6:
            raise ValueError("OTP must be exactly 6 digits")
        return v

    @field_validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength"""
        result = validate_password_strength(v)

        if not result["is_valid"]:
            error_message = ". ".join(result["errors"])
            raise ValueError(error_message)

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

    @field_validator("phone_number")
    def validate_phone(cls, v):
        """Validate phone number jika diisi"""
        # Skip validation jika None atau empty string
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None  # Ubah empty string jadi None

        # Validasi hanya jika ada value
        if not validate_phone_number(v):
            raise ValueError(
                "Invalid phone number. Must start with 08 and be 10-15 digits long"
            )
        return v

    @field_validator(
        "full_name",
        "profession",
        "province_name",
        "city_name",
        "district_name",
        "village_name",
        "detailed_address",
        "assignment_location",
    )
    def validate_string_fields(cls, v):
        """Ubah empty string jadi None untuk semua string fields"""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator("date_of_birth", mode="before")
    def validate_dob(cls, v):
        """Validate date of birth jika diisi"""
        # Skip validation jika None atau empty string
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None

        # Jika sudah date object, validate
        if isinstance(v, date):
            result = validate_date_of_birth(v)
            if not result["is_valid"]:
                raise ValueError(result["error"])
            return v

        # Jika string, parse dulu
        if isinstance(v, str):
            try:
                parsed_date = datetime.strptime(v.strip(), "%Y-%m-%d").date()
                result = validate_date_of_birth(parsed_date)
                if not result["is_valid"]:
                    raise ValueError(result["error"])
                return parsed_date
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")

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
