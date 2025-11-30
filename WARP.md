# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Key Commands

### Python backend (FastAPI)

- Create and activate a virtual environment (from repo root):
  - Windows (PowerShell): `python -m venv .venv; .venv\\Scripts\\Activate.ps1`
  - Unix-like: `python -m venv .venv && source .venv/bin/activate`
- Install Python dependencies:
  - `pip install -r requirements.txt`
- Run the backend with auto-reload (preferred for development):
  - `uvicorn app_main:app --reload`
- Alternative: run via the main guard in `app_main.py` (also honors `APP_HOST`/`APP_PORT`):
  - `python app_main.py`

The backend listens on `APP_HOST:APP_PORT` (default `0.0.0.0:8000`).

### Node.js frontend (proxy + static UI)

From the repo root (where `package.json` and `server.js` live):

- Install Node dependencies (first time or when dependencies change):
  - `npm install`
- Run the frontend server (production-style):
  - `npm start`  
    (alias for `node server.js`)
- Run the frontend in watch/dev mode (requires `nodemon`):
  - `npm run dev`

The frontend listens on `PORT` (default `3000`) and proxies requests to the Python backend at `AI_BACKEND_URL`.

### Environment configuration

- Python backend loads configuration from `.env.python` (see `app_main.py` and `patient_app/config.py`).
  - Important variables include (names only): `MONGODB_URI`, `GEOAPIFY_API_KEY`, `GEMINI_API_KEY`, `CALENDAR_API_KEY`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `APP_HOST`, `APP_PORT`, `APP_URL`, `MODEL_PATH`, email-related variables (`SENDGRID_API_KEY`, `SMTP_*`, `ADMIN_EMAIL`, etc.).
- A more generic example config is in `.env.example`; it can be copied and adapted but note that the running backend currently calls `load_dotenv(".env.python")`.
- The Node frontend reads its own `.env` (via `dotenv` in `server.js`):
  - Typical variables: `PORT`, `AI_BACKEND_URL`, `NODE_ENV`.

### Test and utility scripts

This project uses ad-hoc Python scripts rather than a unified test runner. Each `test_*.py` file is intended to be run directly with `python` from the repo root.

Commonly used ones:

- Basic FastAPI smoke test (imports the app and hits a few routes):
  - `python test_fastapi_basic.py`
- AI diagnostics HTTP smoke tests (requires backend running at `http://localhost:8000`):
  - `python test_ai_diagnostics.py`
  - `python test_new_features.py`
- Emergency hospitals / Geoapify connectivity tests (require `GEOAPIFY_API_KEY` and backend or direct HTTP access):
  - `python test_hospitals.py`
  - `python test_geoapify.py`
  - `python test_geoapify_simple.py`
- MongoDB and real data flow integration test (requires `MONGODB_URI`):
  - `python test_real_data_flow.py`
- Files for checking image upload paths and bcrypt behavior:
  - `python test_image.py`
  - `python test_bcrypt.py`
  - `python test_hash_only.py`

To "run a single test" in this repository, invoke the corresponding script with `python`, e.g. `python test_new_features.py`.

## Architecture Overview

### High-level system design

The project is a two-tier web application:

1. **Python FastAPI backend** (`app_main.py`)
   - Hosts the main clinical workflows, AI endpoints, and patient/oncologist views via Jinja2 templates.
   - Provides REST/JSON APIs that the frontend and external scripts call.
2. **Node.js/Express frontend proxy** (`server.js`)
   - Serves static assets from the `static/` directory.
   - Proxies key application routes (`/pcp`, `/oncologist`, `/patient`, `/ai-diagnostics`) to the FastAPI backend configured via `AI_BACKEND_URL`.

### Python backend structure (`app_main.py` and related modules)

`app_main.py` is the FastAPI entrypoint and wires together:

- **Template and static asset handling**
  - Uses `Jinja2Templates` with the `templates/` directory.
  - Serves static assets from `static/`, and exposes uploaded imaging files under `static/uploads`.

- **Breast cancer imaging triage (PCP workflow)**
  - Route: `/pcp` (GET) renders the PCP dashboard template.
  - Route: `/pcp/upload` (POST) accepts an image upload and patient metadata.
    - Uses `ml.model_utils.BreastCancerModel` to run a CNN on the uploaded mammogram.
    - Stores cases in an in-memory list `SCAN_CASES` for the current process.
    - Persists mirrored case data (including risk label/score and optional image URL) into MongoDB collection `onco_cases` (and `patient_cases` for patient-centric views) when `MONGODB_URI` is configured.
    - Saves the uploaded image to `static/uploads/` and returns a Jinja template (`pcp_result.html`) with the prediction and preview URL.

