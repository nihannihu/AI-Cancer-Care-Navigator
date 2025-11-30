
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Try loading from both possible env files
load_dotenv()
load_dotenv(".env.python")

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        genai.configure(api_key=api_key)
        with open("available_models.txt", "w") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
        print("Models written to available_models.txt")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("Cannot list models without API key.")
