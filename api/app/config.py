from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POS_", env_file=".env")

    database_url: str = "sqlite:///./pos.db"
    photos_dir: Path = Path("./media/photos")


def get_settings() -> Settings:
    return Settings()
