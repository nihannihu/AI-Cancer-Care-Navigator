from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os
from datetime import datetime

from fastapi import FastAPI, File, Form, Request, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import httpx

from ml.model_utils import BreastCancerModel

# Import patient app router
from patient_app.router import patient_app_router, set_db

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"

# Load configuration from .env and .env.python if present
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.python", override=True)

# Geoapify API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"DEBUG: GEOAPIFY_API_KEY loaded at startup: {GEOAPIFY_API_KEY[:10] if GEOAPIFY_API_KEY else None}")

# Optional MongoDB client (mirrors data for persistence; app still works without it)
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI else None
db = mongo_client.get_default_database() if mongo_client is not None else None
db_cases = db["onco_cases"] if db is not None else None
db_symptoms = db["onco_patient_symptoms"] if db is not None else None

# Pass the database connection to the patient app router
if db is not None:
    set_db(db)

app = FastAPI(title="Onco-Navigator AI (No React)")

# Include the patient app router
app.include_router(patient_app_router, prefix="/patient")

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load model once at startup (honour MODEL_PATH if set)
_model_path_env = os.getenv("MODEL_PATH")
try:
    model = BreastCancerModel(Path(_model_path_env)) if _model_path_env else BreastCancerModel()
    print("✅ Breast cancer model loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load breast cancer model: {e}")
    print("⚠️ Initializing app without model - image analysis features will be disabled")
    model = None

# In-memory storage for demo (Mongo is used as a mirror for persistence)
class ScanCase:
    def __init__(
        self,
        case_id: int,
        patient_name: str,
        risk_label: str,
        risk_score: float,
        image_url: Optional[str] = None,
        image_path: Optional[Path] = None,
    ) -> None:
        self.case_id = case_id
        self.patient_name = patient_name
        self.risk_label = risk_label
        self.risk_score = risk_score
        self.status = "PENDING_NCG_REVIEW"  # or REVIEWED
        self.image_url = image_url
        self.image_path = image_path


SCAN_CASES: List[ScanCase] = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------- PCP: AI-Assisted Triage (The "Scan") --------------------

@app.get("/pcp", response_class=HTMLResponse)
async def pcp_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pcp_dashboard.html", {"request": request})


@app.post("/pcp/upload", response_class=HTMLResponse)
async def pcp_upload(
    request: Request,
    patient_name: str = Form(...),
    patient_email: str = Form(...),
    patient_phone: str = Form(...),
    file: UploadFile = File(...),
) -> HTMLResponse:
    # Check if model is available
    if model is None:
        return templates.TemplateResponse(
            "pcp_result.html",
            {
                "request": request,
                "patient_name": patient_name,
                "risk_label": "MODEL_UNAVAILABLE",
                "risk_score": 0.0,
                "case_id": 0,
                "image_url": None,
                "error": "Model not available - image analysis disabled"
            },
        )
    
    data = await file.read()
    label, score = model.predict_label(data)
    # Get cancer stage based on the probability score
    stage = model.predict_stage(score) if model else "Unknown"
    
    case_id = len(SCAN_CASES) + 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Persist uploaded image so it can be previewed in the UI
    uploads_dir = UPLOADS_DIR
    uploads_dir.mkdir(parents=True, exist_ok=True)
    original_suffix = Path(file.filename or "").suffix.lower() or ".jpg"
    filename = f"case_{case_id}{original_suffix}"
    image_path = uploads_dir / filename
    try:
        image_path.write_bytes(data)
        image_url = f"/static/uploads/{filename}"
    except Exception:
        # If saving fails, continue without a preview image
        image_url = None
        image_path = None

    case = ScanCase(
        case_id=case_id,
        patient_name=patient_name,
        risk_label=label,
        risk_score=score,
        image_url=image_url,
        image_path=image_path,
    )
    SCAN_CASES.append(case)

    # Mirror to MongoDB if configured (best-effort; failures do not break the app)
    if db_cases is not None:
        try:
            doc = {
                "case_id": case_id,
                "patient_name": patient_name,
                "patient_email": patient_email,
                "patient_phone": patient_phone,
                "risk_label": label,
                "risk_score": float(score),
                "status": case.status,
                "timestamp": timestamp
            }
            if image_url:
                doc["image_url"] = image_url
            await db_cases.insert_one(doc)
        except Exception:
            # For this prototype we silently ignore DB errors and continue with in-memory storage
            pass

    return templates.TemplateResponse(
        "pcp_result.html",
        {
            "request": request,
            "patient_name": patient_name,
            "risk_label": label,
            "risk_score": score,
            "case_id": case_id,
            "image_url": image_url,
            "timestamp": timestamp,
            "cancer_stage": stage  # Add cancer stage to the response
        },
    )


