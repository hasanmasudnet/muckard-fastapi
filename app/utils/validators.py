import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, None


def validate_kraken_api_key(api_key: str) -> bool:
    """Validate Kraken API key format"""
    # Kraken API keys are typically 56 characters
    return len(api_key) >= 50 and len(api_key) <= 60


def validate_kraken_api_secret(api_secret: str) -> bool:
    """Validate Kraken API secret format"""
    # Kraken API secrets are typically 88 characters
    return len(api_secret) >= 80 and len(api_secret) <= 100

