from pydantic import BaseModel


class BreakdownBySeverity(BaseModel):
    """Breakdown deteksi berdasarkan tingkat keparahan DR"""
    no_dr: int = 0
    mild: int = 0      
    moderate: int = 0
    severe: int = 0
    proliferative: int = 0


class DashboardStatsResponse(BaseModel):
    """Response model untuk dashboard statistics"""
    total_patients: int
    total_detections: int
    detections_today: int
    breakdown: BreakdownBySeverity

    class Config:
        from_attributes = True