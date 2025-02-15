from zenml.client import Client
from zenml.exceptions import EntityExistsError

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    CLIENT_ID: str
    CLIENT_SECRET: str
    USER_AGENT: str
    MONGO_DB_NAME: str
    MONGO_COLLECTION: str
    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_AUTH_SOURCE: str

    @classmethod
    def load_settings(cls) -> "Settings":
        try:
            logger.info("Loading settings from ZenML secret store.")
            settings_secrets = Client().get_secret("settings")
            settings = Settings(**settings_secrets.secret_values)
        except (RuntimeError, KeyError):
            logger.warning(
                "Failed to load settings from ZenML secret store. Defaulting to loading the settings from .env file"
            )

            settings = Settings()

        return settings


settings = Settings.load_settings()
