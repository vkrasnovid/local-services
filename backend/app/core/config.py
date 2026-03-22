from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://app:password@postgres:5432/local_services"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Auth
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # YuKassa
    YUKASSA_SHOP_ID: str = "test"
    YUKASSA_SECRET_KEY: str = "test"
    YUKASSA_RETURN_URL: str = "https://app.example.com/payment/return"
    YUKASSA_WEBHOOK_SECRET: str = ""

    # FCM
    FCM_SERVER_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Business
    PLATFORM_FEE_PERCENT: int = 10

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()

if not settings.SECRET_KEY or settings.SECRET_KEY == "change-me-in-production":
    if settings.ENVIRONMENT not in ("development", "testing", "test"):
        raise RuntimeError(
            "SECRET_KEY must be set to a secure value in non-development environments. "
            "Set the SECRET_KEY environment variable."
        )
    if not settings.SECRET_KEY:
        settings.SECRET_KEY = "insecure-dev-key-do-not-use-in-production"
