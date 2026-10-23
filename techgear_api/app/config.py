from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "techgear"
    admin_api_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
