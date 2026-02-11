"""
Gemini Image Chat Configuration

환경변수를 타입 안전하게 로드
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    port: int = 8000
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-pro-image-preview"

    # Database
    database_url: str = "sqlite:///./data/image_chat.db"

    # Shopify (for image file storage)
    shopify_store_url: str = ""
    shopify_access_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환"""
    return Settings()
