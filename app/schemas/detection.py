from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class DetectionStartRequest(BaseModel):
    patient_code: str = Field(..., min_length=1, max_length=50)
    side_eye: str = Field(..., pattern="^(Right|Left)$")

class DetectionStartResponse(BaseModel):
    patient_code: str
    patient_name: str
    patient_gender: str
    patient_age: int
    side_eye: str
    classification: int
    predicted_label: str
    confidence: float
    description: Optional[str] = None 
    detected_at: datetime
    image_url: str
    gcs_filename: str
    all_probabilities: Dict[str, float]

class DetectionSaveRequest(BaseModel):
    patient_code: str
    side_eye: str
    classification: int
    confidence: float
    description: Optional[str] = None
    detected_at: datetime
    image_url: str
    gcs_filename: str

class DetectionResponse(BaseModel):
    id: int
    patient_id: int
    patient_code: str
    patient_name: str
    patient_gender: str
    patient_age: int
    side_eye: str
    classification: int
    predicted_label: str
    confidence: float
    description: Optional[str] = None
    image_url: str
    detected_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionDetailResponse(BaseModel):
    id: int
    patient_code: str
    patient_name: str
    patient_gender: str
    patient_age: int
    side_eye: str
    classification: int
    predicted_label: str
    confidence: float
    description: Optional[str] = None
    image_url: str
    detected_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionPreviewData(BaseModel):
    patient_code: str
    patient_name: str
    patient_gender: str
    patient_age: int
    side_eye: str
    classification: int
    predicted_label: str
    confidence: float
    description: Optional[str] = None
    detected_at: datetime
    image_url: str
    all_probabilities: Dict[str, float]

class DetectionStartResponseNew(BaseModel):
    session_id: str
    message: str
    data: DetectionPreviewData

class DetectionSaveRequestNew(BaseModel):
    session_id: str = Field(..., min_length=1)

class ProgressChartDataPoint(BaseModel):
    date: datetime
    classification: int
    predicted_label: str
    confidence: float
    side_eye: str

class ProgressChartResponse(BaseModel):
    patient_code: str
    patient_name: str
    patient_gender: str
    patient_age: int
    total_detections: int
    data_points: list[ProgressChartDataPoint]

    class Config:
        from_attributes = True
