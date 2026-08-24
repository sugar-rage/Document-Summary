from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_storage_bucket: str = "documents"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"


    upload_dir: str = ""
    max_upload_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 20
    max_extracted_chars: int = 200_000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://document-summary-frontend-l5hk.onrender.com"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
