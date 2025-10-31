from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import DateTime, Date, String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from .patient import Patient
    from .fundus_image import FundusImage
    from .detection import Detection

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'schema_retinophaty'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Address fields
    province_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detailed_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment_location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Authentication fields
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # OTP fields
    otp: Mapped[str | None] = mapped_column(String(6), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patients: Mapped[List["Patient"]] = relationship(back_populates="creator")
    fundus_images: Mapped[List["FundusImage"]] = relationship(back_populates="user")
    detections: Mapped[List["Detection"]] = relationship(back_populates="user")