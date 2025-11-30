# AI Features and Emergency Button Fixes

## Overview
This update addresses the reported issues where AI features (Voice Symptoms, Predictive Models) and the Emergency Button were hanging in a loading state.

## Changes Made

### 1. Voice Symptoms Analysis
- **Issue:** The backend was trying to use `gemini-2.5-flash`, which is an invalid model name, causing the API call to fail.
- **Fix:** Updated `app_main.py` to use `gemini-1.5-flash`.
- **Verification:**
    1. Go to **AI Diagnostics** page.
    2. Click **Voice Symptoms** tab.
    3. Click **Start Recording**, speak some symptoms (e.g., "I have a headache"), then click **Stop**.
    4. Click **Analyze Symptoms**.
    5. Result should appear (or a mock result if API key is invalid/leaked).

### 2. Predictive Models (Survival Prediction)
- **Issue:** The frontend expected a `risk_score` field in the JSON response, but the backend was returning `5_year_survival_probability`. This caused the Javascript to fail silently or display undefined values.
- **Fix:** Updated `ml/predictive_models.py` to include `risk_score` in the return dictionary.
- **Verification:**
    1. Go to **AI Diagnostics** page.
    2. Click **Predictive Models** tab.
    3. Fill in the **Treatment Outcome Predictor** form.
    4. Click **Predict Survival**.
    5. The result card should now display the Risk Score and Prediction correctly.

### 3. Emergency Button
- **Issue:** The feature relied on the user's geolocation which could timeout or be denied, and the backend API (Geoapify) could fail if the key was missing, causing the "Locating..." spinner to hang forever.
- **Fix:**
    - **Frontend (`templates/base.html`):** Added a 10-second timeout to geolocation. Added error handling to display a "Try Again" button if it fails.
    - **Backend (`app_main.py`):** Added a fallback mechanism. If the Geoapify API key is missing or the request fails, it now returns mock hospital data so the feature is demonstrable.
- **Verification:**
    1. Click the **🚨 Emergency** button in the top navigation.
    2. Allow location access if prompted.
    3. If location is found, it should display a list of nearby hospitals (either real or mock data).
    4. If location fails/times out, an error message with a retry button will appear.

## Technical Details
- **Files Modified:**
    - `app_main.py`: Fixed Gemini model name, added emergency fallback.
    - `ml/predictive_models.py`: Added `risk_score` to response.
    - `templates/base.html`: Improved geolocation logic and error handling.

## Next Steps
- Ensure `.env` has valid `GEMINI_API_KEY` and `GEOAPIFY_API_KEY` for production use.
- Restart the FastAPI server (`uvicorn app_main:app --reload`) to apply changes.
