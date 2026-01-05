"""
Direct test of Kraken Service startup - shows all errors
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
service_dir = project_root / "services" / "kraken-service"

print("=" * 70)
print("Direct Kraken Service Startup Test")
print("=" * 70)
print(f"Project root: {project_root}")
print(f"Service dir: {service_dir}")
print()

# Change to service directory
os.chdir(service_dir)
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(service_dir))

print("Attempting to import main module...")
try:
    import main
    print("✅ Main module imported successfully")
    print(f"   App title: {main.app.title}")
    print(f"   Routes: {len(main.app.routes)}")
except Exception as e:
    print(f"❌ Failed to import main module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("If you see this, the module loads correctly.")
print("The issue might be in the lifespan function or uvicorn startup.")
print("=" * 70)

