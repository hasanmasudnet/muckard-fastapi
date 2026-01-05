"""
Test Kraken Service Lifespan
Tests the lifespan function to identify startup errors
"""
import sys
import os
import asyncio
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.absolute()
service_dir = project_root / "services" / "kraken-service"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(service_dir))

print("Testing Kraken Service Lifespan...")
print(f"Project root: {project_root}")
print(f"Service dir: {service_dir}")
print()

# Test lifespan function
print("Testing lifespan function...")
try:
    from main import app, lifespan
    print("[OK] App and lifespan imported")
    
    # Create a mock app state
    class MockApp:
        def __init__(self):
            self.state = type('State', (), {})()
    
    mock_app = MockApp()
    
    # Run lifespan
    async def test_lifespan():
        try:
            async with lifespan(mock_app):
                print("[OK] Lifespan started successfully")
                print("[OK] Service should be running now")
                # Keep it running for a moment
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[ERROR] Lifespan failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    asyncio.run(test_lifespan())
    print("\n[OK] All lifespan tests passed!")
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


