"""
Session Manager for Temporary Detection Storage
Handles temporary storage of detection results before user confirmation
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class DetectionSessionManager:
    """
    Manages temporary detection sessions in memory.
    
    For production: Replace this with Redis implementation
    with automatic TTL (Time To Live) of 15 minutes.
    """
    
    def __init__(self):
        # In-memory storage: {session_id: session_data}
        self._storage: Dict[str, dict] = {}
        logger.info("DetectionSessionManager initialized with in-memory storage")
    
    def create_session(
        self,
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
        Create a new detection session and return session_id
        
        Returns:
            session_id (str): Unique identifier for this session
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
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
            'detected_at': detected_at.isoformat(),
            'image_url': image_url,
            'gcs_filename': gcs_filename,
            'all_probabilities': all_probabilities,
            'created_at': datetime.now()
        }
        
        self._storage[session_id] = session_data
        
        logger.info(f"Created session {session_id} for user {user_id}, patient {patient_code}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session data by session_id
        
        Returns:
            dict or None: Session data if found, None otherwise
        """
        session_data = self._storage.get(session_id)
        
        if session_data:
            # Check if session expired (15 minutes)
            created_at = session_data['created_at']
            now = datetime.now()
            age_seconds = (now - created_at).total_seconds()
            
            if age_seconds > 900:  # 15 minutes = 900 seconds
                logger.warning(f"Session {session_id} expired (age: {age_seconds}s)")
                self.delete_session(session_id)
                return None
            
            logger.info(f"Retrieved session {session_id}")
            return session_data
        
        logger.warning(f"Session {session_id} not found")
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from storage
        
        Returns:
            bool: True if deleted, False if not found
        """
        if session_id in self._storage:
            del self._storage[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        
        logger.warning(f"Attempted to delete non-existent session {session_id}")
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions (older than 15 minutes)
        
        Returns:
            int: Number of sessions cleaned up
        """
        now = datetime.now()
        expired_keys = []
        
        for session_id, session_data in self._storage.items():
            created_at = session_data['created_at']
            age_seconds = (now - created_at).total_seconds()
            
            if age_seconds > 900:  # 15 minutes
                expired_keys.append(session_id)
        
        for key in expired_keys:
            del self._storage[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired sessions")
        
        return len(expired_keys)
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self._storage)


# Global instance
session_manager = DetectionSessionManager()