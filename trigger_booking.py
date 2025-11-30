
import requests
import json

# Login first to get token
login_url = "http://localhost:8000/patient/login"
chat_url = "http://localhost:8000/patient/chat"

import random
import string

# Generate random username
rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
username = f"testuser_{rand_suffix}"
print(f"Using username: {username}")

# Create a test user first (if not exists)
register_url = "http://localhost:8000/patient/register"
requests.post(register_url, data={"username": username, "password": "password123", "email": "nihanmohammed95@gmail.com"})

# Login
session = requests.Session()
response = session.post(login_url, data={"username": username, "password": "password123"})
if response.status_code != 200:
    print(f"Login failed: {response.text}")
    exit()

token = response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Send Booking Message
print("Sending booking request...")
booking_msg = "I want to book an appointment with Dr. Sharma for tomorrow at 10 AM"
response = session.post(chat_url, data={"message": booking_msg}, headers=headers)

print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {data}")
if "debug_info" in data:
    print(f"DEBUG INFO: {data['debug_info']}")
