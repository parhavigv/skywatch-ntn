from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SkyWatch NTN"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql://skywatch:skywatch123@localhost:5432/skywatch_db"
    API_V1_PREFIX: str = "/api/v1"
    TOTAL_DEVICES: int = 500
    SIMULATION_INTERVAL_SECONDS: float = 1.0
    ADMIN_API_KEY: str = "sw-admin-changeme-in-prod"
    DEVICE_API_KEY: str = "sw-device-changeme-in-prod"
    REDIS_URL: str = "redis://localhost:6379"
    RATE_LIMIT_PER_MINUTE: int = 300


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()