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

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"

# Load configuration from .env if present
load_dotenv(ROOT / ".env")

app = FastAPI(title="Onco-Navigator AI (No React)")

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load model once at startup (honour MODEL_PATH if set)
_model_path_env = os.getenv("MODEL_PATH")
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

@app.post("/api/predict")
async def api_predict(file: UploadFile = File(...)) -> JSONResponse:
    data = await file.read()
    label, score = model.predict_label(data)
    return JSONResponse({"label": label, "risk_score": score})


# -------------------- Emergency Hospital Finder -----------------------------

@app.post("/emergency-hospitals")
async def emergency_hospitals(request: Request, location: dict) -> JSONResponse:
    """
    Find nearby hospitals based on patient's location using Geoapify API
    """
    try:
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        
        if not latitude or not longitude:
            return JSONResponse({"error": "Invalid location data"}, status_code=400)
        
        # Check if Geoapify API key is available
        if not GEOAPIFY_API_KEY:
            # Fallback to mock data if API key is missing
            latitude = location.get("latitude", 17.4243)
            longitude = location.get("longitude", 78.4312)
            return get_mock_hospitals_near_location(latitude, longitude)
        
        # Use Geoapify API to find nearby hospitals
        async with httpx.AsyncClient() as client:
            # Search for hospitals and medical facilities within 10km radius
            response = await client.get(
                f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare.clinic,healthcare&filter=circle:{longitude},{latitude},10000&limit=5&apiKey={GEOAPIFY_API_KEY}"
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                
                hospitals = []
                for feature in features:
                    properties = feature.get("properties", {})
                    coordinates = feature.get("geometry", {}).get("coordinates", [])
                    
                    if properties and len(coordinates) >= 2:
                        # Calculate accurate distance using haversine formula
                        hospital_lon, hospital_lat = coordinates[0], coordinates[1]
                        distance_km = haversine_distance(latitude, longitude, hospital_lat, hospital_lon)
                        
                        hospital_info = {
                            "name": properties.get("name", "Unnamed Hospital"),
                            "address": properties.get("formatted", "Address not available"),
                            "distance": round(distance_km, 2),
                            "estimated_time": int(distance_km * 2),  # Rough estimate: 2 minutes per km
                            "phone": properties.get("phone", "Phone not available"),
                            "specialist_name": "Medical Specialist"  # Default specialist name
                        }
                        hospitals.append(hospital_info)
                
                # Sort hospitals by distance
                hospitals.sort(key=lambda x: x["distance"])
                
                # Return up to 5 nearest hospitals
                return JSONResponse({"hospitals": hospitals[:5]})
            else:
                # Fallback to mock data if API fails - using user's actual location
                return get_mock_hospitals_near_location(latitude, longitude)
        
    except Exception as e:
        print(f"Error finding hospitals: {e}")
        # Fallback to mock data if there's an error
        latitude = location.get("latitude", 17.4243)
        longitude = location.get("longitude", 78.4312)
        return get_mock_hospitals_near_location(latitude, longitude)


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
    Generate mock hospitals near the user's actual location
    """
    import random
    
    # Generate mock hospitals within 5km of user's location
    mock_hospitals = []
    
    hospital_names = [
        "City General Hospital",
        "Metropolitan Medical Center",
        "Community Health Center",
        "Regional Medical Facility",
        "District Hospital",
        "Public Health Center",
        "Central Clinic",
        "University Medical Center",
        "General Hospital",
        "Healthcare Center"
    ]
    
    for i in range(5):
        # Generate random offset within ~5km
        lat_offset = random.uniform(-0.045, 0.045)  # ~5km latitude offset
        lon_offset = random.uniform(-0.045, 0.045)  # ~5km longitude offset
        
        hospital_lat = user_lat + lat_offset
        hospital_lon = user_lon + lon_offset
        
        # Calculate accurate distance
        distance = haversine_distance(user_lat, user_lon, hospital_lat, hospital_lon)
        
        hospital_info = {
            "name": f"{random.choice(hospital_names)} {i+1}",
            "address": f"{random.randint(100, 999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Dr'])}",
            "distance": round(distance, 2),
            "estimated_time": int(distance * 2),
            "phone": f"+1 ({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "specialist_name": "Emergency Medical Specialist"
        }
        mock_hospitals.append(hospital_info)
    
    # Sort by distance
    mock_hospitals.sort(key=lambda x: x["distance"])
    
    return JSONResponse({"hospitals": mock_hospitals[:5]})

# To run: uvicorn app_main:app --reload
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_main:app", host=host, port=port, reload=True)