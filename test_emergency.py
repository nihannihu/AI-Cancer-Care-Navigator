import requests
import json

# Test the emergency hospital API
url = "http://localhost:8000/emergency-hospitals"
data = {
    "latitude": 40.7128,
    "longitude": -74.0060
}

print("Sending request to emergency hospital API...")
try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")