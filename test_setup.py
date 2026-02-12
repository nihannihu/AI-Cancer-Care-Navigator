import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio

# Load environment variables
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

async def test_mongodb():
    print("\n--- Testing MongoDB Connection ---")
    uri = os.getenv("MONGODB_URI")
    print(f"URI found: {'Yes' if uri else 'No'}")
    if not uri:
        print("❌ MongoDB URI missing!")
        return
        
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(uri)
        # Ping the server
        await client.admin.command('ping')
        print("✅ MongoDB Connection Successful!")
        
        # Check database access
        db = client.get_default_database()
        print(f"✅ Default Database: {db.name}")
        
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")

async def test_gemini():
    print("\n--- Testing Gemini AI (Robust Client) ---")
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key found: {'Yes' if api_key else 'No'} ({api_key[:5]}...)" if api_key else "No")
    
    if not api_key:
        print("❌ Gemini API Key missing!")
        return

    try:
        from ml.gemini_utils import get_gemini_client
        client = get_gemini_client()
        
        print(f"Attempting generation with fallback models: {client.FALLBACK_MODELS}")
        response = await client.generate_content_async("Hello! Are you working?")
        print(f"✅ Gemini Response: {response.text.strip()}")
        
    except Exception as e:
        print(f"❌ Gemini Generation Failed: {e}")

async def main():
    await test_mongodb()
    await test_gemini()

if __name__ == "__main__":
    asyncio.run(main())
