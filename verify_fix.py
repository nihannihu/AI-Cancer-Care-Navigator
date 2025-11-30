import requests
import json

try:
    print("Sending request to /api/book-ambulance...")
    resp = requests.post("http://localhost:8000/api/book-ambulance", json={"latitude": 12.9716, "longitude": 77.5946})
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
