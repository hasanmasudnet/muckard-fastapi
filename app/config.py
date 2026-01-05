from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings - ALL from .env file"""
    
    # Application (from .env)
    APP_NAME: str = "Muckard FastAPI Backend"  # Default if not in .env
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Security (from .env)
    SECRET_KEY: str = ""  # Auto-generated if empty
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Default if not in .env
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Default if not in .env
    
    # Database (from .env)
    DATABASE_URL: str = ""  # Will be required in practice
    
    # Redis (from .env)
    REDIS_HOST: str = "localhost"  # Default if not in .env
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    CACHE_TTL: int = 3600  # Default 1 hour
    
    # Vault (from .env, optional)
    VAULT_URL: str = ""
    VAULT_TOKEN: str = ""
    VAULT_MOUNT_PATH: str = "secret"
    
    # Kraken API (from .env)
    KRAKEN_API_BASE_URL: str = "https://api.kraken.com"
    
    # CORS (from .env)
    CORS_ORIGINS: str = "http://localhost:3000"  # Default if not in .env
    
    # Email (Resend) - Optional
    RESEND_KEY: str = ""
    
    # Kafka (from .env, optional)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = ""
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    KAFKA_ONBOARDING_TOPIC: str = "onboarding.events"
    KAFKA_USER_EVENTS_TOPIC: str = "user.events"
    KAFKA_KRAKEN_EVENTS_TOPIC: str = "kraken.events"
    KAFKA_TRADING_EVENTS_TOPIC: str = "trading.events"
    KAFKA_ENABLED: bool = True
    
    # RabbitMQ (from .env)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

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

