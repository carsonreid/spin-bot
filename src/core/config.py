from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. SPINCO_* are optional; login can supply credentials per request."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    spinco_email: Optional[str] = None
    spinco_password: Optional[str] = None
    db_path: str = "data/spinbot.db"


settings = Settings()
