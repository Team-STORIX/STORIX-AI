from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="STORIX_AI_", extra="ignore")

    env: str = "local"
    pipeline_version: str = "v0.0"
    internal_token: SecretStr


@lru_cache
def get_settings() -> Settings:
    return Settings()
