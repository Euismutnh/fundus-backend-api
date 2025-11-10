from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional

# Import validator dari utils
from app.core.utils import (
    validate_patient_code,
    validate_date_of_birth
)


class PatientCreateRequest(BaseModel):
    patient_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    gender: str = Field(..., pattern="^(Male|Female)$")
    date_of_birth: date

    @field_validator('patient_code')
    def validate_code(cls, v):
        """Validate patient code format"""
        if not validate_patient_code(v):
            raise ValueError('Patient code cannot be empty and must not exceed 50 characters')
        return v.strip().upper()  # Auto-convert to uppercase
    
    @field_validator('name')
    def validate_name(cls, v):
        """Validate patient name"""
        if not v or not v.strip():
            raise ValueError('Patient name cannot be empty')
        return v.strip()
    
    
    @field_validator('date_of_birth')
    def validate_dob(cls, v):
        """Validate date of birth"""
        result = validate_date_of_birth(v)
        if not result['is_valid']:
            raise ValueError(result['error'])
        return v


class PatientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    gender: Optional[str] = Field(None, pattern="^(Male|Female)$")
    date_of_birth: Optional[date] = None

    @field_validator('name')
    def validate_name(cls, v):
        """Validate patient name jika diisi"""
        if v is None:
            return v
        
        if not v.strip():
            raise ValueError('Patient name cannot be empty')
        return v.strip()
    
    
    @field_validator('date_of_birth')
    def validate_dob(cls, v):
        """Validate date of birth jika diisi"""
        if v is None:
            return v
        
        result = validate_date_of_birth(v)
        if not result['is_valid']:
            raise ValueError(result['error'])
        return v


class PatientResponse(BaseModel):
    id: int
    patient_code: str
    name: str
    gender: str
    date_of_birth: date
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientWithAgeResponse(BaseModel):
    id: int
    patient_code: str
    name: str
    gender: str
    date_of_birth: date
    age: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True