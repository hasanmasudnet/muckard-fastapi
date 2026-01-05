import subprocess
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    processes = []
    
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    try:
        # Start user-service on port 8000 (matches muckard-backend)
        # Run from service directory to handle relative imports
        user_service_dir = project_root / "services" / "user-service"
        user_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", 
             "main:app",
             "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=str(user_service_dir),
            env={**os.environ, "PYTHONPATH": str(project_root)}
        )
        processes.append(user_process)
        print("✅ User service started on port 8000")
        
        # Start kraken-service on port 8001 (matches muckard-backend)
        # Run from service directory to handle relative imports
        kraken_service_dir = project_root / "services" / "kraken-service"
        kraken_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn",
             "main:app",
             "--host", "127.0.0.1", "--port", "8001", "--reload"],
            cwd=str(kraken_service_dir),
            env={**os.environ, "PYTHONPATH": str(project_root)}
        )
        processes.append(kraken_process)
        print("✅ Kraken service started on port 8001")
        
        # Bot service (muckai/muckai) runs separately on port 8002
        # Start it separately or via separate command
        print("ℹ️  Bot service should be started separately on port 8002")
        
        # Wait for processes
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down services...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error terminating process: {e}")
        print("✅ All services stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        for process in processes:
            try:
                process.terminate()
            except:
                pass
        sys.exit(1)

