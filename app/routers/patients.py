from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.patient import (
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    PatientWithAgeResponse
)
from app.schemas.user_schema import MessageResponse
from app.crud.crud_patient import patient_crud

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new patient (FR-02.1)"""
    # Check if patient code already exists for this user
    if patient_crud.is_patient_code_exists(db, patient_data.patient_code, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with code '{patient_data.patient_code}' already exists"
        )
    
    # Create patient
    patient = patient_crud.create_patient(db, patient_data, current_user.id)
    db.commit()
    db.refresh(patient)
    
    return patient

@router.get("/{patient_code}", response_model=PatientWithAgeResponse)
async def get_patient_by_code(
    patient_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get patient by patient code (FR-02.1)"""
    patient = patient_crud.get_patient_by_code_and_user(db, patient_code, current_user.id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Calculate age
    age = patient_crud.calculate_age(patient.date_of_birth)
    
    # Convert to response with age
    patient_dict = {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "name": patient.name,
        "gender": patient.gender,
        "date_of_birth": patient.date_of_birth,
        "age": age,
        "created_by_user_id": patient.created_by_user_id,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at
    }
    
    return patient_dict

@router.get("/", response_model=List[PatientWithAgeResponse])
async def get_all_patients(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all patients for current user"""
    patients = patient_crud.get_patients_by_user(db, current_user.id, skip, limit)
    
    # Add age to each patient
    patients_with_age = []
    for patient in patients:
        age = patient_crud.calculate_age(patient.date_of_birth)
        patient_dict = {
            "id": patient.id,
            "patient_code": patient.patient_code,
            "name": patient.name,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth,
            "age": age,
            "created_by_user_id": patient.created_by_user_id,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at
        }
        patients_with_age.append(patient_dict)
    
    return patients_with_age

@router.put("/{patient_code}", response_model=PatientResponse)
async def update_patient(
    patient_code: str,
    patient_data: PatientUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update patient information"""
    patient = patient_crud.get_patient_by_code_and_user(db, patient_code, current_user.id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    updated_patient = patient_crud.update_patient(db, patient, patient_data)
    
    return updated_patient

@router.delete("/{patient_code}", response_model=MessageResponse)
async def delete_patient(
    patient_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete patient and all related records"""
    patient = patient_crud.get_patient_by_code_and_user(db, patient_code, current_user.id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    success = patient_crud.delete_patient(db, patient)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete patient"
        )
    
    return MessageResponse(message="Patient deleted successfully", success=True)
