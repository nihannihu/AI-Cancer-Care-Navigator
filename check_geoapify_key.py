import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.python", override=True)

# Check if Geoapify API key is loaded
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
print(f"Geoapify API Key loaded: {GEOAPIFY_API_KEY}")
print(f"Key length: {len(GEOAPIFY_API_KEY) if GEOAPIFY_API_KEY else 0}")

if GEOAPIFY_API_KEY:
    print("API key is available")
else:
    print("API key is missing - you need to create a .env file with your Geoapify API key")
    print("Copy .env.example to .env and add your actual API key")