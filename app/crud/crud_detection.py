from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timedelta, date
from typing import Optional, List
from app.models.detection import Detection
from app.models.fundus_image import FundusImage
from app.models.patient import Patient

class DetectionCRUD:
    def __init__(self):
        pass

    def create_fundus_image(
        self,
        db: Session,
        patient_id: int,
        user_id: int,
        side_eye: str,
        image_url: str,
        gcs_filename: str
    ) -> FundusImage:
        """Create fundus image record"""
        db_image = FundusImage(
            patient_id=patient_id,
            user_id=user_id,
            side_eye=side_eye,
            image_url=image_url,
            gcs_filename=gcs_filename
        )
        
        db.add(db_image)
        db.flush()
        return db_image

    def create_detection(
        self,
        db: Session,
        patient_id: int,
        fundus_image_id: int,
        user_id: int,
        classification: int,
        confidence: float,
        description: Optional[str],
        detected_at: datetime,
        age_at_detection: int  # Tambahkan parameter ini
    ) -> Detection:
        """Create detection record"""
        db_detection = Detection(
            patient_id=patient_id,
            fundus_image_id=fundus_image_id,
            user_id=user_id,
            classification=classification,
            confidence=confidence,
            description=description,
            detected_at=detected_at,
            age_at_detection=age_at_detection # Tambahkan ini
        )
        
        db.add(db_detection)
        db.flush()
        return db_detection

    def get_detection_by_id_and_user(
        self,
        db: Session,
        detection_id: int,
        user_id: int
    ) -> Optional[Detection]:
        """Get detection by ID and user_id (data isolation)"""
        stmt = select(Detection).where(
            and_(
                Detection.id == detection_id,
                Detection.user_id == user_id
            )
        )
        return db.scalars(stmt).first()

    def get_detections_by_user(
        self,
        db: Session,
        user_id: int,
        classification: Optional[int] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        gender: Optional[str] = None,
        period: Optional[str] = None,
        patient_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Detection]:
        """Get detections with filters (data isolation)"""
        stmt = select(Detection).join(Patient).where(
            Detection.user_id == user_id
        )

        if classification is not None:
            stmt = stmt.where(Detection.classification == classification)
        if gender:
            stmt = stmt.where(Patient.gender == gender)
        if patient_code:
            stmt = stmt.where(Patient.patient_code == patient_code.upper())
        if age_min is not None or age_max is not None:
            today = date.today()
            if age_max is not None:
                min_birth_date = date(today.year - age_max - 1, today.month, today.day)
                stmt = stmt.where(Patient.date_of_birth >= min_birth_date)
            if age_min is not None:
                max_birth_date = date(today.year - age_min, today.month, today.day)
                stmt = stmt.where(Patient.date_of_birth <= max_birth_date)
        if period:
            now = datetime.now()
            start_date = None
            if period == "last_7_days":
                start_date = now - timedelta(days=7)
            elif period == "last_1_month":
                start_date = now - timedelta(days=30)
            elif period == "last_3_months":
                start_date = now - timedelta(days=90)
            elif period == "last_1_year":
                start_date = now - timedelta(days=365)
            if start_date:
                stmt = stmt.where(Detection.detected_at >= start_date)

        stmt = stmt.order_by(Detection.detected_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    # === FUNGSI INI DIPERBARUI ===
    def get_all_detections_for_patient(
        self,
        db: Session,
        patient_id: int,
        user_id: int  # ← TAMBAHKAN parameter ini
    ) -> List[Detection]:
        """Get ALL detections for a specific patient ID (with data isolation)."""
        stmt = select(Detection).where(
            and_(  # ← GUNAKAN and_
                Detection.patient_id == patient_id,
                Detection.user_id == user_id  # ← VALIDASI user_id
            )
        ).order_by(Detection.detected_at.asc())
        return list(db.scalars(stmt).all())

    def delete_detection(
        self,
        db: Session,
        detection: Detection
    ) -> bool:
        """Delete detection and associated fundus image"""
        try:
            stmt = select(FundusImage).where(FundusImage.id == detection.fundus_image_id)
            fundus_image = db.scalars(stmt).first()
            
            db.delete(detection)
            
            if fundus_image:
                db.delete(fundus_image)
            
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def count_detections_by_user(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """Count total detections for a user"""
        from sqlalchemy import func
        stmt = select(func.count(Detection.id)).where(Detection.user_id == user_id)
        return db.scalar(stmt) or 0

detection_crud = DetectionCRUD()