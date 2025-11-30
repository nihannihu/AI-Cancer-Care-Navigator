
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_manual_email():
    # Credentials
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    to_email = "nihanmohammed95@gmail.com"
    
    if not smtp_user or not smtp_pass:
        print("Error: Credentials not found in .env")
        return

    # Construct Email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = "Patient & Appointment Details - Onco-Navigator"
    
    body = f"""
ONCO-NAVIGATOR PATIENT REPORT
=============================

Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PATIENT DETAILS
---------------
Name: Nihan
ID: #8821
Condition: Breast Cancer (Stage I)
Status: Active Treatment

APPOINTMENT DETAILS
-------------------
Doctor: Dr. Sharma (Oncologist)
Hospital: Bendiganahalli Primary Health Centre
Date: 2025-11-29
Time: 10:00 AM
Status: Confirmed

NOTES
-----
Patient reported severe chest pain and high risk symptoms.
Ambulance dispatch requested.

---------------------------------------------------
This is a manually triggered report from the system.
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"Sending email to {to_email}...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print("SUCCESS: Email sent successfully.")
    except Exception as e:
        print(f"FAILED to send email: {e}")

if __name__ == "__main__":
    send_manual_email()
