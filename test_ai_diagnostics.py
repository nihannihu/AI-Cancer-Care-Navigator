import requests
import json

url = "http://localhost:8000/api/analyze-symptoms"
data = {
    "text": "I feel nauseous after my chemo yesterday. Is this normal?"
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response Headers: {response.headers}")
print(f"Response: {response.text}")