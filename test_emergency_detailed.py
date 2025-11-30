import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.python", override=True)

# Test the emergency hospital API
url = "http://localhost:8000/emergency-hospitals"
data = {
    "latitude": 40.7128,
    "longitude": -74.0060
}

# Check if Geoapify API key is loaded
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key loaded: {GEOAPIFY_API_KEY[:10] if GEOAPIFY_API_KEY else None}")

print("Sending request to emergency hospital API...")
try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")