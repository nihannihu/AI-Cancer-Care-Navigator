import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key: {GEOAPIFY_API_KEY}")

if GEOAPIFY_API_KEY:
    # Try a simple request to Hyderabad, India (known to have hospitals)
    search_radius = 50000  # 50km in meters (increased from 5km)
    # Use coordinates for Hyderabad, India
    url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare&filter=circle:78.4867,17.3850,{search_radius}&limit=5&apiKey={GEOAPIFY_API_KEY}"
    print(f"Requesting URL: {url}")
    
    try:
        response = httpx.get(url, timeout=30.0)
        print(f"Response Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('features', []))} hospitals")
            # Print first hospital if found
            features = data.get('features', [])
            if features:
                first_hospital = features[0]
                props = first_hospital.get('properties', {})
                print(f"First hospital name: {props.get('name', 'Unknown')}")
                print(f"First hospital address: {props.get('formatted', 'Unknown')}")
            print(f"Response Text: {response.text[:1000]}")
        else:
            print(f"Response Text: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No Geoapify API key found")