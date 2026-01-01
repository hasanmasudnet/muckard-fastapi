"""
Direct Resend API test using requests library
This bypasses the Python SDK to test if the API key itself is valid
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

api_key = os.getenv("RESEND_KEY")

print("="*60)
print("DIRECT RESEND API TEST")
print("="*60)

if not api_key:
    print("[FAIL] RESEND_KEY not found")
    sys.exit(1)

print(f"[OK] API Key: {api_key[:10]}...{api_key[-5:]}")

# Test: Send email (requires Sending access)
print("\n" + "-"*60)
print("TEST: Send Test Email (This will verify API key)")
print("-"*60)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--email", help="Email address to test")
args = parser.parse_args()

test_email = args.email
if not test_email:
    try:
        test_email = input("Enter email to test (or press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("Skipping email send test (non-interactive mode)")
        print("\nRun with: python test_resend_direct_api.py --email your@email.com")
        sys.exit(0)

if not test_email:
    print("Skipping email send test")
    sys.exit(0)

email_data = {
    "from": "onboarding@resend.dev",
    "to": [test_email],
    "subject": "Test from Direct API",
    "html": "<h1>Test</h1><p>This is a direct API test.</p>",
    "text": "Test\n\nThis is a direct API test."
}

try:
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=email_data,
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("[OK] Email sent successfully!")
        data = response.json()
        print(f"  Email ID: {data.get('id')}")
    elif response.status_code == 401:
        print("[FAIL] API key is INVALID")
        print(f"  Response: {response.text}")
    elif response.status_code == 403:
        print("[FAIL] API key lacks SENDING permissions")
        print("  Go to Resend dashboard and ensure key has 'Sending access'")
        print(f"  Response: {response.text}")
    else:
        print(f"[WARN] Status: {response.status_code}")
        print(f"  Response: {response.text}")
except Exception as e:
    print(f"[ERROR] Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("Status 200: Email sent successfully - API key is VALID")
print("Status 401: API key is INVALID or REVOKED")
print("Status 403: Key is valid but needs SENDING permissions")
print("="*60)

