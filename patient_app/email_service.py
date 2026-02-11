"""
Email service for sending notifications
"""
import os
import logging
from typing import Dict, Any
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        """Initialize email service with configuration"""
        self.enabled = False
        self.method = None
        
        # Check for SendGrid API key first (more reliable)
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if self.sendgrid_api_key:
            self.method = "sendgrid"
            self.enabled = True
            logger.info("Using SendGrid for email notifications")
            return
            
        # Fallback to SMTP if configured
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        
        # DEBUG PRINT
        print(f"STDOUT DEBUG: EmailService Init - SMTP_USER={self.smtp_user}")
        
        if self.smtp_user and self.smtp_pass:
            self.method = "smtp"
            self.enabled = True
            self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
            self.admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            logger.info("Using SMTP for email notifications")
            return
            
        logger.info("No email service configured. Email notifications will be disabled.")
    
    def send_appointment_confirmation(self, patient_data: Dict[str, Any], appointment_details: Dict[str, Any]) -> bool:
        """
        Send appointment confirmation email to admin/doctor
        
        Args:
            patient_data: Dictionary containing patient information
            appointment_details: Dictionary containing appointment details
            
        Returns:
            bool: True if email sent successfully or if service is disabled, False if email failed
        """
        # If email service is not configured, return True (successful no-op)
        if not self.enabled:
            return True
            
        try:
            if self.method == "sendgrid":
                return self._send_via_sendgrid(patient_data, appointment_details)
            elif self.method == "smtp":
                return self._send_via_smtp(patient_data, appointment_details)
            else:
                return True  # Should not happen
        except Exception as e:
            logger.error(f"Failed to send appointment email: {e}")
            return False
    
    def _send_via_sendgrid(self, patient_data: Dict[str, Any], appointment_details: Dict[str, Any]) -> bool:
        """
        Send email via SendGrid API
        """
        try:
            # Prepare email content
            subject = f"New Appointment Booking - {patient_data.get('username', 'Patient')}"
            content = self._create_plain_text_body(patient_data, appointment_details)
            
            # SendGrid API request
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "personalizations": [
                    {
                        "to": [{"email": os.getenv("ADMIN_EMAIL", "admin@example.com")}],
                        "subject": subject
                    }
                ],
                "from": {"email": os.getenv("SMTP_FROM", "notification@onconavigator.com")},
                "content": [{"type": "text/plain", "value": content}]
            }
            
            response = httpx.post(url, headers=headers, json=data, timeout=10.0)
            if response.status_code in [200, 201, 202]:
                logger.info("Appointment confirmation email sent via SendGrid")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid email error: {e}")
            return False
    
    def _send_via_smtp(self, patient_data: Dict[str, Any], appointment_details: Dict[str, Any]) -> bool:
        """
        Send email via SMTP (fallback method)
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = self.admin_email
            msg['Subject'] = f"New Appointment Booking - {patient_data.get('username', 'Patient')}"
            
            # Add plain text body (simpler than HTML for better compatibility)
            body = self._create_plain_text_body(patient_data, appointment_details)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_from, self.admin_email, msg.as_string())
            
            logger.info(f"Appointment confirmation email sent via SMTP to {self.admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP email error: {e}")
            return False
    
    def _create_plain_text_body(self, patient_data: Dict[str, Any], appointment_details: Dict[str, Any]) -> str:
        """
        Create plain text email body for appointment confirmation
        
        Args:
            patient_data: Dictionary containing patient information
            appointment_details: Dictionary containing appointment details
            
        Returns:
            str: Formatted email body with patient and appointment details
        """
        from datetime import datetime
        
        # Create email body with patient and appointment details
        body = f"""
New Appointment Booking Confirmation
=================================

Patient Information:
------------------
Name: {patient_data.get('username', 'N/A')}
Email: {patient_data.get('email', 'N/A')}

Appointment Details:
-------------------
Doctor: {appointment_details.get('doctor_name', 'N/A')}
Preferred Time: {appointment_details.get('preferred_time', 'N/A')}
Booking Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please contact the patient to confirm this appointment.
        """.strip()
        
        return body