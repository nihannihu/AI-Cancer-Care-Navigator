import asyncio
import httpx
import os
import math
from dotenv import load_dotenv

load_dotenv()
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# Haversine distance function
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r

async def debug_hospitals():
    # Use coordinates for a central location (e.g., Bangalore) or try to guess user's location
    # I'll use the coordinates from the previous verify script: 12.9716, 77.5946
    latitude = 12.9716
    longitude = 77.5946
    radius_meters = 50000
    limit = 20
    
    with open("debug_output.txt", "w", encoding="utf-8") as log_file:
        def log(msg):
            print(msg)
            log_file.write(msg + "\n")
            
        log(f"Searching near {latitude}, {longitude} with radius {radius_meters}m")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Try healthcare.hospital
            url = f"https://api.geoapify.com/v2/places?categories=healthcare.hospital&filter=circle:{longitude},{latitude},{radius_meters}&limit={limit}&apiKey={GEOAPIFY_API_KEY}"
            log(f"\n--- Query 1: healthcare.hospital ---\nURL: {url}")
            
            response = await client.get(url)
            data = response.json()
            features = data.get("features", [])
            log(f"Found {len(features)} raw features.")
            
            for i, f in enumerate(features):
                props = f.get("properties", {})
                name = props.get("name", "Unknown")
                cats = props.get("categories", [])
                
                coords = f.get("geometry", {}).get("coordinates", [])
                dist = 0
                if len(coords) >= 2:
                    dist = haversine_distance(latitude, longitude, coords[1], coords[0])
                
                log(f"{i+1}. {name} ({dist:.2f} km) - Cats: {cats}")
                
                # Simulate filtering
                name_lower = name.lower()
                if "dental" in name_lower or "dentist" in name_lower or "clinic" in name_lower:
                    log(f"   [FILTERED OUT] Name contains dental/clinic")
                elif any("dentist" in c for c in cats):
                    log(f"   [FILTERED OUT] Category contains dentist")
                else:
                    log(f"   [KEPT]")

            # 2. Try healthcare (fallback) if needed
            url2 = f"https://api.geoapify.com/v2/places?categories=healthcare&filter=circle:{longitude},{latitude},{radius_meters}&limit={limit}&apiKey={GEOAPIFY_API_KEY}"
            log(f"\n--- Query 2: healthcare (General) ---\nURL: {url2}")
            response2 = await client.get(url2)
            features2 = response2.json().get("features", [])
            log(f"Found {len(features2)} raw features.")
            
            for i, f in enumerate(features2):
                props = f.get("properties", {})
                name = props.get("name", "Unknown")
                
                coords = f.get("geometry", {}).get("coordinates", [])
                dist = 0
                if len(coords) >= 2:
                    dist = haversine_distance(latitude, longitude, coords[1], coords[0])
                    
                # Check if this was in the first list
                already_found = any(f.get("properties", {}).get("name") == name for f in features)
                if not already_found and dist < 10: # Only show close ones we missed
                    log(f"   [NEW] {name} ({dist:.2f} km)")

if __name__ == "__main__":
    asyncio.run(debug_hospitals())
