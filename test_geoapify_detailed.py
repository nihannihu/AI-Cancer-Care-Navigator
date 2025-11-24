import os
from dotenv import load_dotenv
import httpx
import asyncio
import pytest

# This is a manual integration script and not part of the automated pytest suite
pytestmark = pytest.mark.skip("Manual Geoapify integration script; run directly with python, not via pytest")

# Load environment variables
load_dotenv(".env.python")

# Get the API key
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key: {GEOAPIFY_API_KEY}")

async def test_geoapify():
    if GEOAPIFY_API_KEY:
        # Correct order: longitude, latitude
        # Use expanded search radius (50km instead of 10km)
        # Use only supported categories
        search_radius = 50000  # 50km in meters
        url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare&filter=circle:78.4312,17.4243,{search_radius}&limit=10&apiKey={GEOAPIFY_API_KEY}"
        print(f"Requesting URL: {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                print(f"Response Status: {response.status_code}")
                print(f"Response Headers: {response.headers}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        features = data.get("features", [])
                        print(f"Found {len(features)} hospitals")
                        print(f"First hospital: {features[0] if features else 'None'}")
                        
                        # Print first few features for inspection
                        for i, feature in enumerate(features[:3]):
                            props = feature.get("properties", {})
                            print(f"Hospital {i+1}: {props.get('name', 'Unknown')} at {props.get('distance', 'Unknown')}m")
                    except Exception as json_error:
                        print(f"Error parsing JSON: {json_error}")
                        print(f"Response text: {response.text[:500]}")
                else:
                    print(f"Error response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No Geoapify API key found")

# Run the async function
asyncio.run(test_geoapify())