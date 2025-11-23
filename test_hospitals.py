import requests
import json

url = "http://localhost:8000/emergency-hospitals"
data = {
    "latitude": 17.4243,
    "longitude": 78.4312
}

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")