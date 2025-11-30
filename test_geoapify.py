import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key: {GEOAPIFY_API_KEY}")

# Test the API directly
if GEOAPIFY_API_KEY:
    url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare&filter=circle:78.4312,17.4243,10000&limit=5&apiKey={GEOAPIFY_API_KEY}"
    print(f"Requesting URL: {url}")
    
    try:
        response = httpx.get(url)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No Geoapify API key found")