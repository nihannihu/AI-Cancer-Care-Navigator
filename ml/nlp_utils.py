from __future__ import annotations

import io
from typing import Dict, Any, List
import pypdf
import re

# Try to load spacy, fallback to None if not found
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = spacy.blank("en")
except ImportError:
    print("Spacy not installed. Using regex fallback.")
    nlp = None

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

import google.generativeai as genai
import os

def analyze_report(pdf_bytes: bytes) -> Dict[str, Any]:
    text = extract_text_from_pdf(pdf_bytes)
    
    # DEBUG: Write extracted text to file for inspection
    try:
        with open("debug_last_pdf_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"Failed to write debug file: {e}")

    # Check if text is empty (scanned PDF case)
    if not text or not text.strip():
        print("DEBUG: No text extracted from PDF. Attempting fallback to Gemini Vision API...")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             return {
                "text_snippet": "No text extracted.",
                "sentiment": {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0},
                "extracted_entities": {
                    "diagnosis": ["Error: Scanned PDF detected but GEMINI_API_KEY not found."],
                    "stage": [], "grade": [], "tumor_size": [],
                    "biomarkers": [], "alerts": [], "risk_level": ["Unknown"]
                },
                "summary": "Could not read text from PDF. Please configure GEMINI_API_KEY to enable OCR for scanned documents."
            }
            
        try:
            genai.configure(api_key=api_key)
            # User has access to gemini-pro-latest
            model = genai.GenerativeModel('models/gemini-pro-latest')
            
            prompt = """
            Analyze this pathology report and extract the following information in JSON format:
            {
                "diagnosis": "The main diagnosis",
                "stage": "The cancer stage (e.g., IIA)",
                "grade": "The histologic grade (e.g., 2)",
                "tumor_size": "The size of the tumor",
                "biomarkers": [
                    {"name": "ER", "status": "Positive/Negative", "value": "percentage/intensity"},
                    {"name": "PR", "status": "Positive/Negative", "value": "percentage/intensity"},
                    {"name": "HER2", "status": "Positive/Negative", "value": "score"},
                    {"name": "Ki-67", "status": "High/Low", "value": "percentage"}
                ],
                "alerts": [
                    {"alert": "Alert Name", "why": "Reason", "action": "Recommended Action"}
                ],
                "risk_level": "High/Low/Unknown"
            }
            Only return the JSON.
            """
            
            # Gemini supports PDF via parts
            response = model.generate_content([
                {'mime_type': 'application/pdf', 'data': pdf_bytes},
                prompt
            ])
            
            # Clean up response text to ensure valid JSON
            json_str = response.text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]
                
            import json
            data = json.loads(json_str)
            
            # Construct the return format expected by the frontend
            return {
                "text_snippet": "Scanned PDF processed by Gemini AI.",
                "sentiment": {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0},
                "extracted_entities": {
                    "diagnosis": [data.get("diagnosis", "Not found")],
                    "stage": [data.get("stage", "Not specified")],
                    "grade": [data.get("grade", "Not specified")],
                    "tumor_size": [data.get("tumor_size", "Not specified")],
                    "biomarkers": data.get("biomarkers", []),
                    "alerts": data.get("alerts", []),
                    "risk_level": [data.get("risk_level", "Unknown")]
                },
                "summary": f"Patient diagnosed with {data.get('diagnosis', 'unknown condition')}."
            }
            
        except Exception as e:
            print(f"Gemini Fallback Error: {e}")
            return {
                "text_snippet": "Error using Gemini API.",
                "sentiment": {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0},
                "extracted_entities": {
                    "diagnosis": [f"Error: Failed to analyze scanned PDF. {str(e)}"],
                    "stage": [], "grade": [], "tumor_size": [],
                    "biomarkers": [], "alerts": [], "risk_level": ["Unknown"]
                },
                "summary": "An error occurred while processing the scanned document."
            }

    # --- 1. Diagnosis Extraction ---
    # Look for "Diagnosis:" followed by text, capturing until double newline or specific keywords
    diagnosis_match = re.search(r"(?:diagnosis|impression|conclusion):?\s*(.*?)(?:\n\n|\n(?:Stage|Tumor|Margins|Biomarkers|Markers|History|Specimen))", text, re.IGNORECASE | re.DOTALL)
    diagnosis = diagnosis_match.group(1).strip() if diagnosis_match else "Not found"
    
    # --- 2. Stage & Grade ---
    stage_match = re.search(r"(?:stage)(?:/grade)?[:\s]+([IV0-9]+[ab]?)", text, re.IGNORECASE)
    stage = stage_match.group(1) if stage_match else "Not specified"
    
    grade_match = re.search(r"(?:grade|gleason)[:\s]+(.*?)(?:\n|$)", text, re.IGNORECASE)
    grade = grade_match.group(1).strip() if grade_match else "Not specified"

    # --- 3. Tumor Size ---
    size_match = re.search(r"Tumor Size:?\s*([\d\.]+\s*cm)", text, re.IGNORECASE)
    tumor_size = size_match.group(1) if size_match else "Not specified"

    # --- 4. Biomarkers (ER, PR, HER2, Ki-67) ---
    biomarkers = []
    
    # Helper to find biomarker status and value
    def extract_marker(name_pattern, text_block):
        # Regex to find: MarkerName ... [Status] ... [Value]
        # Example: Estrogen Receptor (ER): Positive (90%...)
        match = re.search(rf"({name_pattern}).*?[:\s]+(Positive|Negative|High|Low|Equivocal)(.*)", text_block, re.IGNORECASE)
        if match:
            return {
                "name": match.group(1).upper(),
                "status": match.group(2),
                "value": match.group(3).strip(" ()-.,")
            }
        return None

    # Extract from the "Biomarkers:" section if possible, or just search the whole text
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        
        # Check for ER
        if re.search(r"\b(ER|Estrogen Receptor)\b", line, re.IGNORECASE):
            m = extract_marker(r"ER|Estrogen Receptor", line)
            if m: 
                m["name"] = "ER"
                biomarkers.append(m)
        
        # Check for PR
        elif re.search(r"\b(PR|Progesterone Receptor)\b", line, re.IGNORECASE):
            m = extract_marker(r"PR|Progesterone Receptor", line)
            if m: 
                m["name"] = "PR"
                biomarkers.append(m)
                
        # Check for HER2
        elif re.search(r"\bHER2\b", line, re.IGNORECASE):
            m = extract_marker(r"HER2", line)
            if m: biomarkers.append(m)
            
        # Check for Ki-67
        elif re.search(r"\bKi-67\b", line, re.IGNORECASE):
            m = extract_marker(r"Ki-67", line)
            if m: biomarkers.append(m)

    # --- 5. Risk Alerts ---
    alerts = []
    
    # Alert: Positive Margins
    if re.search(r"Margins:?\s*Positive", text, re.IGNORECASE):
        alerts.append({
            "alert": "Positive Margins",
            "why": "The report says \"Margins: Positive\".",
            "action": "Surgical re-excision may be required."
        })
        
    # Alert: Lymphovascular Invasion
    if re.search(r"Lymphovascular Invasion:?\s*Present", text, re.IGNORECASE):
        alerts.append({
            "alert": "Lymphovascular Invasion",
            "why": "Report says \"Present\".",
            "action": "Increases risk of metastasis; check lymph nodes."
        })

    # --- Risk Stratification Logic ---
    risk = "Unknown"
    if "carcinoma" in diagnosis.lower() or "malignant" in diagnosis.lower():
        risk = "High"
    elif "benign" in diagnosis.lower():
        risk = "Low"
    
    # Mock Sentiment Analysis
    sentiment = {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}
    if risk == "High":
        sentiment["compound"] = -0.7
        sentiment["neg"] = 0.8
    elif risk == "Low":
        sentiment["compound"] = 0.5
        sentiment["pos"] = 0.6

    # DEBUG LOGGING
    print(f"DEBUG: Extracted text length: {len(text)}")
    print(f"DEBUG: Text snippet: {text[:200]!r}")
    print(f"DEBUG: Diagnosis: {diagnosis}")
    print(f"DEBUG: Biomarkers found: {len(biomarkers)}")
    print(f"DEBUG: Alerts found: {len(alerts)}")

    return {
        "text_snippet": text[:500] + "...",
        "sentiment": sentiment,
        "extracted_entities": {
            "diagnosis": [diagnosis] if diagnosis != "Not found" else [],
            "stage": [stage] if stage != "Not specified" else [],
            "grade": [grade] if grade != "Not specified" else [],
            "tumor_size": [tumor_size] if tumor_size != "Not specified" else [],
            "biomarkers": biomarkers,
            "alerts": alerts,
            "risk_level": [risk]
        },
        "summary": f"Patient diagnosed with {diagnosis}. Risk level assessed as {risk}."
    }
