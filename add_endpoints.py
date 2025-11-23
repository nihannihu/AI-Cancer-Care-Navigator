#!/usr/bin/env python3
with open('app_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '# To run: uvicorn app_main:app --reload'

if marker in content and '/api/analyze-image' not in content:
    endpoints = '''
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": f"Analyze these symptoms: {text}"}]}]}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30.0)
        if response.status_code != 200:
            return JSONResponse({"error": f"API Error: {response.text}"}, status_code=response.status_code)
        data = response.json()
        analysis = data["candidates"][0]["content"]["parts"][0]["text"]
        return JSONResponse({"analysis": analysis})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

'''
    content = content.replace(marker, endpoints + '\n' + marker)
    with open('app_main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Added all API endpoints!")
else:
    print("⚠️ Endpoints already exist or marker not found")
