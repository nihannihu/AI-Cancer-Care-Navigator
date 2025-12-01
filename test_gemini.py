import os
import httpx

# Use the new API key directly for testing
# GEMINI_API_KEY = "AIzaSyCKg3ur9DIN8oCMN02hZ06jA_GWb8CWbIQ"
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCKg3ur9DIN8oCMN02hZ06jA_GWb8CWbIQ")
print(f"New Gemini API Key: {GEMINI_API_KEY[:15] + '...' if GEMINI_API_KEY else 'None'}")

# First, let's list available models
print("\nListing available models...")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"

try:
    response = httpx.get(url, timeout=30.0)
    print(f"List Models Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Available models:")
        if "models" in data:
            for model in data["models"]:
                print(f"  - {model.get('name', 'Unknown')}: {model.get('displayName', 'No display name')}")
        else:
            print("Unexpected response format for models list")
            print(data)
    else:
        print(f"Error listing models: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error listing models: {e}")

# Try the gemini-2.5-flash model
print("\nTrying gemini-2.5-flash model...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
payload = {
    "contents": [{
        "parts": [{
            "text": "What are common symptoms of breast cancer?"
        }]
    }]
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("API Test Successful!")
        if "candidates" in data and len(data["candidates"]) > 0:
            analysis = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Response: {analysis[:200]}...")  # First 200 characters
            print("\nFull response received - Gemini API is working correctly!")
        else:
            print("Unexpected response format")
            print(data)
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Connection Error: {e}")