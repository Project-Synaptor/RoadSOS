"""Application configuration via pydantic-settings.

All environment variables are loaded here. No magic strings or numbers
in business logic — everything references these settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global app settings loaded from environment variables."""

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str

    # MiMo AI
    mimo_api_key: str
    mimo_api_base_url: str = "https://api.mimo.ai/v1"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Session TTL in seconds (default 1 hour)
    session_ttl: int = 3600

    # Path to the triage system prompt file
    triage_prompt_path: str = "prompts/triage_system.txt"

    # Path to the local emergency services JSON data
    hospital_data_path: str = "data/hospitals.json"

    # Supported languages for multilingual triage (ISO 639-1 codes)
    supported_languages: list[str] = ["en", "hi", "bn", "or", "ta", "te", "kn", "ml"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
