from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration read from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str
    secret_key: str
    access_token_expire_hours: int = 8
    activation_token_expire_days: int = 7
    cookie_secure: bool = False
    upload_dir: str = "/uploads"
    max_upload_size_mb: int = 5
    max_files_per_report: int = 10
    frontend_origin: str = "http://localhost:5173"
    seed_manager_email: str = "manager@supherman.com"
    seed_manager_password: str = "Suph3rm4n!"


settings = Settings()
