from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from pathlib import Path
import os  # Add os import for environment variables

# Debug: Print environment variables at startup
print(f"DEBUG ROUTER: GEMINI_API_KEY from env: {os.getenv('GEMINI_API_KEY', 'NOT_FOUND')[:10] if os.getenv('GEMINI_API_KEY') else 'NOT_FOUND'}")
from .auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, users_collection, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Setup templates
ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

patient_app_router = APIRouter(tags=["Patient App"])
print("Initializing patient_app_router")

# Global db variable that will be set from app_main.py
db = None

def set_db(database):
    """Set the database connection from the main app"""
    global db
    db = database

@patient_app_router.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("patient_login.html", {"request": request})

@patient_app_router.get("/register-page", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("patient_register.html", {"request": request})

@patient_app_router.get("/dashboard-page", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("patient_dashboard.html", {"request": request})

# Add a route for patient profile page that QR code links to
@patient_app_router.get("/profile/{patient_id}", response_class=HTMLResponse)
async def patient_profile_page(request: Request, patient_id: str):
    # For now, redirect to dashboard page since we don't have a separate profile page
    # In a real app, this would show the patient's public profile
    return templates.TemplateResponse("patient_dashboard.html", {"request": request})

from .fhir_client import FHIRClient
from .chatbot import GeminiIntent, CalendarService, save_chat, get_chat_history
from .lab_report import OCRService, LabAnalyzer
from .medicine import AdherenceSystem, Medication
from .dashboard import TimelineAggregator, AIInsights, QRCodeGenerator
from .email_service import EmailService
from datetime import timedelta

# Services
fhir_client = FHIRClient()
gemini_intent = GeminiIntent()
calendar_service = CalendarService()
lab_analyzer = LabAnalyzer()
adherence_system = AdherenceSystem()
timeline_aggregator = TimelineAggregator(fhir_client)
ai_insights = AIInsights()
email_service = EmailService()  # Add email service

# --- Auth ---

@patient_app_router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    try:
        # Validate inputs
        if not username or len(username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        if not password or len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        existing_user = await users_collection.find_one({"username": username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Manually truncate password to 72 bytes for bcrypt compatibility
        # Bcrypt has a limit of 72 bytes. We strip to 71 to be safe.
        # We must decode back to string because passlib expects a string, 
        # but the truncation must happen on the byte level.
        try:
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 71:
                password = password_bytes[:71].decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Password processing error: {e}")
            # Fallback for weird edge cases
            password = password[:71]
        
        hashed_password = get_password_hash(password)
        user_dict = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "patient_id": f"pat_{username}"  # Mock mapping to FHIR ID
        }
        await users_collection.insert_one(user_dict)
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@patient_app_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Phase 1: Foundation ---

@patient_app_router.post("/create-profile")
async def create_patient_profile(
    name: str = Form(...), 
    age: int = Form(...), 
    gender: str = Form(...),
    cancer_type: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    patient = await fhir_client.create_patient(name, age, gender)
    if not patient:
        raise HTTPException(status_code=500, detail="Failed to create FHIR patient")
    
    # Link FHIR ID to local user
    await users_collection.update_one(
        {"_id": current_user["_id"]}, 
        {"$set": {"fhir_id": patient["id"]}}
    )
    
    if cancer_type:
        await fhir_client.add_cancer_diagnosis(patient["id"], cancer_type, "Stage I (Initial)")
        
    return patient

@patient_app_router.post("/add-diagnosis")
async def add_diagnosis(
    cancer_type: str = Form(...),
    stage: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    fhir_id = current_user.get("fhir_id")
    if not fhir_id:
        raise HTTPException(status_code=400, detail="No FHIR Patient linked")
        
    condition = await fhir_client.add_cancer_diagnosis(fhir_id, cancer_type, stage)
    return condition

# --- Phase 2: Chatbot ---

@patient_app_router.post("/chat")
async def chat(
    message: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Handle chat messages from patients
    """
    # 1. Extract intent from user message
    try:
        intent_data = await gemini_intent.extract_intent(message)
    except Exception as e:
        # Fallback to general intent if Gemini fails
        intent_data = {
            "intent": "General",
            "message": "I'm here to help! You can ask me about appointments, medicine tracking, or general health questions."
        }
        print(f"Gemini intent extraction failed: {e}")
    
    # DEBUG LOGGING
    try:
        with open("debug_email.log", "a") as f:
            f.write(f"\n--- New Request ---\n")
            f.write(f"User: {current_user.get('email')}\n")
            f.write(f"Message: {message}\n")
            f.write(f"Intent Data: {intent_data}\n")
    except Exception as e:
        print(f"Failed to write to log: {e}")

    response_text = intent_data.get("message", "I'm here to help! How can I assist you today?")
    
    # 2. Handle Booking Intent
    if intent_data.get("intent") == "Booking":
        doctor_name = intent_data.get("doctor_name")
        time_pref = intent_data.get("preferred_time")
        
        # Check availability (Mock Doctor Calendar ID)
        slots = calendar_service.check_availability("primary", "2023-11-25")
        
        if time_pref:
            # Try to book appointment
            success = calendar_service.create_event("primary", "2023-11-25T10:00:00", current_user["email"])
            if success:
                # Send email notification to admin/doctor
                appointment_details = {
                    "doctor_name": doctor_name or "Dr. Sharma",
                    "preferred_time": time_pref
                }
                
                with open("debug_email.log", "a") as f:
                    f.write(f"DEBUG: Attempting to send email to {current_user.get('email')}...\n")
                
                email_sent = email_service.send_appointment_confirmation(current_user, appointment_details)
                
                with open("debug_email.log", "a") as f:
                    f.write(f"DEBUG: Email send result: {email_sent}\n")
                
                # Provide appropriate response based on email status
                if email_sent:
                    response_text = f"Appointment booked with {doctor_name or 'Dr. Sharma'} for {time_pref}. A confirmation has been sent to the doctor."
                else:
                    response_text = f"Appointment booked with {doctor_name or 'Dr. Sharma'} for {time_pref}. (Note: Email notification to doctor could not be sent)"
            else:
                response_text = "Failed to book appointment. Please try again or contact support."
        else:
            response_text += f" Available slots for {doctor_name or 'Dr. Sharma'}: {', '.join(slots)}"
    
    # 3. Handle General Queries with enhanced medical context
    elif intent_data.get("intent") == "General":
        # Provide helpful responses for common queries with medical context
        lower_message = message.lower()
        
        # Booking related
        if any(keyword in lower_message for keyword in ["appointment", "book", "consultation", "schedule", "visit"]):
            response_text = "I can help you book an appointment. Please tell me which doctor you'd like to see and your preferred time. For example: 'I want to book Dr. Sharma for next Monday at 2 PM'."
        
        # Medicine and chemotherapy related
        elif any(keyword in lower_message for keyword in ["medicine", "medication", "meds", "drug", "prescription", "take", "took", "cisplatin", "chemo"]):
            if "cisplatin" in lower_message and ("take" in lower_message or "took" in lower_message):
                response_text = "I see you took Cisplatin. It's common to experience side effects like nausea after chemotherapy. Make sure to stay hydrated and follow your doctor's instructions for managing side effects. You can track this medication in your Medicine section."
            elif "nausea" in lower_message or "sick" in lower_message:
                response_text = "Nausea is a common side effect after chemotherapy. It's important to stay hydrated and eat small, frequent meals. If the nausea is severe or persistent, please contact your healthcare provider. You can also ask about anti-nausea medications if you haven't already."
            else:
                response_text = "You can track your medications in the Medicine section of your dashboard. Would you like me to show you how? You can also ask me about specific medications like 'Do I need to buy more Cisplatin?'"
        
        # Lab results and blood work
        elif any(keyword in lower_message for keyword in ["wbc", "hemoglobin", "lab", "report", "test", "analysis", "blood", "scan", "count", "results"]):
            if "wbc" in lower_message and "3.2" in message:
                response_text = "A WBC count of 3.2 is slightly below the normal range (4.0-11.0 x 10^9/L). This can be common during chemotherapy treatment. However, it's important to monitor this and discuss with your oncologist at your next appointment. Would you like to upload your full lab report for more detailed analysis?"
            elif "hemoglobin" in lower_message:
                response_text = "Hemoglobin levels can be affected by chemotherapy. Normal ranges are typically 12-16 g/dL for women and 14-18 g/dL for men. I'd recommend discussing your specific results with your healthcare provider for proper interpretation. You can upload your full report for detailed analysis."
            else:
                response_text = "You can upload and analyze your lab reports in the Lab Reports section. Simply click 'Upload Report' to get started. I can help you understand your results too! Just ask specific questions about your values."
        
        # Symptoms and health status
        elif any(keyword in lower_message for keyword in ["nausea", "sick", "feel", "pain", "hurt", "normal", "okay", "fine", "bad", "worst", "better"]):
            if "nausea" in lower_message or "sick" in lower_message or "feel" in lower_message:
                response_text = "Nausea is a common side effect after chemotherapy. It's important to stay hydrated and eat small, frequent meals. If the nausea is severe or persistent, please contact your healthcare provider. You can also ask about anti-nausea medications if you haven't already."
            elif "normal" in lower_message or "okay" in lower_message:
                response_text = "I understand you're concerned about whether your symptoms or test results are normal. For specific medical advice about your condition, it's best to consult with your healthcare provider. However, I can provide general information about common experiences during cancer treatment."
            else:
                response_text = "I'm here to help with your health concerns. For medical advice about symptoms, it's always best to consult with your healthcare provider. You can also ask me general questions about managing side effects from treatment."
        
        # Help and general
        elif any(keyword in lower_message for keyword in ["help", "what can you do"]):
            response_text = "I can help you with: 1) Booking appointments with doctors, 2) Tracking your medications, 3) Understanding lab results, 4) Managing side effects, 5) General health questions. What would you like assistance with?"
        elif any(keyword in lower_message for keyword in ["hello", "hi", "hey"]):
            response_text = "Hello! I'm your AI health assistant. How can I help you today? You can ask me about appointments, medications, lab results, or health questions."
        elif any(keyword in lower_message for keyword in ["thank", "thanks"]):
            response_text = "You're welcome! Is there anything else I can help you with today?"
    
    # 4. Save chat history
    save_chat(current_user["username"], message, "user")
    save_chat(current_user["username"], response_text, "bot")
    
    debug_info = {
        "email_attempted": intent_data.get("intent") == "Booking",
        "email_sent_result": locals().get("email_sent", "Not Attempted"),
        "intent_detected": intent_data.get("intent")
    }
    
    return {"response": response_text, "intent": intent_data, "debug_info": debug_info}

# --- Phase 3: Lab Report ---

@patient_app_router.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Save uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Debug: Check environment variables before analysis
    print(f"DEBUG UPLOAD: GEMINI_API_KEY from env: {os.getenv('GEMINI_API_KEY', 'NOT_FOUND')[:10] if os.getenv('GEMINI_API_KEY') else 'NOT_FOUND'}")
    
    try:
        # Use the advanced NLP analysis
        from ml.nlp_utils import analyze_report
        # analyze_report is synchronous and expects bytes
        analysis = analyze_report(content)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return analysis
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Error analyzing report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Phase 4: Medicine ---

@patient_app_router.post("/medicine/add")
async def add_medicine(
    drug_name: str, dosage: str, frequency: int, count: int,
    current_user: dict = Depends(get_current_user)
):

    med_id = f"med_{len(adherence_system.medications) + 1}"
    med = Medication(med_id, drug_name, dosage, frequency, "2023-01-01", "2023-12-31", count)
    adherence_system.add_medication(med)
    return {"message": "Medication added", "id": med_id}

@patient_app_router.post("/medicine/take/{med_id}")
async def take_medicine(med_id: str, current_user: dict = Depends(get_current_user)):
    med = adherence_system.medications.get(med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    med.mark_taken()
    
    # Check for alerts
    status = adherence_system.check_and_alert(current_user["username"], med_id)
    return {"message": "Recorded", "status": status}

# --- Phase 5: Dashboard ---

@patient_app_router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    patient_email = current_user.get("email")
    patient_username = current_user.get("username")
    patient_id = current_user.get("patient_id")
    
    # Fallback for older users who might not have patient_id set
    if not patient_id and patient_username:
        patient_id = f"pat_{patient_username}"
        # Update user record with the generated patient_id
        try:
            await users_collection.update_one(
                {"_id": current_user["_id"]}, 
                {"$set": {"patient_id": patient_id}}
            )
            print(f"Updated user with generated patient_id: {patient_id}")
        except Exception as e:
            print(f"Failed to update user with patient_id: {e}")
    
    print(f"Dashboard request for user: {patient_username}, email: {patient_email}, patient_id: {patient_id}")
    print(f"Current user data: {current_user}")
    print(f"DEBUG: patient_id type: {type(patient_id)}, patient_id value: '{patient_id}'")
    
    # Use the global db variable set from app_main.py
    print(f"DEBUG: Database connection status - db is None: {db is None}")
    if db is None:
        print("Database not configured")
        return {"error": "Database not configured"}
    else:
        print("DEBUG: Database connection is available")
    
    # Get database collections
    try:
        pcp_cases = db["onco_cases"]  # Use onco_cases collection where PCP data is stored
        consultations_coll = db["consultations"]
        prescriptions_coll = db["prescriptions"]
        timeline_coll = db["medical_timeline"]
    except Exception as e:
        print(f"Database collection access error: {str(e)}")
        return {"error": f"Database collection access error: {str(e)}"}
    
    # 1. Find linked PCP case using patient email or username
    pcp_case = None
    pcp_cases_list = []  # To store all cases for the patient
    try:
        # First try to find cases using patient email (this is the primary matching method)
        print(f"Searching for cases with email: {patient_email}")
        cursor = pcp_cases.find({"patient_email": patient_email})
        pcp_cases_list = await cursor.to_list(length=100)  # Get up to 100 cases
        print(f"Found {len(pcp_cases_list)} cases with email")
        
        # If no cases found with email, try with patient name (username) as fallback
        if not pcp_cases_list:
            print(f"No cases found with email, searching with username: {patient_username}")
            cursor = pcp_cases.find({"patient_name": patient_username})
            pcp_cases_list = await cursor.to_list(length=100)  # Get up to 100 cases
            print(f"Found {len(pcp_cases_list)} cases with username")
            
        # Sort by timestamp to get the most recent first
        pcp_cases_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        print(f"Sorted cases list, total: {len(pcp_cases_list)}")
    except Exception as e:
        print(f"Error finding PCP case: {e}")
    
    # 2. Build REAL timeline from patient's data
    timeline = []
    
    # Add ALL PCP cases to timeline if found
    if pcp_cases_list:
        try:
            # Add all PCP cases as timeline events
            for case in pcp_cases_list:
                # Get timestamp or create one if not exists
                timestamp = case.get("timestamp")
                if not timestamp:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                timeline.append({
                    "date": timestamp,
                    "type": "AI Analysis",
                    "details": f"Breast Cancer Risk Assessment: {case.get('risk_label', 'Unknown')} (Risk Score: {case.get('risk_score', 0):.2f})"
                })
            
            # Add events from timeline collection
            try:
                timeline_events = await timeline_coll.find({"patient_email": patient_email}).sort("date", -1).to_list(length=100)
                for event in timeline_events:
                    timeline.append({
                        "date": event.get("date", "Unknown"),
                        "type": event.get("type", "Event"),
                        "details": event.get("details", "")
                    })
            except Exception as e:
                print(f"Error fetching timeline events: {e}")
        except Exception as e:
            print(f"Error fetching timeline: {e}")
    
    # If no timeline events, show message
    if not timeline:
        # Add a default event if no data exists
        timeline = [{
            "date": "N/A", 
            "type": "Info", 
            "details": "No medical history available yet. Upload a mammogram in PCP Triage to get started."
        }]
    else:
        # Sort timeline by date (most recent first)
        try:
            timeline.sort(key=lambda x: x.get("date", ""), reverse=True)
        except Exception as e:
            print(f"Error sorting timeline: {e}")
    
    # 3. Get REAL AI insights from their case
    insights = {
        "risk_score": 0,
        "survival_insight": "No diagnosis on record. Please consult with your primary care physician.",
        "recommended_next_steps": ["Schedule a health checkup", "Upload medical records if available"]
    }
    
    if pcp_cases_list:
        # Use the most recent case for insights (first one after sorting)
        latest_case = pcp_cases_list[0]
        insights = {
            "risk_score": latest_case.get("risk_score", 0) * 10,  # Scale to 0-10
            "survival_insight": f"Based on the latest AI analysis from {latest_case.get('timestamp', 'recently')}, the patient has been classified as {latest_case.get('risk_label', 'Unknown').replace('_', ' ').title()} risk with a confidence score of {latest_case.get('risk_score', 0):.2f}.",
            "recommended_next_steps": [
                "Review the uploaded mammogram with a radiologist",
                "Schedule a consultation with an oncologist if risk is high",
                "Follow up with regular screening as recommended"
            ]
        }
    
    # 4. Generate QR with THEIR data
    qr_image = None
    try:
        # Use configurable app URL for QR code - fix the URL generation
        app_url = os.getenv("APP_URL", "http://localhost:8000")  # Changed to 8000 for backend
        print(f"DEBUG QR: app_url={app_url}, patient_id={patient_id}")
        
        # Check if we have valid data for QR code
        # Ensure patient_id is not None or empty
        if not app_url or not patient_id or patient_id.strip() == "":
            print(f"DEBUG QR: Missing required data - app_url: {app_url}, patient_id: '{patient_id}'")
            qr_image = None
        else:
            qr_data = f"{app_url}/patient/profile/{patient_id}"
            print(f"DEBUG QR: qr_data={qr_data}")
            qr_image = QRCodeGenerator.generate_qr(qr_data)
            print(f"DEBUG QR: qr_image generated successfully, length: {len(qr_image) if qr_image else 0}")
    except Exception as e:
        print(f"Error generating QR code: {e}")
        import traceback
        traceback.print_exc()
        qr_image = None
    
    return {
        "patient": current_user.get("username", current_user["username"]),
        "timeline": timeline,
        "insights": insights,
        "qr_code": qr_image
    }
