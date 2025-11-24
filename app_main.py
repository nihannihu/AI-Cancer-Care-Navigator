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
load_dotenv(ROOT / ".env.python")  # Load the Python environment file with API keys

app = FastAPI(title="Onco-Navigator AI (No React)")

# Include the patient app router
app.include_router(patient_app_router, prefix="/patient")


# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    # Also mount uploads directory if it exists
    uploads_dir = STATIC_DIR / "uploads"
    if uploads_dir.exists():
        app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="uploads")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load model once at startup (honour MODEL_PATH if set)
_model_path_env = os.getenv("MODEL_PATH")
model = BreastCancerModel(Path(_model_path_env)) if _model_path_env else BreastCancerModel()

# Optional MongoDB client (mirrors data for persistence; app still works without it)
MONGODB_URI = os.getenv("MONGODB_URI")
try:
    mongo_client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI and MONGODB_URI != "mongodb://localhost:27017/onco_navigator" else None
    db = mongo_client.get_default_database() if mongo_client is not None else None
    db_cases = db["onco_cases"] if db is not None else None
    db_symptoms = db["onco_patient_symptoms"] if db is not None else None
except Exception as e:
    print(f"Warning: Could not connect to MongoDB: {e}")
    mongo_client = None
    db = None
    db_cases = None
    db_symptoms = None

# Geoapify API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# Get database instance for patient app
try:
    if db is not None:
        from patient_app.auth import users_collection
        # Make db available to patient_app
        import patient_app.router
        patient_app.router.db = db
except Exception as e:
    print(f"Warning: Could not setup patient app database: {e}")

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
    patient_email: str = Form(...),  # Add email for linking to patient
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
        print(f"Image saved to: {image_path}")
        print(f"Image URL: {image_url}")
    except Exception as e:
        # If saving fails, continue without a preview image
        print(f"Error saving image: {e}")
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
                "patient_email": patient_email,  # Store email for linking
                "risk_label": label,
                "risk_score": float(score),
                "status": case.status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
            }
            if image_url:
                doc["image_url"] = image_url
            await db_cases.insert_one(doc)
            
            # Also store in patient_cases collection for patient dashboard
            try:
                db_patient_cases = db["patient_cases"] if db is not None else None
                if db_patient_cases is not None:
                    await db_patient_cases.insert_one({
                        "patient_email": patient_email,
                        "case_id": case_id,
                        "risk_label": label,
                        "risk_score": float(score),
                        "image_url": image_url,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
                    })
            except Exception as e:
                print(f"Warning: Could not store case in patient_cases collection: {e}")
        except Exception as e:
            print(f"Warning: Could not store case in database: {e}")
            # For this prototype we silently ignore DB errors and continue with in-memory storage
            pass

    return templates.TemplateResponse(
        "pcp_result.html",
        {
            "request": request,
            "patient_name": patient_name,
            "patient_email": patient_email,
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
@app.get("/ai-diagnostics", response_class=HTMLResponse)
async def ai_diagnostics_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("ai_diagnostics.html", {"request": request})

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
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        print(f"Gemini API Key: {GEMINI_API_KEY}")  # Debug output
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            # Return mock response when API key is not configured
            return JSONResponse({
                "analysis": f"Mock analysis of symptoms: {text}\n\nNote: Gemini API key not configured. Please set GEMINI_API_KEY in .env file for real AI analysis."
            })
        
        # Check if the API key is valid (not reported as leaked)
        if "AIzaSyCrJaAJih1vUhv_lZHJZHycm4Nvsja9Png" in GEMINI_API_KEY:
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_main:app", host=host, port=port, reload=True)