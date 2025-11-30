import requests
import json

# Test the emergency hospital API directly
url = "http://127.0.0.1:8000/emergency-hospitals"
data = {
    "latitude": 40.7128,
    "longitude": -74.0060
}

print("Testing emergency hospital API...")
print("Sending request with coordinates:", data)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Success! Received real hospital data:")
        if "features" in result and len(result["features"]) > 0:
            print(f"Found {len(result['features'])} hospitals")
            for i, feature in enumerate(result["features"][:3]):  # Show first 3 hospitals
                props = feature.get("properties", {})
                name = props.get("name", "Unknown")
                distance = props.get("distance_km", "Unknown")
                print(f"  {i+1}. {name} - {distance} km away")
        else:
            print("No hospitals found in response")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error connecting to server: {e}")

print("\nTest completed.")