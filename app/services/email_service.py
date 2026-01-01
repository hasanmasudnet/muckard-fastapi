from app.config import settings
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via Resend API"""
    
    def __init__(self):
        self.api_key = settings.RESEND_KEY
        self.api_url = "https://api.resend.com/emails"
        # Using verified domain with display name
        self.from_email = "Muckard<hello@muckard.com>"
        self.template_path = Path(__file__).parent.parent / "templates" / "email_verification.html"
    
    def _load_template(self) -> str:
        """Load email template from file"""
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Email template not found at {self.template_path}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """Fallback template if file not found"""
        return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #0a0a0a; color: #ffffff; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 40px;">
        <h1 style="color: #ef4444; margin-bottom: 20px;">Verify Your Email</h1>
        <p>Hello {{name}},</p>
        <p>Your verification code is:</p>
        <div style="font-size: 48px; font-weight: bold; color: #ef4444; letter-spacing: 8px; margin: 30px 0; font-family: monospace;">{{otp_code}}</div>
        <p style="color: rgba(255, 255, 255, 0.6);">This code expires in 10 minutes.</p>
    </div>
</body>
</html>"""
    
    def _render_template(self, name: str, otp_code: str) -> str:
        """Render email template with variables"""
        template = self._load_template()
        return template.replace("{{name}}", name).replace("{{otp_code}}", otp_code)
    
    def send_otp_email(self, email: str, otp_code: str, name: str) -> bool:
        """
        Send OTP verification email using Resend API
        
        Args:
            email: Recipient email address
            otp_code: 6-digit OTP code
            name: User's name
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"[EMAIL_SERVICE] send_otp_email called for email: {email}, name: {name}, OTP: {otp_code}")
        
        if not self.api_key:
            logger.error("[EMAIL_SERVICE] Resend API key not configured. Email not sent.")
            return False
        
        logger.debug(f"[EMAIL_SERVICE] API key configured: {self.api_key[:10]}...")
        logger.debug(f"[EMAIL_SERVICE] From email: {self.from_email}")
        logger.debug(f"[EMAIL_SERVICE] API URL: {self.api_url}")
        
        try:
            logger.debug(f"[EMAIL_SERVICE] Loading and rendering email template")
            html_content = self._render_template(name, otp_code)
            logger.debug(f"[EMAIL_SERVICE] Email template rendered successfully")
            
            # Plain text version for better compatibility
            plain_text = f"""Verify Your Email - Muckard

Hello {name},

Thank you for signing up! Please use the verification code below to complete your registration:

Your Verification Code: {otp_code}

This code will expire in 10 minutes. If you didn't request this code, you can safely ignore this email.

Need help? Contact us at support@muckard.com

© 2024 Muckard. All rights reserved.
"""
            
            # Use Resend REST API directly (more reliable than SDK)
            payload = {
                "from": self.from_email,
                "to": [email],
                "subject": "Verify Your Email - Muckard",
                "html": html_content,
                "text": plain_text,
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"[EMAIL_SERVICE] Sending POST request to Resend API: {self.api_url}")
            logger.debug(f"[EMAIL_SERVICE] Payload: from={self.from_email}, to={email}, subject=Verify Your Email - Muckard")
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"[EMAIL_SERVICE] Resend API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                email_id = data.get("id")
                logger.info(f"[EMAIL_SERVICE] OTP email sent successfully to {email} (ID: {email_id})")
                return True
            elif response.status_code == 401:
                logger.error(f"[EMAIL_SERVICE] Resend API key is invalid. Please check your RESEND_KEY in .env file.")
                logger.error(f"[EMAIL_SERVICE] Response body: {response.text}")
                return False
            elif response.status_code == 403:
                error_data = response.json()
                error_msg = error_data.get("message", "Permission denied")
                logger.error(f"[EMAIL_SERVICE] Resend API error (403): {error_msg}")
                logger.error(f"[EMAIL_SERVICE] Full response: {response.text}")
                if "domain" in error_msg.lower() or "not verified" in error_msg.lower():
                    logger.error(f"[EMAIL_SERVICE] Please verify '{self.from_email}' domain in Resend dashboard.")
                return False
            else:
                logger.error(f"[EMAIL_SERVICE] Failed to send OTP email to {email}. Status: {response.status_code}")
                logger.error(f"[EMAIL_SERVICE] Response body: {response.text}")
                return False
                
        except requests.exceptions.Timeout as e:
            logger.error(f"[EMAIL_SERVICE] Timeout error sending OTP email to {email}: {str(e)}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"[EMAIL_SERVICE] Network error sending OTP email to {email}: {str(e)}")
            return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[EMAIL_SERVICE] Unexpected error sending OTP email to {email}: {error_msg}", exc_info=True)
            return False

