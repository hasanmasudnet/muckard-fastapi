"""
Service Startup Script
Starts all microservices and verifies they're running
"""
import subprocess
import sys
import os
import time
import requests
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")

def check_service(port: int, name: str, path: str = "/") -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(f"http://localhost:{port}{path}", timeout=2)
        if response.status_code == 200:
            print_success(f"{name} is running on port {port}")
            return True
        else:
            print_error(f"{name} returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{name} is not accessible on port {port}: {e}")
        return False

def start_service(name: str, port: int, service_dir: Path, project_root: Path):
    """Start a service"""
    print_info(f"Starting {name} on port {port}...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn",
             "main:app",
             "--host", "127.0.0.1", "--port", str(port), "--reload"],
            cwd=str(service_dir),
            env={**os.environ, "PYTHONPATH": str(project_root)},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            universal_newlines=True
        )
        # Start a thread to read and print output
        def read_output():
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        print(f"[{name}] {line.rstrip()}")
        import threading
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        return process
    except Exception as e:
        print_error(f"Failed to start {name}: {e}")
        return None

def main():
    print_header("Microservices Startup Script")
    
    project_root = Path(__file__).parent.absolute()
    processes = []
    
    try:
        # Start user-service
        user_service_dir = project_root / "services" / "user-service"
        user_process = start_service("User Service", 8000, user_service_dir, project_root)
        if user_process:
            processes.append(("User Service", user_process, 8000, "/user"))
        
        # Start kraken-service
        kraken_service_dir = project_root / "services" / "kraken-service"
        kraken_process = start_service("Kraken Service", 8001, kraken_service_dir, project_root)
        if kraken_process:
            processes.append(("Kraken Service", kraken_process, 8001, "/kraken"))
        
        if not processes:
            print_error("No services were started")
            return
        
        # Wait for services to start
        print_info("Waiting for services to start...")
        time.sleep(3)
        
        # Verify services are running
        print_header("Verifying Services")
        all_running = True
        for name, process, port, path in processes:
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                print_error(f"{name} has terminated")
                if stderr:
                    print_error(f"Error: {stderr.decode()[:200]}")
                all_running = False
            else:
                # Check if service is responding
                if not check_service(port, name, path):
                    all_running = False
        
        if all_running:
            print_header("All Services Running")
            print_success("User Service: http://localhost:8000")
            print_success("Kraken Service: http://localhost:8001")
            print_info("Press Ctrl+C to stop all services")
            print()
            
            # Keep running until interrupted
            try:
                for name, process, port, path in processes:
                    process.wait()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Shutting down services...{Colors.RESET}")
        else:
            print_error("Some services failed to start. Check the logs above.")
            # Clean up
            for name, process, port, path in processes:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    process.kill()
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down services...{Colors.RESET}")
        for name, process, port, path in processes:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
        print_success("All services stopped")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        # Clean up
        for name, process, port, path in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main()


