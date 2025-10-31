from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from app.models.token_blacklist import TokenBlacklist

class TokenCRUD:
    """CRUD operations untuk Token Blacklist"""
    
    def blacklist_token(self, db: Session, token: str, user_id: int, expires_at: datetime) -> TokenBlacklist:
        """
        Add token to blacklist
        
        Args:
            db: Database session
            token: JWT token yang akan di-blacklist
            user_id: ID user pemilik token
            expires_at: Waktu expire token
            
        Returns:
            TokenBlacklist object
        """
        try:
            # Cek apakah token sudah ada (prevent duplicate)
            existing = self.is_token_blacklisted(db, token)
            if existing:
                return existing
            
            blacklisted_token = TokenBlacklist(
                token=token,
                user_id=user_id,
                expires_at=expires_at
            )
            db.add(blacklisted_token)
            db.commit()
            db.refresh(blacklisted_token)
            return blacklisted_token
        except Exception as e:
            db.rollback()
            raise e

    def is_token_blacklisted(self, db: Session, token: str) -> Optional[TokenBlacklist]:
        """
        Check if token is blacklisted
        
        Args:
            db: Database session
            token: JWT token to check
            
        Returns:
            TokenBlacklist object if found, None otherwise
        """
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token
        ).first()

    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Remove expired tokens from blacklist
        
        Args:
            db: Database session
            
        Returns:
            Number of deleted tokens
        """
        try:
            # Delete semua token yang sudah expire
            deleted_count = db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at < datetime.now(timezone.utc)
            ).delete(synchronize_session=False)
            
            db.commit()
            return deleted_count
        except Exception as e:
            db.rollback()
            raise e
    
    def get_user_blacklisted_tokens(self, db: Session, user_id: int) -> list[TokenBlacklist]:
        """
        Get all blacklisted tokens for a specific user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of TokenBlacklist objects
        """
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.user_id == user_id
        ).all()
    
    def revoke_all_user_tokens(self, db: Session, user_id: int, expires_at: datetime) -> Optional[int]:
        """
        Blacklist all active tokens for a user (untuk logout from all devices)
        
        Args:
            db: Database session
            user_id: User ID
            expires_at: Token expiry time
            
        Returns:
            Number of tokens revoked
        """
        # Note: Ini hanya placeholder. Untuk implementasi full,
        # perlu tracking semua active tokens per user
        pass

# Global instance
token_crud = TokenCRUD()