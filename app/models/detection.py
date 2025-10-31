from __future__ import annotations
from sqlalchemy import String, Float, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .patient import Patient
    from .fundus_image import FundusImage

class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = {'schema': 'schema_retinophaty'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.patients.id"), nullable=False)
    fundus_image_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.fundus_images.id"), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.users.id"), nullable=False)
    
    classification: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_at_detection: Mapped[int] = mapped_column(Integer, nullable=False)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="detections")
    fundus_image: Mapped["FundusImage"] = relationship(back_populates="detection")
    user: Mapped["User"] = relationship(back_populates="detections")