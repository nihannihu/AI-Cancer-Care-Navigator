
import os
from dotenv import load_dotenv

# Load envs manually since we are not running via app_main
load_dotenv(".env")

print("--- Testing EmailService Direct ---")
try:
    from patient_app.email_service import EmailService
    print("Imported EmailService class.")
    
    es = EmailService()
    print(f"Instantiated EmailService. Enabled: {es.enabled}, Method: {es.method}")
    
    if es.enabled:
        print("SUCCESS: EmailService is enabled.")
    else:
        print("FAILURE: EmailService is disabled.")
        
except Exception as e:
    print(f"Error: {e}")
