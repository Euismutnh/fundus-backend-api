from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional

class PatientCreateRequest(BaseModel):
    patient_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    gender: str = Field(..., pattern="^(Male|Female)$")
    date_of_birth: date

    @field_validator('patient_code')
    def validate_patient_code(cls, v):
        if not v.strip():
            raise ValueError('Patient code cannot be empty')
        return v.strip().upper()

class PatientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    gender: Optional[str] = Field(None, pattern="^(Male|Female)$")
    date_of_birth: Optional[date] = None

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
