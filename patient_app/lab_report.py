import pytesseract
from PIL import Image
import io
import re
import json
import logging
from typing import Dict, Any, Tuple
import google.generativeai as genai
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

NORMAL_RANGES = {
    'WBC': (4.5, 11.0),
    'RBC': (4.5, 5.9), # Male approx
    'Platelets': (150, 450),
    'Hemoglobin': (13.5, 17.5) # Male approx
}

class OCRService:
    @staticmethod
    def extract_text(image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return ""

class LabAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_values(self, extracted_data: Dict[str, float]) -> Dict[str, Any]:
        results = []
        for test, value in extracted_data.items():
            status = "Normal"
            message = "Within normal range."
            
            # Normalize key to match NORMAL_RANGES
            norm_key = None
            for k in NORMAL_RANGES.keys():
                if k.lower() in test.lower():
                    norm_key = k
                    break
            
            if norm_key:
                low, high = NORMAL_RANGES[norm_key]
                if value < low:
                    status = "Low"
                elif value > high:
                    status = "High"
                
                results.append({
                    "test": norm_key,
                    "value": value,
                    "status": status,
                    "range": f"{low}-{high}"
                })
        return results

    async def analyze_report(self, text: str) -> Dict[str, Any]:
        """
        Uses Gemini to extract values and generate a summary.
        """
        prompt = f"""
        Extract the following blood test values from the text below:
        - WBC (White Blood Cells)
        - RBC (Red Blood Cells)
        - Platelets
        - Hemoglobin
        
        Return a JSON object with keys: 'WBC', 'RBC', 'Platelets', 'Hemoglobin'. 
        Values should be numbers (floats). If not found, use null.
        
        Also generate a "summary" field: A comforting, non-medical summary for the patient explaining the results in simple terms. 
        If values are abnormal (WBC < 4.5 or > 11.0, RBC < 4.5 or > 5.9, Platelets < 150 or > 450, Hemoglobin < 13.5 or > 17.5), mention it gently.
        Example summary: "Your WBC is slightly low, which is common during Chemo. Please rest well."

        Report Text:
        {text}
        
        JSON Response:
        """
        
        try:
            response = self.model.generate_content(prompt)
            text_resp = response.text.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:-3]
            
            data = json.loads(text_resp)
            
            # Clean up extraction for analysis
            extraction = {k: v for k, v in data.items() if k in NORMAL_RANGES and isinstance(v, (int, float))}
            
            # Run rule-based analysis on top of Gemini's extraction for structured status
            structured_analysis = self.analyze_values(extraction)
            
            return {
                "raw_text": text[:200] + "...",
                "extracted_values": extraction,
                "analysis": structured_analysis,
                "summary": data.get("summary", "Analysis complete.")
            }

        except Exception as e:
            logger.error(f"Gemini Analysis Error: {e}")
            return {"error": "Failed to analyze report."}
