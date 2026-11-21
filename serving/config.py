from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="STORIX_AI_", extra="ignore")

    env: str = "local"
    pipeline_version: str = "v0.0"
    internal_token: SecretStr

    # 답변 (파이프라인 ⑦). Claude 키는 SDK 기본값대로 ANTHROPIC_API_KEY 에서 읽는다
    answer_model: str = "claude-sonnet-5-5"
    answer_effort: str = "low"
    answer_max_tokens: int = 4000
    answer_timeout_seconds: float = 40.0

    # 오래 조용하면 Spring · 프록시가 연결을 끊지 않게 주석 줄을 보낸다
    heartbeat_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
