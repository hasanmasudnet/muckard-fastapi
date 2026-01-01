"""Test EmailService with real API"""
from app.services.email_service import EmailService

service = EmailService()
print(f"API Key configured: {service.api_key is not None and service.api_key != ''}")
print(f"From email: {service.from_email}")

print("\nSending test OTP email...")
result = service.send_otp_email('hasanmasudnet@gmail.com', '888777', 'Hasan Masud')
print(f"\nEmail sent successfully: {result}")

