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
        url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare&filter=circle:78.4312,17.4243,10000&limit=5&apiKey={GEOAPIFY_API_KEY}"
        print(f"Requesting URL: {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                print(f"Response Status: {response.status_code}")
                print(f"Response Headers: {response.headers}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Response Text: {response.text[:1000]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"Parsed JSON data: {data}")
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

# Run the async function
asyncio.run(test_geoapify())