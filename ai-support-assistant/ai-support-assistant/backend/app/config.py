"""Application configuration.

All settings are environment-overridable with the ``APP_`` prefix, e.g.
``APP_OLLAMA_MODEL=qwen2.5`` or ``APP_OLLAMA_BASE_URL=http://ollama:11434``.
This keeps the app portable between local dev and docker-compose without code
changes.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # --- Ollama (local LLM) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    # temperature 0 -> deterministic intent classification
    ollama_temperature: float = 0.0
    request_timeout: float = 60.0

    # --- Conversation memory ---
    # How many prior turns to feed back into the model for follow-up resolution.
    max_history_turns: int = 5

    # --- Server ---
    cors_allow_origins: list[str] = ["*"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
