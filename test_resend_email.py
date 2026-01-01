"""
Test script for Resend email functionality
Run this to debug email sending issues: python test_resend_email.py

Usage:
    python test_resend_email.py
    python test_resend_email.py --email your@email.com
    python test_resend_email.py --email your@email.com --name "Your Name"
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env file from: {env_path}")
else:
    print(f"[WARN] .env file not found at: {env_path}")
    print("  Make sure RESEND_KEY is set in your environment or .env file")

# Set up path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_resend_import():
    """Test if Resend can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Resend Package Import")
    print("="*60)
    try:
        from resend import Emails
        print("[OK] Resend package imported successfully")
        print(f"  Emails class: {Emails}")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import Resend: {e}")
        print("  Run: pip install resend==2.0.0")
        return False

def test_api_key():
    """Test if API key is configured"""
    print("\n" + "="*60)
    print("TEST 2: API Key Configuration")
    print("="*60)
    
    api_key = os.getenv("RESEND_KEY") or os.getenv("RESEND_API_KEY")
    
    if not api_key:
        print("[FAIL] RESEND_KEY not found in environment")
        print("  Set it in .env file: RESEND_KEY=re_your_key_here")
        return False, None
    
    print(f"[OK] API Key found")
    print(f"  Length: {len(api_key)} characters")
    print(f"  Starts with: {api_key[:3]}...")
    
    if not api_key.startswith("re_"):
        print("  [WARN] Warning: Resend API keys usually start with 're_'")
    
    return True, api_key

def test_email_service():
    """Test EmailService initialization"""
    print("\n" + "="*60)
    print("TEST 3: EmailService Initialization")
    print("="*60)
    try:
        from app.services.email_service import EmailService
        
        service = EmailService()
        print("[OK] EmailService initialized")
        print(f"  From email: {service.from_email}")
        print(f"  Emails client: {service.emails_client is not None}")
        
        if not service.emails_client:
            print("  [WARN] Warning: Emails client is None (API key may be missing)")
        
        return True, service
    except Exception as e:
        print(f"[FAIL] Failed to initialize EmailService: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_resend_direct(test_email=None):
    """Test Resend API directly"""
    print("\n" + "="*60)
    print("TEST 4: Direct Resend API Test")
    print("="*60)
    
    api_key = os.getenv("RESEND_KEY") or os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[FAIL] Skipping: No API key configured")
        return False
    
    try:
        from resend import Emails
        
        # Set API key in environment
        os.environ["RESEND_API_KEY"] = api_key
        emails = Emails()
        
        print("[OK] Resend Emails client created")
        print(f"  Client type: {type(emails)}")
        
        # Try to send a test email
        if not test_email:
            try:
                test_email = input("\n  Enter test email address (or press Enter to skip): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("  Skipping actual email send (non-interactive mode)")
                return True
        
        if not test_email:
            print("  Skipping actual email send")
            return True
        
        print(f"\n  Attempting to send test email to: {test_email}")
        
        params = {
            "from": "onboarding@resend.dev",
            "to": [test_email],
            "subject": "Test Email from Muckard",
            "html": "<h1>Test Email</h1><p>This is a test email from Muckard OTP system.</p>",
            "text": "Test Email\n\nThis is a test email from Muckard OTP system."
        }
        
        print("  Sending email...")
        response = emails.send(params)
        
        if response and hasattr(response, "id"):
            print(f"  [OK] Email sent successfully!")
            print(f"    Email ID: {response.id}")
            return True
        else:
            print(f"  [FAIL] Email send failed")
            print(f"    Response: {response}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error testing Resend API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_otp_email(test_email=None, test_name=None):
    """Test sending OTP email through EmailService"""
    print("\n" + "="*60)
    print("TEST 5: OTP Email via EmailService")
    print("="*60)
    
    try:
        from app.services.email_service import EmailService
        
        service = EmailService()
        if not service.emails_client:
            print("[FAIL] Skipping: EmailService not properly initialized")
            return False
        
        if not test_email:
            try:
                test_email = input("\n  Enter test email address (or press Enter to skip): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("  Skipping actual email send (non-interactive mode)")
                return True
        
        if not test_email:
            print("  Skipping actual email send")
            return True
        
        if not test_name:
            try:
                test_name = input("  Enter test name (default: Test User): ").strip() or "Test User"
            except (EOFError, KeyboardInterrupt):
                test_name = "Test User"
        
        test_otp = "123456"
        
        print(f"\n  Sending OTP email to: {test_email}")
        print(f"  Name: {test_name}")
        print(f"  OTP: {test_otp}")
        print("  Sending...")
        
        result = service.send_otp_email(test_email, test_otp, test_name)
        
        if result:
            print("  [OK] OTP email sent successfully!")
            return True
        else:
            print("  [FAIL] Failed to send OTP email")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error sending OTP email: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description="Test Resend email functionality")
    parser.add_argument("--email", help="Test email address to send to")
    parser.add_argument("--name", default="Test User", help="Test name (default: Test User)")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("RESEND EMAIL TESTING SUITE")
    print("="*60)
    print("\nThis script will test Resend email functionality step by step.")
    print("Make sure you have:")
    print("  1. RESEND_KEY set in .env file")
    print("  2. Valid Resend API key")
    print("  3. Internet connection")
    if args.email:
        print(f"\n  Using provided email: {args.email}")
        print(f"  Using provided name: {args.name}")
    
    results = []
    
    # Test 1: Import
    results.append(("Import", test_resend_import()))
    if not results[-1][1]:
        print("\n[FAIL] Cannot continue without Resend package")
        return
    
    # Test 2: API Key
    key_ok, api_key = test_api_key()
    results.append(("API Key", key_ok))
    if not key_ok:
        print("\n[FAIL] Cannot continue without API key")
        return
    
    # Test 3: EmailService
    service_ok, service = test_email_service()
    results.append(("EmailService", service_ok))
    
    # Test 4: Direct Resend
    results.append(("Direct Resend", test_resend_direct(args.email)))
    
    # Test 5: OTP Email
    if service_ok:
        results.append(("OTP Email", test_otp_email(args.email, args.name)))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name:20} {status}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "="*60)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED - Check errors above")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

