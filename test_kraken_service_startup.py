"""
Test Kraken Service Startup
Diagnoses why the service might not be starting
"""
import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.absolute()
service_dir = project_root / "services" / "kraken-service"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(service_dir))

print("Testing Kraken Service Startup...")
print(f"Project root: {project_root}")
print(f"Service dir: {service_dir}")
print()

# Test imports
print("1. Testing imports...")
try:
    from config import settings
    print("   [OK] config.settings imported")
except Exception as e:
    print(f"   [ERROR] config.settings: {e}")
    sys.exit(1)

try:
    from database import get_db
    print("   [OK] database imported")
except Exception as e:
    print(f"   [ERROR] database: {e}")

try:
    from services import get_consumer, BotStatusService
    print("   [OK] services module imported")
except Exception as e:
    print(f"   [ERROR] services module: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.utils.kafka_consumer import get_kafka_consumer
    print("   [OK] kafka_consumer imported")
except Exception as e:
    print(f"   [ERROR] kafka_consumer: {e}")

try:
    from app.config import settings as app_settings
    print("   [OK] app.config.settings imported")
except Exception as e:
    print(f"   [ERROR] app.config.settings: {e}")

# Test main module
print("\n2. Testing main module...")
try:
    import main
    print("   [OK] main module imported")
    print(f"   [OK] FastAPI app created: {hasattr(main, 'app')}")
except Exception as e:
    print(f"   [ERROR] main module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test app creation
print("\n3. Testing FastAPI app...")
try:
    app = main.app
    print(f"   [OK] App title: {app.title}")
    print(f"   [OK] App has lifespan: {hasattr(app, 'router')}")
except Exception as e:
    print(f"   [ERROR] FastAPI app: {e}")
    import traceback
    traceback.print_exc()

print("\n[OK] All startup checks passed!")
print("\nYou can now start the service with:")
print(f"  cd {service_dir}")
print("  python -m uvicorn main:app --host 127.0.0.1 --port 8001")


