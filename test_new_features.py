import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    print("Testing Image Analysis Endpoint...")
    # Mock image upload
    try:
        files = {'file': ('test.jpg', b'fake image data', 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/api/analyze-image", files=files)
        if response.status_code == 200:
            print("✅ Image Analysis: Success")
            print(response.json())
        else:
            print(f"❌ Image Analysis: Failed ({response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"❌ Image Analysis: Error {e}")

    print("\nTesting Report Analysis Endpoint...")
    try:
        files = {'file': ('test.pdf', b'%PDF-1.4 fake pdf content', 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/analyze-report", files=files)
        if response.status_code == 200:
            print("✅ Report Analysis: Success")
            print(response.json())
        else:
            print(f"❌ Report Analysis: Failed ({response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"❌ Report Analysis: Error {e}")

    print("\nTesting Outcome Prediction Endpoint...")
    try:
        data = {"age": 65, "stage": 2, "comorbidities": 1}
        response = requests.post(f"{BASE_URL}/api/predict-outcome", json=data)
        if response.status_code == 200:
            print("✅ Outcome Prediction: Success")
            print(response.json())
        else:
            print(f"❌ Outcome Prediction: Failed ({response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"❌ Outcome Prediction: Error {e}")

    print("\nTesting Side Effect Prediction Endpoint...")
    try:
        data = {"age": 45, "chemo_type": 1, "dosage": 0.8}
        response = requests.post(f"{BASE_URL}/api/predict-side-effects", json=data)
        if response.status_code == 200:
            print("✅ Side Effect Prediction: Success")
            print(response.json())
        else:
            print(f"❌ Side Effect Prediction: Failed ({response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"❌ Side Effect Prediction: Error {e}")

if __name__ == "__main__":
    test_endpoints()
