from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str
    JWT_SECRET_KEY: str = "a_very_long_random_secret_key_at_least_32_bytes_long"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
