from google.cloud import storage
from google.oauth2 import service_account
import os
import uuid
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GCSService:
    def __init__(self):
        """
        Initialize Google Cloud Storage service with smart credential detection.
        
        Authentication Strategy:
        1. Check if running in Cloud Run (via env var K_SERVICE)
        2. LOCAL DEV: If not Cloud Run and credentials file exists, load from JSON
        3. CLOUD RUN: Always use runtime service account (automatic)
        
        This prevents accidentally using JSON file in production.
        """
        try:
            # Detect if running in Cloud Run environment
            is_cloud_run = os.getenv('K_SERVICE') is not None
            
            if is_cloud_run:
                # Force production mode in Cloud Run
                logger.info("🚀 Detected Cloud Run environment - using runtime service account")
                self.client = storage.Client()
                logger.info("✅ GCS Service initialized with runtime credentials (CLOUD RUN MODE)")
                
            elif settings.GOOGLE_APPLICATION_CREDENTIALS:
                # Local development mode with credentials file
                logger.info(f"🔑 GCS: Using credentials file: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
                
                # Verify file exists
                if not os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                    raise FileNotFoundError(
                        f"GCS credentials file not found: {settings.GOOGLE_APPLICATION_CREDENTIALS}"
                    )
                
                # Load credentials from JSON file
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
                self.client = storage.Client(credentials=credentials)
                logger.info("✅ GCS Service initialized with JSON credentials (LOCAL MODE)")
                
            else:
                # Fallback: Try runtime service account (for other cloud environments)
                logger.info("🔧 No credentials file specified, using runtime service account")
                self.client = storage.Client()
                logger.info("✅ GCS Service initialized with runtime credentials (AUTO MODE)")
            
            # Initialize bucket
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
            
            # Verify bucket exists
            if not self.bucket.exists():
                raise ValueError(f"GCS bucket does not exist: {settings.GCS_BUCKET_NAME}")
            
            logger.info(f"✅ GCS bucket connected: {settings.GCS_BUCKET_NAME}")
            
        except FileNotFoundError as e:
            logger.error(f"❌ GCS initialization failed: {str(e)}")
            raise RuntimeError(f"GCS credentials file not found: {str(e)}")
            
        except ValueError as e:
            logger.error(f"❌ GCS initialization failed: {str(e)}")
            raise RuntimeError(f"GCS bucket error: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ GCS initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize GCS service: {str(e)}")
    
    def _generate_unique_filename(self, original_filename: Optional[str], folder: str = "") -> str:
        """Generate unique filename with UUID prefix"""
        file_extension = os.path.splitext(original_filename or "default.png")[1]
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{file_extension}"
        
        if folder:
            return f"{folder}/{filename}"
        return filename
    
    def _validate_image_file(self, file: UploadFile) -> bool:
        """Validate if uploaded file is an image"""
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        return file.content_type in allowed_types
    
    async def upload_profile_photo(self, file: UploadFile, user_id: int) -> Tuple[str, str]:
        """
        Upload profile photo to GCS
        Returns: (file_url, filename)
        """
        if not self._validate_image_file(file):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only images are allowed."
            )
        
        # Check file size (max 2MB)
        file_content = await file.read()
        if len(file_content) > 2 * 1024 * 1024:  # 2MB
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum size is 2MB."
            )
        
        try:
            # Generate unique filename in profile_photos folder
            filename = self._generate_unique_filename(file.filename, f"profile_photos/user_{user_id}")
            
            # Upload to GCS
            blob = self.bucket.blob(filename)
            blob.upload_from_string(
                file_content,
                content_type=file.content_type or "application/octet-stream"
            )
            
            # Make blob publicly accessible (if needed)
            # blob.make_public()
            
            # Return public URL and filename
            file_url = blob.public_url
            logger.info(f"✅ Profile photo uploaded: {filename}")
            
            return file_url, filename
            
        except Exception as e:
            logger.error(f"❌ Failed to upload profile photo: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload profile photo: {str(e)}"
            )
    
    async def upload_fundus_image(
        self, 
        file: UploadFile, 
        user_id: int, 
        patient_code: str
    ) -> Tuple[str, str]:
        """
        Upload fundus image to GCS
        Returns: (file_url, filename)
        """
        if not self._validate_image_file(file):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only images are allowed."
            )
        
        # Check file size (max 5MB for fundus images)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum size is 5MB."
            )
        
        try:
            # Generate unique filename in fundus_images folder
            folder = f"fundus_images/user_{user_id}/patient_{patient_code}"
            filename = self._generate_unique_filename(file.filename, folder)
            
            # Upload to GCS
            blob = self.bucket.blob(filename)
            blob.upload_from_string(
                file_content,
                content_type=file.content_type or "application/octet-stream"
            )
            
            # Make blob publicly accessible (if needed)
            # blob.make_public()
            
            # Return public URL and filename
            file_url = blob.public_url
            logger.info(f"✅ Fundus image uploaded: {filename}")
            
            return file_url, filename
            
        except Exception as e:
            logger.error(f"❌ Failed to upload fundus image: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload fundus image: {str(e)}"
            )
    
    def delete_file(self, filename: str) -> bool:
        """Delete file from GCS"""
        try:
            blob = self.bucket.blob(filename)
            if blob.exists():
                blob.delete()
                logger.info(f"✅ File deleted: {filename}")
                return True
            else:
                logger.warning(f"⚠️ File not found for deletion: {filename}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to delete file {filename}: {str(e)}")
            return False
    
    def get_file_url(self, filename: str) -> Optional[str]:
        """Get public URL for a file"""
        try:
            blob = self.bucket.blob(filename)
            if blob.exists():
                return blob.public_url
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get file URL for {filename}: {str(e)}")
            return None

# Create global GCS service instance
try:
    gcs_service = GCSService()
    logger.info("🎉 GCS Service initialization complete")
except RuntimeError as e:
    logger.critical(f"💥 CRITICAL: GCS Service failed to initialize: {str(e)}")
    logger.critical("⚠️ File upload/download functionality will NOT work!")
    gcs_service = None