"""
Service Verification Script
Verifies that all services can be imported and dependencies are installed
"""
import sys
import os
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")

def check_dependency(module_name: str, package_name: str = None) -> bool:
    """Check if a Python module is installed"""
    try:
        __import__(module_name)
        print_success(f"{package_name or module_name} is installed")
        return True
    except ImportError:
        print_error(f"{package_name or module_name} is NOT installed")
        print_info(f"   Install with: pip install {package_name or module_name}")
        return False

def check_service_imports():
    """Check if service modules can be imported"""
    print_header("Checking Service Imports")
    
    # Check user-service
    print_info("Checking user-service...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "services" / "user-service"))
        from services.auth_service import AuthService
        from services.user_service import UserService
        print_success("user-service modules can be imported")
    except Exception as e:
        print_error(f"user-service import failed: {e}")
    
    # Check kraken-service
    print_info("Checking kraken-service...")
    try:
        # Test if services directory is accessible
        service_dir = Path(__file__).parent / "services" / "kraken-service"
        if (service_dir / "services" / "__init__.py").exists():
            print_success("kraken-service/services directory exists")
        else:
            print_error("kraken-service/services directory not found")
            return
        
        # Change to service directory and test imports
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(service_dir))
            sys.path.insert(0, str(service_dir))
            # Clear any cached imports
            if 'services' in sys.modules:
                del sys.modules['services']
            from services import get_consumer, BotStatusService
            print_success("kraken-service modules can be imported")
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print_error(f"kraken-service import failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print_header("Service Verification Script")
    
    # Check dependencies
    print_header("Checking Dependencies")
    deps_ok = True
    deps_ok &= check_dependency("aio_pika", "aio-pika")
    deps_ok &= check_dependency("confluent_kafka", "confluent-kafka")
    deps_ok &= check_dependency("fastapi", "fastapi")
    deps_ok &= check_dependency("sqlalchemy", "sqlalchemy")
    deps_ok &= check_dependency("redis", "redis")
    
    if not deps_ok:
        print_error("\nSome dependencies are missing. Please install them:")
        print_info("pip install -r requirements.txt")
        return
    
    # Check service imports
    check_service_imports()
    
    print_header("Verification Complete")
    print_success("All checks completed!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

