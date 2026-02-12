
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    admin_email = os.getenv("ADMIN_EMAIL")

    print(f"Testing SMTP Configuration:")
    print(f"Host: {smtp_host}:{smtp_port}")
    print(f"User: {smtp_user}")
    print(f"From: {smtp_from}")
    print(f"To:   {admin_email}")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, admin_email]):
        print("❌ Error: Missing SMTP configuration in .env")
        return

    try:
        msg = MIMEText("This is a test email from Onco-Navigator AI to verify SMTP configuration.")
        msg['Subject'] = "Onco-Navigator AI - Test Email"
        msg['From'] = smtp_from
        msg['To'] = admin_email

        print("Connecting to SMTP server...")
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            print("Logging in...")
            server.login(smtp_user, smtp_pass)
            print("Sending email...")
            server.sendmail(smtp_from, admin_email, msg.as_string())
        
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    test_smtp()
