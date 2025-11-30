import httpx

# Use the new API key directly for testing
GEMINI_API_KEY = "AIzaSyCKg3ur9DIN8oCMN02hZ06jA_GWb8CWbIQ"
print(f"New Gemini API Key: {GEMINI_API_KEY[:15] + '...' if GEMINI_API_KEY else 'None'}")

# Try a simple request with gemini-pro-latest which should be available
print("\nTrying gemini-pro-latest model...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"
payload = {
    "contents": [{
        "parts": [{
            "text": "Hello, what model are you?"
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
            print(f"Response: {analysis}")
        else:
            print("Unexpected response format")
            print(data)
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Connection Error: {e}")