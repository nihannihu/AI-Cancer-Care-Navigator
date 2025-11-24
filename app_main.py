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
            # Return mock response when API key is reported as leaked
            return JSONResponse({
                "analysis": f"Mock analysis of symptoms: {text}\n\nNote: The provided Gemini API key has been reported as leaked. Please generate a new API key from the Google Cloud Console for real AI analysis."
            })
        
        # Use gemini-2.5-flash model which is available
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": f"Analyze these symptoms: {text}"}]}]}
        print(f"Requesting URL: {url}")  # Debug output
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30.0)
                print(f"Gemini API Response Status: {response.status_code}")  # Debug output
                print(f"Gemini API Response Text: {response.text}")  # Debug output
                
                # Check if response is JSON
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    print(f"Non-JSON response received. Content-Type: {content_type}")
                    return JSONResponse({"error": f"Invalid response from Gemini API. Expected JSON, got {content_type}. Response: {response.text[:200]}"}, status_code=response.status_code)
                
            if response.status_code != 200:
                return JSONResponse({"error": f"API Error: {response.text}"}, status_code=response.status_code)
            
            try:
                data = response.json()
            except Exception as json_error:
                print(f"Error parsing JSON response: {json_error}")
                return JSONResponse({"error": f"Failed to parse JSON response from Gemini API: {str(json_error)}. Response text: {response.text[:200]}"}, status_code=500)
            
            # Check if response has the expected structure
            if "candidates" not in data or not data["candidates"]:
                return JSONResponse({"error": f"Unexpected response structure from Gemini API: {data}"}, status_code=500)
                
            analysis = data["candidates"][0]["content"]["parts"][0]["text"]
            return JSONResponse({"analysis": analysis})
        except httpx.TimeoutException:
            print("Gemini API request timed out")
            return JSONResponse({"error": "Request to Gemini API timed out. Please try again."}, status_code=500)
        except httpx.RequestError as e:
            print(f"Gemini API request error: {e}")
            return JSONResponse({"error": f"Failed to connect to Gemini API: {str(e)}"}, status_code=500)
        except Exception as e:
            print(f"Unexpected error in AI diagnostics: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse({"error": f"Unexpected error: {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# To run: uvicorn app_main:app --reload
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_main:app", host=host, port=port, reload=True)