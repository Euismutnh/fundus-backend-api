from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

class TokenBlacklist(Base):
    """
    Model untuk menyimpan token yang sudah di-logout (blacklisted).
    Token yang ada di sini tidak bisa digunakan lagi untuk akses endpoint protected.
    """
    __tablename__ = "token_blacklist"
    __table_args__ = {'schema': 'schema_retinophaty'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('schema_retinophaty.users.id', ondelete='CASCADE'), nullable=False)
    blacklisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"