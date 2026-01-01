"""Test Resend SDK with verified domain"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Set API key in environment BEFORE importing Resend
api_key = os.getenv("RESEND_KEY")
os.environ["RESEND_API_KEY"] = api_key

print(f"API Key set: {api_key[:10]}...")

# Now import Resend
from resend import Emails

emails = Emails()

print("Sending test email...")
params = {
    "from": "hello@muckard.com",
    "to": ["hasanmasudnet@gmail.com"],
    "subject": "Test from SDK",
    "html": "<h1>Test</h1><p>This is a test from the SDK.</p>",
    "text": "Test\n\nThis is a test from the SDK."
}

try:
    response = emails.send(params)
    if isinstance(response, dict):
        print(f"[OK] Email sent! ID: {response.get('id', 'N/A')}")
    elif hasattr(response, 'id'):
        print(f"[OK] Email sent! ID: {response.id}")
    else:
        print(f"[OK] Email sent! Response: {response}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

