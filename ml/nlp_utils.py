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

def analyze_report(pdf_bytes: bytes) -> Dict[str, Any]:
    text = extract_text_from_pdf(pdf_bytes)
    
    # Basic Entity Extraction using Spacy if available
    entities = []
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            entities.append({"text": ent.text, "label": ent.label_})
        
    # Regex based extraction for specific medical fields (Simulating BioBERT capabilities)
    # In a real app, we would use a fine-tuned BERT model for this.
    
    diagnosis_match = re.search(r"(diagnosis|impression|conclusion):?\s*(.*)", text, re.IGNORECASE)
    diagnosis = diagnosis_match.group(2).strip() if diagnosis_match else "Not found"
    
    stage_match = re.search(r"(stage)\s+([IV0-9]+[ab]?)", text, re.IGNORECASE)
    stage = stage_match.group(2) if stage_match else "Not specified"
    
    gleason_match = re.search(r"(gleason|grade)\s*([0-9]\s*\+\s*[0-9]|[0-9])", text, re.IGNORECASE)
    grade = gleason_match.group(0) if gleason_match else "Not specified"

    # Risk Stratification Logic (Rule-based for demo)
    risk = "Unknown"
    if "carcinoma" in diagnosis.lower() or "malignant" in diagnosis.lower():
        risk = "High"
    elif "benign" in diagnosis.lower():
        risk = "Low"
    
    # Mock Sentiment Analysis (VADER style)
    sentiment = {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}
    if risk == "High":
        sentiment["compound"] = -0.7
        sentiment["neg"] = 0.8
    elif risk == "Low":
        sentiment["compound"] = 0.5
        sentiment["pos"] = 0.6

    return {
        "text_snippet": text[:500] + "...",
        "sentiment": sentiment,
        "extracted_entities": {
            "diagnosis": [diagnosis] if diagnosis != "Not found" else [],
            "stage": [stage] if stage != "Not specified" else [],
            "grade": [grade] if grade != "Not specified" else [],
            "risk_level": [risk]
        },
        "summary": f"Patient diagnosed with {diagnosis}. Risk level assessed as {risk}."
    }
