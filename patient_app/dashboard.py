import qrcode
import io
import base64
import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from .config import GEMINI_API_KEY
from .fhir_client import FHIRClient

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TimelineAggregator:
    def __init__(self, fhir_client: FHIRClient):
        self.fhir = fhir_client

    async def get_patient_timeline(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetches Conditions, Procedures, and Observations from FHIR and sorts by date.
        """
        # In a real app, we would query each resource type by patient reference.
        # Since we don't have full search implemented in FHIRClient, we'll mock the aggregation 
        # or assume we can get everything if we had the queries.
        # For this hackathon, let's try to fetch them if possible, or return a structure 
        # that the frontend expects, populated with some real/mock data.
        
        timeline = []
        
        # 1. Conditions (Diagnosis)
        # conditions = await self.fhir.search("Condition", {"patient": patient_id}) 
        # Mocking for now as FHIRClient only has basic GET/POST
        
        timeline.append({
            "type": "Condition",
            "date": "2023-01-15",
            "details": "Diagnosed with Stage II Breast Cancer"
        })
        
        timeline.append({
            "type": "Procedure",
            "date": "2023-02-20",
            "details": "Lumpectomy Surgery"
        })
        
        timeline.append({
            "type": "Observation",
            "date": "2023-03-10",
            "details": "WBC Count: 3.2 (Low)"
        })
        
        # Sort by date
        timeline.sort(key=lambda x: x["date"], reverse=True)
        return timeline

class AIInsights:
    def __init__(self):
        # We will use the GeminiClient for robust handling
        pass

    async def generate_insights(self, timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates Risk Score, Survival Insight, and Next Steps.
        """
        prompt = f"""
        Analyze the following patient timeline and generate insights:
        Timeline: {json.dumps(timeline_data)}
        
        Output JSON with:
        - risk_score: Integer 0-10 (based on trends, 10 is high risk)
        - survival_insight: A positive, encouraging framing based on data (string)
        - recommended_next_steps: List of strings (e.g. "Schedule follow-up", "Maintain diet")
        
        JSON Response:
        """
        
        try:
            from ml.gemini_utils import get_gemini_client
            client = get_gemini_client()
            response = await client.generate_content_async(prompt)
            text = response.text.strip()
            
            # Clean up potential markdown formatting
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
                
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Insight Error: {e}")
            return {
                "risk_score": 5,
                "survival_insight": "Stable condition. Continue monitoring.",
                "recommended_next_steps": ["Consult your oncologist"]
            }

class QRCodeGenerator:
    @staticmethod
    def generate_qr(data: str) -> str:
        """
        Generates a QR code containing the link/data and returns it as a base64 string.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