# -------------------- Oncologist: Tele-Oncology Navigation (The "Help") ------

@app.get("/oncologist", response_class=HTMLResponse)
async def oncologist_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "oncologist_dashboard.html",
        {"request": request, "cases": SCAN_CASES},
    )


@app.post("/oncologist/case/{case_id}/review")
async def oncologist_review(case_id: int) -> RedirectResponse:
    for c in SCAN_CASES:
        if c.case_id == case_id:
            c.status = "REVIEWED"
            if db_cases is not None:
                try:
                    # mirror status update to Mongo
                    await db_cases.update_one({"case_id": case_id}, {"$set": {"status": "REVIEWED"}})
                except Exception:
                    pass
            break
    return RedirectResponse(url="/oncologist", status_code=303)


@app.post("/oncologist/clear")
async def oncologist_clear() -> RedirectResponse:
    """Clear all oncologist worklist cases and associated images.

    This resets the in-memory worklist, removes any persisted cases in MongoDB,
    and deletes uploaded image files for the current session.
    """
    # Delete associated image files from disk (best-effort)
    for c in SCAN_CASES:
        if getattr(c, "image_path", None):
            try:
                Path(c.image_path).unlink(missing_ok=True)
            except Exception:
                pass

    SCAN_CASES.clear()
    if db_cases is not None:
        try:
            await db_cases.delete_many({})
        except Exception:
            pass
    return RedirectResponse(url="/oncologist", status_code=303)


# -------------------- Patient: Symptom Monitoring (The "Cure" support) ------

PATIENT_SYMPTOMS: List[dict] = []


