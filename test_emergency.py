import requests
import json

url = "http://localhost:8000/emergency-hospitals"
data = {
    "latitude": 17.4243,
    "longitude": 78.4312
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")