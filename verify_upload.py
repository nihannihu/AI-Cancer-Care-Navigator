import requests
import os

BASE_URL = "http://localhost:8000"
USERNAME = "testuser_123"
PASSWORD = "Password123!"

def verify():
    # 1. Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/patient/login", data={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Upload Report
    print("Uploading report...")
    file_path = "test_report.pdf"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        files = {"file": ("test_report.pdf", f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/patient/upload-report", headers=headers, files=files)
    
    print(f"Upload Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    verify()