@app.get("/patient", response_class=HTMLResponse)
async def patient_portal(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("patient_portal.html", {"request": request})


# Add a new endpoint to view patient symptom history
@app.get("/oncologist/patient-symptoms", response_class=HTMLResponse)
async def view_patient_symptoms(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("patient_symptoms.html", {"request": request, "symptoms": PATIENT_SYMPTOMS})


# Add a route to clear patient symptoms
@app.post("/oncologist/patient-symptoms/clear", response_class=HTMLResponse)
async def clear_patient_symptoms() -> RedirectResponse:
    PATIENT_SYMPTOMS.clear()
    if db_symptoms is not None:
        try:
            await db_symptoms.delete_many({})
        except Exception:
            pass
    return RedirectResponse(url="/oncologist/patient-symptoms", status_code=303)


@app.post("/patient/symptoms", response_class=HTMLResponse)
async def submit_symptoms(
    request: Request,
    patient_name: str = Form(...),
    nausea: int = Form(...),
    fatigue: int = Form(...),
    pain: int = Form(...),
) -> HTMLResponse:
    record = {
        "patient_name": patient_name,
        "nausea": nausea,
        "fatigue": fatigue,
        "pain": pain,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    PATIENT_SYMPTOMS.append(record)

    # Mirror to MongoDB if configured (best-effort)
    if db_symptoms is not None:
        try:
            await db_symptoms.insert_one(record)
        except Exception:
            pass

    alert = None
    if max(nausea, fatigue, pain) >= 4:
        alert = "High symptom burden detected. Nurse should follow up."  # in real app, push alert

    return templates.TemplateResponse(
        "patient_thanks.html",
        {"request": request, "alert": alert},
    )


# -------------------- Raw AI API endpoint (for future integration) ----------

@app.get("/ai-diagnostics", response_class=HTMLResponse)
async def ai_diagnostics_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("ai_diagnostics.html", {"request": request})

@app.post("/api/predict")
async def api_predict(file: UploadFile = File(...)) -> JSONResponse:
    data = await file.read()
    label, score = model.predict_label(data)
    return JSONResponse({"label": label, "risk_score": score})


# -------------------- Emergency Hospital Finder -----------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the earth
    """
    import math
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

async def find_nearby_hospitals(latitude: float, longitude: float, api_key: str, radius_meters: int = 50000, limit: int = 15) -> List[dict]:
    """
    Helper function to find nearby hospitals using Geoapify API with filtering
    """
    if not latitude or not longitude or not api_key:
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search for healthcare.hospital first
        # Fetch more results to account for filtering (dental/clinics)
        fetch_limit = max(limit * 20, 100) # Increased limit to ensure we find valid hospitals
        
        # Add bias=proximity to ensure results are sorted by distance from the user
        url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital&filter=circle:{longitude},{latitude},{radius_meters}&bias=proximity:{longitude},{latitude}&limit={fetch_limit}&apiKey={api_key}"
        print(f"Calling Geoapify API: {url}")
        
        headers = {
            "User-Agent": "Onco-Navigator AI/1.0",
            "Accept": "application/json"
        }
        
        try:
            response = await client.get(url, headers=headers)
            features = []
            
            if response.status_code == 200:
                features = response.json().get("features", [])

            # Helper to filter features
            def filter_features(raw_features):
                valid = []
                for feature in raw_features:
                    props = feature.get("properties", {})
                    name = props.get("name", "").lower()
                    categories = props.get("categories", [])
                    
                    # Strict filtering
                    if "dental" in name or "dentist" in name:
                        continue
                    if "veterinary" in name or "animal" in name:
                        continue
                        
                    # Filter out clinics unless they are clearly hospitals/medical centers
                    # But allow "Medical Centre", "Health Centre", "Nursing Home"
                    if "clinic" in name and not any(x in name for x in ["hospital", "medical center", "medical centre", "nursing home"]):
                         continue
                    
                    # Exclude if category explicitly says dentist or veterinary
                    if any("dentist" in cat or "veterinary" in cat for cat in categories):
                        continue

                    # Calculate accurate distances
                    geometry = feature.get("geometry", {})
                    coords = geometry.get("coordinates", [])
                    
                    if len(coords) >= 2:
                        hospital_lon, hospital_lat = coords[0], coords[1]
                        distance_km = haversine_distance(latitude, longitude, hospital_lat, hospital_lon)
                        props["distance"] = int(distance_km * 1000)
                        props["distance_km"] = round(distance_km, 2)
                        valid.append(feature)
                return valid

            filtered_features = filter_features(features)

            # Fallback to general healthcare if no valid hospitals found after filtering
            if not filtered_features:
                print("No hospitals found after filtering, trying broader healthcare category")
                url = f"https://api.geoapify.com/v2/places?categories=healthcare&filter=circle:{longitude},{latitude},{radius_meters}&bias=proximity:{longitude},{latitude}&limit={fetch_limit}&apiKey={api_key}"
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    features = response.json().get("features", [])
                    filtered_features = filter_features(features)
            
            # Sort by distance
            sorted_features = sorted(filtered_features, key=lambda x: x.get("properties", {}).get("distance", float('inf')))
            
            # Log the top result
            if sorted_features:
                print(f"Top hospital found: {sorted_features[0].get('properties', {}).get('name')} at {sorted_features[0].get('properties', {}).get('distance_km')} km")
            
            return sorted_features[:limit]
            
        except Exception as e:
            print(f"Error in find_nearby_hospitals: {e}")
            
    return []

@app.post("/emergency-hospitals")
async def emergency_hospitals(request: Request) -> JSONResponse:
    """
    Find nearby hospitals based on patient's location using Geoapify API
    """
    try:
        body = await request.json()
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        
        # If no location provided, use mock data as fallback
        if not latitude or not longitude:
            return get_mock_hospitals_near_location(0, 0)
        
        # Check if Geoapify API key is available
        if not GEOAPIFY_API_KEY:
            return get_mock_hospitals_near_location(latitude, longitude)
        
        features = await find_nearby_hospitals(latitude, longitude, GEOAPIFY_API_KEY)
        
        if features:
            return JSONResponse({"features": features[:5]})
        else:
            return get_mock_hospitals_near_location(latitude, longitude)
        
    except Exception as e:
        print(f"Error in emergency hospitals: {e}")
        return get_mock_hospitals_near_location(0, 0)


def get_mock_hospitals_near_location(user_lat, user_lon):
    """
    Generate mock hospitals in Geoapify features format
    """
    import random
    
    # Generate mock hospitals within 5km of user's location
    mock_features = []
    
    hospital_names = [
        "City General Hospital",
        "Metropolitan Medical Center",
        "Community Health Center",
        "Regional Cancer Treatment Center",
        "District Hospital & Oncology",
        "Public Health Medical Center",
        "Central Clinic & Emergency Care",
        "University Medical Center",
        "General Hospital & Cancer Care",
        "Healthcare Center & Oncology"
    ]
    
    for i in range(10):
        # Generate random offset within ~5km
        lat_offset = random.uniform(-0.045, 0.045)
        lon_offset = random.uniform(-0.045, 0.045)
        
        hospital_lat = user_lat + lat_offset
        hospital_lon = user_lon + lon_offset
        
        # Calculate distance
        distance = haversine_distance(user_lat, user_lon, hospital_lat, hospital_lon) if user_lat != 0 else random.uniform(1, 5)
        
        # Create feature in Geoapify format
        feature = {
            "type": "Feature",
            "properties": {
                "name": f"{random.choice(hospital_names)}",
                "address_line1": f"{random.randint(100, 999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Dr', 'Hospital Rd', 'Medical Plaza'])}",
                "address_line2": f"{random.choice(['Downtown', 'Westside', 'North Hills', 'South End', 'East District'])}",
                "city": "City",
                "formatted": f"{random.randint(100, 999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd'])}, City",
                "distance": int(distance * 1000),  # Geoapify returns distance in meters
                "phone": f"+1 ({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "categories": ["healthcare.hospital"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [hospital_lon, hospital_lat]
            }
        }
        mock_features.append(feature)
    
    # Sort by distance
    mock_features.sort(key=lambda x: x["properties"]["distance"])
    
    return JSONResponse({"features": mock_features[:10]})


# AI Diagnostics API Endpoints
from ml.image_analysis import analyze_image
from ml.nlp_utils import analyze_report
from ml.predictive_models import predict_survival, predict_side_effects
import json

@app.post("/api/analyze-image")
async def api_analyze_image(file: UploadFile = File(...)) -> JSONResponse:
    try:
        data = await file.read()
        result = analyze_image(data)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/analyze-report")
async def api_analyze_report(file: UploadFile = File(...)) -> JSONResponse:
    try:
        data = await file.read()
        result = analyze_report(data)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/predict-outcome")
async def api_predict_outcome(request: Request) -> JSONResponse:
    try:
        body = await request.json()
        result = predict_survival(int(body.get("age", 50)), int(body.get("stage", 1)), int(body.get("comorbidities", 0)))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/predict-side-effects")
async def api_predict_side_effects(request: Request) -> JSONResponse:
    try:
        body = await request.json()
        result = predict_side_effects(int(body.get("age", 50)), int(body.get("chemo_type", 0)), float(body.get("dosage", 0.5)))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/analyze-symptoms")
async def api_analyze_symptoms(request: Request) -> JSONResponse:
    try:
        body = await request.json()
        text = body.get("text", "")
        if not text:
            return JSONResponse({"error": "No text provided"}, status_code=400)
        
        # Use Gemini API instead of OpenAI
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        print(f"DEBUG: GEMINI_API_KEY loaded: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else None}")  # Debug output
        if not GEMINI_API_KEY:
            return JSONResponse({"error": "Gemini API key not configured"}, status_code=500)
        
        # Use gemini-pro-latest model which should be more widely available
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are a medical assistant. Analyze the following symptoms and provide helpful medical insights: {text}"
                }]
            }]
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
        
        if response.status_code != 200:
            error_text = response.text
            return JSONResponse({
                "error": f"Gemini API Error ({response.status_code}): {error_text}",
                "status_code": response.status_code
            }, status_code=response.status_code)
        
        try:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0 and "content" in data["candidates"][0] and "parts" in data["candidates"][0]["content"] and len(data["candidates"][0]["content"]["parts"]) > 0:
                analysis = data["candidates"][0]["content"]["parts"][0]["text"]
                return JSONResponse({"analysis": analysis})
            else:
                return JSONResponse({
                    "error": "Unexpected response format from Gemini API",
                    "response": data
                }, status_code=500)
        except Exception as json_error:
            return JSONResponse({
                "error": f"Failed to parse Gemini API response: {str(json_error)}",
                "raw_response": response.text[:500]
            }, status_code=500)
            
    except Exception as e:
        print(f"Unexpected error in symptom analysis: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "error": f"Unexpected error: {str(e)}",
            "type": type(e).__name__
        }, status_code=500)



# -------------------- Smart Ambulance Booking -------------------------------

@app.post("/api/book-ambulance")
async def book_ambulance(request: Request) -> JSONResponse:
    """
    Smart Ambulance Booking API
    Returns priority, nearest hospital, and pre-filled WhatsApp message link.
    """
    try:
        body = await request.json()
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        
        # 1. AI Triage & Priority (Mocked based on existing data points)
        # In a real app, we'd fetch patient vitals/risk score from DB
        priority_level = "Priority 1"
        priority_desc = "Life-threatening (High Risk)"
        
        # 2. Find Nearest Hospital (Reuse logic or mock)
        # For MVP, we'll use the same logic as emergency_hospitals but pick the best one
        hospital_name = "City Cancer Center"
        hospital_lat = latitude + 0.01 if latitude else 0
        hospital_lon = longitude + 0.01 if longitude else 0
        distance = "8.2 km"
        eta = "14 min"
        
        # Try to get real hospital if location is provided
        if latitude and longitude and GEOAPIFY_API_KEY:
            # Get nearest hospital with filtering
            features = await find_nearby_hospitals(latitude, longitude, GEOAPIFY_API_KEY, limit=1)
            if features:
                hospital = features[0]
                props = hospital.get("properties", {})
                hospital_name = props.get("name", "Unknown Hospital")
                
                # Get address if name is generic
                if hospital_name == "Unknown Hospital" or not hospital_name:
                    hospital_name = props.get("formatted", "Nearby Medical Facility")
                
                dist_km = props.get("distance_km", 0)
                distance = f"{dist_km} km"
                # Estimate 3 min per km + 5 min base time for traffic/dispatch
                eta_val = int(dist_km * 3) + 5
                eta = f"{eta_val} min"
                
                coords = hospital.get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    hospital_lon, hospital_lat = coords[0], coords[1]

        # 3. Generate WhatsApp Link
        # Target: 9845325913
        phone_number = "919845325913"
        
        # Construct message
        message = f"""*EMERGENCY AMBULANCE REQUEST*
Priority: {priority_level} ({priority_desc})
Patient: Nihan (Cancer Care ID: #8821)
Location: https://www.google.com/maps?q={latitude},{longitude}
Symptoms: Severe chest pain, high cancer risk case
Destination: {hospital_name} (ETA: {eta})
"""
        import urllib.parse
        # Use api.whatsapp.com for better compatibility
        whatsapp_url = f"https://api.whatsapp.com/send?phone={phone_number}&text={urllib.parse.quote(message)}"
        
        return JSONResponse({
            "priority": priority_level,
            "priority_desc": priority_desc,
            "hospital": {
                "name": hospital_name,
                "distance": distance,
                "eta": eta,
                "lat": hospital_lat,
                "lng": hospital_lon
            },
            "whatsapp_url": whatsapp_url,
            "tracking_url": f"/ambulance/tracking?lat={latitude}&lng={longitude}&hospital={urllib.parse.quote(hospital_name)}&h_lat={hospital_lat}&h_lng={hospital_lon}"
        })

    except Exception as e:
        print(f"Error in book_ambulance: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/ambulance/tracking", response_class=HTMLResponse)
async def ambulance_tracking(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("ambulance_tracking.html", {"request": request})


# To run: uvicorn app_main:app --reload
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_main:app", host=host, port=port, reload=True)
