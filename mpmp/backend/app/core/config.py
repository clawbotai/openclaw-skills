"""Application configuration — all secrets from environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "MPMP"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str  # JWT signing key
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://...
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # PHI Encryption (AES-256-GCM)
    PHI_ENCRYPTION_KEY: str  # 32-byte hex key

    # Azoth OS Integration
    AZOTH_OS_SYNC: bool = False
    AZOTH_API_BASE: str = "https://api.azoth-os.com/fhir/v1"
    AZOTH_CLIENT_ID: Optional[str] = None
    AZOTH_CLIENT_SECRET: Optional[str] = None
    AZOTH_WEBHOOK_SECRET: Optional[str] = None
    AZOTH_TOKEN_URL: str = "https://auth.azoth-os.com/oauth2/token"
    AZOTH_FHIR_SCOPE: str = "system/MedicationRequest.write"

    # External Services
    STRIPE_SECRET_KEY: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@mpmp.local"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
