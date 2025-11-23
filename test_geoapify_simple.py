import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key: {GEOAPIFY_API_KEY}")

if GEOAPIFY_API_KEY:
    # Try a simple request to New York
    url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital&filter=circle:-74.006,40.7128,5000&limit=2&apiKey={GEOAPIFY_API_KEY}"
    print(f"Requesting URL: {url}")
    
    try:
        response = httpx.get(url, timeout=30.0)
        print(f"Response Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Response Text: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No Geoapify API key found")