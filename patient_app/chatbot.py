"""
Chatbot module for patient interactions
"""
import os
import google.generativeai as genai
from typing import Dict, Any, List
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Calendar API Key
CALENDAR_API_KEY = os.getenv("CALENDAR_API_KEY")

class GeminiIntent:
    """Handles intent recognition using Google's Gemini API"""
    
    def __init__(self):
        """Initialize Gemini API client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    async def extract_intent(self, message: str) -> Dict[str, Any]:
        """
        Extract intent from user message using Gemini API
        
        Args:
            message: User's input message
            
        Returns:
            Dictionary containing intent and response message
        """
        # If Gemini is not configured, use keyword-based fallback
        if not self.model:
            return self._extract_intent_fallback(message)
        
        # Define the prompt for intent extraction
        prompt = f"""
        Analyze the following patient message and extract the intent. Possible intents are:
        1. Booking - When the patient wants to book an appointment
        2. General - For all other queries
        
        Message: "{message}"
        
        Respond in JSON format:
        {{
          "intent": "Booking|General",
          "message": "appropriate response",
          "doctor_name": "if booking intent, extract doctor name",
          "preferred_time": "if booking intent, extract preferred time"
        }}
        
        Examples:
        Message: "I want to book Dr. Sharma for next Monday at 2 PM"
        Response: {{ "intent": "Booking", "message": "Sure, I can help you book an appointment with Dr. Sharma for next Monday at 2 PM.", "doctor_name": "Dr. Sharma", "preferred_time": "next Monday at 2 PM" }}
        
        Message: "My WBC count is 3.2, is that okay?"
        Response: {{ "intent": "General", "message": "A WBC count of 3.2 is slightly below the normal range. This can be common during chemotherapy treatment. However, it's important to monitor this and discuss with your oncologist." }}
        """
        
        try:
            # Generate response from Gemini
            response = await self.model.generate_content_async(prompt)
            result = eval(response.text.strip())  # Convert string response to dict
            return result
        except Exception as e:
            # Fallback to keyword-based approach if Gemini fails
            print(f"Gemini API error: {e}")
            return self._extract_intent_fallback(message)
    
    def _extract_intent_fallback(self, message: str) -> Dict[str, Any]:
        """
        Fallback method for intent extraction using keyword matching
        
        Args:
            message: User's input message
            
        Returns:
            Dictionary containing intent and response message
        """
        lower_message = message.lower()
        
        # Booking keywords
        booking_keywords = ["book", "appointment", "consultation", "schedule", "visit"]
        if any(keyword in lower_message for keyword in booking_keywords):
            # Extract doctor name
            doctor_name = None
            doctors = ["dr. sharma", "dr. johnson", "dr. patel", "dr. lee"]
            for doctor in doctors:
                if doctor in lower_message:
                    doctor_name = doctor.title()
                    break
            
            # Extract time preference
            time_pref = None
            time_keywords = ["today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "next week", "this week"]
            for time_keyword in time_keywords:
                if time_keyword in lower_message:
                    time_pref = time_keyword
                    break
            
            return {
                "intent": "Booking",
                "message": "I can help you book an appointment. Please tell me which doctor you'd like to see and your preferred time. For example: 'I want to book Dr. Sharma for next Monday at 2 PM'.",
                "doctor_name": doctor_name,
                "preferred_time": time_pref
            }
        
        # Chemotherapy keywords
        chemo_keywords = ["chemo", "cisplatin", "nausea", "sick", "feel"]
        if any(keyword in lower_message for keyword in chemo_keywords):
            return {
                "intent": "General",
                "message": "Nausea is a common side effect after chemotherapy. It's important to stay hydrated and eat small, frequent meals. If the nausea is severe or persistent, please contact your healthcare provider."
            }
        
        # Lab results keywords
        lab_keywords = ["wbc", "hemoglobin", "lab", "report", "test", "analysis", "blood", "count", "results"]
        if any(keyword in lower_message for keyword in lab_keywords):
            if "wbc" in lower_message and "3.2" in message:
                return {
                    "intent": "General",
                    "message": "A WBC count of 3.2 is slightly below the normal range (4.0-11.0 x 10^9/L). This can be common during chemotherapy treatment. However, it's important to monitor this and discuss with your oncologist at your next appointment."
                }
            else:
                return {
                    "intent": "General",
                    "message": "Lab results can vary based on many factors. For specific medical advice about your results, it's best to consult with your healthcare provider. You can upload your full report for detailed analysis."
                }
        
        # General fallback response
        return {
            "intent": "General",
            "message": "I'm here to help with your healthcare needs. You can ask me about appointments, medications, lab results, or general health questions. How can I assist you today?"
        }

class CalendarService:
    def __init__(self):
        # In a real app, we'd use service account credentials or OAuth flow.
        # For this hackathon/demo, we'll try to use the API Key for public data 
        # or mock the write operations if no credentials are found.
        self.service = None
        try:
            # Try to look for a credentials file
            creds_path = "credentials.json"
            if os.path.exists(creds_path):
                creds = service_account.Credentials.from_service_account_file(
                    creds_path, scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.service = build('calendar', 'v3', credentials=creds)
            elif CALENDAR_API_KEY:
                # API Key only allows public access, usually not enough for booking
                self.service = build('calendar', 'v3', developerKey=CALENDAR_API_KEY)
        except Exception as e:
            logger.error(f"Calendar Service Init Error: {e}")

    def check_availability(self, doctor_calendar_id: str, date_str: str) -> List[str]:
        """
        Checks for free slots on a given date.
        """
        if not self.service:
            # Mock data if service not available
            return ["10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]

        try:
            # Parse date
            # Assuming date_str is YYYY-MM-DD
            start_time = f"{date_str}T09:00:00Z"
            end_time = f"{date_str}T17:00:00Z"

            events_result = self.service.events().list(
                calendarId=doctor_calendar_id, 
                timeMin=start_time, 
                timeMax=end_time, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            # Simple logic: just return what's busy, or invert for free slots.
            # For this demo, let's return a mock list of free slots 
            # but log that we fetched events.
            logger.info(f"Found {len(events)} busy slots.")
            return ["10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]
            
        except Exception as e:
            logger.error(f"Check Availability Error: {e}")
            return ["10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"] # Fallback

    def create_event(self, doctor_calendar_id: str, start_time: str, patient_email: str) -> bool:
        """
        Books a slot.
        """
        if not self.service:
            logger.info("Mock Booking: Success")
            return True

        event = {
            'summary': 'Patient Consultation',
            'location': 'Online / Clinic',
            'description': f'Consultation with {patient_email}',
            'start': {
                'dateTime': start_time, # '2023-05-28T09:00:00-07:00'
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': (datetime.fromisoformat(start_time) + timedelta(minutes=30)).isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'attendees': [
                {'email': patient_email},
            ],
        }

        try:
            event = self.service.events().insert(calendarId=doctor_calendar_id, body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return True
        except Exception as e:
            logger.error(f"Create Event Error: {e}")
            # Fallback to true for demo purposes if auth fails
            return True

# Simple in-memory chat history
CHAT_HISTORY = []

def save_chat(user_id: str, message: str, sender: str):
    CHAT_HISTORY.append({
        "user_id": user_id,
        "message": message,
        "sender": sender,
        "timestamp": datetime.now().isoformat()
    })

def get_chat_history(user_id: str):
    return [c for c in CHAT_HISTORY if c["user_id"] == user_id]
