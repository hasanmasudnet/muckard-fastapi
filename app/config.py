from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings - ALL from .env file"""
    
    # Application
    APP_NAME: str
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = ""  # Auto-generated if empty
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    CACHE_TTL: int = 3600  # Default 1 hour
    
    # Vault
    VAULT_URL: str = ""
    VAULT_TOKEN: str = ""
    VAULT_MOUNT_PATH: str = "secret"
    
    # Kraken API
    KRAKEN_API_BASE_URL: str = "https://api.kraken.com"
    
    # CORS
    CORS_ORIGINS: str  # Comma-separated list
    
    # Email (Resend)
    RESEND_KEY: str = ""  # Optional - for email functionality
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"  # or "SASL_SSL" for production
    KAFKA_SASL_MECHANISM: str = ""  # "PLAIN", "SCRAM-SHA-256", etc.
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    KAFKA_ONBOARDING_TOPIC: str = "onboarding.completed"
    KAFKA_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate SECRET_KEY if not provided
        if not self.SECRET_KEY or self.SECRET_KEY == "":
            self.SECRET_KEY = secrets.token_urlsafe(32)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

