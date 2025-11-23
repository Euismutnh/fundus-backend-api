from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import DashboardStatsResponse, BreakdownBySeverity
from app.crud.crud_patient import patient_crud
from app.crud.crud_detection import detection_crud

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for current user
    
    **Returns:**
    - total_patients: Total number of patients created by user
    - total_detections: Total number of detections performed by user
    - detections_today: Number of detections made today (since 00:00)
    - breakdown: Count of detections grouped by classification (0-4)
    """
    
    # Count total patients
    total_patients = patient_crud.count_patients_by_user(db, current_user.id)
    
    # Count total detections
    total_detections = detection_crud.count_detections_by_user(db, current_user.id)
    
    # Count detections today
    detections_today = detection_crud.count_detections_today(db, current_user.id)
    
    # Get breakdown by classification
    breakdown_dict = detection_crud.get_breakdown_by_classification(db, current_user.id)
    
    # Map to response model
    breakdown = BreakdownBySeverity(
        no_dr=breakdown_dict[0],
        mild=breakdown_dict[1],
        moderate=breakdown_dict[2],
        severe=breakdown_dict[3],
        proliferative=breakdown_dict[4]
    )
    
    return DashboardStatsResponse(
        total_patients=total_patients,
        total_detections=total_detections,
        detections_today=detections_today,
        breakdown=breakdown
    )