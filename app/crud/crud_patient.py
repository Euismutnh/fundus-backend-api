from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import date, datetime
from typing import Optional, List
from app.models.patient import Patient
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest

class PatientCRUD:
    def __init__(self):
        pass

    def get_patient_by_code_and_user(
        self, 
        db: Session, 
        patient_code: str, 
        user_id: int
    ) -> Optional[Patient]:
        """Get patient by patient_code and user_id (data isolation)"""
        stmt = select(Patient).where(
            and_(
                Patient.patient_code == patient_code.upper(),
                Patient.created_by_user_id == user_id
            )
        )
        return db.scalars(stmt).first()

    def get_patient_by_id_and_user(
        self, 
        db: Session, 
        patient_id: int, 
        user_id: int
    ) -> Optional[Patient]:
        """Get patient by ID and user_id (data isolation)"""
        stmt = select(Patient).where(
            and_(
                Patient.id == patient_id,
                Patient.created_by_user_id == user_id
            )
        )
        return db.scalars(stmt).first()

    def get_patients_by_user(
        self, 
        db: Session, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Patient]:
        """Get all patients for a specific user"""
        stmt = select(Patient).where(
            Patient.created_by_user_id == user_id
        ).order_by(Patient.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create_patient(
        self, 
        db: Session, 
        patient_data: PatientCreateRequest, 
        user_id: int
    ) -> Patient:
        """Create new patient"""
        db_patient = Patient(
            patient_code=patient_data.patient_code.upper(),
            name=patient_data.name,
            gender=patient_data.gender,
            date_of_birth=patient_data.date_of_birth,
            created_by_user_id=user_id
        )
        
        db.add(db_patient)
        db.flush()
        return db_patient

    def update_patient(
        self, 
        db: Session, 
        patient: Patient, 
        patient_data: PatientUpdateRequest
    ) -> Patient:
        """Update patient information"""
        update_data = patient_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(patient, field) and value is not None:
                setattr(patient, field, value)
        
        db.commit()
        db.refresh(patient)
        return patient

    def delete_patient(self, db: Session, patient: Patient) -> bool:
        """Delete patient (cascade will delete related records)"""
        try:
            db.delete(patient)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def is_patient_code_exists(
        self, 
        db: Session, 
        patient_code: str, 
        user_id: int
    ) -> bool:
        """Check if patient code already exists for this user"""
        stmt = select(Patient).where(
            and_(
                Patient.patient_code == patient_code.upper(),
                Patient.created_by_user_id == user_id
            )
        )
        return db.scalars(stmt).first() is not None

    def calculate_age(self, date_of_birth: date) -> int:
        """Calculate age from date of birth"""
        today = date.today()
        age = today.year - date_of_birth.year
        
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        return age

# Create global CRUD instance
patient_crud = PatientCRUD()
