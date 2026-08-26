"""Application configuration and environment variables management."""

from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Sheetsly backend configuration settings."""

    # Application
    APP_NAME: str = "Sheetsly"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Server
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # File Processing
    MAX_UPLOAD_SIZE_MB: int = 50
    TEMP_FILE_DIRECTORY: str = "./storage/temp"

    # AI Configuration (Qwen / DashScope)
    DASHSCOPE_API_KEY: str = ""
    QWEN_MODEL: str = "qwen3.5-397b-a17b"
    QWEN_BASE_URL: str = "https://ws-6avfe6m7o2twqw9n.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    QWEN_ENABLE_THINKING: bool = True

    # AI Configuration (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_DEFAULT_MODEL: str = "gemini-3.5-flash"

    # Database (Reserved for future, disabled in MVP)
    DATABASE_ENABLED: bool = False
    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=[str(Path(__file__).resolve().parent.parent.parent / ".env"), ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def temp_storage_path(self) -> Path:
        path = Path(self.TEMP_FILE_DIRECTORY)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
