from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'scam_warning.db'}"
DEFAULT_UPLOAD_DIR = str(BACKEND_DIR / "uploads")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Scam Warning Platform"
    database_url: str = DEFAULT_DATABASE_URL
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    upload_dir: str = DEFAULT_UPLOAD_DIR
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    frontend_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
