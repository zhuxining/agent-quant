import pathlib
import tomllib
from typing import Any, Literal, cast

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

with pathlib.Path("pyproject.toml").open("rb") as f:
    pyproject = tomllib.load(f)


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields from env file
    )

    # General Settings
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    LOG_LEVEL: str = "INFO"  # Logging level
    SWAGGER_UI_ENABLED: bool = True  # Swagger UI, Change in production
    SCHEDULER_ENABLED: bool = False  # 是否启用定时任务
    AGENT_OS_ENABLED: bool = True  # 是否启用 AgentOS 封装

    # Database Settings
    DATABASE_TYPE: Literal["postgresql", "sqlite"] = "sqlite"
    SQLITE_URL: str = "tmp/local.db"
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SCHEMA: str = "fastapi_app"  # PostgreSQL schema name

    SECRET_KEY: str = "YOUR-SECRET-KEY-123"  # JWT Settings, Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    FIRST_SUPERUSER_EMAIL: str = "admin@admin.com"  # First Superuser
    FIRST_SUPERUSER_PASSWORD: str = "admin@admin.com"

    # OpenAPI Docs Settings, loaded from pyproject.toml
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = pyproject.get("project", {}).get("name")
    VERSION: str = pyproject.get("project", {}).get("version")
    DESCRIPTION: str = pyproject.get("project", {}).get("description")

    # LLMAgent
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_KEY: str = ""

    KIMI_MODEL: str = "kimi-k2-0905-preview"
    KIMI_API_KEY: str = ""

    # Longport
    LONGPORT_APP_KEY: str = ""
    LONGPORT_APP_SECRET: str = ""
    LONGPORT_ACCESS_TOKEN: str = ""

    @computed_field
    @property
    def postgre_url(self) -> PostgresDsn:
        url = MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
        return cast(PostgresDsn, str(url))


settings = Settings()
