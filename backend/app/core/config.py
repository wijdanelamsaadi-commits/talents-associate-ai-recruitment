import ast
from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]


def _clean_cors_origins(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]

    if not isinstance(values, (list, tuple, set)):
        values = [values]

    origins: list[str] = []
    for value in values:
        origin = str(value).strip()
        if origin:
            origins.append(origin)
    return origins


class Settings(BaseSettings):
    PROJECT_NAME: str = "Talents Associate AI Recruitment Platform"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "talents_associate_ai"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str | None = None

    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_CORS_ORIGINS.copy()
    )
    FRONTEND_URL: str = "http://localhost:5173"
    JWT_SECRET_KEY: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str | None = None
    LLM_MODEL_NAME: str = "gpt-4.1-mini"
    LLM_ENABLED: bool = True
    LLM_REQUEST_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 2
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_REQUEST_TIMEOUT_SECONDS: int = 30
    EMBEDDING_MAX_RETRIES: int = 2
    WORDPRESS_API_KEY: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "Talents Associate"
    SMTP_TIMEOUT_SECONDS: int = 30
    EMAIL_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def postgres_dsn(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def effective_llm_model(self) -> str:
        return self.LLM_MODEL or self.LLM_MODEL_NAME

    @property
    def effective_embedding_api_key(self) -> str | None:
        return self.EMBEDDING_API_KEY or self.OPENAI_API_KEY

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return DEFAULT_CORS_ORIGINS.copy()

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            if raw_value.startswith("[") and raw_value.endswith("]"):
                try:
                    parsed_value = ast.literal_eval(raw_value)
                except (ValueError, SyntaxError):
                    parsed_value = None
                if isinstance(parsed_value, (list, tuple, set)):
                    return _clean_cors_origins(parsed_value)

            return _clean_cors_origins(raw_value.split(","))

        return _clean_cors_origins(value)

    @model_validator(mode="after")
    def normalize_openai_embedding_model(self) -> "Settings":
        if self.LLM_PROVIDER.lower() == "openai" and self.OPENAI_API_KEY:
            self.LLM_ENABLED = True
        if (
            self.EMBEDDING_PROVIDER.lower() == "openai"
            and self.EMBEDDING_MODEL_NAME.startswith("sentence-transformers/")
        ):
            self.EMBEDDING_MODEL_NAME = "text-embedding-3-small"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
