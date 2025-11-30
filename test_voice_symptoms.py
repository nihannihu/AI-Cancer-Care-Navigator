import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Gemini API Key exists: {bool(GEMINI_API_KEY)}")
print(f"Key preview: {GEMINI_API_KEY[:15] + '...' if GEMINI_API_KEY else 'None'}")

if GEMINI_API_KEY:
    # Test the same endpoint that the voice symptoms feature uses
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{
                "text": "You are a medical assistant. Analyze the following symptoms and provide helpful medical insights: I have been experiencing persistent cough and chest pain for the past two weeks."
            }]
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\nTesting Voice Symptoms API call...")
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API Test Successful!")
            if "candidates" in data and len(data["candidates"]) > 0:
                analysis = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Response: {analysis[:300]}...")  # First 300 characters
                print("\nVoice Symptoms feature should be working correctly!")
            else:
                print("Unexpected response format")
                print(data)
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")
else:
    print("No Gemini API key found in environment variables")