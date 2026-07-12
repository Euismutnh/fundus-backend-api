"""
Session Manager for Temporary Detection Storage (DB-backed)
Handles temporary storage of detection results before user confirmation.
Safe for Gunicorn multi-worker and Cloud Run.
"""

import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.detection_sessions import DetectionSession

logger = logging.getLogger(__name__)

SESSION_TTL_MINUTES = 15

class DetectionSessionManager:
    """
    Manages temporary detection sessions in PostgreSQL Database using SQLAlchemy.
    Replaces the old in-memory dictionary to fix multi-worker bugs.
    """
    
    def __init__(self):
        logger.info("DetectionSessionManager initialized with ORM storage")

    def create_session(
        self,
        db: Session,
        user_id: int,
        patient_id: int,
        patient_code: str,
        patient_name: str,
        patient_gender: str,
        patient_age: int,
        side_eye: str,
        classification: int,
        predicted_label: str,
        confidence: float,
        description: str,
        detected_at: datetime,
        image_url: str,
        gcs_filename: str,
        all_probabilities: Dict[str, float]
    ) -> str:
        """
        Create a new detection session in the database and return session_id.
        """
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Susun payload data deteksi persis seperti format dictionary yang lama
        payload = {
            'user_id': user_id,
            'patient_id': patient_id,
            'patient_code': patient_code,
            'patient_name': patient_name,
            'patient_gender': patient_gender,
            'patient_age': patient_age,
            'side_eye': side_eye,
            'classification': classification,
            'predicted_label': predicted_label,
            'confidence': confidence,
            'description': description,
            'detected_at': detected_at.isoformat() if isinstance(detected_at, datetime) else detected_at,
            'image_url': image_url,
            'gcs_filename': gcs_filename,
            'all_probabilities': all_probabilities,
            'created_at': now.isoformat()
        }

        # Simpan ke PostgreSQL menggunakan model ORM
        new_session = DetectionSession(
            session_id=session_id,
            user_id=user_id,
            payload=payload,
            expires_at=now + timedelta(minutes=SESSION_TTL_MINUTES)
        )
        
        db.add(new_session)
        db.commit()
        
        logger.info(f"Created DB session {session_id} for user {user_id}, patient {patient_code}")
        return str(session_id)

    def get_session(self, db: Session, session_id: str) -> Optional[dict]:
        """
        Retrieve session data from database by session_id using ORM.
        """
        # Cari data yang ID-nya cocok dan belum expired
        session_obj = db.query(DetectionSession).filter(
            DetectionSession.session_id == session_id,
            DetectionSession.expires_at > func.now()
        ).first()

        if not session_obj:
            logger.warning(f"Session {session_id} not found or expired in DB")
            return None

        # Kembalikan payload-nya
        data = dict(session_obj.payload)
        
        # Pastikan user_id juga ada di dalam dictionary agar aman saat diakses
        if 'user_id' not in data:
            data['user_id'] = session_obj.user_id 
            
        logger.info(f"Retrieved session {session_id} from DB")
        return data

    def delete_session(self, db: Session, session_id: str) -> bool:
        """
        Delete a session from database.
        """
        session_obj = db.query(DetectionSession).filter(
            DetectionSession.session_id == session_id
        ).first()
        
        if session_obj:
            db.delete(session_obj)
            db.commit()
            logger.info(f"Deleted session {session_id} from DB")
            return True
            
        logger.warning(f"Attempted to delete non-existent session {session_id}")
        return False

    def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Remove all expired sessions from database.
        """
        deleted_count = db.query(DetectionSession).filter(
            DetectionSession.expires_at <= func.now()
        ).delete(synchronize_session=False)
        
        db.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired DB sessions")
            
        return deleted_count

    def get_session_count(self, db: Session) -> int:
        """
        Get total number of active (non-expired) sessions from the database.
        """
        count = db.query(DetectionSession).filter(
            DetectionSession.expires_at > func.now()
        ).count()
        
        return count

# Global instance
session_manager = DetectionSessionManager()