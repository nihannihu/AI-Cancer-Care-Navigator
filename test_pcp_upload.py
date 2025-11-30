import requests

# Test uploading a mammogram through PCP triage
upload_url = "http://127.0.0.1:8000/pcp/upload"

# Data for the PCP upload form
data = {
    "patient_name": "testuser",
    "patient_email": "testuser@example.com",
    "patient_phone": "123-456-7890"
}

# The mammogram image file
files = {
    "file": ("test_mammogram.jpg", open("test_mammogram.jpg", "rb"), "image/jpeg")
}

print("Uploading mammogram through PCP triage...")
try:
    response = requests.post(upload_url, data=data, files=files)
    print(f"Upload Status: {response.status_code}")
    print(f"Upload Response: {response.text[:200]}...")  # First 200 characters
except Exception as e:
    print(f"Upload Error: {e}")
finally:
    files["file"][1].close()

print("\nTest completed.")