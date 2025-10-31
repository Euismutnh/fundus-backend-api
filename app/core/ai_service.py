import httpx
import logging
from typing import Dict, Tuple
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ai_endpoint = "https://fundus-api-service-165772118694.asia-southeast2.run.app/predict"
        self.timeout = 60.0  # 60 seconds timeout for AI processing
        
        # DR classification mapping
        self.classification_labels = {
            0: "No DR",
            1: "Mild NPDR",
            2: "Moderate NPDR",
            3: "Severe NPDR",
            4: "PDR"
        }
        
        # DR descriptions in Indonesian
        self.classification_descriptions = {
            0: (
                "Tidak terdeteksi kelainan (No Disease Visible). "
                "Tidak ditemukan abnormalitas pada pemeriksaan citra fundus mata."
            ),
            1: (
                "Retinopati Diabetik Non-Proliferatif Ringan (Mild Non-Proliferative Diabetic Retinopathy). "
                "Terdeteksi pembengkakan lokal pada pembuluh darah kecil di retina (mikroaneurisma)."
            ),
            2: (
                "Retinopati Diabetik Non-Proliferatif Sedang (Moderate Non-Proliferative Diabetic Retinopathy). "
                "Terdeteksi Mild NPDR disertai perdarahan kecil berupa dot hemorrhages dan blot hemorrhages, "
                "kebocoran berupa hard exudates, atau penutupan pembuluh darah kecil yang menghasilkan cotton wool spots."
            ),
            3: (
                "Retinopati Diabetik Non-Proliferatif Berat (Severe Non-Proliferative Diabetic Retinopathy). "
                "Terdeteksi Moderate NPDR disertai kerusakan lebih lanjut pada pembuluh darah berupa "
                "perdarahan intraretinal, venous beading (pembengkakan vena tidak teratur), "
                "dan abnormalitas mikrovaskular intraretinal."
            ),
            4: (
                "Retinopati Diabetik Proliferatif (Proliferative Diabetic Retinopathy). "
                "Terdeteksi Severe NPDR disertai pembentukan pembuluh darah baru (neovaskularisasi) "
                "atau perdarahan ke dalam vitreous/preretinal."
            )
        }
    
    async def predict_dr(self, image_file: UploadFile) -> Tuple[int, str, float, Dict[str, float]]:
        """
        Call AI service to predict DR classification
        Returns: (classification, predicted_label, confidence, all_probabilities)
        """
        try:
            # Reset file pointer to beginning
            await image_file.seek(0)
            
            # Prepare multipart form data
            files = {
                "file": (image_file.filename, await image_file.read(), image_file.content_type)
            }
            
            # Call AI service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.ai_endpoint,
                    files=files,
                    headers={"accept": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"AI service returned status {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail="AI service failed to process the image"
                    )
                
                result = response.json()
                
                # Extract data from AI response
                classification = result.get("predicted_class")
                predicted_label = result.get("predicted_label")
                confidence_str = result.get("confidence")
                all_probabilities = result.get("all_probabilities", {})
                
                if classification is None or predicted_label is None or confidence_str is None:
                    logger.error(f"Invalid AI response format: {result}")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid response from AI service"
                    )
                
                try:
                    confidence = float(confidence_str)
                except (ValueError, TypeError):
                    logger.error(f"Could not convert confidence to float: {confidence_str}")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid confidence value from AI service"
                    )
                
                logger.info(f"AI prediction successful: {predicted_label} ({confidence:.4f})")
                
                return classification, predicted_label, confidence, all_probabilities
                
        except httpx.TimeoutException:
            logger.error("AI service request timed out")
            raise HTTPException(
                status_code=504,
                detail="AI service request timed out. Please try again."
            )
        except httpx.RequestError as e:
            logger.error(f"AI service request failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="AI service is currently unavailable. Please try again later."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI prediction: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during AI prediction"
            )
    
    def get_description(self, classification: int) -> str:
        """Get description for DR classification"""
        return self.classification_descriptions.get(classification, "Deskripsi tidak tersedia.")
    
    def get_label(self, classification: int) -> str:
        """Get label for DR classification"""
        return self.classification_labels.get(classification, "Unknown")

# Create global AI service instance
ai_service = AIService()
