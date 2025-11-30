import os
from dotenv import load_dotenv

load_dotenv()

HAPI_FHIR_URL = os.getenv("HAPI_FHIR_URL", "https://hapi.fhir.org/baseR4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CALENDAR_API_KEY = os.getenv("CALENDAR_API_KEY") # AIza...
MONGODB_URI = os.getenv("MONGODB_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