- **Oncologist tele-oncology dashboard**
  - Route: `/oncologist` (GET) lists `SCAN_CASES` for review.
  - Route: `/oncologist/case/{case_id}/review` (POST) updates the case status to `REVIEWED` in memory and in MongoDB (`onco_cases`) if available.
  - Route: `/oncologist/clear` (POST) clears the in-memory worklist and deletes corresponding documents in `onco_cases`; it also best-effort deletes uploaded image files from disk.

- **Patient symptom monitoring and oncologist view of symptoms**
  - In-memory list `PATIENT_SYMPTOMS` holds recent symptom submissions.
  - Route: `/patient` (GET) serves the patient symptom submission portal.
  - Route: `/patient/symptoms` (POST) records symptom scores, appends timestamps, and mirrors them into `onco_patient_symptoms` when MongoDB is configured; can set an alert flag for high symptom burden.
  - Routes under `/oncologist/patient-symptoms` allow oncologists to view and clear the aggregated patient symptom history.

- **Raw AI endpoints for integrations**
  - `/api/predict` — wraps `BreastCancerModel` for direct image binary classification.
  - `/api/analyze-image` — uses `ml.image_analysis.analyze_image` (MobileNetV2-based general image classifier with heuristics for X-ray-like images and base64 previews).
  - `/api/analyze-report` — uses `ml.nlp_utils.analyze_report` to parse PDF reports, perform simple NLP/regex extraction, and compute a risk-oriented summary.
  - `/api/predict-outcome` and `/api/predict-side-effects` — call into `ml.predictive_models` RandomForest-based mock models to return survival and side-effect predictions given basic clinical inputs.
  - `/api/analyze-symptoms` — sends free-text symptom descriptions to the Gemini API (or returns a mock analysis when no valid `GEMINI_API_KEY` is set), with robust error handling and explicit fallbacks for missing or reported-leaked keys.

- **Emergency hospital finder**
  - Route: `/emergency-hospitals` (POST) expects a JSON body with `latitude` and `longitude`.
  - Calls the Geoapify Places API using `GEOAPIFY_API_KEY` to fetch nearby hospitals/healthcare facilities, validates response type, and normalizes results (name, address, distance via `haversine_distance`, rough travel time, phone, and a generic specialist label).
  - Includes `get_mock_hospitals_near_location` as a utility to generate synthetic nearby hospitals when a real API call is not desired.

- **App inclusion and startup**
  - Includes the `patient_app` router under the `/patient` prefix (`app.include_router(patient_app_router, prefix="/patient")`), layering the patient portal API on top of the base app.
  - The `if __name__ == "__main__"` guard uses `uvicorn.run("app_main:app", ...)`, so direct `python app_main.py` is sufficient for local runs.

MongoDB usage is optional but, when enabled, `app_main.py` sets up `AsyncIOMotorClient` and exposes `db`, `db_cases`, and `db_symptoms`. It also tries to link this `db` into `patient_app.router` for dashboard queries.

### Machine learning utilities (`ml/`)

The `ml` package provides self-contained utilities for AI tasks:

- `model_utils.py` — wraps a TensorFlow CNN model stored at `ml/breast_cancer_cnn.h5` in `BreastCancerModel`, handling image preprocessing from raw bytes to model input and mapping predictions into BENIGN/MALIGNANT labels.
- `image_analysis.py` — uses MobileNetV2 (when available) to classify uploaded images, with additional heuristics for X-ray-like grayscale images and simulated lung nodule findings; also returns a downscaled, base64-encoded preview image for UI display.
- `nlp_utils.py` — focuses on PDF lab/diagnostic report ingestion using `pypdf` and optional spaCy, extracting entities and a few structured fields (diagnosis, stage, grade) via regex and producing a risk-level summary and sentiment-like scores.
- `predictive_models.py` — generates synthetic datasets on import, trains `RandomForestClassifier` instances for survival and side-effect prediction, and exposes `predict_survival` and `predict_side_effects` helper functions used by the FastAPI endpoints.

