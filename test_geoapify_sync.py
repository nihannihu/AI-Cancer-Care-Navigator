import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key: {GEOAPIFY_API_KEY}")

if GEOAPIFY_API_KEY:
    # Correct order: longitude, latitude
    url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare&filter=circle:78.4312,17.4243,10000&limit=5&apiKey={GEOAPIFY_API_KEY}"
    print(f"Requesting URL: {url}")
    
    try:
        response = httpx.get(url, timeout=30.0)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Response Text: {response.text[:1000]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed JSON data keys: {data.keys()}")
            except Exception as json_error:
                print(f"Error parsing JSON: {json_error}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No Geoapify API key found")