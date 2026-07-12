from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.detection import (
    # New schemas
    DetectionStartResponseNew,
    DetectionSaveRequestNew,
    DetectionPreviewData,
    # Existing schemas
    DetectionResponse,
    DetectionDetailResponse,
    ProgressChartResponse,
    ProgressChartDataPoint
)
from app.schemas.user_schema import MessageResponse
from app.crud.crud_patient import patient_crud
from app.crud.crud_detection import detection_crud
from app.core.gcs_service import gcs_service
from app.core.ai_service import ai_service
from app.core.utils import calculate_age
from app.core.session_manager import session_manager

router = APIRouter(prefix="/detections", tags=["Detections"])


# ========================================================================
# ENDPOINT 1: START DETECTION (PREVIEW ONLY - NO SAVE TO DATABASE)
# ========================================================================

@router.post("/start", response_model=DetectionStartResponseNew)
async def start_detection(
    patient_code: str = Form(...),
    side_eye: str = Form(..., pattern="^(Right|Left)$"),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start DR detection and return temporary result for preview (FR-03.1 - Step 1)
    
    **Workflow:**
    1. Validate patient exists and belongs to current user
    2. Upload image to GCS (temporary storage)
    3. Run AI prediction
    4. Store result in temporary session storage
    5. Return session_id + preview data
    
    **Important:** 
    - This does NOT save to database yet
    - User must call POST /detections/save to persist data
    - Session expires after 15 minutes
    - User can cancel by calling DELETE /detections/cancel/{session_id}
    
    **Activity Diagram Reference:**
    - User: "Mengunggah citra fundus"
    - System: "Memproses Citra" → "Mengirim ke model AI"
    - System: "Menampilkan Hasil Deteksi"
    """
    
    # 1. Validate patient exists and belongs to current user (data isolation)
    patient = patient_crud.get_patient_by_code_and_user(db, patient_code, current_user.id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or you don't have permission to access this patient"
        )

    # 2. Upload image to GCS (temporary storage)
    try:
        image_url, gcs_filename = await gcs_service.upload_fundus_image(
            image, current_user.id, patient_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

    # 3. Run AI prediction
    try:
        classification, predicted_label, confidence, all_probabilities = await ai_service.predict_dr(image)
    except Exception as e:
        # Cleanup: Delete uploaded image if prediction fails
        gcs_service.delete_file(gcs_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI prediction failed: {str(e)}"
        )

    # 4. Prepare detection data
    description = ai_service.get_description(classification)
    patient_age = calculate_age(patient.date_of_birth)
    detected_at = datetime.now()

    # 5. Create session and store temporarily
    session_id = session_manager.create_session(
        db=db,
        user_id=current_user.id,
        patient_id=patient.id,
        patient_code=patient.patient_code,
        patient_name=patient.name,
        patient_gender=patient.gender,
        patient_age=patient_age,
        side_eye=side_eye,
        classification=classification,
        predicted_label=predicted_label,
        confidence=confidence,
        description=description,
        detected_at=detected_at,
        image_url=image_url,
        gcs_filename=gcs_filename,
        all_probabilities=all_probabilities
    )

    # 6. Return response with session_id
    preview_data = DetectionPreviewData(
        patient_code=patient.patient_code,
        patient_name=patient.name,
        patient_gender=patient.gender,
        patient_age=patient_age,
        side_eye=side_eye,
        classification=classification,
        predicted_label=predicted_label,
        confidence=confidence,
        description=description,
        detected_at=detected_at,
        image_url=image_url,
        all_probabilities=all_probabilities
    )

    return DetectionStartResponseNew(
        session_id=session_id,
        message="Detection completed successfully. Please review the result and decide to Save, Retry, or Cancel.",
        data=preview_data
    )


# ========================================================================
# ENDPOINT 2: SAVE DETECTION (AFTER USER CONFIRMATION)
# ========================================================================

@router.post("/save", response_model=MessageResponse)
async def save_detection(
    request: DetectionSaveRequestNew,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save detection result to database after user confirmation (FR-03.1 - Step 2)
    
    **Workflow:**
    1. Retrieve temporary session data using session_id
    2. Validate session exists and belongs to current user
    3. Validate patient still exists
    4. Save to database permanently (fundus_image + detection)
    5. Cleanup temporary session
    
    **Important:**
    - User must call POST /detections/start first to get session_id
    - Session must not be expired (15 minutes limit)
    - This is called when user presses "Save" button in the app
    
    **Activity Diagram Reference:**
    - User: "Memilih keputusan" → [Save]
    - System: "Menyimpan hasil ke database"
    """
    
    session_id = request.session_id
    
    # 1. Retrieve session data
    session_data = session_manager.get_session(db, session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired. Please start detection again."
        )
    
    # 2. Validate ownership (security check)
    if session_data['user_id'] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to save this detection"
        )
    
    # 3. Validate patient still exists (edge case: patient deleted between start and save)
    patient = patient_crud.get_patient_by_id_and_user(
        db, session_data['patient_id'], current_user.id
    )
    if not patient:
        # Cleanup: Delete image and session
        gcs_service.delete_file(session_data['gcs_filename'])
        session_manager.delete_session(db, session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found. It may have been deleted."
        )

    # 4. Save to database permanently
    try:
        # Save fundus image record
        fundus_image = detection_crud.create_fundus_image(
            db=db,
            patient_id=session_data['patient_id'],
            user_id=current_user.id,
            side_eye=session_data['side_eye'],
            image_url=session_data['image_url'],
            gcs_filename=session_data['gcs_filename']
        )
        
        # Save detection record
        detection = detection_crud.create_detection(
            db=db,
            patient_id=session_data['patient_id'],
            fundus_image_id=fundus_image.id,
            user_id=current_user.id,
            classification=session_data['classification'],
            confidence=session_data['confidence'],
            description=session_data['description'],
            detected_at=datetime.fromisoformat(session_data['detected_at']),
            age_at_detection=session_data['patient_age']
        )
        
        db.commit()
        
        # 5. Cleanup: Remove session from temporary storage
        session_manager.delete_session(db, session_id)
        
        return MessageResponse(
            message="Detection saved successfully!",
            success=True
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save detection: {str(e)}"
        )


