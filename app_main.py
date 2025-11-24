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
from patient_app.router import patient_app_router

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"

# Load configuration from .env if present
load_dotenv(ROOT / ".env")

app = FastAPI(title="Onco-Navigator AI (No React)")

# Include the patient app router
app.include_router(patient_app_router, prefix="/patient")

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load model once at startup (honour MODEL_PATH if set)
_model_path_env = os.getenv("MODEL_PATH")
model = BreastCancerModel(Path(_model_path_env)) if _model_path_env else BreastCancerModel()
model = BreastCancerModel(Path(_model_path_env)) if _model_path_env else BreastCancerModel()

# Optional MongoDB client (mirrors data for persistence; app still works without it)
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI else None
db = mongo_client.get_default_database() if mongo_client is not None else None
db_cases = db["onco_cases"] if db is not None else None
db_symptoms = db["onco_patient_symptoms"] if db is not None else None

# Geoapify API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


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
    file: UploadFile = File(...),
) -> HTMLResponse:
    data = await file.read()
    label, score = model.predict_label(data)

    case_id = len(SCAN_CASES) + 1

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
                "risk_label": label,
                "risk_score": float(score),
                "status": case.status,
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
            print("No location provided, returning mock hospitals")
            return get_mock_hospitals_near_location(0, 0)
        
        # Check if Geoapify API key is available
        if not GEOAPIFY_API_KEY:
            print("No Geoapify API key, using mock data")
            return get_mock_hospitals_near_location(latitude, longitude)
        
        # Use Geoapify API to find nearby hospitals
        async with httpx.AsyncClient() as client:
            # Search for hospitals and medical facilities within 10km radius
            url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare.clinic,healthcare&filter=circle:{longitude},{latitude},10000&limit=10&apiKey={GEOAPIFY_API_KEY}"
            print(f"Calling Geoapify API: {url[:100]}...")
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                if features and len(features) > 0:
                    print(f"Found {len(features)} hospitals from Geoapify")
                    # Return the features directly - frontend expects this format
                    return JSONResponse({"features": features[:10]})
                else:
                    print("No hospitals found via API, using mock data")
                    return get_mock_hospitals_near_location(latitude, longitude)
            else:
                print(f"Geoapify API failed with status {response.status_code}, using mock data")
                return get_mock_hospitals_near_location(latitude, longitude)
        
    except Exception as e:
        print(f"Error in emergency hospitals: {e}")
        # Final fallback to mock data
        lat = body.get("latitude", 0) if 'body' in locals() else 0
        lon = body.get("longitude", 0) if 'body' in locals() else 0
        return get_mock_hospitals_near_location(lat, lon)


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
        
        # Use OpenAI API instead of Gemini
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return JSONResponse({"error": "OpenAI API key not configured"}, status_code=500)
        
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a medical assistant. Analyze the following symptoms and provide helpful medical insights."},
                {"role": "user", "content": f"Analyze these symptoms: {text}"}
            ],
            "max_tokens": 500
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
        
        if response.status_code != 200:
            return JSONResponse({"error": f"API Error: {response.text}"}, status_code=response.status_code)
        
        data = response.json()
        analysis = data["choices"][0]["message"]["content"]
        return JSONResponse({"analysis": analysis})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# To run: uvicorn app_main:app --reload
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_main:app", host=host, port=port, reload=True)
