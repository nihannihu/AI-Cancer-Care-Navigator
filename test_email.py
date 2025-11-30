
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env explicitly
load_dotenv(".env")

def test_email():
    print("--- Testing Email Configuration ---")
    
    # 1. Check Environment Variables
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    admin_email = os.getenv("ADMIN_EMAIL")
    
    print(f"SMTP_USER: {smtp_user}")
    print(f"SMTP_PASS: {'*' * len(smtp_pass) if smtp_pass else 'None'}")
    print(f"ADMIN_EMAIL: {admin_email}")
    
    if not smtp_user or not smtp_pass:
        print("ERROR: Missing SMTP credentials in .env")
        return

    # 2. Try Sending Email
    print("\n--- Attempting to Send Test Email ---")
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = "nihanmohammed95@gmail.com"
        msg['Subject'] = "Test Email from Onco-Navigator Debugger"
        
        body = "This is a test email to verify SMTP configuration."
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Connecting to smtp.gmail.com:587...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.set_debuglevel(1) # Enable SMTP debug output
            server.starttls()
            print("Logging in...")
            server.login(smtp_user, smtp_pass)
            print("Sending mail...")
            server.sendmail(smtp_user, "nihanmohammed95@gmail.com", msg.as_string())
        
        print("\nSUCCESS: Email sent successfully!")
        
    except Exception as e:
        print(f"\nFAILED: {e}")

if __name__ == "__main__":
    test_email()
