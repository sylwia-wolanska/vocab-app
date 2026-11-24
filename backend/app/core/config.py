from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vocab App"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str
    db_echo: bool = False
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
