from __future__ import annotations
from sqlalchemy import String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from typing import List, TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .fundus_image import FundusImage
    from .detection import Detection

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint('patient_code', 'created_by_user_id', name='uq_patient_code_user'),
        {'schema': 'schema_retinophaty'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator: Mapped["User"] = relationship(back_populates="patients")
    fundus_images: Mapped[List["FundusImage"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    detections: Mapped[List["Detection"]] = relationship(back_populates="patient", cascade="all, delete-orphan")