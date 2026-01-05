from pydantic_settings import BaseSettings
from typing import List
import secrets
from pathlib import Path


class Settings(BaseSettings):
    """Service settings - ALL from shared .env file in project root"""
    
    # All settings come from .env file - no defaults here
    
    # Security (REQUIRED from .env)
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    SECRET_KEY: str = ""  # Auto-generated if empty in .env
    ALGORITHM: str  # From .env
    
    # Database (REQUIRED from .env)
    DATABASE_URL: str
    
    # Redis (REQUIRED from .env)
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str
    
    # CORS (REQUIRED from .env)
    CORS_ORIGINS: str
    
    # RabbitMQ (REQUIRED from .env)
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_VHOST: str
    
    # Kafka (from .env, with defaults)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = ""
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    KAFKA_USER_EVENTS_TOPIC: str = "user.events"
    KAFKA_ONBOARDING_TOPIC: str = "onboarding.events"
    KAFKA_ENABLED: bool = True
    
    # Email (Resend API) - Optional
    RESEND_KEY: str = ""
    
    class Config:
        # Look for .env in project root (two levels up from services/user-service/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore any other extra fields from .env

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

