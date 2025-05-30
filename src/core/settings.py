"""Application settings."""
from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    ENVIRONMENT: str = "development"

    # Project
    PROJECT_NAME: str = "xrouter-webhook-proxy"
    VERSION: str

    # Registry configuration
    REGISTRY_ID: str = ""

    # Host
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # Доступные форматы: json, text, structured
    LOG_EXTRA_FIELDS: list[str] = []  # Дополнительные поля для логов

    # Carrot Quest
    CARROT_QUEST_WEBHOOK_TOKEN: str = (
        ""  # Token from Carrot Quest admin panel for webhook verification
    )

    # Agent Service
    AGENT_SERVICE_URL: str = "http://localhost:8080"  # Base URL for agent service
    AGENT_SERVICE_TIMEOUT: float = 30.0  # Timeout for agent service requests in seconds

    class Config:
        """Configuration for settings loading."""

        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
