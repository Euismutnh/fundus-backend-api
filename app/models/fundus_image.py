from __future__ import annotations
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .patient import Patient
    from .detection import Detection

class FundusImage(Base):
    __tablename__ = "fundus_images"
    __table_args__ = {'schema': 'schema_retinophaty'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.patients.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("schema_retinophaty.users.id"), nullable=False)
    side_eye: Mapped[str] = mapped_column(String(10), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    gcs_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="fundus_images")
    user: Mapped["User"] = relationship(back_populates="fundus_images")
    detection: Mapped[Optional["Detection"]] = relationship(back_populates="fundus_image", uselist=False)