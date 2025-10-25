from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_DATABASE_URL: str
    ADMIN_TOKEN: str = "changeme"  # Default for dev; override in production
    APP_PORT: int = 8081
    ALEMBIC_INI: str = "alembic.ini"

    # Feature flags for bars_ohlcv and job tracking
    BARS_OHLCV_ENABLED: bool = True
    JOB_TRACKING_ENABLED: bool = True

    # StoreClient config (optional overrides)
    STORE_BATCH_THRESHOLD: int = 1000  # COPY vs executemany threshold

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def admin_token(self) -> str:
        return self.ADMIN_TOKEN

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