# ========================================================================
# ENDPOINT 3: CANCEL DETECTION (USER CANCELS BEFORE SAVE)
# ========================================================================

@router.delete("/cancel/{session_id}", response_model=MessageResponse)
async def cancel_detection(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel detection and cleanup temporary data
    
    **Workflow:**
    1. Retrieve session data
    2. Validate ownership
    3. Delete image from GCS
    4. Remove session from temporary storage
    
    **Important:**
    - This is called when user presses "Cancel" button in the app
    - All temporary data will be deleted
    
    **Activity Diagram Reference:**
    - User: "Memilih keputusan" → [Cancel]
    - System: Cleanup temporary data
    """
    
    # 1. Retrieve session data
    session_data = session_manager.get_session(db, session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already expired"
        )
    
    # 2. Validate ownership
    if session_data['user_id'] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this detection"
        )
    
    # 3. Cleanup: Delete image from GCS
    try:
        gcs_service.delete_file(session_data['gcs_filename'])
    except Exception as e:
        # Log error but don't fail the request
        print(f"Warning: Failed to delete file {session_data['gcs_filename']}: {str(e)}")
    
    # 4. Remove session from temporary storage
    session_manager.delete_session(db, session_id)
    
    return MessageResponse(
        message="Detection cancelled successfully",
        success=True
    )


# ========================================================================
# ENDPOINT 4-7: EXISTING ENDPOINTS (NO CHANGES)
# ========================================================================

@router.get("/", response_model=List[DetectionResponse])
async def get_detections(
    classification: Optional[int] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    gender: Optional[str] = None,
    period: Optional[str] = None,
    patient_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detection history with filters (FR-04.1)"""
    detections = detection_crud.get_detections_by_user(
        db=db, user_id=current_user.id, classification=classification, age_min=age_min,
        age_max=age_max, gender=gender, period=period, patient_code=patient_code,
        skip=skip, limit=limit
    )
    
    response_list = []
    for detection in detections:
        predicted_label = ai_service.get_label(detection.classification)
        response_list.append(DetectionResponse(
            id=detection.id,
            patient_id=detection.patient_id,
            patient_code=detection.patient.patient_code,
            patient_name=detection.patient.name,
            patient_gender=detection.patient.gender,
            patient_age=detection.age_at_detection,
            side_eye=detection.fundus_image.side_eye,
            classification=detection.classification,
            predicted_label=predicted_label,
            confidence=detection.confidence,
            description=detection.description,
            image_url=detection.fundus_image.image_url,
            detected_at=detection.detected_at,
            created_at=detection.created_at
        ))
    return response_list


@router.get("/{detection_id}", response_model=DetectionDetailResponse)
async def get_detection_detail(
    detection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detection detail by ID (FR-05.2)"""
    detection = detection_crud.get_detection_by_id_and_user(db, detection_id, current_user.id)
    if not detection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")
    
    predicted_label = ai_service.get_label(detection.classification)
    
    return DetectionDetailResponse(
        id=detection.id,
        patient_code=detection.patient.patient_code,
        patient_name=detection.patient.name,
        patient_gender=detection.patient.gender,
        patient_age=detection.age_at_detection,
        side_eye=detection.fundus_image.side_eye,
        classification=detection.classification,
        predicted_label=predicted_label,
        confidence=detection.confidence,
        description=detection.description,
        image_url=detection.fundus_image.image_url,
        detected_at=detection.detected_at,
        created_at=detection.created_at
    )


@router.delete("/{detection_id}", response_model=MessageResponse)
async def delete_detection(
    detection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete detection by ID (FR-05.3)"""
    detection = detection_crud.get_detection_by_id_and_user(db, detection_id, current_user.id)
    if not detection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")
    
    gcs_filename = detection.fundus_image.gcs_filename
    success = detection_crud.delete_detection(db, detection)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete detection"
        )
    
    gcs_service.delete_file(gcs_filename)
    return MessageResponse(message="Detection deleted successfully", success=True)


@router.get("/patients/{patient_id}/progress-chart", response_model=ProgressChartResponse)
async def get_patient_progress_chart(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get patient progress chart data (FR-05.4)"""
    patient = patient_crud.get_patient_by_id_and_user(db, patient_id, current_user.id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # PERBAIKAN: Tambahkan user_id untuk data isolation
    detections = detection_crud.get_all_detections_for_patient(db, patient_id, current_user.id)
    
    data_points = []
    for detection in detections:
        predicted_label = ai_service.get_label(detection.classification)
        data_points.append(ProgressChartDataPoint(
            date=detection.detected_at,
            classification=detection.classification,
            predicted_label=predicted_label,
            confidence=detection.confidence,
            side_eye=detection.fundus_image.side_eye
        ))
    
    return ProgressChartResponse(
        patient_code=patient.patient_code,
        patient_name=patient.name,
        patient_gender=patient.gender,
        patient_age=calculate_age(patient.date_of_birth),
        total_detections=len(data_points),
        data_points=data_points
    )