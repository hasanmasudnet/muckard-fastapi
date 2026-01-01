"""
Quick script to verify Resend API key
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

api_key = os.getenv("RESEND_KEY")

print("="*60)
print("RESEND API KEY VERIFICATION")
print("="*60)

if not api_key:
    print("[FAIL] RESEND_KEY not found in .env file")
    sys.exit(1)

print(f"[OK] API Key found in .env")
print(f"  Length: {len(api_key)} characters")
print(f"  Starts with: {api_key[:3]}...")
print(f"  Full key: {api_key}")

# Check format
if not api_key.startswith("re_"):
    print("\n[WARN] API key should start with 're_'")
    print("  Your key starts with:", api_key[:3])

if len(api_key) < 30:
    print("\n[WARN] API key seems too short (should be ~36 characters)")

# Check for common issues
if " " in api_key:
    print("\n[WARN] API key contains spaces - this will cause issues!")
    print("  Remove any spaces from the key")

if api_key.startswith('"') or api_key.endswith('"'):
    print("\n[WARN] API key is wrapped in quotes - remove quotes from .env file")
    print("  Use: RESEND_KEY=re_...")
    print("  Not: RESEND_KEY=\"re_...\"")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Go to: https://resend.com/api-keys")
print("2. Check if this key exists and is ACTIVE")
print("3. If not, create a NEW API key")
print("4. Copy the new key and update .env file")
print("5. Make sure the key has no spaces or quotes")
print("="*60)

