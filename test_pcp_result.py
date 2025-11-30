import requests

# Test uploading a mammogram through PCP triage to see the enhanced results page
upload_url = "http://127.0.0.1:8000/pcp/upload"

# Data for the PCP upload form
data = {
    "patient_name": "Test Patient",
    "patient_email": "test@example.com",
    "patient_phone": "123-456-7890"
}

# The mammogram image file
files = {
    "file": ("test_mammogram.jpg", open("test_mammogram.jpg", "rb"), "image/jpeg")
}

print("Uploading mammogram through PCP triage to test enhanced results page...")
try:
    response = requests.post(upload_url, data=data, files=files)
    print(f"Upload Status: {response.status_code}")
    
    # Check if we got the enhanced results page
    if response.status_code == 200:
        content = response.text
        if "AI Breast Cancer Analysis Result" in content:
            print("✅ Successfully got the enhanced PCP results page!")
            if "risk-score" in content:
                print("✅ Risk score is prominently displayed")
            if "stage-badge" in content:
                print("✅ Cancer stage is highlighted with badge styling")
            if "benign-result" in content or "malignant-result" in content:
                print("✅ Malignancy/Benign classification is clearly highlighted")
        else:
            print("❌ Did not get the expected results page")
    else:
        print(f"❌ Upload failed with status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
except Exception as e:
    print(f"Upload Error: {e}")
finally:
    files["file"][1].close()

print("\nTest completed.")