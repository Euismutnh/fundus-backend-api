from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func # ✅ Tambahkan func
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict # ✅ Tambahkan Dict
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
        age_at_detection: int
    ) -> Detection:
        db_detection = Detection(
            patient_id=patient_id,
            fundus_image_id=fundus_image_id,
            user_id=user_id,
            classification=classification,
            confidence=confidence,
            description=description,
            detected_at=detected_at,
            age_at_detection=age_at_detection
        )
        db.add(db_detection)
        db.flush()
        return db_detection

    def get_detection_by_id_and_user(
        self, db: Session, detection_id: int, user_id: int
    ) -> Optional[Detection]:
        stmt = select(Detection).where(
            and_(Detection.id == detection_id, Detection.user_id == user_id)
        )
        return db.scalars(stmt).first()

    def get_detections_by_user(
        self, db: Session, user_id: int, classification: Optional[int] = None,
        age_min: Optional[int] = None, age_max: Optional[int] = None,
        gender: Optional[str] = None, period: Optional[str] = None,
        patient_code: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Detection]:
        stmt = select(Detection).join(Patient).where(Detection.user_id == user_id)

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

    def get_all_detections_for_patient(
        self, db: Session, patient_id: int, user_id: int
    ) -> List[Detection]:
        stmt = select(Detection).where(
            and_(Detection.patient_id == patient_id, Detection.user_id == user_id)
        ).order_by(Detection.detected_at.asc())
        return list(db.scalars(stmt).all())

    def delete_detection(self, db: Session, detection: Detection) -> bool:
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

    def count_detections_by_user(self, db: Session, user_id: int) -> int:
        """Count total detections for a user"""
        stmt = select(func.count(Detection.id)).where(Detection.user_id == user_id)
        return db.scalar(stmt) or 0
    
    def count_detections_today(self, db: Session, user_id: int) -> int:
        """Count detections made today (since 00:00)"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.count(Detection.id)).where(
            and_(
                Detection.user_id == user_id,
                Detection.detected_at >= today_start
            )
        )
        return db.scalar(stmt) or 0

    def get_breakdown_by_classification(self, db: Session, user_id: int) -> dict:
        """Get breakdown of detections by classification (0-4)"""
        stmt = select(
            Detection.classification,
            func.count(Detection.id).label('count')
        ).where(
            Detection.user_id == user_id
        ).group_by(Detection.classification)
        
        results = db.execute(stmt).all()
        
        breakdown = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        
        for classification, count in results:
            if classification in breakdown:
                breakdown[classification] = count
        
        return breakdown

# Global instance
detection_crud = DetectionCRUD()