These modules are designed so that the FastAPI layer only handles HTTP and orchestration, while the ML logic remains encapsulated under `ml/`.

### Patient application subpackage (`patient_app/`)

The `patient_app` package implements a richer, logged-in patient portal and associated services:

- **Authentication and user storage (`auth.py`)**
  - Uses `passlib` (bcrypt) for password hashing.
  - Stores users in MongoDB (`onco_navigator.patient_users`) via `AsyncIOMotorClient(MONGODB_URI)`.
  - Issues JWT access tokens with `SECRET_KEY` and `ALGORITHM` from `patient_app/config.py`.
  - `get_current_user` is the core dependency used across patient routes to enforce authenticated access.

- **Configuration (`config.py`)**
  - Centralizes environment-driven settings for HAPI FHIR, Gemini, MongoDB, and JWT properties (`ACCESS_TOKEN_EXPIRE_MINUTES`).

- **Router and high-level workflows (`router.py`)**
  - Declares an `APIRouter` (`patient_app_router`) mounted under `/patient` in `app_main.py`.
  - Provides HTML pages for login/registration/dashboard via Jinja templates.
  - Registration/login endpoints integrate with `users_collection` (from `auth.py`) and enforce basic validation and bcrypt-safe password truncation.
  - Profile and diagnosis endpoints call `FHIRClient` to create FHIR `Patient` and `Condition` resources and link FHIR IDs back to local users.
  - Chat endpoints use `GeminiIntent`, `CalendarService`, and `EmailService` to:
    - Infer intent from patient free text.
    - Mock or call Google Calendar for appointment slots.
    - Optionally send email notifications for booked appointments.
    - Persist chat history in an in-memory `CHAT_HISTORY` list.
  - Lab report upload endpoint (`/upload-report`) runs OCR on an image using `OCRService` and then uses `LabAnalyzer` + Gemini for structured extraction and friendly summaries.
  - Medicine-related endpoints (`/medicine/add`, `/medicine/take/{med_id}`) leverage `AdherenceSystem` to track medication logs, calculate compliance, generate refill reminders, and flag low adherence.
  - Dashboard endpoint (`/dashboard`) pulls together:
    - PCP triage cases from Mongo `onco_cases` filtered by patient email.
    - Additional medical timeline entries from `medical_timeline`.
    - AI-derived insights and QR codes via `AIInsights` and `QRCodeGenerator`.

- **FHIR client (`fhir_client.py`)**
  - Minimal async client around the public HAPI FHIR server (`HAPI_FHIR_URL`) to create and fetch `Patient` and `Condition` resources, used when building longitudinal timelines.

- **AI and analytics helpers**
  - `chatbot.py` — Gemini-powered intent extraction with keyword-based fallbacks, and `CalendarService` for (mocked) calendar integration.
  - `lab_report.py` — OCR + Gemini-based lab analysis plus rule-based normal/low/high classification for common lab values.
  - `dashboard.py` — `TimelineAggregator` produces a simplified FHIR-derived event timeline; `AIInsights` wraps Gemini to generate risk score and suggested next steps; `QRCodeGenerator` encodes dashboard/profile URLs as base64 PNG data URIs for display in the UI.
  - `medicine.py` — holds the core medication adherence logic.

These components together form the "patient hub" that surfaces AI and integration features in a cohesive view.

### Templates and static assets

- The HTML UI lives under `templates/` and is rendered by FastAPI/Jinja2 for all three roles (PCP, oncologist, patient), with key pages like `index.html`, `pcp_dashboard.html`, `oncologist_dashboard.html`, patient login/register/dashboard/portal/symptoms, and AI diagnostics views.
- Styling is centralized in `static/medical-theme.css` (a redesigned professional medical theme) and related static assets under `static/`.
- Uploaded imaging files are stored under `static/uploads/` and linked in templates for preview.

### Deployment notes (from `DEPLOYMENT.md`)

- Render (or similar) typically hosts the **Node.js frontend** using:
  - Build command: `npm install`
  - Start command: `node server.js`
- The **Python AI backend** is expected to run separately (locally or hosted), exposed via something like `ngrok http 8000`, and referenced by the frontend through `AI_BACKEND_URL`.

When modifying deployment behavior, keep the `DEPLOYMENT.md` contract in sync with any changes to `server.js` or `app_main.py` so that the two services continue to cooperate correctly.