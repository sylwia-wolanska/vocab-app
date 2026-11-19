from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vocab App"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str
    db_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
