from __future__ import annotations

from io import BytesIO
from typing import Tuple, List, Dict, Any
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import img_to_array
import base64

# Load pre-trained MobileNetV2 model
# In a real scenario, we would fine-tune this on a medical dataset.
# For this hackathon/demo, we use the base model and simulate specific medical findings
# if the model detects something relevant or just provide a general analysis.
try:
    model = MobileNetV2(weights="imagenet")
except Exception as e:
    print(f"Failed to load MobileNetV2: {e}")
    model = None

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes an image using MobileNetV2 and returns predictions.
    Also simulates medical specific findings for demonstration.
    """
    if model is None:
        return {"error": "Model not loaded"}

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)

        preds = model.predict(x)
        decoded = decode_predictions(preds, top=3)[0]

        results = []
        for _, label, score in decoded:
            results.append({"label": label, "confidence": float(score)})

        # Create a base64 preview of the image for frontend display
        # Resize to a smaller size for preview
        preview_img = img.copy()
        preview_img.thumbnail((200, 200))  # Resize for preview
        preview_buffer = BytesIO()
        preview_img.save(preview_buffer, format="JPEG", quality=80)
        preview_base64 = base64.b64encode(preview_buffer.getvalue()).decode("utf-8")
        image_preview_url = f"data:image/jpeg;base64,{preview_base64}"

        # SIMULATED MEDICAL ANALYSIS for Demo
        # If we were fine-tuned, these would be real classes.
        # Here we simulate "Lung Cancer" detection if it looks like an X-ray (grayscale-ish)
        # or just return the ImageNet classes.
        
        is_xray_like = _is_grayscale_or_xray(img)
        medical_findings = {}
        
        if is_xray_like:
            # Simulate findings
            medical_findings = {
                "detected_condition": "Potential Abnormality Detected",
                "condition_type": "Lung Nodule / Mass",
                "confidence_score": 0.87, # Simulated high confidence
                "severity": "High",
                "recommendation": "Immediate CT Scan recommended",
                "regions": [
                    {"x": 100, "y": 100, "width": 50, "height": 50, "label": "Nodule"}
                ]
            }
        else:
            medical_findings = {
                "note": "Image does not appear to be a standard medical X-ray. Showing general object classification."
            }

        return {
            "classification": results,
            "medical_analysis": medical_findings,
            "is_medical_image": is_xray_like,
            "image_preview": image_preview_url
        }

    except Exception as e:
        return {"error": str(e)}

def _is_grayscale_or_xray(img: Image.Image) -> bool:
    # Simple heuristic: check if image is mostly grayscale
    # Convert to HSV and check saturation
    img_hsv = img.convert("HSV")
    s = np.array(img_hsv)[:, :, 1]
    avg_saturation = np.mean(s)
    return bool(avg_saturation < 20) # Low saturation implies grayscale/X-ray like